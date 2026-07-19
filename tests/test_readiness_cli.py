import json

import pytest

from partitioned_versioning.readiness import MANDATORY_GATES, evaluate_readiness
from partitioned_versioning.readiness_cli import DuplicateKeyError, load_evidence


def test_example_shape_remains_blocked(tmp_path):
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps({
        gate: {"passed": False, "evidence_ref": "", "recorded_at": ""}
        for gate in MANDATORY_GATES
    }), encoding="utf-8")
    report = evaluate_readiness(load_evidence(str(path)))
    assert not report.ready
    assert set(report.failed) == set(MANDATORY_GATES)


def test_complete_positive_evidence_passes(tmp_path):
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps({
        gate: {
            "passed": True,
            "evidence_ref": f"receipt:{gate}",
            "recorded_at": "2026-07-16T18:00:00-07:00",
        }
        for gate in MANDATORY_GATES
    }), encoding="utf-8")
    report = evaluate_readiness(load_evidence(str(path)))
    assert report.ready
    assert report.missing == ()
    assert report.failed == ()


@pytest.mark.parametrize("bad_value", ["false", "true", 0, 1, None, [], {}])
def test_passed_requires_a_json_boolean(tmp_path, bad_value):
    gate = MANDATORY_GATES[0]
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps({
        gate: {
            "passed": bad_value,
            "evidence_ref": "receipt:test",
            "recorded_at": "2026-07-16T18:00:00-07:00",
        }
    }), encoding="utf-8")
    with pytest.raises(ValueError, match="must be a boolean"):
        load_evidence(str(path))


def test_unknown_gate_fails_closed(tmp_path):
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps({
        "unapproved_gate": {
            "passed": True,
            "evidence_ref": "receipt:test",
            "recorded_at": "2026-07-16T18:00:00-07:00",
        }
    }), encoding="utf-8")
    with pytest.raises(ValueError, match="unknown readiness gates"):
        load_evidence(str(path))


def test_duplicate_gate_key_fails_closed(tmp_path):
    gate = MANDATORY_GATES[0]
    path = tmp_path / "evidence.json"
    path.write_text(
        '{"' + gate + '":{},"' + gate + '":{}}',
        encoding="utf-8",
    )
    with pytest.raises(DuplicateKeyError, match="duplicate readiness evidence key"):
        load_evidence(str(path))


def test_non_string_evidence_reference_fails_closed(tmp_path):
    gate = MANDATORY_GATES[0]
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps({
        gate: {
            "passed": True,
            "evidence_ref": 123,
            "recorded_at": "2026-07-16T18:00:00-07:00",
        }
    }), encoding="utf-8")
    with pytest.raises(ValueError, match="evidence_ref.*must be a string"):
        load_evidence(str(path))
