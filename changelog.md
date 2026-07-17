# Changelog

All notable product, architecture, implementation, release, and deployment changes are recorded here.

## Unreleased

### Product

- 2026-07-16 — Replaced the generic charter-or-retire hold with a concrete **Partitioned Versioning Trust Core** candidate review after new README, architecture, schema, policy, and audit-design artifacts were committed.
- 2026-07-16 — Classified the new direction as `P0 — REVIEW / APPROVAL REQUIRED`; further implementation is blocked until the product boundary, authority model, Repository `0` relationship, key/capability ownership, and local-only MVP are accepted, revised, or rejected.
- 2026-07-16 — Preserved the existing portfolio order: this approval decision does not supersede QSO-GENOMES acceptance or the QuantumStateObjects runnable-baseline objective.
- 2026-07-16 — Classified draft PR #1 as early candidate implementation rather than an active Builder task because it was opened before P0 approval and P1/P2 contract decomposition.

### Architecture

- 2026-07-16 — Proposed Repository `1` as the conservative canonical-state and approval layer for proposals originating in Repository `0` or external adapters.
- 2026-07-16 — Proposed explicit `working`, `reviewed`, `canonical`, `release`, `quarantine`, `audit`, and `recovery` partitions with deny-by-default movement between them.
- 2026-07-16 — Required the first executable scope to remain local-only and credential-free; remote adapters, webhooks, publication, and production key custody require later independent approval.
- 2026-07-16 — Recorded a route-contract conflict: Repository `0` draft PR #6 specifies `0:working -> 0:proposal -> 1:quarantine`, while Repository `1` draft PR #1 tests a direct `0:working -> 1:quarantine` transition and defines no normal `proposal` edge.
- 2026-07-16 — Required the Architect to select one canonical transition model or explicitly classify `0:proposal` as non-authoritative local staging before either draft can merge.
- 2026-07-16 — Classified path-audit scores and thresholds as advisory observability signals, not canonical security proof or authorization policy.

### Added

- README and architecture/access/audit design documents.
- Candidate VTX envelope, transition-receipt, and state-path-event JSON Schemas.
- Candidate deny-by-default partition transition policy evaluator.
- 2026-07-16 — Draft PR #1 proposes `partitioned_versioning/path_audit.py` and two deterministic tests covering an expected route and a direct-release/digest-discontinuity anomaly.

### Evidence state

- **Implemented and observed on the default branch:** documentation, schemas, and a small Python policy evaluator exist in the repository.
- **Implemented only on draft PR #1:** path-audit model, weighted findings, dispositions, and two tests; these are unmerged and not accepted.
- **Not verified:** schema conformance, cryptographic signatures, replay/expiry enforcement, append-only durable storage, receipt chaining, checkpoint recovery, complete tests, clean-checkout reproducibility, threat-model closure, calibrated path scoring, key custody, and integration behavior.
- **Proposed only:** secure transport, GitHub/webhook adapters, external publication authorization, production deployment, and canonical-state guarantees.
- 2026-07-16 — No GitHub Actions workflow run was found for draft PR #1 head `04eafb37ad13228f3846a1cb4ba86c73e01c5b5a`.

### Release

- No release was promoted. A first candidate is limited to a reproducible local trust-core prototype with deterministic tests, security evidence, provenance, checksums, and rollback proof.
- 2026-07-16 — Draft PR #1 remains excluded from release consideration until authority approval, route reconciliation, interface ownership, clean-checkout CI, negative fixtures, and threat-model review are complete.

### Deployment

- No deployment surface, credential installation, webhook, network listener, or remote-write workflow is authorized.

## Entry format

- Date
- Category: Product / Architecture / Added / Changed / Fixed / Security / Release / Deployment
- Summary
- Evidence: issue, PR, commit, workflow, artifact, or deployment record
- Impact and migration notes where applicable