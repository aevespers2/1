from datetime import datetime, timezone

from partitioned_versioning.path_audit import Location, PathEvent, audit_path


NOW = datetime(2026, 7, 16, tzinfo=timezone.utc)
DIGEST = "sha256:" + ("a" * 64)


def event(event_id: str, source: Location, target: Location, previous: str | None = None, digest: str = DIGEST):
    return PathEvent(
        event_id=event_id,
        occurred_at=NOW,
        actor_id="muse",
        action="proposed",
        source=source,
        target=target,
        payload_digest=digest,
        policy_id="muse-proposal-v1",
        previous_event_id=previous,
    )


def test_expected_path_remains_observational():
    events = [
        event("event-0000000001", Location("aevespers2/0", "working"), Location("aevespers2/1", "quarantine")),
        event("event-0000000002", Location("aevespers2/1", "quarantine"), Location("aevespers2/1", "reviewed"), "event-0000000001"),
        event("event-0000000003", Location("aevespers2/1", "reviewed"), Location("aevespers2/1", "canonical"), "event-0000000002"),
    ]
    result = audit_path(events, known_actor_repositories={"aevespers2/0", "aevespers2/1"})
    assert result.score == 0
    assert result.disposition == "observe"


def test_direct_release_and_digest_change_are_quarantined():
    events = [
        event("event-0000000001", Location("aevespers2/0", "working"), Location("aevespers2/1", "release")),
        event(
            "event-0000000002",
            Location("aevespers2/1", "release"),
            Location("github", "external", branch="main"),
            "event-0000000001",
            digest="sha256:" + ("b" * 64),
        ),
    ]
    result = audit_path(events, known_actor_repositories={"aevespers2/0", "aevespers2/1"})
    assert result.disposition == "quarantine"
    codes = {finding.code for finding in result.findings}
    assert "unusual_partition_edge" in codes
    assert "digest_discontinuity" in codes
