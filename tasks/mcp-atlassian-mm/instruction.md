# Keep caller-supplied file paths inside the workspace

## The system

This project is a server that lets an AI assistant work with a team's Atlassian
tools — issue tracking and the wiki — through a set of callable tools. A client
(the assistant, often steered by untrusted content it has read) invokes a tool
with structured arguments; the server carries the request out against the remote
Atlassian site and returns the result.

Several of these tools accept a **local filesystem path** as an argument, as a
convenience for clients that would rather hand off data via the filesystem than
inline it in the tool call:

- tools that **attach a file** to an item upload the bytes at a caller-named
  path to the remote site; and
- tools that **create or edit an item** (a wiki page, a tracker issue, a
  comment) let the caller supply the item's body either inline as text or as a
  path to a file whose contents are read and used as that body.

The server runs with a working directory that is the client's workspace. The
path arguments above are chosen by the caller at request time, and the file they
name is read by the server and then sent on to the remote site (either as an
uploaded attachment, or echoed back as the body of the item that was created or
edited, which the caller can then read).

## Observed problem

A client calls one of these tools and passes a path that points *outside* the
workspace — for instance an absolute path to a sensitive file elsewhere on the
host, or a relative path that walks up and out of the working directory. The
server reads that file and transmits its contents to the remote Atlassian site,
from which the caller can retrieve them. A single ordinary-looking tool call
thus turns the server into a deputy that reads an arbitrary local file and
exfiltrates it. A file the workspace does not contain must never be reachable
this way.

## Security properties (invariants)

- No filesystem path a caller supplies to any of these tools — whether the path
  names a file to be uploaded as an attachment, or a file whose contents are
  read to become the body of a created or edited item — may cause the server to
  read a file outside the working directory (the workspace) and send it to the
  remote site. This holds however the path is spelled: an absolute path that
  lands outside the workspace, a relative path that walks upward out of it, a
  symbolic link inside the workspace whose target is outside it, or a path the
  platform expands on the caller's behalf before it is used; wherever in the
  request the path appears; whether the path is given on its own or as one entry
  among several in a single call; and for every tool that accepts such a path,
  not only the one first noticed.
- When a supplied path would escape the workspace, the operation must fail
  safely: it either returns a client-side error, or reports that item as a
  per-item failure, and in no case opens, reads or transmits the out-of-bounds
  file. A result shaped like success that nonetheless carries the out-of-bounds
  file's bytes or text is not acceptable.

## Keep working

Ordinary in-workspace use must behave exactly as it does today, including:

- attaching a file that lives inside the workspace, whether named by a relative
  path or by an absolute path that stays within the workspace;
- attaching several in-workspace files named in a single call, each uploaded as
  now;
- creating or editing an item whose body is supplied **inline as text** (no file
  path involved), exactly as before;
- creating or editing an item whose body is read from a file **inside** the
  workspace;
- uploading content handed to the server as in-memory data, with no filesystem
  path involved at all — that route never reads a file and must be left
  untouched;
- the server's existing protection of files it writes, which already keeps
  caller-named destinations inside the workspace and must keep doing so.

For example, attaching `./report.pdf` from the workspace, or creating a page
whose body is read from `./page-body.md` in the workspace, is ordinary and must
keep working; a path that resolves to a file outside the workspace is the case
that must be refused. These are examples, not the full set of tools or inputs.

## Constraints

- Fix the underlying problem and its close variants, not just the exact example.
- Keep every legitimate use working.
- Do not modify or add tests, and do not special-case the example inputs.
- Do not consult any upstream fix, advisory, or changelog for this project.
