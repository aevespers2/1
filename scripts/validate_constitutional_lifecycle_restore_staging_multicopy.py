#!/usr/bin/env python3
"""Independent authority-side verifier for staged multi-copy lifecycle restores."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

MAX_BYTES = 512 * 1024
SCHEMA_ID = "alistaire.constitutional-lifecycle-restore-staging-multicopy.corpus.v1"
NON_OPERATIONAL_STATUS = "synthetic_only_non_operational"
PRODUCER_REPOSITORY = "aevespers2/ALISTAIRE-"
LIFECYCLE_PROFILE = "alistaire.constitutional.lifecycle"

ROOT_KEYS = frozenset({"schema", "profile_version", "status", "cases"})
CASE_KEYS = frozenset({"case_id", "description", "copies", "request", "expected"})
COPY_KEYS = frozenset({
    "copy_id", "available", "manifest_valid", "source_repository", "profile",
    "set_id", "epoch", "state",
})
REQUEST_KEYS = frozenset({
    "target_repository", "expected_profile", "current_epoch", "minimum_quorum",
    "selected_copy_ids", "phase", "commit_marker", "retry_of",
})
RESULT_KEYS = frozenset({"disposition", "reason", "state"})
STATE_KEYS = frozenset({
    "sequence", "authority_generation", "credential_generation", "status",
    "suspended_generations", "revoked_generations", "committed_transactions",
    "pending_ack_transaction",
})
CASE_COVERAGE = frozenset({
    "healthy-quorum-commit",
    "one-copy-inaccessible-quorum-met",
    "quorum-not-met",
    "conflicting-state-same-epoch",
    "split-epochs",
    "stale-epoch-anti-rollback",
    "manifest-mismatch-reduces-quorum",
    "verify-only-staged",
    "interrupted-before-commit-aborts",
    "interrupted-after-commit-recovers",
    "retry-after-commit-idempotent",
    "wrong-source-quarantined",
    "wrong-profile-quarantined",
    "revocation-preserved",
    "suspension-preserved",
    "all-copies-inaccessible",
    "selected-copy-missing",
})
VALID_STATES = frozenset({"inactive", "active", "pending_ack", "suspended", "revoked", "rolled_back_pending_ack"})
VALID_PHASES = frozenset({"verify", "commit", "interrupted_before_commit", "interrupted_after_commit", "retry"})
VALID_RESULTS = frozenset({"staged", "converged", "aborted", "quarantined"})
VALID_REASONS = frozenset({
    "restore_committed",
    "restore_quorum_not_met",
    "restore_copy_conflict",
    "restore_epoch_conflict",
    "restore_anti_rollback",
    "restore_verified_not_committed",
    "restore_interrupted_before_commit",
    "restore_commit_recovered",
    "restore_retry_idempotent",
    "restore_source_mismatch",
    "restore_profile_mismatch",
    "restore_selected_copy_missing",
})
SENSITIVE_NAMES = frozenset({
    "private_key", "secret", "password", "access_token", "credential_value",
    "biometric", "raw_capture", "live_endpoint",
})


class ContractError(ValueError):
    pass


def _object_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name, value in pairs:
        if name in out:
            raise ContractError(f"duplicate key: {name}")
        out[name] = value
    return out


def _no_nonfinite(token: str) -> None:
    raise ContractError(f"non-finite number: {token}")


def decode(raw: bytes) -> tuple[dict[str, Any], str]:
    if len(raw) > MAX_BYTES:
        raise ContractError("fixture exceeds size bound")
    try:
        text = raw.decode("utf-8", "strict")
    except UnicodeDecodeError as exc:
        raise ContractError("fixture is not strict UTF-8") from exc
    try:
        root = json.loads(text, object_pairs_hook=_object_without_duplicates, parse_constant=_no_nonfinite)
    except json.JSONDecodeError as exc:
        raise ContractError(f"invalid JSON: {exc.msg}") from exc
    if not isinstance(root, dict):
        raise ContractError("root must be an object")
    return root, hashlib.sha256(raw).hexdigest()


def exact_object(value: Any, keys: frozenset[str], where: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError(f"{where} must be an object")
    actual = frozenset(value)
    if actual != keys:
        raise ContractError(
            f"{where} field mismatch: missing={sorted(keys - actual)}, unknown={sorted(actual - keys)}"
        )
    return value


def text(value: Any, where: str) -> str:
    if not isinstance(value, str) or not value:
        raise ContractError(f"{where} must be a non-empty string")
    return value


def natural(value: Any, where: str) -> int:
    if type(value) is not int or value < 0:
        raise ContractError(f"{where} must be a non-negative integer")
    return value


def positive(value: Any, where: str) -> int:
    if type(value) is not int or value < 1:
        raise ContractError(f"{where} must be a positive integer")
    return value


def unique_texts(value: Any, where: str) -> list[str]:
    if not isinstance(value, list):
        raise ContractError(f"{where} must be an array")
    out = [text(item, f"{where}[]") for item in value]
    if len(out) != len(set(out)):
        raise ContractError(f"{where} contains duplicates")
    return out


def unique_naturals(value: Any, where: str) -> list[int]:
    if not isinstance(value, list):
        raise ContractError(f"{where} must be an array")
    out = [natural(item, f"{where}[]") for item in value]
    if len(out) != len(set(out)):
        raise ContractError(f"{where} contains duplicates")
    return out


def inspect_state(value: Any, where: str) -> dict[str, Any]:
    state = exact_object(value, STATE_KEYS, where)
    natural(state["sequence"], f"{where}.sequence")
    natural(state["authority_generation"], f"{where}.authority_generation")
    natural(state["credential_generation"], f"{where}.credential_generation")
    if state["status"] not in VALID_STATES:
        raise ContractError(f"{where}.status is unsupported")
    suspended = unique_naturals(state["suspended_generations"], f"{where}.suspended_generations")
    revoked = unique_naturals(state["revoked_generations"], f"{where}.revoked_generations")
    unique_texts(state["committed_transactions"], f"{where}.committed_transactions")
    pending = state["pending_ack_transaction"]
    if pending is not None:
        text(pending, f"{where}.pending_ack_transaction")
    if set(suspended).intersection(revoked):
        raise ContractError(f"{where} overlaps suspended and revoked generations")
    generation = state["authority_generation"]
    if state["status"] == "suspended" and generation not in suspended:
        raise ContractError(f"{where} loses suspended generation")
    if state["status"] == "revoked" and generation not in revoked:
        raise ContractError(f"{where} loses revoked generation")
    pending_status = state["status"] in {"pending_ack", "rolled_back_pending_ack"}
    if pending_status != (pending is not None):
        raise ContractError(f"{where} pending acknowledgment state is inconsistent")
    return state


def inspect_copy(value: Any, where: str) -> dict[str, Any]:
    item = exact_object(value, COPY_KEYS, where)
    text(item["copy_id"], f"{where}.copy_id")
    if type(item["available"]) is not bool:
        raise ContractError(f"{where}.available must be Boolean")
    if type(item["manifest_valid"]) is not bool:
        raise ContractError(f"{where}.manifest_valid must be Boolean")
    text(item["source_repository"], f"{where}.source_repository")
    text(item["profile"], f"{where}.profile")
    text(item["set_id"], f"{where}.set_id")
    natural(item["epoch"], f"{where}.epoch")
    inspect_state(item["state"], f"{where}.state")
    return item


def inspect_request(value: Any, where: str) -> dict[str, Any]:
    request = exact_object(value, REQUEST_KEYS, where)
    text(request["target_repository"], f"{where}.target_repository")
    text(request["expected_profile"], f"{where}.expected_profile")
    natural(request["current_epoch"], f"{where}.current_epoch")
    positive(request["minimum_quorum"], f"{where}.minimum_quorum")
    selected = unique_texts(request["selected_copy_ids"], f"{where}.selected_copy_ids")
    if not selected:
        raise ContractError(f"{where}.selected_copy_ids cannot be empty")
    if request["phase"] not in VALID_PHASES:
        raise ContractError(f"{where}.phase is unsupported")
    if type(request["commit_marker"]) is not bool:
        raise ContractError(f"{where}.commit_marker must be Boolean")
    retry = request["retry_of"]
    if retry is not None:
        text(retry, f"{where}.retry_of")
    if (request["phase"] == "retry") != (retry is not None):
        raise ContractError(f"{where}.retry_of does not match retry phase")
    return request


def state_fingerprint(state: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(state, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def project(case: dict[str, Any]) -> tuple[str, str, dict[str, Any] | None]:
    by_id = {item["copy_id"]: item for item in case["copies"]}
    request = case["request"]
    selected_ids = request["selected_copy_ids"]
    if any(copy_id not in by_id for copy_id in selected_ids):
        return "quarantined", "restore_selected_copy_missing", None

    candidates = [
        by_id[copy_id]
        for copy_id in selected_ids
        if by_id[copy_id]["available"] and by_id[copy_id]["manifest_valid"]
    ]
    if len(candidates) < request["minimum_quorum"]:
        return "quarantined", "restore_quorum_not_met", None

    if request["target_repository"] != PRODUCER_REPOSITORY or any(
        item["source_repository"] != PRODUCER_REPOSITORY for item in candidates
    ):
        return "quarantined", "restore_source_mismatch", None
    if request["expected_profile"] != LIFECYCLE_PROFILE or any(
        item["profile"] != LIFECYCLE_PROFILE for item in candidates
    ):
        return "quarantined", "restore_profile_mismatch", None

    identities = {(item["set_id"], item["epoch"]) for item in candidates}
    if len(identities) != 1:
        return "quarantined", "restore_epoch_conflict", None
    epoch = candidates[0]["epoch"]
    if epoch < request["current_epoch"]:
        return "quarantined", "restore_anti_rollback", None

    fingerprints = {state_fingerprint(item["state"]) for item in candidates}
    if len(fingerprints) != 1:
        return "quarantined", "restore_copy_conflict", None
    restored = candidates[0]["state"]

    phase = request["phase"]
    committed = request["commit_marker"]
    if phase == "verify":
        return (
            ("quarantined", "restore_copy_conflict", None)
            if committed
            else ("staged", "restore_verified_not_committed", restored)
        )
    if phase == "interrupted_before_commit":
        return (
            ("quarantined", "restore_copy_conflict", None)
            if committed
            else ("aborted", "restore_interrupted_before_commit", None)
        )
    if phase == "interrupted_after_commit":
        return (
            ("converged", "restore_commit_recovered", restored)
            if committed
            else ("aborted", "restore_interrupted_before_commit", None)
        )
    if phase == "retry":
        return (
            ("converged", "restore_retry_idempotent", restored)
            if committed
            else ("aborted", "restore_interrupted_before_commit", None)
        )
    return (
        ("converged", "restore_committed", restored)
        if committed
        else ("aborted", "restore_interrupted_before_commit", None)
    )


def scan_sensitive_names(value: Any, where: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            lowered = key.lower()
            if any(token in lowered for token in SENSITIVE_NAMES):
                raise ContractError(f"prohibited field at {where}.{key}")
            scan_sensitive_names(child, f"{where}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            scan_sensitive_names(child, f"{where}[{index}]")


def validate(root: dict[str, Any]) -> dict[str, Any]:
    exact_object(root, ROOT_KEYS, "root")
    if root["schema"] != SCHEMA_ID:
        raise ContractError("schema identifier drift")
    if root["profile_version"] != "1.0.0":
        raise ContractError("profile version drift")
    if root["status"] != NON_OPERATIONAL_STATUS:
        raise ContractError("fixture must remain synthetic-only and non-operational")
    if not isinstance(root["cases"], list):
        raise ContractError("cases must be an array")

    seen: list[str] = []
    for index, raw_case in enumerate(root["cases"]):
        case = exact_object(raw_case, CASE_KEYS, f"cases[{index}]")
        case_id = text(case["case_id"], f"cases[{index}].case_id")
        text(case["description"], f"cases[{index}].description")
        if not isinstance(case["copies"], list) or not case["copies"]:
            raise ContractError(f"cases[{index}].copies must be a non-empty array")
        copies = [inspect_copy(item, f"cases[{index}].copies[{copy_index}]")
                  for copy_index, item in enumerate(case["copies"])]
        copy_ids = [item["copy_id"] for item in copies]
        if len(copy_ids) != len(set(copy_ids)):
            raise ContractError(f"cases[{index}] contains duplicate copy identities")
        request = inspect_request(case["request"], f"cases[{index}].request")
        if request["minimum_quorum"] > len(request["selected_copy_ids"]):
            raise ContractError(f"cases[{index}] quorum exceeds selected copies")
        expected = exact_object(case["expected"], RESULT_KEYS, f"cases[{index}].expected")
        if expected["disposition"] not in VALID_RESULTS:
            raise ContractError(f"cases[{index}].expected.disposition is unsupported")
        if expected["reason"] not in VALID_REASONS:
            raise ContractError(f"cases[{index}].expected.reason is unsupported")
        if expected["state"] is not None:
            inspect_state(expected["state"], f"cases[{index}].expected.state")
        actual = project(case)
        wanted = (expected["disposition"], expected["reason"], expected["state"])
        if actual != wanted:
            raise ContractError(f"{case_id}: evaluator produced {actual!r}, expected {wanted!r}")
        seen.append(case_id)

    if len(seen) != len(set(seen)):
        raise ContractError("duplicate case_id")
    if frozenset(seen) != CASE_COVERAGE:
        raise ContractError(
            f"case coverage drift: missing={sorted(CASE_COVERAGE - frozenset(seen))}, "
            f"unknown={sorted(frozenset(seen) - CASE_COVERAGE)}"
        )
    scan_sensitive_names(root)
    return {
        "schema": SCHEMA_ID,
        "status": NON_OPERATIONAL_STATUS,
        "case_count": len(seen),
        "case_ids": sorted(seen),
        "errors": [],
        "authority_effect": "none",
        "implementation": "repository-1-independent-authority-side",
    }


def validate_bytes(raw: bytes, expected_sha256: str | None = None) -> dict[str, Any]:
    root, digest = decode(raw)
    if expected_sha256 is not None and digest != expected_sha256:
        raise ContractError(f"fixture digest mismatch: expected {expected_sha256}, got {digest}")
    report = validate(root)
    report["sha256"] = digest
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = validate_bytes(args.fixture.read_bytes(), args.expected_sha256)
    except (OSError, ContractError) as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, sort_keys=True))
        return 1
    output = json.dumps(report, indent=2, sort_keys=True) + "\n"
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(output, encoding="utf-8")
    print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
