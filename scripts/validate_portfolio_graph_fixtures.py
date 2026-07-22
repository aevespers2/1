#!/usr/bin/env python3
"""Independently validate the synthetic portfolio contract-graph corpus.

This implementation intentionally does not import the producer-side validator.
It treats the fixture as inert conformance data and grants no operational authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

MAX_FIXTURE_BYTES = 1_000_000
TOP_FIELDS = frozenset(
    {"fixture_id", "fixture_version", "status", "authority_effect", "cases"}
)
CASE_FIELDS = frozenset(
    {
        "case_id",
        "description",
        "nodes",
        "edges",
        "flags",
        "expected_disposition",
        "expected_reason_codes",
    }
)
FLAG_FIELDS = frozenset(
    {
        "owners_assigned",
        "exact_contracts",
        "path_agreement",
        "authority_broadening",
        "dependency_closure_complete",
        "correction_closure_complete",
        "recovery_epochs_equal",
        "rollback_route_complete",
        "required_edge_missing",
        "neutral_custody",
        "sole_operational_steward",
        "independent_cycle_break",
        "output_route_complete",
        "required_node_reachable",
        "optional",
        "retirement_route_complete",
        "evidence_current",
    }
)
REQUIRED_CASES = frozenset(
    {
        "valid-narrowing-linear-chain",
        "missing-interface",
        "self-authorizing-contract",
        "direct-composed-path-divergence",
        "cycle-authority-amplification",
        "orphaned-output",
        "incomplete-dependency-closure",
        "correction-propagation-gap",
        "unreachable-required-node",
        "split-recovery-epoch",
        "rollback-dead-end",
        "bounded-optional-adapter",
    }
)
ALLOWED_DISPOSITIONS = frozenset({"ACCEPTED", "PARTIAL", "BLOCKED"})
ALLOWED_REASON_CODES = frozenset(
    {
        "MISSING_INTERFACE",
        "UNASSIGNED_OWNER",
        "SELF_AUTHORIZING_CONTRACT",
        "CONTRACT_ALIAS_COLLISION",
        "PATH_DIVERGENCE",
        "AUTHORITY_AMPLIFICATION",
        "ORPHANED_OUTPUT",
        "INCOMPLETE_DEPENDENCY_CLOSURE",
        "CORRECTION_PROPAGATION_GAP",
        "UNREACHABLE_REQUIRED_NODE",
        "SPLIT_RECOVERY_EPOCH",
        "ROLLBACK_DEAD_END",
        "CYCLE_WITHOUT_BREAK_AUTHORITY",
        "STALE_EVIDENCE_EDGE",
    }
)
PROHIBITED_FIELDS = frozenset(
    {
        "private_key",
        "secret",
        "credential",
        "biometric_template",
        "raw_biometric",
        "access_token",
        "live_registry_endpoint",
    }
)
SIMPLE_FLAG_REASONS = {
    ("required_edge_missing", True): "MISSING_INTERFACE",
    ("owners_assigned", False): "UNASSIGNED_OWNER",
    ("path_agreement", False): "PATH_DIVERGENCE",
    ("authority_broadening", True): "AUTHORITY_AMPLIFICATION",
    ("output_route_complete", False): "ORPHANED_OUTPUT",
    ("dependency_closure_complete", False): "INCOMPLETE_DEPENDENCY_CLOSURE",
    ("correction_closure_complete", False): "CORRECTION_PROPAGATION_GAP",
    ("required_node_reachable", False): "UNREACHABLE_REQUIRED_NODE",
    ("recovery_epochs_equal", False): "SPLIT_RECOVERY_EPOCH",
    ("rollback_route_complete", False): "ROLLBACK_DEAD_END",
    ("evidence_current", False): "STALE_EVIDENCE_EDGE",
}


class FixtureError(ValueError):
    """Raised when strict parsing or validation fails."""


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
    if len(raw) > MAX_FIXTURE_BYTES:
        raise FixtureError(f"fixture exceeds {MAX_FIXTURE_BYTES} bytes")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise FixtureError("fixture must be valid UTF-8") from exc
    try:
        value = json.loads(
            text,
            object_pairs_hook=_object_without_duplicates,
            parse_constant=_reject_non_finite,
        )
    except json.JSONDecodeError as exc:
        raise FixtureError(f"invalid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise FixtureError("fixture root must be an object")
    return value, hashlib.sha256(raw).hexdigest()


def _field_set_errors(
    value: dict[str, Any], expected: frozenset[str], label: str
) -> list[str]:
    actual = set(value)
    if actual == expected:
        return []
    return [
        f"{label}: field mismatch; missing={sorted(expected - actual)}, "
        f"unknown={sorted(actual - expected)}"
    ]


def _walk_field_names(value: Any) -> set[str]:
    names: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            names.add(str(key).lower())
            names.update(_walk_field_names(child))
    elif isinstance(value, list):
        for child in value:
            names.update(_walk_field_names(child))
    return names


def _derived_reasons(case_id: str, flags: Any) -> set[str]:
    if not isinstance(flags, dict):
        raise FixtureError(f"{case_id}: flags must be an object")
    unknown = sorted(set(flags) - FLAG_FIELDS)
    if unknown:
        raise FixtureError(f"{case_id}: unknown flags {unknown}")
    non_boolean = sorted(key for key, value in flags.items() if type(value) is not bool)
    if non_boolean:
        raise FixtureError(f"{case_id}: flags must be boolean: {non_boolean}")

    reasons = {
        reason
        for (flag, trigger), reason in SIMPLE_FLAG_REASONS.items()
        if flags.get(flag) is trigger
    }
    if flags.get("neutral_custody") is False and flags.get(
        "sole_operational_steward"
    ) is True:
        reasons.add("SELF_AUTHORIZING_CONTRACT")
    if flags.get("authority_broadening") is True and flags.get(
        "independent_cycle_break"
    ) is False:
        reasons.add("CYCLE_WITHOUT_BREAK_AUTHORITY")
    return reasons


def _expected_disposition(reasons: set[str]) -> str:
    if not reasons:
        return "ACCEPTED"
    if reasons == {"CORRECTION_PROPAGATION_GAP"}:
        return "PARTIAL"
    return "BLOCKED"


def _validate_unique_strings(
    case_id: str, label: str, value: Any, *, allow_empty: bool
) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, list):
        return [f"{case_id}: {label} must be a list"]
    if not allow_empty and not value:
        errors.append(f"{case_id}: {label} must not be empty")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        errors.append(f"{case_id}: {label} must contain non-empty strings")
    elif len(value) != len(set(value)):
        errors.append(f"{case_id}: {label} must not contain duplicates")
    return errors


def validate_case(case: dict[str, Any]) -> list[str]:
    errors = _field_set_errors(case, CASE_FIELDS, "case")
    raw_case_id = case.get("case_id")
    case_id = raw_case_id if isinstance(raw_case_id, str) and raw_case_id else "<unknown>"
    if case_id == "<unknown>":
        errors.append("case_id must be a non-empty string")
    description = case.get("description")
    if not isinstance(description, str) or not description.strip():
        errors.append(f"{case_id}: description must be a non-empty string")

    errors.extend(_validate_unique_strings(case_id, "nodes", case.get("nodes"), allow_empty=False))
    errors.extend(_validate_unique_strings(case_id, "edges", case.get("edges"), allow_empty=True))

    reason_codes = case.get("expected_reason_codes")
    if not isinstance(reason_codes, list):
        errors.append(f"{case_id}: expected_reason_codes must be a list")
        expected_reasons: set[str] = set()
    else:
        expected_reasons = set(reason_codes)
        if len(expected_reasons) != len(reason_codes):
            errors.append(f"{case_id}: expected_reason_codes must be unique")
        invalid = sorted(
            code
            for code in reason_codes
            if not isinstance(code, str) or code not in ALLOWED_REASON_CODES
        )
        if invalid:
            errors.append(f"{case_id}: invalid expected_reason_codes {invalid}")

    disposition = case.get("expected_disposition")
    if disposition not in ALLOWED_DISPOSITIONS:
        errors.append(f"{case_id}: invalid expected_disposition {disposition!r}")

    try:
        derived = _derived_reasons(case_id, case.get("flags"))
    except FixtureError as exc:
        errors.append(str(exc))
        derived = set()

    if derived != expected_reasons:
        errors.append(
            f"{case_id}: expected reasons {sorted(expected_reasons)} "
            f"do not match independently derived {sorted(derived)}"
        )
    independently_expected = _expected_disposition(derived)
    if disposition != independently_expected:
        errors.append(
            f"{case_id}: disposition {disposition!r} does not match "
            f"independently derived {independently_expected!r}"
        )
    return errors


def validate_fixture(document: dict[str, Any]) -> tuple[list[str], dict[str, int]]:
    errors = _field_set_errors(document, TOP_FIELDS, "fixture")
    if document.get("fixture_id") != "qso.portfolio-contract-graph.v1":
        errors.append("fixture_id must be qso.portfolio-contract-graph.v1")
    if document.get("fixture_version") != 1:
        errors.append("fixture_version must be 1")
    if document.get("status") != "synthetic-only":
        errors.append("status must be synthetic-only")
    if document.get("authority_effect") != "none":
        errors.append("authority_effect must be none")

    prohibited = sorted(_walk_field_names(document) & PROHIBITED_FIELDS)
    if prohibited:
        errors.append(f"prohibited fields present: {prohibited}")

    cases = document.get("cases")
    if not isinstance(cases, list):
        return errors + ["cases must be a list"], {
            "case_count": 0,
            "pairwise_cases": 0,
            "triple_or_larger_cases": 0,
        }

    case_ids: list[str] = []
    pairwise = 0
    triple_or_larger = 0
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            errors.append(f"case[{index}] must be an object")
            continue
        case_id = case.get("case_id")
        if isinstance(case_id, str):
            case_ids.append(case_id)
        nodes = case.get("nodes")
        if isinstance(nodes, list):
            if len(nodes) == 2:
                pairwise += 1
            elif len(nodes) >= 3:
                triple_or_larger += 1
        errors.extend(validate_case(case))

    if len(case_ids) != len(set(case_ids)):
        errors.append("case_id values must be unique")
    actual_cases = set(case_ids)
    if actual_cases != REQUIRED_CASES:
        errors.append(
            f"case coverage mismatch; missing={sorted(REQUIRED_CASES - actual_cases)}, "
            f"extra={sorted(actual_cases - REQUIRED_CASES)}"
        )
    if pairwise < 4:
        errors.append("corpus must include at least four pairwise cases")
    if triple_or_larger < 5:
        errors.append("corpus must include at least five triple-or-larger overlap cases")

    return errors, {
        "case_count": len(cases),
        "pairwise_cases": pairwise,
        "triple_or_larger_cases": triple_or_larger,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--fixture",
        type=Path,
        default=Path("fixtures/portfolio-contract-graph-v1.json"),
    )
    parser.add_argument("--expected-sha256")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    errors: list[str] = []
    metrics = {"case_count": 0, "pairwise_cases": 0, "triple_or_larger_cases": 0}
    actual_sha256: str | None = None
    try:
        document, actual_sha256 = load_fixture(args.fixture)
        if args.expected_sha256 and actual_sha256 != args.expected_sha256:
            errors.append(
                f"fixture SHA-256 mismatch: expected {args.expected_sha256}, "
                f"got {actual_sha256}"
            )
        validation_errors, metrics = validate_fixture(document)
        errors.extend(validation_errors)
    except FixtureError as exc:
        errors.append(str(exc))

    report = {
        "fixture": str(args.fixture),
        "fixture_sha256": actual_sha256,
        "valid": not errors,
        "error_count": len(errors),
        "errors": errors,
        "independent_consumer": True,
        "synthetic_only": True,
        "authority_effect": "none",
        **metrics,
    }
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    print(rendered, end="")
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered, encoding="utf-8")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
