# Keep file access inside the workspace

## The system

This project is an assistant-facing server for Chrome. An AI assistant connects to
it as a client and calls its tools: the server drives the browser, captures what
the page shows, and returns the result. Several tools take a local filesystem path
as an argument — a place to write captured output, a file to read input from, or a
location the browser is asked to load. That path is chosen by the client, and the
client is often steered by content it read on a page it was browsing.

The server is told which directories it may work in (the workspace roots), and the
system temporary area always counts as scratch space. Filesystem work is meant to
stay inside those places.

## Observed impact

A client calls a tool with a path that looks like it is inside a workspace root but
is actually a link to a directory somewhere else on the machine. The server accepts
the path, follows the link, and writes the captured output over a file that the
workspace does not contain. One ordinary-looking tool call can therefore change or
disclose files anywhere the server can reach.

## Security properties (invariants)

- Every file the server opens, reads, creates, changes, or hands to another program
  or to the browser while serving a tool call must really be inside one of the
  workspace roots (the system temporary area always counts as one). This applies to
  the path the client supplied, to any path the server derives from it or keeps from
  an earlier step, and to every link along the way. It holds whether the target
  already exists or would be created by the operation.
- If the server cannot establish that the real file is inside, it must refuse the
  operation: the client sees an error and the server leaves no side effect — nothing
  outside the roots is created, overwritten, read out, or passed on.

## Keep working

Everything that works today must keep working exactly as today, including:

- writing to a file that does not exist yet, including when several of its parent
  directories do not exist;
- a workspace root that is itself reached through a link, and a link inside a root
  whose target is also inside that root;
- a declared roots list that also contains an entry which cannot be resolved, while
  the other entries still work;
- a client that declares no roots at all, and the temporary area used when a caller
  names no path;
- ordinary files, and a reusable result the server keeps on disk to avoid repeating
  work, when they genuinely live inside a root.

These are examples, not the full set of inputs the fix must handle.

## Constraints

- Fix the underlying problem and its close variants, not just the exact example.
- Keep every legitimate use working.
- Do not look up the upstream fix or existing implementations.
- Do not special-case the example inputs.
- There is no network access.
