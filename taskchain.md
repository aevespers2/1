# Task Chain

Architect owns task dependencies, sequencing, acceptance criteria, and boundaries. Builders execute one highest-priority unblocked task at a time, preserve evidence and rollback paths, and do not treat a committed artifact as an approved product decision or verified capability.

States: `PROPOSED` · `READY` · `IN PROGRESS` · `BLOCKED` · `REVIEW` · `DONE`

## Product directive

- **Next objective:** Accept, revise, or reject the **Partitioned Versioning Trust Core** charter, Repository `1` capability-authority role, and the Repository `0` → Repository `1` gluing contract before additional implementation or external integration.
- **User outcome:** An operator can submit a bounded state-transition proposal from Repository `0`, receive a deterministic allow/reject decision and append-only receipt from Repository `1`, and recover a previously approved checkpoint without giving Muse, CI, a GitHub token, or an external adapter authority to rewrite canonical history.
- **MVP scope:** local-only reference design and later implementation of versioned envelopes, receipts, state-path events, deny-by-default partition/capability policy, deterministic verification, append-only local audit records, checkpoint creation/verification, recovery simulation, and an explicitly approved advisory path-audit function. The MVP contains no credentials, network listener, remote mutation, autonomous approval, or production key custody.
- **Priority:** `P0 — REVIEW / APPROVAL REQUIRED`. This is an immediate product-boundary, authority, and contract decision, not a portfolio reprioritization. QSO-GENOMES acceptance and the QuantumStateObjects runnable baseline retain their upstream priorities unless a separate decision changes them.
- **Success criteria:** the charter and Repository `0` boundary are approved; one canonical route interpretation is selected; schemas are versioned and fail closed; policy decisions, replay/expiry behavior, receipt chaining, checkpoint verification, recovery, and path-audit semantics are covered by deterministic positive and negative tests; threat model and key/capability lifecycle are documented; a clean checkout reproduces all checks; and no single GitHub, CI, agent, or adapter credential can mutate canonical state.
- **Non-goals:** replacing Git; claiming a secure transport exists; storing production secrets or root keys; operating a remote service; automatic publication/deployment; autonomous trust-anchor rotation; using heuristic anomaly scores as proof of compromise; bypassing GitHub protections; or treating draft code or documentation as release evidence before exact-head validation and approval.

## Current evidence state

### Observed on `main`

- README and architecture/access/audit documents describing the Repository `0` → Repository `1` proposal and approval flow.
- `schemas/state-path-event.schema.json`.
- `partitioned_versioning/policy.py` with a deny-by-default transition evaluator.
- Muse access and visual-audit design documents.

VTX-envelope, transition-receipt, capability, approval, revocation, checkpoint, and execution-receipt schemas remain planned unless separately observed and pinned. Documentation must not describe them as accepted default-branch implementation.

### Draft implementation candidate — PR #1

**Status:** `REVIEW — EXACT-HEAD SECURITY CI PASSED; PRODUCT AND CONTRACT GATES REMAIN BLOCKED`

- exact head: `0813308061e27e8289ea8f15af7d5ccdc84b4abf`;
- Security Readiness run `29667702838`: `PASS`;
- retained artifact digest: `sha256:2c7ff8100c706051763de1aff69c6f8d1652c418445c1d8894499335fcf67f94`;
- implemented only in the draft: path-audit model, advisory dispositions, token-assignment preflight safeguards, tests, and deployment-readiness documentation.

The passing run verifies the submitted candidate's stated checks. It does not approve Repository `1` as capability authority, resolve the cross-repository route, validate private key custody or a private authority store, authorize token issuance, or make the draft merge/release ready.

### Documentation and governance candidate — PR #2

**Status:** `REVIEW — DOCUMENTATION MILESTONE; NO AUTHORITY EXPANSION`

The branch adds Pages-ready project, architecture, contract, capability-authority, obstruction/gluing, onboarding, operations, recovery, and rollback documentation plus exact-head validation. Completed run `29773845205` passed at head `4efc3e29280d85ad6173b71beaf2eec546f77e87` with artifact digest `sha256:95143ecf775930ac690c3e0ae86840a93a51297e5f67ba7f3ecbe43bb442feb9`. Later coordination edits require a new exact-head run before review readiness is claimed.

## Material gluing obstruction

Repository `0` draft PR #6 describes:

`0:working → 0:proposal → 1:quarantine`

Repository `1` draft PR #1 tests:

`0:working → 1:quarantine`

