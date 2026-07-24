from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_qso_ecosystem_independent.py"
SPEC = importlib.util.spec_from_file_location("consumer", PATH)
assert SPEC and SPEC.loader
consumer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(consumer)


def valid_manifest():
    return {
        "schema_version": "1.0.0",
        "component": "QSO-FABRIC",
        "version": "0.1.0",
        "purpose": "Provide deterministic bounded coordination with retained evidence.",
        "conformance": {"claimed_level": 1, "evidence_path": "artifacts/conformance"},
        "runtime_bounds": {
            "max_seconds": 300,
            "max_rounds": 16,
            "max_messages": 256,
            "max_memory_mb": 2048,
            "network_default": "deny",
        },
        "capabilities": [
            {
                "name": "bounded-message-exchange",
                "authority": "execute",
                "default": "allow",
                "constraints": ["round limit", "deterministic seed"],
            }
        ],
        "interfaces": [
            {
                "name": "qso-event-ledger",
                "role": "producer",
                "protocol": "append-only-json",
                "schema_version": "1.0.0",
                "idempotent": True,
                "retry_limit": 0,
            }
        ],
        "governance": {
            "review_component": "Jacob Redmond",
            "deprecated_aliases": ["Aequitas"],
            "human_override": True,
            "audit_log": True,
        },
    }


def valid_schema():
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "x",
        "title": "x",
        "type": "object",
        "additionalProperties": False,
        "required": list(consumer.TOP),
        "properties": {
            "schema_version": {},
            "component": {},
            "version": {},
            "purpose": {},
            "conformance": {
                "type": "object",
                "additionalProperties": False,
                "required": sorted(consumer.FIELDS["conformance"]),
                "properties": {key: {} for key in consumer.FIELDS["conformance"]},
            },
            "runtime_bounds": {
                "type": "object",
                "additionalProperties": False,
                "required": sorted(consumer.FIELDS["runtime_bounds"]),
                "properties": {key: {} for key in consumer.FIELDS["runtime_bounds"]},
            },
            "capabilities": {
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": sorted(consumer.FIELDS["capability"]),
                    "properties": {key: {} for key in consumer.FIELDS["capability"]},
                }
            },
            "interfaces": {
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": sorted(consumer.FIELDS["interface"]),
                    "properties": {key: {} for key in consumer.FIELDS["interface"]},
                }
            },
            "governance": {
                "type": "object",
                "additionalProperties": False,
                "required": sorted(consumer.FIELDS["governance"]),
                "properties": {key: {} for key in consumer.FIELDS["governance"]},
            },
        },
    }


class IndependentEcosystemTests(unittest.TestCase):
    def assert_blocked(self, data, code, **kwargs):
        result = consumer.evaluate(data, valid_schema(), **kwargs)
        self.assertEqual(result["disposition"], "BLOCKED")
        self.assertEqual(result["reason_codes"], [code])

    def test_valid(self):
        self.assertEqual(
            consumer.evaluate(valid_manifest(), valid_schema())["disposition"],
            "CONFORMS",
        )

    def test_duplicate_json(self):
        with self.assertRaisesRegex(consumer.ContractError, "duplicate key"):
            consumer.load_bytes(b'{"a":1,"a":2}', "x")

    def test_nonfinite(self):
        with self.assertRaisesRegex(consumer.ContractError, "non-finite"):
            consumer.load_bytes(b'{"a":NaN}', "x")

    def test_invalid_utf8(self):
        with self.assertRaisesRegex(consumer.ContractError, "strict UTF-8"):
            consumer.load_bytes(b'{"a":"\xff"}', "x")

    def test_unknown_top(self):
        data = valid_manifest()
        data["x"] = 1
        self.assert_blocked(data, "UNKNOWN_FIELD")

    def test_unknown_nested(self):
        data = valid_manifest()
        data["runtime_bounds"]["x"] = 1
        self.assert_blocked(data, "UNKNOWN_FIELD")

    def test_boolean_level(self):
        data = valid_manifest()
        data["conformance"]["claimed_level"] = True
        self.assert_blocked(data, "INVALID_CONFORMANCE")

    def test_boolean_bound(self):
        data = valid_manifest()
        data["runtime_bounds"]["max_seconds"] = True
        self.assert_blocked(data, "INVALID_RUNTIME_BOUND")

    def test_unsafe_path(self):
        data = valid_manifest()
        data["conformance"]["evidence_path"] = "../x"
        self.assert_blocked(data, "UNSAFE_EVIDENCE_PATH")

    def test_duplicate_capability(self):
        data = valid_manifest()
        data["capabilities"].append(copy.deepcopy(data["capabilities"][0]))
        self.assert_blocked(data, "INVALID_CAPABILITY")

    def test_nonobject_capability(self):
        data = valid_manifest()
        data["capabilities"] = ["x"]
        self.assert_blocked(data, "UNKNOWN_FIELD")

    def test_unbounded_execution(self):
        data = valid_manifest()
        data["capabilities"][0]["constraints"] = ["human review"]
        self.assert_blocked(data, "UNBOUNDED_EXECUTION")

    def test_empty_interfaces(self):
        data = valid_manifest()
        data["interfaces"] = []
        self.assert_blocked(data, "INVALID_INTERFACE")

    def test_duplicate_interface(self):
        data = valid_manifest()
        data["interfaces"].append(copy.deepcopy(data["interfaces"][0]))
        self.assert_blocked(data, "INVALID_INTERFACE")

    def test_boolean_retry(self):
        data = valid_manifest()
        data["interfaces"][0]["retry_limit"] = False
        self.assert_blocked(data, "INVALID_INTERFACE")

    def test_nonboolean_idempotent(self):
        data = valid_manifest()
        data["interfaces"][0]["idempotent"] = 1
        self.assert_blocked(data, "INVALID_INTERFACE")

    def test_weakened_governance(self):
        data = valid_manifest()
        data["governance"]["human_override"] = False
        self.assert_blocked(data, "WEAK_GOVERNANCE")

    def test_schema_drift(self):
        schema = valid_schema()
        schema["required"].remove("interfaces")
        self.assertEqual(
            consumer.evaluate(valid_manifest(), schema)["reason_codes"],
            ["SCHEMA_DRIFT"],
        )

    def test_missing_readme(self):
        self.assert_blocked(
            valid_manifest(),
            "MISSING_LEVEL_ARTIFACT",
            l1_readme=False,
            l1_workflow=True,
        )

    def test_missing_workflow(self):
        self.assert_blocked(
            valid_manifest(),
            "MISSING_LEVEL_ARTIFACT",
            l1_readme=True,
            l1_workflow=False,
        )

    def test_reason_order_is_stable(self):
        self.assertEqual(consumer.ORDER[0], "INVALID_JSON")
        self.assertEqual(len(consumer.ORDER), len(set(consumer.ORDER)))


if __name__ == "__main__":
    unittest.main()
