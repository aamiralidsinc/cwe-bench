# pytonapi: unauthenticated webhook deliveries reach application handlers

pytonapi is the Python SDK for TONAPI, a blockchain data service. Applications
use the SDK to receive TONAPI event notifications: they create webhooks for the
event kinds they care about and attach a handler to each kind. TONAPI issues a
secret for every webhook it creates and marks each delivery with
`Authorization: Bearer <secret>`. The SDK checks that secret before it runs the
application's handler.

**Reported impact.** A stranger can run an application's handler with no
credential. In the reported case the application attached a handler to a
delivery route of its own and created its webhooks through the SDK; a POST to
that route with no `Authorization` header reached the handler, carrying a
payload the stranger chose.

## Required behaviour

Every delivery route an application attaches a handler to is bound to the
secret TONAPI issued for that route. A delivery to a registered route reaches a
handler only when it carries exactly that route's secret, and a delivery that
carries the right secret still reaches the handler.

## Contracts

- A delivery that fails the check is refused with a client error, before any
  handler runs; the refused delivery has no effect.
- Everything that works today keeps working exactly as it works today.
- Assume a delivery may target any route an application registered.

## Constraints

- Fix the reported problem and its close variants.
- Keep legitimate use working exactly as it works today.
- Do not look up the upstream fix.
- Do not special-case the example above.
