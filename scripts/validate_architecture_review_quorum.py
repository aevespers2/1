#!/usr/bin/env python3
"""Independent Repository 1 consumer for architecture-review quorum corpora.

The evaluator consumes the immutable QSO Field synthetic base and coverage
extension. It does not import producer or QSO-STUDIO code. Passing results are
conformance evidence only and confer no reviewer, quorum, decision, activation,
or operational authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

BASE_CANONICAL_SHA256 = "a8b65c3fce4b7cf80fdefab76c497720b2bf17086d431a53f9bacf82e58bd9ec"
EXTENSION_CANONICAL_SHA256 = "6e767141e6c76ec43366b661db0fee9090a56c9ce7d50eda28da7f1094d5e3c2"
APPROVING_DISPOSITIONS = frozenset({"APPROVE", "APPROVE_WITH_CONDITIONS"})

EXTENSION_TOP_KEYS = frozenset(
    {"schema", "profile_version", "data_class", "extends", "defaults", "cases"}
)
EXTENSION_LINK_KEYS = frozenset(
    {"fixture", "base_case_count", "base_fixture_generation", "contract"}
)
EXTENSION_FACT_KEYS = frozenset(
    {
        "class_coverage_complete",
        "common_control_disclosed",
        "conflicts_and_recusals_resolved",
        "incompatible_role_double_count",
        "appeal_present",
        "appeal_authorized_and_current",
        "appeal_panel_complete_and_independent",
        "emergency_review_present",
        "emergency_scope_bounded",
        "superseded",
        "dependent_findings_invalidated",
    }
)
EXTENSION_REASON_ORDER = (
    "INCOMPLETE_REVIEW_CLASS_COVERAGE",
    "UNDISCLOSED_COMMON_CONTROL",
    "UNRESOLVED_CONFLICT_OR_RECUSAL",
    "INCOMPATIBLE_ROLE_DOUBLE_COUNT",
    "UNAUTHORIZED_OR_EXPIRED_APPEAL",
    "INCOMPLETE_OR_CONFLICTED_APPEAL_PANEL",
    "EMERGENCY_SCOPE_BROADENING",
    "STALE_REVIEW_AFTER_SUPERSESSION",
)
EXTENSION_DISPOSITIONS = frozenset(
    {"COVERAGE_EXTENSION_CLEAR", "REVIEW_INCOMPLETE", "APPEAL_BLOCKED"}
)
PROHIBITED_KEY_FRAGMENTS = (
    "password",
    "private_key",
    "secret",
    "access_token",
    "biometric",
    "iris_template",
)


def _object_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON number is prohibited: {value}")


def _assert_finite(value: Any, location: str = "root") -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"non-finite number at {location}")
    if isinstance(value, dict):
        for key, child in value.items():
            _assert_finite(child, f"{location}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _assert_finite(child, f"{location}[{index}]")


def _reject_sensitive_fields(value: Any, location: str = "root") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            lowered = key.lower()
            if any(fragment in lowered for fragment in PROHIBITED_KEY_FRAGMENTS):
                raise ValueError(f"prohibited sensitive field at {location}.{key}")
            _reject_sensitive_fields(child, f"{location}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_sensitive_fields(child, f"{location}[{index}]")


def load_strict(path: Path) -> Any:
    raw = path.read_bytes()
    if len(raw) > 1_000_000:
        raise ValueError("fixture exceeds one-megabyte validation bound")
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ValueError(f"fixture is not strict UTF-8: {exc}") from exc
    payload = json.loads(
        text,
        object_pairs_hook=_object_without_duplicates,
        parse_constant=_reject_constant,
    )
    _assert_finite(payload)
    _reject_sensitive_fields(payload)
    return payload


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _exact_keys(value: Any, expected: frozenset[str], location: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{location} must be an object")
    actual = frozenset(value)
    missing = sorted(expected - actual)
    unknown = sorted(actual - expected)
    if missing or unknown:
        raise ValueError(f"{location}: missing={missing} unknown={unknown}")
    return value


def _reviewers(case: dict[str, Any]) -> list[dict[str, Any]]:
    reviewers = case.get("reviewers")
    if not isinstance(reviewers, list):
        return []
    if any(not isinstance(item, dict) for item in reviewers):
        raise ValueError("reviewer entries must be objects")
    return reviewers


def _eligible_approvals(case: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        reviewer
        for reviewer in _reviewers(case)
        if all(
            reviewer.get(field) is True
            for field in ("qualified", "appointed", "accepted", "conflict_clear")
        )
        and reviewer.get("disposition") in APPROVING_DISPOSITIONS
    ]


def evaluate_base(case: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    """Project one base case without consulting its expected result."""
    if case.get("superseded") is True:
        return {
            "state": "SUPERSEDED_REVIEW",
            "reason_codes": [],
            "authority_effect": "none",
        }
    if case.get("appeal_status") == "PENDING":
        return {
            "state": "APPEAL_REVIEW_PENDING",
            "reason_codes": [],
            "authority_effect": "none",
        }

    reasons: set[str] = set()
    if case.get("source_exact") is not True or case.get("policy_exact") is not True:
        reasons.add("MISSING_EXACT_SOURCE_OR_POLICY")

    reviewers = _reviewers(case)
    required_classes = set(policy.get("required_classes", []))
    present_classes = {item.get("reviewer_class") for item in reviewers}
    if not required_classes.issubset(present_classes):
        reasons.add("INCOMPLETE_REVIEW_CLASS_COVERAGE")

    reviewer_by_id: dict[str, dict[str, Any]] = {}
    for reviewer in reviewers:
        reviewer_id = reviewer.get("reviewer_id")
        if isinstance(reviewer_id, str):
            if reviewer_id in reviewer_by_id:
                raise ValueError(f"duplicate reviewer_id: {reviewer_id}")
            reviewer_by_id[reviewer_id] = reviewer
        if reviewer.get("qualified") is not True:
            reasons.add("STALE_OR_UNQUALIFIED_REVIEWER")
        if reviewer.get("appointed") is not True or reviewer.get("accepted") is not True:
            reasons.add("MISSING_APPOINTMENT_OR_ACCEPTANCE")
        if reviewer.get("conflict_clear") is not True:
            reasons.add("UNRESOLVED_CONFLICT_OR_RECUSAL")
        roles = set(reviewer.get("roles") or [])
        if "author" in roles and reviewer.get("reviewer_class") == "architecture":
            reasons.add("SELF_REVIEW")

    for reviewer_id in case.get("claimed_counted_reviewers") or []:
        disposition = reviewer_by_id.get(reviewer_id, {}).get("disposition")
        if disposition == "ABSTAIN":
            reasons.add("ABSTENTION_COUNTED_AS_APPROVAL")
        elif disposition == "RECUSE":
            reasons.add("RECUSAL_COUNTED_AS_APPROVAL")

    approvals = _eligible_approvals(case)
    minimum_approvals = policy.get("minimum_approvals")
    minimum_groups = policy.get("minimum_independent_groups")
    if type(minimum_approvals) is not int or type(minimum_groups) is not int:
        raise ValueError("policy minimums must be integers")
    if len(approvals) < minimum_approvals:
        reasons.add("QUORUM_NOT_MET")
    groups = {
        reviewer.get("independence_group")
        for reviewer in approvals
        if reviewer.get("independence_group")
    }
    if len(groups) < minimum_groups:
        reasons.add("INDEPENDENCE_VIOLATION")

    if case.get("dissent_required") is True and case.get("dissent_preserved") is not True:
        reasons.add("DISSENT_NOT_PRESERVED")
    if case.get("decision_record_present") is True:
        reasons.add("REVIEW_PROMOTED_TO_DECISION")

    return {
        "state": "REVIEW_INCOMPLETE" if reasons else "REVIEW_COMPLETE_PENDING_DECISION",
        "reason_codes": sorted(reasons),
        "authority_effect": "none",
    }


def validate_base(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("base top level must be an object")
    if payload.get("profile_id") != "qso.architecture-review-quorum.synthetic.v1":
        raise ValueError("unexpected base profile_id")
    if payload.get("profile_version") != "1.0.0":
        raise ValueError("unexpected base profile_version")
    if payload.get("status") != "synthetic_conformance_only":
        raise ValueError("unexpected base status")
    if payload.get("authority_effect") != "none":
        raise ValueError("base authority_effect must be none")

    policy = payload.get("policy")
    cases = payload.get("cases")
    if not isinstance(policy, dict) or not isinstance(cases, list):
        raise ValueError("base must contain policy object and cases array")
    if len(cases) != 12:
        raise ValueError("base must contain exactly twelve cases")

    seen_case_ids: set[str] = set()
    reports: list[dict[str, Any]] = []
    mismatches: list[dict[str, Any]] = []
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            raise ValueError(f"base.cases[{index}] must be an object")
        case_id = case.get("case_id")
        if not isinstance(case_id, str) or not case_id or case_id in seen_case_ids:
            raise ValueError("base case_id values must be unique non-empty strings")
        seen_case_ids.add(case_id)
        expected = case.get("expected")
        if not isinstance(expected, dict):
            raise ValueError(f"{case_id}.expected must be an object")
        observed = evaluate_base(case, policy)
        normalized_expected = {
            "state": expected.get("state"),
            "reason_codes": sorted(expected.get("reason_codes") or []),
            "authority_effect": expected.get("authority_effect"),
        }
        if observed != normalized_expected:
            mismatches.append(
                {"case_id": case_id, "expected": normalized_expected, "observed": observed}
            )
        reports.append({"case_id": case_id, **observed})

    digest = canonical_sha256(payload)
    return {
        "profile_id": payload["profile_id"],
        "case_count": len(cases),
        "canonical_payload_sha256": digest,
        "canonical_payload_matches": digest == BASE_CANONICAL_SHA256,
        "mismatches": mismatches,
        "cases": reports,
        "result": "PASS" if not mismatches and digest == BASE_CANONICAL_SHA256 else "FAIL",
        "authority_effect": "none",
    }


def evaluate_extension(facts: dict[str, bool]) -> tuple[str, list[str]]:
    conditions = (
        (not facts["class_coverage_complete"], "INCOMPLETE_REVIEW_CLASS_COVERAGE"),
        (not facts["common_control_disclosed"], "UNDISCLOSED_COMMON_CONTROL"),
        (
            not facts["conflicts_and_recusals_resolved"],
            "UNRESOLVED_CONFLICT_OR_RECUSAL",
        ),
        (facts["incompatible_role_double_count"], "INCOMPATIBLE_ROLE_DOUBLE_COUNT"),
        (
            facts["appeal_present"] and not facts["appeal_authorized_and_current"],
            "UNAUTHORIZED_OR_EXPIRED_APPEAL",
        ),
        (
            facts["appeal_present"]
            and not facts["appeal_panel_complete_and_independent"],
            "INCOMPLETE_OR_CONFLICTED_APPEAL_PANEL",
        ),
        (
            facts["emergency_review_present"] and not facts["emergency_scope_bounded"],
            "EMERGENCY_SCOPE_BROADENING",
        ),
        (
            facts["superseded"] and not facts["dependent_findings_invalidated"],
            "STALE_REVIEW_AFTER_SUPERSESSION",
        ),
    )
    active = {reason for condition, reason in conditions if condition}
    reasons = [reason for reason in EXTENSION_REASON_ORDER if reason in active]
    if not reasons:
        return "COVERAGE_EXTENSION_CLEAR", reasons
    appeal_reasons = {
        "UNAUTHORIZED_OR_EXPIRED_APPEAL",
        "INCOMPLETE_OR_CONFLICTED_APPEAL_PANEL",
    }
    if set(reasons).issubset(appeal_reasons):
        return "APPEAL_BLOCKED", reasons
    return "REVIEW_INCOMPLETE", reasons


def validate_extension(payload: Any) -> dict[str, Any]:
    corpus = _exact_keys(payload, EXTENSION_TOP_KEYS, "extension")
    if corpus["schema"] != "qso.architecture-review-quorum.coverage-extension.corpus.v1":
        raise ValueError("unexpected extension schema")
    if corpus["profile_version"] != "1.0.0":
        raise ValueError("unexpected extension profile_version")
    if corpus["data_class"] != "synthetic_only_non_operational":
        raise ValueError("unexpected extension data_class")

    linkage = _exact_keys(corpus["extends"], EXTENSION_LINK_KEYS, "extension.extends")
    if linkage != {
        "fixture": "fixtures/architecture-review-quorum-v1.json",
        "base_case_count": 12,
        "base_fixture_generation": "historical-byte-preserved",
        "contract": "docs/architecture-review-quorum-contract-v0.yaml",
    }:
        raise ValueError("extension linkage drift")

    defaults = _exact_keys(corpus["defaults"], EXTENSION_FACT_KEYS, "extension.defaults")
    if any(type(value) is not bool for value in defaults.values()):
        raise ValueError("extension defaults must be Boolean")

    cases = corpus["cases"]
    if not isinstance(cases, list) or len(cases) != 9:
        raise ValueError("extension must contain exactly nine cases")

    reports: list[dict[str, Any]] = []
    mismatches: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    covered_reasons: set[str] = set()
    covered_dispositions: set[str] = set()
    for index, item in enumerate(cases):
        case = _exact_keys(
            item,
            frozenset({"id", "overrides", "expected"}),
            f"extension.cases[{index}]",
        )
        case_id = case["id"]
        if not isinstance(case_id, str) or not case_id or case_id in seen_ids:
            raise ValueError("extension case ids must be unique non-empty strings")
        seen_ids.add(case_id)
        overrides = case["overrides"]
        if not isinstance(overrides, dict):
            raise ValueError(f"{case_id}.overrides must be an object")
        unknown_overrides = sorted(set(overrides) - set(EXTENSION_FACT_KEYS))
        if unknown_overrides:
            raise ValueError(f"{case_id}: unknown overrides {unknown_overrides}")
        if any(type(value) is not bool for value in overrides.values()):
            raise ValueError(f"{case_id}: override values must be Boolean")

        expected = _exact_keys(
            case["expected"], frozenset({"disposition", "reasons"}), f"{case_id}.expected"
        )
        disposition = expected["disposition"]
        reasons = expected["reasons"]
        if disposition not in EXTENSION_DISPOSITIONS:
            raise ValueError(f"{case_id}: unsupported disposition")
        if (
            not isinstance(reasons, list)
            or len(reasons) != len(set(reasons))
            or any(reason not in EXTENSION_REASON_ORDER for reason in reasons)
        ):
            raise ValueError(f"{case_id}: invalid reason list")

        facts = dict(defaults)
        facts.update(overrides)
        observed_disposition, observed_reasons = evaluate_extension(facts)
        observed = {
            "disposition": observed_disposition,
            "reasons": observed_reasons,
        }
        if observed != expected:
            mismatches.append({"case_id": case_id, "expected": expected, "observed": observed})
        reports.append({"case_id": case_id, **observed})
        covered_reasons.update(reasons)
        covered_dispositions.add(disposition)

    if covered_reasons != set(EXTENSION_REASON_ORDER):
        raise ValueError("extension does not cover every required reason code")
    if covered_dispositions != set(EXTENSION_DISPOSITIONS):
        raise ValueError("extension does not cover every disposition")

    digest = canonical_sha256(corpus)
    return {
        "profile_id": corpus["schema"],
        "case_count": len(cases),
        "canonical_payload_sha256": digest,
        "canonical_payload_matches": digest == EXTENSION_CANONICAL_SHA256,
        "mismatches": mismatches,
        "cases": reports,
        "result": "PASS"
        if not mismatches and digest == EXTENSION_CANONICAL_SHA256
        else "FAIL",
        "authority_effect": "none",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--extension", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    base = validate_base(load_strict(args.base))
    extension = validate_extension(load_strict(args.extension))
    report = {
        "schema": "repo1.architecture-review-quorum.validation.v1",
        "consumer": "aevespers2/1",
        "base": base,
        "extension": extension,
        "combined_case_count": base["case_count"] + extension["case_count"],
        "result": "PASS"
        if base["result"] == extension["result"] == "PASS"
        else "FAIL",
        "reviewer_appointment": False,
        "real_quorum": False,
        "architecture_decision": False,
        "activation_authority": False,
        "operational_authority": False,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
