# virtualenv: seed wheels fetched from an index are not authenticated

## What this is

virtualenv builds isolated Python environments and seeds each new environment with the packaging
tools it needs. Some seed wheels ship with virtualenv; others are fetched from a package index at
environment-creation time.

## What was observed

Creating an environment with downloads enabled against an index that served a different file under
a familiar wheel name installed that file's contents into the new environment. The name was the
only thing that matched the release; the bytes were whatever the index returned.

## What must hold

A seed package may be installed into an environment only when it is the artefact its wheel name
claims. Whenever the authoritative public release record publishes a digest for that exact file
name, the bytes that end up in the environment must match that digest; a mismatch is refused and
nothing is installed from it.

A wheel that no public release record covers is legitimate and keeps working, as is a wheel served
by a package index the operator configured. A wheel whose bytes match the published record also
keeps working.

## Contracts

- A refused wheel fails the operation with an error, and the environment is not seeded from it.
- Everything that works today keeps working.
- The example above is an example, not the full set.

## Constraints

Fix the problem and its close variants. Keep legitimate use working. Do not look up the upstream
fix or an existing implementation. Do not special-case the example. There is no network access.
