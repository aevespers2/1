# Release Plan

## Current Decision

Status: `BLOCKED — PRODUCT, ROUTE, SECURITY, AND VERIFICATION APPROVAL REQUIRED`

Repository `1` contains a concrete Partitioned Versioning Trust Core candidate on reviewed source baseline `c8df554eed6fead9dbf19082a64fcf09d15609a3`: architecture/access/audit documents, three transport/state schemas, and a deny-by-default Python policy evaluator. These are observed candidate artifacts, but the product charter, canonical authority model, Repository `0` route contract, key/capability custody, and local-only MVP have not been approved. There is no clean-checkout test, security, provenance, durable-ledger, recovery, artifact, checksum, or rollback evidence.

A documentation milestone now adds a Pages-ready overview, project guide, contract and state-machine design, developer onboarding, and local operations/recovery playbook. These materials clarify required behavior and evidence but do not validate or release any capability.

Draft PR #1 is not releasable completed work. Its current head `e1b20b4cd59c5ec2aa0b2c92024868ffa6fd500f` adds path auditing and token-assignment safeguards but has no GitHub Actions workflow run. It also conflicts with Repository `0` draft PR #6 by treating `0:working -> 1:quarantine` as the normal path while Repository `0` documents `0:working -> 0:proposal -> 1:quarantine`. Path scores and dispositions remain advisory observability signals and may not authorize canonical transitions.

## Versioning

- Scheme: Semantic Versioning after the product charter and route model are approved.
- First possible candidate: `0.0.1-local-trust-core.1`.
- Path-audit functionality may be included only if its advisory status, interfaces, error semantics, calibration, and policy interaction are explicitly approved.
- No networked, GitHub-integrated, token-bearing, or production-key release may be versioned before the local prototype passes and a separate integration approval is recorded.

## Candidate Scope

- Versioned VTX envelope, transition receipt, and state-path event contracts.
- Deny-by-default capability and partition-transition evaluation.
- Replay/expiry and payload-digest verification.
- Append-only local receipt chain with corruption detection.
- Checkpoint creation, verification, and recovery simulation.
- An optional, explicitly advisory path-audit function with deterministic fixtures and no canonical allow/reject authority.
- Deterministic positive, negative, replay, tamper, recovery, route, and policy-boundary fixtures.
- Threat model, capability/key lifecycle, clean-checkout instructions, provenance, artifacts, checksums, and rollback drill.

## Explicit Exclusions

- Production secrets, root keys, live GitHub tokens, or secret-bearing public repository state.
- Network listeners, webhooks, remote publication, GitHub write automation, or autonomous approval.
- Trust-anchor rotation, destructive history changes, force push, repository administration, workflow/secret mutation, or self-modification.
- Claims that GitHub, VTX, a path score, or any existing transport is secure merely because schemas and policy code exist.
- Any route contract not jointly approved and tested against Repository `0` fixtures.

## Selected Completed Work

- Product direction and Repository `0` relationship are documented as a candidate.
- Candidate schemas and a deny-by-default policy evaluator are present on the reviewed source baseline.
- GitHub Pages-ready project navigation, architecture diagrams, contract design, onboarding, operating evidence, recovery simulation, incident, and rollback requirements are documented.

These items remain subject to acceptance review and do not satisfy release gates. Draft PR #1 path-audit and token-safeguard code is unmerged, has no workflow evidence, and is excluded from completed release work.

## Planned Changelog Entries

- `Added`: validated local envelope, receipt, partition-policy, ledger, checkpoint, recovery, and approved advisory audit capabilities.
- `Security`: threat model, key/capability lifecycle, replay/tamper handling, token isolation, confused-deputy controls, dependency review, and abuse fixtures.
- `Compatibility`: canonical Repository `0` → Repository `1` route and fail-closed cross-repository fixtures.
- `Documentation`: local-only authority boundary, public-mirror limitations, operator ceremony, recovery, and non-goals.
- `Release`: immutable candidate commit, reports, SBOM/dependency manifest, source artifacts, checksums, provenance, rollback drill, and approval record.

## Acceptance Gates

