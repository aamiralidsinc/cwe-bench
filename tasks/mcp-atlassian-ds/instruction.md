# Caller-supplied file references must stay inside the workspace

## The system

This project is a server that exposes callable tools to an AI assistant acting
for a team. A client — often steered by untrusted content it has read — invokes
a tool with structured arguments; the server performs the requested operation
against the team's remote site and returns the result. The server runs with a
working directory that is the client's workspace.

Some caller-supplied values name a local file. The server resolves such a
value to a file on disk, reads it, and sends its contents to the remote site
(or returns them to the caller in a result). These values are chosen by the
caller at request time.

## Observed problem

A client supplies a value that causes the server to read a file outside the
workspace and transmit its contents to the remote site, from which the caller
can retrieve them. A single ordinary tool call thus turns the server into a
deputy that reads an arbitrary local file and exfiltrates it.

## Security properties (invariants)

- No caller-supplied value, through any operation the server exposes and in any
  position of a request, may cause the server to open, read or transmit the
  contents of a file that resolves outside the working directory (the
  workspace). This holds however the value is spelled and however the server
  arrives at the file it names.
- When a caller-supplied value would cause such an out-of-workspace read, the
  operation must fail safely: it returns a client-side error, or reports that
  part of the request as a per-item failure, and in no case opens, reads or
  transmits the out-of-bounds file. A success-shaped result that nonetheless
  carries the out-of-bounds file's bytes or text is not acceptable.

## Keep working

Ordinary in-workspace use must behave exactly as it does today:

- any file that resolves inside the workspace may still be read and sent,
  whether one is named or several in a single request, and however its
  location is spelled;
- content supplied inline in a request, or held in memory, must be handled
  exactly as before, without any filesystem access;
- the server's existing protection of files it writes — which already keeps
  caller-named destinations inside the workspace — must keep working.

## Constraints

- Fix the underlying problem and its close variants, not just one example.
- Keep every legitimate use working.
- Do not modify or add tests, and do not special-case particular inputs.
- Do not consult any upstream fix, advisory, or changelog for this project.
