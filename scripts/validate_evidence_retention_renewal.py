#!/usr/bin/env python3
"""Independent consumer for the QSO Field evidence-retention corpus.

The consumer deliberately does not import the producer validator. It verifies
strict JSON structure, derives outcomes from an independent rule table, and
emits a deterministic synthetic-conformance report. It performs no archive,
renewal, deletion, claim, publication, or operational action.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Callable

PROFILE_ID = "qso.evidence-retention-renewal-tombstone-corpus"
PROFILE_VERSION = 1
EXPECTED_CASE_COUNT = 20

FACT_FIELDS = (
    "source_identity_known",
    "artifact_digest_verified",
    "artifact_available",
    "retention_deadline_known",
    "retention_active",
    "tombstone_required",
    "tombstone_present",
    "renewal_attempted",
    "renewal_new_generation",
    "renewal_source_matches",
    "renewal_artifact_reverified",
    "renewal_independent_verifier",
    "claim_current",
    "claim_rebound_to_renewal",
    "claim_downgraded_or_withdrawn",
    "legal_hold_active",
    "legal_hold_promoted_to_currentness",
    "copy_or_migration",
    "copy_reverified",
    "deletion_requested",
    "deletion_propagated",
    "rollback_reintroduces_expired",
    "claim_validity_within_retention",
)
REASON_ORDER = (
    "SOURCE_IDENTITY_UNKNOWN",
    "ARTIFACT_DIGEST_UNVERIFIED",
    "RETENTION_DEADLINE_UNKNOWN",
    "EVIDENCE_EXPIRED",
    "ARTIFACT_UNAVAILABLE",
    "TOMBSTONE_MISSING",
    "RENEWAL_MUTATES_PRIOR_GENERATION",
    "RENEWAL_SOURCE_MISMATCH",
    "RENEWAL_ARTIFACT_UNVERIFIED",
    "RENEWAL_INDEPENDENCE_MISSING",
    "CLAIM_NOT_REBOUND_OR_DOWNGRADED",
    "LEGAL_HOLD_PROMOTED_TO_CURRENTNESS",
    "COPY_NOT_REVERIFIED",
    "DELETION_PROPAGATION_INCOMPLETE",
    "ROLLBACK_REINTRODUCES_EXPIRED_EVIDENCE",
    "RETENTION_CLAIM_WINDOW_MISMATCH",
)
DISPOSITIONS = (
    "EVIDENCE_CURRENT",
    "EVIDENCE_RENEWED_PENDING_CLAIM_REBINDING",
    "EVIDENCE_HISTORICAL",
    "EVIDENCE_TOMBSTONED",
    "BLOCKED",
)
TOP_KEYS = frozenset({"profile_id", "version", "fact_fields", "reason_order", "dispositions", "cases"})
CASE_KEYS = frozenset({"case_id", "facts", "expected"})
EXPECTED_KEYS = frozenset({"disposition", "reasons"})
PROHIBITED_KEY_FRAGMENTS = (
    "secret", "password", "private_key", "credential", "access_token",
    "biometric", "iris", "protected_template", "legal_hold_payload",
)

Predicate = Callable[[dict[str, bool]], bool]
RULES: tuple[tuple[str, Predicate], ...] = (
    ("SOURCE_IDENTITY_UNKNOWN", lambda f: not f["source_identity_known"]),
    ("ARTIFACT_DIGEST_UNVERIFIED", lambda f: not f["artifact_digest_verified"]),
    ("RETENTION_DEADLINE_UNKNOWN", lambda f: not f["retention_deadline_known"]),
    ("EVIDENCE_EXPIRED", lambda f: not f["retention_active"] and f["claim_current"]),
    ("ARTIFACT_UNAVAILABLE", lambda f: not f["artifact_available"] and not f["tombstone_present"]),
    ("TOMBSTONE_MISSING", lambda f: f["tombstone_required"] and not f["tombstone_present"]),
    ("RENEWAL_MUTATES_PRIOR_GENERATION", lambda f: f["renewal_attempted"] and not f["renewal_new_generation"]),
    ("RENEWAL_SOURCE_MISMATCH", lambda f: f["renewal_attempted"] and not f["renewal_source_matches"]),
    ("RENEWAL_ARTIFACT_UNVERIFIED", lambda f: f["renewal_attempted"] and not f["renewal_artifact_reverified"]),
    ("RENEWAL_INDEPENDENCE_MISSING", lambda f: f["renewal_attempted"] and not f["renewal_independent_verifier"]),
    (
        "CLAIM_NOT_REBOUND_OR_DOWNGRADED",
        lambda f: f["renewal_attempted"]
        and f["renewal_new_generation"]
        and f["claim_current"]
        and not f["claim_rebound_to_renewal"]
        and not f["claim_downgraded_or_withdrawn"],
    ),
    ("LEGAL_HOLD_PROMOTED_TO_CURRENTNESS", lambda f: f["legal_hold_active"] and f["legal_hold_promoted_to_currentness"]),
    ("COPY_NOT_REVERIFIED", lambda f: f["copy_or_migration"] and not f["copy_reverified"]),
    ("DELETION_PROPAGATION_INCOMPLETE", lambda f: f["deletion_requested"] and not f["deletion_propagated"]),
    ("ROLLBACK_REINTRODUCES_EXPIRED_EVIDENCE", lambda f: f["rollback_reintroduces_expired"]),
    ("RETENTION_CLAIM_WINDOW_MISMATCH", lambda f: not f["claim_validity_within_retention"]),
)


def _reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, child in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key: {key}")
        value[key] = child
    return value


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


def _reject_sensitive_keys(value: Any, location: str = "root") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            lowered = key.lower()
            if any(fragment in lowered for fragment in PROHIBITED_KEY_FRAGMENTS):
                raise ValueError(f"prohibited sensitive field at {location}.{key}")
            _reject_sensitive_keys(child, f"{location}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_sensitive_keys(child, f"{location}[{index}]")


def strict_load(path: Path) -> Any:
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ValueError(f"fixture is not strict UTF-8: {exc}") from exc
    payload = json.loads(text, object_pairs_hook=_reject_duplicates, parse_constant=_reject_nonfinite)
    _assert_finite(payload)
    return payload


def _require_exact_keys(value: dict[str, Any], expected: frozenset[str], location: str) -> None:
    actual = frozenset(value)
    missing = sorted(expected - actual)
    unknown = sorted(actual - expected)
    if missing or unknown:
        raise ValueError(f"{location}: missing={missing} unknown={unknown}")


def evaluate(facts: dict[str, bool]) -> tuple[str, list[str]]:
    reasons = [reason for reason, predicate in RULES if predicate(facts)]
    if reasons:
        return "BLOCKED", reasons
    if not facts["artifact_available"] and facts["tombstone_present"] and not facts["claim_current"]:
        return "EVIDENCE_TOMBSTONED", []
    if not facts["retention_active"] and not facts["claim_current"] and facts["claim_downgraded_or_withdrawn"]:
        return "EVIDENCE_HISTORICAL", []
    if facts["renewal_attempted"] and facts["renewal_new_generation"] and not facts["claim_rebound_to_renewal"]:
        return "EVIDENCE_RENEWED_PENDING_CLAIM_REBINDING", []
    return "EVIDENCE_CURRENT", []


def validate_payload(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        raise ValueError("top level must be an object")
    _reject_sensitive_keys(payload)
    _require_exact_keys(payload, TOP_KEYS, "root")
    if payload["profile_id"] != PROFILE_ID or payload["version"] != PROFILE_VERSION:
        raise ValueError("unexpected profile identity")
    if tuple(payload["fact_fields"]) != FACT_FIELDS:
        raise ValueError("fact registry or order drift")
    if tuple(payload["reason_order"]) != REASON_ORDER:
        raise ValueError("reason registry or order drift")
    if tuple(payload["dispositions"]) != DISPOSITIONS:
        raise ValueError("disposition registry or order drift")
    cases = payload["cases"]
    if not isinstance(cases, list) or len(cases) != EXPECTED_CASE_COUNT:
        raise ValueError(f"cases must contain exactly {EXPECTED_CASE_COUNT} entries")

    seen: set[str] = set()
    covered_reasons: set[str] = set()
    covered_dispositions: set[str] = set()
    reports: list[dict[str, Any]] = []
    expected_fact_keys = frozenset(FACT_FIELDS)
    expected_reasons = frozenset(REASON_ORDER)

    for index, case in enumerate(cases):
        location = f"cases[{index}]"
        if not isinstance(case, dict):
            raise ValueError(f"{location} must be an object")
        _require_exact_keys(case, CASE_KEYS, location)
        case_id = case["case_id"]
        if not isinstance(case_id, str) or not case_id.strip() or case_id in seen:
            raise ValueError(f"invalid or duplicate case_id: {case_id!r}")
        seen.add(case_id)

        facts = case["facts"]
        if not isinstance(facts, dict):
            raise ValueError(f"{case_id}.facts must be an object")
        _require_exact_keys(facts, expected_fact_keys, f"{case_id}.facts")
        if any(type(value) is not bool for value in facts.values()):
            raise ValueError(f"{case_id}: every fact must be Boolean")

        expected = case["expected"]
        if not isinstance(expected, dict):
            raise ValueError(f"{case_id}.expected must be an object")
        _require_exact_keys(expected, EXPECTED_KEYS, f"{case_id}.expected")
        disposition = expected["disposition"]
        reasons = expected["reasons"]
        if disposition not in DISPOSITIONS:
            raise ValueError(f"{case_id}: unknown disposition")
        if not isinstance(reasons, list) or any(type(reason) is not str for reason in reasons):
            raise ValueError(f"{case_id}: reasons must be strings")
        if len(reasons) != len(set(reasons)) or any(reason not in expected_reasons for reason in reasons):
            raise ValueError(f"{case_id}: duplicate or unknown reason")
        canonical_reasons = [reason for reason in REASON_ORDER if reason in set(reasons)]
        if reasons != canonical_reasons:
            raise ValueError(f"{case_id}: reasons are not in canonical order")

        derived_disposition, derived_reasons = evaluate(facts)
        if (disposition, reasons) != (derived_disposition, derived_reasons):
            raise ValueError(
                f"{case_id}: expected {(disposition, reasons)!r}, "
                f"derived {(derived_disposition, derived_reasons)!r}"
            )
        covered_reasons.update(derived_reasons)
        covered_dispositions.add(derived_disposition)
        reports.append({"case_id": case_id, "disposition": derived_disposition, "reasons": derived_reasons})

    missing_reasons = sorted(set(REASON_ORDER) - covered_reasons)
    missing_dispositions = sorted(set(DISPOSITIONS) - covered_dispositions)
    if missing_reasons:
        raise ValueError(f"fixture does not cover reasons: {missing_reasons}")
    if missing_dispositions:
        raise ValueError(f"fixture does not cover dispositions: {missing_dispositions}")
    return reports


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    payload = strict_load(args.fixture)
    cases = validate_payload(payload)
    raw = args.fixture.read_bytes()
    report = {
        "schema": "repo1.evidence-retention-renewal.validation.v1",
        "source_fixture_sha256": hashlib.sha256(raw).hexdigest(),
        "source_fixture_git_blob": hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest(),
        "case_count": len(cases),
        "reason_count": len(REASON_ORDER),
        "disposition_counts": {
            disposition: sum(case["disposition"] == disposition for case in cases)
            for disposition in DISPOSITIONS
        },
        "cases": cases,
        "independent_consumer": True,
        "authority_activated": False,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"validated {len(cases)} independent evidence-retention cases")
    print(f"fixture_sha256={report['source_fixture_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
