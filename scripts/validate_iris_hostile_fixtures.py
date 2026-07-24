#!/usr/bin/env python3
"""Independently validate the synthetic iris hostile-context fixture corpus."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EXPECTED_CASES = {
    "valid-baseline": "accept",
    "wrong-eye": "eye-side-mismatch",
    "wrong-device": "device-mismatch",
    "stale-generation": "stale-generation",
    "replayed-attempt": "attempt-replay",
    "corrupted-helper-data-digest": "helper-data-digest-mismatch",
    "revoked-profile": "profile-revoked",
    "profile-replaced": "profile-replaced",
    "recovery-required": "recovery-not-complete",
    "recovery-completed-replacement": "accept",
}
HEX_64 = re.compile(r"^[0-9a-f]{64}$")
IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9._:-]{2,127}$")
ATTEMPT_KEYS = {
    "schema",
    "attempt_id",
    "profile_id",
    "generation",
    "subject_ref",
    "eye_side",
    "device_ref",
    "capture_digest",
    "helper_data_digest",
    "created_at",
    "status",
}
CONTEXT_KEYS = {
    "expected_profile_id",
    "current_generation",
    "expected_subject_ref",
    "expected_eye_side",
    "expected_device_ref",
    "expected_helper_data_digest",
    "now",
    "max_age_seconds",
    "seen_attempt_ids",
    "revoked_profile_ids",
    "replacement_profile_id",
    "recovery_state",
}
TOP_LEVEL_KEYS = {
    "schema",
    "synthetic_only",
    "raw_biometric_material_present",
    "production_key_material_present",
    "baseline",
    "cases",
}


class FixtureError(ValueError):
    """Raised when the shared synthetic fixture corpus violates its contract."""


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise FixtureError(f"duplicate-key:{key}")
        result[key] = value
    return result


def reject_non_finite(value: str) -> None:
    raise FixtureError(f"non-finite-number:{value}")


def strict_loads(text: str) -> Any:
    try:
        return json.loads(
            text,
            object_pairs_hook=reject_duplicate_keys,
            parse_constant=reject_non_finite,
        )
    except FixtureError:
        raise
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise FixtureError(f"invalid-json:{exc}") from exc


def exact_object(name: str, value: Any, expected: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise FixtureError(f"{name}-not-object")
    keys = set(value)
    if keys != expected:
        raise FixtureError(
            f"{name}-fields:missing={sorted(expected - keys)}:"
            f"unknown={sorted(keys - expected)}"
        )
    return dict(value)


def require_identifier(name: str, value: Any) -> str:
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
        raise FixtureError(f"{name}-invalid")
    return value


def require_digest(name: str, value: Any) -> str:
    if not isinstance(value, str) or not HEX_64.fullmatch(value):
        raise FixtureError(f"{name}-invalid")
    return value


def parse_timestamp(name: str, value: Any) -> datetime:
    if not isinstance(value, str):
        raise FixtureError(f"{name}-invalid")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise FixtureError(f"{name}-invalid") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise FixtureError(f"{name}-missing-offset")
    return parsed.astimezone(timezone.utc)


def screen(attempt: Any, context: Any) -> str:
    attempt = exact_object("attempt", attempt, ATTEMPT_KEYS)
    context = exact_object("context", context, CONTEXT_KEYS)

    if attempt["schema"] != "qso.iris-verification-attempt.v0":
        raise FixtureError("unsupported-attempt-schema")
    for field in ("attempt_id", "profile_id", "subject_ref", "device_ref"):
        require_identifier(field, attempt[field])
    generation = attempt["generation"]
    if type(generation) is not int or generation < 1:
        raise FixtureError("generation-invalid")
    if attempt["eye_side"] not in {"left", "right"}:
        raise FixtureError("eye-side-invalid")
    require_digest("capture-digest", attempt["capture_digest"])
    require_digest("helper-data-digest", attempt["helper_data_digest"])
    created_at = parse_timestamp("created-at", attempt["created_at"])
    if attempt["status"] != "proposal-created":
        raise FixtureError("attempt-status-invalid")

    for field in (
        "expected_profile_id",
        "expected_subject_ref",
        "expected_device_ref",
    ):
        require_identifier(field, context[field])
    if context["expected_eye_side"] not in {"left", "right"}:
        raise FixtureError("expected-eye-side-invalid")
    require_digest(
        "expected-helper-data-digest",
        context["expected_helper_data_digest"],
    )
    current_generation = context["current_generation"]
    if type(current_generation) is not int or current_generation < 1:
        raise FixtureError("current-generation-invalid")
    maximum_age = context["max_age_seconds"]
    if type(maximum_age) is not int or not 1 <= maximum_age <= 86_400:
        raise FixtureError("maximum-age-invalid")
    now = parse_timestamp("now", context["now"])

    for field in ("seen_attempt_ids", "revoked_profile_ids"):
        values = context[field]
        if not isinstance(values, list):
            raise FixtureError(f"{field}-not-list")
        if not all(
            isinstance(value, str) and IDENTIFIER.fullmatch(value)
            for value in values
        ):
            raise FixtureError(f"{field}-invalid")
        if len(values) != len(set(values)):
            raise FixtureError(f"{field}-duplicate")

    replacement = context["replacement_profile_id"]
    if replacement is not None:
        require_identifier("replacement-profile-id", replacement)
    recovery = context["recovery_state"]
    if recovery not in {"normal", "recovery-required", "recovery-completed"}:
        raise FixtureError("recovery-state-invalid")
    if recovery == "recovery-completed" and replacement is None:
        raise FixtureError("recovery-completed-without-replacement")

    profile_id = attempt["profile_id"]
    if profile_id in context["revoked_profile_ids"]:
        raise FixtureError("profile-revoked")
    if replacement is not None and profile_id != replacement:
        raise FixtureError("profile-replaced")
    if recovery == "recovery-required":
        raise FixtureError("recovery-not-complete")
    if profile_id != context["expected_profile_id"]:
        raise FixtureError("profile-mismatch")
    if generation < current_generation:
        raise FixtureError("stale-generation")
    if generation > current_generation:
        raise FixtureError("future-generation")
    if attempt["subject_ref"] != context["expected_subject_ref"]:
        raise FixtureError("subject-mismatch")
    if attempt["eye_side"] != context["expected_eye_side"]:
        raise FixtureError("eye-side-mismatch")
    if attempt["device_ref"] != context["expected_device_ref"]:
        raise FixtureError("device-mismatch")
    if attempt["helper_data_digest"] != context["expected_helper_data_digest"]:
        raise FixtureError("helper-data-digest-mismatch")
    if attempt["attempt_id"] in context["seen_attempt_ids"]:
        raise FixtureError("attempt-replay")

    age_seconds = (now - created_at).total_seconds()
    if age_seconds < 0:
        raise FixtureError("future-attempt")
    if age_seconds > maximum_age:
        raise FixtureError("stale-attempt")
    return "accept"


def validate_fixture(path: Path, expected_sha256: str) -> dict[str, Any]:
    payload = path.read_bytes()
    actual_sha256 = hashlib.sha256(payload).hexdigest()
    if actual_sha256 != expected_sha256:
        raise FixtureError(
            f"fixture-digest-mismatch:expected={expected_sha256}:actual={actual_sha256}"
        )
    manifest = strict_loads(payload.decode("utf-8"))
    manifest = exact_object("manifest", manifest, TOP_LEVEL_KEYS)
    if manifest["schema"] != "qso.iris-synthetic-context-fixtures.v0":
        raise FixtureError("manifest-schema-invalid")
    if manifest["synthetic_only"] is not True:
        raise FixtureError("fixture-not-synthetic-only")
    if manifest["raw_biometric_material_present"] is not False:
        raise FixtureError("raw-biometric-material-present")
    if manifest["production_key_material_present"] is not False:
        raise FixtureError("production-key-material-present")

    baseline = exact_object("baseline", manifest["baseline"], {"attempt", "context"})
    cases = manifest["cases"]
    if not isinstance(cases, list):
        raise FixtureError("cases-not-list")

    outcomes: dict[str, str] = {}
    for case in cases:
        if not isinstance(case, dict):
            raise FixtureError("case-not-object")
        expected_keys = {
            "case_id",
            "expected",
            "attempt_overrides",
            "context_overrides",
        }
        if case.get("expected") == "reject":
            expected_keys.add("error")
        case = exact_object("case", case, expected_keys)
        case_id = require_identifier("case-id", case["case_id"])
        if case_id in outcomes:
            raise FixtureError(f"duplicate-case-id:{case_id}")
        if not isinstance(case["attempt_overrides"], dict):
            raise FixtureError(f"attempt-overrides-invalid:{case_id}")
        if not isinstance(case["context_overrides"], dict):
            raise FixtureError(f"context-overrides-invalid:{case_id}")

        attempt = copy.deepcopy(baseline["attempt"])
        context = copy.deepcopy(baseline["context"])
        attempt.update(case["attempt_overrides"])
        context.update(case["context_overrides"])
        try:
            result = screen(attempt, context)
        except FixtureError as exc:
            result = str(exc)

        expected = "accept" if case["expected"] == "accept" else case["error"]
        if result != expected:
            raise FixtureError(
                f"case-outcome-mismatch:{case_id}:expected={expected}:actual={result}"
            )
        outcomes[case_id] = result

    if outcomes != EXPECTED_CASES:
        raise FixtureError(
            f"case-coverage-mismatch:expected={sorted(EXPECTED_CASES)}:"
            f"actual={sorted(outcomes)}"
        )
    return {
        "status": "pass",
        "fixture_sha256": actual_sha256,
        "case_count": len(outcomes),
        "outcomes": outcomes,
        "independent_implementation": True,
        "operational_authority": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    try:
        report = validate_fixture(args.fixture, args.expected_sha256)
    except (FixtureError, OSError, UnicodeError) as exc:
        report = {
            "status": "fail",
            "error": str(exc),
            "independent_implementation": True,
            "operational_authority": False,
        }
        status = 1
    else:
        status = 0

    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    print(rendered, end="")
    if args.report is not None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered, encoding="utf-8")
    return status


if __name__ == "__main__":
    raise SystemExit(main())
