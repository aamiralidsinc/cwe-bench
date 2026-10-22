# Prompt documents must not reach outside their own folder

## The system

This project is a runtime for `.prompty` files — small text documents that
describe a prompt or an agent. Each file has a YAML frontmatter block and a
markdown body. An application loads one of these documents through the library's
public load call and gets back a typed prompt object it can render and run.

To keep prompts modular, a document can pull in content from other files that
sit next to it on disk: shared connection settings as structured JSON or YAML, a
reusable block of text, defaults inherited from a related document, or a
companion prompt it later invokes. The body is itself a template, and a shared
snippet can be pulled into it the same way. In every case the referenced target
is written as a path by whoever authored the prompt, and the runtime resolves it
relative to the prompt file's own directory.

## Observed problem

A prompt document is author-controlled content: applications routinely load
`.prompty` files that came from a template gallery, a shared repository, or an
end user. When such a document names a target, the runtime follows the path the
author wrote and reads whatever it lands on — including locations well outside
the folder the prompt lives in. A hostile or careless prompt can name a path
that points elsewhere on the host and have the contents of an unrelated file
pulled into the loaded prompt, where the application then surfaces or sends it.
Loading a prompt must never be able to read files the prompt's own directory
does not contain.

## Security properties (invariants)

- No path a prompt document expresses may cause the runtime to read a file
  outside the directory that contains the document. This holds for every part of
  a document that can name a file, and at every point in the document's life —
  loading it, rendering its body, and anything the runtime does on the loaded
  prompt's behalf. It holds regardless of how the path is spelled (a relative
  path that walks upward, an absolute path, or a link that points outward), and
  whether the path is given on its own or as one entry among several.
- When a path would escape the prompt's directory, the operation fails with a
  client-side error and no such file is opened or read. Partial reads, or
  returning the out-of-directory contents, are not acceptable.

## Keep working

Legitimate references that stay inside the prompt's own directory must keep
behaving exactly as they do today, including:

- a reference into a sub-directory of the prompt's directory;
- a structured reference (JSON or YAML) that must still be returned as parsed,
  structured data — not flattened to text or dropped;
- every ordinary use of the document format that names a file inside the
  prompt's directory, whether the content is pulled in while the document is
  loaded, while its body is rendered, or while the runtime acts on a prompt it
  declares.

For example, a prompt that pulls in `shared-config.json` sitting beside it, or a
snippet from a `partials/` sub-folder, is ordinary and must still load and
render; a reference whose path resolves to a file outside the prompt's
directory is the case that must be refused. These are examples, not the full
set of inputs.

## Constraints

- Fix the underlying problem and its close variants, not just the exact example.
- Keep every legitimate use working.
- Do not modify or add tests, and do not special-case the example inputs.
- Do not consult any upstream fix, advisory, or changelog for this project.
