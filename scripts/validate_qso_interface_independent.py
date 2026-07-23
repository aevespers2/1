#!/usr/bin/env python3
"""Independent fail-closed consumer for QSO-INTERFACE-COMPATIBILITY-001."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

MAX_BYTES = 1_048_576
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

CONTRACT_ID = "QSO-INTERFACE-COMPATIBILITY-001"
VERSION = "1.0.0"
FACT_ORDER = (
    "source_tuple_current",
    "known_interface",
    "interface_name_match",
    "producer_role_valid",
    "consumer_role_valid",
    "protocol_match",
    "schema_version_match",
    "idempotency_match",
    "retry_policy_match",
    "default_deny_preserved",
    "correction_supported",
    "rollback_supported",
    "evidence_bound",
    "authority_promotion_absent",
)
REASON_BY_FACT = {
    "source_tuple_current": "STALE_SOURCE_TUPLE",
    "known_interface": "UNKNOWN_INTERFACE",
    "interface_name_match": "INTERFACE_NAME_MISMATCH",
    "producer_role_valid": "PRODUCER_ROLE_INVALID",
    "consumer_role_valid": "CONSUMER_ROLE_INVALID",
    "protocol_match": "PROTOCOL_MISMATCH",
    "schema_version_match": "SCHEMA_VERSION_MISMATCH",
    "idempotency_match": "IDEMPOTENCY_MISMATCH",
    "retry_policy_match": "RETRY_POLICY_MISMATCH",
    "default_deny_preserved": "DEFAULT_DENY_NOT_PRESERVED",
    "correction_supported": "CORRECTION_SEMANTICS_MISSING",
    "rollback_supported": "ROLLBACK_SEMANTICS_MISSING",
    "evidence_bound": "EVIDENCE_NOT_BOUND",
    "authority_promotion_absent": "AUTHORITY_PROMOTION_DETECTED",
}
REASON_ORDER = tuple(REASON_BY_FACT[name] for name in FACT_ORDER)
CASE_IDS = (
    "event-ledger-compatible",
    "runtime-report-compatible",
    "stale-source-tuple",
    "unknown-interface",
    "interface-name-mismatch",
    "producer-role-invalid",
    "consumer-role-invalid",
    "protocol-mismatch",
    "schema-version-mismatch",
    "idempotency-mismatch",
    "retry-policy-mismatch",
    "default-deny-not-preserved",
    "correction-semantics-missing",
    "rollback-semantics-missing",
    "evidence-not-bound",
    "authority-promotion-detected",
    "multi-obstruction-order",
)
KNOWN_INTERFACES = {"qso-event-ledger", "qso-runtime-report"}

TUPLE_TOP = {"contract_id", "version", "producer", "consumer", "authority_effect"}
PRODUCER_FIELDS = {
    "repository",
    "pull_request",
    "head_sha",
    "fixture_path",
    "fixture_git_blob",
    "workflow_run",
    "artifact_id",
    "artifact_digest",
    "evidence_expires_at",
}
CONSUMER_FIELDS = {
    "repository",
    "validator_path",
    "test_path",
    "workflow_path",
    "documentation_path",
}


class ContractError(ValueError):
    def __init__(self, code: str, detail: str):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


def _reject_constant(value: str) -> None:
    raise ContractError("INVALID_JSON", f"non-finite number {value}")


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ContractError("INVALID_JSON", f"duplicate key {key}")
        result[key] = value
    return result


def load_bytes(raw: bytes, label: str) -> Any:
    if len(raw) > MAX_BYTES:
        raise ContractError("INVALID_JSON", f"{label} exceeds size bound")
    try:
        text = raw.decode("utf-8", "strict")
    except UnicodeDecodeError as exc:
        raise ContractError("INVALID_JSON", f"{label} is not strict UTF-8") from exc
    try:
        return json.loads(text, object_pairs_hook=_object, parse_constant=_reject_constant)
    except ContractError:
        raise
    except json.JSONDecodeError as exc:
        raise ContractError("INVALID_JSON", f"{label}: {exc.msg}") from exc


def _closed(value: Any, fields: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError("INVALID_STRUCTURE", f"{label} must be object")
    unknown = set(value) - fields
    missing = fields - set(value)
    if unknown:
        raise ContractError("UNKNOWN_FIELD", f"{label}: {sorted(unknown)}")
    if missing:
        raise ContractError("MISSING_FIELD", f"{label}: {sorted(missing)}")
    return value


def _git_blob(raw: bytes) -> str:
    return hashlib.sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest()


def validate_source_tuple(data: Any, fixture_raw: bytes) -> dict[str, Any]:
    root = _closed(data, TUPLE_TOP, "source tuple")
    if root["contract_id"] != CONTRACT_ID or root["version"] != VERSION:
        raise ContractError("SOURCE_TUPLE_DRIFT", "contract identity")
    if root["authority_effect"] != "none":
        raise ContractError(
            "AUTHORITY_PROMOTION_DETECTED", "source tuple authority_effect"
        )

    producer = _closed(root["producer"], PRODUCER_FIELDS, "producer")
    expected_producer = {
        "repository": "aevespers2/QSO-FABRIC",
        "pull_request": 21,
        "head_sha": "25036a5cfcea79e204a4660ddd1af09c054935b1",
        "fixture_path": "fixtures/qso-interface-compatibility-v1.json",
        "fixture_git_blob": "143b80448cb4623682669ab8e6a9599239dd5847",
        "workflow_run": 29986841042,
        "artifact_id": 8555344357,
        "artifact_digest": "sha256:09be1df24f4ab8b08708dd521c6720f4c95195d3e4379cecaad6d1a4b026a238",
        "evidence_expires_at": "2026-10-21T06:59:56Z",
    }
    if producer != expected_producer:
        raise ContractError("SOURCE_TUPLE_DRIFT", "producer tuple differs")
    if (
        type(producer["pull_request"]) is not int
        or type(producer["workflow_run"]) is not int
        or type(producer["artifact_id"]) is not int
    ):
        raise ContractError(
            "SOURCE_TUPLE_DRIFT", "numeric identities must be integers"
        )
    if not SHA40.fullmatch(producer["head_sha"]) or not SHA40.fullmatch(
        producer["fixture_git_blob"]
    ):
        raise ContractError("SOURCE_TUPLE_DRIFT", "invalid Git identity")
    if not SHA256.fullmatch(producer["artifact_digest"]):
        raise ContractError("SOURCE_TUPLE_DRIFT", "invalid artifact digest")
    if not TIMESTAMP.fullmatch(producer["evidence_expires_at"]):
        raise ContractError("SOURCE_TUPLE_DRIFT", "invalid evidence expiration")

    consumer = _closed(root["consumer"], CONSUMER_FIELDS, "consumer")
    expected_consumer = {
        "repository": "aevespers2/1",
        "validator_path": "scripts/validate_qso_interface_independent.py",
        "test_path": "tests/test_qso_interface_independent.py",
        "workflow_path": ".github/workflows/qso-interface-parity.yml",
        "documentation_path": "docs/QSO_INTERFACE_CONFORMANCE.md",
    }
    if consumer != expected_consumer:
        raise ContractError("SOURCE_TUPLE_DRIFT", "consumer tuple differs")

    actual_blob = _git_blob(fixture_raw)
    if actual_blob != producer["fixture_git_blob"]:
        raise ContractError("SOURCE_BYTES_DRIFT", f"fixture Git blob {actual_blob}")
    return {
        "producer_head": producer["head_sha"],
        "fixture_git_blob": actual_blob,
        "fixture_sha256": hashlib.sha256(fixture_raw).hexdigest(),
    }


def derive(facts: dict[str, bool]) -> tuple[str, list[str]]:
    reasons = [REASON_BY_FACT[name] for name in FACT_ORDER if facts[name] is False]
    disposition = (
        "BLOCKED" if reasons else "COMPATIBLE_PENDING_ARCHITECTURE_APPROVAL"
    )
    return disposition, reasons


def validate_fixture(data: Any) -> dict[str, Any]:
    root = _closed(
        data,
        {"contract_id", "version", "fact_order", "reason_order", "cases"},
        "fixture",
    )
    if root["contract_id"] != CONTRACT_ID or root["version"] != VERSION:
        raise ContractError("CONTRACT_IDENTITY_DRIFT", "fixture contract identity")
    if root["fact_order"] != list(FACT_ORDER):
        raise ContractError("FACT_ORDER_DRIFT", "fact_order")
    if root["reason_order"] != list(REASON_ORDER):
        raise ContractError("REASON_ORDER_DRIFT", "reason_order")
    cases = root["cases"]
    if not isinstance(cases, list):
        raise ContractError("INVALID_STRUCTURE", "cases must be array")
    if len(cases) != len(CASE_IDS):
        raise ContractError(
            "CASE_COVERAGE_DRIFT", f"expected {len(CASE_IDS)} cases"
        )

    observed_ids: list[str] = []
    results: list[dict[str, Any]] = []
    for index, raw_case in enumerate(cases):
        case = _closed(
            raw_case,
            {"case_id", "interface", "facts", "expected"},
            f"cases[{index}]",
        )
        case_id = case["case_id"]
        if not isinstance(case_id, str) or not case_id:
            raise ContractError("INVALID_CASE", f"cases[{index}].case_id")
        observed_ids.append(case_id)
        if len(set(observed_ids)) != len(observed_ids):
            raise ContractError("DUPLICATE_CASE", case_id)

        interface = case["interface"]
        if not isinstance(interface, str) or not interface:
            raise ContractError("INVALID_CASE", f"{case_id}.interface")

        facts = _closed(case["facts"], set(FACT_ORDER), f"{case_id}.facts")
        for name in FACT_ORDER:
            if type(facts[name]) is not bool:
                raise ContractError("INVALID_FACT_TYPE", f"{case_id}.{name}")
        if facts["known_interface"] and interface not in KNOWN_INTERFACES:
            raise ContractError("INTERFACE_DECLARATION_DRIFT", case_id)

        expected = _closed(
            case["expected"], {"disposition", "reasons"}, f"{case_id}.expected"
        )
        if not isinstance(expected["reasons"], list) or any(
            not isinstance(reason, str) for reason in expected["reasons"]
        ):
            raise ContractError("INVALID_EXPECTED_RESULT", case_id)
        disposition, reasons = derive(facts)
        if expected["disposition"] != disposition or expected["reasons"] != reasons:
            raise ContractError("EXPECTED_RESULT_DRIFT", case_id)
        results.append(
            {"case_id": case_id, "disposition": disposition, "reasons": reasons}
        )

    if tuple(observed_ids) != CASE_IDS:
        raise ContractError("CASE_COVERAGE_DRIFT", "case IDs or order differ")
    return {
        "contract_id": CONTRACT_ID,
        "version": VERSION,
        "case_count": len(results),
        "reason_count": len(REASON_ORDER),
        "positive_count": sum(
            result["disposition"].startswith("COMPATIBLE") for result in results
        ),
        "blocked_count": sum(
            result["disposition"] == "BLOCKED" for result in results
        ),
        "results": results,
        "authority_effect": "none",
    }


def evaluate(tuple_raw: bytes, fixture_raw: bytes) -> dict[str, Any]:
    try:
        tuple_data = load_bytes(tuple_raw, "source tuple")
        source = validate_source_tuple(tuple_data, fixture_raw)
        fixture_data = load_bytes(fixture_raw, "producer fixture")
        result = validate_fixture(fixture_data)
        result["source"] = source
        return {
            "disposition": "EVIDENCE_SATISFIED_AT_RECORDED_SYNTHETIC_TUPLE",
            **result,
        }
    except ContractError as exc:
        return {
            "disposition": "BLOCKED",
            "reason_codes": [exc.code],
            "detail": exc.detail,
            "authority_effect": "none",
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tuple", required=True, type=Path)
    parser.add_argument("--fixture", required=True, type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    result = evaluate(args.tuple.read_bytes(), args.fixture.read_bytes())
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return (
        0
        if result["disposition"]
        == "EVIDENCE_SATISFIED_AT_RECORDED_SYNTHETIC_TUPLE"
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
