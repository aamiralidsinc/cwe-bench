# Fairness audit: actualbudget-inv

Each hidden test is listed below with the sentence of the new `instruction.md` (or the standard expert
knowledge) that makes it fair. Every security assertion accepts any 4xx status. That matches the
instruction's contract: "Every refusal is a client error (HTTP 4xx) with no side effect."

## Security tests (tests/security/)

| Test | What it asserts | Justified by | Risk |
|---|---|---|---|
| 01-missing-auth::rejects an unauthenticated SimpleFIN status request | POST /simplefin/status with no token returns a 4xx | "Apart from what is needed to sign in or set up the server, the API serves only callers holding a valid session ... Anonymous callers are refused." The system description names bank-sync providers as part of the server. | low |
| 01-missing-auth::rejects an unauthenticated Pluggy.ai status request | Same, for /pluggyai/status | Same sentence | low |
| 01-missing-auth::rejects an unauthenticated SimpleFIN accounts request | POST /simplefin/accounts with no token returns a 4xx | Same sentence. It covers every route, not only status. | low |
| 01-missing-auth::rejects an unauthenticated Pluggy.ai accounts request | Same, for /pluggyai/accounts | Same sentence | low |
| 02-path-traversal::does not write outside the user-files directory | An upload whose file id contains `../` writes nothing outside userFiles, and the status is not 200 | "Uploaded files are stored only in the server's user-file storage. No value a client sends can make the server write or read a file anywhere else; such a request is refused." Treating headers as client values is standard expert knowledge (CWE-22). | low |
| 03-file-authorization::blocks reading another user's file metadata | get-user-file-info on another user's file returns a 4xx | "A budget file may be read or changed in any way (its contents, metadata or encryption-key information) only by its owner, users it is shared with, and administrators. Anyone else is refused" | low |
| 03-file-authorization::blocks renaming another user's file | update-user-filename on another user's file returns a 4xx | Same sentence (changing metadata) | low |
| 03-file-authorization::blocks reading another user's encryption key info | user-get-key on another user's file returns a 4xx | Same sentence (encryption-key information) | low |
| 03-file-authorization::blocks overwriting another user's existing file | upload-user-file over another user's existing file id returns a 4xx | Same sentence (changing contents), plus "the file is left untouched" | low |
| 03-file-authorization::blocks resetting another user's file | reset-user-file on another user's file returns a 4xx | Same sentence (changing contents or sync state) | low |
| 03-file-authorization::blocks downloading another user's file | The victim uploads a file and gets 200; the attacker's download-user-file returns a 4xx | Same sentence (reading contents). The victim's own upload is covered by "Owners ... keep full use of the file endpoints". | low |
| 04-privilege-escalation::cannot obtain an admin session by resetting the password and logging in | On a server migrated from password to OpenID, a BASIC user calls change-password and then logs in with `loginMethod: password`. If a token is issued, it must not validate as ADMIN. | Given almost word for word by the example: "on a single-sign-on server, a tester holding an ordinary user's session set a new server password, then signed in with it and received an administrator session". Also covered by "Only administrators may change ... the server password" and "No sequence of requests gives an ordinary user an administrator session ..., whichever sign-in methods the server has or had enabled." | low |
| 05-secret-enumeration::does not reveal to a non-admin that a secret is configured | In OpenID mode, a BASIC user's GET /secret/:name returns a 4xx (the vulnerable code returns 204 or 404) | "Only administrators may ... manage integration secrets. A non-administrator cannot learn anything about those secrets, not even whether a particular one is configured." Together with the refusal contract, this requires a 4xx and not a uniform 404. | low |
| 06-session-expiration::rejects the disabled user on /account/validate | A disabled user's unexpired token returns a 4xx on validate | "... the API serves only callers holding a valid session of a currently enabled account ... so is every session of an account from the moment an administrator disables it." | low |
| 06-session-expiration::rejects the disabled user on a sync data endpoint | The same token returns a 4xx on list-user-files | Same sentence ("the API serves only ...") | low |

## Functional tests (tests/functional/)

