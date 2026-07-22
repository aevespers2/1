from __future__ import annotations

import copy
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_constitutional_lifecycle_transaction_journal.py"
FIXTURE = ROOT / "fixtures" / "constitutional-lifecycle-transaction-journal-v1.json"

spec = importlib.util.spec_from_file_location("lifecycle_journal_contract", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class LifecycleJournalContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = FIXTURE.read_bytes()
        cls.data, cls.digest = module.decode_fixture(FIXTURE)

    def mutate(self, mutator) -> dict:
        data = copy.deepcopy(self.data)
        mutator(data)
        return data

    def case(self, case_id: str):
        return next(case for case in self.data["cases"] if case["case_id"] == case_id)

    def test_shared_fixture_passes(self) -> None:
        report = module.validate_document(self.data)
        self.assertEqual(report["cases"], 15)
        self.assertFalse(report["appointment_authority"])
        self.assertFalse(report["credential_authority"])
        self.assertFalse(report["operational_authority"])

    def test_digest_is_frozen(self) -> None:
        self.assertEqual(
            self.digest,
            "514ff45d55ae889a534a005465f71c1c74997585e10a53de89094d7f07583dd9",
        )

    def test_duplicate_json_keys_are_rejected(self) -> None:
        raw = self.raw.replace(
            b'"profile_version": "1.0.0",',
            b'"profile_version": "1.0.0",\n  "profile_version": "1.0.0",',
            1,
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "duplicate.json"
            path.write_bytes(raw)
            with self.assertRaises(module.ContractError):
                module.decode_fixture(path)

    def test_non_finite_and_invalid_utf8_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            path.write_bytes(self.raw.replace(b'"cases": [', b'"extra": NaN,\n  "cases": [', 1))
            with self.assertRaises(module.ContractError):
                module.decode_fixture(path)
            path.write_bytes(self.raw + b"\xff")
            with self.assertRaises(module.ContractError):
                module.decode_fixture(path)

    def test_closed_schema_and_prohibited_fields(self) -> None:
        with self.assertRaises(module.ContractError):
            module.validate_document(
                self.mutate(lambda data: data["cases"][0].update({"authority": True}))
            )
        with self.assertRaises(module.ContractError):
            module.validate_document(
                self.mutate(lambda data: data["cases"][0].update({"access_token": "x"}))
            )

    def test_exact_fixture_coverage_is_required(self) -> None:
        with self.assertRaises(module.ContractError):
            module.validate_document(self.mutate(lambda data: data["cases"].pop()))
        with self.assertRaises(module.ContractError):
            module.validate_document(
                self.mutate(lambda data: data["cases"].append(data["cases"][0]))
            )

    def test_expected_disposition_drift_is_rejected(self) -> None:
        with self.assertRaises(module.ContractError):
            module.validate_document(
                self.mutate(
                    lambda data: data["cases"][0].update({"expected_reason": "recovery_noop"})
                )
            )

    def test_concurrent_replacement_is_not_arbitrated(self) -> None:
        self.assertEqual(
            module.project(self.case("concurrent-replacement-conflict")),
            ("active", "concurrent_replacement_conflict",
             "synthetic_bounded_active", 4, 7),
        )

    def test_suspension_and_appeal_race_is_deterministic(self) -> None:
        self.assertEqual(
            module.project(self.case("suspension-wins-over-appeal-race")),
            ("suspended_appeal_pending", "suspension_precedence", "none", 8, 2),
        )

    def test_late_and_replayed_acknowledgments_do_not_widen_authority(self) -> None:
        late = module.project(self.case("late-ack-after-generation-change"))
        replay = module.project(self.case("replayed-acknowledgment-idempotent"))
        self.assertEqual(late[1], "stale_ack_rejected")
        self.assertEqual(replay[1], "acknowledgment_idempotent")

    def test_credential_rotation_requires_new_propagation(self) -> None:
        outcome = module.project(self.case("credential-generation-rotation"))
        self.assertEqual(
            outcome,
            ("pending_propagation", "credential_rotation_pending_ack", "none", 10, 3),
        )

    def test_rollback_interruptions_converge_deterministically(self) -> None:
        before = module.project(self.case("rollback-interrupted-before-commit"))
        prepared = module.project(self.case("rollback-interrupted-after-prepare"))
        committed = module.project(self.case("rollback-committed-before-ack"))
        recovered = module.project(self.case("recovery-preserves-committed-rollback"))
        self.assertEqual((before[0], before[3]), ("active", 7))
        self.assertEqual((prepared[0], prepared[3]), ("active", 7))
        self.assertEqual((committed[0], committed[3]), ("rolled_back_pending_ack", 6))
        self.assertEqual((recovered[0], recovered[3]), ("rolled_back_pending_ack", 6))

    def test_corrupt_gap_and_duplicate_journals_quarantine(self) -> None:
        for case_id in (
            "corrupted-journal-quarantined",
            "journal-sequence-gap-quarantined",
            "duplicate-transaction-id-quarantined",
        ):
            with self.subTest(case_id=case_id):
                self.assertEqual(module.project(self.case(case_id))[0], "quarantined")


if __name__ == "__main__":
    unittest.main()
