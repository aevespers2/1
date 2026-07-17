# Task Chain

Architect owns task dependencies, sequencing, acceptance criteria, and boundaries. Builders execute one highest-priority unblocked task at a time, preserve evidence and rollback paths, and do not treat a committed artifact as an approved product decision or verified capability.

States: `PROPOSED` · `READY` · `IN PROGRESS` · `BLOCKED` · `REVIEW` · `DONE`

## Product directive

- **Next objective:** Accept, revise, or reject the newly introduced **Partitioned Versioning Trust Core** charter before any additional implementation or external integration.
- **User outcome:** An operator can submit a bounded state-transition proposal from Repository `0`, receive a deterministic allow/reject decision and append-only receipt from Repository `1`, and recover a previously approved checkpoint without giving Muse, CI, a GitHub token, or an external adapter authority to rewrite canonical history.
- **MVP scope:** local-only reference implementation of versioned VTX envelopes, transition receipts, state-path events, deny-by-default partition/capability policy, deterministic verification, append-only local audit records, checkpoint creation/verification, and recovery simulation. The MVP contains no credentials, network listener, remote mutation, autonomous approval, or production key custody.
- **Priority:** `P0 — REVIEW / APPROVAL REQUIRED`. This is an immediate product-boundary decision, not a portfolio reprioritization. QSO-GENOMES acceptance and the QuantumStateObjects runnable baseline retain their existing upstream priorities unless a separate decision changes them.
- **Success criteria:** the charter and Repository `0` boundary are approved; schemas are versioned and fail closed; policy decisions, replay/expiry behavior, receipt chaining, checkpoint verification, and recovery are covered by deterministic positive and negative tests; threat model and key/capability lifecycle are documented; a clean checkout reproduces all checks; and no single GitHub, CI, agent, or adapter credential can mutate canonical state.
- **Non-goals:** replacing Git itself; claiming a secure transport exists; storing production secrets or root keys; operating a remote service; automatic publication/deployment; autonomous trust-anchor rotation; bypassing GitHub protections; or treating the current schema and policy commits as release evidence before validation.
- **Release rationale:** a small local trust-core prototype can establish verifiable authority separation and recovery semantics before any webhook, GitHub, VTX transport, or multi-repository automation is allowed. Shipping remote integration first would turn an unreviewed design into a security dependency.

## Evidence classification

### Observed implemented artifacts — not yet accepted

- README and architecture documents describing Repository `0` → Repository `1` proposal and approval flow.
- `schemas/vtx-envelope.schema.json`, `schemas/transition-receipt.schema.json`, and `schemas/state-path-event.schema.json`.
- `partitioned_versioning/policy.py` with a deny-by-default transition evaluator.
- Muse access, communication, and visual audit design documents.

These artifacts establish a concrete candidate direction. They do **not** establish cryptographic verification, durable append-only storage, replay protection, checkpoint recovery, test coverage, secure key custody, transport security, or release readiness.

## Active chain

| Priority | Task | Owner | Depends on | Status | Acceptance criteria |
|---|---|---|---|---|---|
| P0 | Approve, revise, or reject the Partitioned Versioning Trust Core charter | Architect | User approval | REVIEW | Purpose, users, Repository `0` boundary, authority model, partitions, MVP, non-goals, threat model, key/capability ownership, release identity, and retirement/rollback option are approved. |
| P1 | Inventory and verify the committed candidate artifacts | Architect | P0 approval | BLOCKED | Exact files and commit are recorded; schemas validate; policy behavior is tested; missing implementation is separated from proposals; stale coordination documents are reconciled. |
| P2 | Specify the local deterministic trust-core MVP | Architect | P1 | PROPOSED | Named files, APIs, state transitions, failure modes, fixtures, test matrix, evidence outputs, stop conditions, and rollback are Builder-ready. |
| P3 | Implement and test the local no-network MVP | Builder | P2 | PROPOSED | Envelope/receipt validation, replay/expiry checks, append-only audit records, checkpoint verification, recovery simulation, and negative fixtures pass from a clean checkout. |
| P4 | Review an optional Repository `0` adapter | Architect | P3 and separate approval | PROPOSED | Adapter has proposal-only authority, no root credentials, bounded operations, execution receipts, revocation, and failure recovery; remote writes remain disabled by default. |
| P5 | Consider a release candidate | Releaser | P3 or approved P4 | PROPOSED | Tests, security review, provenance, SBOM/dependencies, documentation, artifacts, checksums, rollback drill, and explicit approval pass at one immutable commit. |

## Builder rules

- No Builder task is `READY` until P0 is approved and P2 is decomposed.
- Do not add credentials, webhooks, network listeners, GitHub write workflows, external publication, or production key material under the current directive.
- Treat all current capability statements as design claims until reproduced by tests and evidence.
- Stop on ambiguous authority, unclear key custody, non-reproducible state, or an undefined rollback path.

## Builder log

Record approval decisions, source commits, commands/results, schema and fixture hashes, policy decisions, security findings, dependency/tool versions, artifacts, limitations, rollback evidence, and follow-up work.