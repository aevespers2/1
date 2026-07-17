# Release Plan

## Current decision

Status: `BLOCKED — PRODUCT APPROVAL AND VERIFICATION REQUIRED`

Repository `1` now contains a concrete Partitioned Versioning Trust Core candidate: architecture/access/audit documents, three transport/state schemas, and a deny-by-default Python policy evaluator. These are observed implementation artifacts, but the product charter has not been explicitly approved and there is no clean-checkout test, security, provenance, key-management, durable-ledger, recovery, or artifact evidence. No secure transport, remote integration, canonical-state guarantee, or deployable service is established.

## Versioning

- Scheme: Semantic Versioning after the product charter is approved.
- First possible candidate: `0.0.1-local-trust-core.1`.
- No networked, GitHub-integrated, or production-key release may be versioned before the local prototype passes and a separate integration approval is recorded.

## Candidate scope

- Versioned VTX envelope, transition receipt, and state-path event contracts.
- Deny-by-default capability and partition-transition evaluation.
- Replay/expiry and payload-digest verification.
- Append-only local receipt chain with corruption detection.
- Checkpoint creation, verification, and recovery simulation.
- Deterministic positive, negative, replay, tamper, recovery, and policy-boundary fixtures.
- Threat model, capability/key lifecycle, clean-checkout instructions, provenance, artifacts, checksums, and rollback drill.

## Explicit exclusions

- Production secrets or root keys.
- Network listeners, webhooks, remote publication, or GitHub write automation.
- Autonomous approval, trust-anchor rotation, destructive history changes, or self-modification.
- Claims that GitHub, VTX, or any existing transport is secure merely because schemas and policy code exist.

## Selected completed work

- Product direction and Repository `0` relationship are documented as a candidate.
- Candidate schemas and a policy evaluator are present.

These items remain subject to acceptance review and do not satisfy release gates.

## Acceptance gates

| Gate | Status | Requirement |
|---|---|---|
| Product approval | BLOCKED | Accept, revise, or reject the charter, authority boundary, partitions, key/capability ownership, and local-only MVP. |
| Artifact inventory | PARTIAL | Bind every candidate file and claim to one immutable commit and reconcile stale coordination documents. |
| Contract validation | NO EVIDENCE | Validate all schemas and canonicalization/error behavior with deterministic fixtures. |
| Policy tests | NO EVIDENCE | Positive and fail-closed cases cover issuer, repository, operation, transition, branch, replay, expiry, and approvals. |
| Ledger/recovery | NOT IMPLEMENTED | Append-only receipt chain, checkpoint verification, tamper detection, and restoration simulation pass. |
| Security | NO EVIDENCE | Threat model, trust/key lifecycle, credential isolation, dependency review, unsafe-boundary checks, and abuse cases pass. |
| Reproducibility | NO EVIDENCE | Clean checkout reproduces complete tests and artifacts with recorded tool/dependency versions. |
| Provenance | NO EVIDENCE | Commit, commands, outputs, timestamps, environment, artifact hashes, and approval record are retained. |
| Deployment | NOT AUTHORIZED | No deployment or remote write is part of this candidate. |
| Approval | PENDING | Release approval is recorded only after every blocking gate passes. |

## Artifact requirements

- Source and rendered architecture/threat-model documentation.
- Machine-readable schemas and deterministic fixture corpus.
- Test, security, dependency, and reproducibility reports.
- Receipt-chain and checkpoint/recovery evidence.
- SBOM or explicit dependency manifest where applicable.
- Source/package artifacts with SHA-256 checksums.
- Provenance manifest tied to the immutable candidate commit.

## Rollback criteria

Withdraw the candidate if authority or key custody is ambiguous, the local prototype can mutate state outside policy, replay/tamper cases are accepted, receipt or checkpoint verification is non-reproducible, clean-checkout results differ, or documentation implies remote/canonical security guarantees not supported by evidence. Restore the pre-candidate reviewed commit and preserve failed evidence.

## Unresolved blockers

- Explicit product and authority approval.
- `punchlist.md` completion.
- Tests and clean-checkout evidence.
- Durable append-only ledger and recovery implementation.
- Threat model, key/capability lifecycle, dependency/security review, provenance, artifacts, and rollback drill.

## Release log

- 2026-07-16: Reclassified the newly committed trust-core artifacts as a blocked local prototype candidate; no release or deployment approved.