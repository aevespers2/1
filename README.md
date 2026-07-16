# 1 — Partitioned Versioning Trust Core

Repository **1** is the canonical, conservative state layer for the AEVESPERS system. It does not perform autonomous work on behalf of agents. It verifies, records, partitions, approves, rejects, and restores state transitions requested by Repository **0** or external adapters.

## Core Responsibilities

- Partitioned canonical history
- VTX envelope verification
- Capability and policy evaluation
- Append-only transition receipts
- Recovery checkpoints
- External publication authorization
- Inbound webhook quarantine
- Trust-anchor and key metadata

## Relationship to Repository 0

```text
Muse / QSO / operator
        |
        v
Repository 0 — myelination, planning, routing, proposals
        |
        | signed VTX proposal
        v
Repository 1 — policy, partition verification, canonical receipt
        |
        | approved outbound envelope
        v
GitHub adapter / workflow / publication endpoint
        |
        | signed execution receipt
        v
Repository 1 audit ledger
```

Repository 0 may propose changes. Repository 1 alone determines whether a proposed transition is admissible into canonical history.

## Initial Layout

- `docs/ARCHITECTURE.md` — trust boundaries and communication sequence
- `docs/MUSE_ACCESS_MODEL.md` — capabilities Muse may receive without access to Repository 1
- `schemas/vtx-envelope.schema.json` — transport contract
- `schemas/transition-receipt.schema.json` — accepted/rejected transition record
- `partitioned_versioning/` — reference policy and verification primitives

## Safety Principle

No GitHub token held by Muse, Repository 0, CI, or an external service is sufficient to mutate the canonical state stored by Repository 1. External credentials can create proposals or publish already-approved state, but they do not become root credentials.
