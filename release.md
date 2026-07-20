# Release Plan

## Current Decision

Status: `BLOCKED — PORTABLE PRODUCT, ROUTE, AUTHORITY, SECURITY, PLATFORM, AND VERIFICATION APPROVAL REQUIRED`

Repository `1` contains a concrete **Partitioned Versioning Trust Core** candidate and now has a clarified product role: it is the proposed independent baseline, capability, revocation, receipt, checkpoint, and recovery authority paired with Repository `0` for first installation on newly acquired, replaced, reset, recovered, or suspect owned devices. The default branch contains architecture and access documentation, one observed state-path-event schema, and a small deny-by-default Python policy evaluator. Device-identity, baseline-policy, inventory, proposal, capability, approval, revocation, checkpoint, resulting-state, transition-receipt, and execution-receipt contracts remain planned or draft-only unless separately observed and pinned.

The product charter, canonical authority model, Repository `0` route contract, device and baseline identity lifecycle, per-platform control matrix, private/offline authority topology, key/capability custody, privacy policy, and local-only portable MVP have not been approved.

Draft PR #1 at exact head `0813308061e27e8289ea8f15af7d5ccdc84b4abf` adds path auditing, token-assignment preflight safeguards, tests, and deployment-readiness documentation. Security Readiness run `29667702838` passed and retained artifact digest `sha256:2c7ff8100c706051763de1aff69c6f8d1652c418445c1d8894499335fcf67f94`. This is bounded implementation evidence, not portable product or authority approval. It does not validate a private trust store, production key custody, live token issuance, route compatibility, durable canonical storage, device identity, platform controls, or release readiness.

Draft PR #2 adds a Pages-ready overview, project guide, portable device trust baseline, capability-authority model, obstruction/gluing ledger, contract and state-machine design, developer onboarding, and local operations/recovery playbook. Earlier documentation evidence applies to superseded heads. The latest portable-bootstrap coordination edits require a fresh exact-head run before the documentation candidate is review-ready.

## Versioning

- Scheme: Semantic Versioning after the portable product charter, capability-authority role, route model, device identity, and platform support policy are approved.
- First possible candidate: `0.0.1-portable-trust-core.1`.
- Path-audit functionality may be included only if its advisory status, interfaces, error semantics, calibration, and policy non-interference are explicitly approved.
- Platform profiles may version independently but must identify the core contract version they require.
- No networked, GitHub-integrated, token-bearing, secret-bearing, remote-administration, or production-key release may be versioned before the local prototype passes and a separate integration approval is recorded.

## Candidate Scope

- Versioned device identity, baseline-policy identity, inventory, proposal, capability, approval, transition-receipt, revocation, checkpoint, resulting-state, execution-receipt, and state-path-event contracts.
- Deny-by-default capability and partition-transition evaluation.
- Replay/expiry, wrong-device, expected-head, canonical serialization, nonce, payload-digest, and approval verification.
- Append-only local receipt chain with corruption detection.
- Atomic accepted receipt and resulting canonical-state persistence.
- Checkpoint creation, verification, and lost/replaced-device recovery simulation.
- Per-platform profile classification of supported, advisory, unavailable, and out-of-scope controls.
- An optional, explicitly advisory path-audit function with deterministic fixtures and no canonical allow/reject authority.
- Deterministic positive, negative, wrong-device, stale, replay, tamper, recovery, route, revocation, freeze, partial-failure, and policy-boundary fixtures.
- Threat model, privacy/retention policy, capability/key lifecycle, clean-checkout instructions, provenance, artifacts, checksums, and rollback drill.

## Explicit Exclusions

- Production secrets, root keys, live GitHub tokens, or secret-bearing public repository state.
- Network listeners, webhooks, remote publication, GitHub write automation, device-management agents, or autonomous approval.
- Trust-anchor rotation, destructive history changes, force push, repository administration, workflow/secret mutation, or self-modification.
- Intrusive surveillance, traffic interception, counter-intrusion, or control of devices without ownership or explicit permission.
- Automatic deletion, quarantine, or remediation based solely on anomaly or suspicion.
- Claims that GitHub, VTX, a path score, passing CI, a successful command, or any existing transport proves a device secure or uncompromised.
- Any route contract not jointly approved and tested against Repository `0` fixtures.
- Treating Studio, AionUi, Pages, comments, transported messages, or external success as canonical approval.

