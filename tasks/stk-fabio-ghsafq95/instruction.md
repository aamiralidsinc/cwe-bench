# Backends cannot trust the forwarding headers they receive

Fabio is a router and load balancer. It forwards a client's request to a backend and, along the
way, sets headers that describe the exchange. Backends routinely trust those headers for access
decisions, rate limiting and audit records, so they have to carry the proxy's values.

A client sent a request whose hop-by-hop declaration named a forwarding header the proxy had just
set. The backend received the request with no such header at all.

## Requirement

Whatever a backend may take as the proxy's own word about a forwarded request must really be the
proxy's. Where the proxy sets a value on a forwarded request, or the operator designates a header to
carry a trust value, the backend must receive the proxy's value unchanged: the client must not be
able to remove it, alter it, or substitute a value of its own. For every header the operator
designates to carry a trust value, the backend receives the proxy's own value on every path the
proxy serves.

These are invariants, not a list of cases. The example above is one example.

## Behaviour that must not change

- Everything that works today keeps working.

## Constraints

Fix the problem and its close variants. Keep legitimate use working. Do not look up the upstream
fix. Do not special-case the example above.
