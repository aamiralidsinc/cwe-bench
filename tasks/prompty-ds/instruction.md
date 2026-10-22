# Prompt documents can read files outside their own directory

## The system

This project provides runtimes for `.prompty` documents: small, portable text
documents that describe a prompt or an agent. An application loads a document
through a runtime's public load call and receives a typed object that it can
render and run. Documents are routinely obtained from template galleries, shared
repositories, and end users.

## Observed problem

Loading a document obtained from an untrusted source can return an object whose
fields hold the contents of an unrelated file on the host — a file that lives
outside the folder that holds the document. The application then surfaces or
sends that content. Loading a document taken from a template gallery can be
enough to return a description built from a file that lives elsewhere on the
host.

## Security property

No path written in a prompt document, or in anything that document loads, may
cause loading or use of the document to open or read a file outside the
directory that contains the document. What counts is the location a reference
actually resolves to, not how it is spelled. When a reference resolves outside,
the operation fails with a clean error and that file is never opened; returning
any part of its contents is not acceptable.

## Keep working

Every reference whose target resolves inside the document's directory keeps
behaving exactly as it does today, through every public way of loading or using
the document, in both synchronous and asynchronous form:

- the same content comes back in the same form as today: structured targets
  still arrive as parsed structured data rather than flattened text, and
  composed or inherited content is still applied;
- the spelling of a reference does not matter: upward or absolute spellings are
  fine when the target really is inside the directory;
- targets in sub-directories remain valid.

These are examples of the contract, not an exhaustive list of inputs.

## Constraints

- Fix the underlying problem and its close variants, not just the exact example.
- Keep every legitimate use working.
- Do not special-case the example inputs.
- Do not consult any upstream fix, advisory, or changelog for this project.
- There is no network access.
