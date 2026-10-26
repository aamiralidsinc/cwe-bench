# stk-mailpit-ghsa8r62 — build notes

Track: stacked (H3b). Patterns A+B. Slug `stk-mailpit-ghsa8r62`; control `stk-mailpit-ghsa8r62-control`.

Start (UTC): 2026-10-26T02:12:20Z. End (UTC): (filled in at the end).

## Gate results (stacked task)

- static: PASS (2026-10-26T03:04Z, after the final instruction edit re-run).
- nop: PASS — 7 security tests all fail on the pinned tree, 18 functional tests pass.
- oracle: PASS — 3 runs, reward 1.0, identical test results.
- patches: PASS — all 10 check patches reproduced their declared outcome (the per-concept
  security_fail checks fail only their own concept's tests; upstream_first_fix/upstream_fix leave
  the write routes open; unlisted_route leaves release open; functional_overbroad and
  preflight_breaks fail functional tests; alt_correct_fix and hardening score 1.0).
- One oracle attempt failed with an infrastructure error: Harbor's compose file under /tmp vanished
  while the shared VM's /tmp was churning; re-running with TMPDIR on the data disk passed. No task
  change was made for it.


## Levers (one line each)

- **T1 / concept 1 — live event stream admission** (advisory route). `server/websockets/client.go:37-38`
  installs an unconditional `CheckOrigin`; `server/server.go:199,333-336` serves the route outside the
  shared middleware. A browser attaches cached basic credentials to a cross-origin handshake, so the
  new-message summaries reach a page on another origin. Dismiss reason: the line is commented as
  deliberately allowing multi-domain use and the socket "only" pushes notifications.
- **T2 / concept 1 — route outside the shared middleware**. Same route; the shared middleware is where
  every other route gets its checks, and `ServeWs` repeats the basic-auth check, so a fix placed only
  in the middleware looks complete but never runs for the socket. Dismiss reason: the handler reads as
  self-contained.
- **T3 / concept 2 — raw request target instead of the dispatched path**. `server/server.go:287,291`
  makes its path decision on `r.RequestURI`; a percent-encoded spelling still routes to the handler but
  a lexical prefix test on the raw target misses it. Dismiss reason: the existing path-scoped block is
  the obvious template, and on its own it only adds a response header (fails closed).
- **T6 / concept 3 — state-changing requests have no origin decision**. `server/server.go:267-325`;
  `server/apiv1/send.go:45-49,186`; `server/apiv1/release.go:58-67,170`. A cross-origin simple POST is
  issued without a preflight and the handlers ignore Origin and content type. Dismiss reason: the API
  is unauthenticated by default for local scripts and CI, CORS response headers are assumed to cover it,
  and release needs relay configuration.

Concepts: `[[T1,T2],[T3],[T6]]`. DeepSeek-type: T2, T6. MiMo-type: T1, T3.

## What was verified

- Pinned commit `877a9159ceeaf380d5bb0e1d84017b24d2e7b361` is the first parent of A's fix
  `6f1f4f34c989` (`git rev-parse 6f1f4f34c989^`). B is `fbe5e006c3f1` (parent `69145ed`), a later
  commit on a refactored tree. A's source change is the removal of the `CheckOrigin` override; B's is
  `SetCheckOriginFunc` plus `r.URL.Path` on the existing path decision. The reference reproduces both
  as one predicate, adapted to the pin's code.
- The project's own tests (`go test ./server`) pass at the pinned commit and with the reference fix
  (verified on the host and inside the gate's oracle runs).
- The hidden suites drive the built daemon binary over loopback HTTP/SMTP. A fix wired in `Listen`
  (the shape of the published B fix) was checked explicitly and passes, so the tests exercise the real
  server at any layer rather than only `apiRoutes()`.
- Every check patch was run on the host before the gate: the oracle, alt and hardening pass; each
  concept miss fails its own security tests with functional all green; `upstream_first_fix` (A alone)
  and `upstream_fix` (A + the B-equivalent predicate) leave the write routes open; `unlisted_route`
  leaves release open; `functional_overbroad` and `preflight_breaks` fail only functional tests.
- Current upstream (`origin/master` `ce798cf`, v1.32.0) applies the origin decision to API paths and
  reads `r.URL.Path`, so both write-route and path-spelling protections are present there; both named
  fix commits for this candidate leave them out.

## What could not be verified

- The advisory texts themselves are not in the worktree; the mechanisms were taken from the two fix
  commits and the pinned code. B's exact diff does not cherry-pick onto the pin (it sits after routing
  and CORS refactors), so the reference uses an equivalent predicate (recorded in
  `stacking.history.pinned_rule`).
- Whether upstream regards the cross-origin simple POST routes as a published vulnerability: no
  advisory was found. They are recorded as `uncovered_upstream` (pattern B), and current master does
  now apply the origin check to API paths, which supports the reading that the protection was intended
  to cover them.
- `score_at_build` is copied from `pipelines/stacking/out/stack_scores_ds.tsv` (0.542); no scoring run
  was made by this build.

## Scope notes

- Out of scope, one line: the send-API handler temporarily clears the process-wide UI credential
  pointer (`server/server.go:216-253`), a concurrent-request race that the reader also flagged; it is
  not built on because a deterministic test would be flaky.
- The OPTIONS auth exemption (`server/server.go:299`) is a fairness constraint (preflight must stay
  credential-less), not a scored lever; the only OPTIONS handler returns a blank 200.
- Everything stays inside this advisory's protection and this repository at the pinned commit.

## Fairness

- The coupled values are tested functionally: same-origin UI, clients that send no origin, a non-root
  webroot, operator-configured origins (including the documented wildcard), and the credential-less
  preflight. The report covers them only through "Everything that works today keeps working exactly as
  today."
- No security test asserts one exact refusal status; a refusal is any client error plus no side effect.
- A daemon instance is started per test with a free database, so tests are independent and offline.
