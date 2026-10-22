# Table storage is not scoped to the caller

This project is a multi-tenant object store. Its gateway also serves table
storage: the resources it manages, the data inside them, and the access rules
recorded with them. Operators configure identities, each identity belongs to an
account, and an account is the isolation boundary for what its identities
create.

## Observed impact

On a deployment with identities configured, an authenticated caller in its own
account, holding only ordinary permissions, can read, change and delete table
storage owned by another account. The caller never joins the other account and
is granted no role there.

## Security property that must hold

A caller may act on table storage, or on anything recorded within it, only if
the caller's account owns it, the caller has been granted the permission the
operation needs, or an access rule recorded on the resource allows the caller.
This holds for every operation on every entry point that serves remote callers,
and for every element of a request that names more than one resource. The owner
of a resource, and the identity under which a request acts, come only from what
the server has recorded; neither may be chosen by an identifier the request
supplies. Only an identity granted administrative permissions is an
administrator, and only authentication decides who a request acts as: a request
without valid credentials never acts as an owner or an administrator, whatever
else it carries, so an explicit deny always applies to it.

The open-by-default fallback — access granted when no access rule decides —
applies only to requests that carry no credentials: a deployment with no
identities configured, and requests served as a configured anonymous identity.
An authenticated caller is never granted access merely because nothing denied
it. A refused request changes nothing and discloses nothing the caller may not
see, and anything that lists resources leaves out the ones the caller may not
see.

## Contracts the fix must honor

- **Refusal form.** A refused request returns a client error (4xx) — never a
  success and never a server error — and performs no side effect: it creates
  nothing, records nothing, removes nothing.
- The properties hold for every deployment, however that deployment
  authenticates its callers.
- **Preservation.** These keep working exactly as today:
  - an owner acting on its own resources;
  - identities granted administrative or wildcard permissions;
  - permissions granted explicitly to an identity, and access rules recorded on
    a resource;
  - requests that carry no credentials on a deployment with no identities
    configured, or served as a configured anonymous identity;
  - trusted local administration tooling: tools that run on the operator's own
    host against the storage backend directly, rather than as a remote caller,
    and that act for an account they name.

The impact above is one example, not the full set of inputs to which the
property applies.

## Constraints

- Fix the flaw and its close variants; keep legitimate use working.
- Do not modify or add tests.
- Do not look up the upstream fix.
- Do not special-case the example.
