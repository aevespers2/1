# Developer Onboarding

## Read before changing code

Repository `1` is in `P0 — REVIEW / APPROVAL REQUIRED`. Existing code and schemas are candidate evidence, not an approved security product. Contributions should improve reproducibility, tests, documentation, or narrowly specified local behavior without introducing network access, credentials, remote mutation, autonomous approval, or unsupported security claims.

Start with:

1. [`taskchain.md`](../taskchain.md)
2. [`release.md`](../release.md)
3. [`changelog.md`](../changelog.md)
4. [`PROJECT_GUIDE.md`](PROJECT_GUIDE.md)
5. [`ARCHITECTURE.md`](ARCHITECTURE.md)
6. [`DESIGN_CONTRACTS.md`](DESIGN_CONTRACTS.md)

## Development posture

Until P0 and P2 are approved:

- treat all implementation as exploratory;
- do not merge route-specific behavior that resolves the Repository `0` conflict implicitly;
- do not add secrets, tokens, webhooks, listeners, or production key material;
- do not describe path scores as authorization or compromise proof;
- preserve rejected-case evidence and rollback paths;
- keep changes small enough to review and revert independently.

## Local setup

The repository currently contains Python reference material and JSON Schemas. Use an isolated environment and record exact tool versions in review evidence.

```bash
git clone https://github.com/aevespers2/1.git
cd 1

python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
```

Before installing project dependencies, inspect the repository for the authoritative dependency declaration and lockfile. Do not invent or silently update dependency versions as part of an unrelated documentation or policy change.

## Baseline inventory

From a clean checkout, record:

```bash
git status --short
git rev-parse HEAD
find . -maxdepth 3 -type f -print | sort
python --version
python -m pip --version
```

Then identify:

- schema files and their declared versions;
- policy modules and public entry points;
- existing tests and fixtures;
- documentation claims tied to behavior;
- generated files or local state that must remain untracked.

The commands above are evidence-gathering examples, not a claim that a complete test suite or packaging baseline currently exists.

## Working on contracts

For any schema or serialization change:

1. state the compatibility intent;
2. identify the owning repository and package;
3. add positive and negative fixtures;
4. define deterministic canonicalization behavior;
5. document digest impact;
6. test unknown versions and unexpected fields;
7. preserve prior receipts or define a verifiable migration record;
8. update architecture, release, and changelog documentation.

Do not modify the Repository `0` route contract without a recorded architecture decision shared by both repositories.

## Working on policy

Policy changes must be deny-by-default and should include:

- the capability or transition being added or removed;
- the exact source and destination partitions;
- required approvals;
- expiry and revocation behavior;
- positive fixtures;
- unknown, missing, stale, replay, and self-approval negative fixtures;
- stable reason-code expectations;
- rollback instructions.

Policy relaxation is a high-risk operation and requires explicit approval.

## Working on receipts or recovery

Do not call a store append-only merely because application code never calls an update method. Evidence should cover storage semantics, atomicity, corruption detection, ordering, restart behavior, and failure handling.

Recovery work should first target an isolated simulation:

```text
checkpoint + receipt history + policy versions
                    |
                    v
          isolated reconstruction
                    |
                    v
       digest and compatibility checks
                    |
                    v
             recovery report
```

A recovery simulation must not overwrite authoritative state.

## Tests expected for a local MVP

A future Builder-ready test plan should cover:

- schema and canonicalization behavior;
- unknown versions and fields;
- issuer and capability validation;
- expiry, nonce, and replay handling;
- payload and prior-state digest mismatch;
- allowed and denied partition edges;
- missing, stale, and self-issued approvals;
- accepted and rejected receipt construction;
- receipt persistence failure;
- chain corruption and prior-head mismatch;
- checkpoint tamper and incompatible recovery;
- deterministic ordering and reason codes;
- cross-repository route fixtures.

## Pull-request checklist

- [ ] Change is tied to a `taskchain.md` item or an explicitly documented review need.
- [ ] Implementation scope is not widened.
- [ ] No credential, listener, webhook, or remote mutation is introduced.
- [ ] Product and security claims are evidence-qualified.
- [ ] Positive and negative cases are documented.
- [ ] Exact commands and results are retained.
- [ ] `release.md` remains blocked unless every gate actually passes.
- [ ] `changelog.md` records the change and evidence state.
- [ ] Rollback is a simple revert or an explicitly tested migration.
- [ ] Route-model ambiguity is not resolved implicitly.

## Review vocabulary

Use these labels consistently:

- **observed** — the artifact exists at a named commit;
- **tested** — a named command produced retained results;
- **verified** — acceptance criteria and negative cases passed;
- **approved** — the responsible authority accepted the decision;
- **released** — immutable artifacts, provenance, checksums, rollback, and approval are recorded;
- **deployed** — an approved environment is running the released artifact.

Do not substitute one label for another.

## Stop and escalate

Return to architectural review rather than continuing when:

- the route model affects the proposed change;
- authority or key custody is unclear;
- a failure case would accept by default;
- receipt persistence cannot be made atomic;
- a test requires production credentials or network access;
- documentation and observed behavior disagree;
- the change would make an advisory signal authoritative;
- rollback would destroy or rewrite evidence.