| Test | What it asserts | Justified by | Risk |
|---|---|---|---|
| 01-authentication::issues a token for the correct password and validates it | On a single-user password server, login returns 200 with a token; validate returns 200 with validated=true and permission ADMIN | "On a single-user server the correct password yields a token that validates as the administrator" | low |
| 01-authentication::refuses an incorrect password | A wrong password gets exactly 400 and no token | "a wrong password is refused as now" (the exact status is today's behaviour) | low |
| 02-file-access::lets the owner read their file info | Owner gets 200 with the right fileId | "Owners ... keep full use of the file endpoints" (exactly as today) | low |
| 02-file-access::lets a granted collaborator read the file info | A shared user gets 200 | "users a file is shared with ... keep full use of the file endpoints" | low |
| 02-file-access::lets a server admin read the file info | A non-owner ADMIN gets 200 | "... and administrators keep full use of the file endpoints". The access rule also lists administrators. | low |
| 02-file-access::lets the owner rename their own file | Owner rename gets 200 with status ok | "Owners ... keep full use of the file endpoints" | low |
| 03-upload-download::uploads a new file and downloads the same content | Uploading with a UUID file id gets 200 and ok; downloading returns identical bytes | "including uploading a file and downloading the same bytes". A UUID is the normal id that clients send today. | low |
| 04-secrets-admin::reports a configured secret as present for an admin | Admin GET /secret/:name returns 204 | "Administrators can still ... check whether one is configured" (exactly as today) | low |
| 04-secrets-admin::reports an unset secret as absent for an admin | Admin GET of an unset secret returns 404 | Same sentence (today's statuses are kept) | low |
| 05-session-valid::validates an enabled user | An enabled BASIC user's token validates with 200 and validated=true | "sessions of enabled accounts keep working" | low |
| 05-session-valid::lets an enabled user list their files | The same token on list-user-files gets 200 and ok | Same sentence | low |
| 06-bank-sync-authed::returns SimpleFIN status for an authenticated user | An authenticated user's /simplefin/status returns 200, ok, configured=false | "Signed-in users can still use the bank-sync endpoints" (exactly as today) | low |
| 06-bank-sync-authed::returns Pluggy.ai status for an authenticated user | Same, for Pluggy.ai | Same sentence | low |

## Residual risks

None is rated medium or high. Two points are borderline:

- **Privilege escalation (04).** This test is fair because the single trigger example describes the attack
  at the product level. Without that example the invariants alone would cover it ("Only administrators may
  change ... the server password"; "whichever sign-in methods the server has or had enabled"), but with a
  medium risk. The example uses the instruction's single allowed trigger.
- **Bank-sync /accounts (01).** These tests depend on the general rule that the API serves only callers with
  a session. That is the strongest standard expectation for an authenticated API, so the risk is low.

## Details removed from the old instruction

- The finding count ("several independent findings") and the six findings as separate bullets, one per flaw.
- The token transport: the `X-Actual-Token` header, or the token in the request body.
- "The endpoints that report and return bank-connection data respond ... with no session token", which named
  the unauthenticated endpoints and said that every other data endpoint already refuses anonymous callers.
- The file-authorization root cause ("checks only that the caller is logged in, not that the caller owns the
  target file") and the list of affected actions: read metadata, read key info, rename, overwrite, reset.
- The path-traversal location and mechanism: the upload endpoint, a caller-supplied identifier header, and
  directory-traversal sequences.
- The privilege-escalation mechanism: an endpoint "that never checks the caller's privileges", the "forced
  password method", and the "built-in administrator account". The scenario "first set up with password login
  and later switched to single-sign-on" is reduced to "whichever sign-in methods the server has or had
  enabled".
- The secret-enumeration root cause: the existence-probe endpoint lacks the privilege check that the matching
  write endpoint applies.
- The session root cause: validation checks only existence and timeout and never rechecks whether the account
  is enabled.
- The per-flaw "What to fix" list, which mapped one preservation clause to each flaw. It is now one neutral
  list of what must keep working.
- The package path `packages/sync-server`. The new text says only "the Node/TypeScript server package in this
  monorepo".
- New text added: the refusal contract ("client error (HTTP 4xx) with no side effect"), "Do not modify or add
  tests" and "Do not look up the upstream fix", from the brief's standard constraints block. The old
  instruction had no such block.
