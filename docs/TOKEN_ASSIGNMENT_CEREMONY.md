# Muse Token Assignment Ceremony

Token assignment is prohibited until every gate below passes. The ceremony produces an auditable authorization record but never records the token value.

## Preferred Credential Order

1. **No token:** operator- or gateway-mediated proposals.
2. **GitHub App installation token:** short lived and generated only when required.
3. **Fine-grained personal access token:** temporary fallback with explicit expiry.
4. Classic personal access tokens are prohibited.

## Hard Boundaries

- Repository `aevespers2/1` is excluded from the credential's repository selection.
- Muse cannot administer repositories, workflows, environments, members, or secrets.
- Muse cannot force-push, delete repositories, change visibility, alter branch protection, or publish releases.
- Muse writes only to branches beginning with `muse/proposal/`.
- The credential is held by a gateway process, not placed in Muse's prompt, memory, workspace, repository, logs, or generated artifacts.
- Every GitHub action must match both the GitHub credential scope and a live VTX capability.
- Absence, expiry, replay, or mismatch causes denial.

## Pre-Issuance Gates

1. Repository allowlist contains only the intended non-trust-core repositories.
2. Permission list has been reviewed against the exact automation task.
3. Branch prefix enforcement is operational.
4. VTX capability verification is operational.
5. Append-only audit recording is operational.
6. Token redaction tests pass for logs and errors.
7. Credential storage is outside all repositories and agent memory.
8. Revocation has been exercised successfully in a test credential.
9. Expiration is configured for no more than 24 hours initially.
10. An operator has approved the grant manifest digest.

## Initial Muse Grant

The first grant should be limited to:

- repository: `aevespers2/0` only;
- metadata: read;
- contents: read and write;
- pull requests: read and write;
- branches: `muse/proposal/*` only;
- duration: eight hours or less;
- no Repository 1 access;
- no Actions, secrets, administration, deletion, release, or environment permissions.

GitHub's repository-level token permissions do not independently enforce a branch prefix. Therefore, branch restrictions must also be enforced by the gateway, VTX policy, and protected branches. A token that technically permits broader content writes remains unusable outside the VTX-approved branch scope.

## Assignment Sequence

1. Generate a token-grant manifest without any secret value.
2. Run `evaluate_token_grant` in Repository 1.
3. Record the approved manifest digest in the audit partition.
4. Create the credential with the approved repository and permissions.
5. Insert it into the gateway's ephemeral secret store.
6. Run a read-only identity and repository check.
7. Create one disposable `muse/proposal/token-smoke-*` branch.
8. Attempt and confirm denial of a protected-branch operation.
9. Revoke the test credential and confirm subsequent requests fail.
10. Only then create a fresh operational credential under the same approved manifest.

## Runtime Enforcement

For every operation, the gateway must verify:

- token grant identifier;
- VTX envelope signature;
- envelope expiry;
- nonce uniqueness;
- repository allowlist;
- operation allowlist;
- branch prefix;
- payload digest;
- rate and volume limits;
- absence of a freeze or revocation flag.

The gateway returns a signed receipt to Repository 1 for both accepted and rejected operations.

## Immediate Revocation Conditions

- Repository 1 appears in a requested target.
- Muse requests an unapproved permission or branch.
- Any token fragment appears in logs, output, memory, or a repository.
- Digest continuity fails.
- VTX replay is detected.
- Path auditing returns `quarantine`.
- More than three policy denials occur in one task.
- The gateway cannot reach Repository 1's current policy state.

## Recovery

Revoke the credential first, disable the Muse issuer capability second, freeze Repository 0 publication third, and reconcile all actions since the last known-good receipt. Credential rotation alone is not sufficient; the path graph and GitHub state must be compared against Repository 1's canonical ledger.
