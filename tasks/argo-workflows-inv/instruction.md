# Shared workflow engine: tenant isolation and secret-handling report

## Report

We run this Kubernetes-native workflow engine as a shared service. Each team
works in its own namespaces and calls the engine's API server with its own
cluster identity; the server must give every caller exactly what the cluster's
access control grants that identity. Workflows keep artifacts in object-store
repositories configured with credentials. Source-hosting providers deliver
events to the server's webhook endpoint, which anyone can reach before any
authentication. Administrators can switch on the template-referencing
restriction, under which every submitted workflow must reference a stored
template that they control.

A review with a low-privilege tenant account found that the engine does not
keep the properties below. For example, a tenant with no right to read workflow
templates in another team's namespace asked the API for one of them by name and
received its full definition. Treat this as one symptom; the engine must keep
every property below.

## Security properties

- The API server hands a stored workflow template to a caller only if the
  cluster's access control lets that caller read that template: a namespaced
  template by the caller's rights in its namespace, a cluster-wide template by
  the caller's cluster-wide rights.
- Concurrency limits (the semaphore limits workflows wait on) can be read and
  managed through the API in any namespace. A caller may read a limit only if
  they may read, in that namespace, the cluster objects that hold the limits,
  and may create, change or remove a limit only if they may change those
  objects in that namespace. Rights held in other namespaces do not count.
- Repository credentials (access keys, secret keys, passwords, tokens) never
  appear in log output, for any artifact operation and any kind of repository.
- No one can make the server read or buffer an arbitrarily large request body
  before the request is authenticated. An oversized webhook delivery is refused.
- Under the template-referencing restriction the referenced template alone
  decides how the workflow's pods are specified. Apart from the inputs the
  template declares (its parameters), if anything the submitter supplies would
  end up in the specification of the pods the workflow runs, by whatever field
  or route, the submission is rejected.
- A refused request gets an error and nothing else: no template body, no limit
  value, no change to any stored limit. Over HTTP it is a client error (4xx). A
  workflow rejected by the template-referencing restriction is rejected the way
  the restriction rejects submissions today: it ends in the error state and none
  of its pods run.

## What must keep working, exactly as today

- A caller allowed to read a template receives it.
- A caller who holds the rights above in a namespace, and none cluster-wide,
  creates, reads, changes and removes limits there.
- Every artifact operation; only what reaches the log changes.
- Webhook deliveries of ordinary size: a correctly signed delivery from a
  configured provider is accepted and acted on under that provider's identity,
  and a request matching no configured provider is passed on.
- Under the template-referencing restriction, a referencing workflow that
  overrides nothing runs, and everything rejected today stays rejected.

## Constraints

- Fix the engine so that the reported attack and close variants of it no longer
  work, while legitimate use keeps working.
- Do not modify, delete or add tests. Hidden tests will grade the result.
- Do not look up or copy the upstream fix.
- Do not special-case the example.

## Environment

The source is checked out at `/app`, with Go dependencies and build cache in
the image. No live cluster or network is needed: the hidden tests drive the API
server, the artifact handling and the workflow controller in-process against an
in-memory stand-in for the cluster.
