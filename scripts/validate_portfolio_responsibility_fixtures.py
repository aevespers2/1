#!/usr/bin/env python3
"""Independently validate the synthetic responsibility/custody/vacancy corpus."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

MAX_BYTES = 1_000_000
TOP_FIELDS = frozenset({"fixture_id", "fixture_version", "status", "authority_effect", "cases"})
CASE_FIELDS = frozenset(
    {"case_id", "description", "flags", "expected_disposition", "expected_reason_codes"}
)
FLAG_FIELDS = frozenset(
    {
        "critical_role_filled",
        "self_appointment",
        "neutral_custody",
        "sole_operational_steward",
        "appointment_record",
        "acceptance_record",
        "term_current",
        "credential_binding_separate",
        "conflict_present",
        "recusal_complete",
        "deputy_activation_valid",
        "delegation_narrowing",
        "lifecycle_owners_complete",
        "hidden_inheritance",
        "rollback_target_complete",
        "propagation_complete",
    }
)
REQUIRED_CASES = frozenset(
    {
        "valid-separated-assignment",
        "vacant-critical-role",
        "self-appointment",
        "self-authorizing-custody",
        "missing-appointment-record",
        "missing-acceptance-record",
        "expired-appointment",
        "credential-role-conflation",
        "unresolved-conflict",
        "invalid-deputy-activation",
        "authority-broadening-delegation",
        "incomplete-lifecycle-ownership",
        "hidden-vacancy-inheritance",
        "missing-rollback-target",
        "propagation-gap",
    }
)
REASONS = frozenset(
    {
        "UNASSIGNED_CRITICAL_RESPONSIBILITY",
        "SELF_APPOINTMENT",
        "SELF_AUTHORIZING_CUSTODY",
        "MISSING_APPOINTMENT_RECORD",
        "MISSING_ACCEPTANCE_RECORD",
        "EXPIRED_APPOINTMENT",
        "CREDENTIAL_ROLE_CONFLATION",
        "UNRESOLVED_CONFLICT",
        "INVALID_DEPUTY_ACTIVATION",
        "AUTHORITY_BROADENING_DELEGATION",
        "INCOMPLETE_LIFECYCLE_OWNERSHIP",
        "HIDDEN_VACANCY_INHERITANCE",
        "MISSING_ROLLBACK_TARGET",
        "PROPAGATION_GAP",
    }
)
PROHIBITED_FIELDS = frozenset(
    {
        "private_key",
        "secret",
        "credential",
        "access_token",
        "biometric_template",
        "raw_biometric",
        "government_identifier",
        "legal_identity_document",
        "live_registry_endpoint",
    }
)


class FixtureError(ValueError):
    """Raised for strict parsing or corpus-shape failures."""


def _object_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise FixtureError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_non_finite(token: str) -> None:
    raise FixtureError(f"non-finite JSON number is prohibited: {token}")


def load_fixture(path: Path) -> tuple[dict[str, Any], str]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise FixtureError(f"unable to read fixture: {exc}") from exc
    if len(raw) > MAX_BYTES:
        raise FixtureError(f"fixture exceeds {MAX_BYTES} bytes")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise FixtureError("fixture must be valid UTF-8") from exc
    try:
        document = json.loads(
            text,
            object_pairs_hook=_object_without_duplicates,
            parse_constant=_reject_non_finite,
        )
    except json.JSONDecodeError as exc:
        raise FixtureError(f"invalid JSON: {exc}") from exc
    if not isinstance(document, dict):
        raise FixtureError("fixture root must be an object")
    return document, hashlib.sha256(raw).hexdigest()


def _field_errors(value: dict[str, Any], expected: frozenset[str], label: str) -> list[str]:
    actual = set(value)
    if actual == expected:
        return []
    return [
        f"{label}: field mismatch; missing={sorted(expected - actual)}, "
        f"unknown={sorted(actual - expected)}"
    ]


def _walk_fields(value: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            found.add(str(key).lower())
            found.update(_walk_fields(child))
    elif isinstance(value, list):
        for child in value:
            found.update(_walk_fields(child))
    return found


def derive_reasons(flags: dict[str, bool]) -> set[str]:
    reasons: set[str] = set()
    checks = (
        (not flags["critical_role_filled"], "UNASSIGNED_CRITICAL_RESPONSIBILITY"),
        (flags["self_appointment"], "SELF_APPOINTMENT"),
        (
            not flags["neutral_custody"] and flags["sole_operational_steward"],
            "SELF_AUTHORIZING_CUSTODY",
        ),
        (not flags["appointment_record"], "MISSING_APPOINTMENT_RECORD"),
        (not flags["acceptance_record"], "MISSING_ACCEPTANCE_RECORD"),
        (not flags["term_current"], "EXPIRED_APPOINTMENT"),
        (not flags["credential_binding_separate"], "CREDENTIAL_ROLE_CONFLATION"),
        (flags["conflict_present"] and not flags["recusal_complete"], "UNRESOLVED_CONFLICT"),
        (not flags["deputy_activation_valid"], "INVALID_DEPUTY_ACTIVATION"),
        (not flags["delegation_narrowing"], "AUTHORITY_BROADENING_DELEGATION"),
        (not flags["lifecycle_owners_complete"], "INCOMPLETE_LIFECYCLE_OWNERSHIP"),
        (flags["hidden_inheritance"], "HIDDEN_VACANCY_INHERITANCE"),
        (not flags["rollback_target_complete"], "MISSING_ROLLBACK_TARGET"),
        (not flags["propagation_complete"], "PROPAGATION_GAP"),
    )
    for triggered, reason in checks:
        if triggered:
            reasons.add(reason)
    return reasons


def validate_case(case: dict[str, Any]) -> list[str]:
    errors = _field_errors(case, CASE_FIELDS, "case")
    raw_case_id = case.get("case_id")
    case_id = raw_case_id if isinstance(raw_case_id, str) and raw_case_id else "<unknown>"
    if case_id == "<unknown>":
        errors.append("case_id must be a non-empty string")
    if not isinstance(case.get("description"), str) or not case["description"].strip():
        errors.append(f"{case_id}: description must be a non-empty string")

    flags = case.get("flags")
    derived: set[str] = set()
    if not isinstance(flags, dict):
        errors.append(f"{case_id}: flags must be an object")
    else:
        errors.extend(_field_errors(flags, FLAG_FIELDS, f"{case_id}: flags"))
        non_boolean = sorted(key for key, value in flags.items() if type(value) is not bool)
        if non_boolean:
            errors.append(f"{case_id}: flags must be boolean: {non_boolean}")
        elif set(flags) == FLAG_FIELDS:
            derived = derive_reasons(flags)

    raw_reasons = case.get("expected_reason_codes")
    expected: set[str] = set()
    if not isinstance(raw_reasons, list):
        errors.append(f"{case_id}: expected_reason_codes must be a list")
    else:
        invalid = sorted(
            value for value in raw_reasons if not isinstance(value, str) or value not in REASONS
        )
        if invalid:
            errors.append(f"{case_id}: invalid expected_reason_codes {invalid}")
        if len(raw_reasons) != len(set(raw_reasons)):
            errors.append(f"{case_id}: expected_reason_codes must be unique")
        expected = {value for value in raw_reasons if isinstance(value, str)}

    if derived != expected:
        errors.append(
            f"{case_id}: expected reasons {sorted(expected)} "
            f"do not match independently derived {sorted(derived)}"
        )
    independently_expected = "ACCEPTED" if not derived else "BLOCKED"
    if case.get("expected_disposition") != independently_expected:
        errors.append(
            f"{case_id}: disposition {case.get('expected_disposition')!r} "
            f"does not match independently derived {independently_expected!r}"
        )
    return errors


def validate_fixture(document: dict[str, Any]) -> list[str]:
    errors = _field_errors(document, TOP_FIELDS, "fixture")
    if document.get("fixture_id") != "qso.portfolio-responsibility-custody.v1":
        errors.append("fixture_id must be qso.portfolio-responsibility-custody.v1")
    if document.get("fixture_version") != 1:
        errors.append("fixture_version must be 1")
    if document.get("status") != "synthetic-only":
        errors.append("status must be synthetic-only")
    if document.get("authority_effect") != "none":
        errors.append("authority_effect must be none")

    prohibited = sorted(_walk_fields(document) & PROHIBITED_FIELDS)
    if prohibited:
        errors.append(f"prohibited fields present: {prohibited}")

    cases = document.get("cases")
    if not isinstance(cases, list):
        return errors + ["cases must be a list"]

    case_ids: list[str] = []
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            errors.append(f"case[{index}] must be an object")
            continue
        if isinstance(case.get("case_id"), str):
            case_ids.append(case["case_id"])
        errors.extend(validate_case(case))
    if len(case_ids) != len(set(case_ids)):
        errors.append("case_id values must be unique")
    actual = set(case_ids)
    if actual != REQUIRED_CASES:
        errors.append(
            f"case coverage mismatch; missing={sorted(REQUIRED_CASES - actual)}, "
            f"extra={sorted(actual - REQUIRED_CASES)}"
        )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--fixture",
        type=Path,
        default=Path("fixtures/portfolio-responsibility-custody-v1.json"),
    )
    parser.add_argument("--expected-sha256")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    errors: list[str] = []
    actual_sha256: str | None = None
    try:
        document, actual_sha256 = load_fixture(args.fixture)
        if args.expected_sha256 and actual_sha256 != args.expected_sha256:
            errors.append(
                f"fixture SHA-256 mismatch: expected {args.expected_sha256}, got {actual_sha256}"
            )
        errors.extend(validate_fixture(document))
    except FixtureError as exc:
        errors.append(str(exc))

    report = {
        "fixture": str(args.fixture),
        "sha256": actual_sha256,
        "valid": not errors,
        "error_count": len(errors),
        "errors": errors,
        "strict_json": True,
        "independent_implementation": True,
        "synthetic_only": True,
        "authority_effect": "none",
    }
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    print(rendered, end="")
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered, encoding="utf-8")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
