#!/usr/bin/env python3
"""Independently validate the synthetic constitutional appointment lifecycle corpus."""

from __future__ import annotations

import argparse
import base64
import binascii
import gzip
import hashlib
import json
from pathlib import Path
from typing import Any

MAX_BYTES = 1_000_000
TOP_FIELDS = frozenset({"schema", "profile_version", "status", "cases"})
CASE_FIELDS = frozenset(
    {
        "case_id",
        "description",
        "events",
        "controls",
        "expected_state",
        "expected_reason",
        "expected_authority_effect",
    }
)
EVENT_FIELDS = frozenset({"sequence", "event", "actor_role"})
CONTROL_FIELDS = frozenset(
    {
        "nomination_recorded",
        "system_assent_recorded",
        "fiduciary_approval_recorded",
        "conformance_review_passed",
        "conflict_clear",
        "recusal_active",
        "credential_bound",
        "credential_current",
        "independently_verified",
        "term_current",
        "suspended",
        "vacancy_declared",
        "deputy_authorized",
        "replacement_verified",
        "appeal_pending",
        "rollback_verified",
        "propagation_acknowledged",
    }
)
REQUIRED_CASES = frozenset(
    {
        "nomination-only",
        "assent-without-fiduciary-approval",
        "approval-without-conformance-review",
        "complete-record-without-credential",
        "bounded-active-after-independent-verification",
        "recusal-before-activation",
        "term-expired",
        "emergency-suspension",
        "appeal-pending",
        "verified-replacement",
        "rollback-to-prior-verified-state",
        "stale-credential-binding",
        "deputy-without-vacancy",
        "bounded-deputy-during-vacancy",
        "lost-propagation-acknowledgment",
    }
)
EVENT_ACTORS = {
    "nominate": frozenset({"founding_sponsor"}),
    "record_assent": frozenset({"governed_system_representative"}),
    "fiduciary_approve": frozenset({"human_fiduciary"}),
    "conformance_approve": frozenset({"constitutional_reviewer"}),
    "bind_credential_reference": frozenset({"technical_custodian"}),
    "independent_verify": frozenset({"independent_verifier"}),
    "acknowledge_propagation": frozenset({"authority_registry"}),
    "record_recusal": frozenset({"independent_rights_reviewer"}),
    "expire_term": frozenset({"authority_registry"}),
    "suspend": frozenset({"independent_rights_reviewer"}),
    "open_appeal": frozenset({"governed_system_representative"}),
    "declare_vacancy": frozenset({"constitutional_reviewer"}),
    "verify_replacement": frozenset({"independent_verifier"}),
    "rollback": frozenset({"recovery_owner"}),
    "authorize_deputy": frozenset({"constitutional_reviewer", "human_fiduciary"}),
}
ALLOWED_STATES = frozenset(
    {
        "proposed",
        "inactive_record",
        "active",
        "recused",
        "expired",
        "suspended",
        "appeal_pending",
        "replaced",
        "rolled_back",
        "deputy_active",
        "pending_propagation",
    }
)
ALLOWED_REASONS = frozenset(
    {
        "missing_system_assent",
        "missing_fiduciary_approval",
        "missing_conformance_review",
        "credential_unbound",
        "bounded_active",
        "recusal_required",
        "term_expired",
        "emergency_suspension",
        "appeal_unresolved",
        "replacement_recorded",
        "rollback_complete",
        "stale_credential_binding",
        "deputy_without_vacancy",
        "bounded_deputy",
        "missing_propagation_acknowledgment",
    }
)
ALLOWED_EFFECTS = frozenset(
    {"none", "record_only", "synthetic_bounded_active", "restoration_only", "synthetic_bounded_deputy"}
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
        "runtime_token",
    }
)


