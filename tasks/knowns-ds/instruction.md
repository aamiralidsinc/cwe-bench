# Keep knowledge-base files inside the folders the product manages

## The system

Knowns is a local knowledge base for a software project, shipped as a command
line tool, an assistant-facing tool server, and a web UI. A project keeps its
knowledge in a folder inside the repository: documents (Markdown pages),
persistent memory notes, and reusable code-generation templates. Memory notes
can also live in a machine-level folder shared across projects. Documents can
be created, read, updated, renamed, deleted, previewed and exported; notes can
be created, read, updated, deleted and moved between the project and machine
levels by promoting or demoting them; templates are selected by name and their
files are previewed before generation.

Clients name these items: a document by its path inside the document library, a
note by its identifier, a template by its name. The product turns the name it
receives into a file inside the folder it manages for that kind of content.

## Observed problem

A local web API request for the document named `../notes` returns the contents
of `notes.md` from outside the project's document library. The same kind of
value also lets a client write, rename or delete files outside the library,
read or remove memory notes outside the memory folders, and reach files outside
the template library. Read-only or not, the file the client names is not the
file the product is allowed to touch.

## Security properties (invariants)

- No value that names a document, a memory note, a template, a template file,
  or a generated destination may cause the product to read or write a file
  outside the folder it manages for that kind of content. This holds for every
  operation that resolves such a value, whatever the operation is called and
  whatever it returns.
- An identifier read back from stored data — a record's own identifier in its
  metadata — is as untrusted as one supplied by a client. Using it must not
  reach outside the managed folders either.
- This holds however the value is spelled, including forms another platform
  would treat as a separator, an absolute reference, or an alternate file name,
  and for a symbolic link inside a managed folder whose target is outside it.
  A value that uses path syntax is not a valid name for an item and must be
  refused, not silently reinterpreted as a name inside the folder.
- Refusal must be safe: a client-side error (an error result from the
  assistant tools, a 4xx response from the web API) and no file read, created,
  changed or removed outside the managed folders. A result shaped like success
  that carries the outside file's bytes is not a refusal.

## Keep working

Ordinary use must behave exactly as it does today, including:

- nested document paths of ordinary depth (for example `guides/setup`), a
  document name given with or without its `.md` suffix, and names that contain
  dots (`v1..2` is a normal name, not an escape);
- imported documents resolved by their full path and by the short reference
  that omits the import source name;
- memory identifiers made of letters, digits, dots, underscores and hyphens,
  references written as a title slug, and promoting or demoting a note between
  the project and machine levels;
- templates selected by a local name, import-qualified names that contain a
  slash by design (`source/name`), and a template file at a nested path;
- creating, updating, renaming and deleting a document by an ordinary path.

Every response field the product returns today keeps its name and meaning.
These are examples, not the full set of operations or inputs.

## Constraints

- Fix the underlying problem and its close variants, not just the exact example.
- Keep every legitimate use working.
- Do not modify or add tests, and do not special-case the example inputs.
- Do not consult any upstream fix, advisory, or changelog for this project.
