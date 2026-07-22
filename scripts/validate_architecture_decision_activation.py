#!/usr/bin/env python3
"""Independent consumer for the QSO Field architecture-decision corpus.

This validator intentionally does not import the producer implementation. It
parses the immutable synthetic fixture, derives each disposition from a
separate rule table, and fails closed on schema, type, coverage, or semantic
drift.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Callable

SCHEMA = "qso.architecture-decision-activation.corpus.v1"
PROFILE_VERSION = "1.0.0"
DATA_CLASS = "synthetic_only_non_operational"
EXPECTED_CASE_COUNT = 15

TOP_KEYS = frozenset({"schema", "profile_version", "data_class", "cases"})
CASE_KEYS = frozenset({"id", "facts", "expected"})
EXPECTED_KEYS = frozenset({"disposition", "reasons"})
FACT_KEYS = frozenset(
    {
        "exact_source_bound",
        "evidence_current",
        "reviews_complete",
        "conflicts_resolved",
        "self_approved",
        "dissent_preserved",
        "scope_bounded",
        "conditions_satisfied",
        "approval_present",
        "approval_current",
        "activation_present",
        "activation_scope_subset",
        "activation_authorized",
        "consumer_registry_complete",
        "propagation_complete",
        "superseded_or_withdrawn",
        "dependent_activation_invalidated",
        "rollback_required",
        "rollback_checkpoint_present",
        "restored_state_verified",
    }
)

REASON_ORDER = (
    "MISSING_EXACT_SOURCE",
    "EXPIRED_OR_MISSING_EVIDENCE",
    "INCOMPLETE_REQUIRED_REVIEW",
    "UNRESOLVED_CONFLICT_OR_RECUSAL",
    "SELF_APPROVAL",
    "DISSENT_NOT_PRESERVED",
    "UNBOUNDED_SCOPE",
    "UNSATISFIED_CONDITIONS",
    "EXPIRED_APPROVAL",
    "APPROVAL_PROMOTED_TO_ACTIVATION",
    "ACTIVATION_SCOPE_BROADENING",
    "UNAUTHORIZED_ACTIVATION",
    "INCOMPLETE_CONSUMER_REGISTRY",
    "PARTIAL_OR_UNREACHABLE_PROPAGATION",
    "STALE_ACTIVATION_AFTER_SUPERSESSION",
    "MISSING_ROLLBACK_CHECKPOINT",
    "UNVERIFIED_RESTORED_STATE",
)
ALLOWED_REASONS = frozenset(REASON_ORDER)
ALLOWED_DISPOSITIONS = frozenset(
    {
        "REVIEW_COMPLETE_PENDING_DECISION",
        "APPROVED_NOT_ACTIVATED",
        "ACTIVATED_AT_RECORDED_SCOPE",
        "ACTIVATION_BLOCKED",
        "PARTIAL_OR_UNKNOWN",
        "WITHDRAWN_OR_SUPERSEDED",
    }
)
PARTIAL_ONLY = frozenset(
    {"INCOMPLETE_CONSUMER_REGISTRY", "PARTIAL_OR_UNREACHABLE_PROPAGATION"}
)
PROHIBITED_KEY_FRAGMENTS = (
    "secret",
    "private_key",
    "credential",
    "password",
    "token",
    "biometric",
    "iris",
)

Predicate = Callable[[dict[str, bool]], bool]
RULES: tuple[tuple[str, Predicate], ...] = (
    ("MISSING_EXACT_SOURCE", lambda f: not f["exact_source_bound"]),
    ("EXPIRED_OR_MISSING_EVIDENCE", lambda f: not f["evidence_current"]),
    ("INCOMPLETE_REQUIRED_REVIEW", lambda f: not f["reviews_complete"]),
    ("UNRESOLVED_CONFLICT_OR_RECUSAL", lambda f: not f["conflicts_resolved"]),
    ("SELF_APPROVAL", lambda f: f["self_approved"]),
    ("DISSENT_NOT_PRESERVED", lambda f: not f["dissent_preserved"]),
    ("UNBOUNDED_SCOPE", lambda f: not f["scope_bounded"]),
    (
        "UNSATISFIED_CONDITIONS",
        lambda f: f["approval_present"] and not f["conditions_satisfied"],
    ),
    (
        "EXPIRED_APPROVAL",
        lambda f: f["approval_present"]
        and not f["approval_current"]
        and not f["superseded_or_withdrawn"],
    ),
    (
        "APPROVAL_PROMOTED_TO_ACTIVATION",
        lambda f: f["activation_present"] and not f["approval_present"],
    ),
    (
        "ACTIVATION_SCOPE_BROADENING",
        lambda f: f["activation_present"] and not f["activation_scope_subset"],
    ),
    (
        "UNAUTHORIZED_ACTIVATION",
        lambda f: f["activation_present"] and not f["activation_authorized"],
    ),
    (
        "INCOMPLETE_CONSUMER_REGISTRY",
        lambda f: f["activation_present"] and not f["consumer_registry_complete"],
    ),
    (
        "PARTIAL_OR_UNREACHABLE_PROPAGATION",
        lambda f: f["activation_present"] and not f["propagation_complete"],
    ),
    (
        "STALE_ACTIVATION_AFTER_SUPERSESSION",
        lambda f: f["superseded_or_withdrawn"]
        and f["activation_present"]
        and not f["dependent_activation_invalidated"],
    ),
    (
        "MISSING_ROLLBACK_CHECKPOINT",
        lambda f: f["rollback_required"] and not f["rollback_checkpoint_present"],
    ),
    (
        "UNVERIFIED_RESTORED_STATE",
        lambda f: f["rollback_required"] and not f["restored_state_verified"],
    ),
)


def _object_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_nonfinite_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON value is prohibited: {value}")


def strict_load(path: Path) -> Any:
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ValueError(f"fixture is not strict UTF-8: {exc}") from exc
    payload = json.loads(
        text,
        object_pairs_hook=_object_without_duplicates,
        parse_constant=_reject_nonfinite_constant,
    )
    _assert_finite(payload)
    return payload


def _assert_finite(value: Any, location: str = "root") -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"non-finite number at {location}")
    if isinstance(value, dict):
        for key, child in value.items():
            _assert_finite(child, f"{location}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _assert_finite(child, f"{location}[{index}]")


def _reject_sensitive_keys(value: Any, location: str = "root") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            lowered = key.lower()
            if any(fragment in lowered for fragment in PROHIBITED_KEY_FRAGMENTS):
                raise ValueError(f"prohibited sensitive field at {location}.{key}")
            _reject_sensitive_keys(child, f"{location}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_sensitive_keys(child, f"{location}[{index}]")


def _require_exact_keys(value: dict[str, Any], expected: frozenset[str], location: str) -> None:
    actual = frozenset(value)
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing or extra:
        raise ValueError(f"{location}: missing={missing} unknown={extra}")


def evaluate(facts: dict[str, bool]) -> tuple[str, list[str]]:
    """Derive one disposition without consulting fixture expectations."""
    reasons = [reason for reason, predicate in RULES if predicate(facts)]

    if not reasons and facts["superseded_or_withdrawn"]:
        return "WITHDRAWN_OR_SUPERSEDED", []
    if reasons:
        if set(reasons).issubset(PARTIAL_ONLY):
            return "PARTIAL_OR_UNKNOWN", reasons
        return "ACTIVATION_BLOCKED", reasons
    if not facts["approval_present"]:
        return "REVIEW_COMPLETE_PENDING_DECISION", []
    if not facts["activation_present"]:
        return "APPROVED_NOT_ACTIVATED", []
    return "ACTIVATED_AT_RECORDED_SCOPE", []


def validate_case(case: Any, location: str = "case") -> tuple[str, list[str]]:
    if not isinstance(case, dict):
        raise ValueError(f"{location} must be an object")
    _require_exact_keys(case, CASE_KEYS, location)

    case_id = case["id"]
    if not isinstance(case_id, str) or not case_id.strip():
        raise ValueError(f"{location}.id must be a non-empty string")

    facts = case["facts"]
    if not isinstance(facts, dict):
        raise ValueError(f"{location}.facts must be an object")
    _require_exact_keys(facts, FACT_KEYS, f"{location}.facts")
    for key, value in facts.items():
        if type(value) is not bool:
            raise ValueError(f"{location}.facts.{key} must be Boolean")

    expected = case["expected"]
    if not isinstance(expected, dict):
        raise ValueError(f"{location}.expected must be an object")
    _require_exact_keys(expected, EXPECTED_KEYS, f"{location}.expected")

    disposition = expected["disposition"]
    reasons = expected["reasons"]
    if disposition not in ALLOWED_DISPOSITIONS:
        raise ValueError(f"{location}: unsupported disposition {disposition!r}")
    if not isinstance(reasons, list) or any(type(reason) is not str for reason in reasons):
        raise ValueError(f"{location}: reasons must be a list of strings")
    if len(reasons) != len(set(reasons)):
        raise ValueError(f"{location}: duplicate reasons are prohibited")
    if any(reason not in ALLOWED_REASONS for reason in reasons):
        raise ValueError(f"{location}: unknown reason code")
    if reasons != [reason for reason in REASON_ORDER if reason in set(reasons)]:
        raise ValueError(f"{location}: reasons are not in canonical order")

    derived = evaluate(facts)
    if derived != (disposition, reasons):
        raise ValueError(
            f"{case_id}: expected {(disposition, reasons)!r}, derived {derived!r}"
        )
    return derived


def validate_payload(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        raise ValueError("top level must be an object")
    _reject_sensitive_keys(payload)
    _require_exact_keys(payload, TOP_KEYS, "root")

    if payload["schema"] != SCHEMA:
        raise ValueError(f"unexpected schema: {payload['schema']!r}")
    if payload["profile_version"] != PROFILE_VERSION:
        raise ValueError(f"unexpected profile version: {payload['profile_version']!r}")
    if payload["data_class"] != DATA_CLASS:
        raise ValueError(f"unexpected data class: {payload['data_class']!r}")

    cases = payload["cases"]
    if not isinstance(cases, list) or len(cases) != EXPECTED_CASE_COUNT:
        raise ValueError(f"cases must contain exactly {EXPECTED_CASE_COUNT} entries")

    reports: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    covered_reasons: set[str] = set()
    covered_dispositions: set[str] = set()

    for index, case in enumerate(cases):
        disposition, reasons = validate_case(case, f"cases[{index}]")
        case_id = case["id"]
        if case_id in seen_ids:
            raise ValueError(f"duplicate case id: {case_id}")
        seen_ids.add(case_id)
        covered_dispositions.add(disposition)
        covered_reasons.update(reasons)
        reports.append({"id": case_id, "disposition": disposition, "reasons": reasons})

    missing_reasons = sorted(ALLOWED_REASONS - covered_reasons)
    if missing_reasons:
        raise ValueError(f"fixture does not cover reason codes: {missing_reasons}")
    missing_dispositions = sorted(ALLOWED_DISPOSITIONS - covered_dispositions)
    if missing_dispositions:
        raise ValueError(f"fixture does not cover dispositions: {missing_dispositions}")
    return reports


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    payload = strict_load(args.fixture)
    cases = validate_payload(payload)
    digest = hashlib.sha256(args.fixture.read_bytes()).hexdigest()
    report = {
        "schema": "repo1.architecture-decision-activation.validation.v1",
        "source_fixture_sha256": digest,
        "case_count": len(cases),
        "disposition_counts": {
            disposition: sum(case["disposition"] == disposition for case in cases)
            for disposition in sorted(ALLOWED_DISPOSITIONS)
        },
        "cases": cases,
        "authority_activated": False,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"validated {len(cases)} independent architecture-decision cases")
    print(f"fixture_sha256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
