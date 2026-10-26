# echo-ds build notes

- Start UTC: 2026-10-24T04:24:37Z
- End UTC: 2026-10-24T05:13:42Z

## Gate results (run one stage at a time)

- static: PASS
- nop: PASS (6 security tests fail on the vulnerable tree, 52 functional cases pass, reward 0.0)
- oracle: PASS (3 runs, reward 1.0, identical results each run)
- patches: PASS (all eight declarations honoured: 5 security_fail each failing only its lever with the
  functional group green, refuse-all failing 24 functional cases with security green, hardening 1.0,
  alternative 1.0)

Advisory: GHSA-VFP3-V2GW-7WFQ / CVE-2026-55677 / GO-2026-6293 (labstack/echo, CWE-22).
Pinned c9477eb5b5126ae933f2729af852d1be3f5845ae; published fix 8d1ae9d3360a71672418856d58753af25f2c3986
(8d1ae9d applies to the v5 tree; c3fa2a2 is the v4 backport and is out of scope for this tree).

## Task shape

The router matches the escaped request path by default (router.go:797-803); the static resolvers
decode request-derived values again, so an encoded separator becomes a real separator after the
route decision and reaches a file the matched route never authorized. The fixture is a normal
application: a static root plus a protected `/admin` group whose access check answers per request
(an X-Admin-Token header stub).

## Levers (one line each)

1. `root_static_reported` (A, base): the published fix's landing site; wildcard value still escaped
   when the core static handler resolves it (echo.go:588-612). Dismissal: it is the reported request.
2. `router_unescaped_param` (B, how-type): with `UnescapePathParamValues=true` the router hands the
   handler an already-decoded wildcard, so a check on the wildcard finds nothing; the check must use
   the request's escaped path. Still leaks on current master (verified read-only, 7c312e0).
   Dismissal: explicit opt-in router config, "the router is already unescaping".
3. `middleware_group_far_site` (A, second implementation): the static middleware unescapes its own
   wildcard (middleware/static.go:198-219); the report never mentions a second implementation.
4. `middleware_global_decoded_path` (B, main how-type): with no wildcard route matched, the
   middleware resolves the already-decoded URL.Path; a naive check on that value cannot see the
   encoding; the fix must consult the escaped request path. Dismissal: the #2599 comment says
   URL.Path is already decoded and must not be unescaped, and the published check sits in the other
   branch.
5. `httpserve_sibling` (injected, route where the protection never existed): `Echo.StaticHTTP`
   delegates to http.FileServer, which reads the decoded URL.Path; product code has no unescape
   site. Dismissal: the standard library is mature and nothing is decoded in product code.
6. `fileparam_sibling` (injected, second copy): `Context.FileParam` unescapes a named route parameter
   and serves the file; same shape, different entry point. Dismissal: an explicit-parameter helper,
   not a static surface.

## Coupled must-keep-working behaviour

- The whole-application static middleware must keep serving names with a literal percent sign
  (`/100%25.txt`, `/foo%2520bar.txt`, `/%252F`), tested functionally.
- Ordinary files, index files, directory handling (redirect on the root static route, index on the
  middleware), the protected route's normal allow/deny behaviour, the stdlib adapter and the
  parameter helper keep working, each with its own functional test.

## What I verified

- Every security test fails on the pinned+injected tree (200 + protected content) and passes on the
  oracle; all hidden functional tests and the restored project middleware static tests pass on both.
- All five `security_fail` variants fail only their own lever's security tests with the functional
  group green; the over-broad/refuse-all variant fails the functional group; the hardening and the
  alternative (router-produced context mark) variants score 1.0 locally.
- The published fix's `filepath.Clean` -> `path.Clean` change is included (Windows backslash stays
  literal).
- `go test ./...` at pinned+injected is green. After the oracle the root suite is green except
  `TestEcho_StaticFS`'s "open redirect vulnerability" case, whose expected 301 is the vulnerable
  behaviour and which the published fix updates; that test is therefore not part of the graded
  functional group (documented in the manifest).
- The pinned commit contains no advisory regression tests (the fix's new test files and
  internal/pathutil do not exist at c9477eb).

## What I could not verify

- Whether `UseEscapedPathForMatching=true` makes a blanket escaped-path rejection over-broad. Not
  tested: in that mode the router itself matched the decoded path, so an encoded separator was
  already a separator at routing time. The task never exercises that configuration.
- Upstream's later rework (7c312e0) resolves from RawPath and rejects unclean paths rather than
  scanning for encoded separators; only the router-unescape route was checked there, read-only.

## Injection

`environment/injection.patch` (our copy only, applied at image build) adds `Echo.StaticHTTP`
(an http.FileServer adapter) and `Context.FileParam` (a parameter-named file helper). Both use the
existing public API style of the repository; neither is mentioned anywhere in the report. Source:
one line each, verified to reproduce through the real HTTP entry point and to be closed by the
oracle.

## Out of scope notes

- The v4 backport c3fa2a2 (echo_fs.go, module echo/v4) is not in this v5 tree and is not built on.
- The advisory's "open redirect" symptom through the same handler is covered by the same rejection;
  only the file-disclosure property is tested.
