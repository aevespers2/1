# Punch List

This punch list validates the proposed local Partitioned Versioning Trust Core, its portable first-install role, and its cross-repository gluing contracts. Checked items require reproducible evidence tied to one immutable commit. Design text or a committed file alone is not completion evidence.

## P0 — Product, governance, and authority approval

- [ ] Approve, revise, or reject Repository `1` as the canonical device-baseline, state-transition, capability, revocation, receipt, checkpoint, and recovery authority.
- [ ] Approve the Repository `0` bootstrap, inspection, proposal, bounded-execution, and prohibited-authority boundary.
- [ ] Define authorized device scope: owned devices or environments with explicit permission only.
- [ ] Accept an immutable `ALISTAIRE-` governance-policy input and define how policy changes become active.
- [ ] Accept, revise, or reject [ADR-0001](docs/adr/0001-canonical-state-and-capability-authority.md).
- [ ] Approve partition semantics and permitted transition classes.
- [ ] Define requester, device owner, operator, Architect, Builder, verifier, approver, issuer, CI, adapter, reconciler, privacy, incident, emergency-stop, and recovery authority.
- [ ] Define key/capability ownership, issuance, rotation, revocation, expiry, use count, freeze behavior, and loss recovery.
- [ ] Approve the local-only portable MVP, release identity, non-goals, public-mirror/private-authority topology, and retirement/rollback option.
- [ ] Approve prohibited uses: unauthorized-device control, interception, counter-intrusion, covert monitoring, evidence destruction, automatic deletion, and unsupported claims of compromise or security.

## P0A — Portable identity, route, and gluing decision

- [ ] Approve one Repository `0` → Repository `1` route interpretation.
- [ ] Decide whether `0:proposal` is a contractual partition, non-authoritative local staging, or removed.
- [ ] Record the recommended local-staging interpretation and its rejected alternatives in an ADR or equivalent decision record.
- [ ] Define device identity, ownership scope, enrollment, replacement, retirement, loss, theft, and uncertain-state semantics.
- [ ] Define baseline-policy identity, platform-profile identity, expected-head binding, and migration rules.
- [ ] Assign package/schema ownership for inventory, proposals, envelopes, capabilities, approvals, receipts, revocations, checkpoints, resulting-state records, execution receipts, and shared reason codes.
- [ ] Define canonical serialization, digest, expected-head, clock, skew, nonce, replay-domain, expiry, and idempotency semantics.
- [ ] Create shared positive, negative, stale, replay, unsupported-version, wrong-device, revoked-device, mismatch, partial-failure, and rollback fixtures pinned to exact commits in Repository `0` and Repository `1`.
- [ ] Create triple-overlap fixtures for `ALISTAIRE-` → Repository `0` → Repository `1`, Repository `0` → Repository `1` → platform adapter, and Repository `0` → Repository `1` → recovery store.

## P0B — Platform, privacy, and recovery policy

- [ ] Define per-platform support profiles for macOS, Linux, Windows, Android, iOS, and constrained environments.
- [ ] Classify each control as supported, advisory, unavailable, or out of scope.
- [ ] Define baseline domains for package managers, package sources, shell initialization, startup agents/jobs/services, accounts, certificates, profiles, browser extensions, DNS, proxy, VPN, routes, forwarding, firewall, hotspot/tethering, sharing, Bluetooth, backups, and recovery.
- [ ] Define trusted-bootstrap assumptions before Homebrew or another package manager is trusted.
- [ ] Define purpose limitation, sensitive fields, redaction, retention, export, deletion, and public/private evidence boundaries for device inventories.
- [ ] Define lost, stolen, replaced, retired, and unavailable-device revocation semantics.
- [ ] Require unsupported or unobservable state to remain `UNKNOWN`.
- [ ] Require anomaly findings to remain separate from attacker attribution and authorization policy.

## P1 — Candidate inventory and contract review

- [x] Record PR #1 exact head `0813308061e27e8289ea8f15af7d5ccdc84b4abf`, Security Readiness run `29667702838`, and artifact digest `sha256:2c7ff8100c706051763de1aff69c6f8d1652c418445c1d8894499335fcf67f94`.
- [ ] Record the immutable default-branch candidate commit and exact artifact inventory.
- [ ] Reconcile README, Pages, portable baseline, project guide, architecture, capability-authority, obstruction/gluing, ADR, task chain, punch list, changelog, release plan, and deployment status at one exact head.
- [ ] Separate observed default-branch artifacts from planned and draft-only contracts.
- [ ] Validate each observed JSON Schema against Draft 2020-12 and deterministic valid/invalid fixtures.
- [ ] Define canonical serialization and payload-digest rules.
- [ ] Define expiry, nonce, replay, approval, signature, receipt-chain, correction, revocation, device replacement, and supersession semantics.
- [ ] Define fail-closed error taxonomy, stable reason codes, compatibility/versioning policy, and migration rules.
- [ ] Validate all relative documentation links and retain exact-head evidence after final coordination edits.

