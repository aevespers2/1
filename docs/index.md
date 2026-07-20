# Repository 1 — Partitioned Versioning Trust Core

Repository `1` is a **candidate conservative trust and state layer** for the AEVESPERS and A.L.I.S.T.A.I.R.E. systems. Its proposed role is to evaluate bounded transition requests, preserve append-only decision evidence, issue or deny narrowly scoped capabilities, and support recovery without granting an agent, CI workflow, GitHub token, or external adapter authority to rewrite canonical history.

> **Current status:** `P0 — REVIEW / APPROVAL REQUIRED`. The repository contains candidate documentation, one observed state-path-event schema, and a small policy evaluator. It is not a released security boundary, deployed service, durable ledger, credential issuer, or verified recovery system.

## Documentation map

- [Project guide](PROJECT_GUIDE.md)
- [Architecture](ARCHITECTURE.md)
- [Canonical-state and capability authority](CAPABILITY_AUTHORITY.md)
- [Obstruction and gluing analysis](OBSTRUCTION_AND_GLUING.md)
- [ADR-0001: candidate canonical-state and capability authority](adr/0001-canonical-state-and-capability-authority.md)
- [Contract and state-machine design](DESIGN_CONTRACTS.md)
- [Developer onboarding](DEVELOPER_ONBOARDING.md)
- [Operations and recovery playbook](OPERATIONS.md)
- [Muse access model](MUSE_ACCESS_MODEL.md)
- [Task chain on GitHub](https://github.com/aevespers2/1/blob/main/taskchain.md)
- [Punch list on GitHub](https://github.com/aevespers2/1/blob/main/punchlist.md)
- [Release plan on GitHub](https://github.com/aevespers2/1/blob/main/release.md)
- [Changelog on GitHub](https://github.com/aevespers2/1/blob/main/changelog.md)

The GitHub links intentionally point to repository source because a Pages site built from `docs/` does not publish files from the repository root.

## Candidate system boundary

The inbound route is unresolved. Documentation records three interpretations without treating any as canonical:

| Candidate | Proposed path | Status |
|---|---|---|
| Contractual proposal partition | `0:working → 0:proposal → 1:quarantine` | requires shared fixtures and explicit ownership |
| Direct envelope route | `0:working → 1:quarantine` | requires Repository `0` documentation and tests to align |
| Local staging interpretation | `0:proposal` is non-authoritative Repository `0` staging; the cross-boundary contract begins at `1:quarantine` | lowest-coupling recommendation; explicit approval still required |

The local-staging interpretation is recommended for review because it preserves Repository `0`'s planning workflow while avoiding a duplicate Repository `1` partition and preventing local staging from gaining authority. It remains blocked until both repositories pin the same route definition and pass shared compatibility fixtures.

After a route is approved, the intended processing boundary is:

| Stage | Candidate responsibility | Failure behavior |
|---|---|---|
| Inbound quarantine | retain the bounded proposal without granting authority | reject malformed or unsupported input |
| Contract validation | validate version, shape, canonical form, issuer, target, nonce, expiry, and digests | issue a rejected receipt |
| Deny-by-default policy | evaluate explicit capability, partition, and approval rules | issue a rejected receipt |
| Staged transition | compute the proposed resulting state without mutating canonical state | discard on any later failure |
| Atomic persistence | durably commit the accepted receipt and resulting canonical state together | fail closed if either write cannot complete |
| Optional execution | issue one narrow, expiring authorization to an external adapter | retain the execution receipt or record failure |
| Recovery | verify an independent checkpoint and simulate restoration before approval | never overwrite canonical state implicitly |

This is a design target, not evidence that every component exists. Durable receipt storage, cryptographic verification, replay protection, checkpoint recovery, external adapters, authoritative key custody, and live capability issuance remain unimplemented or unverified.

## Portfolio authority separation

| Responsibility | Candidate owner | Must not collapse into |
|---|---|---|
| mission and constitutional governance | `ALISTAIRE-` | runtime execution or credential custody |
| autonomous planning and proposal preparation | Repository `0` | self-approval or canonical writes |
| canonical-state decision, capability issuance, revocation, and recovery | Repository `1` | silent governance changes or self-approved root authority |
| external execution | GitHub, publication, model, payment, or infrastructure adapter | canonical promotion merely because an operation succeeds |
| human review | QSO-STUDIO or AionUi | unsigned approval or capability minting |

## Proposed responsibilities

Repository `1` may eventually provide:

- versioned envelope and receipt validation;
- explicit partition-transition policy;
- replay, expiry, digest, and approval checks;
- accepted and rejected transition receipts;
- independently verifiable checkpoints and recovery simulation;
- narrowly scoped outbound authorization;
- reconciliation of external execution receipts.

It must not become:

- a general-purpose autonomous agent;
- a replacement for Git;
- a network-facing service in the local MVP;
- a holder of production credentials in public repository state;
- an authority that approves its own policy changes;
- a source of security claims unsupported by exact-head evidence.

## Lifecycle model

| State | Entry condition | Allowed next states |
|---|---|---|
| Quarantine | a bounded inbound proposal is retained | Rejected, Reviewed |
| Rejected | contract, authority, time, replay, digest, route, approval, policy, or storage checks fail | terminal receipt |
| Reviewed | deterministic checks pass but promotion is not yet durable | Rejected, Canonical |
| Canonical | accepted receipt and resulting state are committed atomically | Release, Recovery |
| Release | separately approved publication completes | terminal execution receipt |
| Recovery | a checkpoint is verified and restoration is simulated | Canonical only through a separately approved receipt-producing operation |

All movement is explicit and receipt-producing. A file does not become canonical merely because it exists in GitHub, appears in a pull request, or passes CI.

## Current release posture

No release or deployment is authorized. Before a first local candidate can be considered, the repository needs an approved charter, capability-authority boundary, and route model; deterministic contract and policy tests; durable atomic receipt-and-state behavior; a threat model; clean-checkout reproducibility; provenance; artifacts; checksums; rollback evidence; and explicit approval.

## Architectural clarification required

Formal approval is required for:

1. Repository `1` as canonical-state and capability authority;
2. the local-staging or alternative Repository `0` inbound-route interpretation;
3. contract/package ownership for envelopes, capabilities, approvals, receipts, revocations, and checkpoints;
4. the private/offline authority-store and key-custody model;
5. named human owners for policy, credentials, security, incident response, emergency stop, and recovery.

Until then, documentation may recommend and compare candidates, but implementation must not silently select or activate one.
