# Release Plan

## Current Decision
Status: `BLOCKED`

No work is eligible for release. P0 is only `READY`, `punchlist.md` is absent, no completed Builder evidence is recorded, and reviewed commit `eb39b796e4a754fb80cab61991296d2c7b27b668` has no reported commit-status checks.

## Versioning
- Scheme: Semantic Versioning.
- First eligible candidate: `0.0.1-bootstrap`.
- Do not tag until repository purpose, constraints, verification approach, and a bounded implementation scope are approved and reproducibly verified.

## Candidate Scope
- Approved repository charter and non-goals.
- Repository map, supported runtimes, dependency/build/test commands, and trust boundaries.
- A Builder-ready first task with named files, tests, constraints, and rollback guidance.
- Minimal CI, security checks, documentation, and provenance reporting.

## Selected Completed Work
None. The coordination and changelog files are administrative setup only.

## Planned Changelog Entries
- `Added`: repository charter, baseline verification, and first bounded implementation contract.
- `Security`: documented trust boundary, dependency/secret checks, and least-privilege CI.
- `Documentation`: reproducible setup, verification, and rollback instructions.

## Acceptance Gates
| Gate | Status | Requirement |
|---|---|---|
| Task completion | FAIL | P0 marked `DONE` with evidence; P1 defined and completed if included. |
| Build/tests | NO EVIDENCE | Clean build, lint/static checks, tests, and smoke test pass. |
| Security | NO EVIDENCE | Dependency, secret, permissions, and supply-chain checks pass. |
| Documentation | FAIL | Purpose, constraints, setup, usage, and rollback are not yet established. |
| Provenance | NO EVIDENCE | Commit, commands, tool versions, and artifact hashes recorded. |
| Approval | PENDING | Explicit approval after all blocking gates pass. |

## Artifact Requirements
- Charter and baseline report.
- Test/static/security reports.
- Checksummed release bundle or source archive.
- Provenance manifest tied to the release commit.

## Rollback Criteria
Withdraw the candidate if repository purpose changes materially, verification is non-reproducible, severe security findings remain, or release contents exceed the approved charter. Before the first release, rollback means removing the candidate tag/release and returning to the last reviewed commit.

## Unresolved Blockers
- Repository purpose and acceptance boundaries are not established.
- `punchlist.md` and completed Builder evidence are missing.
- No CI, test, security, documentation, or provenance evidence is attached to the reviewed commit.

## Release Log
- 2026-07-16: Bootstrap candidate evaluated and held `BLOCKED`; no completed work selected.