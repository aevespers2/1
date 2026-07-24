# Independent QSO Ecosystem Conformance

Repository `1` independently consumes the draft QSO ecosystem manifest contract from `aevespers2/QSO-FABRIC` PR #21 at exact producer head `738cf25aec9b2bae0b71c50374585bab36934ef3`.

## Bounded purpose

This consumer verifies the exact producer manifest and schema bytes, checks the closed manifest contract through a separately implemented validator, and reproduces the producer's positive and hostile outcomes without importing `tools/validate_ecosystem.py`.

```mermaid
flowchart LR
    P[QSO-FABRIC PR 21 exact head] --> M[manifest bytes]
    P --> S[schema bytes]
    M --> I[byte identity and source tuple]
    S --> I
    I --> V[Repository 1 independent validator]
    V --> T[21 positive and hostile regressions]
    T --> E[retained exact-head evidence]
    E --> R[review input only]
```

## Preserved separations

```text
byte identity
!= semantic conformance
!= ecosystem admission
!= capability grant
!= execution authority
!= architecture approval
!= merge, release, publication, or deployment authority
```

The consumer checks strict UTF-8, duplicate keys, non-finite numbers, closed field sets, non-Boolean integer ambiguity, safe evidence paths, unique capability and interface names, bounded default-allow execution, interface types, canonical review-component identity, human override, audit logging, schema/validator field convergence, and L1 artifact presence.

## Immutable source tuple

`contracts/qso-ecosystem-source-tuple-v1.json` binds:

- producer repository, pull request, and exact head;
- exact manifest and schema paths;
- Git blob, SHA-256, and byte-size identities;
- L1 README and conformance-workflow blob identities;
- the independent consumer implementation path; and
- explicit denial of ecosystem-admission or operational authority.

## Skill-tree mapping

Applied FYSA-120 capabilities:

- **CAT-012** — technical documentation and developer-facing conformance guidance;
- **CAT-017** — source identity, derivation, and citation-grade provenance;
- **CAT-031** — independent verified-software implementation and hostile regression testing;
- **CAT-044** — adversarial evaluation of parser and contract boundaries;
- **CAT-052** — cryptographic source identity;
- **CAT-054** — cross-repository contract and supply-chain integrity;
- **CAT-059** — exact-head attestation and retained evidence transport.

Proposed refinement: **validator/schema differential conformance** as a reusable subdivision, covering independent semantic implementations, strict JSON type ambiguity, source-tuple binding, and reason/disposition convergence.

## Remaining obstruction

Synthetic agreement at one immutable generation does not approve QSO-ECOSYSTEM-001. Neutral contract custody, compatibility and migration rules, signed evidence, trusted time, consumer registration, rollback ownership, accessibility/security/licensing review, and resulting-default-branch verification remain unresolved.
