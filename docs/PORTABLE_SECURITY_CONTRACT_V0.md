# Portable Security Contract v0

## Status

`PROPOSED — DOCUMENTATION ONLY`

This document defines the shared candidate contract between Repository `0` and Repository `1` for portable first-install security, device recovery, and evidence-backed remediation. It does not activate device-management authority, credentials, remote administration, remediation commands, or canonical-state mutation.

Repository `1` is the candidate independent quarantine, policy, capability, revocation, checkpoint, receipt-reconciliation, and recovery authority for this contract. Repository `0` remains the observation, proposal, bounded-execution, and evidence producer.

## Canonical route

```text
Repository 0 local working state
  → non-authoritative local proposal
  → signed/versioned proposal envelope
  → Repository 1 quarantine
  → validation and authority decision
  → optional narrow capability
  → Repository 0 bounded execution
  → execution/resulting-state receipt
  → Repository 1 reconciliation
```

`0:proposal` is local staging only. It is not canonical state, approval, or authority. Repository `1` begins its responsibility when a proposal envelope is admitted to quarantine.

## Ownership split

| Concern | Repository `0` | Repository `1` |
|---|---|---|
| Device observation | Collects supported read-only observations | Validates identity, provenance, and policy relevance |
| Local proposal | Builds a reviewable proposed change | Does not trust proposal status as approval |
| Baseline | Consumes a pinned baseline | Owns accepted baseline identity and lifecycle |
| Capability | Requests a bounded capability | Issues, rejects, expires, and revokes capability |
| Execution | Performs only separately authorized bounded action | Never treats execution success as automatic acceptance |
| Evidence | Produces observation and execution evidence | Reconciles evidence into canonical decisions/checkpoints |
| Recovery | Executes approved local rollback/recovery | Owns accepted checkpoint, freeze, revocation, and recovery state |

## Required identifiers

Every envelope must carry these identifiers or be rejected:

| Field | Meaning |
|---|---|
| `contract_version` | Exact portable-security contract version |
| `message_type` | `inventory`, `proposal`, `decision`, `capability`, `receipt`, `revocation`, `checkpoint`, or `correction` |
| `message_id` | Globally unique immutable identifier |
| `correlation_id` | Links one bootstrap or remediation transaction |
| `device_id` | Stable device identity scoped to the approved ownership domain |
| `environment_id` | OS installation or runtime-environment identity distinct from hardware |
| `owner_scope` | Human or organizational authorization scope |
| `platform_profile_id` | Exact platform-control profile and version |
| `baseline_id` | Exact accepted baseline and version |
| `policy_id` | Exact policy set used for the decision |
| `producer_id` | Identity of the component producing the message |
| `created_at` | UTC timestamp from the producer clock |
| `expires_at` | Expiration for time-bounded messages |
| `nonce` | Replay-resistant unique value |
| `expected_head` | Immutable source/configuration identity expected by the receiver |
| `content_digest` | Digest of canonicalized message content |
| `evidence_refs` | Hash-bound references to supporting artifacts |

## Device identity model

`device_id` must not rely only on hostname, IP address, Bluetooth name, user-visible label, or mutable serial aliases. The candidate identity record separates:

- physical hardware identity where legally and technically available;
- operating-system installation identity;
- user-assigned friendly label;
- ownership and authorization scope;
- enrollment epoch;
- lost, stolen, retired, replaced, quarantined, or active status;
- privacy-preserving public reference versus private authority-store record.

A replaced operating-system installation on the same hardware receives a new `environment_id`. A replacement device receives a new `device_id`. Prior identities remain revocable and auditable.

## Result semantics

Observations use one of four states:

- `PASS` — observed state matches the applicable accepted baseline;
- `FAIL` — observed state conflicts with the applicable accepted baseline;
- `UNKNOWN` — control is unsupported, inaccessible, incomplete, ambiguous, or not measured;
- `NOT_APPLICABLE` — policy explicitly excludes the control for this platform/profile.

`UNKNOWN` must never be collapsed into `PASS`. Summary status must preserve per-control completion and evidence.

## Proposal admission

A proposal includes:

- exact pre-state claims and evidence;
- requested operation and affected resources;
- expected post-state;
- command or adapter method identifier, not an unconstrained shell string where avoidable;
- permitted paths, packages, services, interfaces, accounts, certificates, profiles, routes, or settings;
- network destinations if network access is required;
- maximum duration, retries, cost, and change count;
- risk classification;
- rollback plan and checkpoint prerequisite;
- required human approval class;
- privacy and retention classification;
- unresolved `UNKNOWN` controls and stop conditions.

