#!/usr/bin/env python3
"""Fail-closed producer-source and evidence tuple gate for retention corpora.

The tuple and exact producer bytes are verified before the retention corpus is
decoded or semantically evaluated. Passing this gate is synthetic conformance
evidence only and grants no archive, renewal, deletion, claim, publication, or
operational authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "repo1.evidence-retention.source-tuple.v1"
MAX_TUPLE_BYTES = 64_000
MAX_FIXTURE_BYTES = 1_000_000

EXPECTED_PRODUCER = {
    "repository": "aevespers2/qso-field.github.io",
    "pull_request": 24,
    "head_sha": "155437912906a0119a087d63bf4ed889368a4a9f",
    "path": "fixtures/evidence-retention-renewal-v1.json",
    "git_blob": "f624abed1f72fbb7e6f2dbe5b443cce891abc05c",
    "sha256": "9d4c78fc8c9b54a91bd272a4bc929dc368d3af23b62cf2eec1d833b9a7ec449f",
}
EXPECTED_EVIDENCE = {
    "run_id": 29970998778,
    "run_conclusion": "success",
    "artifact_id": 8549658807,
    "artifact_name": "evidence-retention-renewal-155437912906a0119a087d63bf4ed889368a4a9f",
    "artifact_digest": "sha256:803e80829c29c8f1bfaf916e76d0e9f14ce191c3d65b4bc543490aa98d86021a",
    "created_at": "2026-07-23T01:08:09Z",
    "expires_at": "2026-08-22T01:08:09Z",
}
TOP_KEYS = frozenset({
    "schema", "observation_generation", "current", "producer",
    "workflow_evidence", "resolution", "authority_effect",
})
PRODUCER_KEYS = frozenset(EXPECTED_PRODUCER)
EVIDENCE_KEYS = frozenset({*EXPECTED_EVIDENCE, "artifact_available"})
RESOLUTION_KEYS = frozenset({
    "resolved_at", "resolver_id", "verifier_id",
    "resolver_and_verifier_independent", "supersedes",
})


def _reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_nonfinite(token: str) -> None:
    raise ValueError(f"non-finite number is prohibited: {token}")


def _assert_finite(value: Any, location: str = "root") -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"non-finite number at {location}")
    if isinstance(value, dict):
        for key, child in value.items():
            _assert_finite(child, f"{location}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _assert_finite(child, f"{location}[{index}]")


def _load_strict(path: Path, maximum: int) -> Any:
    raw = path.read_bytes()
    if len(raw) > maximum:
        raise ValueError(f"{path}: input exceeds {maximum} bytes")
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{path}: input is not strict UTF-8: {exc}") from exc
    payload = json.loads(
        text,
        object_pairs_hook=_reject_duplicates,
        parse_constant=_reject_nonfinite,
    )
    _assert_finite(payload)
    return payload


def _require_exact_keys(value: dict[str, Any], expected: frozenset[str], location: str) -> None:
    actual = frozenset(value)
    missing = sorted(expected - actual)
    unknown = sorted(actual - expected)
    if missing or unknown:
        raise ValueError(f"{location}: missing={missing} unknown={unknown}")


def _parse_utc(value: str, location: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError(f"{location}: timestamp must be an RFC3339 UTC string")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ValueError(f"{location}: invalid timestamp") from exc
    if parsed.tzinfo != timezone.utc:
        raise ValueError(f"{location}: timestamp must use UTC")
    return parsed


def _git_blob_sha(raw: bytes) -> str:
    return hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()


def validate_tuple(payload: Any, as_of: datetime) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("root must be an object")
    _require_exact_keys(payload, TOP_KEYS, "root")
    if payload["schema"] != SCHEMA:
        raise ValueError("unexpected tuple schema")
    generation = payload["observation_generation"]
    if type(generation) is not int or generation < 1:
        raise ValueError("observation_generation must be a positive integer")
    if payload["current"] is not True:
        raise ValueError("tuple is not marked current")
    if payload["authority_effect"] != "none":
        raise ValueError("tuple must not claim authority")

    producer = payload["producer"]
    if not isinstance(producer, dict):
        raise ValueError("producer must be an object")
    _require_exact_keys(producer, PRODUCER_KEYS, "producer")
    if producer != EXPECTED_PRODUCER:
        mismatches = sorted(
            key for key, expected in EXPECTED_PRODUCER.items()
            if producer.get(key) != expected
        )
        raise ValueError(f"producer source tuple mismatch: {mismatches}")

    evidence = payload["workflow_evidence"]
    if not isinstance(evidence, dict):
        raise ValueError("workflow_evidence must be an object")
    _require_exact_keys(evidence, EVIDENCE_KEYS, "workflow_evidence")
    for key, expected in EXPECTED_EVIDENCE.items():
        if evidence[key] != expected:
            raise ValueError(f"workflow_evidence.{key}: unexpected value")
    if evidence["artifact_available"] is not True:
        raise ValueError("producer evidence artifact is unavailable")
    created_at = _parse_utc(evidence["created_at"], "workflow_evidence.created_at")
    expires_at = _parse_utc(evidence["expires_at"], "workflow_evidence.expires_at")
    if expires_at <= created_at:
        raise ValueError("artifact expiry must follow creation")
    if as_of >= expires_at:
        raise ValueError("producer evidence artifact has expired")

    resolution = payload["resolution"]
    if not isinstance(resolution, dict):
        raise ValueError("resolution must be an object")
    _require_exact_keys(resolution, RESOLUTION_KEYS, "resolution")
    resolved_at = _parse_utc(resolution["resolved_at"], "resolution.resolved_at")
    if resolved_at < created_at or resolved_at > as_of:
        raise ValueError("resolution timestamp is outside the valid observation window")
    resolver_id = resolution["resolver_id"]
    verifier_id = resolution["verifier_id"]
    if not isinstance(resolver_id, str) or not resolver_id.strip():
        raise ValueError("resolver_id must be a non-empty string")
    if not isinstance(verifier_id, str) or not verifier_id.strip():
        raise ValueError("verifier_id must be a non-empty string")
    if resolver_id == verifier_id:
        raise ValueError("resolver and verifier identities collide")
    if resolution["resolver_and_verifier_independent"] is not True:
        raise ValueError("resolver/verifier independence is not established")
    supersedes = resolution["supersedes"]
    if not isinstance(supersedes, list) or any(
        not isinstance(item, str) or len(item) != 64
        or any(char not in "0123456789abcdef" for char in item)
        for item in supersedes
    ):
        raise ValueError("supersedes must be a list of lowercase SHA-256 strings")
    if len(supersedes) != len(set(supersedes)):
        raise ValueError("supersedes contains duplicate identities")
    if generation == 1 and supersedes:
        raise ValueError("first observation generation must not supersede prior tuples")
    if generation > 1 and not supersedes:
        raise ValueError("later observation generation is missing supersession linkage")

    return {
        "schema": SCHEMA,
        "observation_generation": generation,
        "producer": producer,
        "workflow_evidence": evidence,
        "resolution": resolution,
        "artifact_current_at_check": True,
        "source_tuple_current": True,
        "resolver_verifier_independent": True,
        "authority_effect": "none",
    }


def verify_fixture_bytes(path: Path, producer: dict[str, Any]) -> dict[str, Any]:
    raw = path.read_bytes()
    if len(raw) > MAX_FIXTURE_BYTES:
        raise ValueError("producer fixture exceeds one-megabyte source bound")
    observed_sha256 = hashlib.sha256(raw).hexdigest()
    observed_blob = _git_blob_sha(raw)
    if observed_sha256 != producer["sha256"]:
        raise ValueError("producer fixture SHA-256 mismatch")
    if observed_blob != producer["git_blob"]:
        raise ValueError("producer fixture Git-blob mismatch")
    return {
        "path": str(path),
        "size_bytes": len(raw),
        "sha256": observed_sha256,
        "git_blob": observed_blob,
        "verified_before_semantic_parse": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tuple", dest="tuple_path", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    as_of = _parse_utc(args.as_of, "as_of")
    payload = _load_strict(args.tuple_path, MAX_TUPLE_BYTES)
    report = validate_tuple(payload, as_of)
    report["fixture"] = verify_fixture_bytes(args.fixture, report["producer"])
    report["checked_at"] = args.as_of
    report["result"] = "PASS"
    report["semantic_validation_permitted"] = True
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