## Route and Gluing Decision

The active obstruction is the mismatch between:

- `0:working → 0:proposal → 1:quarantine`; and
- `0:working → 1:quarantine`.

The documentation candidate recommends, but does not approve, treating `0:proposal` as non-authoritative local staging in Repository `0`, with the cross-repository contract beginning when a versioned device proposal envelope enters `1:quarantine`. Approval requires one versioned route definition, device/baseline identity semantics, contract/package ownership, and shared pairwise and triple-overlap fixtures pinned to immutable commits.

## Selected Completed Work

- Product direction and Repository `0` relationship are documented as a candidate.
- The portable first-install trust role, device lifecycle, baseline domains, capability scope, and lost/replaced-device recovery flow are documented.
- One observed state-path-event schema and a deny-by-default policy evaluator are present on the default branch.
- PR #1 has successful exact-head Security Readiness evidence for its draft-only path-audit and token-preflight surface.
- GitHub Pages-ready project navigation, authority separation, obstruction/gluing analysis, architecture, contract design, onboarding, operating evidence, recovery, incident, and rollback requirements are documented.

These items remain subject to acceptance review and do not satisfy portable product, route, authority, durable-state, private-store, device-identity, credential, platform, release, or deployment gates.

## Acceptance Gates

| Gate | Status | Requirement |
|---|---|---|
| Product approval | BLOCKED | Accept, revise, or reject the portable trust-core charter, Repository `1` role, authorized device scope, partitions, release identity, local-only MVP, and retirement/rollback option. |
| Capability authority | BLOCKED | Approve constitutional input, authority classes, separation of duties, issuer/revoker ownership, human approvals, freeze, recovery, and prohibited self-authorization. |
| Route contract | BLOCKED | Select one canonical route interpretation; define whether `0:proposal` is contractual, local staging, or removed; assign contract/package ownership; add shared pairwise and triple-overlap fixtures. |
| Device and baseline identity | NO EVIDENCE | Define device identity, ownership scope, replacement/retirement, baseline-policy identity, platform profile, expected-head binding, and wrong-device rejection. |
| Platform profiles | NO EVIDENCE | Classify macOS, Linux, Windows, Android, iOS, and constrained-environment controls as supported, advisory, unavailable, or out of scope with evidence requirements. |
| Privacy and retention | NO EVIDENCE | Approve purpose limitation, redaction, retention, export, deletion, sensitive-field handling, and public/private evidence boundaries for device inventories. |
| Artifact inventory | PARTIAL | Bind every default-branch and draft candidate file and claim to immutable commits and reconcile coordination documents. |
| Contract validation | NO EVIDENCE | Validate observed and accepted schemas, canonical serialization, error taxonomy, versioning, migration, and fail-closed behavior with deterministic fixtures. |
| Policy tests | PARTIAL | PR #1 has bounded exact-head test evidence; complete issuer, device, repository, operation, transition, branch, replay, expiry, approvals, use count, revocation, freeze, and protected-authority fixtures remain required. |
| Path audit | BLOCKED | Approve advisory ownership and semantics; test route gaps, digest continuity, false positives/negatives, thresholds, deterministic errors, and policy non-interference. |
| Ledger/recovery | NOT IMPLEMENTED | Append-only receipt chain, atomic receipt/state commit, checkpoint verification, lost/replaced-device recovery, tamper detection, and restoration simulation pass. |
| Security | PARTIAL | PR #1 validates bounded preflight controls; complete threat model, private/offline store, trust/key lifecycle, redaction, package/startup/network/Bluetooth/sharing boundaries, dependency review, abuse cases, and revocation/recovery drills remain absent. |
| Reproducibility/CI | PARTIAL | PR #1 exact-head security CI passed; documentation requires a fresh exact-head run; complete local portable trust-core clean-checkout evidence remains absent. |
| Documentation | PARTIAL | Project, Pages, portable baseline, authority, obstruction/gluing, architecture, contract, onboarding, operations, recovery, incident, and rollback material exist; final exact-head validation and architectural approval remain. |
| Provenance | PARTIAL | Draft workflow artifacts and hashes exist; complete candidate manifest, tool/runtime versions, platform evidence, source/package artifacts, approvals, and supersession records remain. |
| Deployment | NOT AUTHORIZED | No deployment, token issuance, device agent, private gateway activation, remote write, or canonical-state service is part of this candidate. |
| Approval | PENDING | Release approval is recorded only after every blocking gate passes. |

