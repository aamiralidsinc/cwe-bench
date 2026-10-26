# AnyCable: usage telemetry leaves the server without consent

AnyCable is a real-time WebSocket server for Ruby on Rails applications. It can report anonymous
usage information to a hosted telemetry service. Operators configure the server through
command-line options, environment variables and a TOML configuration file.

## What we observed

Starting a stock build of the server, without configuring anything related to telemetry, sends a
usage event to the telemetry service. The request is authenticated with a credential that is the
same in every copy of the product, so the event is accepted as if the operator had enrolled this
deployment. Pointing the server at a local capture endpoint reproduces it.

## What must be true

Telemetry is opt-in. The server must not send anything to the telemetry service unless this
deployment has been given its own telemetry token to use. A credential compiled into the product,
or supplied as a shipped default, is not the deployment's own, and consent expressed without one is
not enough.

Nothing that is sent to the telemetry service may contain, encode or be derived from any other
secret or credential value the deployment has configured: not in whole, not in part, and not
through any transformation. Reporting only whether a secret is configured is acceptable.

Both requirements apply to everything the server sends to that service, in every event.

## Contracts

- A deployment supplies its telemetry token through the `ANYCABLE_TELEMETRY_TOKEN` environment
  variable, or when the binary is built. When a token is supplied, telemetry keeps working: the
  boot event is delivered with its documented properties and any custom properties, presented
  under that token.
- Setting `ANYCABLE_DISABLE_TELEMETRY=true` keeps silencing telemetry, even when a token is
  supplied.
- Everything else that works today keeps working exactly as today: the server starts, serves its
  endpoints, and honours the configuration it accepts now.
- The examples above are examples, not the full set of forms these values can take.

## Constraints

- Fix the problem and its close variants, not only the example.
- Keep legitimate use working.
- Do not look up the upstream fix or advisory.
- Do not special-case the example.
