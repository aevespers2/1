from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .readiness import GateEvidence, MANDATORY_GATES, evaluate_readiness


def load_evidence(path: str) -> dict[str, GateEvidence]:
    with Path(path).open("r", encoding="utf-8") as handle:
        value: Any = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("readiness evidence must be a JSON object")

    parsed: dict[str, GateEvidence] = {}
    for gate, record in value.items():
        if not isinstance(record, dict):
            raise ValueError(f"evidence for {gate!r} must be an object")
        parsed[gate] = GateEvidence(
            passed=bool(record.get("passed", False)),
            evidence_ref=str(record.get("evidence_ref", "")),
            recorded_at=str(record.get("recorded_at", "")),
            notes=str(record.get("notes", "")),
        )
    return parsed


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate Muse token-assignment readiness.")
    parser.add_argument("evidence", help="Path to readiness evidence JSON")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    report = evaluate_readiness(load_evidence(args.evidence))
    verified = [gate for gate in MANDATORY_GATES if gate not in report.missing and gate not in report.failed]
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
