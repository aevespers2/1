from __future__ import annotations

import copy
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "validate_portfolio_graph_fixtures.py"
SPEC = importlib.util.spec_from_file_location("portfolio_graph_validator", MODULE_PATH)
assert SPEC and SPEC.loader
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)

FIXTURE_PATH = ROOT / "fixtures" / "portfolio-contract-graph-v1.json"


class PortfolioGraphContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.document, self.sha256 = validator.load_fixture(FIXTURE_PATH)

    def test_reference_fixture_passes_independent_validation(self) -> None:
        errors, metrics = validator.validate_fixture(copy.deepcopy(self.document))
        self.assertEqual([], errors)
        self.assertEqual(12, metrics["case_count"])
        self.assertGreaterEqual(metrics["pairwise_cases"], 4)
        self.assertGreaterEqual(metrics["triple_or_larger_cases"], 5)

    def test_duplicate_json_key_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "duplicate.json"
            path.write_text(
                '{"fixture_id":"a","fixture_id":"b","fixture_version":1,'
                '"status":"synthetic-only","authority_effect":"none","cases":[]}',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(validator.FixtureError, "duplicate JSON key"):
                validator.load_fixture(path)

    def test_non_finite_number_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "nan.json"
            path.write_text('{"value":NaN}', encoding="utf-8")
            with self.assertRaisesRegex(validator.FixtureError, "non-finite"):
                validator.load_fixture(path)

    def test_unknown_top_level_field_is_rejected(self) -> None:
        document = copy.deepcopy(self.document)
        document["live_registry"] = True
        errors, _ = validator.validate_fixture(document)
        self.assertTrue(any("unknown=['live_registry']" in error for error in errors))

    def test_unknown_or_non_boolean_flags_are_rejected(self) -> None:
        document = copy.deepcopy(self.document)
        document["cases"][0]["flags"]["mystery"] = True
        document["cases"][1]["flags"]["required_edge_missing"] = "true"
        errors, _ = validator.validate_fixture(document)
        self.assertTrue(any("unknown flags ['mystery']" in error for error in errors))
        self.assertTrue(any("flags must be boolean" in error for error in errors))

    def test_path_divergence_cannot_be_marked_accepted(self) -> None:
        document = copy.deepcopy(self.document)
        case = next(
            item
            for item in document["cases"]
            if item["case_id"] == "direct-composed-path-divergence"
        )
        case["expected_disposition"] = "ACCEPTED"
        case["expected_reason_codes"] = []
        errors, _ = validator.validate_fixture(document)
        self.assertTrue(any("independently derived" in error for error in errors))
        self.assertTrue(
            any("does not match independently derived 'BLOCKED'" in error for error in errors)
        )

    def test_correction_gap_is_partial_only_when_it_is_the_only_obstruction(self) -> None:
        document = copy.deepcopy(self.document)
        case = next(
            item
            for item in document["cases"]
            if item["case_id"] == "correction-propagation-gap"
        )
        case["flags"]["rollback_route_complete"] = False
        case["expected_reason_codes"].append("ROLLBACK_DEAD_END")
        errors, _ = validator.validate_fixture(document)
        self.assertTrue(
            any("does not match independently derived 'BLOCKED'" in error for error in errors)
        )

    def test_missing_required_case_is_rejected(self) -> None:
        document = copy.deepcopy(self.document)
        document["cases"] = document["cases"][:-1]
        errors, _ = validator.validate_fixture(document)
        self.assertTrue(any("case coverage mismatch" in error for error in errors))

    def test_duplicate_nodes_edges_and_reason_codes_are_rejected(self) -> None:
        document = copy.deepcopy(self.document)
        case = document["cases"][0]
        case["nodes"].append(case["nodes"][0])
        case["edges"].append(case["edges"][0])
        blocked = document["cases"][1]
        blocked["expected_reason_codes"].append(blocked["expected_reason_codes"][0])
        errors, _ = validator.validate_fixture(document)
        self.assertTrue(any("nodes must not contain duplicates" in error for error in errors))
        self.assertTrue(any("edges must not contain duplicates" in error for error in errors))
        self.assertTrue(any("expected_reason_codes must be unique" in error for error in errors))

    def test_prohibited_secret_bearing_field_is_rejected_recursively(self) -> None:
        document = copy.deepcopy(self.document)
        document["cases"][0]["flags"]["secret"] = False
        errors, _ = validator.validate_fixture(document)
        self.assertTrue(any("prohibited fields present" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
