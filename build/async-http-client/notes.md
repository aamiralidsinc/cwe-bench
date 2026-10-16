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

## 2026-10-16 test repair

Inputs: `build/audit/lenient_items_2026-10-16.txt` has three REC lines for this task and no
`==` items. `research/own-runs/TEST-REPAIRS.md` has no `## async-http-client` section.

| item | decision |
|---|---|
| REC deepseek-1013-214752 (uGhFbba): optional security case, a caller header mixing an RFC-invalid pair with a valid one, plus a stored cookie with the invalid pair's name | **fix** (below) |
| REC mimo-1013-214753 (tfkenPc), first: graded code vs the agent's late edit; kill the agent before verification | **already fixed**: test.sh kills Claude Code processes before grading (added 2026-10-16); the main-session audit counts it as a solve |
| REC mimo-1013-214753 (tfkenPc), second: keep the agent-kill step | **already fixed** (kept) |

Why the new case is fair: the instruction says "When the caller names a cookie, the caller's value is
the one that must be sent". If the store's same-named session goes out in its place, that breaks the
stated property, however the caller's value is formatted. The test asserts only that property. It
does NOT require the unusual value to be delivered verbatim: refusing the request (an exception) or
dropping the unusual pair is accepted, because the instruction says nothing about non-RFC values.
If a request reaches the server, it must still carry the caller's ordinary pair `x=1`. That pair is
a caller-set cookie, which the instruction says must be delivered.

New test: `SecurityTests::storedSessionNotSubstitutedForANamedCallerCookieWithAnUnusualValue`. It
seeds the store with `SID=storeval`, then sends `Cookie: SID=user"B; x=1` and `Cookie: SID=user B; x=1`,
each with a fresh client. It asserts that no request to `/first` carries `storeval`, and that every
such request carries `x=1`. On the vulnerable build, the stored cookie replaces the header (the test fails).

New patch check: `checks/fix_strict_decode.patch` (`security_fail`). It is `alt_correct_fix.patch`
with the serialiser's caller-header decoder switched from LAX to STRICT. That is the
decode-and-re-encode shape the audit described: the strict decoder silently drops `SID=user"B`, so
the caller no longer "names" SID, and the store's `SID=storeval` is added. Result: security 5/6
(only the new test fails), functional 6/6, reward 0.8333.

Gate (`build/slot.py 3 -- builder/gate.py async-http-client`): **PASSED**. nop: security 0/6
fail-as-expected, functional 6/6. Oracle 1.0 twice. fix_hops_only 0.3333 (now also fails the new
test), fix_serialiser_only 0.0 (functional_fail), alt_correct_fix 1.0 (it decodes LAX and its STRICT
encoder throws on the unusual value, which counts as refusing the request, so it passes), fix_strict_decode 0.8333.

Regrade: none of the six trial folders under `~/.tb-graders/cwe/jobs/async-http-client-*/*/`
has `final-code/changes.patch`, so `regrade_from_code.py` cannot run on any of them. Nothing was regraded.

| trial | old | new | failing tests |
|---|---|---|---|
| deepseek-1013-214752/NnexR8M | 1.0 | not regraded (no final-code) | - |
| deepseek-1013-214752/QGRAtMd | 1.0 | not regraded (no final-code) | - |
| deepseek-1013-214752/uGhFbba | 1.0 | not regraded (no final-code) | - |
| mimo-1013-214753/diNL3jn | 0.0 | not regraded (no final-code; tests only tightened) | - |
| mimo-1013-214753/td32DYY | no result.json | not eligible | - |
| mimo-1013-214753/tfkenPc | 1.0 | not regraded (no final-code) | - |

Expected effect on uGhFbba, from its audit (transcript.md:307,316): the fix folds the caller header
into the cookie list with `config.isUseLaxCookieEncoder() ? LAX : STRICT`, which is STRICT by default,
and then removes the header. That is the same defect `fix_strict_decode.patch` has, so it would very
likely fail the new test if its final code were harvested. Not run.
