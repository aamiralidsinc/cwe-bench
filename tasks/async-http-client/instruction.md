# Cookie header replaced by the client's stored session

## Summary

Our backend uses this asynchronous HTTP client library to call an upstream API
on behalf of many end users from a single long-lived client instance. The client
runs with its default configuration, which keeps a cookie store that remembers
cookies seen in responses for each origin.

For every outbound call we attach the *calling* user's own session by setting a
`Cookie` request header on the request we build (for example
`Cookie: SID=<this-user's-session>`). We observed that the request actually sent
on the wire does **not** carry the session we set. Instead it carries a session
value the client had stored earlier for the same origin — a value that belongs to
a *different* user whose response happened to set that cookie before. In effect
one user's request is transmitted authenticated as another user, which is a
cross-account authentication failure.

## How to reproduce

- Use a client in its default configuration so its cookie store is active, and
  arrange for the store to already hold a cookie for the target origin (for
  instance by first performing any request whose response sets one).
- Build a request to that origin and set a `Cookie` request header with your own
  value, then execute it against a server that reports back the `Cookie` header
  it received.
- The server receives the stored cookie, not the one you set on the request.

The same substitution happens on requests the client issues automatically as a
continuation of yours — when it follows a redirect to the same origin, and when
it retries after an authentication challenge: those follow-up requests also go
out carrying the stored session rather than the header you set.

## Required behaviour

- A `Cookie` request header that the caller sets explicitly must be delivered to
  the server. When the caller names a cookie, the caller's value is the one that
  must be sent, on the first request and on any automatic follow-up request.
- The cookie store must keep working: it may still add its own cookies to a
  request, including alongside a caller-set header, and a session that the server
  rotates during a redirect or an authentication exchange must still take effect
  for the continued request.

## Environment

The repository is checked out at `/app` and builds offline with Maven
(`mvn -o -pl client -am package -Dmaven.test.skip=true`); all dependencies are
already cached in the image, so no network access is required or available.
