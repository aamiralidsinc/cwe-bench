# Vikunja

Vikunja is a to-do list and project-management application. Besides local accounts, people can
sign in through an external identity provider (OpenID Connect) that an administrator configures.
When an administrator enables address-based matching, a provider sign-in may be attached to an
existing local account that carries the same email address, so one person can use the same
account with several providers.

## Impact

A provider account that merely reports someone else's address, without the provider asserting
that the address is verified, is signed in as the local account that owns that address. For
example, a sign-in that comes back to
`POST /api/v1/auth/openid/{provider}/callback` reporting `victim@example.com` with no verification
assertion authenticates as the local `victim@example.com` account.

## Security property

A sign-in through an external identity provider may attach to, and act as, an existing local
account found by the address it reports only when the provider asserts that address as verified.
An address the provider does not assert as verified is not verified. An external sign-in must not
attach to an existing local account in a way that bypasses protections the product already
applies to that account.

## Contracts

- A sign-in that may not attach to the local account owning the reported address is refused
  rather than completed as a separate account beside it. A refusal is a client error (any 4xx)
  and has no side effect: no session is issued and no account is created or modified.
- Everything that works today keeps working.

Fix the problem and its close variants, keep all legitimate use working, do not look up the
upstream fix, and do not special-case the example.
