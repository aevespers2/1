from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


MANDATORY_GATES = (
    "private_authoritative_store",
    "public_mirror_secret_free",
    "operator_policy_digest_pinned",
    "muse_no_trust_core_route",
    "separate_gateway_identity",
    "secret_redaction_tested",
    "structured_operations_only",
    "vtx_checks_active",
    "append_only_audit_active",
    "path_audit_active",
    "protected_branches_active",
    "revocation_drill_passed",
    "protected_branch_denial_passed",
    "trust_core_denial_passed",
    "grant_manifest_approved",
    "emergency_freeze_tested",
)


@dataclass(frozen=True)
class GateEvidence:
    passed: bool
    evidence_ref: str
    recorded_at: str
    notes: str = ""


@dataclass(frozen=True)
class ReadinessResult:
    ready: bool
    missing: tuple[str, ...]
    failed: tuple[str, ...]


def evaluate_readiness(evidence: Mapping[str, GateEvidence]) -> ReadinessResult:
    """Require explicit evidence for every deployment gate."""
    missing = tuple(gate for gate in MANDATORY_GATES if gate not in evidence)
    failed = tuple(
        gate for gate in MANDATORY_GATES
        if gate in evidence and (
            not evidence[gate].passed
            or not evidence[gate].evidence_ref.strip()
            or not evidence[gate].recorded_at.strip()
        )
    )
    return ReadinessResult(ready=not missing and not failed, missing=missing, failed=failed)
