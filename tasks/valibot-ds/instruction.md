# Validation mishandles submitted field names that every object inherits

## The system

This project is a schema-validation library for JavaScript and TypeScript. A service
declares a schema for the data it accepts, passes submitted values through it, and gets
back either the parsed value or a list of issues describing what did not fit. The
library also offers helpers that turn such an issue list into a form the service can
render for its users. Whoever submits the data chooses its property names, so any name
at all can arrive.

## Observed problem

A service accepts an object whose entry names come from the request, validates it with a
schema that checks each entry's value, and passes the resulting issues to the library's
flattening helper so it can show the field messages. When one submitted entry is named
like a member that every JavaScript object inherits -- a name the service did not declare
-- the helper throws a `TypeError`, and the service returns an internal error instead of
the validation messages. The issues themselves are correct; rendering them is what
breaks.

The same kind of submitted name also makes other parts of the library decide that data
is present when it is absent, or absent when it is present.

## What must hold (invariant)

For any property name that comes from validated data, the library must treat that name
as an ordinary data key wherever it decides whether a key is an entry, copies entries,
merges entries, or reports them:

- it must not be mistaken for an entry the schema declared, or for an entry of any
  internal lookup, merely because every JavaScript object inherits a member with that
  name;
- it must not be silently dropped, skipped or overwritten, and it must never make the
  library throw; wherever the library accepts, preserves, validates or reports an
  ordinary supplied name, it must do the same for such a name;
- the library's existing deliberate refusal of names that could mutate an object's
  prototype is unchanged.

The example above shows how the problem appears, not an exhaustive list of names,
schemas or helpers; reason about the property, not the sample.

## Contracts the fix must honour

- **Reporting.** When data does not fit its schema the library reports failure through
  its ordinary result: a failed parse that carries issues. It must never throw instead,
  and a field the schema does not declare is refused as that same ordinary failure.
- **Preservation.** Everything that works today keeps working exactly as today. In
  particular: several messages for the same ordinary field still accumulate; messages
  whose path is not a simple name still reach their existing fallback group; ordinary
  fields supplied to two schemas at once still merge, while genuinely conflicting values
  still produce an issue; a field the schema declares still binds and is still required,
  whatever its name; the treatment of undeclared ordinary fields is unchanged; and a
  collection still returns every entry it accepts.
- **Interfaces.** Issues still carry `message` and `path`, and the flattening helper's
  existing result groups keep their meaning.

## Constraints

- Fix the underlying problem and its close variants, not just the example.
- Keep every legitimate use working.
- Do not special-case the example inputs.
- Do not consult any upstream fix, advisory, or changelog for this project.
