# A key for one thing can open something else

copyparty is a single-binary file server. An operator can publish a folder with
per-file keys and per-folder keys. A link that carries a per-file key lets a visitor
download that one file; a link that carries a per-folder key lets a visitor read that
folder.

## Observed impact

A visitor who has been given a link to one file — the link carries that file's key —
opens the file's page and receives a key for the folder that contains it, without ever
being given access to that folder. With that folder key the visitor can then read the
whole folder, including files they were never given links for. We reproduced this with
an ordinary request: one file's key in, the folder's contents out.

## Security property

A key is worth exactly the access it was issued for, and nothing more. It may only be
handed to a caller who already has the access it represents, and using it must never
reach data outside what it was issued for, as the server's configuration defines it.

## Contracts the fix must honor

- **Refusal form.** A request that cannot be served under this rule is answered with a
  client error and has no effect.
- **Preservation.** Everything that works today keeps working exactly as today.
- **No crashes.** A refusal is a normal client error, not a crash, a hang, or a server
  error.

The example above is one instance, not the full set of ways the property can be
violated.

## Constraints

- Fix the flaw and its close variants, not just the request shown.
- Keep every legitimate use working.
- Do not special-case the example input.
- Do not consult any upstream advisory or fix for this issue.
- There is no network access.
