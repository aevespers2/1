# Obstruction and Gluing Analysis

## Method

This document treats each repository as a local capability section and each versioned contract as a gluing map. A composition is considered coherent only when the same request, identity, authority, state, and evidence have compatible meanings on every overlap.

The terms **obstruction**, **overlap**, and **gluing** are used here as an engineering discipline. They identify concrete incompatibilities and missing witnesses; they do not claim that a formal cohomology computation has been completed.

## Current obstruction classes

| ID | Obstruction | Affected overlap | Consequence | Required repair witness |
|---|---|---|---|---|
| `O-01` | Inbound route mismatch | Repository `0` ↔ Repository `1` | one side specifies `0:proposal`; the other may accept direct `0:working → 1:quarantine` | one approved route decision plus shared positive and fail-closed fixtures |
| `O-02` | Capability authority is named but not contractually bound | `ALISTAIRE-` ↔ Repository `0` ↔ Repository `1` | orchestration, governance, and authorization can be interpreted differently | accepted governance commit, capability schema ownership, and triple-overlap fixtures |
| `O-03` | Canonical state versus GitHub state ambiguity | Repository `1` ↔ GitHub adapter | a successful remote write could be mistaken for canonical promotion | expected-head authorization, execution receipt, reconciliation, and mismatch fixtures |
| `O-04` | Envelope and receipt ownership gap | Repository `0` ↔ Repository `1` ↔ Bridge | multiple repositories may define similar transport/evidence records without one version authority | package owner, compatibility policy, migration rules, and one pinned fixture corpus |
| `O-05` | Identity and revocation semantics are incomplete | Repository `1` ↔ QSO-GENOMES ↔ runtime | an identity may be recognized by one layer but revoked or unknown in another | versioned identity reference, revocation propagation, and stale-identity tests |
| `O-06` | Freeze and emergency-stop domains are not unified | `ALISTAIRE-` ↔ Repository `1` ↔ adapters | one component may resume while another remains compromised or uncertain | portfolio/domain freeze contract, no-auto-unlock rule, and restart-order exercise |
| `O-07` | Receipt/state atomicity is designed but not witnessed | Repository `1` local persistence | canonical state could exist without its accepted receipt, or vice versa | deterministic fault-injection fixtures proving atomic fail-closed behavior |
| `O-08` | Clock and replay domains are undefined | Repository `0` ↔ Repository `1` ↔ adapters | expiry and replay decisions can disagree across hosts or transports | canonical time policy, skew limits, nonce domain, and boundary fixtures |
| `O-09` | Public mirror versus private authority boundary is unresolved | public Repository `1` ↔ future private store | public source may be mistaken for live trust root or secret-bearing authority | deployment topology, key custody, redaction checks, and recovery procedure |
| `O-10` | UI review can be confused with approval | Repository `1` ↔ QSO-STUDIO/AionUi | annotation, button state, or browser session could be treated as authoritative approval | signed approval contract and read-only UI negative tests |
| `O-11` | Path-audit scores can leak into authorization | Repository `1` PR #1 ↔ policy evaluator | heuristic findings may silently become allow/reject policy | explicit advisory-only interface, calibrated fixtures, and policy non-interference tests |
| `O-12` | Correction, revocation, and evidence retention are not unified | Repository `1` ↔ Bridge ↔ public documentation | stale or invalid evidence may remain discoverable without canonical correction semantics | correction record, supersession links, retention/redaction policy, and UI rendering rules |

## Contract-edge gluing matrix

### Governance → orchestration → authority

| Edge | Producer promises | Consumer requires | Current status |
|---|---|---|---|
| `ALISTAIRE-` → Repository `0` | accepted mission, task authority, prohibited scope, required approvals | immutable policy reference and task boundary | proposed; no pinned portfolio contract |
| Repository `0` → Repository `1` | bounded proposal, identity, route, payload digest, requested capability, approvals | canonical serialization, accepted route, replay and policy inputs | blocked by `O-01` and schema ownership |
| Repository `1` → Repository `0` | accepted/rejected receipt, stable reason codes, resulting state reference | deterministic interpretation and retry/repair rules | proposed; receipt schema absent on default branch |

The triple overlap glues only when the governance policy referenced by Repository `0` is the same immutable policy evaluated by Repository `1`, and the requested capability cannot exceed the task authority granted by that policy.

### Authority → adapter → canonical reconciliation

| Edge | Producer promises | Consumer requires | Current status |
|---|---|---|---|
| Repository `1` → adapter | exact operation, target, expected head/effect, expiry, use count, payload digest | enforceable narrow authorization | documentation-only candidate |
| adapter → Repository `1` | object identifiers, resulting digests, status, errors, attempt identity | deterministic reconciliation and duplicate handling | not implemented |
| Repository `1` → canonical ledger | reconciled receipt and resulting state | atomic commit, chain integrity, checkpoint linkage | not implemented |

This overlap fails to glue if external success is accepted without matching the issued authorization or if canonical state changes before the receipt and result are durably committed together.

### Identity → capability → runtime

