# Metadata filters are executed as Redis query syntax

## What this is

This repository contains LangChain.js integrations, including a Redis vector store. An
application uses it to store documents together with metadata and to run a similarity search
with a metadata filter: only this tenant's documents, only this category, this price range, and
so on. The library compiles the filter into a RediSearch query and sends it to Redis.

## What was observed

When an application builds a metadata filter from a value it received from an end user (a tenant
identifier, a category, a list of tags, a text search term or a numeric bound), that user can put
Redis query punctuation into the value. The punctuation is then treated as part of the query, and
the search returns documents that were never meant to be returned, although the application only
asked for one value.

For example, a search restricted to the tenant `acme`, using the value `acme} @tenant_id:{beta`,
can return `beta`'s documents as well.

## Required behaviour

- No value supplied through a metadata filter, and no filter field name, may be interpreted as
  Redis query syntax. A supplied value must reach Redis as inert data: it must not add, remove or
  alter any condition or clause in the query, and a supplied field name must not make the query
  address a different field. This holds for every kind of filter the library offers, for every
  value shape it accepts, and regardless of how the filter is assembled.
- Filter values can originate from request payloads, stored records or configuration, so their
  run-time type and shape cannot be assumed from the TypeScript signature.
- If a supplied filter cannot be represented safely, the search must fail with a client-visible
  error and must not send a query to Redis. The wording of the error is not specified.

## What must keep working

- Legitimate filters keep selecting exactly what they select today: ordinary values including
  punctuation, several values combined on one filter, wildcard patterns in wildcard searches,
  numeric ranges, date/time bounds, geographic filters, and explicitly raw query text.
- Where a filter kind deliberately supports wildcard patterns, the wildcard characters remain
  operators; where one treats spaces as token separators, they stay separators.
- Public interfaces, filter syntax and return formats do not change.

These examples are examples, not a complete list of the ways the requirement can be violated.

## Constraints

- Fix the problem and its close variants.
- Keep legitimate use working.
- Do not look up the upstream fix or existing implementations.
- Do not special-case the examples.
- There is no network access.
