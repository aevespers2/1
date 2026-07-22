# Architecture Decision and Activation — Independent Conformance Consumer

## Status

`SYNTHETIC CONFORMANCE ONLY — NO DECISION OR ACTIVATION AUTHORITY`

Repository `1` independently consumes the immutable QSO Field architecture-decision and activation corpus. The consumer verifies that proposals, evidence, reviews, conflicts and recusals, dissent, decisions, conditional approvals, activation requests, activation records, consumer propagation, supersession, and rollback remain separate records.

This work does not accept an architecture proposal, approve a decision, satisfy approval conditions, activate implementation, appoint a reviewer, bind repository permissions, or authorize merge, release, publication, deployment, recovery, or canonical-state mutation.

## Immutable producer boundary

| Field | Value |
|---|---|
| Producer repository | `aevespers2/qso-field.github.io` |
| Producer commit | `dc05e4da47b1afee93feb0f9dabfb9eba79341a8` |
| Producer fixture | `fixtures/architecture-decision-activation-v1.json` |
| Producer Git blob | `9bcd29c33c10cc23769b8189587d5b8feda9286a` |
| Corpus schema | `qso.architecture-decision-activation.corpus.v1` |
| Data class | `synthetic_only_non_operational` |
| Cases | 15 |

The exact-head workflow downloads the fixture from the commit-pinned raw URL and verifies its Git blob identity before parsing it. SHA-256 is calculated and retained as run evidence. A changed producer commit or blob is a new fixture generation and requires a new consumer disposition.

## Independent implementation

Repository `1` uses its own standard-library parser and rule table. It does not import the QSO Field validator. The consumer rejects:

- duplicate JSON keys, non-finite numbers, or invalid UTF-8;
- missing or unknown top-level, case, fact, or expected-result fields;
- non-Boolean facts, duplicate case identifiers, reason drift, disposition drift, or incomplete corpus coverage;
- secret-, credential-, token-, private-key-, biometric-, or iris-bearing fields;
- review completion represented as approval;
- approval represented as activation;
- unbounded or unauthorized activation;
- activation scope broader than the approved scope;
- incomplete consumer registries or partial propagation represented as currentness;
- stale activation after supersession;
- rollback without a checkpoint or independently verified restored state.

## State separation

```text
proposal snapshot
!= evidence manifest
!= review completion
!= architecture decision
!= conditional approval
!= activation request
!= activation record
!= implementation authority
!= merge, release, publication, or operational authority
```

A passing synthetic case establishes only that the independent consumer derives the expected bounded disposition for the recorded fixture generation.

## Evidence and rollback

The workflow records the producer commit and blob, consumer exact head, tool version, fixture SHA-256, validator report, regression log, source hashes, and artifact manifest. It is read-only and has no write credentials.

Rollback is deletion or reversion of the four consumer files on the draft branch. Any conformance claim tied to the reverted consumer head must then be marked withdrawn or historical. Reverting files does not revoke or alter any external architecture decision because none is created here.

## Remaining blockers

- neutral decision-profile, reason-code, fixture, and canonical-byte custody;
- approved reviewer classes, quorum, independence, conflicts, recusals, and dissent handling;
- immutable decision identifiers, signatures, trusted time, condition-expiry semantics, and appeal rules;
- repository acceptance and bounded activation authority;
- complete consumer registration, supersession propagation, emergency suspension, and rollback ownership;
- durable decision storage and independent restored-state verification;
- explicit human architecture, merge, release, and publication decisions.
