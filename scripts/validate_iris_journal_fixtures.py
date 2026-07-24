#!/usr/bin/env python3
"""Independently validate the shared synthetic iris journal-recovery corpus."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9._:-]{2,127}$")
TOP_LEVEL_KEYS = {"schema", "synthetic_only", "operational_authority", "cases"}
CASE_KEYS = {"case_id", "authority_state", "journal_records", "expected"}
STATE_KEYS = {"schema", "state_version", "seen_attempt_ids", "revoked_profile_ids", "receipts"}
RECEIPT_KEYS = {"receipt_id", "operation_id", "attempt_id", "profile_id", "disposition", "committed_state_version"}
RECORD_KEYS = {"schema", "journal_seq", "operation_id", "attempt_id", "profile_id", "receipt_id", "phase", "prior_state_sha256", "state_after", "record_sha256"}
EXPECTED_KEYS = {"outcome", "error", "state_version", "seen_attempt_ids", "receipt_count", "state_sha256"}
EXPECTED_CASES = {
    "clean-no-journal": ("clean", None),
    "prepared-only-rolls-back": ("rolled-back", None),
    "committed-without-ack-recovers": ("recovered-committed", None),
    "acknowledged-journal-recovers-stale-state": ("recovered-committed", None),
    "committed-state-replay-is-idempotent": ("already-recovered", None),
    "corrupted-record-digest": ("reject", "journal-record-digest-mismatch"),
    "journal-sequence-gap": ("reject", "journal-sequence-gap"),
    "revoked-before-recovery": ("reject", "profile-revoked-before-recovery"),
    "duplicate-receipt-in-target-state": ("reject", "duplicate receipt"),
    "prepared-prior-digest-mismatch": ("reject", "journal-prior-state-mismatch"),
}


class FixtureError(ValueError):
    pass


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
        return json.loads(text, object_pairs_hook=reject_duplicate_keys, parse_constant=reject_non_finite)
    except FixtureError:
        raise
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise FixtureError(f"invalid-json:{exc}") from exc


def canonical_bytes(value: Any) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise FixtureError(f"non-canonical-json:{exc}") from exc


def sha(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def exact_object(name: str, value: Any, expected: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise FixtureError(f"{name}-not-object")
    if set(value) != expected:
        raise FixtureError(f"{name}-fields")
    return copy.deepcopy(value)


def require_identifier(name: str, value: Any) -> str:
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
        raise FixtureError(f"{name}-invalid")
    return value


def validate_state(value: Any) -> dict[str, Any]:
    state = exact_object("state", value, STATE_KEYS)
    if state["schema"] != "qso.iris-authority-state.v0":
        raise FixtureError("state-schema-invalid")
    if type(state["state_version"]) is not int or state["state_version"] < 1:
        raise FixtureError("state-version-invalid")
    for field in ("seen_attempt_ids", "revoked_profile_ids"):
        values = state[field]
        if not isinstance(values, list):
            raise FixtureError(f"{field}-not-list")
        for item in values:
            require_identifier(field, item)
        if len(values) != len(set(values)):
            raise FixtureError(f"{field}-duplicate")
    if not isinstance(state["receipts"], list):
        raise FixtureError("receipts-not-list")
    receipt_ids: set[str] = set()
    operation_ids: set[str] = set()
    attempts: list[str] = []
    for value in state["receipts"]:
        receipt = exact_object("receipt", value, RECEIPT_KEYS)
        for field in ("receipt_id", "operation_id", "attempt_id", "profile_id"):
            require_identifier(field, receipt[field])
        if receipt["receipt_id"] in receipt_ids or receipt["operation_id"] in operation_ids:
            raise FixtureError("duplicate receipt")
        receipt_ids.add(receipt["receipt_id"])
        operation_ids.add(receipt["operation_id"])
        attempts.append(receipt["attempt_id"])
        if receipt["disposition"] != "accepted":
            raise FixtureError("receipt-disposition-invalid")
        version = receipt["committed_state_version"]
        if type(version) is not int or not 1 <= version <= state["state_version"]:
            raise FixtureError("receipt-version-invalid")
    if sorted(attempts) != sorted(state["seen_attempt_ids"]):
        raise FixtureError("partial-consume-record")
    return state


def record_sha256(record: Mapping[str, Any]) -> str:
    body = dict(record)
    body.pop("record_sha256", None)
    return sha(body)


def validate_record(value: Any) -> dict[str, Any]:
    record = exact_object("journal-record", value, RECORD_KEYS)
    if record["schema"] != "qso.iris-authority-journal-record.v0":
        raise FixtureError("journal-record-schema-invalid")
    if type(record["journal_seq"]) is not int or record["journal_seq"] < 1:
        raise FixtureError("journal-sequence-invalid")
    for field in ("operation_id", "attempt_id", "profile_id", "receipt_id"):
        require_identifier(field, record[field])
    if record["phase"] not in {"prepared", "committed", "acknowledged"}:
        raise FixtureError("journal-phase-invalid")
    if not isinstance(record["prior_state_sha256"], str) or not re.fullmatch(r"[0-9a-f]{64}", record["prior_state_sha256"]):
        raise FixtureError("journal-prior-digest-invalid")
    if record["state_after"] is not None:
        record["state_after"] = validate_state(record["state_after"])
    if record["phase"] == "prepared" and record["state_after"] is not None:
        raise FixtureError("prepared-state-after-forbidden")
    if record["phase"] in {"committed", "acknowledged"} and record["state_after"] is None:
        raise FixtureError("committed-state-after-required")
    if record_sha256(record) != record["record_sha256"]:
        raise FixtureError("journal-record-digest-mismatch")
    return record


def validate_transition(prior: dict[str, Any], committed: dict[str, Any], record: dict[str, Any]) -> None:
    if committed["state_version"] != prior["state_version"] + 1:
        raise FixtureError("journal-commit-version-mismatch")
    if committed["revoked_profile_ids"] != prior["revoked_profile_ids"]:
        raise FixtureError("journal-commit-revocation-drift")
    if committed["seen_attempt_ids"] != prior["seen_attempt_ids"] + [record["attempt_id"]]:
        raise FixtureError("journal-commit-attempt-mismatch")
    expected_receipt = {
        "receipt_id": record["receipt_id"],
        "operation_id": record["operation_id"],
        "attempt_id": record["attempt_id"],
        "profile_id": record["profile_id"],
        "disposition": "accepted",
        "committed_state_version": committed["state_version"],
    }
    if committed["receipts"][:-1] != prior["receipts"] or committed["receipts"][-1] != expected_receipt:
        raise FixtureError("journal-commit-receipt-mismatch")


def reconcile(authority_state: Any, records_value: Any) -> dict[str, Any]:
    state = validate_state(authority_state)
    if not isinstance(records_value, list):
        raise FixtureError("journal-records-not-list")
    if len(records_value) > 16:
        raise FixtureError("journal-record-limit-exceeded")
    if not records_value:
        return {"outcome": "clean", "error": None, "state": state}
    records = [validate_record(value) for value in records_value]
    if [record["journal_seq"] for record in records] != list(range(1, len(records) + 1)):
        raise FixtureError("journal-sequence-gap")
    identity = {
        (record["operation_id"], record["attempt_id"], record["profile_id"], record["receipt_id"])
        for record in records
    }
    if len(identity) != 1:
        raise FixtureError("journal-identity-drift")
    phases = [record["phase"] for record in records]
    if phases not in (["prepared"], ["prepared", "committed"], ["prepared", "committed", "acknowledged"]):
        raise FixtureError("journal-phase-order-invalid")
    prior_digest = records[0]["prior_state_sha256"]
    if any(record["prior_state_sha256"] != prior_digest for record in records):
        raise FixtureError("journal-prior-digest-drift")
    if records[0]["profile_id"] in state["revoked_profile_ids"]:
        return {"outcome": "reject", "error": "profile-revoked-before-recovery", "state": state}
    current_digest = sha(state)
    if phases == ["prepared"]:
        if current_digest != prior_digest:
            raise FixtureError("journal-prior-state-mismatch")
        return {"outcome": "rolled-back", "error": None, "state": state}
    committed = records[1]["state_after"]
    if records[-1]["state_after"] != committed:
        raise FixtureError("journal-acknowledgement-state-mismatch")
    if current_digest == sha(committed):
        return {
            "outcome": "clean" if phases[-1] == "acknowledged" else "already-recovered",
            "error": None,
            "state": state,
        }
    if current_digest != prior_digest:
        raise FixtureError("journal-authority-state-diverged")
    validate_transition(state, committed, records[1])
    return {"outcome": "recovered-committed", "error": None, "state": committed}


def validate_fixture(path: Path, expected_sha256: str) -> dict[str, Any]:
    payload = path.read_bytes()
    actual_sha = hashlib.sha256(payload).hexdigest()
    if actual_sha != expected_sha256:
        raise FixtureError(f"fixture-digest-mismatch:expected={expected_sha256}:actual={actual_sha}")
    manifest = exact_object("manifest", strict_loads(payload.decode("utf-8")), TOP_LEVEL_KEYS)
    if manifest["schema"] != "qso.iris-journal-recovery-fixtures.v0":
        raise FixtureError("manifest-schema-invalid")
    if manifest["synthetic_only"] is not True or manifest["operational_authority"] is not False:
        raise FixtureError("manifest-authority-boundary-invalid")
    if not isinstance(manifest["cases"], list):
        raise FixtureError("cases-not-list")
    observed: dict[str, tuple[str, str | None]] = {}
    for value in manifest["cases"]:
        case = exact_object("case", value, CASE_KEYS)
        case_id = require_identifier("case-id", case["case_id"])
        if case_id in observed:
            raise FixtureError(f"duplicate-case-id:{case_id}")
        expected = exact_object("expected", case["expected"], EXPECTED_KEYS)
        try:
            result = reconcile(case["authority_state"], case["journal_records"])
        except FixtureError as exc:
            result = {"outcome": "reject", "error": str(exc), "state": copy.deepcopy(case["authority_state"])}
        state = result["state"]
        actual = {
            "outcome": result["outcome"],
            "error": result["error"],
            "state_version": state["state_version"],
            "seen_attempt_ids": state["seen_attempt_ids"],
            "receipt_count": len(state["receipts"]),
            "state_sha256": sha(state),
        }
        if actual != expected:
            raise FixtureError(f"case-outcome-mismatch:{case_id}:expected={expected!r}:actual={actual!r}")
        observed[case_id] = (actual["outcome"], actual["error"])
    if observed != EXPECTED_CASES:
        raise FixtureError(f"case-coverage-mismatch:expected={sorted(EXPECTED_CASES)}:actual={sorted(observed)}")
    return {
        "status": "pass",
        "fixture_sha256": actual_sha,
        "case_count": len(observed),
        "independent_implementation": True,
        "journal_recovery": True,
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
        print(f"journal fixture validation failed: {exc}")
        return 1
    output = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(output, encoding="utf-8")
    print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
