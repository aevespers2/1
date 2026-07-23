from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path
from unittest import mock

from scripts import validate_qso_interface_independent as validator

ROOT = Path(__file__).resolve().parents[1]
TUPLE_PATH = ROOT / "contracts/qso-interface-source-tuple-v1.json"


def case(case_id: str, interface: str, false_facts: tuple[str, ...] = ()) -> dict:
    facts = {name: name not in false_facts for name in validator.FACT_ORDER}
    disposition, reasons = validator.derive(facts)
    return {
        "case_id": case_id,
        "interface": interface,
        "facts": facts,
        "expected": {"disposition": disposition, "reasons": reasons},
    }


def valid_fixture() -> dict:
    return {
        "contract_id": validator.CONTRACT_ID,
        "version": validator.VERSION,
        "fact_order": list(validator.FACT_ORDER),
        "reason_order": list(validator.REASON_ORDER),
        "cases": [
            case("event-ledger-compatible", "qso-event-ledger"),
            case("runtime-report-compatible", "qso-runtime-report"),
            case("stale-source-tuple", "qso-event-ledger", ("source_tuple_current",)),
            case("unknown-interface", "qso-unknown-interface", ("known_interface",)),
            case("interface-name-mismatch", "qso-event-ledger", ("interface_name_match",)),
            case("producer-role-invalid", "qso-event-ledger", ("producer_role_valid",)),
            case("consumer-role-invalid", "qso-runtime-report", ("consumer_role_valid",)),
            case("protocol-mismatch", "qso-event-ledger", ("protocol_match",)),
            case("schema-version-mismatch", "qso-runtime-report", ("schema_version_match",)),
            case("idempotency-mismatch", "qso-event-ledger", ("idempotency_match",)),
            case("retry-policy-mismatch", "qso-runtime-report", ("retry_policy_match",)),
            case("default-deny-not-preserved", "qso-event-ledger", ("default_deny_preserved",)),
            case("correction-semantics-missing", "qso-event-ledger", ("correction_supported",)),
            case("rollback-semantics-missing", "qso-runtime-report", ("rollback_supported",)),
            case("evidence-not-bound", "qso-runtime-report", ("evidence_bound",)),
            case("authority-promotion-detected", "qso-event-ledger", ("authority_promotion_absent",)),
            case(
                "multi-obstruction-order",
                "qso-runtime-report",
                (
                    "source_tuple_current",
                    "protocol_match",
                    "schema_version_match",
                    "evidence_bound",
                    "authority_promotion_absent",
                ),
            ),
        ],
    }


class InterfaceConsumerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = valid_fixture()
        self.tuple_data = json.loads(TUPLE_PATH.read_text(encoding="utf-8"))

    def assert_code(self, code: str, func, *args) -> None:
        with self.assertRaises(validator.ContractError) as ctx:
            func(*args)
        self.assertEqual(ctx.exception.code, code)

    def test_01_valid_fixture_converges(self) -> None:
        result = validator.validate_fixture(self.fixture)
        self.assertEqual(result["case_count"], 17)
        self.assertEqual(result["positive_count"], 2)
        self.assertEqual(result["blocked_count"], 15)

    def test_02_duplicate_key_rejected(self) -> None:
        raw = b'{"contract_id":"x","contract_id":"y"}'
        self.assert_code("INVALID_JSON", validator.load_bytes, raw, "fixture")

    def test_03_non_finite_rejected(self) -> None:
        self.assert_code("INVALID_JSON", validator.load_bytes, b'{"x":NaN}', "fixture")

    def test_04_invalid_utf8_rejected(self) -> None:
        self.assert_code("INVALID_JSON", validator.load_bytes, b"\xff", "fixture")

    def test_05_unknown_root_field_rejected(self) -> None:
        data = copy.deepcopy(self.fixture)
        data["extra"] = True
        self.assert_code("UNKNOWN_FIELD", validator.validate_fixture, data)

    def test_06_missing_root_field_rejected(self) -> None:
        data = copy.deepcopy(self.fixture)
        data.pop("version")
        self.assert_code("MISSING_FIELD", validator.validate_fixture, data)

    def test_07_fact_order_drift_rejected(self) -> None:
        data = copy.deepcopy(self.fixture)
        data["fact_order"].reverse()
        self.assert_code("FACT_ORDER_DRIFT", validator.validate_fixture, data)

    def test_08_reason_order_drift_rejected(self) -> None:
        data = copy.deepcopy(self.fixture)
        data["reason_order"].reverse()
        self.assert_code("REASON_ORDER_DRIFT", validator.validate_fixture, data)

    def test_09_duplicate_case_rejected(self) -> None:
        data = copy.deepcopy(self.fixture)
        data["cases"][1]["case_id"] = data["cases"][0]["case_id"]
        self.assert_code("DUPLICATE_CASE", validator.validate_fixture, data)

    def test_10_missing_case_rejected(self) -> None:
        data = copy.deepcopy(self.fixture)
        data["cases"].pop()
        self.assert_code("CASE_COVERAGE_DRIFT", validator.validate_fixture, data)

    def test_11_case_order_drift_rejected(self) -> None:
        data = copy.deepcopy(self.fixture)
        data["cases"][0], data["cases"][1] = data["cases"][1], data["cases"][0]
        self.assert_code("CASE_COVERAGE_DRIFT", validator.validate_fixture, data)

    def test_12_boolean_integer_ambiguity_rejected(self) -> None:
        data = copy.deepcopy(self.fixture)
        data["cases"][0]["facts"]["protocol_match"] = 1
        self.assert_code("INVALID_FACT_TYPE", validator.validate_fixture, data)

    def test_13_missing_fact_rejected(self) -> None:
        data = copy.deepcopy(self.fixture)
        data["cases"][0]["facts"].pop("evidence_bound")
        self.assert_code("MISSING_FIELD", validator.validate_fixture, data)

    def test_14_unknown_fact_rejected(self) -> None:
        data = copy.deepcopy(self.fixture)
        data["cases"][0]["facts"]["automatic_approval"] = False
        self.assert_code("UNKNOWN_FIELD", validator.validate_fixture, data)

    def test_15_wrong_disposition_rejected(self) -> None:
        data = copy.deepcopy(self.fixture)
        data["cases"][0]["expected"]["disposition"] = "BLOCKED"
        self.assert_code("EXPECTED_RESULT_DRIFT", validator.validate_fixture, data)

    def test_16_reason_order_in_result_rejected(self) -> None:
        data = copy.deepcopy(self.fixture)
        expected = data["cases"][-1]["expected"]["reasons"]
        expected[0], expected[1] = expected[1], expected[0]
        self.assert_code("EXPECTED_RESULT_DRIFT", validator.validate_fixture, data)

    def test_17_known_interface_declaration_drift_rejected(self) -> None:
        data = copy.deepcopy(self.fixture)
        data["cases"][0]["interface"] = "qso-unknown-interface"
        self.assert_code("INTERFACE_DECLARATION_DRIFT", validator.validate_fixture, data)

    def test_18_producer_head_drift_rejected(self) -> None:
        data = copy.deepcopy(self.tuple_data)
        data["producer"]["head_sha"] = "0" * 40
        self.assert_code("SOURCE_TUPLE_DRIFT", validator.validate_source_tuple, data, b"fixture")

    def test_19_authority_effect_rejected(self) -> None:
        data = copy.deepcopy(self.tuple_data)
        data["authority_effect"] = "activate"
        self.assert_code("AUTHORITY_PROMOTION_DETECTED", validator.validate_source_tuple, data, b"fixture")

    def test_20_source_byte_drift_blocks_before_fixture_parse(self) -> None:
        tuple_raw = json.dumps(self.tuple_data).encode("utf-8")
        with mock.patch.object(validator, "validate_fixture") as semantic:
            result = validator.evaluate(tuple_raw, b"changed producer bytes")
        self.assertEqual(result["reason_codes"], ["SOURCE_BYTES_DRIFT"])
        semantic.assert_not_called()

    def test_21_real_source_tuple_shape_and_paths(self) -> None:
        with mock.patch.object(validator, "_git_blob", return_value="143b80448cb4623682669ab8e6a9599239dd5847"):
            result = validator.validate_source_tuple(self.tuple_data, b"bounded fixture placeholder")
        self.assertEqual(result["producer_head"], "25036a5cfcea79e204a4660ddd1af09c054935b1")


if __name__ == "__main__":
    unittest.main()
