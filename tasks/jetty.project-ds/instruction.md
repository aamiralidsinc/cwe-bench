# A wrong secret can be accepted as a user's login

## System

This project is a Java web server and servlet container. Deployments protect
parts of a site with user authentication: a client presents a credential, the
server compares it with the secret configured for that account, and only then
does the request run as that user.

## Observed impact

An account's real secret contains a character that the server does not
represent faithfully (for example, a euro sign, `€`). An attacker who does not
know that secret presents a different value that differs only in that
character (for example, `?` in its place). The server treats the two as the
same value, establishes the victim's identity, and serves the protected page.

## Security property

No value may establish an account's identity unless it is exactly that
account's secret. In particular, two distinct values must never both
authenticate the same account, and no value other than the exact secret may
authenticate — however the value is presented, and however the account's
secret is held.

## Contracts the fix must honor

- **Refusal form.** A rejected login is an ordinary client error (any 4xx
  response) with no authenticated identity and no side effect. No particular
  status code or message is required, and a refusal must not surface as a
  server error.
- **Preservation.** Every legitimate login keeps working: the exact secret
  configured for an account must still authenticate. A secret containing
  characters that the server does not represent faithfully must remain usable
  when the client and server agree on how those characters are represented. A
  secret already held in a one-way form must be used exactly as held and must
  not be recomputed. Ordinary text secrets and existing deployments must
  behave exactly as they do today.
- **Magnitudes.** A legitimate request presents an account's real secret; the
  attack presents a value that differs by one character the server does not
  represent faithfully.

The example above is an illustration, not the full set of ways these
properties can be violated.

## Constraints

- Fix the flaw and its close variants, not just the exact request shown.
- Keep every legitimate use working.
- Do not special-case the example input.
- Do not consult any upstream advisory or fix for this issue.

There is no network access.
