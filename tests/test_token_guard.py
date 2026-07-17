from datetime import datetime, timedelta, timezone

from partitioned_versioning.token_guard import (
    REQUIRED_CONTROLS,
    TokenGrantRequest,
    evaluate_token_grant,
)


NOW = datetime(2026, 7, 16, 17, 0, tzinfo=timezone.utc)


def safe_request(**overrides):
    values = dict(
        subject="Muse",
        repositories=frozenset({"aevespers2/0"}),
        permissions=frozenset({"contents:read", "contents:write", "pull_requests:write", "metadata:read"}),
        branch_prefixes=("muse/proposal/",),
        expires_at=NOW + timedelta(hours=8),
        controls=REQUIRED_CONTROLS,
        token_type="fine_grained_pat",
    )
    values.update(overrides)
    return TokenGrantRequest(**values)


def test_safe_proposal_only_grant_passes():
    result = evaluate_token_grant(
        safe_request(),
        now=NOW,
        allowed_repositories=("aevespers2/0",),
    )
    assert result.allowed
    assert result.findings == ()


def test_repository_one_is_never_assignable():
    result = evaluate_token_grant(
        safe_request(repositories=frozenset({"aevespers2/0", "aevespers2/1"})),
        now=NOW,
        allowed_repositories=("aevespers2/0",),
    )
    assert not result.allowed
    assert "trust_core_targeted" in {finding.code for finding in result.findings}


def test_admin_or_long_lived_grant_fails_closed():
    result = evaluate_token_grant(
        safe_request(
            permissions=frozenset({"administration:write"}),
            expires_at=NOW + timedelta(days=30),
            can_administer=True,
        ),
        now=NOW,
        allowed_repositories=("aevespers2/0",),
    )
    codes = {finding.code for finding in result.findings}
    assert not result.allowed
    assert {"forbidden_permission", "admin_enabled", "lifetime_too_long"}.issubset(codes)


def test_missing_revocation_test_blocks_assignment():
    result = evaluate_token_grant(
        safe_request(controls=REQUIRED_CONTROLS - {"revocation_tested"}),
        now=NOW,
        allowed_repositories=("aevespers2/0",),
    )
    assert not result.allowed
    assert "missing_controls" in {finding.code for finding in result.findings}
