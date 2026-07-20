# Release Plan

## Current Decision

Status: `BLOCKED — PRODUCT, ROUTE, AUTHORITY, SECURITY, AND VERIFICATION APPROVAL REQUIRED`

Repository `1` contains a concrete **Partitioned Versioning Trust Core** candidate: architecture and access documentation, one observed state-path-event schema, and a small deny-by-default Python policy evaluator on the default branch. VTX-envelope, transition-receipt, capability, approval, revocation, checkpoint, and execution-receipt contracts remain planned or draft-only unless separately observed and pinned. The product charter, canonical authority model, Repository `0` route contract, private/offline authority topology, key/capability custody, and local-only MVP have not been approved.

Draft PR #1 at exact head `0813308061e27e8289ea8f15af7d5ccdc84b4abf` adds path auditing, token-assignment preflight safeguards, tests, and deployment-readiness documentation. Security Readiness run `29667702838` passed and retained artifact digest `sha256:2c7ff8100c706051763de1aff69c6f8d1652c418445c1d8894499335fcf67f94`. This is bounded implementation evidence, not product or authority approval. It does not validate a private trust store, production key custody, live token issuance, route compatibility, durable canonical storage, or release readiness.

Draft PR #2 adds a Pages-ready overview, project guide, capability-authority model, obstruction/gluing ledger, contract and state-machine design, developer onboarding, and local operations/recovery playbook. Documentation run `29773845205` passed at head `4efc3e29280d85ad6173b71beaf2eec546f77e87` with artifact digest `sha256:95143ecf775930ac690c3e0ae86840a93a51297e5f67ba7f3ecbe43bb442feb9`. Later coordination edits require a fresh exact-head run before the documentation candidate is review-ready.

## Versioning

- Scheme: Semantic Versioning after the product charter, capability-authority role, and route model are approved.
- First possible candidate: `0.0.1-local-trust-core.1`.
- Path-audit functionality may be included only if its advisory status, interfaces, error semantics, calibration, and policy non-interference are explicitly approved.
- No networked, GitHub-integrated, token-bearing, secret-bearing, or production-key release may be versioned before the local prototype passes and a separate integration approval is recorded.

## Candidate Scope

- Versioned envelope, capability, approval, transition-receipt, revocation, checkpoint, execution-receipt, and state-path-event contracts.
- Deny-by-default capability and partition-transition evaluation.
- Replay/expiry, expected-head, canonical serialization, nonce, payload-digest, and approval verification.
- Append-only local receipt chain with corruption detection.
- Atomic accepted receipt and resulting canonical-state persistence.
- Checkpoint creation, verification, and recovery simulation.
- An optional, explicitly advisory path-audit function with deterministic fixtures and no canonical allow/reject authority.
- Deterministic positive, negative, replay, tamper, recovery, route, revocation, freeze, partial-failure, and policy-boundary fixtures.
- Threat model, capability/key lifecycle, clean-checkout instructions, provenance, artifacts, checksums, and rollback drill.

## Explicit Exclusions

- Production secrets, root keys, live GitHub tokens, or secret-bearing public repository state.
- Network listeners, webhooks, remote publication, GitHub write automation, or autonomous approval.
- Trust-anchor rotation, destructive history changes, force push, repository administration, workflow/secret mutation, or self-modification.
- Claims that GitHub, VTX, a path score, passing CI, or any existing transport is secure merely because schemas, tests, and policy code exist.
- Any route contract not jointly approved and tested against Repository `0` fixtures.
- Treating Studio, AionUi, Pages, comments, transported messages, or external success as canonical approval.

## Route and Gluing Decision

The active obstruction is the mismatch between:

- `0:working → 0:proposal → 1:quarantine`; and
- `0:working → 1:quarantine`.

The documentation candidate recommends, but does not approve, treating `0:proposal` as non-authoritative local staging in Repository `0`, with the cross-repository contract beginning when a versioned envelope enters `1:quarantine`. Approval requires one versioned route definition, contract/package ownership, and shared pairwise and triple-overlap fixtures pinned to immutable commits.

## Selected Completed Work

- Product direction and Repository `0` relationship are documented as a candidate.
- One observed state-path-event schema and a deny-by-default policy evaluator are present on the default branch.
- PR #1 has successful exact-head Security Readiness evidence for its draft-only path-audit and token-preflight surface.
- GitHub Pages-ready project navigation, authority separation, obstruction/gluing analysis, architecture, contract design, onboarding, operating evidence, recovery, incident, and rollback requirements are documented.

These items remain subject to acceptance review and do not satisfy product, route, authority, durable-state, private-store, credential, release, or deployment gates.

## Acceptance Gates

