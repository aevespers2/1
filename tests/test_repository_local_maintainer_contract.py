from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_repository_local_maintainer_fixtures import (
    FixtureError,
    REQUIRED_CASES,
    derive_reasons,
    load_fixture,
    validate_fixture,
)

FIXTURE = Path("fixtures/repository-local-maintainer-v1.json")
EXPECTED_SHA256 = "a920723c66e45acae7be988295f193e64f20d847d52564bfd295644190f65cd4"


class RepositoryLocalMaintainerContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.document, cls.sha256 = load_fixture(FIXTURE)

    def test_shared_fixture_is_byte_identical(self) -> None:
        self.assertEqual(self.sha256, EXPECTED_SHA256)

    def test_fixture_passes_independent_validation(self) -> None:
        self.assertEqual(validate_fixture(self.document), [])

    def test_exact_case_coverage(self) -> None:
        self.assertEqual({case["case_id"] for case in self.document["cases"]}, REQUIRED_CASES)

    def test_only_positive_case_is_review_eligible(self) -> None:
        positive = [
            case
            for case in self.document["cases"]
            if case["expected_disposition"] == "REVIEW_ELIGIBLE"
        ]
        self.assertEqual(
            [case["case_id"] for case in positive],
            ["bounded_documentation_packet"],
        )
        self.assertEqual(positive[0]["expected_reasons"], [])

    def test_reason_derivation_is_independent(self) -> None:
        for case in self.document["cases"]:
            with self.subTest(case=case["case_id"]):
                self.assertEqual(
                    derive_reasons(case["controls"]),
                    set(case["expected_reasons"]),
                )

    def test_unknown_top_level_field_fails_closed(self) -> None:
        changed = copy.deepcopy(self.document)
        changed["permission_grant"] = True
        self.assertTrue(any("field mismatch" in error for error in validate_fixture(changed)))

    def test_unknown_control_fails_closed(self) -> None:
        changed = copy.deepcopy(self.document)
        changed["cases"][0]["controls"]["merge_authority"] = True
        errors = validate_fixture(changed)
        self.assertTrue(any("unknown=['merge_authority']" in error for error in errors))

    def test_non_boolean_control_fails_closed(self) -> None:
        changed = copy.deepcopy(self.document)
        changed["cases"][0]["controls"]["designation"] = 1
        self.assertTrue(
            any("controls must be boolean" in error for error in validate_fixture(changed))
        )

    def test_disposition_drift_fails_closed(self) -> None:
        changed = copy.deepcopy(self.document)
        changed["cases"][0]["expected_disposition"] = "AUTHORIZED"
        self.assertTrue(
            any(
                "does not match independently derived" in error
                for error in validate_fixture(changed)
            )
        )

    def test_reason_drift_fails_closed(self) -> None:
        changed = copy.deepcopy(self.document)
        changed["cases"][1]["expected_reasons"] = []
        self.assertTrue(
            any(
                "do not match independently derived" in error
                for error in validate_fixture(changed)
            )
        )

    def test_prohibited_secret_field_fails_closed(self) -> None:
        changed = copy.deepcopy(self.document)
        changed["secret_key"] = "synthetic-but-prohibited"
        errors = validate_fixture(changed)
        self.assertTrue(any("prohibited fields present" in error for error in errors))

    def test_duplicate_case_identity_fails_closed(self) -> None:
        changed = copy.deepcopy(self.document)
        changed["cases"][1]["case_id"] = changed["cases"][0]["case_id"]
        errors = validate_fixture(changed)
        self.assertTrue(any("case_id values must be unique" in error for error in errors))
        self.assertTrue(any("case coverage mismatch" in error for error in errors))

    def test_duplicate_json_key_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate.json"
            path.write_text('{"fixture_id":"a","fixture_id":"b"}', encoding="utf-8")
            with self.assertRaises(FixtureError):
                load_fixture(path)

    def test_non_finite_number_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nan.json"
            path.write_text('{"value":NaN}', encoding="utf-8")
            with self.assertRaises(FixtureError):
                load_fixture(path)

    def test_invalid_utf8_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.json"
            path.write_bytes(b"\xff\xfe")
            with self.assertRaises(FixtureError):
                load_fixture(path)

    def test_serialized_copy_preserves_semantics_but_not_byte_identity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "reserialized.json"
            path.write_text(json.dumps(self.document, indent=2), encoding="utf-8")
            copied, copied_sha = load_fixture(path)
            self.assertEqual(validate_fixture(copied), [])
            self.assertNotEqual(copied_sha, EXPECTED_SHA256)


if __name__ == "__main__":
    unittest.main()
