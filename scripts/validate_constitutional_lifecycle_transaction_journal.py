#!/usr/bin/env python3
"""Independently validate the shared synthetic constitutional lifecycle journal corpus."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

MAX_BYTES = 256 * 1024
SCHEMA = "alistaire.constitutional-lifecycle-transaction-journal.corpus.v1"
STATUS = "synthetic_only_non_operational"
ROOT_FIELDS = frozenset({"schema", "profile_version", "status", "cases"})
RECORD_FIELDS = frozenset({
    "case_id", "description", "operation", "current_state", "current_generation",
    "current_credential_generation", "operation_generation",
    "operation_credential_generation", "journal_phase", "interruption",
    "concurrent_operation", "concurrent_generation", "transaction_id",
    "prior_transaction_ids", "ack_generation", "acknowledged_generations",
    "sequence_start", "sequence_values", "expected_state", "expected_reason",
    "expected_effect", "expected_generation", "expected_credential_generation",
})
REQUIRED_CASES = frozenset({
    "replacement-committed-and-acknowledged",
    "concurrent-replacement-conflict",
    "suspension-wins-over-appeal-race",
    "appeal-without-suspension",
    "late-ack-after-generation-change",
    "replayed-acknowledgment-idempotent",
    "credential-generation-rotation",
    "rollback-interrupted-before-commit",
    "rollback-interrupted-after-prepare",
    "rollback-committed-before-ack",
    "recovery-preserves-committed-rollback",
    "corrupted-journal-quarantined",
    "journal-sequence-gap-quarantined",
    "duplicate-transaction-id-quarantined",
    "stale-suspension-after-replacement",
})
OPERATIONS = frozenset({
    "replacement", "suspension", "appeal", "propagation_ack",
    "credential_rotation", "rollback", "recovery",
})
CURRENT_STATES = frozenset({
    "active", "suspended", "appeal_pending", "suspended_appeal_pending",
    "replaced", "rolled_back", "rolled_back_pending_ack", "pending_propagation",
})
OUTPUT_STATES = CURRENT_STATES | {"quarantined"}
PHASES = frozenset({"none", "prepared", "committed", "acknowledged", "corrupt"})
INTERRUPTIONS = frozenset({"none", "before_commit", "after_prepare", "after_commit_before_ack"})
CONCURRENT = frozenset({None, "replacement", "suspension", "appeal", "rollback"})
REASONS = frozenset({
    "replacement_committed", "replacement_committed_unacknowledged",
    "concurrent_replacement_conflict", "suspension_recorded",
    "suspension_precedence", "appeal_recorded", "stale_ack_rejected",
    "acknowledgment_idempotent", "propagation_acknowledged",
    "credential_rotation_pending_ack", "prior_state_preserved",
    "prepared_state_discarded", "rollback_committed_unacknowledged",
    "rollback_complete", "recovery_preserved_committed_state",
    "journal_corrupt", "journal_sequence_gap", "duplicate_transaction_id",
    "stale_operation_rejected", "recovery_noop",
})
EFFECTS = frozenset({"none", "record_only", "restoration_only", "synthetic_bounded_active"})
PROHIBITED_NAMES = frozenset({
    "private_key", "secret", "password", "access_token", "credential_value",
    "biometric_template", "raw_biometric", "live_registry_endpoint",
})


class ContractError(ValueError):
    """Fail-closed parsing or conformance error."""


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for name, value in pairs:
        if name in output:
            raise ContractError(f"duplicate JSON key: {name}")
        output[name] = value
    return output


def _no_nonfinite(token: str) -> None:
    raise ContractError(f"non-finite JSON number: {token}")


def decode_fixture(path: Path) -> tuple[dict[str, Any], str]:
    raw = path.read_bytes()
    if len(raw) > MAX_BYTES:
        raise ContractError(f"fixture exceeds {MAX_BYTES} bytes")
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ContractError("fixture must be strict UTF-8") from exc
    try:
        value = json.loads(
            text,
            object_pairs_hook=_strict_object,
            parse_constant=_no_nonfinite,
        )
    except json.JSONDecodeError as exc:
        raise ContractError(f"malformed JSON: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise ContractError("fixture root must be an object")
    return value, hashlib.sha256(raw).hexdigest()


def _field_diff(record: dict[str, Any], expected: frozenset[str], label: str) -> list[str]:
    actual = set(record)
    if actual == expected:
        return []
    return [
        f"{label}: fields differ; missing={sorted(expected - actual)}, "
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


def _effect_for_state(state: str) -> str:
    return {
        "active": "synthetic_bounded_active",
        "replaced": "record_only",
        "rolled_back": "restoration_only",
        "rolled_back_pending_ack": "restoration_only",
    }.get(state, "none")


def _unchanged(case: dict[str, Any], reason: str) -> tuple[str, str, str, int, int]:
    state = case["current_state"]
    return (
        state,
        reason,
        _effect_for_state(state),
        case["current_generation"],
        case["current_credential_generation"],
    )


def project(case: dict[str, Any]) -> tuple[str, str, str, int, int]:
    current_generation = case["current_generation"]
    current_credential = case["current_credential_generation"]
    operation_generation = case["operation_generation"]
    operation_credential = case["operation_credential_generation"]

    if case["journal_phase"] == "corrupt":
        return "quarantined", "journal_corrupt", "none", current_generation, current_credential

    expected_sequence = list(
        range(
            case["sequence_start"] + 1,
            case["sequence_start"] + 1 + len(case["sequence_values"]),
        )
    )
    if case["sequence_values"] != expected_sequence:
        return "quarantined", "journal_sequence_gap", "none", current_generation, current_credential
    if case["transaction_id"] in set(case["prior_transaction_ids"]):
        return "quarantined", "duplicate_transaction_id", "none", current_generation, current_credential

    if case["interruption"] == "before_commit":
        return _unchanged(case, "prior_state_preserved")
    if case["interruption"] == "after_prepare":
        return _unchanged(case, "prepared_state_discarded")

    operation = case["operation"]
    if operation == "replacement":
        if (
            case["concurrent_operation"] == "replacement"
            and case["concurrent_generation"] == operation_generation
        ):
            return _unchanged(case, "concurrent_replacement_conflict")
        if operation_generation != current_generation + 1 or operation_credential != current_credential:
            return _unchanged(case, "stale_operation_rejected")
        if case["journal_phase"] == "acknowledged" and case["ack_generation"] == operation_generation:
            return "replaced", "replacement_committed", "record_only", operation_generation, current_credential
        if case["journal_phase"] == "committed" or case["interruption"] == "after_commit_before_ack":
            return (
                "pending_propagation", "replacement_committed_unacknowledged",
                "none", operation_generation, current_credential,
            )
        return _unchanged(case, "prior_state_preserved")

    if operation == "suspension":
        if operation_generation != current_generation or operation_credential != current_credential:
            return _unchanged(case, "stale_operation_rejected")
        if case["concurrent_operation"] == "appeal" and case["concurrent_generation"] == current_generation:
            return (
                "suspended_appeal_pending", "suspension_precedence",
                "none", current_generation, current_credential,
            )
        return "suspended", "suspension_recorded", "none", current_generation, current_credential

    if operation == "appeal":
        if operation_generation != current_generation or operation_credential != current_credential:
            return _unchanged(case, "stale_operation_rejected")
        if case["concurrent_operation"] == "suspension" and case["concurrent_generation"] == current_generation:
            return (
                "suspended_appeal_pending", "suspension_precedence",
                "none", current_generation, current_credential,
            )
        return "appeal_pending", "appeal_recorded", "none", current_generation, current_credential

    if operation == "propagation_ack":
        if case["ack_generation"] != current_generation or operation_credential != current_credential:
            return _unchanged(case, "stale_ack_rejected")
        if case["ack_generation"] in set(case["acknowledged_generations"]):
            return _unchanged(case, "acknowledgment_idempotent")
        return (
            "active", "propagation_acknowledged", "synthetic_bounded_active",
            current_generation, current_credential,
        )

    if operation == "credential_rotation":
        if operation_generation != current_generation or operation_credential != current_credential + 1:
            return _unchanged(case, "stale_operation_rejected")
        return (
            "pending_propagation", "credential_rotation_pending_ack",
            "none", current_generation, operation_credential,
        )

    if operation == "rollback":
        if operation_generation >= current_generation or operation_credential != current_credential:
            return _unchanged(case, "stale_operation_rejected")
        if case["journal_phase"] == "acknowledged" and case["ack_generation"] == operation_generation:
            return (
                "rolled_back", "rollback_complete", "restoration_only",
                operation_generation, current_credential,
            )
        if case["journal_phase"] == "committed" or case["interruption"] == "after_commit_before_ack":
            return (
                "rolled_back_pending_ack", "rollback_committed_unacknowledged",
                "restoration_only", operation_generation, current_credential,
            )
        return _unchanged(case, "prior_state_preserved")

    if operation == "recovery":
        if case["journal_phase"] == "prepared":
            return _unchanged(case, "prepared_state_discarded")
        if case["journal_phase"] == "committed":
            if operation_generation >= current_generation:
                return _unchanged(case, "stale_operation_rejected")
            return (
                "rolled_back_pending_ack", "recovery_preserved_committed_state",
                "restoration_only", operation_generation, current_credential,
            )
        if case["journal_phase"] == "acknowledged":
            if operation_generation >= current_generation:
                return _unchanged(case, "stale_operation_rejected")
            return (
                "rolled_back", "rollback_complete", "restoration_only",
                operation_generation, current_credential,
            )
        return _unchanged(case, "recovery_noop")

    raise ContractError(f"unsupported operation: {operation}")


def _valid_unique_strings(value: Any) -> bool:
    return (
        isinstance(value, list)
        and all(isinstance(item, str) and item for item in value)
        and len(value) == len(set(value))
    )


def _valid_unique_nonnegative_ints(value: Any) -> bool:
    return (
        isinstance(value, list)
        and all(type(item) is int and item >= 0 for item in value)
        and len(value) == len(set(value))
    )


def validate_case(case: dict[str, Any]) -> list[str]:
    errors = _field_diff(case, RECORD_FIELDS, "case")
    case_id = case.get("case_id")
    label = case_id if isinstance(case_id, str) and case_id else "<unknown>"
    if label == "<unknown>":
        errors.append("case_id must be a non-empty string")
    if not isinstance(case.get("description"), str) or len(case["description"].strip()) < 20:
        errors.append(f"{label}: description is too short")
    if case.get("operation") not in OPERATIONS:
        errors.append(f"{label}: unsupported operation")
    if case.get("current_state") not in CURRENT_STATES:
        errors.append(f"{label}: unsupported current_state")
    if case.get("journal_phase") not in PHASES:
        errors.append(f"{label}: unsupported journal_phase")
    if case.get("interruption") not in INTERRUPTIONS:
        errors.append(f"{label}: unsupported interruption")
    if case.get("concurrent_operation") not in CONCURRENT:
        errors.append(f"{label}: unsupported concurrent_operation")
    if case.get("concurrent_operation") is None:
        if case.get("concurrent_generation") is not None:
            errors.append(f"{label}: concurrent_generation requires concurrent_operation")
    elif type(case.get("concurrent_generation")) is not int or case["concurrent_generation"] < 0:
        errors.append(f"{label}: invalid concurrent_generation")
    for name in (
        "current_generation", "current_credential_generation",
        "operation_generation", "operation_credential_generation",
        "sequence_start", "expected_generation", "expected_credential_generation",
    ):
        if type(case.get(name)) is not int or case[name] < 0:
            errors.append(f"{label}: {name} must be a non-negative integer")
    if case.get("ack_generation") is not None and (
        type(case["ack_generation"]) is not int or case["ack_generation"] < 0
    ):
        errors.append(f"{label}: invalid ack_generation")
    if not isinstance(case.get("transaction_id"), str) or not case["transaction_id"]:
        errors.append(f"{label}: transaction_id must be non-empty")
    if not _valid_unique_strings(case.get("prior_transaction_ids")):
        errors.append(f"{label}: prior_transaction_ids must be unique non-empty strings")
    if not _valid_unique_nonnegative_ints(case.get("acknowledged_generations")):
        errors.append(f"{label}: acknowledged_generations must be unique non-negative integers")
    if not _valid_unique_nonnegative_ints(case.get("sequence_values")):
        errors.append(f"{label}: sequence_values must be unique non-negative integers")
    if case.get("expected_state") not in OUTPUT_STATES:
        errors.append(f"{label}: invalid expected_state")
    if case.get("expected_reason") not in REASONS:
        errors.append(f"{label}: invalid expected_reason")
    if case.get("expected_effect") not in EFFECTS:
        errors.append(f"{label}: invalid expected_effect")

    if not errors:
        expected = (
            case["expected_state"], case["expected_reason"], case["expected_effect"],
            case["expected_generation"], case["expected_credential_generation"],
        )
        try:
            actual = project(case)
        except ContractError as exc:
            errors.append(f"{label}: {exc}")
        else:
            if actual != expected:
                errors.append(f"{label}: expected {expected!r}, derived {actual!r}")
    return errors


def validate_document(document: dict[str, Any]) -> dict[str, Any]:
    errors = _field_diff(document, ROOT_FIELDS, "root")
    if document.get("schema") != SCHEMA:
        errors.append("unexpected schema")
    if document.get("profile_version") != "1.0.0":
        errors.append("unexpected profile_version")
    if document.get("status") != STATUS:
        errors.append("fixture must remain synthetic and non-operational")
    prohibited = sorted(_walk_field_names(document) & PROHIBITED_NAMES)
    if prohibited:
        errors.append(f"prohibited fields present: {prohibited}")
    cases = document.get("cases")
    if not isinstance(cases, list):
        errors.append("cases must be an array")
        cases = []
    identities: list[str] = []
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            errors.append(f"case[{index}] must be an object")
            continue
        errors.extend(validate_case(case))
        if isinstance(case.get("case_id"), str):
            identities.append(case["case_id"])
    if len(identities) != len(set(identities)):
        errors.append("duplicate case identities")
    actual_cases = set(identities)
    if actual_cases != REQUIRED_CASES:
        errors.append(
            f"fixture coverage drift: missing={sorted(REQUIRED_CASES - actual_cases)}, "
            f"extra={sorted(actual_cases - REQUIRED_CASES)}"
        )
    if errors:
        raise ContractError("\n".join(errors))
    return {
        "schema": SCHEMA,
        "status": STATUS,
        "cases": len(identities),
        "case_ids": sorted(identities),
        "appointment_authority": False,
        "credential_authority": False,
        "operational_authority": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    document, digest = decode_fixture(args.fixture)
    if digest != args.expected_sha256:
        raise ContractError(
            f"fixture digest mismatch: expected {args.expected_sha256}, got {digest}"
        )
    report = validate_document(document)
    report["fixture_sha256"] = digest
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
