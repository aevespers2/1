from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from scripts.verify_evidence_retention_source_tuple import (
    EXPECTED_EVIDENCE,
    EXPECTED_PRODUCER,
    _git_blob_sha,
    _load_strict,
    validate_tuple,
    verify_fixture_bytes,
)


def valid_tuple() -> dict:
    return {
        "schema": "repo1.evidence-retention.source-tuple.v1",
        "observation_generation": 1,
        "current": True,
        "producer": copy.deepcopy(EXPECTED_PRODUCER),
        "workflow_evidence": {
            **copy.deepcopy(EXPECTED_EVIDENCE),
            "artifact_available": True,
        },
        "resolution": {
            "resolved_at": "2026-07-23T02:55:54Z",
            "resolver_id": "repo1-retention-source-resolver-v1",
            "verifier_id": "repo1-retention-semantic-verifier-v1",
            "resolver_and_verifier_independent": True,
            "supersedes": [],
        },
        "authority_effect": "none",
    }


class SourceTupleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.as_of = datetime(2026, 7, 23, 3, 0, tzinfo=timezone.utc)

    def test_valid_tuple_passes(self) -> None:
        report = validate_tuple(valid_tuple(), self.as_of)
        self.assertTrue(report["source_tuple_current"])
        self.assertTrue(report["artifact_current_at_check"])
        self.assertEqual(report["authority_effect"], "none")

    def test_stale_or_moved_head_fails(self) -> None:
        payload = valid_tuple()
        payload["producer"]["head_sha"] = "0" * 40
        with self.assertRaisesRegex(ValueError, "producer source tuple mismatch"):
            validate_tuple(payload, self.as_of)

    def test_wrong_path_fails(self) -> None:
        payload = valid_tuple()
        payload["producer"]["path"] = "fixtures/moved.json"
        with self.assertRaisesRegex(ValueError, "producer source tuple mismatch"):
            validate_tuple(payload, self.as_of)

    def test_expired_artifact_fails(self) -> None:
        expired_check = datetime(2026, 8, 22, 1, 8, 9, tzinfo=timezone.utc)
        with self.assertRaisesRegex(ValueError, "artifact has expired"):
            validate_tuple(valid_tuple(), expired_check)

    def test_unavailable_artifact_fails(self) -> None:
        payload = valid_tuple()
        payload["workflow_evidence"]["artifact_available"] = False
        with self.assertRaisesRegex(ValueError, "artifact is unavailable"):
            validate_tuple(payload, self.as_of)

    def test_wrong_artifact_identity_fails(self) -> None:
        payload = valid_tuple()
        payload["workflow_evidence"]["artifact_id"] += 1
        with self.assertRaisesRegex(ValueError, "artifact_id"):
            validate_tuple(payload, self.as_of)

    def test_missing_supersession_fails_for_later_generation(self) -> None:
        payload = valid_tuple()
        payload["observation_generation"] = 2
        with self.assertRaisesRegex(ValueError, "missing supersession"):
            validate_tuple(payload, self.as_of)

    def test_resolver_verifier_collision_fails(self) -> None:
        payload = valid_tuple()
        payload["resolution"]["verifier_id"] = payload["resolution"]["resolver_id"]
        with self.assertRaisesRegex(ValueError, "identities collide"):
            validate_tuple(payload, self.as_of)

    def test_independence_must_be_boolean_true(self) -> None:
        payload = valid_tuple()
        payload["resolution"]["resolver_and_verifier_independent"] = 1
        with self.assertRaisesRegex(ValueError, "independence"):
            validate_tuple(payload, self.as_of)

    def test_unknown_field_fails(self) -> None:
        payload = valid_tuple()
        payload["producer"]["branch"] = "governance/consent-capacity-lock"
        with self.assertRaisesRegex(ValueError, "unknown"):
            validate_tuple(payload, self.as_of)

    def test_duplicate_json_key_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tuple.json"
            path.write_text('{"schema":"a","schema":"b"}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
                _load_strict(path, 64_000)

    def test_semantically_equal_byte_drift_fails_before_any_parse(self) -> None:
        original = b'{"a":1,"b":2}\n'
        reserialized = b'{\n  "a": 1,\n  "b": 2\n}\n'
        self.assertEqual(json.loads(original), json.loads(reserialized))
        producer = {
            "sha256": hashlib.sha256(original).hexdigest(),
            "git_blob": _git_blob_sha(original),
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.json"
            path.write_bytes(reserialized)
            with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                verify_fixture_bytes(path, producer)


if __name__ == "__main__":
    unittest.main()
