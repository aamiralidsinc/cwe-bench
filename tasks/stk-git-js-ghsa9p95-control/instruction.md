# Command execution through git arguments

This project is a Node.js library that wraps the `git` command line. Applications use it to run git
operations in a repository while the library builds the argument list and starts the child process.

Passing a caller-supplied option into a clone made the library start a local program named by that
option, instead of refusing the request.

## Required property

No value supplied by a caller may cause git to start a program of the caller's choosing on this
machine. No value supplied by a caller may relax git's transport permissions to permit a transport
helper. An unsafe request must be refused as a client error, with no side effect.

An application that deliberately relies on git's transport-helper facility may opt in with the
option `unsafe: { allowUnsafeProtocolOverride: true }`; with it, the helper use it configures must
keep working.

## Behaviour that must not change

Everything that works correctly today keeps working exactly as today.

## Constraints

Fix the problem and its close variants. Keep legitimate use working. Do not look up the upstream
fix. Do not special-case the example above: it is one instance, not the full set.
