# Task Chain

Architect owns task dependencies, sequencing, acceptance criteria, and boundaries. Builders execute one highest-priority unblocked task at a time, preserve evidence and rollback paths, and do not treat a committed artifact as an approved product decision or verified capability.

States: `PROPOSED` · `READY` · `IN PROGRESS` · `BLOCKED` · `REVIEW` · `DONE`

## Product directive

- **Next objective:** Accept, revise, or reject the newly introduced **Partitioned Versioning Trust Core** charter and reconcile the Repository `0` → Repository `1` transition contract before any additional implementation or external integration.
- **User outcome:** An operator can submit a bounded state-transition proposal from Repository `0`, receive a deterministic allow/reject decision and append-only receipt from Repository `1`, and recover a previously approved checkpoint without giving Muse, CI, a GitHub token, or an external adapter authority to rewrite canonical history.
- **MVP scope:** local-only reference implementation of versioned VTX envelopes, transition receipts, state-path events, deny-by-default partition/capability policy, deterministic verification, append-only local audit records, checkpoint creation/verification, recovery simulation, and an explicitly approved advisory path-audit function. The MVP contains no credentials, network listener, remote mutation, autonomous approval, or production key custody.
- **Priority:** `P0 — REVIEW / APPROVAL REQUIRED`. This is an immediate product-boundary and contract decision, not a portfolio reprioritization. QSO-GENOMES acceptance and the QuantumStateObjects runnable baseline retain their existing upstream priorities unless a separate decision changes them.
- **Success criteria:** the charter and Repository `0` boundary are approved; one canonical route/state model is selected; schemas are versioned and fail closed; policy decisions, replay/expiry behavior, receipt chaining, checkpoint verification, recovery, and path-audit semantics are covered by deterministic positive and negative tests; threat model and key/capability lifecycle are documented; a clean checkout reproduces all checks; and no single GitHub, CI, agent, or adapter credential can mutate canonical state.
- **Non-goals:** replacing Git itself; claiming a secure transport exists; storing production secrets or root keys; operating a remote service; automatic publication/deployment; autonomous trust-anchor rotation; using heuristic anomaly scores as proof of compromise; bypassing GitHub protections; or treating current draft code as release evidence before validation.
- **Release rationale:** a small local trust-core prototype can establish verifiable authority separation, route semantics, and recovery behavior before any webhook, GitHub, VTX transport, or multi-repository automation is allowed. Shipping remote integration or authoritative anomaly scoring first would turn an unreviewed design into a security dependency.

## Evidence classification

### Observed implemented artifacts — not yet accepted

- README and architecture documents describing Repository `0` → Repository `1` proposal and approval flow.
- `schemas/vtx-envelope.schema.json`, `schemas/transition-receipt.schema.json`, and `schemas/state-path-event.schema.json`.
- `partitioned_versioning/policy.py` with a deny-by-default transition evaluator.
- Muse access, communication, and visual audit design documents.
- Draft PR #1 adds path-audit logic, token-assignment preflight safeguards, deployment-readiness documentation, and tests.

These artifacts establish a concrete candidate direction. They do **not** establish cryptographic verification, durable append-only storage, replay protection, checkpoint recovery, complete contract compatibility, calibrated security scoring, secure key custody, transport security, or release readiness.

## Draft implementation gate — PR #1

**Status:** `REVIEW — EARLY IMPLEMENTATION, NOT MERGE-READY`

Draft PR #1 was opened before P0 authority approval and before P1/P2 inventory and decomposition were completed. It therefore remains candidate evidence rather than an active Builder deliverable. Its current head is `e1b20b4cd59c5ec2aa0b2c92024868ffa6fd500f`; no GitHub Actions workflow run is attached to that head.

A cross-repository contract mismatch must be resolved: Repository `0` draft PR #6 documents `0:working -> 0:proposal -> 1:quarantine`, while PR #1 tests a direct `0:working -> 1:quarantine` transition and its normal edge set contains no `proposal` partition. The Architect must either add and define the proposal stage, remove it from the Repository `0` contract, or explicitly model it as local staging that is not part of Repository `1`'s authoritative transition graph.

The path score and thresholds are advisory review signals only. They must not become canonical allow/reject authority without an approved threat model, stable event schema, deterministic error semantics, calibration rationale, false-positive/false-negative fixtures, and a rule explaining how path findings interact with the deny-by-default policy evaluator. Token-assignment safeguards are likewise design evidence only; no token issuance, gateway activation, or remote authority is approved.

**Directive:** keep PR #1 draft. Do not merge until P0 is approved, P1 records the exact candidate inventory, P2 defines path-audit and token-preflight ownership and interfaces, the Repository `0` route contract is reconciled, exact-head clean-checkout CI and negative fixtures pass, and the Architect confirms whether each feature belongs in the local MVP or a later observability/integration layer.

## Active chain

| Priority | Task | Owner | Depends on | Status | Acceptance criteria |
|---|---|---|---|---|---|
| P0 | Approve, revise, or reject the Partitioned Versioning Trust Core charter and canonical route model | Architect | User approval | REVIEW | Purpose, users, Repository `0` boundary, authority model, partitions, route semantics, MVP, non-goals, threat model, key/capability ownership, release identity, and retirement/rollback option are approved. |
| P1 | Inventory and verify the committed candidate artifacts and both cross-repository drafts | Architect | P0 approval | BLOCKED | Exact files and commits are recorded; schemas validate; policy, path-audit, and token-preflight behavior are classified; missing implementation is separated from proposals; stale coordination documents and route conflicts are reconciled. |
| P2 | Specify the local deterministic trust-core MVP | Architect | P1 | PROPOSED | Named files, APIs, state transitions, cross-repository contracts, failure modes, fixtures, test matrix, evidence outputs, stop conditions, and rollback are Builder-ready. |
| P3 | Implement and test the local no-network MVP | Builder | P2 | PROPOSED | Envelope/receipt validation, replay/expiry checks, append-only audit records, checkpoint verification, recovery simulation, approved advisory behavior, and negative fixtures pass from a clean checkout. |
| P4 | Review an optional Repository `0` adapter | Architect | P3 and separate approval | PROPOSED | Adapter has proposal-only authority, no root credentials, bounded operations, execution receipts, revocation, and failure recovery; remote writes remain disabled by default. |
| P5 | Consider a release candidate | Releaser | P3 or approved P4 | PROPOSED | Tests, security review, provenance, SBOM/dependencies, documentation, artifacts, checksums, rollback drill, and explicit approval pass at one immutable commit. |

## Builder rules

- No Builder task is `READY` until P0 is approved and P2 is decomposed.
- Do not add credentials, webhooks, network listeners, GitHub write workflows, external publication, or production key material under the current directive.
- Treat all current capability statements, anomaly scores, and token safeguards as design claims until reproduced by exact-head tests and evidence.
- Stop on ambiguous authority, inconsistent route semantics, unclear key custody, non-reproducible state, or an undefined rollback path.

## Builder log

Record approval decisions, source commits, commands/results, schema and fixture hashes, policy decisions, path-audit findings, security findings, dependency/tool versions, artifacts, limitations, rollback evidence, and follow-up work.

- 2026-07-16 — Synchronized draft PR #1 to current head `e1b20b4cd59c5ec2aa0b2c92024868ffa6fd500f`; no workflow run is attached. The draft remains excluded from active implementation and release until product authority and route semantics are approved.