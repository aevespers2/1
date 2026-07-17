from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Mapping


@dataclass(frozen=True)
class RevocationRecord:
    grant_id: str
    revoked_at: datetime
    reason: str
    authority: str


@dataclass
class RevocationRegistry:
    revoked: dict[str, RevocationRecord] = field(default_factory=dict)
    global_freeze: bool = False
    freeze_reason: str = ""

    def revoke(self, grant_id: str, *, reason: str, authority: str) -> RevocationRecord:
        record = RevocationRecord(
            grant_id=grant_id,
            revoked_at=datetime.now(timezone.utc),
            reason=reason,
            authority=authority,
        )
        self.revoked[grant_id] = record
        return record

    def freeze(self, *, reason: str) -> None:
        self.global_freeze = True
        self.freeze_reason = reason

    def unfreeze(self) -> None:
        self.global_freeze = False
        self.freeze_reason = ""

    def is_allowed(self, grant_id: str) -> tuple[bool, str]:
        if self.global_freeze:
            return False, "global_freeze"
        if grant_id in self.revoked:
            return False, "grant_revoked"
        return True, "active"

    def snapshot(self) -> Mapping[str, object]:
        return {
            "global_freeze": self.global_freeze,
            "freeze_reason": self.freeze_reason,
            "revoked_grants": sorted(self.revoked),
        }
