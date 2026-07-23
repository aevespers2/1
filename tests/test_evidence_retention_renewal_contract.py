from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from scripts import validate_evidence_retention_renewal as validator

FIXTURE = Path(os.environ.get("EVIDENCE_RETENTION_FIXTURE", "evidence/retention/producer-fixture.json"))


class EvidenceRetentionRenewalContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not FIXTURE.is_file():
            raise RuntimeError(f"producer fixture not found: {FIXTURE}")

    def payload(self):
        return validator.strict_load(FIXTURE)

    def write_payload(self, payload) -> Path:
        handle = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        with handle:
            handle.write(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
        return Path(handle.name)

    def assert_rejected(self, payload) -> None:
        path = self.write_payload(payload)
        self.addCleanup(path.unlink, missing_ok=True)
        with self.assertRaises(ValueError):
            validator.validate_payload(validator.strict_load(path))

    def test_producer_fixture_passes_independent_derivation(self):
        cases = validator.validate_payload(self.payload())
        self.assertEqual(len(cases), validator.EXPECTED_CASE_COUNT)

    def test_duplicate_key_rejected_before_semantic_validation(self):
        raw = FIXTURE.read_text(encoding="utf-8").replace('"version":1,', '"version":1,"version":1,', 1)
        path = Path(tempfile.mkstemp(suffix=".json")[1])
        self.addCleanup(path.unlink, missing_ok=True)
        path.write_text(raw, encoding="utf-8")
        with self.assertRaises(ValueError):
            validator.strict_load(path)

    def test_invalid_utf8_rejected(self):
        path = Path(tempfile.mkstemp(suffix=".json")[1])
        self.addCleanup(path.unlink, missing_ok=True)
        path.write_bytes(b'{"profile_id":"x","bad":"\xff"}')
        with self.assertRaises(ValueError):
            validator.strict_load(path)

    def test_unknown_top_level_field_rejected(self):
        payload = self.payload()
        payload["authority"] = True
        self.assert_rejected(payload)

    def test_sensitive_field_rejected(self):
        payload = self.payload()
        payload["cases"][0]["facts"]["private_key_material"] = False
        self.assert_rejected(payload)

    def test_fact_registry_order_drift_rejected(self):
        payload = self.payload()
        payload["fact_fields"] = list(reversed(payload["fact_fields"]))
        self.assert_rejected(payload)

    def test_non_boolean_fact_rejected(self):
        payload = self.payload()
        payload["cases"][0]["facts"]["artifact_available"] = "true"
        self.assert_rejected(payload)

    def test_expected_disposition_drift_rejected(self):
        payload = self.payload()
        payload["cases"][0]["expected"]["disposition"] = "BLOCKED"
        self.assert_rejected(payload)

    def test_reason_order_drift_rejected(self):
        payload = self.payload()
        target = next(case for case in payload["cases"] if len(case["expected"]["reasons"]) > 1)
        target["expected"]["reasons"].reverse()
        self.assert_rejected(payload)

    def test_missing_case_rejected(self):
        payload = self.payload()
        payload["cases"].pop()
        self.assert_rejected(payload)

    def test_unregistered_reason_rejected(self):
        payload = self.payload()
        payload["reason_order"].append("UNREGISTERED_REASON")
        self.assert_rejected(payload)


if __name__ == "__main__":
    unittest.main()
