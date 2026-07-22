from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures" / "constitutional-appointment-lifecycle-v1.json.gz.b64"
SCRIPT = ROOT / "scripts" / "validate_constitutional_appointment_lifecycle.py"
EXPECTED_SHA256 = "be85c05f876a1027fbf960d464fbc919e5896ccdd03dfa7373563c16ab9280fe"

spec = importlib.util.spec_from_file_location("lifecycle_validator", SCRIPT)
assert spec and spec.loader
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


class ConstitutionalLifecycleContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.document, self.sha256 = validator.load_fixture(FIXTURE)

    def validate_copy(self, document: dict) -> list[str]:
        return validator.validate_fixture(copy.deepcopy(document))

    def test_frozen_fixture_is_valid(self) -> None:
        self.assertEqual(self.sha256, EXPECTED_SHA256)
        self.assertEqual(validator.validate_fixture(self.document), [])

    def test_case_coverage_is_exact(self) -> None:
        changed = copy.deepcopy(self.document)
        changed["cases"].pop()
        errors = validator.validate_fixture(changed)
        self.assertTrue(any("case coverage mismatch" in error for error in errors))

    def test_duplicate_case_identity_is_rejected(self) -> None:
        changed = copy.deepcopy(self.document)
        changed["cases"][1]["case_id"] = changed["cases"][0]["case_id"]
        errors = validator.validate_fixture(changed)
        self.assertTrue(any("case_id values must be unique" in error for error in errors))

    def test_unknown_top_level_field_is_rejected(self) -> None:
        changed = copy.deepcopy(self.document)
        changed["authority"] = "active"
        errors = validator.validate_fixture(changed)
        self.assertTrue(any("field mismatch" in error for error in errors))

    def test_unknown_control_is_rejected(self) -> None:
        changed = copy.deepcopy(self.document)
        changed["cases"][0]["controls"]["self_appoint"] = True
        errors = validator.validate_fixture(changed)
        self.assertTrue(any("controls: field mismatch" in error for error in errors))

    def test_non_boolean_control_is_rejected(self) -> None:
        changed = copy.deepcopy(self.document)
        changed["cases"][0]["controls"]["nomination_recorded"] = 1
        errors = validator.validate_fixture(changed)
        self.assertTrue(any("controls must be boolean" in error for error in errors))

    def test_event_actor_mismatch_is_rejected(self) -> None:
        changed = copy.deepcopy(self.document)
        changed["cases"][0]["events"][0]["actor_role"] = "authority_registry"
        errors = validator.validate_fixture(changed)
        self.assertTrue(any("is invalid for" in error for error in errors))

    def test_event_sequence_gap_is_rejected(self) -> None:
        changed = copy.deepcopy(self.document)
        changed["cases"][4]["events"][3]["sequence"] = 99
        errors = validator.validate_fixture(changed)
        self.assertTrue(any("contiguous and ordered" in error for error in errors))

    def test_expected_disposition_drift_is_rejected(self) -> None:
        changed = copy.deepcopy(self.document)
        changed["cases"][4]["expected_reason"] = "credential_unbound"
        errors = validator.validate_fixture(changed)
        self.assertTrue(any("does not match independently derived" in error for error in errors))

    def test_prohibited_secret_bearing_field_is_rejected(self) -> None:
        changed = copy.deepcopy(self.document)
        changed["cases"][0]["controls"]["private_key"] = "synthetic"
        errors = validator.validate_fixture(changed)
        self.assertTrue(any("prohibited fields present" in error for error in errors))

    def write_encoded(self, raw: bytes, path: Path) -> None:
        import base64
        import gzip

        path.write_bytes(base64.b64encode(gzip.compress(raw, mtime=0)))

    def test_duplicate_json_key_is_rejected(self) -> None:
        raw = json.dumps(self.document, indent=2).replace(
            '"profile_version": "1.0.0",',
            '"profile_version": "1.0.0",\n  "profile_version": "1.0.0",',
            1,
        ).encode()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "duplicate.json.gz.b64"
            self.write_encoded(raw, path)
            with self.assertRaises(validator.FixtureError):
                validator.load_fixture(path)

    def test_non_finite_number_is_rejected(self) -> None:
        raw = json.dumps(self.document, indent=2).replace(
            '"profile_version": "1.0.0"',
            '"profile_version": NaN',
            1,
        ).encode()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "nan.json.gz.b64"
            self.write_encoded(raw, path)
            with self.assertRaises(validator.FixtureError):
                validator.load_fixture(path)

    def test_invalid_utf8_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "invalid.json.gz.b64"
            self.write_encoded(b'{"schema":"x","bad":"\xff"}', path)
            with self.assertRaises(validator.FixtureError):
                validator.load_fixture(path)

    def test_invalid_base64_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "invalid.json.gz.b64"
            path.write_bytes(b"not base64!")
            with self.assertRaises(validator.FixtureError):
                validator.load_fixture(path)

    def test_invalid_gzip_is_rejected(self) -> None:
        import base64

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "invalid.json.gz.b64"
            path.write_bytes(base64.b64encode(b"not gzip"))
            with self.assertRaises(validator.FixtureError):
                validator.load_fixture(path)

    def test_hash_drift_is_observable(self) -> None:
        changed = json.dumps(self.document, indent=2).encode() + b"\n\n"
        self.assertNotEqual(
            __import__("hashlib").sha256(changed).hexdigest(),
            EXPECTED_SHA256,
        )


if __name__ == "__main__":
    unittest.main()
