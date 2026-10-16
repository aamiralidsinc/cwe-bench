# Security review: self-hosted budgeting sync server

You are hardening the HTTP sync server of a self-hosted, multi-user budgeting
application. The server exposes a JSON/binary API over HTTP: clients obtain a
session token by logging in and then send it in an `X-Actual-Token` header (or
in the request body) on subsequent calls. In multi-user deployments an
administrator provisions accounts and each account owns its own budget files;
some accounts are also granted shared access to specific files. A separate
single-user mode authenticates with just a server password.

A penetration test against a running instance produced several independent
findings. All of them are reachable by sending ordinary HTTP requests to the
running server as a client would; none require local access.

Observed problems:

- The endpoints that report and return bank-connection data respond normally to
  requests that carry no session token at all. Every other data endpoint
  refuses anonymous callers, but these ones answer anyone on the network.

- A logged-in, ordinary user can act on budget files that belong to other
  users. By supplying another account's file identifier, the tester was able to
  read a file's metadata and encryption-key information, rename it, overwrite
  it, and reset it. The server checks only that the caller is logged in, not
  that the caller owns the target file or was granted access to it.

- The upload endpoint derives the on-disk storage location from a caller-
  supplied identifier header. By placing directory-traversal sequences in that
  header, the tester caused the server to write a file outside the directory
  reserved for user data.

- On an instance that was first set up with password login and later switched
  to single-sign-on, an ordinary user was able to gain administrator rights.
  Using only a normal session, the tester overwrote the server password through
  an endpoint that never checks the caller's privileges, then logged in with the
  forced password method and received a token for the built-in administrator
  account.

- A non-administrator can determine whether specific integration secrets are
  configured on the server. The endpoint that answers an existence probe does
  not apply the privilege check that the matching write endpoint applies, so any
  logged-in user can enumerate which integrations are set up.

- After an administrator disables an account, tokens that account obtained
  earlier keep working. Session validation confirms only that the token exists
  and has not timed out; it never rechecks whether the account is still enabled,
  so a disabled user retains full access until the token is otherwise removed.

## What to fix

Close every one of the problems above while keeping the server fully functional
for legitimate use: correct password login must still issue working tokens;
owners, explicitly granted collaborators and administrators must still be able
to use the file endpoints and upload/download real files; administrators must
still be able to manage and query integration secrets; authenticated users must
still reach the bank-connection endpoints; and still-enabled users must keep
their sessions. Blocking only the exact probes above, or disabling a feature
outright, is not an acceptable fix.

## Environment

The code is a Node/TypeScript package under
`packages/sync-server` in the repository at `/app`. Its dependencies are already
installed (offline). The hidden tests drive the server's real HTTP handlers
against a local SQLite database; no network is used.
