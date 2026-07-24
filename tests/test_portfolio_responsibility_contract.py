from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from scripts.validate_portfolio_responsibility_fixtures import (
    FixtureError,
    load_fixture,
    validate_fixture,
)

FIXTURE = Path("fixtures/portfolio-responsibility-custody-v1.json")


class ResponsibilityCustodyContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.document, cls.sha256 = load_fixture(FIXTURE)

    def mutated(self) -> dict:
        return copy.deepcopy(self.document)

    def test_shared_fixture_passes(self) -> None:
        self.assertEqual(validate_fixture(self.document), [])

    def test_fixture_hash_is_frozen(self) -> None:
        self.assertEqual(
            self.sha256,
            "299e2542d729bf30fabac1c08d0c2ecd8d21f655d190013419e205fba28ebd8f",
        )

    def test_missing_case_fails(self) -> None:
        document = self.mutated()
        document["cases"].pop()
        self.assertTrue(any("case coverage mismatch" in e for e in validate_fixture(document)))

    def test_duplicate_case_id_fails(self) -> None:
        document = self.mutated()
        document["cases"][1]["case_id"] = document["cases"][0]["case_id"]
        self.assertTrue(any("case_id values must be unique" in e for e in validate_fixture(document)))

    def test_unknown_field_fails(self) -> None:
        document = self.mutated()
        document["cases"][0]["ambient_admin"] = True
        self.assertTrue(any("field mismatch" in e for e in validate_fixture(document)))

    def test_unknown_flag_fails(self) -> None:
        document = self.mutated()
        document["cases"][0]["flags"]["implicit_authority"] = False
        self.assertTrue(any("field mismatch" in e for e in validate_fixture(document)))

    def test_non_boolean_flag_fails(self) -> None:
        document = self.mutated()
        document["cases"][0]["flags"]["term_current"] = 1
        self.assertTrue(any("flags must be boolean" in e for e in validate_fixture(document)))

    def test_reason_mismatch_fails(self) -> None:
        document = self.mutated()
        document["cases"][1]["expected_reason_codes"] = []
        self.assertTrue(any("independently derived" in e for e in validate_fixture(document)))

    def test_prohibited_secret_field_fails(self) -> None:
        document = self.mutated()
        document["secret"] = "synthetic-placeholder"
        errors = validate_fixture(document)
        self.assertTrue(any("field mismatch" in e for e in errors))
        self.assertTrue(any("prohibited fields present" in e for e in errors))

    def test_duplicate_json_key_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate.json"
            path.write_text('{"fixture_id":"a","fixture_id":"b"}', encoding="utf-8")
            with self.assertRaisesRegex(FixtureError, "duplicate JSON key"):
                load_fixture(path)

    def test_non_finite_number_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nan.json"
            path.write_text('{"value":NaN}', encoding="utf-8")
            with self.assertRaisesRegex(FixtureError, "non-finite JSON number"):
                load_fixture(path)

    def test_non_utf8_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "binary.json"
            path.write_bytes(b"\xff\xfe")
            with self.assertRaisesRegex(FixtureError, "valid UTF-8"):
                load_fixture(path)


if __name__ == "__main__":
    unittest.main()
