from __future__ import annotations

import copy
import importlib.util
import os
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_constitutional_lifecycle_restore_staging_multicopy.py"
FIXTURE = Path(os.environ.get(
    "RESTORE_STAGING_MULTICOPY_FIXTURE",
    "evidence/lifecycle-journal/restore-staging-multicopy-producer-fixture.json",
))
EXPECTED_SHA256 = "812f1e5580caa687d30e96e9efed8214d47a131337f82577cfcaa1c27d1e46a2"

SPEC = importlib.util.spec_from_file_location("restore_staging_authority", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class RestoreStagingAuthorityContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = FIXTURE.read_bytes()
        cls.root, cls.digest = MODULE.decode(cls.raw)

    def validate(self, root: dict) -> dict:
        return MODULE.validate(copy.deepcopy(root))

    def test_independent_full_corpus_and_digest(self) -> None:
        report = MODULE.validate_bytes(self.raw, EXPECTED_SHA256)
        self.assertEqual(report["case_count"], 17)
        self.assertEqual(report["errors"], [])
        self.assertEqual(report["authority_effect"], "none")
        self.assertEqual(report["implementation"], "repository-1-independent-authority-side")

    def test_digest_mismatch_fails(self) -> None:
        with self.assertRaises(MODULE.ContractError):
            MODULE.validate_bytes(self.raw, "f" * 64)

    def test_duplicate_key_fails(self) -> None:
        with self.assertRaises(MODULE.ContractError):
            MODULE.decode(b'{"schema":"a","schema":"b"}')

    def test_non_finite_number_fails(self) -> None:
        with self.assertRaises(MODULE.ContractError):
            MODULE.decode(b'{"epoch":Infinity}')

    def test_invalid_utf8_fails(self) -> None:
        with self.assertRaises(MODULE.ContractError):
            MODULE.decode(b"\xfe")

    def test_unknown_field_fails(self) -> None:
        root = copy.deepcopy(self.root)
        root["cases"][0]["request"]["activate_authority"] = False
        with self.assertRaises(MODULE.ContractError):
            self.validate(root)

    def test_duplicate_copy_identity_fails(self) -> None:
        root = copy.deepcopy(self.root)
        root["cases"][0]["copies"][1]["copy_id"] = root["cases"][0]["copies"][0]["copy_id"]
        with self.assertRaises(MODULE.ContractError):
            self.validate(root)

    def test_non_boolean_manifest_fails(self) -> None:
        root = copy.deepcopy(self.root)
        root["cases"][0]["copies"][0]["manifest_valid"] = 1
        with self.assertRaises(MODULE.ContractError):
            self.validate(root)

    def test_duplicate_selected_copy_fails(self) -> None:
        root = copy.deepcopy(self.root)
        root["cases"][0]["request"]["selected_copy_ids"] = ["copy-a", "copy-a"]
        with self.assertRaises(MODULE.ContractError):
            self.validate(root)

    def test_retry_reference_on_non_retry_fails(self) -> None:
        root = copy.deepcopy(self.root)
        root["cases"][0]["request"]["retry_of"] = "restore-12"
        with self.assertRaises(MODULE.ContractError):
            self.validate(root)

    def test_disposition_drift_fails(self) -> None:
        root = copy.deepcopy(self.root)
        root["cases"][0]["expected"]["disposition"] = "staged"
        with self.assertRaises(MODULE.ContractError):
            self.validate(root)

    def test_state_conflict_cannot_be_promoted(self) -> None:
        root = copy.deepcopy(self.root)
        case = next(item for item in root["cases"] if item["case_id"] == "conflicting-state-same-epoch")
        case["expected"] = copy.deepcopy(root["cases"][0]["expected"])
        with self.assertRaises(MODULE.ContractError):
            self.validate(root)

    def test_stale_epoch_cannot_be_promoted(self) -> None:
        root = copy.deepcopy(self.root)
        case = next(item for item in root["cases"] if item["case_id"] == "stale-epoch-anti-rollback")
        case["expected"] = copy.deepcopy(root["cases"][0]["expected"])
        with self.assertRaises(MODULE.ContractError):
            self.validate(root)

    def test_prohibited_secret_field_fails(self) -> None:
        root = copy.deepcopy(self.root)
        root["cases"][0]["copies"][0]["state"]["access_token"] = "synthetic"
        with self.assertRaises(MODULE.ContractError):
            self.validate(root)


if __name__ == "__main__":
    unittest.main()
