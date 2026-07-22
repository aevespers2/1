#!/usr/bin/env python3
"""Independent fail-closed consumer for the synthetic lifecycle backup/restore corpus."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

MAX_BYTES = 512 * 1024
SCHEMA = "alistaire.constitutional-lifecycle-backup-restore.corpus.v1"
STATUS = "synthetic_only_non_operational"
SOURCE = "aevespers2/ALISTAIRE-"
PROFILE = "alistaire.constitutional.lifecycle"
ROOT_KEYS = {"schema", "profile_version", "status", "cases"}
CASE_KEYS = {"case_id", "description", "backup", "restore", "expected"}
BACKUP_KEYS = {"phase", "manifest_valid", "source_repository", "profile", "backup_epoch", "state"}
RESTORE_KEYS = {
    "target_repository", "expected_profile", "requested_epoch", "journal_head_sequence",
    "log_floor", "retained_events", "replay_transaction_id",
    "required_suspended_generations", "required_revoked_generations",
}
EXPECTED_KEYS = {"disposition", "reason", "state"}
STATE_KEYS = {
    "sequence", "authority_generation", "credential_generation", "status",
    "suspended_generations", "revoked_generations", "committed_transactions",
    "pending_ack_transaction",
}
EVENT_KEYS = {
    "sequence", "transaction_id", "operation", "authority_generation",
    "credential_generation", "reference_transaction_id",
}
CASE_IDS = {
    "healthy-backup-restore", "stale-backup-complete-log-converges",
    "stale-backup-pruned-log-quarantined", "partial-backup-quarantined",
    "manifest-mismatch-quarantined", "wrong-source-repository-quarantined",
    "wrong-profile-quarantined", "backup-epoch-mismatch-quarantined",
    "backup-ahead-of-journal-quarantined", "revocation-preserved",
    "suspension-preserved", "missing-revocation-quarantined",
    "post-restore-replay-blocked", "unknown-replay-target-quarantined",
    "rollback-across-compaction-converges",
    "rollback-cannot-resurrect-revoked-authority", "lost-ack-remains-pending",
}
STATE_VALUES = {"inactive", "active", "pending_ack", "suspended", "revoked", "rolled_back_pending_ack"}
OPERATIONS = {"replacement", "suspend", "revoke", "credential_rotate", "acknowledge", "rollback"}
REASONS = {
    "state_restored", "log_replay_converged", "restore_log_gap", "backup_incomplete",
    "backup_manifest_mismatch", "backup_source_mismatch", "backup_profile_mismatch",
    "backup_epoch_mismatch", "backup_ahead_of_journal", "revocation_preserved",
    "suspension_preserved", "required_revocation_missing", "replay_blocked",
    "unknown_replay_target", "rollback_pending_ack",
    "revoked_authority_resurrection_blocked", "pending_ack_preserved",
}
PROHIBITED = {"private_key", "secret", "password", "access_token", "credential_value", "biometric", "raw_capture"}


class ContractError(ValueError):
    pass


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ContractError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _constant(value: str) -> None:
    raise ContractError(f"non-finite JSON number: {value}")


def load(raw: bytes) -> tuple[dict[str, Any], str]:
    if len(raw) > MAX_BYTES:
        raise ContractError("fixture exceeds size limit")
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ContractError("fixture is not strict UTF-8") from exc
    try:
        value = json.loads(text, object_pairs_hook=_object, parse_constant=_constant)
    except json.JSONDecodeError as exc:
        raise ContractError(f"malformed JSON: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise ContractError("root must be an object")
    return value, hashlib.sha256(raw).hexdigest()


def exact(value: Any, keys: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        actual = set(value) if isinstance(value, dict) else set()
        raise ContractError(f"{label} fields differ: missing={sorted(keys-actual)}, unknown={sorted(actual-keys)}")
    return value


def uint(value: Any, label: str) -> int:
    if type(value) is not int or value < 0:
        raise ContractError(f"{label} must be a non-negative integer")
    return value


def unique_ints(value: Any, label: str) -> list[int]:
    if not isinstance(value, list) or any(type(item) is not int or item < 0 for item in value):
        raise ContractError(f"{label} must be non-negative integer array")
    if len(value) != len(set(value)):
        raise ContractError(f"{label} contains duplicates")
    return value


def unique_strings(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise ContractError(f"{label} must be non-empty string array")
    if len(value) != len(set(value)):
        raise ContractError(f"{label} contains duplicates")
    return value


def reject_sensitive(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if any(token in key.lower() for token in PROHIBITED):
                raise ContractError(f"prohibited field at {path}.{key}")
            reject_sensitive(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            reject_sensitive(child, f"{path}[{index}]")
    elif isinstance(value, float) and not math.isfinite(value):
        raise ContractError(f"non-finite number at {path}")


def state(value: Any, label: str) -> dict[str, Any]:
    item = exact(value, STATE_KEYS, label)
    uint(item["sequence"], f"{label}.sequence")
    uint(item["authority_generation"], f"{label}.authority_generation")
    uint(item["credential_generation"], f"{label}.credential_generation")
    if item["status"] not in STATE_VALUES:
        raise ContractError(f"{label}.status unsupported")
    suspended = unique_ints(item["suspended_generations"], f"{label}.suspended_generations")
    revoked = unique_ints(item["revoked_generations"], f"{label}.revoked_generations")
    unique_strings(item["committed_transactions"], f"{label}.committed_transactions")
    pending = item["pending_ack_transaction"]
    if pending is not None and (not isinstance(pending, str) or not pending):
        raise ContractError(f"{label}.pending_ack_transaction invalid")
    if set(suspended) & set(revoked):
        raise ContractError(f"{label} overlaps suspension and revocation")
    if item["status"] == "suspended" and item["authority_generation"] not in suspended:
        raise ContractError(f"{label} loses suspension generation")
    if item["status"] == "revoked" and item["authority_generation"] not in revoked:
        raise ContractError(f"{label} loses revocation generation")
    pending_status = item["status"] in {"pending_ack", "rolled_back_pending_ack"}
    if pending_status != (pending is not None):
        raise ContractError(f"{label} pending state is inconsistent")
    return item


def event(value: Any, label: str) -> dict[str, Any]:
    item = exact(value, EVENT_KEYS, label)
    uint(item["sequence"], f"{label}.sequence")
    if not isinstance(item["transaction_id"], str) or not item["transaction_id"]:
        raise ContractError(f"{label}.transaction_id invalid")
    if item["operation"] not in OPERATIONS:
        raise ContractError(f"{label}.operation unsupported")
    uint(item["authority_generation"], f"{label}.authority_generation")
    uint(item["credential_generation"], f"{label}.credential_generation")
    ref = item["reference_transaction_id"]
    if ref is not None and (not isinstance(ref, str) or not ref):
        raise ContractError(f"{label}.reference_transaction_id invalid")
    return item


def clone(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "sequence": item["sequence"], "authority_generation": item["authority_generation"],
        "credential_generation": item["credential_generation"], "status": item["status"],
        "suspended_generations": list(item["suspended_generations"]),
        "revoked_generations": list(item["revoked_generations"]),
        "committed_transactions": list(item["committed_transactions"]),
        "pending_ack_transaction": item["pending_ack_transaction"],
    }


def apply(current: dict[str, Any], entry: dict[str, Any]) -> tuple[dict[str, Any], str | None]:
    output = clone(current)
    tx = entry["transaction_id"]
    if tx in output["committed_transactions"]:
        return output, "duplicate"
    if entry["sequence"] != output["sequence"] + 1:
        return output, "gap"
    operation = entry["operation"]
    generation = entry["authority_generation"]
    credential = entry["credential_generation"]
    if operation == "replacement":
        if output["status"] == "revoked" or generation in output["revoked_generations"]:
            return output, "resurrection"
        if generation != output["authority_generation"] + 1:
            return output, "stale"
        output["authority_generation"] = generation
        output["status"] = "active"
        output["pending_ack_transaction"] = None
    elif operation == "suspend":
        if generation != output["authority_generation"] or credential != output["credential_generation"]:
            return output, "stale"
        if generation not in output["suspended_generations"]:
            output["suspended_generations"].append(generation)
            output["suspended_generations"].sort()
        output["status"] = "suspended"
        output["pending_ack_transaction"] = None
    elif operation == "revoke":
        if generation != output["authority_generation"] or credential != output["credential_generation"]:
            return output, "stale"
        if generation in output["suspended_generations"]:
            output["suspended_generations"].remove(generation)
        if generation not in output["revoked_generations"]:
            output["revoked_generations"].append(generation)
            output["revoked_generations"].sort()
        output["status"] = "revoked"
        output["pending_ack_transaction"] = None
    elif operation == "credential_rotate":
        if generation != output["authority_generation"] or credential != output["credential_generation"] + 1:
            return output, "stale"
        if output["status"] == "revoked":
            return output, "resurrection"
        output["credential_generation"] = credential
        output["status"] = "pending_ack"
        output["pending_ack_transaction"] = tx
    elif operation == "acknowledge":
        if generation != output["authority_generation"] or credential != output["credential_generation"]:
            return output, "stale"
        if entry["reference_transaction_id"] != output["pending_ack_transaction"]:
            return output, "stale"
        output["status"] = "active"
        output["pending_ack_transaction"] = None
    elif operation == "rollback":
        if generation >= output["authority_generation"] or credential != output["credential_generation"]:
            return output, "stale"
        if output["status"] == "revoked" or generation in output["revoked_generations"]:
            return output, "resurrection"
        output["authority_generation"] = generation
        output["status"] = "rolled_back_pending_ack"
        output["pending_ack_transaction"] = tx
    output["sequence"] = entry["sequence"]
    output["committed_transactions"].append(tx)
    return output, None


def derive(case: dict[str, Any]) -> tuple[str, str, dict[str, Any] | None]:
    backup = case["backup"]
    restore = case["restore"]
    if backup["phase"] != "complete" or backup["state"] is None:
        return "quarantined", "backup_incomplete", None
    if backup["manifest_valid"] is not True:
        return "quarantined", "backup_manifest_mismatch", None
    if backup["source_repository"] != SOURCE or restore["target_repository"] != SOURCE:
        return "quarantined", "backup_source_mismatch", None
    if backup["profile"] != PROFILE or restore["expected_profile"] != PROFILE:
        return "quarantined", "backup_profile_mismatch", None
    if backup["backup_epoch"] != restore["requested_epoch"]:
        return "quarantined", "backup_epoch_mismatch", None
    output = clone(backup["state"])
    if output["sequence"] > restore["journal_head_sequence"]:
        return "quarantined", "backup_ahead_of_journal", None
    entries = restore["retained_events"]
    if output["sequence"] < restore["journal_head_sequence"]:
        needed = output["sequence"] + 1
        if restore["log_floor"] > needed or not entries or entries[0]["sequence"] != needed:
            return "quarantined", "restore_log_gap", None
    for entry in entries:
        output, error = apply(output, entry)
        if error == "resurrection":
            return "quarantined", "revoked_authority_resurrection_blocked", None
        if error is not None:
            return "quarantined", "restore_log_gap", None
    if output["sequence"] != restore["journal_head_sequence"]:
        return "quarantined", "restore_log_gap", None
    if not set(restore["required_revoked_generations"]).issubset(output["revoked_generations"]):
        return "quarantined", "required_revocation_missing", None
    if not set(restore["required_suspended_generations"]).issubset(output["suspended_generations"]):
        return "quarantined", "required_revocation_missing", None
    replay = restore["replay_transaction_id"]
    if replay is not None:
        return (("converged", "replay_blocked", output) if replay in output["committed_transactions"]
                else ("quarantined", "unknown_replay_target", None))
    if output["status"] == "revoked":
        return "converged", "revocation_preserved", output
    if output["status"] == "suspended":
        return "converged", "suspension_preserved", output
    if output["status"] == "rolled_back_pending_ack":
        return "converged", "rollback_pending_ack", output
    if output["status"] == "pending_ack":
        return "converged", "pending_ack_preserved", output
    return ("converged", "log_replay_converged", output) if entries else ("converged", "state_restored", output)


def validate(document: dict[str, Any]) -> dict[str, Any]:
    exact(document, ROOT_KEYS, "root")
    if document["schema"] != SCHEMA or document["profile_version"] != "1.0.0" or document["status"] != STATUS:
        raise ContractError("unsupported or operational corpus identity")
    reject_sensitive(document)
    cases = document["cases"]
    if not isinstance(cases, list):
        raise ContractError("cases must be an array")
    observed: list[str] = []
    results: list[dict[str, str]] = []
    for index, value in enumerate(cases):
        item = exact(value, CASE_KEYS, f"cases[{index}]")
        case_id = item["case_id"]
        if not isinstance(case_id, str) or not case_id or not isinstance(item["description"], str) or not item["description"]:
            raise ContractError(f"cases[{index}] identity invalid")
        observed.append(case_id)
        backup = exact(item["backup"], BACKUP_KEYS, f"{case_id}.backup")
        if backup["phase"] not in {"complete", "partial", "absent"} or type(backup["manifest_valid"]) is not bool:
            raise ContractError(f"{case_id}.backup controls invalid")
        if any(not isinstance(backup[key], str) or not backup[key] for key in ("source_repository", "profile")):
            raise ContractError(f"{case_id}.backup identity invalid")
        uint(backup["backup_epoch"], f"{case_id}.backup.backup_epoch")
        if backup["state"] is not None:
            state(backup["state"], f"{case_id}.backup.state")
        restore = exact(item["restore"], RESTORE_KEYS, f"{case_id}.restore")
        if any(not isinstance(restore[key], str) or not restore[key] for key in ("target_repository", "expected_profile")):
            raise ContractError(f"{case_id}.restore identity invalid")
        for key in ("requested_epoch", "journal_head_sequence", "log_floor"):
            uint(restore[key], f"{case_id}.restore.{key}")
        unique_ints(restore["required_suspended_generations"], f"{case_id}.restore.required_suspended_generations")
        unique_ints(restore["required_revoked_generations"], f"{case_id}.restore.required_revoked_generations")
        replay = restore["replay_transaction_id"]
        if replay is not None and (not isinstance(replay, str) or not replay):
            raise ContractError(f"{case_id}.restore.replay_transaction_id invalid")
        if not isinstance(restore["retained_events"], list):
            raise ContractError(f"{case_id}.restore.retained_events must be an array")
        transactions: list[str] = []
        for event_index, value in enumerate(restore["retained_events"]):
            checked = event(value, f"{case_id}.restore.retained_events[{event_index}]")
            transactions.append(checked["transaction_id"])
        if len(transactions) != len(set(transactions)):
            raise ContractError(f"{case_id} has duplicate retained transactions")
        expected = exact(item["expected"], EXPECTED_KEYS, f"{case_id}.expected")
        if expected["disposition"] not in {"converged", "quarantined"} or expected["reason"] not in REASONS:
            raise ContractError(f"{case_id}.expected invalid")
        if expected["state"] is not None:
            state(expected["state"], f"{case_id}.expected.state")
        disposition, reason, output = derive(item)
        if (disposition, reason, output) != (expected["disposition"], expected["reason"], expected["state"]):
            raise ContractError(f"{case_id} disposition drift")
        results.append({"case_id": case_id, "disposition": disposition, "reason": reason})
    if len(observed) != len(set(observed)) or set(observed) != CASE_IDS:
        raise ContractError(f"fixture coverage differs: missing={sorted(CASE_IDS-set(observed))}, unknown={sorted(set(observed)-CASE_IDS)}")
    return {"schema": SCHEMA, "status": "PASS", "case_count": len(results), "results": results}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    try:
        document, digest = load(args.fixture.read_bytes())
        if digest != args.expected_sha256:
            raise ContractError(f"fixture SHA-256 mismatch: expected {args.expected_sha256}, got {digest}")
        report = validate(document)
        report["sha256"] = digest
    except (OSError, ContractError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True))
        return 1
    encoded = json.dumps(report, indent=2, sort_keys=True)
    print(encoded)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(encoded + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
