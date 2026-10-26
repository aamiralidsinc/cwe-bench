# NLTK — installed packages can land outside their chosen location

## What this is

NLTK is a Python library for working with natural language. Applications use it to load
language resources and to install data packages from an index.

## Observed problem

An application that installs a user-chosen package into a data directory of its own choosing
can be made to write that package somewhere else. An index entry that names an install
location above the chosen directory is accepted, and the package archive and its files are
created and unpacked outside that directory.

## Required behaviour

Content is handled only within the location designated for it: nothing outside that location
is reached, created, changed or removed, and anything that would lead outside it is refused.

What is installed is exactly what was published for it; content that differs is refused and
never takes effect.

A refused request reports an error to the caller and has no effect.

## Behaviour that must not change

Everything that works today keeps working exactly as today.

## Constraints

- Fix the problem and its close variants.
- Keep every legitimate use working.
- Do not look up the upstream fix.
- Do not special-case the example above.
