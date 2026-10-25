# Administrator-facing account records disclose other accounts' credentials

## System

New API is a self-hosted gateway for multiple AI model providers, with a web
console and an HTTP API. Accounts are ordinary users, administrators, or the
root account. An account may hold credential material that authenticates API
requests as that account or that its notifications use.

## Observed impact

An administrator who is not the root account can obtain another account's
credential material — including the root account's — from administrator
responses about accounts, and can then act as that account. The same
administrator can also change or revoke a peer's or a higher-ranked account's
sign-in credentials or protections.

## Security property that must hold

An account's credential material belongs to that account alone: it may be
returned only to that account, in any response an administrator receives about
accounts. Another account's sign-in credentials or sign-in protections may be
changed or revoked only by an administrator that outranks that account; the root
account outranks every account. An attempt on a peer or on a higher-ranked
account must be refused and must leave the target unchanged.

## Contracts the fix must honor

- A refusal is a failed response: the API's usual `success: false` envelope or an
  HTTP client error. A server error is not a refusal.
- An account still receives its own stored notification credentials, and a newly
  issued management token is still returned to the account that issued it.
  Authentication with a management token keeps working.
- Administrator-facing responses keep every non-credential account field exactly
  as today.
- Existing administrator actions on lower-ranked accounts keep working,
  including those that affect their sign-in protections or credentials, and the
  existing refusal of such actions against higher-ranked accounts keeps its
  meaning.
- Root may act on any account, including another root account.

## Constraints

- Fix the flaw and its close variants, not just one request.
- Keep every legitimate use working.
- Do not modify or add tests, and do not special-case any input.
- Do not consult any upstream advisory or fix for this issue.