## Artifact Requirements

- Accepted portable product, authority, route, device/baseline identity, schema/package ownership, privacy, platform, and public/private topology decisions.
- Source and rendered architecture, portable baseline, capability-authority, obstruction/gluing, route-contract, access-control, threat-model, onboarding, and operations documentation.
- Machine-readable contracts and deterministic shared fixture corpus with Repository `0` and relevant triple overlaps.
- Per-platform inventories and support declarations containing no secrets.
- Policy and advisory path-audit test reports, including negative, wrong-device, calibration, and non-interference fixtures.
- Atomic receipt/state, receipt-chain, checkpoint, loss/replacement recovery, correction, revocation, and supersession evidence.
- Test, security, privacy, dependency, clean-checkout, documentation, and reproducibility reports.
- Credential issuance/revocation design evidence without live credentials.
- Incident-response, emergency-stop, no-auto-unlock, bounded restart, and rollback-drill evidence.
- SBOM or explicit dependency manifest where applicable.
- Source/package artifacts with SHA-256 checksums.
- Provenance manifest tied to one immutable candidate commit and explicit approval record.

## Rollback Criteria

Withdraw the candidate if authority, device identity, baseline identity, privacy, or key custody is ambiguous; Repository `0` and `1` route semantics diverge; the local prototype can mutate state outside policy; path scores become canonical authorization; replay, wrong-device, tamper, revoked, or frozen cases are accepted; receipt and state can diverge; checkpoint or loss/replacement recovery is non-reproducible; unsupported state is reported as secure; clean-checkout results differ; token/revocation controls are absent; external success is mistaken for canonical promotion; or documentation implies remote/device security guarantees unsupported by evidence. Restore the pre-candidate reviewed commit and preserve failed and superseded evidence.

## Unresolved Blockers

- Explicit portable product, canonical-authority, route-model, device/baseline identity, schema/package ownership, release-identity, local-MVP, privacy, platform, and retirement/rollback approval.
- Reconciliation of the Repository `0` proposal stage with Repository `1` quarantine entry.
- `punchlist.md` completion and immutable candidate inventory.
- Fresh exact-head Documentation evidence after the latest portable-bootstrap coordination changes.
- Path-audit calibration, advisory ownership, error semantics, policy interaction, and false-positive/false-negative fixtures.
- Complete contract, policy, wrong-device, replay, expiry, tamper, capability, revocation, freeze, expected-head, and cross-repository tests.
- Durable append-only ledger, atomic receipt/state persistence, checkpoint recovery, and loss/replacement implementation.
- Threat model, per-platform profiles, privacy/retention policy, private/offline authority design, key/capability lifecycle, dependency/security review, provenance, artifacts, checksums, and rollback drill.
- Private credential gateway, branch protections, redaction checks, and revocation drill remain non-operational and outside the local candidate.

## Release Log

- 2026-07-20: Clarified Repository `1` as the portable first-install baseline, capability, revocation, receipt, checkpoint, and recovery authority paired with Repository `0`; no operational authority was enabled.
- 2026-07-20: Reconciled PR #1 to exact-head Security Readiness evidence, added capability-authority and obstruction/gluing documentation, and recorded the local-staging route recommendation for review; no authority or release gate was approved.
- 2026-07-19: Added a documentation milestone covering Pages, project boundaries, contracts, onboarding, operations, recovery, incidents, and rollback; all product, route, verification, security, and release gates remained blocked or incomplete.
- 2026-07-16: Reclassified the newly committed trust-core artifacts as a blocked local prototype candidate; no release or deployment approved.
