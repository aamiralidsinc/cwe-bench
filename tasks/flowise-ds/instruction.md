# Cross-tenant use of stored credentials

## System

This project is the server for a self-hostable, low-code platform for building
LLM applications. It is multi-tenant: users belong to workspaces, and a
workspace is the isolation boundary for the resources its members create.
Workspaces save stored credentials — encrypted secrets that they can reference
when they want the server to act on their behalf with an external provider.

## Observed impact

A user in one workspace can make the server act on behalf of an unrelated
workspace: the server resolves a stored credential that the caller's workspace
does not own, decrypts it, and uses it to contact the external provider. The
caller never joins the victim's workspace and is never granted any role there.

## Security property that must hold

A stored credential may be loaded, decrypted, or used to act with an external
provider only if it belongs to the caller's active workspace, or the owning
workspace has explicitly shared it into that workspace for this purpose. This
applies to every request that can reach a stored credential. If a request's
caller is authenticated but has no active workspace, no stored credential may
be loaded or used.

## Contracts the fix must honor

- **Refusal form.** When a request would reach a credential the caller is not
  entitled to — or the caller has no active workspace — the operation must
  simply not use it: respond with a client error and perform no side effect. The
  foreign secret is never decrypted and never used to contact the external
  provider. No specific status code or message is required.
- **Preservation.** A caller acting on a credential its own workspace owns, or
  on a credential another workspace has explicitly shared into the caller's
  workspace for this purpose, must succeed exactly as before. Sharing is an
  existing mechanism with a type: a share recorded for a different kind of
  resource is not a credential share. A fix that only checks direct ownership
  and forgets shared credentials would break legitimate use.
- **Sessions.** The property applies both to interactive sessions and to
  callers authenticated by an API key.

The description above is an illustration, not the full set of ways the property
can be violated.

## Constraints

- Fix the flaw and its close variants, not just a single path.
- Keep every legitimate use working.
- Do not modify or add tests, and do not special-case any particular input.
- Do not consult any upstream advisory or fix for this issue.
