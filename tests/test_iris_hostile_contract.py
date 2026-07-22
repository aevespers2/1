from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_iris_hostile_fixtures.py"
FIXTURE = ROOT / "fixtures" / "iris-verifier" / "hostile-context-vectors.json"
EXPECTED_SHA256 = "677a66f65bde813e122c6493b5421a06dadf867cfa029a05f3bc610564f50006"


def run_validator(
    fixture: Path,
    expected_sha256: str,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--fixture",
            str(fixture),
            "--expected-sha256",
            expected_sha256,
        ],
        check=False,
        capture_output=True,
        text=True,
    )


class IrisHostileFixtureContractTests(unittest.TestCase):
    def test_shared_fixture_passes_independent_validation(self) -> None:
        self.assertEqual(
            hashlib.sha256(FIXTURE.read_bytes()).hexdigest(),
            EXPECTED_SHA256,
        )
        result = run_validator(FIXTURE, EXPECTED_SHA256)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["case_count"], 10)
        self.assertTrue(report["independent_implementation"])
        self.assertFalse(report["operational_authority"])

    def test_fixture_digest_mismatch_fails_closed(self) -> None:
        result = run_validator(FIXTURE, "0" * 64)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("fixture-digest-mismatch", result.stdout)

    def test_duplicate_keys_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            duplicate = Path(directory) / "duplicate.json"
            duplicate.write_text(
                '{"schema":"first","schema":"second"}\n',
                encoding="utf-8",
            )
            digest = hashlib.sha256(duplicate.read_bytes()).hexdigest()
            result = run_validator(duplicate, digest)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("duplicate-key", result.stdout)

    def test_changed_expected_outcome_fails_semantic_validation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            changed = Path(directory) / "changed.json"
            manifest = json.loads(FIXTURE.read_text(encoding="utf-8"))
            manifest["cases"][1]["error"] = "device-mismatch"
            changed.write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            digest = hashlib.sha256(changed.read_bytes()).hexdigest()
            result = run_validator(changed, digest)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("case-outcome-mismatch:wrong-eye", result.stdout)


if __name__ == "__main__":
    unittest.main()