| Gate | Status | Requirement |
|---|---|---|
| Product approval | BLOCKED | Accept, revise, or reject the charter, Repository `1` authority, Repository `0` proposal boundary, partitions, release identity, and local-only MVP. |
| Route contract | BLOCKED | Select one canonical route model; define whether `0:proposal` is authoritative, local staging, or removed; assign schema/package ownership; add shared positive and negative fixtures. |
| Artifact inventory | PARTIAL | Bind every reviewed-baseline and draft candidate file and claim to immutable commits and reconcile coordination documents. |
| Contract validation | NO EVIDENCE | Validate all schemas, canonical serialization, error taxonomy, versioning, and fail-closed behavior with deterministic fixtures. |
| Policy tests | NO EVIDENCE | Positive and fail-closed cases cover issuer, repository, operation, transition, branch, replay, expiry, approvals, token lifetime, revocation, and protected authorities. |
| Path audit | BLOCKED | Approve advisory ownership and semantics; test route gaps, digest continuity, false positives/negatives, thresholds, deterministic errors, and interaction with canonical policy. |
| Ledger/recovery | NOT IMPLEMENTED | Append-only receipt chain, checkpoint verification, tamper detection, and restoration simulation pass. |
| Security | NO EVIDENCE | Threat model, trust/key lifecycle, credential isolation, private/offline authoritative-store design, dependency review, unsafe-boundary checks, and abuse cases pass. |
| Reproducibility/CI | FAIL | Clean checkout reproduces complete tests and artifacts at the exact candidate commit; draft PR #1 currently has no workflow run. |
| Documentation | PARTIAL | Project, architecture, contract, onboarding, operations, recovery, incident, rollback, and Pages material exist; claims, commands, public-mirror limits, and operator procedures still require exact-head verification and review. |
| Provenance | NO EVIDENCE | Commit, commands, outputs, timestamps, environment, artifact hashes, review decisions, and approval record are retained. |
| Deployment | NOT AUTHORIZED | No deployment, token issuance, gateway activation, or remote write is part of this candidate. |
| Approval | PENDING | Release approval is recorded only after every blocking gate passes. |

## Artifact Requirements

- Source and rendered architecture, route-contract, access-control, threat-model, onboarding, and operations documentation.
- Machine-readable schemas and deterministic shared fixture corpus with Repository `0`.
- Policy and advisory path-audit test reports, including negative and calibration fixtures.
- Test, security, dependency, clean-checkout, documentation, and reproducibility reports.
- Receipt-chain and checkpoint/recovery evidence.
- Credential issuance/revocation design evidence without live credentials.
- Incident-response and rollback-drill evidence for local state corruption and incompatible recovery.
- SBOM or explicit dependency manifest where applicable.
- Source/package artifacts with SHA-256 checksums.
- Provenance manifest tied to the immutable candidate commit and explicit approval record.

## Rollback Criteria

Withdraw the candidate if authority or key custody is ambiguous, Repository `0` and `1` route semantics diverge, the local prototype can mutate state outside policy, path scores become canonical authorization, replay/tamper cases are accepted, receipt or checkpoint verification is non-reproducible, clean-checkout results differ, token/revocation controls are absent, or documentation implies remote/canonical security guarantees unsupported by evidence. Restore the pre-candidate reviewed commit and preserve failed evidence.

## Unresolved Blockers

- Explicit product, canonical-authority, route-model, schema/package ownership, release-identity, and local-MVP approval.
- Reconciliation of `0:working -> 0:proposal -> 1:quarantine` versus direct `0:working -> 1:quarantine` semantics.
- `punchlist.md` completion and immutable candidate inventory.
- Draft PR #1 has no exact-head GitHub Actions workflow evidence and is not merge-ready.
- Path-audit calibration, advisory ownership, error semantics, policy interaction, and false-positive/false-negative fixtures.
- Complete contract, policy, replay, expiry, tamper, token-boundary, and cross-repository tests.
- Durable append-only ledger and recovery implementation.
- Threat model, private/offline authority design, key/capability lifecycle, dependency/security review, provenance, artifacts, checksums, and rollback drill.
- Private credential gateway, branch protections, redaction checks, and revocation drill remain non-operational and outside the local candidate.

## Release Log

- 2026-07-16: Reclassified the newly committed trust-core artifacts as a blocked local prototype candidate; no release or deployment approved.
- 2026-07-16: Excluded draft PR #1 from completed release work, recorded the Repository `0`/`1` route-contract decision, and blocked path-audit authority and token assignment pending approval, CI, security, provenance, and recovery evidence.
- 2026-07-19: Added a documentation milestone covering Pages, project boundaries, contracts, onboarding, operations, recovery, incidents, and rollback; all product, route, verification, security, and release gates remain blocked or incomplete.
