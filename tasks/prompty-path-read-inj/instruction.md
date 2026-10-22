# Prompt loader: external references must stay inside the prompt directory

## The system

This project is a runtime for `.prompty` files — small text documents that
describe a prompt or an agent. Each file has a YAML frontmatter block and a
markdown body. An application loads one of these documents through the library's
public load call and gets back a typed prompt object it can render and run.

To keep prompts modular, a document can pull in content from other files that
sit next to it on disk. Frontmatter values can reference an external file so its
contents are injected in place (shared connection settings as structured JSON or
YAML, or a reusable block of text). A document can also build on a base document
that supplies common defaults, and it can declare child prompts that it invokes
as tools. In every case the referenced target is written as a path by whoever
authored the prompt, and the loader reads it relative to the prompt file's own
directory.

## Observed problem

A prompt document is author-controlled content: applications routinely load
`.prompty` files that came from a template gallery, a shared repository, or an
end user. When such a document references a target, the loader follows the path
the author wrote and reads whatever it lands on — including locations well
outside the folder the prompt lives in. A hostile or careless prompt can name a
path that points elsewhere on the host and have the contents of an unrelated
file pulled into the loaded prompt, where the application then surfaces or sends
it. Loading a prompt must never be able to read files the prompt's own directory
does not contain.

## Security properties (invariants)

- No path expressed in a prompt document may cause loading that document to read
  a file outside the directory that contains the document. This applies to every
  kind of external target a document can name — injected file contents, an
  included text fragment, an inherited base document, and a referenced child
  prompt — regardless of how the path is spelled.
- When a path would escape the prompt's directory, loading fails with a
  client-side error and no such file is opened or read. Partial reads, or
  returning the out-of-directory contents, are not acceptable.

## Keep working

Legitimate references that stay inside the prompt's own directory must keep
behaving exactly as they do today, including:

- a reference into a sub-directory of the prompt's directory;
- a structured reference (JSON or YAML) that must still be returned as parsed,
  structured data — not flattened to text or dropped;
- an included text fragment, an inherited base document, and a child-prompt tool
  whose target lives inside the prompt's directory.

A reference whose path resolves to a file outside the prompt's directory is the
case that must be refused. The list above is illustrative, not exhaustive.

## Constraints

- Fix the underlying problem, not just the example.
- Keep every legitimate use working.
- Do not modify or add tests, and do not special-case the example inputs.
- Do not consult any upstream fix, advisory, or changelog for this project.
