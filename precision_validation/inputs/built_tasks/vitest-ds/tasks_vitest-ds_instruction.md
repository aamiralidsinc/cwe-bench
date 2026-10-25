# Network clients can change files and run code through the test runner

## The system

The project in `/app` is a JavaScript/TypeScript test runner. While it is
running it can expose a control server used by clients that drive the running
project. The server is protected by an access token, but that token is embedded
in a page the server serves, so any client that can load the page obtains it.
The address the server binds to is configurable, and it can be bound to an
address reachable from the network.

## What we observed

With the server bound to a network-reachable address, a client holding the
token caused files on disk to be overwritten and project code to run. This is
one example of the problem, not its whole extent.

## Required behaviour

- While the server is reachable from the network, no request from a client may
  create, modify or delete any file on disk, and no request may cause code
  belonging to the project to execute. Such a request has no effect.
- No request may create, modify or delete a file outside the project's root
  directory, whichever address the server is bound to. Such a request has no
  effect on the file it names.
- A refused request fails cleanly: the client may receive an error or the
  request may simply be ignored, but the server keeps running and nothing on
  disk changes. It must not crash.
- Reading files, file metadata and other read-only information keeps working
  whichever address the server is bound to.
- When the server is reachable only from the local machine, changing files and
  running code keep working exactly as today, and requests naming a file the
  server has not registered keep being rejected as before.

## Constraints

- Fix the problem and its close variants in the library itself, for every
  operation and interface that can reach it, not only the example above. Do not
  special-case the example's file names or values.
- Keep legitimate local use working as described.
- Do not modify or add tests; hidden tests will check the behaviour.
- Do not look up or copy an upstream fix for this issue.
