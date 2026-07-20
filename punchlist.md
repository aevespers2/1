# Punch List

This punch list validates the proposed local Partitioned Versioning Trust Core and its cross-repository gluing contracts. Checked items require reproducible evidence tied to one immutable commit. Design text or a committed file alone is not completion evidence.

## P0 — Product, governance, and authority approval

- [ ] Approve, revise, or reject Repository `1` as the canonical state-transition, capability, revocation, receipt, and recovery authority.
- [ ] Approve the Repository `0` proposal-only boundary and prohibited authorities.
- [ ] Accept an immutable `ALISTAIRE-` governance-policy input and define how policy changes become active.
- [ ] Accept, revise, or reject [ADR-0001](docs/adr/0001-canonical-state-and-capability-authority.md).
- [ ] Approve partition semantics and permitted transition classes.
- [ ] Define requester, operator, Architect, Builder, verifier, approver, issuer, CI, adapter, reconciler, incident, emergency-stop, and recovery authority.
- [ ] Define key/capability ownership, issuance, rotation, revocation, expiry, use count, freeze behavior, and loss recovery.
- [ ] Approve the local-only MVP, release identity, non-goals, public-mirror/private-authority topology, and retirement/rollback option.

## P0A — Route and gluing decision

- [ ] Approve one Repository `0` → Repository `1` route interpretation.
- [ ] Decide whether `0:proposal` is a contractual partition, non-authoritative local staging, or removed.
- [ ] Record the recommended local-staging interpretation and its rejected alternatives in an ADR or equivalent decision record.
- [ ] Assign package/schema ownership for envelopes, capabilities, approvals, receipts, revocations, checkpoints, execution receipts, and shared reason codes.
- [ ] Define canonical serialization, digest, expected-head, clock, skew, nonce, replay-domain, expiry, and idempotency semantics.
- [ ] Create shared positive, negative, stale, replay, unsupported-version, mismatch, partial-failure, and rollback fixtures pinned to exact commits in Repository `0` and Repository `1`.
- [ ] Create triple-overlap fixtures for `ALISTAIRE-` → Repository `0` → Repository `1` and Repository `0` → Repository `1` → adapter.

## P1 — Candidate inventory and contract review

- [x] Record PR #1 exact head `0813308061e27e8289ea8f15af7d5ccdc84b4abf`, Security Readiness run `29667702838`, and artifact digest `sha256:2c7ff8100c706051763de1aff69c6f8d1652c418445c1d8894499335fcf67f94`.
- [ ] Record the immutable default-branch candidate commit and exact artifact inventory.
- [ ] Reconcile README, Pages, project guide, architecture, capability-authority, obstruction/gluing, ADR, task chain, punch list, changelog, release plan, and deployment status at one exact head.
- [ ] Separate observed default-branch artifacts from planned and draft-only contracts.
- [ ] Validate each observed JSON Schema against Draft 2020-12 and deterministic valid/invalid fixtures.
- [ ] Define canonical serialization and payload-digest rules.
- [ ] Define expiry, nonce, replay, approval, signature, receipt-chain, correction, revocation, and supersession semantics.
- [ ] Define fail-closed error taxonomy, stable reason codes, compatibility/versioning policy, and migration rules.
- [ ] Validate all relative documentation links and retain exact-head evidence after final coordination edits.

## P2 — Local implementation and tests

- [ ] Test every deny-by-default policy rejection and allowed transition.
- [ ] Implement deterministic envelope and receipt verification.
- [ ] Implement replay/expiry and payload-tamper rejection.
- [ ] Implement append-only local receipt chaining with corruption detection.
- [ ] Commit accepted receipt and resulting canonical state atomically; prove failure between writes cannot leave partial canonical state.
- [ ] Implement checkpoint creation, verification, and recovery simulation.
- [ ] Keep path-audit findings advisory and prove they cannot override canonical policy.
- [ ] Add positive, negative, tamper, replay, stale, approval, recovery, revocation, freeze, expected-head, partial-failure, and property-based fixtures where practical.
- [ ] Run targeted and complete tests from a clean checkout at one immutable commit.

## P3 — Security, provenance, and release evidence

- [ ] Threat model trust roots, policy substitution, key compromise, confused deputy, forged receipts, rollback attacks, replay, dependency compromise, UI approval confusion, Bridge/adapter compromise, and public-mirror confusion.
- [ ] Verify no secret, network listener, webhook, GitHub remote write, production key, or live credential is included in the local candidate.
- [ ] Define and independently review private/offline authority-store and key-custody design.
- [ ] Test issuance, expiry, maximum use, revocation, freeze, no-auto-unlock, and bounded restart order without live credentials.
- [ ] Record dependency/runtime/tool versions and produce an SBOM or explicit dependency manifest.
- [ ] Generate test, security, provenance, documentation, and reproducibility reports.
- [ ] Generate source/package artifacts and SHA-256 checksum manifest.
- [ ] Perform and record a route rollback, receipt/state atomicity, checkpoint recovery, and portfolio freeze/restart drill.
- [ ] Record explicit release approval.

## Open obstruction ledger

| ID | Obstruction | Exit witness |
|---|---|---|
| `O-01` | Repository `0` inbound route mismatch | approved route plus shared fixtures |
| `O-02` | capability authority not contractually accepted | immutable governance and authority decision |
| `O-03` | GitHub success may be confused with canonical state | authorization/execution reconciliation fixtures |
| `O-04` | envelope and receipt ownership gap | one contract owner and compatibility policy |
| `O-05` | identity and revocation semantics differ or are absent across genome, authority, and runtime layers | versioned identity reference, revocation propagation, and stale-identity fixtures |
| `O-06` | freeze and restart domains not unified | no-auto-unlock contract and recovery exercise |
| `O-07` | accepted receipt/state atomicity unproved | deterministic fault-injection evidence |
| `O-08` | clock and replay domains undefined | canonical time/replay contract and boundary tests |
| `O-09` | public mirror/private authority topology unresolved | reviewed deployment, redaction, custody, and recovery design |
| `O-10` | UI review can be confused with approval | signed approval contract and read-only negative tests |
| `O-11` | path-audit score may leak into authorization | policy non-interference tests |
| `O-12` | correction, revocation, supersession, and evidence retention are not unified | versioned correction record, supersession links, retention/redaction policy, and review-surface fixtures |

## Evidence log

Record date, task, source commit, commands, environment, result (`PASS`, `FAIL`, or `UNKNOWN`), artifacts/hashes, limitations, reviewer, and follow-up work.

- 2026-07-20 — PR #1 exact-head security evidence recorded. Result applies to the draft implementation checks only; product, route, authority, private-store, credential, release, and deployment approval remain blocked.
- 2026-07-20 — Capability-authority, ADR, and obstruction/gluing documents added to PR #2. Latest coordination edits require a fresh exact-head Documentation run before the documentation reconciliation item may be checked.
