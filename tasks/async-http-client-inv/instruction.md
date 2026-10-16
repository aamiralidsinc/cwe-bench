# One user's requests go out with another user's session

## Report

Our backend calls an upstream API for many end users through one shared,
long-lived instance of this asynchronous Java HTTP client, in its default
configuration (it keeps a cookie store that remembers cookies from responses).
On each call we attach the calling user's own session by setting a `Cookie`
request header.

The upstream service sometimes receives our calls authenticated as the wrong
user. For example, after an earlier response had set `SID=<user A's session>`
for the upstream origin, a request we built with
`Cookie: SID=<user B's session>` reached the server carrying user A's session.

## Security properties the client must keep

- Every cookie the caller puts in a request's `Cookie` header(s) is delivered
  to the server. A cookie the store already held before the call never
  replaces, removes or overrides a cookie the caller set, on any request the
  client sends for that call, including those it issues automatically to
  continue it.
- This holds whatever value, in whatever syntax, the caller gives a cookie. A
  client that cannot send a caller's header may fail the request instead, but
  it must never send a stored cookie in place of one the caller named.

## Behaviour that must keep working

- The cookie store works as today: with no caller header it sends its cookies,
  and next to a caller header it still adds the stored cookies whose names the
  caller did not set.
- A caller's `Cookie` header is sent exactly as written when the store holds
  nothing for that origin. Cookies added through the client's request-cookie
  API are still sent.
- When the server sets a new value for a cookie in a response during the call
  (a session rotation), the requests the client then issues automatically to
  continue the call carry that new value, not the value the caller started
  with.
- Everything else about how requests are sent and continued behaves exactly
  as today.

## Constraints

- Fix the client so that the reported behaviour and its close variants no
  longer occur, while legitimate use keeps working.
- Do not modify or add tests.
- Do not look up the upstream fix for this issue.
- Do not special-case the example above.

## Environment

The repository is checked out at `/app` and builds offline with Maven
(`mvn -o -pl client -am package -Dmaven.test.skip=true`); all dependencies are
already cached in the image, so no network access is required or available.
