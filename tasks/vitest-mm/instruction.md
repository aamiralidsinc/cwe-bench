# Network clients can change files, run code, and reach files outside the project

## The system

The project in `/app` is a JavaScript/TypeScript test runner. While it is running
it can expose a small control server. A browser-based UI and the browser-mode test
driver use it to interact with the running project. The control server is
protected by an access token, but that token is embedded in the page the server
itself serves, so any client that can load the page obtains it.

The address the control server listens on is configurable. Developers usually run
it bound to the local machine, but it can be bound to a network-reachable address
so the UI can be opened from another machine. The same server also exchanges test
evidence with the UI over HTTP.

## What we observed

With the control server bound to a network-reachable address, a client that holds
the token sends a single request naming one of the project's test files and new
contents, and the file on disk is overwritten with those contents. The same
client can also make the runner execute test code. This is one example, not the
whole problem.

Separately, a request named a path outside the project and the runner read or
wrote that path. That happened even when the project had relaxed the usual
file-serving restriction.

## Required behaviour

- Authorization. When the control server is reachable from the network, no
  request from a client may create, modify, or delete any file on disk, and no
  request may cause test code to run — whichever of the server's operations is
  used, through whichever interface, and whichever target the request names. Such
  a request has no effect: the targeted file is left exactly as it was and no run
  is started.
- Confinement. No request from a client may read or write a file outside the
  project's files — whichever operation, whichever interface, and whatever
  file-serving settings the project has.
- A refused request fails cleanly: the client may receive an error or the request
  may simply be ignored, but the server keeps running and nothing on disk
  changes. It must not crash.
- Reading files, file metadata, and other read-only information must keep working
  regardless of where the server is bound. Writing a file that is inside the
  project must keep working whatever file-serving settings the project has.
- When the control server is reachable only from the local machine, every
  operation keeps working exactly as today: a developer can save an edited test
  file, run and re-run tests, write snapshots, and have browser tests read and
  write files. Operations that name a file the server has not registered are
  rejected exactly as before.

## Constraints

- Fix the problem and its close variants in the library itself, for every
  operation and interface that can reach it, not only the example above. Do not
  special-case the example's file names or values.
- Keep legitimate local use working as described.
- Do not modify or add tests; hidden tests will check the behaviour.
- Do not look up or copy an upstream fix for this issue.
