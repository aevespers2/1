from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .readiness import GateEvidence, MANDATORY_GATES, evaluate_readiness


class DuplicateKeyError(ValueError):
    """Raised when readiness JSON repeats an object key."""


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise DuplicateKeyError(f"duplicate readiness evidence key: {key}")
        value[key] = item
    return value


def _required_string(record: dict[str, Any], field: str, gate: str) -> str:
    value = record.get(field, "")
    if not isinstance(value, str):
        raise ValueError(f"{field} for {gate!r} must be a string")
    return value


def load_evidence(path: str) -> dict[str, GateEvidence]:
    with Path(path).open("r", encoding="utf-8") as handle:
        value: Any = json.load(
            handle,
            object_pairs_hook=_strict_object,
            parse_constant=lambda constant: (_ for _ in ()).throw(
                ValueError(f"non-finite JSON number is not allowed: {constant}")
            ),
        )
    if not isinstance(value, dict):
        raise ValueError("readiness evidence must be a JSON object")

    unknown = sorted(set(value) - set(MANDATORY_GATES))
    if unknown:
        raise ValueError(f"unknown readiness gates: {unknown}")

    parsed: dict[str, GateEvidence] = {}
    for gate, record in value.items():
        if not isinstance(record, dict):
            raise ValueError(f"evidence for {gate!r} must be an object")
        passed = record.get("passed", False)
        if not isinstance(passed, bool):
            raise ValueError(f"passed for {gate!r} must be a boolean")
        parsed[gate] = GateEvidence(
            passed=passed,
            evidence_ref=_required_string(record, "evidence_ref", gate),
            recorded_at=_required_string(record, "recorded_at", gate),
            notes=_required_string(record, "notes", gate),
        )
    return parsed


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate Muse token-assignment readiness.")
    parser.add_argument("evidence", help="Path to readiness evidence JSON")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    report = evaluate_readiness(load_evidence(args.evidence))
    verified = [
        gate
        for gate in MANDATORY_GATES
        if gate not in report.missing and gate not in report.failed
    ]
    payload = {
        "ready": report.ready,
        "missing": list(report.missing),
        "failed": list(report.failed),
        "verified": verified,
    }
    print(json.dumps(payload, indent=2 if args.pretty else None, sort_keys=True))
    return 0 if report.ready else 2


if __name__ == "__main__":
    raise SystemExit(main())
