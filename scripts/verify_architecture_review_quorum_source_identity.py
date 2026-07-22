#!/usr/bin/env python3
"""Fail-closed byte and canonical identity gate for review-quorum corpora.

Raw producer bytes are verified before JSON decoding or semantic validation.
Passing this gate is synthetic conformance evidence only and grants no reviewer,
quorum, decision, activation, merge, publication, or operational authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from scripts.validate_architecture_review_quorum import canonical_sha256, load_strict

BASE_RAW_SHA256 = "dea97fcfd54cd71e9bf38af0c8ca4eeeedd83156ab4d1ae2a7f91513a32485f5"
EXTENSION_RAW_SHA256 = "14ed2b65dea7b3c5fc0b026e839144beff34f07fc416f0a54b77b8acf17a6ed4"
BASE_CANONICAL_SHA256 = "a8b65c3fce4b7cf80fdefab76c497720b2bf17086d431a53f9bacf82e58bd9ec"
EXTENSION_CANONICAL_SHA256 = "6e767141e6c76ec43366b661db0fee9090a56c9ce7d50eda28da7f1094d5e3c2"
MAX_FIXTURE_BYTES = 1_000_000


def verify_source_identity(
    path: Path,
    expected_raw_sha256: str,
    expected_canonical_sha256: str,
) -> dict[str, Any]:
    """Verify exact bytes before allowing strict parse and canonical validation."""
    raw = path.read_bytes()
    if len(raw) > MAX_FIXTURE_BYTES:
        raise ValueError("fixture exceeds one-megabyte identity bound")

    observed_raw_sha256 = hashlib.sha256(raw).hexdigest()
    if observed_raw_sha256 != expected_raw_sha256:
        raise ValueError(
            "raw fixture SHA-256 mismatch: "
            f"expected={expected_raw_sha256} observed={observed_raw_sha256}"
        )

    payload = load_strict(path)
    observed_canonical_sha256 = canonical_sha256(payload)
    if observed_canonical_sha256 != expected_canonical_sha256:
        raise ValueError(
            "canonical fixture SHA-256 mismatch: "
            f"expected={expected_canonical_sha256} "
            f"observed={observed_canonical_sha256}"
        )

    return {
        "path": str(path),
        "size_bytes": len(raw),
        "raw_sha256": observed_raw_sha256,
        "expected_raw_sha256": expected_raw_sha256,
        "canonical_sha256": observed_canonical_sha256,
        "expected_canonical_sha256": expected_canonical_sha256,
        "raw_identity_matches": True,
        "canonical_identity_matches": True,
        "raw_gate_precedes_semantic_validation": True,
        "authority_effect": "none",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--extension", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    report = {
        "schema": "repo1.architecture-review-quorum.source-identity.v1",
        "consumer": "aevespers2/1",
        "base": verify_source_identity(
            args.base, BASE_RAW_SHA256, BASE_CANONICAL_SHA256
        ),
        "extension": verify_source_identity(
            args.extension, EXTENSION_RAW_SHA256, EXTENSION_CANONICAL_SHA256
        ),
        "result": "PASS",
        "reviewer_appointment": False,
        "real_quorum": False,
        "architecture_decision": False,
        "activation_authority": False,
        "operational_authority": False,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
