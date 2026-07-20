# ADR-0001: Candidate Canonical-State and Capability Authority

- **Status:** Proposed — architectural approval required
- **Date:** 2026-07-20
- **Decision scope:** Repository `1` portfolio role, authority boundary, and documentation contract

## Context

A.L.I.S.T.A.I.R.E. requires autonomous engineering to progress quickly without allowing the planning system, CI, a model, a GitHub credential, or an external adapter to become the sole authority over canonical state. Repository `0` is already documented as the candidate planning and proposal-orchestration plane. The portfolio governance charter names Repository `1`, or an approved successor, as the candidate independent canonical-state and capability authority.

Repository `1` contains early architecture documents, one observed state-path-event schema, and a small deny-by-default policy evaluator. Its broader trust-core behavior, capability issuance, durable ledger, checkpoint recovery, route compatibility, key custody, and production authority are not established.

## Decision

Repository `1` is accepted **for documentation and architectural review only** as the candidate service responsible for:

- evaluating versioned, bounded state-transition and capability requests;
- enforcing deny-by-default policy, expiry, nonce, replay, expected-state, and approval requirements;
- producing accepted and rejected receipts;
- preserving append-only decision evidence;
- atomically coupling accepted receipts with resulting canonical state;
- issuing narrow, expiring authorizations to separately approved adapters;
- reconciling execution receipts;
- supporting independently verified checkpoints, freeze, recovery, and rollback.

Repository `1` is not authorized by this ADR to:

- hold production credentials or root keys;
- run a network service;
- write remotely;
- merge, release, deploy, pay, rotate secrets, or migrate canonical state;
- approve changes to its own constitutional policy without independent human approval;
- treat path-audit scores, successful CI, GitHub state, transport delivery, or UI actions as authority;
- grant itself or Repository `0` broader capabilities.

## Required separation

- `ALISTAIRE-` owns accepted mission, governance, repository roles, and constitutional policy.
- Repository `0` plans, generates, verifies candidate work, and submits bounded proposals.
- Repository `1` evaluates authority and records canonical decisions.
- External adapters execute only one approved operation and return receipts.
- Human or threshold approval remains mandatory for critical capabilities.

## Route decision retained as open

This ADR does not select among:

1. `0:working → 0:proposal → 1:quarantine`;
2. `0:working → 1:quarantine`;
3. `0:proposal` as non-authoritative local staging before a cross-repository envelope originates.

One route and package-owner decision must be approved and covered by shared fixtures before implementation promotion.

## Acceptance conditions

Formal adoption requires:

- approval of Repository `1` as the portfolio capability authority or selection of a successor;
- an immutable governance-policy reference from `ALISTAIRE-`;
- one canonical Repository `0` route;
- named owners for policy, schemas, identity, capability issuance, revocation, credentials, security, incidents, emergency stop, and recovery;
- versioned identity, proposal, capability, approval, receipt, revocation, checkpoint, and reason-code contracts;
- deterministic pairwise and triple-overlap fixtures;
- a private/offline authority and key-custody design;
- exact-head validation, provenance, retained evidence, and rollback guidance;
- explicit human approval of the immutable candidate commit.

## Consequences

### Positive

- separates fast autonomous engineering from canonical authority;
- makes privilege explicit, narrow, expiring, auditable, and revocable;
- provides one place to reconcile external effects with canonical state;
- creates a portfolio-wide freeze and recovery anchor;
- exposes cross-repository contract gaps before runtime integration.

### Costs and risks

- introduces a high-value security boundary that must be independently reviewed;
- requires deterministic shared contracts across several repositories;
- may become a bottleneck if policy, fixture, and review processes are not efficient;
- creates operational complexity around time, replay, key custody, revocation, recovery, and evidence retention;
- risks false confidence if documentation is mistaken for implemented security.

## Alternatives considered

### Repository `0` owns planning and authority

Rejected as the default architecture because the proposer could become its own sole authorizer, increasing confused-deputy and self-expansion risk.

### GitHub is canonical authority

Rejected because branch state, CI success, and platform authorization do not encode the portfolio's complete governance, capability, consent, recovery, and evidence semantics.

### Bridge owns generic authority

Not selected. Bridge may transport and validate evidence, but transport should not silently become canonical authorization. Its specialist evidence/publication responsibilities must remain distinct unless separately revised.

### Human-only manual authority without Repository `1`

Viable as an interim safety mode. It limits automation and does not provide the deterministic capability, receipt, replay, and recovery contracts needed for later bounded autonomous operation.

## Rollback

If Repository `1` is rejected or cannot meet the acceptance conditions:

1. retain Repository `0` in proposal-only mode;
2. disable live capability issuance and remote execution;
3. use explicit human review for consequential actions;
4. preserve all candidate documentation and evidence as historical design records;
5. select and charter a successor authority service;
6. migrate only through an approved, checksummed, reversible contract and provenance plan.
