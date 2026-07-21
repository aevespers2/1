#!/usr/bin/env python3
"""Validate the duplicated Portable Security Contract semantic profile.

The profile is deliberately repository-neutral while ownership is unresolved.
CI supplies one expected canonical SHA-256 in both repositories, preventing the
two documentation candidates from drifting while each local check remains
offline and read-only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

EXPECTED_KEYS = {
    "profile_id",
    "profile_version",
    "status",
    "route",
    "roles",
    "message_types",
    "required_identifiers",
    "result_states",
    "fixture_descriptions",
    "document_requirements",
}
EXPECTED_PROFILE_ID = "portable-security-contract-v0.semantic-profile"
EXPECTED_STATUS = "proposed-documentation-only"
EXPECTED_ROLE_KEYS = {"repository_0", "repository_1"}


class ProfileError(ValueError):
    """Raised when the semantic profile is malformed."""


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ProfileError(f"duplicate key: {key}")
        result[key] = value
    return result


def _reject_non_finite(value: str) -> None:
    raise ProfileError(f"non-finite number: {value}")


def load_profile(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_bytes()
        text = raw.decode("utf-8", errors="strict")
        profile = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_pairs,
            parse_constant=_reject_non_finite,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ProfileError) as exc:
        raise ProfileError(f"cannot load strict profile: {exc}") from exc
    if not isinstance(profile, dict):
        raise ProfileError("profile root must be an object")
    return profile


def canonical_bytes(profile: dict[str, Any]) -> bytes:
    return json.dumps(
        profile,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _validate_unique_string_list(
    findings: list[dict[str, str]], profile: dict[str, Any], key: str
) -> list[str]:
    value = profile.get(key)
    if not isinstance(value, list) or not value:
        findings.append({"kind": "invalid-profile-list", "field": key})
        return []
    strings = [item for item in value if isinstance(item, str) and item]
    if len(strings) != len(value):
        findings.append({"kind": "non-string-profile-item", "field": key})
    if len(set(strings)) != len(strings):
        findings.append({"kind": "duplicate-profile-item", "field": key})
    return strings


def validate(
    profile_path: Path,
    document_path: Path,
    expected_sha256: str,
) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    try:
        profile = load_profile(profile_path)
    except ProfileError as exc:
        return {
            "schema_version": 1,
            "status": "fail",
            "profile_path": str(profile_path),
            "document_path": str(document_path),
            "expected_sha256": expected_sha256,
            "actual_sha256": None,
            "findings": [{"kind": "invalid-profile", "detail": str(exc)}],
        }

    keys = set(profile)
    for missing in sorted(EXPECTED_KEYS - keys):
        findings.append({"kind": "missing-profile-key", "field": missing})
    for unexpected in sorted(keys - EXPECTED_KEYS):
        findings.append({"kind": "unexpected-profile-key", "field": unexpected})

    if profile.get("profile_id") != EXPECTED_PROFILE_ID:
        findings.append({"kind": "invalid-profile-id", "field": "profile_id"})
    if profile.get("status") != EXPECTED_STATUS:
        findings.append({"kind": "invalid-profile-status", "field": "status"})

    version = profile.get("profile_version")
    if not isinstance(version, str) or not version.startswith("0."):
        findings.append({"kind": "invalid-profile-version", "field": "profile_version"})

    route = _validate_unique_string_list(findings, profile, "route")
    message_types = _validate_unique_string_list(findings, profile, "message_types")
    identifiers = _validate_unique_string_list(findings, profile, "required_identifiers")
    result_states = _validate_unique_string_list(findings, profile, "result_states")
    fixtures = _validate_unique_string_list(findings, profile, "fixture_descriptions")
    document_requirements = _validate_unique_string_list(
        findings, profile, "document_requirements"
    )

    roles = profile.get("roles")
    if not isinstance(roles, dict) or set(roles) != EXPECTED_ROLE_KEYS:
        findings.append({"kind": "invalid-role-map", "field": "roles"})
    else:
        for role_key in sorted(EXPECTED_ROLE_KEYS):
            role_values = roles.get(role_key)
            if (
                not isinstance(role_values, list)
                or not role_values
                or not all(isinstance(item, str) and item for item in role_values)
                or len(set(role_values)) != len(role_values)
            ):
                findings.append({"kind": "invalid-role-list", "field": role_key})

    canonical = canonical_bytes(profile)
    actual_sha256 = hashlib.sha256(canonical).hexdigest()
    if len(expected_sha256) != 64 or any(
        char not in "0123456789abcdef" for char in expected_sha256
    ):
        findings.append({"kind": "invalid-expected-sha256", "field": "expected_sha256"})
    elif actual_sha256 != expected_sha256:
        findings.append(
            {
                "kind": "profile-digest-mismatch",
                "expected": expected_sha256,
                "actual": actual_sha256,
            }
        )

    try:
        document = document_path.read_text(encoding="utf-8", errors="strict")
    except (OSError, UnicodeError) as exc:
        findings.append({"kind": "unreadable-document", "detail": str(exc)})
        document = ""

    for item in route:
        if item not in document:
            findings.append({"kind": "missing-route-text", "value": item})
    for item in message_types:
        if f"`{item}`" not in document:
            findings.append({"kind": "missing-message-type", "value": item})
    for item in identifiers:
        if f"`{item}`" not in document:
            findings.append({"kind": "missing-identifier", "value": item})
    for item in result_states:
        if f"`{item}`" not in document:
            findings.append({"kind": "missing-result-state", "value": item})
    for item in fixtures:
        if item not in document:
            findings.append({"kind": "missing-fixture-description", "value": item})
    for item in document_requirements:
        if item not in document:
            findings.append({"kind": "missing-document-requirement", "value": item})

    return {
        "schema_version": 1,
        "status": "pass" if not findings else "fail",
        "profile_path": str(profile_path),
        "document_path": str(document_path),
        "profile_id": profile.get("profile_id"),
        "profile_version": profile.get("profile_version"),
        "expected_sha256": expected_sha256,
        "actual_sha256": actual_sha256,
        "fixture_count": len(fixtures),
        "required_identifier_count": len(identifiers),
        "findings": findings,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--document", required=True, type=Path)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--report", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = validate(args.profile, args.document, args.expected_sha256.lower())
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
