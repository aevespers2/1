#!/usr/bin/env python3
"""Independent, fail-closed consumer for QSO-ECOSYSTEM-001 manifest semantics."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

MAX_BYTES = 1_048_576
SEMVER = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:[-+][A-Za-z0-9.-]+)?$")
IDENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{1,127}$")
SAFE_PATH = re.compile(r"^(?!/)(?!.*(?:^|/)\.\.(?:/|$))[A-Za-z0-9._/-]+$")

TOP = (
    "schema_version",
    "component",
    "version",
    "purpose",
    "conformance",
    "runtime_bounds",
    "capabilities",
    "interfaces",
    "governance",
)
FIELDS = {
    "conformance": {"claimed_level", "evidence_path"},
    "runtime_bounds": {
        "max_seconds",
        "max_rounds",
        "max_messages",
        "max_memory_mb",
        "network_default",
    },
    "capability": {"name", "authority", "default", "constraints"},
    "interface": {
        "name",
        "role",
        "protocol",
        "schema_version",
        "idempotent",
        "retry_limit",
    },
    "governance": {
        "review_component",
        "deprecated_aliases",
        "human_override",
        "audit_log",
    },
}
ORDER = (
    "INVALID_JSON",
    "SCHEMA_DRIFT",
    "UNKNOWN_FIELD",
    "MISSING_FIELD",
    "INVALID_IDENTITY",
    "INVALID_CONFORMANCE",
    "UNSAFE_EVIDENCE_PATH",
    "INVALID_RUNTIME_BOUND",
    "INVALID_CAPABILITY",
    "UNBOUNDED_EXECUTION",
    "INVALID_INTERFACE",
    "WEAK_GOVERNANCE",
    "MISSING_LEVEL_ARTIFACT",
)


class ContractError(ValueError):
    def __init__(self, code: str, detail: str):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


def _reject_constant(value: str) -> None:
    raise ContractError("INVALID_JSON", f"non-finite number {value}")


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise ContractError("INVALID_JSON", f"duplicate key {key}")
        out[key] = value
    return out


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


def load_path(path: Path) -> Any:
    return load_bytes(path.read_bytes(), str(path))


def _closed(value: Any, expected: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError("UNKNOWN_FIELD", f"{label} must be object")
    actual = set(value)
    unknown = actual - expected
    missing = expected - actual
    if unknown:
        raise ContractError("UNKNOWN_FIELD", f"{label}: {sorted(unknown)}")
    if missing:
        raise ContractError("MISSING_FIELD", f"{label}: {sorted(missing)}")
    return value


def _int(value: Any) -> bool:
    return type(value) is int


def validate_schema(schema: Any) -> None:
    if not isinstance(schema, dict):
        raise ContractError("SCHEMA_DRIFT", "schema root is not object")
    required = {
        "$schema",
        "$id",
        "title",
        "type",
        "additionalProperties",
        "required",
        "properties",
    }
    if set(schema) != required:
        raise ContractError("SCHEMA_DRIFT", "schema root fields differ")
    if schema.get("type") != "object" or schema.get("additionalProperties") is not False:
        raise ContractError("SCHEMA_DRIFT", "schema root is not closed object")
    if not isinstance(schema.get("required"), list) or set(schema["required"]) != set(TOP):
        raise ContractError("SCHEMA_DRIFT", "required fields differ")
    props = schema.get("properties")
    if not isinstance(props, dict) or set(props) != set(TOP):
        raise ContractError("SCHEMA_DRIFT", "property fields differ")
    nested = {
        "conformance": FIELDS["conformance"],
        "runtime_bounds": FIELDS["runtime_bounds"],
        "capabilities": FIELDS["capability"],
        "interfaces": FIELDS["interface"],
        "governance": FIELDS["governance"],
    }
    for name, expected in nested.items():
        node = props[name]
        if name in {"capabilities", "interfaces"}:
            node = node.get("items", {})
        if node.get("type") != "object" or node.get("additionalProperties") is not False:
            raise ContractError("SCHEMA_DRIFT", f"{name} is not closed")
        if set(node.get("required", [])) != expected or set(node.get("properties", {})) != expected:
            raise ContractError("SCHEMA_DRIFT", f"{name} fields differ")


def validate_manifest(
    data: Any,
    *,
    l1_readme: bool = True,
    l1_workflow: bool = True,
) -> dict[str, Any]:
    root = _closed(data, set(TOP), "manifest")
    if root["schema_version"] != "1.0.0":
        raise ContractError("INVALID_IDENTITY", "schema_version")
    if not isinstance(root["component"], str) or not IDENT.fullmatch(root["component"]):
        raise ContractError("INVALID_IDENTITY", "component")
    if not isinstance(root["version"], str) or not SEMVER.fullmatch(root["version"]):
        raise ContractError("INVALID_IDENTITY", "version")
    if not isinstance(root["purpose"], str) or len(root["purpose"]) < 20:
        raise ContractError("INVALID_IDENTITY", "purpose")

    conformance = _closed(root["conformance"], FIELDS["conformance"], "conformance")
    level = conformance["claimed_level"]
    if not _int(level) or not 0 <= level <= 5:
        raise ContractError("INVALID_CONFORMANCE", "claimed_level")
    if not isinstance(conformance["evidence_path"], str) or not SAFE_PATH.fullmatch(
        conformance["evidence_path"]
    ):
        raise ContractError("UNSAFE_EVIDENCE_PATH", "evidence_path")

    bounds = _closed(root["runtime_bounds"], FIELDS["runtime_bounds"], "runtime_bounds")
    for key in ("max_seconds", "max_rounds", "max_messages", "max_memory_mb"):
        if not _int(bounds[key]) or bounds[key] < 1:
            raise ContractError("INVALID_RUNTIME_BOUND", key)
    if bounds["network_default"] not in {"deny", "allow-declared"}:
        raise ContractError("INVALID_RUNTIME_BOUND", "network_default")

    capabilities = root["capabilities"]
    if not isinstance(capabilities, list) or not capabilities:
        raise ContractError("INVALID_CAPABILITY", "empty")
    capability_names: set[str] = set()
    for index, raw in enumerate(capabilities):
        capability = _closed(raw, FIELDS["capability"], f"capabilities[{index}]")
        name = capability["name"]
        if not isinstance(name, str) or not IDENT.fullmatch(name) or name in capability_names:
            raise ContractError("INVALID_CAPABILITY", f"name:{name}")
        capability_names.add(name)
        if capability["authority"] not in {"observe", "propose", "execute"}:
            raise ContractError("INVALID_CAPABILITY", name)
        if capability["default"] not in {"deny", "allow"}:
            raise ContractError("INVALID_CAPABILITY", name)
        constraints = capability["constraints"]
        if (
            not isinstance(constraints, list)
            or not constraints
            or any(not isinstance(item, str) or not item.strip() for item in constraints)
            or len(set(constraints)) != len(constraints)
        ):
            raise ContractError("INVALID_CAPABILITY", f"constraints:{name}")
        if capability["authority"] == "execute" and capability["default"] == "allow":
            normalized = " ".join(constraints).lower()
            if not any(token in normalized for token in ("bound", "limit", "deterministic")):
                raise ContractError("UNBOUNDED_EXECUTION", name)

    interfaces = root["interfaces"]
    if not isinstance(interfaces, list) or not interfaces:
        raise ContractError("INVALID_INTERFACE", "empty")
    interface_names: set[str] = set()
    for index, raw in enumerate(interfaces):
        interface = _closed(raw, FIELDS["interface"], f"interfaces[{index}]")
        name = interface["name"]
        if not isinstance(name, str) or not IDENT.fullmatch(name) or name in interface_names:
            raise ContractError("INVALID_INTERFACE", f"name:{name}")
        interface_names.add(name)
        if interface["role"] not in {"producer", "consumer", "bidirectional"}:
            raise ContractError("INVALID_INTERFACE", f"role:{name}")
        if not isinstance(interface["protocol"], str) or not interface["protocol"].strip():
            raise ContractError("INVALID_INTERFACE", f"protocol:{name}")
        if not isinstance(interface["schema_version"], str) or not SEMVER.fullmatch(
            interface["schema_version"]
        ):
            raise ContractError("INVALID_INTERFACE", f"schema:{name}")
        if type(interface["idempotent"]) is not bool:
            raise ContractError("INVALID_INTERFACE", f"idempotent:{name}")
        if not _int(interface["retry_limit"]) or interface["retry_limit"] < 0:
            raise ContractError("INVALID_INTERFACE", f"retry_limit:{name}")

    governance = _closed(root["governance"], FIELDS["governance"], "governance")
    aliases = governance["deprecated_aliases"]
    if (
        governance["review_component"] != "Jacob Redmond"
        or governance["human_override"] is not True
        or governance["audit_log"] is not True
    ):
        raise ContractError("WEAK_GOVERNANCE", "required governance control")
    if (
        not isinstance(aliases, list)
        or any(not isinstance(alias, str) or not alias.strip() for alias in aliases)
        or len(set(aliases)) != len(aliases)
        or "Jacob Redmond" in aliases
    ):
        raise ContractError("WEAK_GOVERNANCE", "deprecated_aliases")

    if level >= 1 and (not l1_readme or not l1_workflow):
        raise ContractError("MISSING_LEVEL_ARTIFACT", "L1 README/workflow")
    return {
        "disposition": "CONFORMS",
        "reason_codes": [],
        "component": root["component"],
        "claimed_level": level,
    }


def evaluate(
    data: Any,
    schema: Any,
    *,
    l1_readme: bool = True,
    l1_workflow: bool = True,
) -> dict[str, Any]:
    try:
        validate_schema(schema)
        return validate_manifest(data, l1_readme=l1_readme, l1_workflow=l1_workflow)
    except ContractError as exc:
        return {
            "disposition": "BLOCKED",
            "reason_codes": [exc.code],
            "detail": exc.detail,
        }


def verify_source_tuple(tuple_data: Any, manifest_raw: bytes, schema_raw: bytes) -> None:
    producer = tuple_data["producer"]
    files = producer["files"]
    for key, raw in (("manifest", manifest_raw), ("schema", schema_raw)):
        record = files[key]
        if len(raw) != record["size_bytes"]:
            raise ContractError("INVALID_IDENTITY", f"{key} size")
        if hashlib.sha256(raw).hexdigest() != record["sha256"]:
            raise ContractError("INVALID_IDENTITY", f"{key} sha256")
        git_blob = hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()
        if git_blob != record["git_blob_sha"]:
            raise ContractError("INVALID_IDENTITY", f"{key} git blob")
    if tuple_data["claims"]["capability_or_execution_authority"] is not False:
        raise ContractError("WEAK_GOVERNANCE", "authority promotion")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tuple", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--schema", required=True, type=Path)
    parser.add_argument("--readme", type=Path)
    parser.add_argument("--workflow", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    try:
        tuple_data = load_path(args.tuple)
        manifest_raw = args.manifest.read_bytes()
        schema_raw = args.schema.read_bytes()
        verify_source_tuple(tuple_data, manifest_raw, schema_raw)
        result = evaluate(
            load_bytes(manifest_raw, str(args.manifest)),
            load_bytes(schema_raw, str(args.schema)),
            l1_readme=bool(args.readme and args.readme.is_file() and args.readme.stat().st_size),
            l1_workflow=bool(
                args.workflow and args.workflow.is_file() and args.workflow.stat().st_size
            ),
        )
    except (OSError, KeyError, TypeError, ContractError) as exc:
        result = {
            "disposition": "BLOCKED",
            "reason_codes": [getattr(exc, "code", "INVALID_IDENTITY")],
            "detail": str(exc),
        }

    output = json.dumps(result, indent=2, sort_keys=True) + "\n"
    print(output, end="")
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(output, encoding="utf-8")
    return 0 if result["disposition"] == "CONFORMS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
