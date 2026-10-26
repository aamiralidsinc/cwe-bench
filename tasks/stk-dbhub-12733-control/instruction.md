# A read-only database tool can still change data

DBHub is a database MCP server. An application points it at one or more databases and exposes its
tools to an AI agent. A tool can be configured read-only for databases that must not be changed; a
read-only tool is supposed to run only statements that cannot modify anything, and to refuse
everything else.

Our deployment configures the SQL tool read-only on a PostgreSQL database. A caller still changed a
sequence: a request whose SQL was `SELECT setval('orders_id_seq', 1)` returned success and the
sequence moved. The same kind of request can change anything else the database user is allowed to
change.

## Security invariant

A tool configured read-only must never change database state — no rows, no schema, no sequence and
no other durable setting — in response to any request it handles.

Read-only mode must decide before anything runs: a request is admitted only when every statement in
it is a read-only statement by its own syntax, and any other request is refused with the read-only
error.

Execution must not weaken that decision: a request that would change something is refused or has no
effect even when admission let it through.

## Refusal

A refused request reports a client error and has no effect. A request refused by read-only mode is
reported with the tool's read-only violation error (`READONLY_VIOLATION`); a request the database
rejects while executing is reported with an execution error (`EXECUTION_ERROR`). Nothing after the
refusal runs, and no change is left behind.

## What must keep working

Everything that works today keeps working exactly as it does today.

The example above is an example, not the full set.

## Constraints

- Fix the problem and its close variants.
- Keep legitimate use working.
- Do not look up the upstream fix.
- Do not special-case the example above.
