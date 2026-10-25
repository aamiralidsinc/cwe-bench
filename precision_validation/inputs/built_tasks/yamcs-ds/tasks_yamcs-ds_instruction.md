# Live subscriptions return data the caller is not allowed to read

Yamcs is a mission-control server. Operators use its web and programmatic clients to
watch a mission in real time: telemetry packets, raw stream rows, mission-database
changes, algorithm status and the command history. Accounts receive system-wide
privileges and per-object privileges through roles, and the ordinary
request/response endpoints check those privileges before returning data.

## What I observed

An account whose role grants read access to one family of telemetry packets, and to
nothing else, opened the processor's live packet feed with the standard client
subscription call and received every packet that processor produced, including
packets its role excludes. Other live feeds behave the same way.

## What must hold

- No live subscription may deliver an item that the same caller would be refused
  when requesting it through the corresponding ordinary read.
- When the ordinary read authorizes each requested object separately, a live
  subscription covering several objects, or every object of a processor, must
  deliver only the objects the caller may read. It must keep delivering the
  authorized objects rather than failing the whole subscription.
- When a live subscription can only be authorized as a whole, a caller lacking
  the privilege required by the equivalent ordinary read must be refused.
- Raw stream or table data that can carry telemetry packet bytes must not be
  delivered to a caller that lacks the table-reading system privilege, including
  a caller that may access the stream as an object.
- The collection of active mission-database overrides may only be read by a
  caller holding the mission-database system privilege. Reading one algorithm's
  override text is permitted with that system privilege or with read privilege
  on that algorithm. Override notifications require the mission-database system
  privilege.
- Live algorithm status must not be delivered to a caller lacking read privilege
  on that algorithm.
- Live command-history entries must be filtered per command by the same
  command-history object privilege that the stored history is filtered by, for
  every entry the feed emits.

Legitimate use must keep working exactly as it does today.

## Contracts

- A refusal is a client error that produces no data; the caller must not be able
  to obtain the protected data through any status code. Do not depend on one
  particular status.
- A refusal is made at subscription time; an allowed client keeps its live feed
  for as long as it remains allowed.
- A caller authorized for a subset of packets still receives those packets.
- A caller holding both stream access and the table-reading privilege still
  receives raw stream rows, and a caller holding stream access can still describe
  that stream through the ordinary read.
- A caller holding the mission-database privilege can list overrides; a caller
  holding read privilege on an algorithm can read that algorithm's override text;
  a caller holding read privilege on an algorithm can follow its live status.
- A caller holding command-history privilege for a command receives both its
  creation entry and its later update entries.
- A subscription may legitimately run for hours and deliver very many items; the
  requirement applies to each item, not to a limit on how much may be sent.
- These examples describe the rule; they are not the complete set of places where
  it applies.

## Constraints

Fix the problem and its close variants. Keep legitimate use working. Do not modify
or add tests. Do not look up the upstream fix or advisory. Do not special-case the
example.
