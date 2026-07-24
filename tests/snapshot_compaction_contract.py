from __future__ import annotations

import copy
import importlib.util
import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_constitutional_lifecycle_snapshot_compaction.py"
FIXTURE = Path(os.environ["SNAPSHOT_COMPACTION_FIXTURE"])

spec = importlib.util.spec_from_file_location("snapshot_consumer", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class SnapshotCompactionConsumerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = FIXTURE.read_bytes()
        cls.data = json.loads(cls.raw)

    def mutate(self, mutator) -> bytes:
        data = copy.deepcopy(self.data)
        mutator(data)
        return (json.dumps(data, indent=2) + "\n").encode("utf-8")

    def case(self, case_id: str):
        return next(item for item in self.data["cases"] if item["case_id"] == case_id)

    def test_exact_producer_corpus_passes_independently(self) -> None:
        report = module.validate(self.raw)
        self.assertEqual(report["case_count"], 15)
        self.assertEqual(report["sha256"], "6b1e0177e73145572286d66e662bf498755cdbf685c05534f6e99a0d903bf140")
        self.assertTrue(report["independent_consumer"])
        self.assertFalse(report["grants_authority"])
        self.assertFalse(report["mutates_state"])

    def test_duplicate_keys_are_rejected(self) -> None:
        raw = self.raw.replace(
            b'"profile_version": "1.0.0",',
            b'"profile_version": "1.0.0",\n  "profile_version": "1.0.0",',
            1,
        )
        with self.assertRaises(module.ContractError):
            module.validate(raw)

    def test_non_finite_numbers_are_rejected(self) -> None:
        raw = self.raw.replace(b'"cases": [', b'"unexpected": NaN,\n  "cases": [', 1)
        with self.assertRaises(module.ContractError):
            module.validate(raw)

    def test_invalid_utf8_is_rejected(self) -> None:
        with self.assertRaises(module.ContractError):
            module.validate(self.raw + b"\xff")

    def test_unknown_and_prohibited_fields_are_rejected(self) -> None:
        with self.assertRaises(module.ContractError):
            module.validate(self.mutate(lambda data: data["cases"][0].update({"authority": True})))
        with self.assertRaises(module.ContractError):
            module.validate(self.mutate(lambda data: data["cases"][0].update({"private_key": "synthetic"})))

    def test_missing_and_duplicate_cases_are_rejected(self) -> None:
        with self.assertRaises(module.ContractError):
            module.validate(self.mutate(lambda data: data["cases"].pop()))
        with self.assertRaises(module.ContractError):
            module.validate(self.mutate(lambda data: data["cases"].append(copy.deepcopy(data["cases"][0]))))

    def test_snapshot_metadata_is_typed(self) -> None:
        with self.assertRaises(module.ContractError):
            module.validate(self.mutate(lambda data: data["cases"][0]["snapshot"].update({"digest_valid": 1})))

    def test_expected_disposition_drift_is_rejected(self) -> None:
        def mutate(data):
            case = next(item for item in data["cases"] if item["case_id"] == "healthy-compaction")
            case["expected"]["reason"] = "pending_ack_preserved"
        with self.assertRaises(module.ContractError):
            module.validate(self.mutate(mutate))

    def test_torn_snapshot_and_divergence_paths_fail_closed(self) -> None:
        evaluator = module.IndependentEvaluator()
        replay = evaluator.derive(self.case("torn-snapshot-full-log-replay"))
        pruned = evaluator.derive(self.case("torn-snapshot-after-prune-quarantined"))
        divergent = evaluator.derive(self.case("snapshot-log-divergence-quarantined"))
        self.assertEqual(replay[:2], ("converged", "full_log_replay"))
        self.assertEqual(pruned[:2], ("quarantined", "snapshot_unrecoverable_after_prune"))
        self.assertEqual(divergent[:2], ("quarantined", "snapshot_log_divergence"))

    def test_duplicate_transaction_identity_is_bounded(self) -> None:
        evaluator = module.IndependentEvaluator()
        accepted = evaluator.derive(self.case("duplicate-commit-idempotent"))
        blocked = evaluator.derive(self.case("conflicting-duplicate-commit-quarantined"))
        self.assertEqual(accepted[1], "duplicate_commit_idempotent")
        self.assertEqual(blocked[1], "conflicting_duplicate_transaction")

    def test_suspension_and_revocation_survive_compaction(self) -> None:
        evaluator = module.IndependentEvaluator()
        suspended = evaluator.derive(self.case("suspension-survives-compaction"))[2]
        revoked = evaluator.derive(self.case("revocation-survives-compaction"))[2]
        self.assertEqual(suspended["status"], "suspended")
        self.assertIn(suspended["authority_generation"], suspended["suspended_generations"])
        self.assertEqual(revoked["status"], "revoked")
        self.assertIn(revoked["authority_generation"], revoked["revoked_generations"])

    def test_revoked_authority_is_not_resurrected(self) -> None:
        outcome = module.IndependentEvaluator().derive(
            self.case("replacement-cannot-resurrect-revoked-authority")
        )
        self.assertEqual(outcome[:2], ("quarantined", "superseded_authority_resurrection_blocked"))

    def test_acknowledgment_loss_and_recovery_converge(self) -> None:
        evaluator = module.IndependentEvaluator()
        pending = evaluator.derive(self.case("lost-ack-preserves-pending-state"))[2]
        complete = evaluator.derive(self.case("acknowledgment-after-compaction-converges"))[2]
        self.assertEqual(pending["status"], "pending_ack")
        self.assertIsNotNone(pending["pending_ack_transaction"])
        self.assertEqual(complete["status"], "active")
        self.assertIsNone(complete["pending_ack_transaction"])


if __name__ == "__main__":
    unittest.main()
