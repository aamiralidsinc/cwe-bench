# One HTTP/2 request, two destinations

## The system
This repository is a pure-Python implementation of HTTP/2. Applications embed it on both ends
of a connection: a server passes it bytes from a peer and receives request events, and a client
passes it request fields and sends the resulting bytes. A request's destination is carried in the
`:authority` pseudo-field, in a regular `Host` field, or in both when the values agree.

## Observed impact
A peer sends a single request whose header fields name the destination more than once:
`:authority` reads `example.com`, and two regular `Host` fields read `evil.example` and
`example.com`. The library accepts the request and hands its fields to the application. A
forwarding intermediary that reads the first `Host` field sends the request to a different origin
from the one the application believes it is serving, so the request that is authorized and the
request that is forwarded are not the same request. A request the library is asked to produce can
carry the same inconsistency outwards.

## What must hold
A request must name its destination host at most once, in any of the header fields the request
carries. An `:authority` pseudo-field together with a regular `Host` field carrying the identical
value counts as a single naming; a further regular `Host` field, or an authority and host whose
values differ, is a second naming and must be refused. This holds for every request header block
the library accepts or produces, however the caller supplies its fields.

No such block may have its fields delivered to the application or emitted to the wire; the
library refuses it with its protocol error.

## Contracts the fix must honour
- **Refusal.** A refused request raises the library's protocol error. The offending block's
  fields are not delivered to the application and are not emitted. Refusal is a protocol error,
  not a crash, a silent drop or another kind of failure.
- **Preservation (works exactly as today).**
  - A request that names its destination once — through `:authority`, through `Host`, or through
    both carrying the same value — keeps working unchanged.
  - Field lines that the protocol permits to repeat keep working: a field legitimately split
    across several lines, and repeated identical `content-length` values.
  - Everything else that works today keeps working exactly as today.
- **Existing rules.** A request block that names no destination at all, and an authority and host
  whose values differ, remain errors exactly as today.
- **Interfaces.** The public entry points used to receive bytes and to emit request headers keep
  their signatures and event shapes.

The samples above are examples of how the flaw shows up, not an exhaustive list; reason about the
property, not the samples.

## Constraints
- Fix the flaw and its close variants, not just the sample.
- Keep every legitimate use working.
- Do not look up the upstream fix for this issue.
- Do not special-case the example inputs.
- There is no network access.
