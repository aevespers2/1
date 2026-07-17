# Deployment Readiness Gates

The GitHub repositories are currently public. They are suitable for public schemas, reference code, tests, and architecture documentation only. They are not the authoritative secret-bearing trust core.

## Token Assignment Status

**Blocked until all mandatory gates are satisfied.**

## Mandatory Gates

- [ ] A private or offline authoritative Repository 1 store exists outside the public GitHub repository.
- [ ] Signing keys, token material, nonces, revocation state, and canonical audit records are absent from public repositories.
- [ ] Public Repository 1 is designated as a read-only reference mirror, not the root of trust.
- [ ] The authoritative policy digest is independently pinned by the operator.
- [ ] Muse has no direct network route or repository permission to the authoritative Repository 1 store.
- [ ] Credential gateway runs as a separate process and identity from Muse.
- [ ] Gateway logs have passed secret-redaction tests.
- [ ] Gateway accepts only structured operations, never arbitrary commands or URLs.
- [ ] VTX signature, expiry, nonce, digest, repository, operation, and branch checks are active.
- [ ] Append-only event storage and path anomaly auditing are active.
- [ ] Protected branches prevent direct Muse writes to `main`, canonical, and release branches.
- [ ] A disposable credential revocation drill has succeeded.
- [ ] A protected-branch denial test has succeeded.
- [ ] A Repository 1 access denial test has succeeded.
- [ ] An operator-approved grant manifest exists with an expiration of 24 hours or less.
- [ ] Emergency freeze and issuer-disable procedures have been tested.

## Public Mirror Rule

Public GitHub may contain:

- schemas;
- policy source code;
- tests;
- sanitized example events;
- documentation;
- reproducible visualization code.

Public GitHub may not contain:

- private signing keys;
- access tokens;
- authentication cookies;
- live nonces;
- confidential repository maps;
- unredacted audit events;
- private agent memory;
- canonical recovery materials;
- operator identity secrets.

## Readiness Decision

Token assignment is permitted only when `evaluate_token_grant` returns allowed **and** every mandatory deployment gate has recorded evidence. A passing unit test alone is insufficient.
