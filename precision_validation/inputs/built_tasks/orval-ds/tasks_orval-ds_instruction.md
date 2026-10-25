# Generated clients can be made to run description-supplied code

## The system
This repository is a TypeScript client generator. It reads an OpenAPI/Swagger API description and
writes TypeScript source: HTTP clients, request validation schemas, mock handlers and factory
helpers, and server-side scaffolding. Descriptions are commonly fetched from third parties, and the
generated source is compiled and shipped, so every string in a description has to be treated as
untrusted data.

## Observed impact
A description whose schema default value contains a backtick or a `${...}` sequence produces a
generated module in which that text is no longer data: importing the generated module runs the
supplied expression instead of carrying a default value. A harmless way to see it is a default value
that sets a global flag when the generated module is imported.

## What must hold (invariants)
For every output kind and configuration the generator supports, any string that originates in the
API description — default values, property and parameter and form-field names, path text, base-URL
text and its variable defaults, and media-type metadata — must remain data in every generated file:

- No description string may add, remove or alter executable statements or expressions in generated
  source, and loading or calling any generated export must not perform an effect described by that
  data other than as data.
- The property holds in every generated artifact (HTTP clients, validation schemas, mock and factory
  code, server scaffolding) and in every supported mode.
- Values survive generation: a description string containing backslashes or other special characters
  must still denote exactly the same string at runtime — it must not be dropped, refused or altered.
- Existing legitimate behaviour is unchanged: path placeholders still become runtime interpolations,
  a dollar sign not followed by an opening brace stays literal, server-variable placeholders are
  still substituted, and non-string defaults (numbers, booleans, null, arrays, objects) keep their
  current meaning.

The characters and positions above are examples, not an exhaustive list; reason about the property,
not the samples.

## Contracts the fix must honour
- Generation keeps succeeding for well-formed descriptions and the emitted files parse. There is no
  user-facing error channel to lean on: an offending value must be carried as escaped data, not
  rejected.
- Generated output keeps its present shape for ordinary inputs: the same exports, the same request
  URLs, the same cache keys, the same defaults.
- Do not add dependencies; the environment is offline.

## Constraints
- Fix the problem and its close variants, not just the exact sample above.
- Keep every legitimate use working.
- Do not modify or add tests; do not change the test harness.
- Do not look up the upstream fix for this issue.
- Do not special-case the example inputs.
