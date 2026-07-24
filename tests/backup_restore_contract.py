from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_constitutional_lifecycle_backup_restore.py"
FIXTURE = ROOT / "evidence" / "lifecycle-journal" / "backup-restore-producer-fixture.json"
EXPECTED_SHA256 = "1da592ac85a1880e7b3701860e5c360260622bf4ca36f8eb6c14693a7201a83b"

spec = importlib.util.spec_from_file_location("backup_restore_consumer", SCRIPT)
consumer = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(consumer)


class BackupRestoreConsumerTests(unittest.TestCase):
    def setUp(self) -> None:
        raw = FIXTURE.read_bytes()
        self.document, self.digest = consumer.load(raw)

    def test_frozen_fixture_is_valid(self) -> None:
        self.assertEqual(EXPECTED_SHA256, self.digest)
        report = consumer.validate(copy.deepcopy(self.document))
        self.assertEqual("PASS", report["status"])
        self.assertEqual(17, report["case_count"])

    def test_duplicate_key_is_rejected(self) -> None:
        with self.assertRaises(consumer.ContractError):
            consumer.load(b'{"schema":"a","schema":"b"}')

    def test_non_finite_number_is_rejected(self) -> None:
        with self.assertRaises(consumer.ContractError):
            consumer.load(b'{"value":Infinity}')

    def test_unknown_field_is_rejected(self) -> None:
        document = copy.deepcopy(self.document)
        document["cases"][0]["backup"]["unexpected"] = True
        with self.assertRaises(consumer.ContractError):
            consumer.validate(document)

    def test_prohibited_material_is_rejected(self) -> None:
        document = copy.deepcopy(self.document)
        document["cases"][0]["secret"] = "synthetic"
        with self.assertRaises(consumer.ContractError):
            consumer.validate(document)

    def test_missing_case_is_rejected(self) -> None:
        document = copy.deepcopy(self.document)
        document["cases"].pop()
        with self.assertRaises(consumer.ContractError):
            consumer.validate(document)

    def test_manifest_boolean_is_strict(self) -> None:
        document = copy.deepcopy(self.document)
        document["cases"][0]["backup"]["manifest_valid"] = 1
        with self.assertRaises(consumer.ContractError):
            consumer.validate(document)

    def test_disposition_drift_is_rejected(self) -> None:
        document = copy.deepcopy(self.document)
        document["cases"][0]["expected"]["reason"] = "restore_log_gap"
        with self.assertRaises(consumer.ContractError):
            consumer.validate(document)

    def test_duplicate_retained_transaction_is_rejected(self) -> None:
        document = copy.deepcopy(self.document)
        case = next(item for item in document["cases"] if item["case_id"] == "stale-backup-complete-log-converges")
        case["restore"]["retained_events"].append(copy.deepcopy(case["restore"]["retained_events"][0]))
        with self.assertRaises(consumer.ContractError):
            consumer.validate(document)

    def test_invalid_utf8_is_rejected(self) -> None:
        with self.assertRaises(consumer.ContractError):
            consumer.load(b"\xff")


if __name__ == "__main__":
    unittest.main()
