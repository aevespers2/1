#!/usr/bin/env python3
"""Independently validate synthetic atomic consume-and-record fixture cases."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any


IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9._:-]{2,127}$")
TOP_LEVEL_KEYS = {
    "schema",
    "synthetic_only",
    "operational_authority",
    "baseline",
    "cases",
}
STATE_KEYS = {
    "schema",
    "state_version",
    "seen_attempt_ids",
    "revoked_profile_ids",
    "receipts",
}
OPERATION_KEYS = {
    "schema",
    "operation_id",
    "attempt_id",
    "profile_id",
    "expected_state_version",
    "proposed_receipt_id",
    "fault_point",
}
RECEIPT_KEYS = {
    "receipt_id",
    "operation_id",
    "attempt_id",
    "profile_id",
    "disposition",
    "committed_state_version",
}
EXPECTED_KEYS = {
    "outcome",
    "error",
    "state_version",
    "seen_attempt_ids",
    "receipt_count",
    "state_sha256",
}
EXPECTED_CASES = {
    "valid-commit": ("accepted", None),
    "replayed-attempt": ("reject", "attempt-replay"),
    "revoked-profile": ("reject", "profile-revoked"),
    "stale-state-version": ("reject", "stale-state-version"),
    "interrupted-before-commit": ("interrupted-before-commit", "before-commit"),
    "interrupted-after-prepare": ("interrupted-before-commit", "after-prepare"),
    "committed-before-ack": ("committed-no-ack", None),
    "retry-after-unknown-ack": ("already-committed", None),
    "partial-consume-without-receipt": ("reject", "partial-consume-record"),
    "partial-receipt-without-consume": ("reject", "partial-consume-record"),
}
FAULT_POINTS = {
    "none",
    "before-commit",
    "after-prepare",
    "after-commit-before-ack",
}


class FixtureError(ValueError):
    """Raised when atomic fixture semantics fail closed."""


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise FixtureError(f"duplicate-key:{key}")
        result[key] = value
    return result


def reject_non_finite(value: str) -> None:
    raise FixtureError(f"non-finite-number:{value}")


def strict_loads(text: str) -> Any:
    try:
        return json.loads(
            text,
            object_pairs_hook=reject_duplicate_keys,
            parse_constant=reject_non_finite,
        )
    except FixtureError:
        raise
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise FixtureError(f"invalid-json:{exc}") from exc


def canonical_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise FixtureError(f"non-canonical-json:{exc}") from exc


def exact_object(name: str, value: Any, expected: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise FixtureError(f"{name}-not-object")
    keys = set(value)
    if keys != expected:
        raise FixtureError(
            f"{name}-fields:missing={sorted(expected - keys)}:"
            f"unknown={sorted(keys - expected)}"
        )
    return copy.deepcopy(value)


def require_identifier(name: str, value: Any) -> str:
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
        raise FixtureError(f"{name}-invalid")
    return value


def require_identifier_list(name: str, value: Any) -> list[str]:
    if not isinstance(value, list):
        raise FixtureError(f"{name}-not-list")
    for item in value:
        require_identifier(name, item)
    if len(value) != len(set(value)):
        raise FixtureError(f"{name}-duplicate")
    return list(value)


def validate_state(value: Any) -> dict[str, Any]:
    state = exact_object("state", value, STATE_KEYS)
    if state["schema"] != "qso.iris-authority-state.v0":
        raise FixtureError("state-schema-invalid")
    version = state["state_version"]
    if type(version) is not int or version < 1:
        raise FixtureError("state-version-invalid")
    seen = require_identifier_list("seen-attempt-ids", state["seen_attempt_ids"])
    require_identifier_list("revoked-profile-ids", state["revoked_profile_ids"])
    if not isinstance(state["receipts"], list):
        raise FixtureError("receipts-not-list")

    receipt_ids: set[str] = set()
    operation_ids: set[str] = set()
    receipt_attempt_ids: list[str] = []
    receipts: list[dict[str, Any]] = []
    for value in state["receipts"]:
        receipt = exact_object("receipt", value, RECEIPT_KEYS)
        for field in ("receipt_id", "operation_id", "attempt_id", "profile_id"):
            require_identifier(field, receipt[field])
        if receipt["receipt_id"] in receipt_ids:
            raise FixtureError("duplicate-receipt-id")
        if receipt["operation_id"] in operation_ids:
            raise FixtureError("duplicate-operation-id")
        receipt_ids.add(receipt["receipt_id"])
        operation_ids.add(receipt["operation_id"])
        receipt_attempt_ids.append(receipt["attempt_id"])
        if receipt["disposition"] != "accepted":
            raise FixtureError("receipt-disposition-invalid")
        committed_version = receipt["committed_state_version"]
        if (
            type(committed_version) is not int
            or committed_version < 1
            or committed_version > version
        ):
            raise FixtureError("receipt-version-invalid")
        receipts.append(receipt)

    if sorted(receipt_attempt_ids) != sorted(seen):
        raise FixtureError("partial-consume-record")
    state["receipts"] = receipts
    return state


def validate_operation(value: Any) -> dict[str, Any]:
    operation = exact_object("operation", value, OPERATION_KEYS)
    if operation["schema"] != "qso.iris-consume-record-operation.v0":
        raise FixtureError("operation-schema-invalid")
    for field in (
        "operation_id",
        "attempt_id",
        "profile_id",
        "proposed_receipt_id",
    ):
        require_identifier(field, operation[field])
    expected_version = operation["expected_state_version"]
    if type(expected_version) is not int or expected_version < 1:
        raise FixtureError("expected-state-version-invalid")
    if operation["fault_point"] not in FAULT_POINTS:
        raise FixtureError("fault-point-invalid")
    return operation


def apply_atomic(state_value: Any, operation_value: Any) -> dict[str, Any]:
    state = validate_state(state_value)
    operation = validate_operation(operation_value)

    matching_receipts = [
        receipt
        for receipt in state["receipts"]
        if receipt["operation_id"] == operation["operation_id"]
    ]
    if matching_receipts:
        receipt = matching_receipts[0]
        if (
            receipt["attempt_id"] == operation["attempt_id"]
            and receipt["profile_id"] == operation["profile_id"]
            and receipt["receipt_id"] == operation["proposed_receipt_id"]
        ):
            return {"outcome": "already-committed", "error": None, "state": state}
        return {"outcome": "reject", "error": "operation-id-conflict", "state": state}

    if operation["attempt_id"] in state["seen_attempt_ids"]:
        return {"outcome": "reject", "error": "attempt-replay", "state": state}
    if operation["profile_id"] in state["revoked_profile_ids"]:
        return {"outcome": "reject", "error": "profile-revoked", "state": state}
    if operation["expected_state_version"] != state["state_version"]:
        return {"outcome": "reject", "error": "stale-state-version", "state": state}

    fault_point = operation["fault_point"]
    if fault_point in {"before-commit", "after-prepare"}:
        return {
            "outcome": "interrupted-before-commit",
            "error": fault_point,
            "state": state,
        }

    committed = copy.deepcopy(state)
    committed["state_version"] += 1
    committed["seen_attempt_ids"].append(operation["attempt_id"])
    committed["receipts"].append(
        {
            "receipt_id": operation["proposed_receipt_id"],
            "operation_id": operation["operation_id"],
            "attempt_id": operation["attempt_id"],
            "profile_id": operation["profile_id"],
            "disposition": "accepted",
            "committed_state_version": committed["state_version"],
        }
    )
    committed = validate_state(committed)
    return {
        "outcome": (
            "committed-no-ack"
            if fault_point == "after-commit-before-ack"
            else "accepted"
        ),
        "error": None,
        "state": committed,
    }


def evaluate_case(
    baseline: dict[str, Any],
    case: dict[str, Any],
) -> tuple[str, str | None, dict[str, Any]]:
    state = copy.deepcopy(baseline["state"])
    operation = copy.deepcopy(baseline["operation"])
    state.update(copy.deepcopy(case["state_overrides"]))
    operation.update(copy.deepcopy(case["operation_overrides"]))
    try:
        result = apply_atomic(state, operation)
    except FixtureError as exc:
        return "reject", str(exc), state
    return result["outcome"], result["error"], result["state"]


def validate_fixture(path: Path, expected_sha256: str) -> dict[str, Any]:
    payload = path.read_bytes()
    actual_sha256 = hashlib.sha256(payload).hexdigest()
    if actual_sha256 != expected_sha256:
        raise FixtureError(
            f"fixture-digest-mismatch:expected={expected_sha256}:actual={actual_sha256}"
        )

    manifest = exact_object("manifest", strict_loads(payload.decode("utf-8")), TOP_LEVEL_KEYS)
    if manifest["schema"] != "qso.iris-atomic-consume-record-fixtures.v0":
        raise FixtureError("manifest-schema-invalid")
    if manifest["synthetic_only"] is not True:
        raise FixtureError("fixture-not-synthetic-only")
    if manifest["operational_authority"] is not False:
        raise FixtureError("operational-authority-must-be-false")
    baseline = exact_object("baseline", manifest["baseline"], {"state", "operation"})
    validate_state(baseline["state"])
    validate_operation(baseline["operation"])

    cases = manifest["cases"]
    if not isinstance(cases, list):
        raise FixtureError("cases-not-list")
    observed: dict[str, tuple[str, str | None]] = {}
    for value in cases:
        case = exact_object(
            "case",
            value,
            {"case_id", "state_overrides", "operation_overrides", "expected"},
        )
        case_id = require_identifier("case-id", case["case_id"])
        if case_id in observed:
            raise FixtureError(f"duplicate-case-id:{case_id}")
        if not isinstance(case["state_overrides"], dict):
            raise FixtureError(f"state-overrides-invalid:{case_id}")
        if not isinstance(case["operation_overrides"], dict):
            raise FixtureError(f"operation-overrides-invalid:{case_id}")
        expected = exact_object("expected", case["expected"], EXPECTED_KEYS)

        outcome, error, state = evaluate_case(baseline, case)
        actual = {
            "outcome": outcome,
            "error": error,
            "state_version": state["state_version"],
            "seen_attempt_ids": state["seen_attempt_ids"],
            "receipt_count": len(state["receipts"]),
            "state_sha256": hashlib.sha256(canonical_bytes(state)).hexdigest(),
        }
        if actual != expected:
            raise FixtureError(
                f"case-outcome-mismatch:{case_id}:"
                f"expected={expected!r}:actual={actual!r}"
            )
        observed[case_id] = (outcome, error)

    if observed != EXPECTED_CASES:
        raise FixtureError(
            f"case-coverage-mismatch:expected={sorted(EXPECTED_CASES)}:"
            f"actual={sorted(observed)}"
        )
    return {
        "status": "pass",
        "fixture_sha256": actual_sha256,
        "case_count": len(observed),
        "outcomes": {
            key: {"outcome": value[0], "error": value[1]}
            for key, value in observed.items()
        },
        "independent_implementation": True,
        "atomic_consume_and_record": True,
        "operational_authority": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    try:
        report = validate_fixture(args.fixture, args.expected_sha256)
    except (FixtureError, OSError, UnicodeError) as exc:
        report = {
            "status": "fail",
            "error": str(exc),
            "independent_implementation": True,
            "atomic_consume_and_record": True,
            "operational_authority": False,
        }
        status = 1
    else:
        status = 0

    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    print(rendered, end="")
    if args.report is not None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered, encoding="utf-8")
    return status


if __name__ == "__main__":
    raise SystemExit(main())
