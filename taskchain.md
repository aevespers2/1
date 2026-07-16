# Task Chain

Architect owns task dependencies, sequencing, acceptance criteria, and boundaries. Builders execute one highest-priority unblocked task at a time, preserve tests and rollback paths, and record evidence.

States: `PROPOSED` · `READY` · `IN PROGRESS` · `BLOCKED` · `REVIEW` · `DONE`

| Priority | Task | Owner | Depends on | Status | Acceptance criteria |
|---|---|---|---|---|---|
| P0 | Establish repository purpose and baseline | Architect | — | READY | Repository purpose, constraints, initial structure, and verification approach are documented. |
| P1 | Define first bounded Builder task | Architect | P0 | PROPOSED | Scope names files, tests, constraints, and rollback guidance. |

## Builder Log
Record commits, verification commands/results, risks, and follow-ups.
