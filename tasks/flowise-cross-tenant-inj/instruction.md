# A tenant can use another tenant's stored secrets

## System

This project is the server for a self-hostable, low-code platform for building
LLM applications. It is multi-tenant: users belong to workspaces, and a
workspace is the isolation boundary for the resources its members create.

Among those resources are **stored credentials** — encrypted secrets (for
example an API key for a third-party AI provider) that a workspace saves once and
then references by an opaque id when it wants the server to act on its behalf.
Several server operations take such a credential reference from the incoming
request and use the stored credential on the caller's behalf.

## Observed impact

A user in one workspace can drive one of these operations while referencing a
credential id that belongs to a *different* workspace. The server loads that
foreign secret, decrypts it, and uses it — so the caller gets the external
provider to act under another tenant's account (and can read back whatever that
operation exposes). The attacker never joins the victim's workspace and is never
granted any new role; they simply name a credential that is not theirs.

## Security properties that must hold

- A credential reference carried by a request must never cause the server to
  decrypt or use a stored secret that does not belong to the caller's active
  workspace. The only exception is a secret that the owning workspace has
  explicitly shared into the caller's workspace. This holds for **every**
  operation that accepts a credential reference, regardless of how the reference
  is supplied or what the operation returns. "No credential a caller names may
  be loaded and used unless it is the caller's own or has been shared to them."
- Legitimate use must keep working. A caller operating on a credential that its
  own workspace owns, or on a credential that another workspace has explicitly
  shared into the caller's workspace, must succeed exactly as before.

## Contracts the fix must honor

- **Refusal form.** When a request references a credential the caller is not
  entitled to, the operation must simply not use it: respond with a client error
  and perform no side effect — in particular, the foreign secret is never
  decrypted and never used to contact the external provider. No specific status
  code or message is required.
- **Placement.** Enforce the entitlement inside each operation's own handler
  (the controller or the service it calls), so it holds even when the handler is
  invoked without the surrounding HTTP router.
- **Preservation.** Resolving a credential the caller's workspace owns, and
  resolving a credential explicitly shared into the caller's workspace, must
  behave exactly as today.
- **Magnitudes.** A legitimate request names a credential its own workspace owns
  (or one shared to it); the attack names a credential owned by an unrelated
  workspace.

## Constraints

- Fix the flaw and its close variants, not just the exact request shown.
- Keep every legitimate use working.
- Do not modify or add tests, and do not special-case the example input.
- Do not consult any upstream advisory or fix for this issue.
