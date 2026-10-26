# Koel: server-side fetches of user-supplied media URLs

Koel is a self-hosted music and podcast server. A signed-in user subscribes to podcasts by giving a
feed URL and adds internet radio stations by giving a stream URL. The server itself fetches those
URLs, sometimes while the request is handled and sometimes later.

## What goes wrong

A user subscribes to an otherwise ordinary public podcast feed whose episode entries point their
media at an address only the server can reach. The subscription succeeds, and Koel later fetches
that media from the internal address and serves the response back to the user.

## Requirement

No URL that a user supplies, and no URL carried inside data the server later processes on that
user's behalf, may cause Koel to send a request to a host that is not publicly routable. Wherever
such a URL is used for a server-side fetch, the fetch must be refused before any connection is
made, and nothing may be stored, written or returned from the refused target.

This is an invariant about the target of every outbound request, not a list of cases. It applies
however the value arrives. The example above is one example.

A refusal is a client error and has no effect.

## Behaviour that must not change

Everything that works today keeps working exactly as today.

## Constraints

Fix the problem and its close variants. Keep legitimate use working. Do not look up the upstream fix.
Do not special-case the example above.