Repository `1` rejects proposals that are ambiguous, overbroad, stale, wrong-device, unsupported-version, missing evidence, or unable to roll back safely.

## Capability envelope

A capability is narrow, expiring, non-transferable, and bound to:

- one `device_id` and `environment_id`;
- one proposal digest;
- one policy and baseline version;
- one operation set;
- one executor identity;
- one validity interval;
- explicit resource and network limits;
- evidence and receipt requirements;
- revocation and emergency-stop authority;
- expected source/configuration head.

A capability cannot mint, widen, renew, or delegate itself. Success of one operation does not authorize another.

## Receipt and reconciliation

Repository `0` returns an immutable receipt containing:

- capability identifier and proposal digest;
- exact start and finish timestamps;
- command/adapter version and source head;
- observed pre-state and resulting state;
- changed resources;
- exit/result codes;
- stdout/stderr or structured output references with redaction rules;
- artifact digests;
- rollback status;
- partial-failure and interruption details;
- remaining `UNKNOWN` or failed controls.

Repository `1` independently validates the receipt. A successful process exit is not enough to accept the resulting state. Canonical acceptance requires identity, digest, policy, baseline, expected-head, evidence, and post-state checks.

## Revocation and emergency stop

Revocation messages identify:

- capability or device scope;
- reason and authority;
- effective time;
- required local stop action;
- evidence-preservation requirements;
- downstream cache/session invalidation;
- recovery or re-enrollment conditions.

Emergency stop fails closed. Repository `0` stops starting new consequential work and preserves evidence. Repository `1` stops new capability issuance. There is no automatic unlock.

## Privacy and retention

Device inventories may expose account names, package lists, network identifiers, certificates, profiles, routes, paired devices, and security posture. Each field must have:

- classification;
- collection purpose;
- minimum necessary representation;
- redaction rule;
- retention period;
- export/deletion policy;
- public/private storage boundary.

GitHub Pages, public artifacts, logs, and issue text must not contain live secrets, private keys, recovery keys, raw tokens, sensitive network identifiers, or unredacted personal device inventories.

## Canonicalization and integrity

The contract owner must define one canonical serialization and digest procedure. Until then:

- producers record the serialization format and implementation version;
- receivers reject unsupported canonicalization versions;
- signatures or MACs cover identifiers, payload, evidence references, and expiry;
- detached artifacts are hash-bound to the message;
- corrections create new records linked to the superseded record rather than silently rewriting history.

## Required compatibility fixtures

The shared fixture suite must include:

1. valid inventory and proposal;
2. malformed schema;
3. unsupported contract version;
4. stale timestamp and expired proposal;
5. duplicate nonce and replayed message;
6. wrong `device_id` or `environment_id`;
7. wrong baseline or policy identity;
8. expected-head mismatch;
9. missing or mismatched evidence digest;
10. overbroad operation/resource scope;
11. capability expiry before execution;
12. capability revocation during execution;
13. partial execution with successful rollback;
14. partial execution with failed rollback and freeze;
15. successful command but unacceptable resulting state;
16. `UNKNOWN` control preserved end to end;
17. lost-device revocation and replacement-device enrollment;
18. correction and supersession without history loss.

Fixtures must be deterministic, secret-free, pinned to immutable commits, and run in both repositories.

## Versioning

- `0.x` versions are pre-acceptance and may change incompatibly.
- A contract version is not accepted until both repositories pass the same fixture bundle against immutable heads.
- Minor compatible additions must remain optional for older readers.
- Breaking field, state, canonicalization, or authority changes require a new major version and migration plan.
- Unsupported versions fail closed.

## Open decisions

The following remain unresolved:

- canonical contract/package owner;
- private authority-store and key-custody topology;
- device identity derivation and privacy-preserving public references;
- per-platform baseline owners;
- signature and canonicalization standards;
- human approval classes and named owners;
- retention periods and deletion authority;
- offline bootstrap and recovery quorum;
- whether mobile platforms use advisory-only profiles or managed-device integrations.

## Acceptance criteria

This contract may advance from `PROPOSED` only when:

- Repository `0` and Repository `1` documentation agree on route and ownership;
- schema examples and deterministic fixtures exist;
- both repositories reject all negative fixtures;
- privacy and key-custody reviews pass;
- lost/replaced-device and emergency-stop tabletop exercises are recorded;
- rollback and correction behavior are verified;
- the human Architect approves the exact contract version and immutable repository heads.
