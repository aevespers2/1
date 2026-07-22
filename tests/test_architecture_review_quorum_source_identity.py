from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.validate_architecture_review_quorum import canonical_sha256
from scripts.verify_architecture_review_quorum_source_identity import (
    verify_source_identity,
)


class ArchitectureReviewQuorumSourceIdentityTests(unittest.TestCase):
    def test_exact_bytes_and_canonical_identity_pass(self) -> None:
        raw = b'{"a":1,"b":[2,3]}'
        expected_raw = hashlib.sha256(raw).hexdigest()
        expected_canonical = canonical_sha256(json.loads(raw))

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.json"
            path.write_bytes(raw)
            report = verify_source_identity(path, expected_raw, expected_canonical)

        self.assertTrue(report["raw_identity_matches"])
        self.assertTrue(report["canonical_identity_matches"])
        self.assertTrue(report["raw_gate_precedes_semantic_validation"])
        self.assertEqual(report["authority_effect"], "none")

    def test_semantically_equal_reserialization_fails_before_parse(self) -> None:
        producer_raw = b'{"a":1,"b":[2,3]}'
        expected_raw = hashlib.sha256(producer_raw).hexdigest()
        expected_canonical = canonical_sha256(json.loads(producer_raw))
        reserialized = (
            json.dumps(json.loads(producer_raw), indent=2, sort_keys=True) + "\n"
        ).encode("utf-8")

        self.assertNotEqual(hashlib.sha256(reserialized).hexdigest(), expected_raw)
        self.assertEqual(canonical_sha256(json.loads(reserialized)), expected_canonical)

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "reserialized.json"
            path.write_bytes(reserialized)
            with patch(
                "scripts.verify_architecture_review_quorum_source_identity.load_strict",
                side_effect=AssertionError("semantic validation was reached"),
            ) as parser:
                with self.assertRaisesRegex(ValueError, "raw fixture SHA-256 mismatch"):
                    verify_source_identity(path, expected_raw, expected_canonical)
                parser.assert_not_called()

    def test_canonical_drift_fails_after_exact_byte_gate(self) -> None:
        raw = b'{"a":1,"b":[2,4]}'
        expected_raw = hashlib.sha256(raw).hexdigest()
        wrong_canonical = canonical_sha256({"a": 1, "b": [2, 3]})

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "changed.json"
            path.write_bytes(raw)
            with self.assertRaisesRegex(ValueError, "canonical fixture SHA-256 mismatch"):
                verify_source_identity(path, expected_raw, wrong_canonical)


if __name__ == "__main__":
    unittest.main()
