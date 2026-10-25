# Unauthenticated takeover of a fresh Portainer instance

## What this is

Portainer is a management platform for containers and Kubernetes. A freshly deployed
instance has no operator account until its first operator completes setup, and until
then it is reachable without credentials.

## What was observed

A freshly deployed instance that had never had an operator account was taken over by a
client that presented no credential of any kind. The client caused the instance to start
with persistent state of the client's choosing and then signed in as its operator. The
operator had configured no account and no password, and the client proved nothing.

## Required behaviour

While an instance has no operator account, every action that would grant operator
authority or replace the instance's persistent state is an operator action: it may
proceed only for a request that proves knowledge of the instance's current setup token.

No value a client can send or configure may substitute for that proof, regardless of how
the request is shaped or delivered. A request that does not present the token, presents a
wrong one, or presents no usable value at all must be refused with a client error and
must leave the instance unchanged: no operator authority may be granted and no persistent
state may be replaced.

The token is presented in the `X-Setup-Token` request header. An operator can pin it for
a fresh instance with the `PORTAINER_SETUP_TOKEN` environment variable, and that exact
value must be accepted. With no token pinned on a fresh instance the server must still
require a token that it generates itself; the requirement must not be disabled just
because no value was configured. Comparison is exact: only the configured or generated
token is accepted.

## Behaviour that must keep working

- With the correct token, legitimate operator actions continue to succeed exactly as they
  do today, with the same validation and the same success responses.
- On an instance that already has an operator account, the corresponding actions keep
  their present behaviour and require no token, including the existing "already
  initialized" refusals. This holds however the operator account came to exist.
- Information that must stay publicly readable before anyone signs in stays readable
  without credentials.

## Constraints

- Fix the problem and its close variants.
- Keep legitimate use working.
- Do not modify or add tests.
- Do not look up the upstream fix.
- Do not special-case the example.
