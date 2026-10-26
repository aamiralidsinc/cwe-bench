# Prototype pollution through caller-supplied names

This project is a JavaScript library that reimplements PHP's standard library functions for use in
JavaScript applications. Applications call these functions with data they did not write, and some
run the library in a process that also loads third-party code.

When a process has loaded code that replaces a standard string helper, a request string such as
`__proto__[isAdmin]=true` is accepted, and afterwards every plain object in the process reports
`isAdmin` as true, including objects that belong to unrelated users.

## Required property

Every caller- or payload-supplied name is data. It may only become an ordinary own property of an
object the call is working on, or be refused. It must never change the prototype of any object, and
a call must never cause a write to an object outside the call's own data. This holds for names that
collide with property names built into the JavaScript runtime, and it holds even when other code in
the process has replaced built-in methods the library might use.

A refusal must leave no trace: no shared or unrelated object may be modified, and a refusal may be
silent or reported as an error.

## Behaviour that must not change

Everything that works correctly today keeps working exactly as today, with no change to the
structure or the values a call returns for ordinary input.

## Constraints

Fix the problem and its close variants. Keep legitimate use working. Do not look up the upstream
fix. Do not special-case the example above.
