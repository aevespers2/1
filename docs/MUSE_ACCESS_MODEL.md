# Muse Access Model

Muse does not require direct access to Repository 1 in order to automate useful work.

## Recommended Initial Mode: No Token

Before issuing any GitHub token, Muse can operate through a local or operator-mediated proposal queue:

1. Muse prepares a patch bundle and manifest.
2. Repository 0 records the request and computes its digest.
3. The operator or a separate gateway submits the proposal to Repository 1.
4. Repository 1 accepts or rejects the transition.
5. Only approved material is published externally.

This mode proves the architecture without exposing a credential.

## Later Mode: Proposal-Only Credential

When automation is ready, Muse may receive a credential limited to one or more noncritical repositories. The credential should permit only the minimum required actions, such as:

- read repository metadata;
- create a branch;
- create or update files on a designated proposal branch;
- open pull requests;
- read checks and comments.

Muse should not receive:

- access to Repository 1;
- organization administration;
- repository administration;
- secret management;
- workflow permission changes;
- branch-protection modification;
- deletion or force-push privileges;
- release signing authority;
- trust-anchor or policy authority.

## Capability Envelope

Every Muse operation should also be constrained by a VTX capability containing:

- Muse identity;
- permitted repository;
- permitted operation set;
- permitted branch prefix;
- maximum lifetime;
- payload digest;
- nonce;
- policy identifier;
- optional human-approval requirement.

A GitHub token proves that GitHub will accept an API call. A VTX capability proves that the AEVESPERS trust system intended that exact call.

## Kill Switches

- Revoke the GitHub credential.
- Disable Muse's VTX issuer identity.
- Reject all proposals under the affected policy ID.
- Rotate gateway credentials.
- Freeze promotion from `working` to `canonical`.

These controls are independent so that one failed control does not become total compromise.