The lowest-coupling repair candidate is to define `0:proposal` as non-authoritative local staging in Repository `0`, with the cross-repository contract beginning when the versioned proposal envelope enters `1:quarantine`. This preserves Repository `0`'s proposal workflow without adding a Repository `1` proposal partition or granting staging authority. It remains a recommendation for explicit approval, not an implemented or accepted contract.

Approval requires one versioned route definition and shared positive, negative, stale, replay, unsupported-version, expected-head, and rollback fixtures pinned to immutable commits in both repositories.

## Architecture and authority gates

The Architect must record decisions for:

1. Repository `1` as canonical-state and capability authority, or an alternative owner;
2. constitutional input from `ALISTAIRE-` and separation from Repository `0` orchestration;
3. the inbound route and whether `0:proposal` is local staging;
4. package/schema ownership for envelopes, capabilities, approvals, receipts, revocations, checkpoints, and execution receipts;
5. canonical serialization, digest, clock, nonce, replay, expiry, and reason-code semantics;
6. private/offline authority-store topology, key custody, rotation, revocation, and loss recovery;
7. human owners for policy, approval, credentials, security, incident response, emergency stop, and recovery;
8. atomic receipt/state persistence, checkpoint, correction, rollback, and restart behavior.

## Active chain

| Priority | Task | Owner | Depends on | Status | Acceptance criteria |
|---|---|---|---|---|---|
| P0 | Approve, revise, or reject the trust-core charter, capability-authority role, and canonical route model | Architect | User approval | REVIEW | Purpose, users, Repository `0` boundary, authority model, partitions, route semantics, MVP, non-goals, threat model, key/capability ownership, release identity, and retirement/rollback option are approved. |
| P0A | Review the capability-authority and obstruction/gluing documentation | Architect | P0 evidence preparation | REVIEW | Authority classes, separation of duties, cross-repository contracts, obstruction ledger, recommended route repair, emergency stop, and open decisions are accurate and bounded. |
| P1 | Inventory and verify default-branch artifacts and both draft candidates | Architect | P0 approval | BLOCKED | Exact files and commits are recorded; planned versus observed contracts are separated; schemas validate; policy/path/token behavior is classified; coordination records are current. |
| P2 | Specify the local deterministic trust-core MVP and shared fixture corpus | Architect | P1 | PROPOSED | Named files, APIs, route, state transitions, ownership, failure modes, fixtures, test matrix, evidence outputs, stop conditions, and rollback are Builder-ready. |
| P3 | Implement and test the local no-network MVP | Builder | P2 | PROPOSED | Envelope/receipt validation, replay/expiry checks, append-only audit records, checkpoint verification, recovery simulation, approved advisory behavior, and negative fixtures pass from a clean checkout. |
| P4 | Review an optional Repository `0` or external adapter | Architect | P3 and separate approval | PROPOSED | Adapter has proposal/execution-only authority, no root credentials, bounded operations, execution receipts, revocation, and failure recovery; remote writes remain disabled by default. |
| P5 | Consider a release candidate | Releaser | P3 or approved P4 | PROPOSED | Tests, security review, provenance, SBOM/dependencies, documentation, artifacts, checksums, rollback drill, and explicit approval pass at one immutable commit. |

## Builder rules

- No implementation Builder task is `READY` until P0 is approved and P2 is decomposed.
- Documentation may compare and recommend route/authority candidates but must not silently activate one.
- Do not add credentials, webhooks, network listeners, GitHub write workflows, external publication, or production key material under the current directive.
- Treat capability statements, anomaly scores, token safeguards, and passing draft CI as bounded evidence rather than product approval.
- Stop on ambiguous authority, inconsistent route semantics, unclear key custody, non-reproducible state, missing exact-head evidence, or an undefined rollback path.

## Evidence rules

Record approval decisions, source commits, commands/results, schema and fixture hashes, policy decisions, path-audit findings, security findings, dependency/tool versions, artifacts, limitations, superseded evidence, rollback instructions, and follow-up work.

## Builder log

- 2026-07-20 — Reconciled PR #1 to exact head `0813308061e27e8289ea8f15af7d5ccdc84b4abf` and successful Security Readiness run `29667702838`; preserved every product, route, key-custody, private-store, release, and deployment blocker.
- 2026-07-20 — Added capability-authority and obstruction/gluing documentation, recorded the local-staging route recommendation for review, separated observed from planned schemas, and required shared pairwise and triple-overlap fixtures. No implementation or privileged authority was added.
