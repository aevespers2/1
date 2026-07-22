from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_architecture_review_quorum import (
    canonical_sha256,
    evaluate_base,
    evaluate_extension,
    load_strict,
)


POLICY = {
    "required_classes": ["architecture", "security", "operations"],
    "minimum_approvals": 3,
    "minimum_independent_groups": 3,
}


def reviewer(
    identifier: str,
    reviewer_class: str,
    *,
    disposition: str = "APPROVE",
    qualified: bool = True,
    appointed: bool = True,
    accepted: bool = True,
    conflict_clear: bool = True,
    group: str | None = None,
    roles: list[str] | None = None,
) -> dict[str, object]:
    return {
        "reviewer_id": identifier,
        "reviewer_class": reviewer_class,
        "disposition": disposition,
        "qualified": qualified,
        "appointed": appointed,
        "accepted": accepted,
        "conflict_clear": conflict_clear,
        "independence_group": group or identifier,
        "roles": roles or [reviewer_class],
    }


def clean_case() -> dict[str, object]:
    return {
        "source_exact": True,
        "policy_exact": True,
        "reviewers": [
            reviewer("r-arch", "architecture"),
            reviewer("r-sec", "security"),
            reviewer("r-ops", "operations"),
        ],
        "dissent_required": False,
        "dissent_preserved": True,
        "decision_record_present": False,
        "appeal_status": "NONE",
        "superseded": False,
    }


class ArchitectureReviewQuorumConsumerTests(unittest.TestCase):
    def test_clean_review_stops_before_decision(self) -> None:
        result = evaluate_base(clean_case(), POLICY)
        self.assertEqual(result["state"], "REVIEW_COMPLETE_PENDING_DECISION")
        self.assertEqual(result["reason_codes"], [])
        self.assertEqual(result["authority_effect"], "none")

    def test_unqualified_reviewer_fails_quorum_and_independence(self) -> None:
        case = clean_case()
        case["reviewers"][1]["qualified"] = False
        result = evaluate_base(case, POLICY)
        self.assertEqual(result["state"], "REVIEW_INCOMPLETE")
        self.assertIn("STALE_OR_UNQUALIFIED_REVIEWER", result["reason_codes"])
        self.assertIn("QUORUM_NOT_MET", result["reason_codes"])
        self.assertIn("INDEPENDENCE_VIOLATION", result["reason_codes"])

    def test_abstention_is_not_approval(self) -> None:
        case = clean_case()
        case["reviewers"][2]["disposition"] = "ABSTAIN"
        case["claimed_counted_reviewers"] = ["r-ops"]
        result = evaluate_base(case, POLICY)
        self.assertIn("ABSTENTION_COUNTED_AS_APPROVAL", result["reason_codes"])
        self.assertIn("QUORUM_NOT_MET", result["reason_codes"])

    def test_self_review_is_rejected(self) -> None:
        case = clean_case()
        case["reviewers"][0]["roles"] = ["author", "architecture"]
        result = evaluate_base(case, POLICY)
        self.assertIn("SELF_REVIEW", result["reason_codes"])

    def test_review_record_cannot_become_decision(self) -> None:
        case = clean_case()
        case["decision_record_present"] = True
        result = evaluate_base(case, POLICY)
        self.assertIn("REVIEW_PROMOTED_TO_DECISION", result["reason_codes"])

    def test_pending_appeal_is_separate_state(self) -> None:
        case = clean_case()
        case["appeal_status"] = "PENDING"
        result = evaluate_base(case, POLICY)
        self.assertEqual(result["state"], "APPEAL_REVIEW_PENDING")
        self.assertEqual(result["reason_codes"], [])

    def test_extension_detects_common_control_and_role_collision(self) -> None:
        facts = {
            "class_coverage_complete": True,
            "common_control_disclosed": False,
            "conflicts_and_recusals_resolved": True,
            "incompatible_role_double_count": True,
            "appeal_present": False,
            "appeal_authorized_and_current": False,
            "appeal_panel_complete_and_independent": False,
            "emergency_review_present": False,
            "emergency_scope_bounded": True,
            "superseded": False,
            "dependent_findings_invalidated": True,
        }
        disposition, reasons = evaluate_extension(facts)
        self.assertEqual(disposition, "REVIEW_INCOMPLETE")
        self.assertEqual(
            reasons,
            ["UNDISCLOSED_COMMON_CONTROL", "INCOMPATIBLE_ROLE_DOUBLE_COUNT"],
        )

    def test_extension_blocks_unauthorized_appeal(self) -> None:
        facts = {
            "class_coverage_complete": True,
            "common_control_disclosed": True,
            "conflicts_and_recusals_resolved": True,
            "incompatible_role_double_count": False,
            "appeal_present": True,
            "appeal_authorized_and_current": False,
            "appeal_panel_complete_and_independent": True,
            "emergency_review_present": False,
            "emergency_scope_bounded": True,
            "superseded": False,
            "dependent_findings_invalidated": True,
        }
        disposition, reasons = evaluate_extension(facts)
        self.assertEqual(disposition, "APPEAL_BLOCKED")
        self.assertEqual(reasons, ["UNAUTHORIZED_OR_EXPIRED_APPEAL"])

    def test_duplicate_keys_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate.json"
            path.write_text('{"a":1,"a":2}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
                load_strict(path)

    def test_canonical_digest_ignores_whitespace_not_semantics(self) -> None:
        first = {"b": [2, 3], "a": 1}
        second = json.loads('{  "a": 1, "b": [2,3] }')
        changed = {"b": [2, 4], "a": 1}
        self.assertEqual(canonical_sha256(first), canonical_sha256(second))
        self.assertNotEqual(canonical_sha256(first), canonical_sha256(changed))


if __name__ == "__main__":
    unittest.main()
