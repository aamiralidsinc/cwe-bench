# Server exceptions leak their text to gRPC clients

## System

This is the pure-JavaScript implementation of gRPC for Node.js. An
application registers service methods with a server; the library accepts calls
over a connection, dispatches each one to the matching method implementation,
and turns the implementation's outcome into the response the client receives.
Application code runs on the server wherever the application has supplied it.

## Observed impact

A client invokes a unary method whose implementation throws an ordinary
`Error` carrying a value that exists only inside the server:

```js
throw new Error('database password is hunter2');
```

The call fails, but the error status the client receives repeats the
exception's message verbatim, so `database password is hunter2` appears in the
client's status details. Anyone allowed to call the method can read server
internals this way.

## Security property that must hold

No exception that application code does not deliberately report may deliver
its text to a client. Whenever application code the server is running fails
with an exception, the call must end with a client-visible error status whose
detail text is a fixed, generic message containing none of the exception's
message, stack, type, file names or values — however far the failing code sits
from the method implementation itself, and whether the failure is immediate or
surfaces later. After such a failure the server must keep serving later calls
normally. This holds for every kind of call the server accepts.

## Contracts the fix must honor

- **Error form.** The failure ends the call with a non-OK gRPC status; it does
  not hang the call and does not take the server down. The detail text is a
  fixed generic message; no particular status code is required.
- **Deliberate reports are preserved.** When application code reports an error
  through the library's own error-reporting API — handing an error to the
  response callback, or emitting an error on a response stream, with or without
  a status code, detail text and trailing metadata — the client receives
  exactly what was supplied: same code, same detail text, same trailing
  metadata. A status that application code supplies directly through the
  library's status-reporting API is likewise delivered unchanged.
- **Everything else works as today.** Successful calls of every kind, request
  metadata, response metadata and trailers are unchanged. Values the
  application itself reports are never redacted.
- **Generality.** The example above is one instance, not the full set of ways
  the property can be violated.

Fix the problem and its close variants. Keep legitimate use working. Do not
look up or copy an upstream fix for this issue. Do not special-case the
example.
