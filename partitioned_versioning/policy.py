from __future__ import annotations

from dataclasses import dataclass, field
from typing import FrozenSet


PARTITIONS = frozenset({
    "working",
    "reviewed",
    "canonical",
    "release",
    "quarantine",
    "audit",
    "recovery",
})


@dataclass(frozen=True)
class Capability:
    issuer: str
    repositories: FrozenSet[str]
    operations: FrozenSet[str]
    transitions: FrozenSet[tuple[str, str]]
    branch_prefixes: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason: str


def evaluate(
    capability: Capability,
    *,
    issuer: str,
    repository: str,
    operation: str,
    source_partition: str,
    target_partition: str,
    target_branch: str | None = None,
) -> Decision:
    """Evaluate one requested transition using deny-by-default semantics."""
    if source_partition not in PARTITIONS or target_partition not in PARTITIONS:
        return Decision(False, "unknown_partition")
    if issuer != capability.issuer:
        return Decision(False, "issuer_mismatch")
    if repository not in capability.repositories:
        return Decision(False, "repository_not_permitted")
    if operation not in capability.operations:
        return Decision(False, "operation_not_permitted")
    if (source_partition, target_partition) not in capability.transitions:
        return Decision(False, "transition_not_permitted")
    if target_branch and capability.branch_prefixes:
        if not any(target_branch.startswith(prefix) for prefix in capability.branch_prefixes):
            return Decision(False, "branch_not_permitted")
    return Decision(True, "allowed")
