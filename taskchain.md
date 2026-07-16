# Task Chain

Architect owns task dependencies, sequencing, acceptance criteria, and boundaries. Builders execute one highest-priority unblocked task at a time, preserve evidence and rollback paths, and do not infer product purpose from the repository name.

States: `PROPOSED` · `READY` · `IN PROGRESS` · `BLOCKED` · `REVIEW` · `DONE`

## Product directive

- **Next objective:** Approve a unique repository charter or explicitly retire/archive this repository.
- **User outcome:** Contributors can identify the problem, users, ownership boundary, inputs/outputs, verification strategy, and reason this repository exists before code or public capability claims are added.
- **MVP scope:** documentation-only charter with purpose, users, user outcome, non-goals, trust/data/security boundaries, repository relationships, license, supported environment, verification plan, and retirement criteria.
- **Priority:** The charter/retirement decision is the only active priority; implementation is blocked.
- **Success criteria:** a reviewed charter identifies a necessary non-overlapping product and first bounded task, or the repository is marked retired with links to the repositories that own the work.
- **Non-goals:** speculative code, schemas, integrations, workflows, credentials, deployments, or a release identity before the charter is approved.
- **Release rationale:** A documentation-only bootstrap may be useful; an ambiguous implementation release would create duplicated ownership and unverifiable expectations.

## Active chain

| Priority | Task | Owner | Depends on | Status | Acceptance criteria |
|---|---|---|---|---|---|
| P0 | Approve or retire the repository charter | Architect | User decision | BLOCKED | Purpose, users, inputs/outputs, non-goals, trust/data/security boundaries, relationships, license, verification, and retirement criteria are approved. |
| P1 | Define the first bounded Builder task | Architect | P0 approved as active | PROPOSED | Scope names files, tests, constraints, dependencies, stop conditions, and rollback guidance. |
| P2 | Archive the repository | Architect | P0 retirement decision | BLOCKED | README, repository description, and release state clearly identify retirement and replacement repositories. |

## Builder Log

Record approval decisions, commits, verification commands/results, risks, retirement references, and follow-ups.