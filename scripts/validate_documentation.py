#!/usr/bin/env python3
"""Validate repository documentation without network access.

The validator checks the reviewed documentation surface for missing files and
broken relative Markdown links. External URLs and same-document anchors are
intentionally excluded because CI must remain deterministic and offline.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_PATHS = (
    Path("README.md"),
    Path("taskchain.md"),
    Path("punchlist.md"),
    Path("release.md"),
    Path("changelog.md"),
    Path("docs/index.md"),
    Path("docs/PROJECT_GUIDE.md"),
    Path("docs/ARCHITECTURE.md"),
    Path("docs/CAPABILITY_AUTHORITY.md"),
    Path("docs/OBSTRUCTION_AND_GLUING.md"),
    Path("docs/adr/0001-canonical-state-and-capability-authority.md"),
    Path("docs/DESIGN_CONTRACTS.md"),
    Path("docs/DEVELOPER_ONBOARDING.md"),
    Path("docs/OPERATIONS.md"),
    Path("docs/MUSE_ACCESS_MODEL.md"),
    Path("docs/_config.yml"),
)
MARKDOWN_LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")


def documentation_files() -> list[Path]:
    files = [path for path in REQUIRED_PATHS if path.suffix.lower() == ".md"]
    files.extend(path.relative_to(ROOT) for path in (ROOT / "docs").rglob("*.md"))
    return sorted(set(files), key=lambda item: item.as_posix())


def normalized_target(source: Path, raw_target: str) -> Path | None:
    target = raw_target.strip()
    if not target or target.startswith("#"):
        return None
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1].strip()
    split = urlsplit(target)
    if split.scheme or split.netloc:
        return None
    decoded_path = unquote(split.path)
    if not decoded_path:
        return None
    pure = PurePosixPath(decoded_path)
    if pure.is_absolute():
        raise ValueError("absolute repository path")
    candidate = (ROOT / source.parent / Path(*pure.parts)).resolve()
    try:
        return candidate.relative_to(ROOT)
    except ValueError as exc:
        raise ValueError("path escapes repository") from exc


def main() -> int:
    findings: list[dict[str, object]] = []
    checked_links = 0

    for required in REQUIRED_PATHS:
        if not (ROOT / required).is_file():
            findings.append({"kind": "missing-required-file", "path": required.as_posix()})

    for relative_source in documentation_files():
        source = ROOT / relative_source
        if not source.is_file():
            continue
        text = source.read_text(encoding="utf-8")
        for match in MARKDOWN_LINK.finditer(text):
            raw_target = match.group(1).split(maxsplit=1)[0]
            try:
                relative_target = normalized_target(relative_source, raw_target)
            except ValueError as exc:
                findings.append(
                    {
                        "kind": "invalid-relative-link",
                        "source": relative_source.as_posix(),
                        "target": raw_target,
                        "reason": str(exc),
                    }
                )
                continue
            if relative_target is None:
                continue
            checked_links += 1
            resolved = ROOT / relative_target
            if resolved.is_dir():
                resolved = resolved / "index.md"
            if not resolved.exists():
                findings.append(
                    {
                        "kind": "broken-relative-link",
                        "source": relative_source.as_posix(),
                        "target": raw_target,
                        "resolved": relative_target.as_posix(),
                    }
                )

    report = {
        "schema_version": 1,
        "documentation_files": [path.as_posix() for path in documentation_files()],
        "required_paths": [path.as_posix() for path in REQUIRED_PATHS],
        "checked_relative_links": checked_links,
        "findings": findings,
        "status": "pass" if not findings else "fail",
    }
    output = ROOT / "evidence" / "documentation" / "validation.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not findings else 1


if __name__ == "__main__":
    sys.exit(main())
