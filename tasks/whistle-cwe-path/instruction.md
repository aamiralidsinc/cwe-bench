# Local debugging proxy — background data component leaks host files

## System
This project is a developer HTTP/HTTPS debugging proxy with a browser-based
control panel. Behind the panel runs a background component that the panel talks
to over a small local HTTP interface. That component owns the tool's on-disk data:
it serves captured traffic and stored artifacts back to the panel, creates
short-lived scratch items on request, and lists what has been saved. The panel is
the only intended client of this interface. The panel already relies on a
specific, existing contract for how it identifies itself to this component;
honour that contract rather than inventing a new one.

## Observed problem
An operator reports that anything able to reach this local interface can read
files off the host, including files that have nothing to do with the tool's own
storage area. For example, a single HTTP `GET` to the interface that asks for a
file by its path comes back with that file's contents, even though the caller
presented nothing to show it was the tool's own panel. Other data the component
holds is exposed the same way, to the same anonymous caller.

## Required properties
- The background component must act only on requests that prove they come from
  the tool itself. Any other request must be refused and must cause no file to
  be read, no stored data to be returned and nothing to be written — regardless
  of what the request asks for. "Refused" means the request ends in a client
  error with no data in the response and no change on disk.
- Legitimate use driven by the panel must keep working exactly as it does
  today. All existing panel functionality, including loading arbitrary files
  the operator selects, must keep working unchanged.

The path and item names in the examples are only examples; the properties above
hold for any value a caller might send and for every operation the component
exposes, not just the one shown.

## Constraints
- Fix the reported problem and its close variants; do not special-case the
  example path or item.
- Keep all legitimate, authorized use working.
- Do not modify or add tests, and do not change what the tests exercise.
- Do not look up the upstream project's own fix for this issue; solve it from
  this repository.
