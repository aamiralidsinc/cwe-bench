# OpenBao — lease operations reachable across namespaces

## What this is

OpenBao is a secrets-management server. A deployment can split its configuration into
namespaces, each with its own mounts, tokens, policies and leases. A lease records a
secret or credential that a mount handed out and the lifetime it stays valid for.
Clients act on leases they hold, and a parent namespace administers the namespaces
beneath it.

## Observed problem

A client holding a valid token in one namespace can name a lease that belongs to a
different namespace and have the server revoke it. The request is accepted, and the
other namespace's leased secret is torn down even though the caller has no authority
there.

## Security property

A request that acts on a lease may act only on a lease that belongs to the caller's
own namespace, or to a namespace the caller's namespace administers. The lease's owner
must be established from the lease itself; it must never be taken from a value the
caller supplies. A request that would act on a lease outside that set is refused with a
client error and has no effect: the lease keeps running, and nothing about it is
changed or disclosed.

## Keep working

Everything that works today keeps working: a request that stays within the set above
behaves exactly as it does now.

## Constraints

- Fix the underlying problem and its close variants, not just the one example trigger.
- Keep every legitimate use working.
- Do not look up the upstream fix for this issue.
- Do not special-case the example values.
