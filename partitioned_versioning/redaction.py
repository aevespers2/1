from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable


PATTERNS = (
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"ghs_[A-Za-z0-9]{20,}"),
    re.compile(r"gho_[A-Za-z0-9]{20,}"),
    re.compile(r"Bearer\s+[A-Za-z0-9._~+/=-]{20,}", re.IGNORECASE),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |)PRIVATE KEY-----"),
)


@dataclass(frozen=True)
class RedactionFinding:
    pattern: str
    start: int
    end: int


def detect_secret_material(text: str) -> tuple[RedactionFinding, ...]:
    findings: list[RedactionFinding] = []
    for pattern in PATTERNS:
        for match in pattern.finditer(text):
            findings.append(RedactionFinding(pattern=pattern.pattern, start=match.start(), end=match.end()))
    return tuple(findings)


def redact(text: str, replacement: str = "[REDACTED]") -> str:
    redacted = text
    for pattern in PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


def assert_secret_free(values: Iterable[str]) -> None:
    for index, value in enumerate(values):
        findings = detect_secret_material(value)
        if findings:
            raise ValueError(f"secret-like material detected in value {index}")
