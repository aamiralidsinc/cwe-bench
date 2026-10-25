# Build-analysis data is served to other machines and other web pages

Rsdoctor analyses an Rspack build and serves the result on a local port while the build runs, so
that a developer can inspect it from a page or from a tool of their own.

## What happens

While an analysis is being served, any web page the developer happens to open can read it, and a
client on another machine can reach it. In one case a page delivered from an unrelated origin made
an ordinary read of the analysis and was answered with the analysis and with the machine's own
address.

## Security property

An analysis, and any state the tool changes when asked to act on it, is private to the machine and
to the person running it. No page delivered from another origin and no client on another machine
may obtain that analysis, change it, or receive anything derived from it — however the analysis is
served, by whichever part of the product the serving is started, for whatever a request asks, and
whether the data is pulled by a client or pushed to it.

For every server the product starts to serve an analysis, the property takes these forms:

- **Reachability.** Only a client on the local machine may connect; a client using any other
  address of the machine cannot.
- **Destination.** A request is served only when it names this machine by a local name: a loopback
  address in either family, a bare `localhost`, or a named `*.localhost` subdomain. A request
  naming any other destination, or naming none, is refused.
- **Origin.** A request delivered by a browser from an origin that is not local is refused with a
  client error, no analysis data, no side effect, and no cross-origin access grant. A local origin
  is allowed whatever local port it names; a named `*.localhost` origin is allowed only when it
  names the same local host the request was addressed to. A request that carries no origin, from a
  command-line or other non-browser client, keeps working.
- **Credential.** Being local does not make a client the first-party page. The updates the product
  delivers to its own page are available only to a client that presents the credential that server
  instance issued: the credential is part of the endpoint value the server already publishes to
  that page (`socketUrl`), a connection that does not present it fails to establish, and another
  instance's credential is not accepted. The first-party page, using the published value, keeps
  working.
- **Disabled.** When the analysis is configured not to be served, nothing listens.
- **Configuration.** The existing options that select the port and the accepted origins keep
  working in every form they accept today: a configured origin is allowed, a configuration that
  names no origin keeps the local default, and turning cross-origin access off still serves local
  clients.

A refused request is a 4xx client error with no data and no side effect: it must not crash the
process and must not answer with a server error. A refused connection is simply not established.

Legitimate local use behaves exactly as today: clients that send no origin, pages served from a
loopback or localhost origin, a page on one local port reading an analysis served on another,
requests addressed to a loopback address of either family, and the address the product advertises
for its own page, which is local.

These examples are examples, not the full set.

## Constraints

- Fix the problem and its close variants; do not special-case the example above.
- Keep every legitimate use working.
- Do not modify or add tests.
- Do not look up the upstream fix.
