import json

from partitioned_versioning.readiness import MANDATORY_GATES
from partitioned_versioning.readiness_cli import load_evidence
from partitioned_versioning.readiness import evaluate_readiness


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
