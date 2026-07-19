# Punch List

This punch list validates the proposed local Partitioned Versioning Trust Core. Checked items require reproducible evidence tied to one immutable commit. Design text or a committed file alone is not completion evidence.

## P0 — Product and authority approval

- [ ] Approve or reject Repository `1` as the canonical state-transition approval and recovery layer.
- [ ] Approve the Repository `0` proposal-only boundary and prohibited authorities.
- [ ] Approve partition semantics and permitted transition classes.
- [ ] Define operator, Architect, Builder, CI, adapter, and recovery authority.
- [ ] Define key/capability ownership, issuance, rotation, revocation, and loss recovery.
- [ ] Approve the local-only MVP, release identity, non-goals, and retirement/rollback option.

## P1 — Candidate inventory and contract review

- [ ] Record the immutable candidate commit and exact artifact inventory.
- [ ] Reconcile README, architecture, task chain, changelog, release plan, and deployment status.
- [ ] Validate each JSON Schema against Draft 2020-12 and deterministic valid/invalid fixtures.
- [ ] Define canonical serialization and payload-digest rules.
- [ ] Define expiry, nonce, replay, approval, signature, and receipt-chain semantics.
- [ ] Define fail-closed error taxonomy and compatibility/versioning policy.

## P2 — Local implementation and tests

- [ ] Test every deny-by-default policy rejection and allowed transition.
- [ ] Implement deterministic envelope and receipt verification.
- [ ] Implement replay/expiry and payload-tamper rejection.
- [ ] Implement append-only local receipt chaining with corruption detection.
- [ ] Implement checkpoint creation, verification, and recovery simulation.
- [ ] Add positive, negative, tamper, replay, stale, approval, recovery, and property-based fixtures where practical.
- [ ] Run targeted and complete tests from a clean checkout.

## P3 — Security, provenance, and release evidence

- [ ] Threat model trust roots, key compromise, confused deputy, forged receipts, rollback attacks, replay, dependency compromise, and adapter compromise.
- [ ] Verify no secret, network listener, webhook, GitHub remote write, or production key is included.
- [ ] Record dependency/runtime/tool versions and produce an SBOM or explicit dependency manifest.
- [ ] Generate test, security, provenance, and reproducibility reports.
- [ ] Generate source/package artifacts and SHA-256 checksum manifest.
- [ ] Perform and record a rollback/recovery drill.
- [ ] Record explicit release approval.

## Pre-Review Tasks — current candidate

- [x] Repair the failed Security Readiness workflow by installing a pinned pytest version.
- [x] Check out and assert the exact submitted PR head instead of the synthetic merge ref.
- [x] Disable persisted checkout credentials and pin the checkout and Python setup actions by immutable commit SHA.
- [x] Retain deterministic exact-head test evidence with Python, pytest, commands, JUnit output, logs, and SHA-256 manifest on the previously submitted head.
- [x] Reject non-boolean `passed` values instead of coercing truthy strings.
- [x] Reject duplicate evidence keys, non-finite JSON values, unknown gate names, and non-string evidence metadata.
- [x] Restrict branch grants to normalized `muse/proposal/` descendants and reject broad, protected, malformed, mixed-case, traversal, and wildcard prefixes.
- [ ] Confirm the complete Security Readiness workflow succeeds at the final submitted head after these parsing and scope repairs.
- [ ] Retain and record the final exact-head artifact digest.
- [ ] Reconcile Repository `0`'s documented `working -> proposal -> quarantine` path with this candidate's direct `working -> quarantine` route before approval.
- [ ] Keep token issuance and deployment blocked until the private authority store, external gateway, branch protections, redaction evidence, and revocation drill are independently verified.

## Evidence log

Record date, task, source commit, commands, environment, result (`PASS`, `FAIL`, or `UNKNOWN`), artifacts/hashes, limitations, reviewer, and follow-up work.
