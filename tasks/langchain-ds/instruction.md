# Agent file access must stay inside the configured area

## The system

This project ships middleware for building LLM agents. The middleware gives a
model controlled access to a file store while the agent runs. An application
configures it with a workspace directory, and may also narrow access to a set
of allowed directories inside that workspace. The model chooses the arguments
of each request at run time, and it may be steered by untrusted content it has
read.

These components are the boundary that keeps such input away from files the
application never offered.

## Observed problem

An application ran an agent over a shared directory of project files. In one
run, a tool result the agent received surfaced a file that lived outside the
configured workspace. The agent then repeated that file's contents into its
reply, where the user saw material the application never exposed.

## Security property

No argument supplied by the agent may cause any operation of these components
to reach, read, write, enumerate, delete, or otherwise affect anything outside
the configured workspace — or, when the application has narrowed access,
outside the allowed directories. This holds for every value and for every
operation the component offers.

A permitted location is the workspace itself, an allowed directory itself, or
a location beneath either by whole path segments. Nothing else counts as
inside. A link is judged by the location it resolves to, not by the text of
its own path.

When an input would leave the permitted area, the operation must fail safely:
it may report nothing found or no match, or return an error, but it must not
read, enumerate, create or modify the out-of-bounds target. A result that
looks like success while carrying an out-of-bounds path or content is not
acceptable, and no out-of-bounds file may be created or changed.

## Keep working

Ordinary use inside the permitted area must behave exactly as it does today.
In particular, every operation must keep working, with its current result
shape, for the workspace, for an allowed directory itself, and for anything
nested beneath them, for reads and writes alike. Values that merely resemble
an escape must keep working: a file name that contains dots without being an
upward-walking path segment, and a link inside the permitted area whose target
is also inside it. A legitimate request that simply finds nothing must still
report that nothing was found rather than return an error.

These are examples, not the full set of values or operations.

## Constraints

- Fix the underlying problem and its close variants, not just the exact example.
- Keep every legitimate use working.
- Do not special-case the example inputs.
- Do not consult any upstream fix or existing implementation for this project.
- There is no network access.
