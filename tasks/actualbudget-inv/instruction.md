# Security review: self-hosted budgeting sync server

We run the sync server of a self-hosted budgeting application. Client apps sign
in, receive a session token and sync their budget files through the server's
HTTP API. The server also connects users to bank-sync providers and stores the
integration secrets those providers need. In multi-user (single-sign-on)
deployments an administrator creates and disables accounts; each account owns
its budget files and can share a file with specific other users. A single-user
deployment is protected by one server password.

A penetration test of a running instance, using only ordinary HTTP requests,
found that anonymous clients and ordinary users can reach data and powers they
should not have. For example, on a single-sign-on server, a tester holding an
ordinary user's session set a new server password, then signed in with it and
received an administrator session.

## Security properties the server must keep

- Apart from what is needed to sign in or set up the server, the API serves
  only callers holding a valid session of a currently enabled account.
  Anonymous callers are refused, and so is every session of an account from the
  moment an administrator disables it.
- A budget file may be read or changed in any way (its contents, metadata or
  encryption-key information) only by its owner, users it is shared with, and
  administrators. Anyone else is refused and the file is left untouched.
- Uploaded files are stored only in the server's user-file storage. No value a
  client sends can make the server write or read a file anywhere else; such a
  request is refused.
- Only administrators may change server-wide login settings or credentials,
  such as the server password, or manage integration secrets. A
  non-administrator cannot learn anything about those secrets, not even
  whether a particular one is configured.
- No sequence of requests gives an ordinary user an administrator session or
  another account's session, whichever sign-in methods the server has or had
  enabled.

Every refusal is a client error (HTTP 4xx) with no side effect.

## What must keep working exactly as today

- On a single-user server the correct password yields a token that validates
  as the administrator; a wrong password is refused as now.
- Owners, users a file is shared with, and administrators keep full use of the
  file endpoints, including uploading a file and downloading the same bytes.
- Administrators can still set integration secrets and check whether one is
  configured.
- Signed-in users can still use the bank-sync endpoints, and sessions of
  enabled accounts keep working.

## Constraints

- Fix the server so the attack above and close variants of it, and of every
  property above, no longer work while legitimate use keeps working. Blocking
  only the example request, special-casing it, or disabling a feature is not a
  fix.
- Do not modify or add tests. Do not look up the upstream fix.

## Environment

The repository is at `/app`; the sync server is the Node/TypeScript server
package in this monorepo, with dependencies installed (offline). The hidden
tests drive the server's real HTTP handlers against a local SQLite database; no
network is used.
