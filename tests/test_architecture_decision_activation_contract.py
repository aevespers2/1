from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import tempfile
import unittest

MODULE_PATH = Path(__file__).parents[1] / "scripts" / "validate_architecture_decision_activation.py"
SPEC = importlib.util.spec_from_file_location("architecture_decision_consumer", MODULE_PATH)
assert SPEC and SPEC.loader
consumer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(consumer)


def base_facts() -> dict[str, bool]:
    return {
        "exact_source_bound": True,
        "evidence_current": True,
        "reviews_complete": True,
        "conflicts_resolved": True,
        "self_approved": False,
        "dissent_preserved": True,
        "scope_bounded": True,
        "conditions_satisfied": True,
        "approval_present": False,
        "approval_current": False,
        "activation_present": False,
        "activation_scope_subset": True,
        "activation_authorized": False,
        "consumer_registry_complete": True,
        "propagation_complete": True,
        "superseded_or_withdrawn": False,
        "dependent_activation_invalidated": True,
        "rollback_required": False,
        "rollback_checkpoint_present": False,
        "restored_state_verified": False,
    }


def case(facts: dict[str, bool], disposition: str, reasons: list[str]) -> dict:
    return {
        "id": "synthetic-test",
        "facts": facts,
        "expected": {"disposition": disposition, "reasons": reasons},
    }


class ArchitectureDecisionConsumerTests(unittest.TestCase):
    def test_review_complete_does_not_become_approval(self) -> None:
        self.assertEqual(
            consumer.evaluate(base_facts()),
            ("REVIEW_COMPLETE_PENDING_DECISION", []),
        )

    def test_approval_does_not_become_activation(self) -> None:
        facts = base_facts()
        facts.update(approval_present=True, approval_current=True)
        self.assertEqual(consumer.evaluate(facts), ("APPROVED_NOT_ACTIVATED", []))

    def test_narrow_authorized_activation(self) -> None:
        facts = base_facts()
        facts.update(
            approval_present=True,
            approval_current=True,
            activation_present=True,
            activation_authorized=True,
            rollback_checkpoint_present=True,
        )
        self.assertEqual(consumer.evaluate(facts), ("ACTIVATED_AT_RECORDED_SCOPE", []))

    def test_scope_broadening_fails_closed(self) -> None:
        facts = base_facts()
        facts.update(
            approval_present=True,
            approval_current=True,
            activation_present=True,
            activation_authorized=True,
            activation_scope_subset=False,
        )
        self.assertEqual(
            consumer.evaluate(facts),
            ("ACTIVATION_BLOCKED", ["ACTIVATION_SCOPE_BROADENING"]),
        )

    def test_partial_propagation_is_unknown(self) -> None:
        facts = base_facts()
        facts.update(
            approval_present=True,
            approval_current=True,
            activation_present=True,
            activation_authorized=True,
            propagation_complete=False,
        )
        self.assertEqual(
            consumer.evaluate(facts),
            ("PARTIAL_OR_UNKNOWN", ["PARTIAL_OR_UNREACHABLE_PROPAGATION"]),
        )

    def test_withdrawal_requires_no_remaining_obstruction(self) -> None:
        facts = base_facts()
        facts.update(
            approval_present=True,
            superseded_or_withdrawn=True,
            rollback_required=True,
            rollback_checkpoint_present=True,
            restored_state_verified=True,
        )
        self.assertEqual(consumer.evaluate(facts), ("WITHDRAWN_OR_SUPERSEDED", []))

    def test_reason_drift_is_rejected(self) -> None:
        facts = base_facts()
        facts["exact_source_bound"] = False
        with self.assertRaisesRegex(ValueError, "derived"):
            consumer.validate_case(case(facts, "ACTIVATION_BLOCKED", []))

    def test_non_boolean_fact_is_rejected(self) -> None:
        facts = base_facts()
        facts["evidence_current"] = 1  # type: ignore[assignment]
        with self.assertRaisesRegex(ValueError, "must be Boolean"):
            consumer.validate_case(
                case(facts, "REVIEW_COMPLETE_PENDING_DECISION", [])
            )

    def test_duplicate_json_key_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate.json"
            path.write_text('{"schema":"a","schema":"b"}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
                consumer.strict_load(path)

    def test_invalid_utf8_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            path.write_bytes(b"{\xff}")
            with self.assertRaisesRegex(ValueError, "strict UTF-8"):
                consumer.strict_load(path)

    def test_sensitive_field_is_rejected(self) -> None:
        payload = {
            "schema": consumer.SCHEMA,
            "profile_version": consumer.PROFILE_VERSION,
            "data_class": consumer.DATA_CLASS,
            "cases": [],
            "private_key": "synthetic-but-prohibited",
        }
        with self.assertRaisesRegex(ValueError, "prohibited sensitive field"):
            consumer.validate_payload(payload)

    def test_immutable_producer_fixture_when_available(self) -> None:
        fixture = os.environ.get("ARCHITECTURE_DECISION_FIXTURE")
        if not fixture:
            self.skipTest("producer fixture is supplied by exact-head CI")
        payload = consumer.strict_load(Path(fixture))
        report = consumer.validate_payload(payload)
        self.assertEqual(len(report), 15)
        self.assertEqual(
            {item["disposition"] for item in report},
            consumer.ALLOWED_DISPOSITIONS,
        )


if __name__ == "__main__":
    unittest.main()
