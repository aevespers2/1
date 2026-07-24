# Repository-Local Maintainer Conformance

## Status

`SYNTHETIC CONFORMANCE CANDIDATE — NO APPOINTMENT OR AUTHORITY EFFECT`

Repository `1` independently consumes the QSO Field repository-local maintainer fixture without importing the producer validator. The bounded purpose is to prove that two repositories derive the same review-eligibility and obstruction outcomes from one byte-identical synthetic corpus.

This document does not appoint a maintainer, accept a designation, bind permissions, approve a change packet, authorize merge or publication, operate a registry, or activate runtime authority.

## Immutable fixture identity

| Field | Value |
|---|---|
| fixture | `fixtures/repository-local-maintainer-v1.json` |
| fixture id | `qso.repository-local-maintainer-conformance` |
| fixture version | `1.0.0-synthetic` |
| profile id | `qso.repository-local-maintainer-boundary` |
| SHA-256 | `a920723c66e45acae7be988295f193e64f20d847d52564bfd295644190f65cd4` |
| authority effect | `none` |
| implementation relation | independent consumer; no producer-validator import |

Any byte, case, control, reason-code, disposition, or algorithm change creates a new conformance generation and requires a fresh cross-repository reproduction.

## Governing separation

```text
role class
!= designation
!= acceptance
!= current term
!= repository permission
!= change packet
!= independent review
!= approval
!= merge
!= release or publication
!= operational authority
```

`REVIEW_ELIGIBLE` means only that the synthetic case contains the minimum bounded preconditions for an independent reviewer to inspect a repository-local documentation packet. It is not `APPROVED`, `AUTHORIZED`, `MERGEABLE`, `RELEASABLE`, or `PUBLISHABLE`.

## Independently derived controls

The Repository `1` consumer derives reasons from these exact Boolean controls:

- current policy generation;
- separately identified designation and acceptance;
- current term;
- exact repository scope;
- complete change packet;
- approved low-risk surface;
- independent review;
- rollback or quarantine path;
- no self-appointment;
- no secret or credential access;
- no cross-repository authority claim;
- no protected-policy mutation;
- no self-certified restoration;
- reachability of every required consumer.

The consumer fails closed on unknown fields, non-Boolean controls, duplicate JSON keys, non-finite numbers, invalid UTF-8, duplicate or missing fixture identities, prohibited secret-bearing fields, reason drift, and disposition drift.

## Synthetic coverage

The sixteen cases cover:

1. one bounded documentation packet eligible for review;
2. missing designation;
3. missing acceptance;
4. expired or missing term;
5. self-appointment;
6. administrator permission represented as appointment;
7. secret or credential access;
8. cross-repository scope;
9. incomplete change packet;
10. missing rollback;
11. missing independent review;
12. emergency scope broadening;
13. protected-policy mutation;
14. self-certified restoration;
15. unreachable required consumer;
16. stale policy generation.

## Evidence path

```text
byte-identical fixture
→ strict independent parser
→ independently derived reason set
→ independently derived disposition
→ adversarial regression suite
→ exact-head workflow evidence
```

The workflow records the submitted commit, expected fixture digest, validator output, tests, source hashes, and explicit `authority_effect=none` assertions.

## Rollback and invalidation

Withdraw this conformance claim when:

- the shared fixture bytes no longer match the recorded digest;
- the producer profile, reason codes, or disposition semantics change;
- Repository `1` imports or delegates to the producer validator;
- exact-head validation is absent or unsuccessful;
- the documentation represents `REVIEW_ELIGIBLE` as appointment, permission, approval, merge, release, publication, or operational authority.

Rollback removes the reproduction claim and preserves the failed or superseded evidence. It does not change real repository permissions, appointments, releases, or operational state.

## Remaining blockers

Synthetic agreement does not establish an accepted maintainer policy. Neutral policy and fixture custody, designation and acceptance schemas, term and conflict rules, permission binding, allowed-surface ownership, independent-review thresholds, emergency-stop semantics, lifecycle propagation, rollback ownership, and explicit human architecture decisions remain required.
