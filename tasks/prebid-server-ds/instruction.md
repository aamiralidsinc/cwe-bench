# Outbound bidder requests can be redirected by request data

Prebid Server is a header-bidding server: publishers send it OpenRTB auction requests, and for every bidder named in an impression the server constructs and sends an HTTP request to that bidder's configured endpoint.

## Observed impact

A bid request can decide where the server sends its outbound bid traffic. Supplying `attacker.example/path` where a bidder's network label belongs is accepted today, and the outbound bid request is delivered to `attacker.example` instead of the bidder's own server. Anyone who can submit a bid request can point the server's outbound connections at a host of their choosing.

## Required invariant

Whatever values a bid request carries for a bidder, the server must never construct or send an outbound bidder request whose destination differs from the host that bidder's own endpoint configuration names. A value that would move the destination elsewhere must be refused with a client error before any outbound request exists. This guarantee belongs to the code that builds outbound bidder requests: it must hold for every bidder and for every caller that supplies bidder parameters.

## Contracts

- Refusal is a client error and has no side effect: no outbound bidder request is constructed for the offending parameters.
- Legitimate values must keep producing exactly the destination they produce today. Values the server normalises before use (an optional scheme, or the bidder's own domain, may be stripped first) remain legitimate; so do optional values that are legitimately empty, explicit numeric ports, mixed case, and single-label or numeric names such as `localhost` or `127.0.0.1`.
- Everything else that works today keeps working; do not remove or degrade unrelated bidders or parameters.

The examples above are examples, not an exhaustive list of values or places.

Fix the problem and its close variants. Keep legitimate use working. Do not look up the upstream fix. Do not special-case the examples.
