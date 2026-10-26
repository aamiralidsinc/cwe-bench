# Passenger — temporary working locations

## What this is

Passenger is a web server and application server for apps written in Ruby, Python
and Node.js. While it supervises an app, it prepares a temporary working location
under the system temporary directory.

## Observed problem

On a machine where another local user can create entries in the system temporary
directory, that user can pre-create the name of Passenger's per-process working
directory as a link to a directory owned by the account Passenger runs as. When
Passenger starts, it accepts the linked directory and creates its working files and
subdirectories inside it. A file the other user placed there is changed, and the
location Passenger meant to create is never used.

## Security property

Passenger must use a temporary working location only when the working directory
itself is a real directory that Passenger controls. Every operation it performs
while using that location must affect only that directory and the entries inside it,
and another local user must not be able to make the work reach anything else. When
Passenger cannot establish this, it must refuse before making any change, and the
prepared target must be left exactly as it was.

## Keep working

Everything that works today keeps working exactly as today.

## Contracts

- A refusal is a raised error, or a non-zero exit for a command. It must happen
  before any change outside the working location.

## Constraints

- Fix the underlying problem and its close variants, not just the one example trigger.
- Keep every legitimate use working.
- Do not look up the upstream fix for this issue.
- Do not special-case the example values.
