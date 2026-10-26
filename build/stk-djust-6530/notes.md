# stk-djust-6530 build notes

- Start: 2026-10-26T02:18:30Z
- End: 2026-10-26T04:04:19Z
- Repo: `djust-org/djust`, pinned `3b369d0c1a5e1efd6d63ad244ef5874440675bd2`
  (direct parent of the published fix `1ae8aa9246b80477de7ddc4d90319a3b267bef04`).
- The published fix touches only `python/djust/websocket.py` (plus docs/CHANGELOG
  and its own regression test, which the pinned tree does not contain).

## Levers (one line each)

- **T1 (A, both)** — an authorisation refusal on a WebSocket mount sends the
  navigate frame and returns, leaving the unmounted view as the consumer's event
  target with the socket open (`websocket.py:1795,1979-1986,2722-2724`; also
  reached through `live_redirect_mount` at `websocket.py:4290`). Reason to
  dismiss: the navigate frame looks like the handled response, and the wire
  snapshot pins it.
- **T2 (A, both)** — the `on_mount` hook redirect has the identical exit
  (`websocket.py:2002-2007`, `hooks.py:71-88`). Reason to dismiss: it is
  developer-hook control flow, and a second redirect branch twenty lines below
  the first looks like the same code already fixed.
- **T3 (A, mimo)** — the coupled value: the consumer has one event slot and a
  batch shares one socket, so the refusal must neither close the socket nor leave
  the denied view in the slot (`websocket.py:2524-2537,2571-2596,2671-2679`).
  Reason to dismiss: close is the obvious fix and `mount_batch` reads as a
  lazy-hydration optimisation.
- **T4 (B, deepseek)** — the streaming transport's own mount implementation
  registers the view on the session before the auth check, and both denial
  shapes return with it installed (`sse.py:229,236-244,352-355,785-810`). Reason
  to dismiss: the transport is the documented degraded fallback with a "legacy"
  event endpoint, and the advisory speaks only about WebSocket close codes.
- **T5 (B, both)** — the same mount logs an unexpected exception from the
  view-level check and continues (fail-open; `sse.py:245-246,248-269`). Reason to
  dismiss: a defensive `except` around a check reads as resilience.

Concepts: `[T1,T2]` (the reported base), `[T3]`, `[T4,T5]`.

## Verification performed (local, then container gate)

Reproduced every trap behaviourally on the pinned commit through the real
product entry points (channels `WebsocketCommunicator` for the WebSocket frame
protocol; `DjustSSEStreamView`/`DjustSSEEventView` for the streaming transport),
and verified every check patch:

| tree/patch | security | functional (hidden + project) |
|---|---|---|
| pinned | 15 fail | 14 + 128 pass |
| reference (oracle) | 15 pass | 14 + 128 pass |
| miss_mount_denial | 9 fail | all pass |
| miss_batch | 2 fail | all pass |
| miss_sse | 6 fail | all pass |
| miss_sse_failopen | 2 fail | all pass |
| upstream_fix (recall) | 8 fail | all pass |
| pass_alt | 15 pass | all pass |
| pass_hardening | 15 pass | all pass |
| ff_refuse_all | 15 pass | 1 functional fail |
| ff_close_in_batch | 2 fail | 3 functional fail |

Control task (`stk-djust-6530-control`): pinned 4 security fail, 5 + 128
functional pass; control reference 4 + 5 + 128 pass; `control_miss` 4 security
fail with functional passing; `control_overbroad` 1 functional fail.

The project's own affected-area tests (7 files, 128 tests) pass on the pinned
commit, the reference, the alternative and the hardening patch.

Container gate: static PASSED; nop PASSED (security 15/15 fail on the pinned
code, functional 142/142 pass, 0 skipped); oracle PASSED (3 runs, reward 1.0
each); patches PASSED (9/9 check patches behaved as declared: the four
security-fail misses, the recall patch, the two over-broad functional
failures, and the two pass variants at reward 1.0).
The control task's own gate: static PASSED; nop/oracle/patches pending.

## What I could not verify

- The advisory text is not in the worktree; the report wording comes from the
  screener/reader records and the published fix commit message, not from a
  document I read.
- The optional Rust renderer is not built in the image. All mount/auth/dispatch
  logic is pure Python and the project's own SSE tests already stub the render
  call, which the fixture views here do too. Project tests that need the Rust
  state backend (`python/djust/tests/test_ws_reconnect_state_1465.py`) are
  therefore excluded from the functional copies.
- `upstream_fix.patch` contains the published source change only; the published
  docs/CHANGELOG/test file are not part of it.
- The pipeline prompt points `stacking.reader_record` at
  `pipelines/stacking/out/reader/h4-6530.json`, but that path does not exist for
  this job; the real record is `pipelines/stacking/out/reader-ds/h4-6530.json`
  and the manifest points there.
- The reader record labels T1/T2 `type: neither`, which is not a legal manifest
  value. The manifest uses `both` for T1/T2/T5: the field records which target
  model the trap is expected to break, and the reported base is not where this
  task's difficulty lives.
- The `[T1,T2]` concept is the report's own base and is easy for both models by
  itself; the stacked difficulty rests on `[T3]` (MiMo-type) and `[T4,T5]`
  (DeepSeek-type), each hard/xhard on its own in the reader record.
- `present_in_latest` in the Pattern B register was read from `origin/main`
  (`94a24ca3`, 2026-10-22): the streaming mount was refactored onto the shared
  runtime with a fail-closed auth sequence, so both uncovered routes are gone
  there.

## Fairness notes

- The batch keep-working value is covered only by "everything that works today
  must keep working exactly as today", as the stacking rules require; the pinned
  wire-protocol snapshot test and the client's batch handling document it in the
  repository.
- The streaming route is covered only by the general property; a solver has to
  audit for other mount implementations. That is the intended DeepSeek-shaped
  lever.
- The image has no Rust renderer, so an agent that wants an end-to-end mount
  test must stub the render call (as the repository's own SSE tests do) or test
  the refusal before render. The graded flow itself needs no renderer.

## Outside this advisory's own protection

- The reader's T6 (per-event view-level re-check) and T7 (hook-redirect
  same-origin validation, CWE-601) were left out of the design: T6 contradicts
  the project's documented mount-time-only trade-off and T7 is a different
  protection class. Not built on.

## Other

- The project's `test_security_mount_validation.py` carries one test that
  upstream skips ("template rendering needs investigation"); it is omitted from
  the pristine copy because a skipped test cannot count as a pass in the oracle.
