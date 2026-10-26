# Filter values and generated ClickHouse SQL

Hypequery is a TypeScript query builder for ClickHouse. Application code describes the rows it
wants and the values they must match — values that usually come from a request — and the library
assembles all of it into a ClickHouse statement and sends that statement to the server.

A filter value that ends with a backslash is not carried as one value. The backslash escapes the
quote that closes the string literal, so text that was never written as SQL becomes part of the
statement, and a request can change which rows the query returns.

## Requirement

No input that a caller supplies may be read as SQL syntax. Whatever a caller supplies, the
statement the library builds keeps the same structure, and the supplied input never becomes part
of that structure.

Conditions combined in one statement keep their own meaning: no condition that a caller adds may
widen, narrow or drop the effect of another condition in the same statement.

A refusal is a client error and has no effect.

These are invariants, not a list of cases. The example above is an example.

## Behaviour that must not change

Everything that works today keeps returning the same results.

## Constraints

Fix the problem and its close variants. Keep legitimate use working. Do not look up the upstream
fix. Do not special-case the example above.