| Gate | Status | Requirement |
|---|---|---|
| Product approval | BLOCKED | Accept, revise, or reject the charter, Repository `1` role, partitions, release identity, local-only MVP, and retirement/rollback option. |
| Capability authority | BLOCKED | Approve constitutional input, authority classes, separation of duties, issuer/revoker ownership, human approvals, freeze, recovery, and prohibited self-authorization. |
| Route contract | BLOCKED | Select one canonical route interpretation; define whether `0:proposal` is contractual, local staging, or removed; assign contract/package ownership; add shared pairwise and triple-overlap fixtures. |
| Artifact inventory | PARTIAL | Bind every default-branch and draft candidate file and claim to immutable commits and reconcile coordination documents. |
| Contract validation | NO EVIDENCE | Validate observed and accepted schemas, canonical serialization, error taxonomy, versioning, migration, and fail-closed behavior with deterministic fixtures. |
| Policy tests | PARTIAL | PR #1 has bounded exact-head test evidence; complete issuer, repository, operation, transition, branch, replay, expiry, approvals, use count, revocation, freeze, and protected-authority fixtures remain required. |
| Path audit | BLOCKED | Approve advisory ownership and semantics; test route gaps, digest continuity, false positives/negatives, thresholds, deterministic errors, and policy non-interference. |
| Ledger/recovery | NOT IMPLEMENTED | Append-only receipt chain, atomic receipt/state commit, checkpoint verification, tamper detection, and restoration simulation pass. |
| Security | PARTIAL | PR #1 validates bounded preflight controls; complete threat model, private/offline store, trust/key lifecycle, redaction, dependency review, unsafe-boundary checks, abuse cases, and revocation/recovery drills remain absent. |
| Reproducibility/CI | PARTIAL | PR #1 exact-head security CI passed; documentation passed at a superseded PR #2 head and requires rerun; complete local trust-core clean-checkout evidence remains absent. |
| Documentation | PARTIAL | Project, Pages, authority, obstruction/gluing, architecture, contract, onboarding, operations, recovery, incident, and rollback material exist; final exact-head validation and architectural approval remain. |
| Provenance | PARTIAL | Draft workflow artifacts and hashes exist; complete candidate manifest, tool/runtime versions, source/package artifacts, approvals, and supersession records remain. |
| Deployment | NOT AUTHORIZED | No deployment, token issuance, private gateway activation, remote write, or canonical-state service is part of this candidate. |
| Approval | PENDING | Release approval is recorded only after every blocking gate passes. |

## Artifact Requirements

- Accepted product, authority, route, schema/package ownership, and public/private topology decisions.
- Source and rendered architecture, capability-authority, obstruction/gluing, route-contract, access-control, threat-model, onboarding, and operations documentation.
- Machine-readable contracts and deterministic shared fixture corpus with Repository `0` and relevant triple overlaps.
- Policy and advisory path-audit test reports, including negative, calibration, and non-interference fixtures.
- Atomic receipt/state, receipt-chain, checkpoint, recovery, correction, revocation, and supersession evidence.
- Test, security, dependency, clean-checkout, documentation, and reproducibility reports.
- Credential issuance/revocation design evidence without live credentials.
- Incident-response, emergency-stop, no-auto-unlock, bounded restart, and rollback-drill evidence.
- SBOM or explicit dependency manifest where applicable.
- Source/package artifacts with SHA-256 checksums.
- Provenance manifest tied to one immutable candidate commit and explicit approval record.

## Rollback Criteria

Withdraw the candidate if authority or key custody is ambiguous, Repository `0` and `1` route semantics diverge, the local prototype can mutate state outside policy, path scores become canonical authorization, replay/tamper/revoked/frozen cases are accepted, receipt and state can diverge, checkpoint verification is non-reproducible, clean-checkout results differ, token/revocation controls are absent, external success is mistaken for canonical promotion, or documentation implies remote/canonical security guarantees unsupported by evidence. Restore the pre-candidate reviewed commit and preserve failed and superseded evidence.

## Unresolved Blockers

- Explicit product, canonical-authority, route-model, schema/package ownership, release-identity, local-MVP, and retirement/rollback approval.
- Reconciliation of the Repository `0` proposal stage with Repository `1` quarantine entry.
- `punchlist.md` completion and immutable candidate inventory.
- Fresh exact-head Documentation evidence after the latest PR #2 coordination changes.
- Path-audit calibration, advisory ownership, error semantics, policy interaction, and false-positive/false-negative fixtures.
- Complete contract, policy, replay, expiry, tamper, capability, revocation, freeze, expected-head, and cross-repository tests.
- Durable append-only ledger, atomic receipt/state persistence, and recovery implementation.
- Threat model, private/offline authority design, key/capability lifecycle, dependency/security review, provenance, artifacts, checksums, and rollback drill.
- Private credential gateway, branch protections, redaction checks, and revocation drill remain non-operational and outside the local candidate.

## Release Log

- 2026-07-20: Reconciled PR #1 to exact-head Security Readiness evidence, added capability-authority and obstruction/gluing documentation, and recorded the local-staging route recommendation for review; no authority or release gate was approved.
- 2026-07-19: Added a documentation milestone covering Pages, project boundaries, contracts, onboarding, operations, recovery, incidents, and rollback; all product, route, verification, security, and release gates remained blocked or incomplete.
- 2026-07-16: Reclassified the newly committed trust-core artifacts as a blocked local prototype candidate; no release or deployment approved.
