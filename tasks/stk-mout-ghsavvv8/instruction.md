# Untrusted input can change objects the library was not asked to touch

This is a small general-purpose JavaScript utility library for working with object data.

One application deep-mixes a request body it has parsed from JSON into one of its own configuration
objects. A request body can contain a key named `__proto__`, and after that call every unrelated
object created later in the process exposes a property the request chose. The application never
asked the library to modify those objects, and the request did not have access to the process's own
objects.

## Requirement

No caller-supplied input may add, change or remove a property on a shared prototype object. The only
object a call may change is the destination the caller passed, together with that destination's own
nested objects.

A call that would break this invariant must have no effect. It may refuse with an error, but it must
not perform a partial change first.

These are invariants, not a list of cases. The example above is an example.

## Behaviour that must not change

Everything that works today keeps working.

## Constraints

Fix the problem and close variants. Keep legitimate use working. Do not look up the upstream fix. Do
not special-case the example above.
