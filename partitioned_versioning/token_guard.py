from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import FrozenSet, Sequence


FORBIDDEN_REPOSITORIES = frozenset({"aevespers2/1"})
FORBIDDEN_PERMISSIONS = frozenset({
    "administration:write",
    "actions:write",
    "environments:write",
    "members:write",
    "organization_administration:write",
    "secrets:write",
    "workflows:write",
})
REQUIRED_CONTROLS = frozenset({
    "vtx_capability_required",
    "branch_prefix_enforced",
    "append_only_audit",
    "revocation_tested",
    "token_not_in_repo",
    "token_not_in_agent_memory",
    "expiry_configured",
    "repository_allowlist",
})
PROPOSAL_BRANCH_ROOT = "muse/proposal/"
BRANCH_PREFIX_PATTERN = re.compile(r"[a-z0-9][a-z0-9._/-]*/\Z")


@dataclass(frozen=True)
class TokenGrantRequest:
    subject: str
    repositories: FrozenSet[str]
    permissions: FrozenSet[str]
    branch_prefixes: tuple[str, ...]
    expires_at: datetime
    controls: FrozenSet[str]
    token_type: str = "fine_grained_pat"
    can_force_push: bool = False
    can_delete: bool = False
    can_administer: bool = False


@dataclass(frozen=True)
class GuardFinding:
    code: str
    message: str


@dataclass(frozen=True)
class GuardResult:
    allowed: bool
    findings: tuple[GuardFinding, ...]


def _safe_branch_prefix(prefix: object) -> bool:
    if not isinstance(prefix, str):
        return False
    if prefix != prefix.strip() or prefix != prefix.lower():
        return False
    if not BRANCH_PREFIX_PATTERN.fullmatch(prefix):
        return False
    if not prefix.startswith(PROPOSAL_BRANCH_ROOT):
        return False
    parts = prefix[:-1].split("/")
    if any(part in {"", ".", ".."} for part in parts):
        return False
    return True


def evaluate_token_grant(
    request: TokenGrantRequest,
    *,
    now: datetime | None = None,
    max_lifetime_hours: int = 24,
    allowed_repositories: Sequence[str] = (),
) -> GuardResult:
    """Deny token assignment unless every required safeguard is present."""
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None or request.expires_at.tzinfo is None:
        raise ValueError("token guard timestamps must be timezone-aware")

    findings: list[GuardFinding] = []
    allowed_repo_set = set(allowed_repositories)

    if request.subject.lower() != "muse":
        findings.append(GuardFinding("unexpected_subject", "Grant subject must be the registered Muse identity."))

    forbidden_targets = request.repositories & FORBIDDEN_REPOSITORIES
    if forbidden_targets:
        findings.append(GuardFinding("trust_core_targeted", "Repository 1 may not be included in Muse token scope."))

    if not request.repositories:
        findings.append(GuardFinding("empty_repository_scope", "At least one explicit repository is required."))

    if allowed_repo_set and not request.repositories.issubset(allowed_repo_set):
        findings.append(GuardFinding("repository_not_allowlisted", "Token targets a repository outside the approved allowlist."))

    forbidden_permissions = request.permissions & FORBIDDEN_PERMISSIONS
    if forbidden_permissions:
        findings.append(GuardFinding("forbidden_permission", f"Forbidden permissions requested: {sorted(forbidden_permissions)}"))

    if request.can_force_push:
        findings.append(GuardFinding("force_push_enabled", "Force-push capability is prohibited."))
    if request.can_delete:
        findings.append(GuardFinding("delete_enabled", "Deletion capability is prohibited."))
    if request.can_administer:
        findings.append(GuardFinding("admin_enabled", "Administrative capability is prohibited."))

    if not request.branch_prefixes:
        findings.append(GuardFinding("missing_branch_prefix", "At least one proposal-only branch prefix is required."))
    elif any(not _safe_branch_prefix(prefix) for prefix in request.branch_prefixes):
        findings.append(
            GuardFinding(
                "unsafe_branch_prefix",
                f"Every token branch prefix must be a normalized child of {PROPOSAL_BRANCH_ROOT!r} and end with '/'.",
            )
        )

    missing_controls = REQUIRED_CONTROLS - request.controls
    if missing_controls:
        findings.append(GuardFinding("missing_controls", f"Required controls missing: {sorted(missing_controls)}"))

    if request.expires_at <= now:
        findings.append(GuardFinding("expired", "Token expiration must be in the future."))
    else:
        lifetime_hours = (request.expires_at - now).total_seconds() / 3600
        if lifetime_hours > max_lifetime_hours:
            findings.append(GuardFinding("lifetime_too_long", f"Token lifetime exceeds {max_lifetime_hours} hours."))

    if request.token_type not in {"fine_grained_pat", "github_app_installation_token"}:
        findings.append(GuardFinding("unsupported_token_type", "Use a fine-grained PAT or short-lived GitHub App installation token."))

    return GuardResult(allowed=not findings, findings=tuple(findings))
