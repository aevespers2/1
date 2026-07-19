# Changelog

All notable product, architecture, implementation, release, and deployment changes are recorded here.

## Unreleased

### Product

- 2026-07-16 — Replaced the generic charter-or-retire hold with a concrete **Partitioned Versioning Trust Core** candidate review after new README, architecture, schema, policy, and audit-design artifacts were committed.
- 2026-07-16 — Classified the new direction as `P0 — REVIEW / APPROVAL REQUIRED`; further implementation is blocked until the product boundary, authority model, Repository `0` relationship, key/capability ownership, and local-only MVP are accepted, revised, or rejected.
- 2026-07-16 — Preserved the existing portfolio order: this approval decision does not supersede QSO-GENOMES acceptance or the QuantumStateObjects runnable-baseline objective.
- 2026-07-16 — Classified draft PR #1 as early candidate implementation rather than an active Builder task because it was opened before P0 approval and P1/P2 contract decomposition.
- 2026-07-16 — Retained that classification after the draft added token-assignment safeguards and advanced to a new head; no remote authority, token issuance, or release eligibility was approved.

### Architecture

- 2026-07-16 — Proposed Repository `1` as the conservative canonical-state and approval layer for proposals originating in Repository `0` or external adapters.
- 2026-07-16 — Proposed explicit `working`, `reviewed`, `canonical`, `release`, `quarantine`, `audit`, and `recovery` partitions with deny-by-default movement between them.
- 2026-07-16 — Required the first executable scope to remain local-only and credential-free; remote adapters, webhooks, publication, and production key custody require later independent approval.
- 2026-07-16 — Recorded a route-contract conflict: Repository `0` draft PR #6 specifies `0:working -> 0:proposal -> 1:quarantine`, while Repository `1` draft PR #1 tests a direct `0:working -> 1:quarantine` transition and defines no normal `proposal` edge.
- 2026-07-16 — Required the Architect to select one canonical transition model or explicitly classify `0:proposal` as non-authoritative local staging before either draft can merge.
- 2026-07-16 — Classified path-audit scores and thresholds as advisory observability signals, not canonical security proof or authorization policy.
- 2026-07-19 — Added diagrams and design guidance that preserve both candidate inbound routes without choosing one, and documented the decision consequences for shared fixtures, schema ownership, and staging semantics.

### Added

- README and architecture/access/audit design documents.
- Candidate VTX envelope, transition-receipt, and state-path-event JSON Schemas.
- Candidate deny-by-default partition transition policy evaluator.
- 2026-07-16 — Draft PR #1 proposes path-audit logic, token-assignment preflight safeguards, deployment-readiness documentation, and deterministic tests.
- 2026-07-19 — Added a GitHub Pages-ready landing page and Pages metadata.
- 2026-07-19 — Added a project guide covering purpose, evidence classes, trust zones, repository relationships, lifecycle stages, non-goals, and stop conditions.
- 2026-07-19 — Added a contract and state-machine design covering validation order, stable reason-code candidates, capability and receipt properties, checkpoint design, path-audit boundaries, compatibility, and fixture requirements.
- 2026-07-19 — Added developer onboarding and a local operations/recovery playbook with evidence, incident, rollback, and remote-integration gates.

### Documentation

- 2026-07-19 — Expanded the root README with evidence-qualified status, architecture navigation, local MVP boundaries, the unresolved route decision, and explicit release posture.
- 2026-07-19 — Kept all new documentation within the existing local-only candidate scope; no implementation, credential, network, deployment, or canonical-authority claim was added.

### Evidence state

- **Implemented and observed on the default branch:** documentation, schemas, and a small Python policy evaluator exist in the repository.
- **Implemented only on draft PR #1:** path-audit model, weighted findings, dispositions, token-assignment preflight safeguards, and tests; these are unmerged and not accepted.
- **Not verified:** schema conformance, cryptographic signatures, replay/expiry enforcement, append-only durable storage, receipt chaining, checkpoint recovery, complete tests, clean-checkout reproducibility, threat-model closure, calibrated path scoring, key custody, and integration behavior.
- **Proposed only:** secure transport, GitHub/webhook adapters, external publication authorization, production deployment, and canonical-state guarantees.
- 2026-07-16 — Draft PR #1 current head is `e1b20b4cd59c5ec2aa0b2c92024868ffa6fd500f`; no GitHub Actions workflow run is attached to that submitted state.
- 2026-07-19 — The documentation branch adds design and operating requirements only; it does not change the evidence classification of any runtime capability or release gate.

### Release

- No release was promoted. A first candidate is limited to a reproducible local trust-core prototype with deterministic tests, security evidence, provenance, checksums, and rollback proof.
- 2026-07-16 — Draft PR #1 remains excluded from release consideration until authority approval, route reconciliation, interface ownership, exact-head CI, negative fixtures, threat-model review, and recovery evidence are complete.
- 2026-07-19 — Documentation completeness improved, but the release remains blocked on every existing product, route, verification, security, recovery, provenance, artifact, and approval requirement.

### Deployment

- No deployment surface, credential installation, token issuance, webhook, network listener, or remote-write workflow is authorized.

## Entry format

- Date
- Category: Product / Architecture / Added / Changed / Fixed / Security / Release / Deployment
- Summary
- Evidence: issue, PR, commit, workflow, artifact, or deployment record
- Impact and migration notes where applicable
