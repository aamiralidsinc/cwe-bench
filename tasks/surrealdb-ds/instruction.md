# SurrealDB: stored expressions can modify data

SurrealDB is a multi-model database. Clients send SurrealQL statements to the
server, and schema owners attach expressions to the definitions they store.
The engine evaluates those stored expressions itself, on behalf of whichever
client happens to trigger the evaluation.

## Invariant

Evaluating an expression that a stored definition carries must never change
stored data as a side effect. A request that reaches a data change this way,
and a request that would store an expression able to reach one, must both fail
with a client error and leave all data and all stored definitions unchanged.
This holds for every stored expression and every way the evaluation can reach
a write, whether or not the requesting client could perform that write itself.

## Contract

- Refusal is a client error for the request that triggered the evaluation; the
  error text is not specified.
- Data changes that an operation is defined to perform as part of its own work
  are not side effects of an evaluation, and must still happen.
- Stored expressions that only read keep working exactly as today.
- Ordinary client reads and writes are unchanged, and access continues to
  follow the stored rules.
- Storing a definition whose expressions only read is accepted exactly as
  before.

The property is general: it covers every stored expression. Fix the underlying
problem and its close variants; do not special-case any example.

## Constraints

- Fix the problem and its close variants; keep legitimate use working.
- Do not look up the upstream fix or advisory.
- Do not special-case the example.
- There is no network access.
