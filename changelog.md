# Changelog

All notable product, architecture, implementation, release, and deployment changes are recorded here.

## Unreleased

### Product

- 2026-07-16 — Replaced the generic charter-or-retire hold with a concrete **Partitioned Versioning Trust Core** candidate review after new README, architecture, schema, policy, and audit-design artifacts were committed.
- 2026-07-16 — Classified the new direction as `P0 — REVIEW / APPROVAL REQUIRED`; further implementation is blocked until the product boundary, authority model, Repository `0` relationship, key/capability ownership, and local-only MVP are accepted, revised, or rejected.
- 2026-07-16 — Preserved the existing portfolio order: this approval decision does not supersede QSO-GENOMES acceptance or the QuantumStateObjects runnable-baseline objective.

### Architecture

- 2026-07-16 — Proposed Repository `1` as the conservative canonical-state and approval layer for proposals originating in Repository `0` or external adapters.
- 2026-07-16 — Proposed explicit `working`, `reviewed`, `canonical`, `release`, `quarantine`, `audit`, and `recovery` partitions with deny-by-default movement between them.
- 2026-07-16 — Required the first executable scope to remain local-only and credential-free; remote adapters, webhooks, publication, and production key custody require later independent approval.

### Added

- README and architecture/access/audit design documents.
- Candidate VTX envelope, transition-receipt, and state-path-event JSON Schemas.
- Candidate deny-by-default partition transition policy evaluator.

### Evidence state

- **Implemented and observed:** documentation, schemas, and a small Python policy evaluator exist in the repository.
- **Not verified:** schema conformance, cryptographic signatures, replay/expiry enforcement, append-only durable storage, receipt chaining, checkpoint recovery, complete tests, clean-checkout reproducibility, threat-model closure, key custody, and integration behavior.
- **Proposed only:** secure transport, GitHub/webhook adapters, external publication authorization, production deployment, and canonical-state guarantees.

### Release

- No release was promoted. A first candidate is limited to a reproducible local trust-core prototype with deterministic tests, security evidence, provenance, checksums, and rollback proof.

### Deployment

- No deployment surface, credential installation, webhook, network listener, or remote-write workflow is authorized.

## Entry format

- Date
- Category: Product / Architecture / Added / Changed / Fixed / Security / Release / Deployment
- Summary
- Evidence: issue, PR, commit, workflow, artifact, or deployment record
- Impact and migration notes where applicable