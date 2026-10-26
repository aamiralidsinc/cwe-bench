# Craft CMS — a caller-supplied destination can reach internal services

## What this is

Craft CMS is a PHP content management system. Sites built on it can ask the server to fetch
a resource from a URL on behalf of a request, and the URL can be influenced by whoever sends
the request.

## What was observed

A GraphQL asset mutation that imports a file from a URL accepts a URL whose host resolves to
a loopback address. The server fetches it and stores the response as an asset, so the caller
can read whatever a local service returns — a service that is not reachable from outside the
host.

## Required behaviour

No destination that the product did not itself configure may cause an outbound request to
reach a loopback, private, link-local, unique-local, unspecified, or cloud-metadata address.
What matters is the address the connection ends up using, however that address is arrived at.
Requests are made only over HTTP and HTTPS.

A request that would violate this is refused with a client error and has no effect: no
connection is made to the refused destination, and no data obtained from it is stored or
returned.

Everything that works today keeps working.

The example above is one instance, not the full set of ways the requirement can be violated.

## Constraints

- Fix the problem and its close variants, not just the example trigger.
- Keep every legitimate use working.
- Do not look up the upstream fix for this issue.
- Do not special-case the example values.
- There is no network access.
