# Prototype pollution from caller-supplied values

bmoor is a small JavaScript utility library that other applications embed to work with nested
values inside ordinary objects.

Writing a nested value through the library can change state shared by every object in the
process. In one reproduction, an application passed a request-controlled name to the library's
deep-set call; afterwards every ordinary object in the process returned the attacker's value for
that name, including objects the application had created itself.

## Required property

A value supplied by a caller must never become a property of a shared built-in prototype. An
operation that would do that must refuse: it either reports an error or leaves its target
unchanged, and in both cases shared built-in state is exactly as it was.

## Behaviour that must not change

Everything that works correctly today keeps working exactly as today.

## Constraints

Fix the problem and its close variants. Keep legitimate use working. Do not look up the upstream
advisory or fix for this issue. Do not special-case the example above. There is no network
access.
