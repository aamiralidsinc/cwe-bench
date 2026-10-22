# Project knowledge base — files escaping their directory

## What this is

This project keeps a knowledge base for each workspace in a dot-directory
inside the project. The knowledge base holds several kinds of records —
documents, long-term memories, and reusable templates — and each kind is
stored as files under its own subdirectory. Assistants and the web interface
address those records by a name or path chosen by the caller: a document
folder and title, a memory identifier, a template name, or a file inside a
template. The storage layer turns that name into a filesystem location under
the matching subdirectory.

## Observed problem

A document whose folder contains parent-segment spelling (for example
`../../outside`) is accepted and written outside the documentation directory.
Depending on which operation is used, the same class of name can also cause
files outside the documentation directory to be read, overwritten or removed.

## Security properties (invariants)

- No name used to locate a record's file may cause the system to create, read,
  write, move or delete any file or directory outside that record kind's own
  subdirectory. This holds however the name arrives and for every operation
  that turns a name into a file location.
- A name that would escape its subdirectory must be refused with a plain client
  error and no side effect: nothing outside is created, changed or removed,
  and no partial result is left behind. Refusal is a clean failure of the
  operation, not a crash and not a partially applied change.

## Keep working

These legitimate behaviours must be unchanged:

- A document in a nested folder (`guides/setup`), with or without a trailing
  `.md`, and a lookup of an imported document by its source-qualified or short
  path.
- Ordinary memory identifiers, including punctuation such as dots, dashes and
  underscores. Moving a memory between layers keeps working, and looking one up
  by title still resolves or falls through rather than hard-failing.
- An imported template name (`source/feature`) and previewing a template's
  default file when the caller names none.
- A symbolic link that stays inside the project's knowledge base still works.
- Existing documents, memories and templates on disk keep loading and saving.

The examples above are examples, not the full set of cases.

## Constraints

- Fix the underlying problem and its close variants, not just the one example
  trigger shown.
- Keep every legitimate use working.
- Do not modify or add tests, and do not special-case the example values.
- Do not look up the upstream fix for this issue.
