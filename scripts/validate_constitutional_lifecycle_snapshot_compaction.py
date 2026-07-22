#!/usr/bin/env python3
"""Independent fail-closed consumer for the synthetic snapshot/compaction corpus."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

MAX_BYTES = 512 * 1024
SCHEMA = "alistaire.constitutional-lifecycle-snapshot-compaction.corpus.v1"
STATUS = "synthetic_only_non_operational"
ROOT_FIELDS = frozenset({"schema", "profile_version", "status", "cases"})
CASE_FIELDS = frozenset({"case_id", "description", "initial_state", "journal_floor", "journal", "snapshot", "compaction", "expected"})
STATE_FIELDS = frozenset({"sequence", "authority_generation", "credential_generation", "status", "suspended_generations", "revoked_generations", "committed_transactions", "pending_ack_transaction"})
ENTRY_FIELDS = frozenset({"sequence", "transaction_id", "operation", "authority_generation", "credential_generation", "reference_transaction_id", "payload_digest", "phase"})
SNAPSHOT_FIELDS = frozenset({"phase", "sequence", "digest_valid", "state"})
COMPACTION_FIELDS = frozenset({"phase", "cutoff_sequence", "interruption"})
EXPECTED_FIELDS = frozenset({"disposition", "reason", "state"})
CASE_IDS = frozenset({
    "healthy-compaction", "torn-snapshot-full-log-replay", "torn-snapshot-after-prune-quarantined",
    "snapshot-log-divergence-quarantined", "compaction-interrupted-before-prune-converges",
    "compaction-interrupted-after-prune-converges", "duplicate-commit-idempotent",
    "conflicting-duplicate-commit-quarantined", "lost-ack-preserves-pending-state",
    "suspension-survives-compaction", "revocation-survives-compaction",
    "replacement-cannot-resurrect-revoked-authority", "log-sequence-gap-quarantined",
    "compaction-cutoff-beyond-snapshot-quarantined", "acknowledgment-after-compaction-converges",
})
OPERATIONS = frozenset({"replacement", "suspend", "revoke", "credential_rotate", "acknowledge", "rollback"})
STATES = frozenset({"inactive", "active", "pending_ack", "suspended", "revoked", "rolled_back_pending_ack"})
REASONS = frozenset({
    "state_converged", "full_log_replay", "snapshot_unrecoverable_after_prune", "snapshot_log_divergence",
    "duplicate_commit_idempotent", "conflicting_duplicate_transaction", "pending_ack_preserved",
    "suspension_preserved", "revocation_preserved", "superseded_authority_resurrection_blocked",
    "journal_sequence_gap", "compaction_cutoff_beyond_snapshot", "acknowledgment_converged",
})
PROHIBITED = ("private_key", "secret", "password", "access_token", "credential_value", "biometric", "raw_capture", "live_endpoint")


class ContractError(ValueError):
    pass


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, value in pairs:
        if key in output:
            raise ContractError(f"duplicate JSON key: {key}")
        output[key] = value
    return output


def _reject_constant(value: str) -> None:
    raise ContractError(f"non-finite JSON number: {value}")


def decode(raw: bytes) -> tuple[dict[str, Any], str]:
    if len(raw) > MAX_BYTES:
        raise ContractError(f"fixture exceeds {MAX_BYTES} bytes")
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ContractError("fixture must be strict UTF-8") from exc
    try:
        value = json.loads(text, object_pairs_hook=_strict_object, parse_constant=_reject_constant)
    except json.JSONDecodeError as exc:
        raise ContractError(f"malformed JSON: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise ContractError("fixture root must be an object")
    return value, hashlib.sha256(raw).hexdigest()


def _fields(value: Any, expected: frozenset[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != expected:
        actual = set(value) if isinstance(value, dict) else set()
        raise ContractError(f"{label}: fields differ; missing={sorted(expected-actual)}, unknown={sorted(actual-expected)}")
    return value


def _walk(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if any(token in key.lower() for token in PROHIBITED):
                raise ContractError(f"prohibited field at {path}.{key}")
            _walk(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _walk(child, f"{path}[{index}]")
    elif isinstance(value, float) and not math.isfinite(value):
        raise ContractError(f"non-finite number at {path}")


def _nat(value: Any, label: str) -> int:
    if type(value) is not int or value < 0:
        raise ContractError(f"{label} must be a non-negative integer")
    return value


def _unique_ints(value: Any, label: str) -> tuple[int, ...]:
    if not isinstance(value, list) or any(type(x) is not int or x < 0 for x in value) or len(value) != len(set(value)):
        raise ContractError(f"{label} must contain unique non-negative integers")
    return tuple(value)


def _unique_strings(value: Any, label: str) -> tuple[str, ...]:
    if not isinstance(value, list) or any(not isinstance(x, str) or not x for x in value) or len(value) != len(set(value)):
        raise ContractError(f"{label} must contain unique non-empty strings")
    return tuple(value)


@dataclass(frozen=True)
class LedgerState:
    sequence: int
    authority_generation: int
    credential_generation: int
    status: str
    suspended_generations: tuple[int, ...]
    revoked_generations: tuple[int, ...]
    committed_transactions: tuple[str, ...]
    pending_ack_transaction: str | None

    @classmethod
    def parse(cls, value: Any, label: str) -> "LedgerState":
        item = _fields(value, STATE_FIELDS, label)
        status = item["status"]
        if status not in STATES:
            raise ContractError(f"{label}.status is unsupported")
        pending = item["pending_ack_transaction"]
        if pending is not None and (not isinstance(pending, str) or not pending):
            raise ContractError(f"{label}.pending_ack_transaction is invalid")
        state = cls(
            _nat(item["sequence"], f"{label}.sequence"),
            _nat(item["authority_generation"], f"{label}.authority_generation"),
            _nat(item["credential_generation"], f"{label}.credential_generation"),
            status,
            _unique_ints(item["suspended_generations"], f"{label}.suspended_generations"),
            _unique_ints(item["revoked_generations"], f"{label}.revoked_generations"),
            _unique_strings(item["committed_transactions"], f"{label}.committed_transactions"),
            pending,
        )
        if set(state.suspended_generations) & set(state.revoked_generations):
            raise ContractError(f"{label}: generation cannot be suspended and revoked")
        if status == "suspended" and state.authority_generation not in state.suspended_generations:
            raise ContractError(f"{label}: suspension generation is not retained")
        if status == "revoked" and state.authority_generation not in state.revoked_generations:
            raise ContractError(f"{label}: revocation generation is not retained")
        if status in {"pending_ack", "rolled_back_pending_ack"} and pending is None:
            raise ContractError(f"{label}: pending state lacks transaction")
        if status not in {"pending_ack", "rolled_back_pending_ack"} and pending is not None:
            raise ContractError(f"{label}: non-pending state retains transaction")
        return state

    def json(self) -> dict[str, Any]:
        return {
            "sequence": self.sequence,
            "authority_generation": self.authority_generation,
            "credential_generation": self.credential_generation,
            "status": self.status,
            "suspended_generations": list(self.suspended_generations),
            "revoked_generations": list(self.revoked_generations),
            "committed_transactions": list(self.committed_transactions),
            "pending_ack_transaction": self.pending_ack_transaction,
        }


@dataclass(frozen=True)
class JournalEntry:
    sequence: int
    transaction_id: str
    operation: str
    authority_generation: int
    credential_generation: int
    reference_transaction_id: str | None
    payload_digest: str
    phase: str

    @classmethod
    def parse(cls, value: Any, label: str) -> "JournalEntry":
        item = _fields(value, ENTRY_FIELDS, label)
        tx = item["transaction_id"]
        if not isinstance(tx, str) or not tx:
            raise ContractError(f"{label}.transaction_id is invalid")
        operation = item["operation"]
        if operation not in OPERATIONS:
            raise ContractError(f"{label}.operation is unsupported")
        reference = item["reference_transaction_id"]
        if reference is not None and (not isinstance(reference, str) or not reference):
            raise ContractError(f"{label}.reference_transaction_id is invalid")
        digest = item["payload_digest"]
        if not isinstance(digest, str) or len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
            raise ContractError(f"{label}.payload_digest is not lowercase SHA-256 hex")
        phase = item["phase"]
        if phase not in {"prepared", "committed"}:
            raise ContractError(f"{label}.phase is unsupported")
        return cls(_nat(item["sequence"], f"{label}.sequence"), tx, operation,
                   _nat(item["authority_generation"], f"{label}.authority_generation"),
                   _nat(item["credential_generation"], f"{label}.credential_generation"),
                   reference, digest, phase)

    def identity(self) -> tuple[Any, ...]:
        return (self.operation, self.authority_generation, self.credential_generation,
                self.reference_transaction_id, self.payload_digest, self.phase)


class IndependentEvaluator:
    def apply(self, state: LedgerState, entry: JournalEntry) -> tuple[LedgerState, str | None]:
        base = replace(state, sequence=entry.sequence)
        if entry.phase == "prepared":
            return base, None
        if entry.transaction_id in state.committed_transactions:
            return base, "duplicate"
        txs = state.committed_transactions + (entry.transaction_id,)
        if entry.operation == "replacement":
            if state.status == "revoked" or entry.authority_generation in state.revoked_generations:
                return base, "resurrection"
            if entry.authority_generation != state.authority_generation + 1 or entry.credential_generation != state.credential_generation:
                return base, "stale"
            return replace(base, authority_generation=entry.authority_generation, status="active",
                           committed_transactions=txs, pending_ack_transaction=None), None
        if entry.operation == "suspend":
            if entry.authority_generation != state.authority_generation or entry.credential_generation != state.credential_generation:
                return base, "stale"
            suspended = tuple(sorted(set(state.suspended_generations) | {entry.authority_generation}))
            return replace(base, status="suspended", suspended_generations=suspended,
                           committed_transactions=txs, pending_ack_transaction=None), None
        if entry.operation == "revoke":
            if entry.authority_generation != state.authority_generation or entry.credential_generation != state.credential_generation:
                return base, "stale"
            revoked = tuple(sorted(set(state.revoked_generations) | {entry.authority_generation}))
            suspended = tuple(x for x in state.suspended_generations if x != entry.authority_generation)
            return replace(base, status="revoked", revoked_generations=revoked,
                           suspended_generations=suspended, committed_transactions=txs,
                           pending_ack_transaction=None), None
        if entry.operation == "credential_rotate":
            if state.status == "revoked":
                return base, "resurrection"
            if entry.authority_generation != state.authority_generation or entry.credential_generation != state.credential_generation + 1:
                return base, "stale"
            return replace(base, credential_generation=entry.credential_generation, status="pending_ack",
                           committed_transactions=txs, pending_ack_transaction=entry.transaction_id), None
        if entry.operation == "acknowledge":
            if entry.authority_generation != state.authority_generation or entry.credential_generation != state.credential_generation:
                return base, "stale"
            if entry.reference_transaction_id != state.pending_ack_transaction:
                if entry.reference_transaction_id in state.committed_transactions:
                    return replace(base, committed_transactions=txs), "ack_idempotent"
                return base, "stale"
            return replace(base, status="active", committed_transactions=txs,
                           pending_ack_transaction=None), None
        if entry.operation == "rollback":
            if state.status == "revoked" or entry.authority_generation in state.revoked_generations:
                return base, "resurrection"
            if entry.authority_generation >= state.authority_generation or entry.credential_generation != state.credential_generation:
                return base, "stale"
            return replace(base, authority_generation=entry.authority_generation,
                           status="rolled_back_pending_ack", committed_transactions=txs,
                           pending_ack_transaction=entry.transaction_id), None
        raise ContractError(f"unsupported operation: {entry.operation}")

    def derive(self, case: dict[str, Any]) -> tuple[str, str, dict[str, Any] | None]:
        initial = LedgerState.parse(case["initial_state"], f"{case['case_id']}.initial_state")
        entries = [JournalEntry.parse(item, f"{case['case_id']}.journal[{i}]") for i, item in enumerate(case["journal"])]
        if entries != sorted(entries, key=lambda item: item.sequence):
            raise ContractError(f"{case['case_id']}: journal is not sequence ordered")
        snap = case["snapshot"]
        comp = case["compaction"]
        if comp["phase"] == "committed" and snap["phase"] == "committed" and comp["cutoff_sequence"] > snap["sequence"]:
            return "quarantined", "compaction_cutoff_beyond_snapshot", None
        valid_snapshot = snap["phase"] == "committed" and snap["digest_valid"] is True
        if valid_snapshot:
            state = LedgerState.parse(snap["state"], f"{case['case_id']}.snapshot.state")
            if state.sequence != snap["sequence"]:
                return "quarantined", "snapshot_log_divergence", None
            prefix = [item for item in entries if item.sequence <= state.sequence]
            if case["journal_floor"] <= initial.sequence + 1 and prefix:
                replay = initial
                identities: dict[str, tuple[Any, ...]] = {}
                for expected_sequence, item in enumerate(prefix, start=initial.sequence + 1):
                    if item.sequence != expected_sequence:
                        return "quarantined", "journal_sequence_gap", None
                    old = identities.get(item.transaction_id)
                    if old is not None and old != item.identity():
                        return "quarantined", "conflicting_duplicate_transaction", None
                    identities.setdefault(item.transaction_id, item.identity())
                    replay, signal = self.apply(replay, item)
                    if signal == "resurrection":
                        return "quarantined", "superseded_authority_resurrection_blocked", None
                if replay.json() != state.json():
                    return "quarantined", "snapshot_log_divergence", None
        else:
            if case["journal_floor"] != initial.sequence + 1:
                return "quarantined", "snapshot_unrecoverable_after_prune", None
            state = initial
        remaining = [item for item in entries if item.sequence > state.sequence]
        expected_sequence = max(case["journal_floor"], state.sequence + 1)
        if remaining and remaining[0].sequence != expected_sequence:
            return "quarantined", "journal_sequence_gap", None
        identities: dict[str, tuple[Any, ...]] = {}
        duplicate = False
        ack = False
        for item in remaining:
            if item.sequence != state.sequence + 1:
                return "quarantined", "journal_sequence_gap", None
            old = identities.get(item.transaction_id)
            if old is not None:
                if old != item.identity():
                    return "quarantined", "conflicting_duplicate_transaction", None
                duplicate = True
            else:
                identities[item.transaction_id] = item.identity()
            state, signal = self.apply(state, item)
            if signal == "duplicate":
                duplicate = True
            elif signal == "ack_idempotent":
                ack = True
            elif signal in {"stale", "resurrection"}:
                return "quarantined", "superseded_authority_resurrection_blocked", None
        if duplicate:
            reason = "duplicate_commit_idempotent"
        elif state.status in {"pending_ack", "rolled_back_pending_ack"}:
            reason = "pending_ack_preserved"
        elif state.status == "suspended":
            reason = "suspension_preserved"
        elif state.status == "revoked":
            reason = "revocation_preserved"
        elif not valid_snapshot:
            reason = "full_log_replay"
        elif ack or any(item.operation == "acknowledge" for item in remaining):
            reason = "acknowledgment_converged"
        else:
            reason = "state_converged"
        return "converged", reason, state.json()


def validate(raw: bytes) -> dict[str, Any]:
    data, digest = decode(raw)
    root = _fields(data, ROOT_FIELDS, "root")
    if root["schema"] != SCHEMA or root["profile_version"] != "1.0.0" or root["status"] != STATUS:
        raise ContractError("unexpected schema, version, or status")
    if not isinstance(root["cases"], list):
        raise ContractError("cases must be an array")
    _walk(root)
    seen: set[str] = set()
    results: list[dict[str, str]] = []
    evaluator = IndependentEvaluator()
    for raw_case in root["cases"]:
        case = _fields(raw_case, CASE_FIELDS, "case")
        case_id = case["case_id"]
        if not isinstance(case_id, str) or not case_id or case_id in seen:
            raise ContractError(f"invalid or duplicate case_id: {case_id!r}")
        seen.add(case_id)
        if not isinstance(case["description"], str) or len(case["description"].strip()) < 20:
            raise ContractError(f"{case_id}: description is too short")
        _nat(case["journal_floor"], f"{case_id}.journal_floor")
        if not isinstance(case["journal"], list):
            raise ContractError(f"{case_id}: journal must be an array")
        snap = _fields(case["snapshot"], SNAPSHOT_FIELDS, f"{case_id}.snapshot")
        if snap["phase"] not in {"absent", "prepared", "committed", "torn"} or type(snap["digest_valid"]) is not bool:
            raise ContractError(f"{case_id}: invalid snapshot metadata")
        _nat(snap["sequence"], f"{case_id}.snapshot.sequence")
        LedgerState.parse(snap["state"], f"{case_id}.snapshot.state")
        comp = _fields(case["compaction"], COMPACTION_FIELDS, f"{case_id}.compaction")
        if comp["phase"] not in {"none", "prepared", "committed"} or comp["interruption"] not in {"none", "before_snapshot_commit", "after_snapshot_commit_before_prune", "after_prune_before_ack"}:
            raise ContractError(f"{case_id}: invalid compaction metadata")
        _nat(comp["cutoff_sequence"], f"{case_id}.compaction.cutoff_sequence")
        expected = _fields(case["expected"], EXPECTED_FIELDS, f"{case_id}.expected")
        if expected["disposition"] not in {"converged", "quarantined"} or expected["reason"] not in REASONS:
            raise ContractError(f"{case_id}: invalid expected disposition")
        expected_state = None if expected["state"] is None else LedgerState.parse(expected["state"], f"{case_id}.expected.state").json()
        actual = evaluator.derive(case)
        wanted = (expected["disposition"], expected["reason"], expected_state)
        if actual != wanted:
            raise ContractError(f"{case_id}: expected {wanted!r}, derived {actual!r}")
        results.append({"case_id": case_id, "disposition": actual[0], "reason": actual[1]})
    if seen != CASE_IDS:
        raise ContractError(f"fixture coverage differs; missing={sorted(CASE_IDS-seen)}, unknown={sorted(seen-CASE_IDS)}")
    return {"schema": SCHEMA, "status": STATUS, "sha256": digest, "case_count": len(results), "cases": results,
            "independent_consumer": True, "grants_authority": False, "mutates_state": False}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = validate(args.fixture.read_bytes())
        if report["sha256"] != args.expected_sha256:
            raise ContractError(f"fixture digest mismatch: expected {args.expected_sha256}, got {report['sha256']}")
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(report, sort_keys=True))
        return 0
    except (OSError, ContractError) as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
