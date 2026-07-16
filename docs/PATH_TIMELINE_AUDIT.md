# Visual Pathfinding and Timeline Audit

Repository 1 maintains a graph of every meaningful state transition across repositories, agents, partitions, branches, artifacts, and external endpoints.

## Purpose

The graph makes it possible to answer, at any point in time:

- Which agent initiated this change?
- Which repositories and partitions did it traverse?
- Which policy approved each hop?
- Which artifacts or commits were produced?
- Which path would normally have been expected?
- Where did the actual path diverge?
- Who edited, approved, rejected, or restored the state?

## Graph Model

### Nodes

- repository
- partition
- branch
- commit
- artifact
- agent or operator
- VTX envelope
- policy decision
- execution receipt
- recovery checkpoint
- external endpoint

### Edges

- proposed
- verified
- rejected
- promoted
- published
- received_from
- derived_from
- superseded_by
- restored_from
- approved_by
- executed_by
- crossed_repository_boundary

Each edge carries timestamps, digests, issuer identity, policy ID, nonce, decision, and supporting receipt references.

## Timeline State Editing

Canonical history is never silently edited. A requested correction creates a new transition that:

1. references the state being corrected;
2. explains the reason;
3. carries the replacement state digest;
4. identifies the approving authority;
5. preserves the prior state as an auditable predecessor;
6. optionally marks the prior state as superseded or invalidated.

The visual timeline can therefore show both the original path and the corrective branch without destroying evidence.

## Peculiarity Detection

A pathfinding monitor compares the observed path with expected policy and historical patterns. It can flag conditions such as:

- an agent touching a repository it has never used before;
- a transition skipping `reviewed` and moving directly from `working` to `release`;
- repeated movement between the same repositories;
- unusual branch prefixes;
- a sudden expansion in operation scope;
- multiple rejected attempts followed by a different route;
- a webhook proposal reaching a trusted partition without quarantine;
- state crossing more repository boundaries than normal;
- access at an unusual time or from a new execution identity;
- a digest changing between adjacent hops;
- a policy or trust-anchor change immediately before publication.

The monitor should issue a human-readable warning such as:

> This path is unusual: Muse moved from Repository 0 working state to an external publication branch without the normal Repository 1 reviewed-state checkpoint.

## Risk Score

The initial score may combine:

- policy deviation;
- route rarity;
- identity novelty;
- repository-boundary count;
- privilege sensitivity;
- failed-attempt history;
- digest discontinuity;
- time anomaly;
- proximity to trust-policy changes.

Scores do not automatically imply malicious behavior. They determine whether the transition proceeds, pauses for review, or is quarantined.

## Visual Views

1. **Repository map** — nodes for repositories and partitions, with animated transition edges.
2. **State timeline** — chronological commits, proposals, approvals, publications, and restorations.
3. **Agent path view** — the route taken by Muse or another QSO during a task.
4. **Diff-and-receipt view** — state changes aligned with signatures, decisions, and receipts.
5. **Anomaly overlay** — highlighted path segments with reasons and risk contribution.

## Storage

The source of truth is an append-only event stream plus deterministic graph projections. Visualizations are regenerated from signed events so that the display itself is not authoritative and cannot conceal historical evidence.
