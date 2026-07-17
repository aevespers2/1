from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .readiness import evaluate_readiness


def load_json(path: str) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("readiness evidence must be a JSON object")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate Muse token-assignment readiness.")
    parser.add_argument("evidence", help="Path to readiness evidence JSON")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    report = evaluate_readiness(load_json(args.evidence))
    payload = {
        "ready": report.ready,
        "missing": list(report.missing),
        "failed": list(report.failed),
        "verified": list(report.verified),
    }
    print(json.dumps(payload, indent=2 if args.pretty else None, sort_keys=True))
    return 0 if report.ready else 2


if __name__ == "__main__":
    raise SystemExit(main())
