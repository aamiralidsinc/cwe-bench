# Network clients can change files and run code through the test runner

## The system

The project in `/app` is a JavaScript/TypeScript test runner. While it is
running it can expose a small control server so that a browser-based UI and the
browser-mode test driver can interact with it. The control server is protected
by an access token, but that token is embedded in the page the server itself
serves, so any client that can load the page obtains it.

The address the control server listens on is configurable. Developers usually
run it bound to the local machine, but it can be bound to a network-reachable
address so the UI can be opened from another machine.

## What we observed

With the control server bound to a network-reachable address, a client that
holds the token sends a single request naming one of the project's test files
and new contents, and the file on disk is overwritten with those contents. The
same client can also make the runner execute test code. This is one example, not
the whole problem.

## Required behaviour

- When the control server is reachable from the network, no request from a
  client may create, modify, or delete any file on disk, and no request may
  cause test code to run — whichever of the server's operations is used, through
  whichever interface, and whichever target the request names. Such a
  request has no effect: the targeted file is left exactly as it was and no run
  is started.
- A refused request fails cleanly: the client may receive an error or the
  request may simply be ignored, but the server keeps running and nothing on
  disk changes. It must not crash.
- Reading files, file metadata, and other read-only information must keep
  working regardless of where the server is bound.
- When the control server is reachable only from the local machine, every
  operation keeps working exactly as today: a developer can save an edited test
  file, run and re-run tests, write snapshots, and have browser tests read and
  write files. Operations that are rejected today must stay rejected.

## Constraints

- Fix the problem in the library itself, not only the example above. Do not
  special-case the example's file names or values.
- Keep legitimate local use working as described.
- Do not modify or add tests; hidden tests will check the behaviour.
- Do not look up or copy an upstream fix for this issue.
