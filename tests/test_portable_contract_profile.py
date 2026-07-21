from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_portable_contract_profile.py"
PROFILE = ROOT / "contracts" / "portable-security-contract-v0.profile.json"
DOCUMENT_CANDIDATES = (
    ROOT / "docs" / "portable-security-contract-v0.md",
    ROOT / "docs" / "PORTABLE_SECURITY_CONTRACT_V0.md",
)
EXPECTED_SHA256 = "2aa1016828fe5797d4bedd1fbaf80a58dbb018d34df23d52d6de23bb8721f619"


def canonical_digest(path: Path) -> str:
    data = json.loads(path.read_text(encoding="utf-8"))
    canonical = json.dumps(
        data,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def contract_document() -> Path:
    for candidate in DOCUMENT_CANDIDATES:
        if candidate.is_file():
            return candidate
    raise AssertionError("portable security contract document is missing")


def run_validator(
    profile: Path, document: Path, expected: str
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--profile",
            str(profile),
            "--document",
            str(document),
            "--expected-sha256",
            expected,
        ],
        check=False,
        capture_output=True,
        text=True,
    )


class PortableContractProfileTests(unittest.TestCase):
    def test_repository_profile_and_document_pass(self) -> None:
        self.assertEqual(canonical_digest(PROFILE), EXPECTED_SHA256)
        result = run_validator(PROFILE, contract_document(), EXPECTED_SHA256)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('"status": "pass"', result.stdout)

    def test_duplicate_profile_key_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            duplicate = Path(directory) / "duplicate.json"
            duplicate.write_text(
                '{"profile_id":"first","profile_id":"second"}\n',
                encoding="utf-8",
            )
            result = run_validator(duplicate, contract_document(), EXPECTED_SHA256)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("duplicate key", result.stdout)

    def test_profile_digest_mismatch_fails_closed(self) -> None:
        result = run_validator(PROFILE, contract_document(), "0" * 64)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("profile-digest-mismatch", result.stdout)

    def test_missing_document_semantics_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            incomplete = Path(directory) / "contract.md"
            incomplete.write_text("# Portable Security Contract v0\n", encoding="utf-8")
            result = run_validator(PROFILE, incomplete, EXPECTED_SHA256)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing-route-text", result.stdout)
        self.assertIn("missing-document-requirement", result.stdout)


if __name__ == "__main__":
    unittest.main()
