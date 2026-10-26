# A schema that admits nothing must admit nothing

## What this is

This repository is a web framework for Node.js. An application attaches a JSON Schema to the
requests it serves and expects the framework to check each incoming request against that schema
before the handler runs. Some handlers are meant to be unreachable: the JSON Schema boolean
`false` is the schema that matches nothing, so a request schema of `false` should refuse every
request.

## What was observed

An application registered a handler whose request schema was the boolean `false`. A request that
should have been refused was accepted and the handler ran. The same handler with an ordinary object
schema in place of `false` refused the request as expected.

## Required behaviour

- Whenever the application has supplied a schema for a request, every request handled under that
  schema must be checked against it before the handler runs. A schema that matches nothing must
  make every such request fail as a client error, and no part of the handler may run.
- This is a rule about the meaning of the schema, not about the kind of value that carries it, the
  name of the field it was written under, or the shape of the handler it protects. It does not
  matter where in the application's code the schema is supplied, nor when.
- A schema that the framework cannot apply must never be silently ignored: either the server
  refuses to become ready with it, or it is enforced.
- Everything that works today keeps working exactly as today. Schemas that accept requests keep
  accepting the same requests. A request part that the application explicitly leaves empty keeps
  its current behaviour: the server warns and still serves the request. A handler whose schema is
  satisfied still runs exactly as before, whatever kind of handler it is, and ordinary requests
  next to a protected one in the same application are still served normally.

These examples are examples, not a complete list of the ways the requirement can be violated.

## Constraints

- Fix the problem and its close variants.
- Keep legitimate use working.
- Do not look up the upstream fix or existing implementations.
- Do not special-case the examples.
- There is no network access.
