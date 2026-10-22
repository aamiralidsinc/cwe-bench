# Agent file tools: keep searches and file operations inside the workspace

## The system

This project is a toolkit for building LLM agents. Among its building blocks are
a set of *middleware* components that give an agent controlled access to files
so it can look things up and keep notes while it works. Two families are
relevant here:

- A **file-search** component. An application configures it with a single
  workspace directory on the host. It exposes the agent two operations: find
  files whose name matches a glob pattern, and search file contents with a
  regular expression. Both take an agent-chosen pattern and report the matching
  files (as workspace-relative paths) or matching lines.

- A **file tool** component that backs Anthropic's text-editor and memory tools.
  It lets the agent view, create, edit, move and remove files. One variant keeps
  the files on the host filesystem under a configured root directory; another
  keeps them in the agent's own conversation state. Either variant can be
  restricted so the agent may only touch paths under one or more allowed
  directories (for example, a memory tool is limited to a notes directory).

In every case the pattern, path or filename the operation acts on is chosen by
the model as it runs — and the model may be steered by untrusted content it has
read. These components are the boundary that keeps that model-chosen input from
reaching files the application never offered.

## Observed problem

An application runs an agent over a shared directory of project files and gives
it the memory tool so it can jot notes under a dedicated notes directory. A
single tool call the model emits — a search pattern, or a path handed to a file
operation — comes back having reached a file the application never meant to
expose: content from elsewhere on the host, or an entry that belongs to a
neighbouring directory outside the one the tool was limited to. The agent then
repeats that content into its reply or its notes, where the user or a downstream
system sees it. A file the configured workspace (or the allowed directory) does
not contain must never be reachable this way.

## Security properties (invariants)

- No pattern, path or filename an agent supplies to any of these operations may
  cause that operation to read, list, enumerate, copy or write a file outside
  the workspace directory it was configured with. This holds however the input
  is spelled — a relative pattern or path that walks upward, an absolute path, a
  name that merely shares leading characters with an allowed directory, or a
  symbolic link inside the workspace whose target lies outside it — and for
  every one of these operations, not only the one first observed.
- When an operation is restricted to one or more allowed directories, only the
  allowed directory itself and genuine descendants of it may be touched; a
  sibling whose name merely begins with the same characters is outside the
  restriction.
- When an input would escape, the operation must fail safely: it either reports
  nothing found / no match, or returns a client-side error, and in no case opens,
  reads, lists, copies or writes the out-of-bounds file. A result that is shaped
  like success but carries the out-of-bounds path or content is not acceptable.

## Keep working

Ordinary in-workspace use must behave exactly as it does today, including:

- a glob such as `*.py` or a recursive `**/…` pattern, and a regex content
  search, over files inside the workspace, returning the same matches as now;
- a filename that merely contains dots (for example a dotted version string in
  the name) — only a genuine upward-walking path segment is an escape, not any
  appearance of those characters;
- a symbolic link inside the workspace whose target is also inside the workspace;
- an operation restricted to a directory still working for that directory itself
  and for files nested beneath it;
- every file operation — viewing, creating, editing, moving, copying and listing
  — continuing to work for in-bounds paths, and a "nothing found" result still
  being returned rather than an error when a legitimate search simply has no
  matches.

For example, searching `*.py` in the workspace, or keeping a note under the
allowed notes directory, is ordinary and must still work; a pattern or path that
resolves to something outside the workspace is the case that must be refused.
These are examples, not the full set of inputs or operations.

## Constraints

- Fix the underlying problem and its close variants, not just the exact example.
- Keep every legitimate use working.
- Do not modify or add tests, and do not special-case the example inputs.
- Do not consult any upstream fix, advisory, or changelog for this project.
