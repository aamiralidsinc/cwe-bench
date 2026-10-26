# Authorization plugins must decide on what the daemon actually does

The daemon can load third-party authorization plugins. Every API request and every response passes through them: a plugin is told what the daemon is about to do, or what it has done, and may allow or deny. Sites rely on these plugins to enforce their policy, so a plugin can only make a sound decision if it is shown the same operation the daemon performs or has performed.

Observed impact: a client sends an API request whose body is a little over one megabyte; the daemon executes the requested operation, while the authorization plugin was asked about a request with an empty body and allowed it. Anyone whose protection depends on that plugin never sees the operation at all.

Required behaviour, wherever an operation can occur:

- Every request body the daemon will parse or act on is either shown to the plugins in full, or the request is refused before it has any effect.
- An authorization plugin's decision on a response is made before any part of that response reaches the client; a denial leaves the protected content undelivered.
- Registry credential material is never shown to authorization plugins.

A refusal is an error response with no effect. Everything that works today keeps working, including requests with bodies up to one megabyte. The example above is one instance, not the full set: fix the behaviour wherever it occurs, do not special-case the example, and do not look up the upstream fix.

Repository note: this checkout predates Go modules. Set `GO111MODULE=off` and build from its GOPATH import path, `/go/src/github.com/docker/docker`.
