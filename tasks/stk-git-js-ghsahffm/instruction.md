# A caller-supplied git configuration can run programs and relax protocol restrictions

simple-git is a Node.js library that applications use to run git operations without building
subprocess calls by hand. Integrations often forward a dictionary or array of git options that
originated from an end user — for example, a service that lets a user choose options for a
repository it fetches on their behalf.

Our service does this. With a crafted option, a user made our git child process run a program of
their choosing. The options were passed through to the library unchanged.

## Security invariant

No configuration value supplied by a caller may make git run a program of the caller's choosing
or relax a transport-protocol restriction, no matter which call it is supplied to or which form
or source it reaches git through.

## Refusal

Refuse by raising the library's existing error for a disallowed option, before the operation has
any effect. A refused operation must leave no filesystem or repository change behind.

Where the library already offers an explicit opt-in for a class of unsafe operation, that opt-in
keeps working.

## What must keep working

Everything that works today keeps working exactly as it does today: ordinary operations with
legitimate options, the library's public interfaces, and their documented error behaviour.
Configuration that carries data rather than naming a program or relaxing a protocol restriction
keeps working.

The example above is an example, not the full set.

## Constraints

- Fix the problem and its close variants.
- Keep legitimate use working.
- Do not look up the upstream fix.
- Do not special-case the example.