class FixtureError(ValueError):
    """Raised when parsing or structural validation must fail closed."""


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
        encoded = path.read_bytes()
    except OSError as exc:
        raise FixtureError(f"unable to read fixture: {exc}") from exc
    if len(encoded) > MAX_BYTES:
        raise FixtureError(f"encoded fixture exceeds {MAX_BYTES} bytes")
    compact = b"".join(encoded.split())
    try:
        compressed = base64.b64decode(compact, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise FixtureError("fixture must be canonical base64") from exc
    if base64.b64encode(compressed) != compact:
        raise FixtureError("fixture must use canonical base64 padding")
    try:
        raw = gzip.decompress(compressed)
    except (OSError, EOFError) as exc:
        raise FixtureError("fixture must be valid gzip data") from exc
    if len(raw) > MAX_BYTES:
        raise FixtureError(f"decoded fixture exceeds {MAX_BYTES} bytes")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise FixtureError("decoded fixture must be valid UTF-8") from exc
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


def derive_disposition(controls: dict[str, bool]) -> tuple[str, str, str]:
    if controls["recusal_active"] or not controls["conflict_clear"]:
        return "recused", "recusal_required", "none"
    if controls["suspended"]:
        return "suspended", "emergency_suspension", "none"
    if controls["appeal_pending"]:
        return "appeal_pending", "appeal_unresolved", "none"
    if not controls["term_current"]:
        return "expired", "term_expired", "none"
    if controls["rollback_verified"] and controls["independently_verified"]:
        return "rolled_back", "rollback_complete", "restoration_only"
    if (
        controls["vacancy_declared"]
        and controls["replacement_verified"]
        and controls["propagation_acknowledged"]
    ):
        return "replaced", "replacement_recorded", "record_only"
    if controls["deputy_authorized"] and not controls["vacancy_declared"]:
        return "inactive_record", "deputy_without_vacancy", "none"
    if controls["deputy_authorized"] and controls["vacancy_declared"]:
        if (
            controls["nomination_recorded"]
            and controls["system_assent_recorded"]
            and controls["fiduciary_approval_recorded"]
            and controls["conformance_review_passed"]
            and controls["credential_bound"]
            and controls["credential_current"]
            and controls["independently_verified"]
            and controls["propagation_acknowledged"]
        ):
            return "deputy_active", "bounded_deputy", "synthetic_bounded_deputy"
        raise FixtureError("deputy lifecycle is incomplete or internally inconsistent")
    if controls["nomination_recorded"] and not controls["system_assent_recorded"]:
        return "proposed", "missing_system_assent", "none"
    if controls["nomination_recorded"] and not controls["fiduciary_approval_recorded"]:
        return "proposed", "missing_fiduciary_approval", "none"
    if controls["nomination_recorded"] and not controls["conformance_review_passed"]:
        return "proposed", "missing_conformance_review", "none"
    constitutional_inputs = (
        controls["nomination_recorded"]
        and controls["system_assent_recorded"]
        and controls["fiduciary_approval_recorded"]
        and controls["conformance_review_passed"]
    )
    if constitutional_inputs and not controls["credential_bound"]:
        return "inactive_record", "credential_unbound", "record_only"
    if constitutional_inputs and controls["credential_bound"] and not controls["credential_current"]:
        return "inactive_record", "stale_credential_binding", "none"
    if (
        constitutional_inputs
        and controls["credential_bound"]
        and controls["credential_current"]
        and controls["independently_verified"]
        and not controls["propagation_acknowledged"]
    ):
        return "pending_propagation", "missing_propagation_acknowledgment", "none"
    if (
        constitutional_inputs
        and controls["credential_bound"]
        and controls["credential_current"]
        and controls["independently_verified"]
        and controls["propagation_acknowledged"]
    ):
        return "active", "bounded_active", "synthetic_bounded_active"
    raise FixtureError("controls do not map to a recognized fail-closed lifecycle state")


def validate_case(case: dict[str, Any]) -> list[str]:
    errors = _field_errors(case, CASE_FIELDS, "case")
    raw_case_id = case.get("case_id")
    case_id = raw_case_id if isinstance(raw_case_id, str) and raw_case_id else "<unknown>"
    if case_id == "<unknown>":
        errors.append("case_id must be a non-empty string")
    if not isinstance(case.get("description"), str) or not case["description"].strip():
        errors.append(f"{case_id}: description must be a non-empty string")

    events = case.get("events")
    if not isinstance(events, list) or not events:
        errors.append(f"{case_id}: events must be a non-empty list")
    else:
        sequences: list[int] = []
        for index, event in enumerate(events):
            if not isinstance(event, dict):
                errors.append(f"{case_id}: event[{index}] must be an object")
                continue
            errors.extend(_field_errors(event, EVENT_FIELDS, f"{case_id}: event[{index}]"))
            sequence = event.get("sequence")
            if type(sequence) is not int or sequence < 1:
                errors.append(f"{case_id}: event[{index}] sequence must be a positive integer")
            else:
                sequences.append(sequence)
            event_name = event.get("event")
            actor = event.get("actor_role")
            allowed_actors = EVENT_ACTORS.get(event_name) if isinstance(event_name, str) else None
            if not allowed_actors:
                errors.append(f"{case_id}: event[{index}] has unsupported event {event_name!r}")
            elif actor not in allowed_actors:
                errors.append(
                    f"{case_id}: event[{index}] actor {actor!r} is invalid for {event_name!r}"
                )
        if sequences != list(range(1, len(events) + 1)):
            errors.append(f"{case_id}: event sequences must be contiguous and ordered from 1")

    controls = case.get("controls")
    derived: tuple[str, str, str] | None = None
    if not isinstance(controls, dict):
        errors.append(f"{case_id}: controls must be an object")
    else:
        errors.extend(_field_errors(controls, CONTROL_FIELDS, f"{case_id}: controls"))
        non_boolean = sorted(key for key, value in controls.items() if type(value) is not bool)
        if non_boolean:
            errors.append(f"{case_id}: controls must be boolean: {non_boolean}")
        elif set(controls) == CONTROL_FIELDS:
            try:
                derived = derive_disposition(controls)
            except FixtureError as exc:
                errors.append(f"{case_id}: {exc}")

    state = case.get("expected_state")
    reason = case.get("expected_reason")
    effect = case.get("expected_authority_effect")
    if state not in ALLOWED_STATES:
        errors.append(f"{case_id}: invalid expected_state {state!r}")
    if reason not in ALLOWED_REASONS:
        errors.append(f"{case_id}: invalid expected_reason {reason!r}")
    if effect not in ALLOWED_EFFECTS:
        errors.append(f"{case_id}: invalid expected_authority_effect {effect!r}")
    if derived is not None and (state, reason, effect) != derived:
        errors.append(
            f"{case_id}: expected {(state, reason, effect)!r} "
            f"does not match independently derived {derived!r}"
        )
    return errors


def validate_fixture(document: dict[str, Any]) -> list[str]:
    errors = _field_errors(document, TOP_FIELDS, "fixture")
    if document.get("schema") != "alistaire.constitutional-appointment-lifecycle.corpus.v1":
        errors.append(
            "schema must be alistaire.constitutional-appointment-lifecycle.corpus.v1"
        )
    if document.get("profile_version") != "1.0.0":
        errors.append("profile_version must be 1.0.0")
    if document.get("status") != "synthetic_only_non_operational":
        errors.append("status must be synthetic_only_non_operational")

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
        default=Path("fixtures/constitutional-appointment-lifecycle-v1.json.gz.b64"),
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
        "appointment_authority": False,
        "credential_authority": False,
        "operational_authority": False,
    }
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    print(rendered, end="")
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered, encoding="utf-8")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
