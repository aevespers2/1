#!/usr/bin/env python3
"""Independently validate the synthetic repository-local maintainer corpus.

This consumer intentionally does not import the producer validator. Passing the
corpus proves only deterministic agreement for the recorded synthetic fixture;
it grants no appointment, permission, merge, release, publication, or runtime
authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

MAX_BYTES = 1_000_000
TOP_FIELDS = frozenset(
    {"fixture_id", "fixture_version", "status", "authority_effect", "profile_id", "cases"}
)
CASE_FIELDS = frozenset(
    {"case_id", "controls", "expected_disposition", "expected_reasons"}
)
CONTROL_FIELDS = frozenset(
    {
        "policy_current",
        "designation",
        "acceptance",
        "term_current",
        "exact_repo_scope",
        "packet_complete",
        "allowed_surface",
        "independent_review",
        "rollback",
        "self_appointment",
        "secret_access",
        "cross_repo",
        "protected_policy",
        "restored_self_certified",
        "required_consumer_reachable",
    }
)
REQUIRED_CASES = frozenset(
    {
        "bounded_documentation_packet",
        "missing_designation",
        "missing_acceptance",
        "expired_term",
        "self_appointment",
        "administrator_permission_only",
        "secret_or_credential_access",
        "cross_repository_scope",
        "incomplete_change_packet",
        "missing_rollback",
        "missing_independent_review",
        "emergency_scope_broadening",
        "protected_policy_mutation",
        "self_certified_restoration",
        "unreachable_required_consumer",
        "stale_policy_generation",
    }
)
REASONS = frozenset(
    {
        "STALE_POLICY_GENERATION",
        "MISSING_DESIGNATION",
        "MISSING_ACCEPTANCE",
        "EXPIRED_OR_MISSING_TERM",
        "REPOSITORY_SCOPE_MISMATCH",
        "INCOMPLETE_CHANGE_PACKET",
        "PROHIBITED_OR_UNAPPROVED_SURFACE",
        "INDEPENDENT_REVIEW_MISSING",
        "ROLLBACK_OR_QUARANTINE_MISSING",
        "SELF_APPOINTMENT",
        "SECRET_OR_CREDENTIAL_ACCESS",
        "CROSS_REPOSITORY_AUTHORITY_CLAIM",
        "PROTECTED_POLICY_MUTATION",
        "SELF_CERTIFIED_RESTORATION",
        "REQUIRED_CONSUMER_UNREACHABLE",
    }
)
PROHIBITED_FIELDS = frozenset(
    {
        "private_key",
        "secret_key",
        "access_token",
        "credential_value",
        "password",
        "biometric_template",
        "raw_biometric",
        "government_identifier",
        "legal_identity_document",
        "live_permission_binding",
        "live_registry_endpoint",
    }
)


class FixtureError(ValueError):
    """Raised for strict parsing or fixture-shape failures."""


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


def derive_reasons(controls: dict[str, bool]) -> set[str]:
    checks = (
        (not controls["policy_current"], "STALE_POLICY_GENERATION"),
        (not controls["designation"], "MISSING_DESIGNATION"),
        (not controls["acceptance"], "MISSING_ACCEPTANCE"),
        (not controls["term_current"], "EXPIRED_OR_MISSING_TERM"),
        (not controls["exact_repo_scope"], "REPOSITORY_SCOPE_MISMATCH"),
        (not controls["packet_complete"], "INCOMPLETE_CHANGE_PACKET"),
        (not controls["allowed_surface"], "PROHIBITED_OR_UNAPPROVED_SURFACE"),
        (not controls["independent_review"], "INDEPENDENT_REVIEW_MISSING"),
        (not controls["rollback"], "ROLLBACK_OR_QUARANTINE_MISSING"),
        (controls["self_appointment"], "SELF_APPOINTMENT"),
        (controls["secret_access"], "SECRET_OR_CREDENTIAL_ACCESS"),
        (controls["cross_repo"], "CROSS_REPOSITORY_AUTHORITY_CLAIM"),
        (controls["protected_policy"], "PROTECTED_POLICY_MUTATION"),
        (controls["restored_self_certified"], "SELF_CERTIFIED_RESTORATION"),
        (
            not controls["required_consumer_reachable"],
            "REQUIRED_CONSUMER_UNREACHABLE",
        ),
    )
    return {reason for triggered, reason in checks if triggered}


def validate_case(case: dict[str, Any]) -> list[str]:
    errors = _field_errors(case, CASE_FIELDS, "case")
    raw_case_id = case.get("case_id")
    case_id = raw_case_id if isinstance(raw_case_id, str) and raw_case_id else "<unknown>"
    if case_id == "<unknown>":
        errors.append("case_id must be a non-empty string")

    controls = case.get("controls")
    derived: set[str] = set()
    if not isinstance(controls, dict):
        errors.append(f"{case_id}: controls must be an object")
    else:
        errors.extend(_field_errors(controls, CONTROL_FIELDS, f"{case_id}: controls"))
        non_boolean = sorted(key for key, value in controls.items() if type(value) is not bool)
        if non_boolean:
            errors.append(f"{case_id}: controls must be boolean: {non_boolean}")
        elif set(controls) == CONTROL_FIELDS:
            derived = derive_reasons(controls)

    raw_reasons = case.get("expected_reasons")
    expected: set[str] = set()
    if not isinstance(raw_reasons, list):
        errors.append(f"{case_id}: expected_reasons must be a list")
    else:
        invalid = sorted(
            value for value in raw_reasons if not isinstance(value, str) or value not in REASONS
        )
        if invalid:
            errors.append(f"{case_id}: invalid expected_reasons {invalid}")
        if len(raw_reasons) != len(set(raw_reasons)):
            errors.append(f"{case_id}: expected_reasons must be unique")
        expected = {value for value in raw_reasons if isinstance(value, str)}

    if derived != expected:
        errors.append(
            f"{case_id}: expected reasons {sorted(expected)} "
            f"do not match independently derived {sorted(derived)}"
        )

    independently_expected = "REVIEW_ELIGIBLE" if not derived else "BLOCKED"
    if case.get("expected_disposition") != independently_expected:
        errors.append(
            f"{case_id}: disposition {case.get('expected_disposition')!r} "
            f"does not match independently derived {independently_expected!r}"
        )
    return errors


def validate_fixture(document: dict[str, Any]) -> list[str]:
    errors = _field_errors(document, TOP_FIELDS, "fixture")
    if document.get("fixture_id") != "qso.repository-local-maintainer-conformance":
        errors.append("fixture_id must be qso.repository-local-maintainer-conformance")
    if document.get("fixture_version") != "1.0.0-synthetic":
        errors.append("fixture_version must be 1.0.0-synthetic")
    if document.get("status") != "synthetic-only":
        errors.append("status must be synthetic-only")
    if document.get("authority_effect") != "none":
        errors.append("authority_effect must be none")
    if document.get("profile_id") != "qso.repository-local-maintainer-boundary":
        errors.append("profile_id must be qso.repository-local-maintainer-boundary")

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
        default=Path("fixtures/repository-local-maintainer-v1.json"),
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
        "positive_disposition": "REVIEW_ELIGIBLE",
        "positive_disposition_authority_effect": "none",
    }
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    print(rendered, end="")
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered, encoding="utf-8")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
