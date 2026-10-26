# Caller-supplied git options can run programs and write files

GitPython is a Python library that applications use to run git operations without building
subprocess calls by hand. A common integration forwards a dictionary of git command options that
originated from an end user — for example, a service that lets a user pick clone options for a
repository it fetches on their behalf.

Our service does this. With a crafted option, a user made our server run a program of their
choosing on the host, outside any repository. The option dictionary was passed through to the
library unchanged, and the library invoked git with it.

## Security invariant

No value supplied by a caller among the options that reach git may cause git to run a program of
the caller's choosing, or to write to a filesystem path of the caller's choosing.

## Refusal

Refuse by raising the library's existing error for a disallowed option, before the operation has
any effect. A refused operation must leave no filesystem change behind.

## What must keep working

Everything that works today keeps working exactly as it does today: ordinary operations with
legitimate options, the library's public interfaces, and their documented error behaviour.

The example above is an example, not the full set.

## Constraints

- Fix the problem and its close variants.
- Keep legitimate use working.
- Do not look up the upstream fix.
- Do not special-case the example.
