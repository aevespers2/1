from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_iris_journal_fixtures.py"
FIXTURE = ROOT / "fixtures" / "iris-verifier" / "crash-recovery-journal-vectors.json"
EXPECTED_SHA256 = "f255438eab406bba71ab23fad60d34b2a7d3a580e90583e1517d432d8e03b89a"

spec = importlib.util.spec_from_file_location("journal_validator", SCRIPT)
assert spec and spec.loader
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


def test_shared_journal_fixture_passes_independent_validation() -> None:
    report = validator.validate_fixture(FIXTURE, EXPECTED_SHA256)
    assert report["status"] == "pass"
    assert report["case_count"] == 10
    assert report["independent_implementation"] is True
    assert report["journal_recovery"] is True
    assert report["operational_authority"] is False


def test_duplicate_key_and_non_finite_json_fail_closed() -> None:
    with pytest.raises(validator.FixtureError, match="duplicate-key"):
        validator.strict_loads('{"schema":"x","schema":"y"}')
    with pytest.raises(validator.FixtureError, match="non-finite-number"):
        validator.strict_loads('{"value":NaN}')


def test_recovery_is_idempotent_and_does_not_mutate_input() -> None:
    manifest = validator.strict_loads(FIXTURE.read_text(encoding="utf-8"))
    case = next(
        item for item in manifest["cases"]
        if item["case_id"] == "committed-without-ack-recovers"
    )
    original = copy.deepcopy(case["authority_state"])
    first = validator.reconcile(case["authority_state"], case["journal_records"])
    assert case["authority_state"] == original
    second = validator.reconcile(first["state"], case["journal_records"])
    assert second["outcome"] == "already-recovered"
    assert second["state"] == first["state"]


def test_phase_order_and_record_limit_fail_closed() -> None:
    manifest = validator.strict_loads(FIXTURE.read_text(encoding="utf-8"))
    case = next(
        item for item in manifest["cases"]
        if item["case_id"] == "acknowledged-journal-recovers-stale-state"
    )
    with pytest.raises(validator.FixtureError, match="journal-phase-order-invalid"):
        validator.reconcile(case["authority_state"], case["journal_records"][1:])
    with pytest.raises(validator.FixtureError, match="journal-record-limit-exceeded"):
        validator.reconcile(case["authority_state"], case["journal_records"] * 6)
