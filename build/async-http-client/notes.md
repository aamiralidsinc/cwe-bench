# Build notes: async-http-client (CWE-287)

## What was verified (empirically, in the built image's toolchain)

Root cause confirmed in the vulnerable request serialiser: when a request's
cookie list is non-empty it does `headers.set(COOKIE, encode(list))`, which
*replaces* any `Cookie` header the caller set directly. With the default cookie
store active, the store injects its cookies into the request's cookie list (via
`addCookieIfUnset` on the first request and again in the redirect/auth-retry
interceptors), so the caller's `Cookie` header is overwritten by a stored
session that may belong to a different user. CWE-287 (improper authentication):
one user's request can be sent authenticated as another.

Observed outgoing `Cookie` header (server side of a loopback stub), per build:

| scenario (caller header / store) | vulnerable | fixed |
|---|---|---|
| first request, SID=userB / SID=storeval | `SID=storeval` | `SID=userB` |
| first request, session=mine / tracking+SID | session dropped | `session=mine; ...` |
| two caller headers a=1,b=2 / SID | replaced | `a=1; b=2; ...` |
| redirect hop, SID=userB / SID=storeval | `SID=storeval` | `SID=userB` |
| 401 auth retry, SID=userB / SID=storeval | `SID=storeval` | `SID=userB` |
| redirect that rotates SID (func) | `SID=rotated` | `SID=rotated` |
| 401 that rotates SID (func) | `SID=rotated` | `SID=rotated` |

Gate-relevant results (5 security tests, 6 functional tests):

- vulnerable (nop): security 0/5 (all exploits succeed), functional 6/6.
- oracle (upstream 3-file source fix): security 5/5, functional 6/6, reward 1.0,
  identical across repeats.
- `fix_hops_only.patch` (patches the redirect + auth-retry reconciliation only,
  leaves the first-request serialiser): security 2/5, functional 6/6
  -> **security_fail** (the first-request leak survives a hop-only fix).
- `fix_serialiser_only.patch` (merges at the serialiser only, no hop
  reconciliation): security 5/5 but functional 4/6 -> **functional_fail**
  (a session the server rotates on a redirect/auth hop is overridden by the
  stale caller header the serialiser now keeps).
- `alt_correct_fix.patch` (independent serialiser merge that decodes the caller
  header with `ServerCookieDecoder` and merges Cookie objects, plus the same hop
  reconciliation): reward 1.0 -> **pass**.

Why genuinely multi-site: no single site suffices. The serialiser merge is
needed for the first-request leak and consistent emission; the hop reconciliation
(redirect interceptor + the cookie-reconciliation helper) is needed so a session
the server rotates mid-flow still wins instead of a stale caller value. A fix at
only one of the two places fails a different group of tests.

## Entry point and services

Entry point is the library's public API driven through `AsyncHttpClient`
(`prepareGet(...).setHeader("Cookie", ...).execute()`), against an in-process
loopback HTTP/1.1 stub (`tests/common/StubServer.java`) that scripts the
Set-Cookie / 302 / 401 responses and records the `Cookie` header it receives.
No external services and no network: the stub binds 127.0.0.1 on an ephemeral
port inside the test JVM.

## Not verified / caveats

- The project's own tests for this area were NOT run (see manifest
  `verified.project_tests_run`). They extend a Jetty-based test harness and the
  suite pulls Jetty/Tomcat/Kerberos test-scope dependencies that were not vendored
  into the lean offline image. The standalone tests here drive the same public
  API and cover the same first-request, redirect and auth-retry code paths.
- The advisory id / CVE in the candidate row are in the future relative to real
  history; treated as given (this is a benchmark fixture). Fields were verified
  against the actual diff, not trusted blindly.
- Build and test rely on a warmed `~/.m2` and a staged dependency set baked into
  the image; `mvn -o` (offline) is used at verify time.
