# Caller-controlled destinations can reach internal services

## What this is

This repository is an MCP server for CKAN open-data portals. It can be run for a single local
client or exposed so that other machines can reach it. The destinations the server contacts can
come from the caller.

## What was observed

A client can pass an ordinary-looking host name that resolves to a loopback address, and the server
connects to it instead of refusing: the caller gets a successful result built from whatever the
internal service answered.

## Required behaviour

- No destination supplied by a caller, and no destination the server takes from anything another
  service returns, may cause the server to open a network connection to a loopback, private,
  link-local, unique-local, shared, broadcast, unspecified, or cloud-metadata address. What matters
  is the address the connection ends up using, however that address was obtained.
- When one name maps to several addresses, every one of them must be acceptable; a single internal
  address is reason enough to refuse.
- A refused operation must fail with a client-visible error and must not reach the address at all.
  The wording of the error is not specified.
- A server that other machines can reach must refuse to start until an operator has configured
  which hosts may be contacted, through the existing comma-separated `CKAN_ALLOWED_DOMAINS`
  setting. A server used only by a single local client must start without that setting.
- Legitimate use keeps working exactly as today: public portals reached through ordinary public
  host names or through public literal addresses are queried normally, including public addresses
  just outside the private ranges such as `172.15.x.x` and `100.63.x.x`. Private literals that are
  refused today stay refused. Public interfaces, names and response formats do not change.

These examples are examples, not a complete list of the ways the requirement can be violated.

## Constraints

- Fix the problem and its close variants.
- Keep legitimate use working.
- Do not look up the upstream fix or existing implementations.
- Do not special-case the examples.
- There is no network access.