| Edge | Producer promises | Consumer requires | Current status |
|---|---|---|---|
| QSO-GENOMES → Repository `1` | versioned identity, lineage, policy and compatibility references | recognized subject/issuer identity and revocation semantics | ownership proposed; contract not pinned |
| Repository `1` → runtime/QSO | accepted capability or canonical state reference | verify version, scope, expiry, revocation, and target | not implemented |
| runtime/QSO → Repository `1` | execution/evidence receipt | reconciliation schema and privacy-safe evidence rules | not implemented |

A runtime must fail closed if the capability is absent, expired, revoked, for a different QSO, or references an unsupported genome or policy version.

### Evidence → review → publication

| Edge | Producer promises | Consumer requires | Current status |
|---|---|---|---|
| Repository `1` → Bridge | decision and execution receipts with provenance | versioned validation and correction rules | boundary unresolved |
| Bridge → QSO-STUDIO/AionUi | redacted review record and supersession links | deterministic rendering without authority escalation | proposed only |
| reviewed evidence → qso-field/publication | approved public fields and publication authority | no secrets, no stale capability implication | proposed only |

A review interface or public page is not a canonical authority. It may display evidence and approvals, but a click, comment, render, or publication cannot substitute for the signed approval and receipt contracts.

## Required triple-overlap witnesses

The following fixture groups are required because pairwise compatibility alone does not prove whole-system coherence.

### `T-01 — ALISTAIRE / Repository 0 / Repository 1`

- governance policy permits one bounded task;
- Repository `0` requests no broader capability;
- Repository `1` evaluates the exact same policy version;
- broader, stale, unknown, or self-modifying requests fail closed.

### `T-02 — Repository 0 / Repository 1 / GitHub adapter`

- one proposal becomes one narrow authorization;
- adapter performs only the authorized operation;
- expected-head mismatch, duplicate use, timeout, partial failure, and out-of-scope target are rejected or reconciled safely;
- external success alone does not produce canonical promotion.

### `T-03 — QSO-GENOMES / Repository 1 / QuantumStateObjects`

- identity and policy versions match across all three layers;
- revoked, incompatible, or unknown identities fail closed;
- execution evidence links to the same capability and genome lineage.

### `T-04 — Repository 1 / Bridge / QSO-STUDIO or AionUi`

- receipt fields survive transport without semantic change;
- private fields are redacted deterministically;
- superseded or revoked evidence is visibly marked;
- review UI cannot mint approval or capability records.

### `T-05 — Repository 1 / emergency stop / recovery owner`

- freeze revokes or blocks relevant capability issuance;
- in-flight execution is reconciled or quarantined;
- evidence is preserved;
- restart remains blocked until explicit recovery approval;
- components resume from least authority to greatest authority.

## Gluing invariants

1. **One immutable identifier per meaning.** Policy, identity, capability, request, receipt, checkpoint, and artifact identifiers must not be reinterpreted across repositories.
2. **One owner per versioned contract.** Other repositories may consume or mirror a contract but must not publish competing semantics under the same version.
3. **No authority by transport.** A message becomes authoritative only after the appropriate policy evaluation and receipt, not because Bridge, GitHub, WebSocket, or another transport delivered it.
4. **No authority by display.** Studio, AionUi, Pages, comments, and dashboards remain review surfaces unless a separate signed action contract is invoked.
5. **Exact-head compatibility.** Cross-repository evidence identifies every participating immutable commit and contract version.
6. **Fail-closed overlap.** Unknown versions, missing witnesses, conflicting state, stale approvals, or unavailable revocation state block promotion.
7. **Atomic accepted state.** Accepted receipt and resulting canonical state are one commit unit.
8. **Reversible composition.** Each edge documents rollback, correction, revocation, and recovery behavior.

## Prioritized repair sequence

| Priority | Repair | Why first |
|---|---|---|
| `G0` | approve Repository `1` role and constitutional input from `ALISTAIRE-` | other contracts cannot determine authority without this boundary |
| `G1` | resolve Repository `0` route and contract/package ownership | removes the immediate cross-repository path obstruction |
| `G2` | define identity, capability, approval, receipt, revocation, and reason-code schemas | creates common semantic objects for fixtures |
| `G3` | implement shared pairwise and triple-overlap fixture corpus | detects incompatible local success before integration |
| `G4` | specify atomic ledger/checkpoint/recovery behavior | prevents canonical state from diverging from evidence |
| `G5` | approve private authority/key-custody and public-mirror topology | required before any live credential or service design |
| `G6` | conduct portfolio freeze-and-recovery tabletop exercise | validates that stop and restart glue across components |

## Exit criteria

The obstruction ledger may mark an item resolved only when:

- an owner and immutable contract version are named;
- positive, negative, stale, replay, incompatible-version, and rollback fixtures pass;
- all participating repository commits are recorded;
- evidence and limitations are retained;
- `taskchain.md`, `release.md`, `punchlist.md`, and `changelog.md` are reconciled;
- the relevant human or independent approval is recorded where required.

Documentation agreement alone is progress, not resolution. Until the witnesses exist, the obstruction remains open and implementation must not silently choose a meaning.
