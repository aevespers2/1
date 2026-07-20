# Changelog

All notable product, architecture, implementation, release, and deployment changes are recorded here.

## Unreleased

### Product

- 2026-07-16 — Replaced the generic charter-or-retire hold with a concrete **Partitioned Versioning Trust Core** candidate review after new README, architecture, schema, policy, and audit-design artifacts were committed.
- 2026-07-16 — Classified the new direction as `P0 — REVIEW / APPROVAL REQUIRED`; further implementation is blocked until the product boundary, authority model, Repository `0` relationship, key/capability ownership, and local-only MVP are accepted, revised, or rejected.
- 2026-07-16 — Preserved the existing portfolio order: this approval decision does not supersede QSO-GENOMES acceptance or the QuantumStateObjects runnable-baseline objective.
- 2026-07-16 — Classified draft PR #1 as early candidate implementation rather than an active Builder task because it was opened before P0 approval and P1/P2 contract decomposition.
- 2026-07-20 — Defined Repository `1` more precisely as the candidate independently reviewable canonical-state, capability, revocation, receipt, and recovery authority, without activating that authority.

### Architecture

- 2026-07-16 — Proposed Repository `1` as the conservative canonical-state and approval layer for proposals originating in Repository `0` or external adapters.
- 2026-07-16 — Proposed explicit `working`, `reviewed`, `canonical`, `release`, `quarantine`, `audit`, and `recovery` partitions with deny-by-default movement between them.
- 2026-07-16 — Required the first executable scope to remain local-only and credential-free; remote adapters, webhooks, publication, and production key custody require later independent approval.
- 2026-07-16 — Recorded a route-contract conflict: Repository `0` draft PR #6 specifies `0:working → 0:proposal → 1:quarantine`, while Repository `1` draft PR #1 tests a direct `0:working → 1:quarantine` transition and defines no normal `proposal` edge.
- 2026-07-16 — Classified path-audit scores and thresholds as advisory observability signals, not canonical security proof or authorization policy.
- 2026-07-19 — Added diagrams and design guidance that preserve all inbound-route candidates without silently choosing one.
- 2026-07-20 — Added a capability-authority design covering constitutional inputs, authority classes, separation of duties, capability envelopes, issuance, revocation, emergency stop, recovery, and cross-repository contracts.
- 2026-07-20 — Added an obstruction and gluing ledger covering route, authority, canonical-state, contract ownership, identity, freeze, atomicity, clock/replay, public/private topology, UI approval, path-audit, and evidence-correction obstructions.
- 2026-07-20 — Recorded the lowest-coupling route repair candidate: treat `0:proposal` as non-authoritative local Repository `0` staging while the cross-boundary contract begins at `1:quarantine`; explicit approval and shared fixtures remain required.
- 2026-07-20 — Added ADR-0001 to capture the candidate canonical-state and capability-authority role, required separation of duties, retained route decision, adoption conditions, alternatives, consequences, and rollback path.

### Added

- README and architecture/access/audit design documents.
- Candidate state-path-event JSON Schema and deny-by-default partition-transition policy evaluator.
- 2026-07-16 — Draft PR #1 proposes path-audit logic, token-assignment preflight safeguards, deployment-readiness documentation, and deterministic tests.
- 2026-07-19 — Added a GitHub Pages-ready landing page and Pages metadata.
- 2026-07-19 — Added a project guide covering purpose, evidence classes, trust zones, repository relationships, lifecycle stages, non-goals, and stop conditions.
- 2026-07-19 — Added contract/state-machine design, developer onboarding, and a local operations/recovery playbook.
- 2026-07-20 — Added `docs/CAPABILITY_AUTHORITY.md`, `docs/OBSTRUCTION_AND_GLUING.md`, and `docs/adr/0001-canonical-state-and-capability-authority.md`.
- 2026-07-20 — Expanded `punchlist.md` with authority, route, gluing, pairwise/triple-overlap fixtures, atomicity, private-store, freeze, recovery, identity/revocation, and evidence-correction work.

### Documentation

- 2026-07-19 — Expanded the root README with evidence-qualified status, architecture navigation, local MVP boundaries, the unresolved route decision, and explicit release posture.
- 2026-07-19 — Kept all new documentation within the existing local-only candidate scope; no implementation, credential, network, deployment, or canonical-authority claim was added.
- 2026-07-20 — Reconciled README, Pages, task chain, punch list, release plan, and changelog with the capability-authority and gluing analysis.
- 2026-07-20 — Corrected the artifact inventory: only `schemas/state-path-event.schema.json` is observed on the default branch; envelope, receipt, capability, approval, revocation, checkpoint, and execution-receipt schemas remain planned or draft-only unless separately pinned.
- 2026-07-20 — Expanded offline documentation validation to require the governance coordination files, architecture, capability-authority guide, obstruction ledger, ADR, onboarding, operations, and access-model surface.

### Evidence state

- **Implemented and observed on the default branch:** documentation, one state-path-event schema, and a small Python policy evaluator exist.
- **Implemented only on draft PR #1:** path-audit model, weighted findings, dispositions, token-assignment preflight safeguards, deployment-readiness documentation, and tests; these remain unmerged and unapproved.
- **Not verified:** accepted contract schemas, cryptographic signatures, replay/expiry enforcement, append-only durable storage, atomic receipt/state persistence, receipt chaining, checkpoint recovery, complete local-MVP tests, threat-model closure, calibrated path scoring, private key custody, and integration behavior.
- **Proposed only:** secure transport, live capability issuance, GitHub/webhook adapters, external publication authorization, production deployment, and canonical-state guarantees.
- 2026-07-20 — PR #1 exact head `0813308061e27e8289ea8f15af7d5ccdc84b4abf` passed Security Readiness run `29667702838`; artifact digest `sha256:2c7ff8100c706051763de1aff69c6f8d1652c418445c1d8894499335fcf67f94`. Passing checks do not resolve product, authority, route, private-store, key-custody, release, or deployment gates.
- 2026-07-20 — PR #2 Documentation run `29773845205` passed at head `4efc3e29280d85ad6173b71beaf2eec546f77e87`; later governance, ADR, punch-list, and validation edits require fresh exact-head validation.

### Release

- No release was promoted. A first candidate remains limited to a reproducible local trust-core prototype with deterministic tests, security evidence, provenance, checksums, and rollback proof.
- Draft PR #1 remains excluded from release consideration until product/authority approval, route reconciliation, contract ownership, private-store/key-custody review, complete local-MVP evidence, recovery, and explicit approval are complete.
- Documentation completeness improved, but the release remains blocked on product, route, authority, contract, durable-state, security, recovery, provenance, artifact, and approval requirements.

### Deployment

- No deployment surface, credential installation, token issuance, webhook, network listener, private gateway, canonical-state service, or remote-write workflow is authorized.

## Entry format

- Date
- Category: Product / Architecture / Added / Changed / Fixed / Security / Release / Deployment
- Summary
- Evidence: issue, PR, commit, workflow, artifact, or deployment record
- Impact and migration notes where applicable
