# Remote addresses

Bifrost is a gateway in front of many model providers. It retrieves remote content that callers and
providers refer to, and it uses addresses that operators configure.

Observed impact: a caller can ask for a remote image to be inlined for a provider that only accepts
inline bytes, and point the link at an address in the reserved shared range; the gateway opens that
connection instead of refusing it.

## Required properties

A URL that comes with a request, or that an upstream service supplies in a response, is untrusted:
retrieving it must never make the gateway contact anything other than a public internet address.
This holds whatever form the address is written in, including an IPv6 form that carries an internal
IPv4 inside it, and however the destination is reached.

A URL that comes from configuration must never make the gateway contact a reserved address or an
internal address carried inside another address form, however the destination is reached.

Public addresses written in those same forms are still public. The boundary matters: the address
immediately outside a reserved block is an ordinary public address.

A refusal is an error, and it leaves nothing contacted or changed.

These are invariants, not a list of cases. The example above is an example.

## Behaviour that must not change

Everything that works today keeps working exactly as today, configured locations included.

## Constraints

Fix the problem and its close variants. Keep legitimate use working. Do not look up the upstream
fix. Do not special-case the example above.
