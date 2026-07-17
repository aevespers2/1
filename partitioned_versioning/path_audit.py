from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterable, Sequence


@dataclass(frozen=True)
class Location:
    repository: str
    partition: str
    branch: str | None = None
    state_id: str | None = None


@dataclass(frozen=True)
class PathEvent:
    event_id: str
    occurred_at: datetime
    actor_id: str
    action: str
    source: Location
    target: Location
    payload_digest: str
    policy_id: str
    decision: str = "observed"
    previous_event_id: str | None = None
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class Finding:
    code: str
    weight: float
    message: str


@dataclass(frozen=True)
class AuditResult:
    score: float
    disposition: str
    findings: tuple[Finding, ...]


NORMAL_PARTITION_EDGES = frozenset({
    ("working", "working"),
    ("working", "quarantine"),
    ("quarantine", "reviewed"),
    ("reviewed", "canonical"),
    ("canonical", "release"),
    ("release", "external"),
    ("external", "audit"),
    ("canonical", "recovery"),
    ("recovery", "canonical"),
})


def _finding(code: str, weight: float, message: str) -> Finding:
    return Finding(code=code, weight=weight, message=message)


def audit_path(
    events: Sequence[PathEvent],
    *,
    known_actor_repositories: Iterable[str] = (),
    allowed_branch_prefixes: Sequence[str] = ("proposal/", "feature/", "release/"),
) -> AuditResult:
    """Score a path without asserting malicious intent.

    The result is deterministic and intentionally conservative. Repository 1 may
    pause or quarantine a path based on the score, but a finding is evidence for
    review rather than proof of compromise.
    """
    findings: list[Finding] = []
    known = set(known_actor_repositories)
    rejected_count = 0

    for index, event in enumerate(events):
        edge = (event.source.partition, event.target.partition)
        if edge not in NORMAL_PARTITION_EDGES:
            findings.append(_finding(
                "unusual_partition_edge",
                0.28,
                f"Unusual partition transition {edge[0]} -> {edge[1]}.",
            ))

        if known and event.target.repository not in known:
            findings.append(_finding(
                "novel_repository",
                0.16,
                f"Actor entered previously unseen repository {event.target.repository}.",
            ))

        if event.target.branch and allowed_branch_prefixes:
            if not any(event.target.branch.startswith(prefix) for prefix in allowed_branch_prefixes):
                findings.append(_finding(
                    "unusual_branch",
                    0.12,
                    f"Branch {event.target.branch!r} is outside expected prefixes.",
                ))

        if event.decision == "rejected":
            rejected_count += 1

        if index:
            previous = events[index - 1]
            if event.previous_event_id and event.previous_event_id != previous.event_id:
                findings.append(_finding(
                    "event_chain_discontinuity",
                    0.35,
                    "Event chain does not reference the immediately preceding event.",
                ))
            if previous.payload_digest != event.payload_digest:
                findings.append(_finding(
                    "digest_discontinuity",
                    0.45,
                    "Payload digest changed between adjacent path events.",
                ))
            if previous.target.repository != event.source.repository:
                findings.append(_finding(
                    "repository_path_gap",
                    0.22,
                    "Observed route contains an unexplained repository boundary gap.",
                ))

    if rejected_count >= 3:
        findings.append(_finding(
            "repeated_rejections",
            min(0.3, rejected_count * 0.06),
            f"Path contains {rejected_count} rejected attempts.",
        ))

    raw_score = sum(item.weight for item in findings)
    score = round(min(1.0, raw_score), 4)
    if score >= 0.7:
        disposition = "quarantine"
    elif score >= 0.35:
        disposition = "pause_for_review"
    else:
        disposition = "observe"
    return AuditResult(score=score, disposition=disposition, findings=tuple(findings))


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