## P2 — Local implementation and tests

- [ ] Test every deny-by-default policy rejection and allowed transition.
- [ ] Implement deterministic envelope and receipt verification.
- [ ] Implement wrong-device, replay/expiry, and payload-tamper rejection.
- [ ] Implement append-only local receipt chaining with corruption detection.
- [ ] Commit accepted receipt and resulting canonical state atomically; prove failure between writes cannot leave partial canonical state.
- [ ] Implement checkpoint creation, verification, and lost/replaced-device recovery simulation.
- [ ] Keep path-audit findings advisory and prove they cannot override canonical policy.
- [ ] Add positive, negative, wrong-device, tamper, replay, stale, approval, recovery, revocation, freeze, expected-head, partial-failure, and property-based fixtures where practical.
- [ ] Run targeted and complete tests from a clean checkout at one immutable commit.

## P3 — Security, provenance, and release evidence

- [ ] Threat model trust roots, policy substitution, device-identity collision, key compromise, confused deputy, forged receipts, rollback attacks, replay, dependency compromise, package-source compromise, startup persistence, UI approval confusion, Bridge/adapter compromise, public-mirror confusion, and privacy exposure.
- [ ] Verify no secret, network listener, webhook, GitHub remote write, device-management agent, production key, or live credential is included in the local candidate.
- [ ] Define and independently review private/offline authority-store and key-custody design.
- [ ] Test issuance, expiry, maximum use, revocation, freeze, no-auto-unlock, lost/replaced-device handling, and bounded restart order without live credentials.
- [ ] Record dependency/runtime/tool versions and produce an SBOM or explicit dependency manifest.
- [ ] Generate test, security, privacy, provenance, documentation, platform-profile, and reproducibility reports.
- [ ] Generate source/package artifacts and SHA-256 checksum manifest.
- [ ] Perform and record a route rollback, receipt/state atomicity, checkpoint recovery, device-loss/replacement, and portfolio freeze/restart drill.
- [ ] Record explicit release approval.

## Open obstruction ledger

| ID | Obstruction | Exit witness |
|---|---|---|
| `O-01` | Repository `0` inbound route mismatch | approved route plus shared fixtures |
| `O-02` | capability and portable baseline authority not contractually accepted | immutable governance and authority decision |
| `O-03` | GitHub or device-command success may be confused with canonical state | authorization/execution reconciliation fixtures |
| `O-04` | device, baseline, envelope, and receipt ownership gap | one contract owner and compatibility policy |
| `O-05` | identity and revocation semantics differ or are absent across device, genome, authority, and runtime layers | versioned identity references, revocation propagation, and stale/wrong-identity fixtures |
| `O-06` | freeze and restart domains not unified | no-auto-unlock contract and recovery exercise |
| `O-07` | accepted receipt/state atomicity unproved | deterministic fault-injection evidence |
| `O-08` | clock and replay domains undefined | canonical time/replay contract and boundary tests |
| `O-09` | public mirror/private authority topology unresolved | reviewed deployment, redaction, custody, and recovery design |
| `O-10` | UI review can be confused with approval | signed approval contract and read-only negative tests |
| `O-11` | path-audit or anomaly score may leak into authorization or attribution | policy non-interference and attribution-separation tests |
| `O-12` | correction, revocation, device replacement, supersession, and evidence retention are not unified | versioned correction/replacement records, supersession links, retention/redaction policy, and review-surface fixtures |
| `O-13` | platform controls differ and unsupported state may be overclaimed | versioned platform profiles and `UNKNOWN` negative fixtures |
| `O-14` | device inventory may expose sensitive information | approved minimization, redaction, retention, export, and deletion policy |
| `O-15` | unavailable prior device may be treated as remotely revoked without evidence | external-authority receipt or explicit `UNKNOWN/UNCONFIRMED` state |

## Evidence log

Record date, task, source commit, commands, environment, result (`PASS`, `FAIL`, or `UNKNOWN`), artifacts/hashes, device/platform scope, privacy limitations, reviewer, and follow-up work.

- 2026-07-20 — PR #1 exact-head security evidence recorded. Result applies to the draft implementation checks only; portable product, route, authority, private-store, credential, platform, release, and deployment approval remain blocked.
- 2026-07-20 — Capability-authority, ADR, and obstruction/gluing documents added to PR #2. Latest coordination edits require a fresh exact-head Documentation run before the documentation reconciliation item may be checked.
- 2026-07-20 — Added portable device identity, baseline, platform, privacy, lost/replaced-device, attribution-separation, and gluing acceptance work without enabling implementation or authority.
