from partitioned_versioning.readiness import GateEvidence, MANDATORY_GATES, evaluate_readiness
from partitioned_versioning.redaction import assert_secret_free, detect_secret_material, redact
from partitioned_versioning.revocation import RevocationRegistry


def evidence(passed: bool = True):
    return GateEvidence(
        passed=passed,
        evidence_ref="audit:sha256:" + ("a" * 64),
        recorded_at="2026-07-16T18:00:00-07:00",
    )


def test_readiness_requires_every_gate():
    controls = {gate: evidence() for gate in MANDATORY_GATES[:-1]}
    result = evaluate_readiness(controls)
    assert not result.ready
    assert result.missing == (MANDATORY_GATES[-1],)


def test_failed_or_empty_evidence_blocks_readiness():
    controls = {gate: evidence() for gate in MANDATORY_GATES}
    controls["revocation_drill_passed"] = GateEvidence(False, "", "")
    result = evaluate_readiness(controls)
    assert not result.ready
    assert "revocation_drill_passed" in result.failed


def test_complete_evidence_passes():
    result = evaluate_readiness({gate: evidence() for gate in MANDATORY_GATES})
    assert result.ready


def test_token_like_material_is_detected_and_redacted():
    secret = "github_pat_" + ("A" * 40)
    text = f"authorization={secret}"
    assert detect_secret_material(text)
    assert secret not in redact(text)


def test_secret_free_values_pass():
    assert_secret_free(["grant-id-001", "muse/proposal/task-001"])


def test_revocation_and_global_freeze_fail_closed():
    registry = RevocationRegistry()
    assert registry.is_allowed("grant-1") == (True, "active")
    registry.revoke("grant-1", reason="drill", authority="operator")
    assert registry.is_allowed("grant-1") == (False, "grant_revoked")
    registry.freeze(reason="emergency")
    assert registry.is_allowed("grant-2") == (False, "global_freeze")
