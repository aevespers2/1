# Architecture: Repository 0 ↔ Repository 1

## Roles

### Repository 0 — Myelination Layer

Repository 0 coordinates cognition and work. It may:

- receive operator intent;
- route tasks to Muse or another QSO;
- assemble candidate patches and artifacts;
- calculate content digests;
- request GitHub operations;
- maintain noncanonical working memory;
- submit signed VTX proposals.

Repository 0 may not:

- alter Repository 1 policy;
- write canonical receipts;
- rotate trust anchors;
- approve its own high-risk transition;
- treat GitHub state as canonical.

### Repository 1 — Partitioned Versioning Layer

Repository 1 preserves identity through time. It may:

- validate VTX envelopes;
- evaluate capabilities and partition policy;
- enforce replay and expiry checks;
- record accepted and rejected transitions;
- issue approved outbound envelopes;
- reconcile GitHub execution receipts;
- restore canonical checkpoints.

## Partitions

A transition is scoped to exactly one primary partition:

- `working` — untrusted or agent-generated candidate state;
- `reviewed` — human- or policy-reviewed candidate state;
- `canonical` — accepted authoritative state;
- `release` — publication-ready immutable state;
- `quarantine` — inbound external events and unverified imports;
- `audit` — append-only receipts and policy decisions;
- `recovery` — independently verified checkpoints.

Movement between partitions is explicit. A file does not become canonical merely because it exists in GitHub or passed CI.

## Proposal Sequence

1. Muse receives a task through Repository 0.
2. Muse produces a patch, artifact, or requested operation inside `working` scope.
3. Repository 0 computes the payload digest and constructs a VTX proposal.
4. Repository 1 verifies issuer capability, repository state, partition transition, expiry, nonce, payload digest, and required approvals.
5. Repository 1 writes an accepted or rejected transition receipt.
6. If external publication is approved, Repository 1 emits a narrowly scoped outbound authorization.
7. The GitHub adapter performs only the approved operation.
8. The adapter returns an execution receipt containing GitHub object identifiers and resulting digests.
9. Repository 1 reconciles that receipt against the authorization and records the result.

## Threat Containment

Compromise of Muse exposes only Muse's granted proposal or publication scope. Compromise of a GitHub token exposes only the repositories and actions attached to that token. Neither compromise grants authority to rewrite Repository 1's canonical ledger, policies, trust anchors, or recovery checkpoints.

## High-Risk Operations

The following should require operator approval or threshold authorization:

- trust-anchor modification;
- policy relaxation;
- deletion or history rewrite;
- canonical-to-release promotion;
- secret or credential changes;
- workflow permission expansion;
- publishing executable artifacts;
- recovery checkpoint replacement.
