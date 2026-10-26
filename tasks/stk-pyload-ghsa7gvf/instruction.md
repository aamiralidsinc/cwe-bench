# A download manager fetches internal services on behalf of a user-supplied link

## System

pyLoad is a download manager. People add links to it, and pyLoad fetches them on
their behalf in the background.

## Observed impact

A person who may add links can make the server fetch a destination that is only
reachable from the server itself — for example a service listening on the local
machine. The product retrieves the response and uses it as though the link had
pointed at a public file host.

## Security property that must hold

An HTTP fetch that pyLoad performs for a destination a user supplied, and every
request that fetch results in, must be addressed only to globally routable
destinations, whatever carries it there. This holds for every address the
destination resolves to. A destination that is not globally routable is refused
before any request is sent on its behalf.

## Contracts the fix must honor

- **Refusal form.** A refused fetch is not performed: no request is sent for the
  refused destination, and nothing it would have served is kept or returned. The
  refusal may be reported to the caller as an error.
- **Preservation.** Everything that works today keeps working.

Globally routable means an ordinary public address; addresses reserved for
private networks, loopback, link-local or other non-public use are not globally
routable.

The example above is one instance, not the full set of ways the property can be
violated.

## Constraints

- Fix the flaw and its close variants, not just the request shown.
- Keep every legitimate use working.
- Do not special-case the example values.
- Do not consult any upstream advisory or fix for this issue.
- There is no network access.
