# CWE-Bench — Results Ledger (internal)

_Generated 2026-10-16 09:40 from the latest evaluation run of each model on each task (64 attempts, 44 graded) in `data/04_eval_runs/` and the pipeline state. Regenerate with `python -m src.common.results_report` (stage 5 does it after every run)._

**Breaker** = pass@3 = 0 on **both** DeepSeek V4.1 Flash (max) and MiMo-V2.6-Pro. A run is solved at reward 1.0. A partial fix (some attack variants still open) and a fix that breaks legitimate behaviour are failures. A run that hit the 2-hour agent limit is **timed out and not counted as a failure**. Runs that were never graded (stopped early, crashed, lost to a connection drop) are left out. Each model is judged on its latest evaluation run; the agent harness (terminus-2 or Claude Code) is shown next to each result.

## Executive summary

**1 accepted out of 24 trialed tasks.** In 5 task(s) at least one model did not solve it (see the second table for which task type broke which model).

## All trialed tasks

| # | Task | Language | CWE | Task type | DeepSeek | MiMo | Final verdict | How it failed | Image build (cached / longest) |
|---|---|---|---|---|---|---|---|---|---|
| 1 | msgpack5 (GHSA-24ch-f2g6-9hhh) | JavaScript | 674 | resource exhaustion (DoS); local fix (2 files / 2 dirs / 40 lines) | SOLVED 1/1 — Claude Code | stopped early (not graded) — Claude Code | REJECTED: DeepSeek solved | — | 11 s / 0.2 min |
| 2 | @typespec/openapi3 (GHSA-2q42-4q24-7rgv) | TypeScript | 22, 73 | path / file handling; wide multi-layer fix (6 files / 5 dirs / 53 lines) | SOLVED 1/1 — Claude Code | stopped early (not graded) — Claude Code | REJECTED: DeepSeek solved | — | 165 s / 2.8 min |
| 3 | GitPython (GHSA-3wxw-xv34-2frg) | Python | 88, 200 | injection (code / command / markup) + information exposure; wide multi-layer fix (5 files / 4 dirs / 55 lines) | SOLVED 1/1 — Claude Code | stopped early (not graded) — Claude Code | REJECTED: DeepSeek solved | — | 72 s / 1.3 min |
| 4 | pypdf (GHSA-5jq2-8x83-x246) | Python | 400, 407 | resource exhaustion (DoS); multi-file fix (4 files / 2 dirs / 117 lines) | SOLVED 1/1 — Claude Code | stopped early (not graded) — Claude Code | REJECTED: DeepSeek solved | — | 28 s / 0.5 min |
| 5 | pyload-ng (GHSA-68w4-83fh-f2w8) | Python | 287 | auth / session / credentials; local fix (2 files / 2 dirs / 9 lines) | SOLVED 1/1 — Claude Code | stopped early (not graded) — Claude Code | REJECTED: DeepSeek solved | — | 14 s / 0.2 min |
| 6 | @modelcontextprotocol/sdk (GHSA-6qxp-vccf-f47h) | TypeScript | 345, 522 | auth / session / credentials; wide multi-layer fix (8 files / 4 dirs / 174 lines) | failed 0/3 (0.92 each, stopped on its own) — Claude Code | timed out 3/3 (0.50 each) — terminus-2 | REJECTED: MiMo timed out, which is not counted as a failure | DeepSeek: partial fix: closed 5 of 6 attack variants in all 3 runs and stopped on its own (it thought it was done); left open every time: schema_roundtrip_keeps_binding — MiMo: ran out of the 120-min limit in 3/3 runs with 0 of 6 attack variants closed; not counted as a failure | 12 s / 0.3 min |
| 7 | datamodel-code-generator (GHSA-77xj-x4rm-935c) | Python | 22, 73 | path / file handling; local fix (1 files / 1 dir / 31 lines) | SOLVED 1/1 — Claude Code | stopped early (not graded) — Claude Code | REJECTED: DeepSeek solved | — | 30 s / 0.5 min |
| 8 | pymongo (GHSA-8fvv-fgr5-f8ch) | Python | 943 | other; multi-file fix (3 files / 3 dirs / 74 lines) | SOLVED 1/1 — Claude Code | stopped early (not graded) — Claude Code | REJECTED: DeepSeek solved | — | 15 s / 0.2 min |
| 9 | httpx2 (GHSA-8xx6-hgc6-gc2m) | Python | 409 | resource exhaustion (DoS); multi-file fix (4 files / 1 dir / 238 lines) | SOLVED 1/1 — Claude Code | stopped early (not graded) — Claude Code | REJECTED: DeepSeek solved | — | 21 s / 0.4 min |
| 10 | pyload-ng (GHSA-9q47-3cm2-2rp8) | Python | 290 | auth / session / credentials; multi-file fix (4 files / 2 dirs / 58 lines) | SOLVED 1/1 — Claude Code | stopped early (not graded) — Claude Code | REJECTED: DeepSeek solved | — | 37 s / 0.6 min |
| 11 | banks (GHSA-hmq2-7hp6-7crh) | Python | 20 | parsing / type confusion; wide multi-layer fix (13 files / 3 dirs / 232 lines) | SOLVED 1/1 — Claude Code | stopped early (not graded) — Claude Code | REJECTED: DeepSeek solved | — | 17 s / 0.3 min |
| 12 | stream-json (GHSA-hqr4-qq8f-hg3x) | JavaScript | 407 | resource exhaustion (DoS); wide multi-layer fix (10 files / 4 dirs / 286 lines) | SOLVED 1/1 — Claude Code | stopped early (not graded) — Claude Code | REJECTED: DeepSeek solved | — | 37 s / 0.6 min |
| 13 | hono (GHSA-hxh3-vqpv-xpqv) | TypeScript | 79 | injection (code / command / markup); wide multi-layer fix (6 files / 3 dirs / 156 lines) | failed 0/3 (0.83/0.94/0.83, stopped on its own) — Claude Code | failed 0/3 (0.89/0.94/0.89, stopped on its own) — Claude Code | **ACCEPTED**: both models failed every run | DeepSeek: partial fix (and broke legitimate behaviour in 1 of 3 runs: runtime-tests/node/index.test.ts > stream > Should call onAbort) in all 3 runs and stopped on its own (it thought it was done); left open every time: render_to_string_escapes_array_root — MiMo: partial fix (and broke legitimate behaviour in 1 of 3 runs: runtime-tests/node/index.test.ts > stream > Should call onAbort) in all 3 runs and stopped on its own (it thought it was done); left open every time: render_to_string_escapes_array_root | 54 s / 1.4 min |
| 14 | devalue (GHSA-j22f-vq7h-c4qm) | JavaScript | 200, 226 | information exposure; multi-file fix (4 files / 1 dir / 40 lines) | SOLVED 1/1 — terminus-2 | stopped early (not graded) — terminus-2 | REJECTED: DeepSeek solved | — | 8 s / 0.1 min |
| 15 | ip-address (GHSA-j6r3-76f7-8jcv) | TypeScript | 697, 843 | parsing / type confusion; multi-file fix (3 files / 1 dir / 25 lines) | SOLVED 1/1 — terminus-2 | SOLVED 1/1 — terminus-2 | REJECTED: both solved | — | 9 s / 0.2 min |
| 16 | pyload-ng (GHSA-jq7h-wrvp-3rgx) | Python | 613 | auth / session / credentials; wide multi-layer fix (5 files / 4 dirs / 111 lines) | SOLVED 1/1 — terminus-2 | timed out 1/1 (0.67) — terminus-2 | REJECTED: DeepSeek solved | MiMo: ran out of the 30-min limit in 1/1 runs with 0 of 7 attack variants closed; not counted as a failure | 15 s / 0.3 min |
| 17 | devalue (GHSA-mcm9-63f2-9j32) | JavaScript | 400, 409 | resource exhaustion (DoS); multi-file fix (3 files / 3 dirs / 141 lines) | SOLVED 1/1 — Claude Code | stopped early (not graded) — Claude Code | REJECTED: DeepSeek solved | — | 10 s / 0.2 min |
| 18 | nltk (GHSA-p4rw-rvv2-7xwr) | Python | 22, 59 | path / file handling; wide multi-layer fix (10 files / 3 dirs / 236 lines) | failed 0/3 (0.93 each, stopped on its own) — Claude Code | SOLVED 1/3 — Claude Code | REJECTED: MiMo solved | DeepSeek: partial fix: closed 4 of 5 attack variants in all 3 runs and stopped on its own (it thought it was done); left open every time: toolbox_symlink_escape | 45 s / 0.9 min |
| 19 | adm-zip (GHSA-p634-w6r4-rjp2) | JavaScript | 436, 696 | parsing / type confusion; local fix (2 files / 2 dirs / 11 lines) | SOLVED 1/1 — terminus-2 | SOLVED 1/1 — terminus-2 | REJECTED: both solved | — | 4 s / 0.1 min |
| 20 | pydantic-ai (GHSA-q2xc-rrxj-58x9) | Python | 346, 350 | auth / session / credentials; wide multi-layer fix (6 files / 3 dirs / 222 lines) | SOLVED 1/1 — Claude Code | stopped early (not graded) — Claude Code | REJECTED: DeepSeek solved | — | 36 s / 0.6 min |
| 21 | @payloadcms/plugin-import-export (GHSA-qf28-8hc6-vwrp) | TypeScript | 1321 | deserialization / prototype pollution; wide multi-layer fix (16 files / 10 dirs / 344 lines) | SOLVED 1/1 — Claude Code | stopped early (not graded) — Claude Code | REJECTED: DeepSeek solved | — | 15 s / 0.3 min |
| 22 | pypdf (GHSA-v247-6f48-mgcj) | Python | 400, 407 | resource exhaustion (DoS); local fix (2 files / 2 dirs / 93 lines) | SOLVED 1/1 — terminus-2 | stopped early (not graded) — terminus-2 | REJECTED: DeepSeek solved | — | 10 s / 0.2 min |
| 23 | undici (GHSA-vp8m-p9jh-q5pm) | JavaScript | 346 | auth / session / credentials; wide multi-layer fix (10 files / 5 dirs / 120 lines) | SOLVED 1/2 — Claude Code | failed 0/1 (0.93, stopped on its own) — Claude Code | REJECTED: DeepSeek solved | MiMo: closed the hole but broke legitimate behaviour (storage_with_custom_lookup_same_host) in its run and stopped on its own (it thought it was done) | 73 s / 1.4 min |
| 24 | nltk (GHSA-w3v8-gmh9-3wv7) | Python | 1333 | resource exhaustion (DoS); wide multi-layer fix (7 files / 4 dirs / 289 lines) | SOLVED 1/1 — Claude Code | stopped early (not graded) — Claude Code | REJECTED: DeepSeek solved | — | 21 s / 0.3 min |

## What breaks which model

Every task where a model did not solve it. A task that breaks only one model is still evidence: it shows which task type that model cannot handle. The task generator reads this as `data/knowledge/model_failure_map.md`.

| Task | Task type | Entry point | Model | Result | How it failed | Other model |
|---|---|---|---|---|---|---|
| @modelcontextprotocol/sdk (GHSA-6qxp-vccf-f47h) | auth / session / credentials; wide multi-layer fix (8 files / 4 dirs / 174 lines) | Exported client OAuth API fetchToken()/auth() called with a pinned credential provider … | DeepSeek | FAILED | partial fix: closed 5 of 6 attack variants in all 3 runs and stopped on its own (it thought it was done); left open every time: schema_roundtrip_keeps_binding | MiMo also did not solve it (timed out 3/3 (0.50 each)) |
| @modelcontextprotocol/sdk (GHSA-6qxp-vccf-f47h) | auth / session / credentials; wide multi-layer fix (8 files / 4 dirs / 174 lines) | Exported client OAuth API fetchToken()/auth() called with a pinned credential provider … | MiMo | timed out (not counted) | ran out of the 120-min limit in 3/3 runs with 0 of 6 attack variants closed; not counted as a failure | DeepSeek also did not solve it (failed 0/3 (0.92 each, stopped on its own)) |
| hono (GHSA-hxh3-vqpv-xpqv) | injection (code / command / markup); wide multi-layer fix (6 files / 3 dirs / 156 lines) | hono/jsx server-side rendering: a JSX tree built with the public … | DeepSeek | FAILED | partial fix (and broke legitimate behaviour in 1 of 3 runs: runtime-tests/node/index.test.ts > stream > Should call onAbort) in all 3 runs and stopped on its own (it thought it was done); left open every time: render_to_string_escapes_array_root | MiMo also did not solve it (failed 0/3 (0.89/0.94/0.89, stopped on its own)) |
| hono (GHSA-hxh3-vqpv-xpqv) | injection (code / command / markup); wide multi-layer fix (6 files / 3 dirs / 156 lines) | hono/jsx server-side rendering: a JSX tree built with the public … | MiMo | FAILED | partial fix (and broke legitimate behaviour in 1 of 3 runs: runtime-tests/node/index.test.ts > stream > Should call onAbort) in all 3 runs and stopped on its own (it thought it was done); left open every time: render_to_string_escapes_array_root | DeepSeek also did not solve it (failed 0/3 (0.83/0.94/0.83, stopped on its own)) |
| pyload-ng (GHSA-jq7h-wrvp-3rgx) | auth / session / credentials; wide multi-layer fix (5 files / 4 dirs / 111 lines) | HTTP POST /api/set_user_permission and /api/change_password (REST API blueprint, session- … | MiMo | timed out (not counted) | ran out of the 30-min limit in 1/1 runs with 0 of 7 attack variants closed; not counted as a failure | DeepSeek solved it (solved in 57 steps, 12 min) |
| nltk (GHSA-p4rw-rvv2-7xwr) | path / file handling; wide multi-layer fix (10 files / 3 dirs / 236 lines) | Loading a corpus through the public corpus-reader APIs over a directory that contains a … | DeepSeek | FAILED | partial fix: closed 4 of 5 attack variants in all 3 runs and stopped on its own (it thought it was done); left open every time: toolbox_symlink_escape | MiMo solved it (solved in 90 steps, 61 min) |
| undici (GHSA-vp8m-p9jh-q5pm) | auth / session / credentials; wide multi-layer fix (10 files / 5 dirs / 120 lines) | Public undici API: dispatcher.request({origin?, path, method}) on … | MiMo | FAILED | closed the hole but broke legitimate behaviour (storage_with_custom_lookup_same_host) in its run and stopped on its own (it thought it was done) | DeepSeek solved it (solved in 164 steps, 49 min) |

## Failure details

Every task a model FAILED (a counted failure: graded, below 1.0, not a timeout), most important first. Solved tasks are only in the tables above. Each attempt is listed in the order it ran; *left open* = hidden security tests still failing, *broke* = functional or enforced existing repo tests that failed.

### hono (GHSA-hxh3-vqpv-xpqv) - ACCEPTED: both models failed every run

- **Task type:** injection (code / command / markup); wide multi-layer fix (6 files / 3 dirs / 156 lines); CWE 79; TypeScript
- **Entry point:** hono/jsx server-side rendering: a JSX tree built with the public jsx()/Suspense/ErrorBoundary/Context.Provider APIs and rendered to the HTTP response body via renderToString / renderToReadableStream (or a node's toString()); an untrusted string placed as child content is the untrusted input.
- **Reference fix (source files):** `src/jsx/base.ts`, `src/jsx/components.ts`, `src/jsx/context.ts`, `src/jsx/dom/server.ts`, `src/jsx/intrinsic-element/components.ts`, `src/jsx/streaming.ts`

| Model | # | Score | Security | Functional | Existing | Left open | Broke | Source files changed | Time | Turns | Ended |
|---|---|---|---|---|---|---|---|---|---|---|---|
| DeepSeek | 1 | 0.83 | 3/6 | 6/6 | 493/494 | render_to_stream_escapes_string_root, render_to_string_escapes_array_root, render_to_string_escapes_string_root | runtime-tests/node/index.test.ts > stream > Should call onAbort | `src/jsx/base.ts`, `src/jsx/components.ts`, `src/jsx/context.ts`, `src/jsx/streaming.ts` | 35 min | 111 | failed - stopped on its own |
| DeepSeek | 2 | 0.83 | 3/6 | 6/6 | 494/494 | render_to_stream_escapes_string_root, render_to_string_escapes_array_root, render_to_string_escapes_string_root | - | `src/jsx/base.ts`, `src/jsx/components.ts`, `src/jsx/context.ts`, `src/jsx/streaming.ts` | 28 min | 77 | failed - stopped on its own |
| DeepSeek | 3 | 0.94 | 5/6 | 6/6 | 494/494 | render_to_string_escapes_array_root | - | `src/jsx/base.ts`, `src/jsx/components.ts`, `src/jsx/context.ts`, `src/jsx/dom/server.ts`, `src/jsx/streaming.ts`, `src/utils/html.ts` | 25 min | 110 | failed - stopped on its own |
| MiMo | 1 | 0.89 | 4/6 | 6/6 | 494/494 | render_to_string_escapes_array_root, render_to_string_escapes_string_root | - | `src/jsx/base.ts`, `src/jsx/components.ts`, `src/jsx/context.ts`, `src/jsx/streaming.ts` | 57 min | 67 | failed - stopped on its own |
| MiMo | 2 | 0.94 | 5/6 | 6/6 | 493/494 | render_to_string_escapes_array_root | runtime-tests/node/index.test.ts > stream > Should call onAbort | `src/jsx/base.ts`, `src/jsx/components.ts`, `src/jsx/context.ts`, `src/jsx/dom/server.ts`, `src/jsx/streaming.ts`, `src/utils/html.ts` | 37 min | 80 | failed - stopped on its own |
| MiMo | 3 | 0.89 | 4/6 | 6/6 | 494/494 | render_to_string_escapes_array_root, render_to_string_escapes_string_root | - | `src/jsx/base.ts`, `src/jsx/components.ts`, `src/jsx/context.ts`, `src/jsx/streaming.ts` | 66 min | 112 | failed - stopped on its own |

#### Summary
ACCEPTED - both models failed all 3 attempts (DeepSeek 0.83/0.83/0.94, MiMo 0.89/0.94/0.89, Claude Code agent), every run stopped on its own (no timeout). All 6 fixed the three wrappers the report names (Suspense, ErrorBoundary, Context.Provider) and all 6 left `renderToString([unsafe, [unsafe]])` unescaped.

#### Why DeepSeek failed
- **The diagnosis was right in all 3 runs** and close to the report's own wording, so the failures are about **scope**,
  not understanding.
- **It found the second renderer every time and declined to fix it in 2 of 3 runs.** It read `src/jsx/dom/server.ts`
  and the existing test expecting `renderToString('Hono')` to return `'Hono'`, then: "top-level string = trusted HTML
  (like `c.html(str)`)... I'll leave top-level semantics unchanged." Run 3 confirmed the hole experimentally ("bare
  string: raw") and still left it: "Top-level entry, leave as is (like c.html)." It read the report's "a bare string
  must still be renderable" as "do not escape".
- **The run that did fix `renderToString` (0.94)** guarded it with `typeof element === 'string'` only, although it had
  already written an array-aware helper for the wrappers. Its own tests covered a bare string, not an array.
- Stopped after its own 9-15 wrapper-focused tests, lint and build: "The fix is complete." (25-35 min, 79-112 turns.)

#### Why MiMo failed
- **It explored narrowly.** It found `dom/server.ts` in only 1 of 3 runs: one run's first grep ended in
  `| grep -v "dom/"` and it then claimed "there's only `renderToReadableStream` and JSXNode.toString()" (false); another
  asked "is there a `renderToString`?" twice and never searched.
- **The run that found it (0.94)** fixed the two entry points unevenly: `renderToReadableStream` through its
  array-aware helper, `renderToString` with a string-only check - and reported full coverage.
- Stopped after ticking off the report's bullet points with 17-21 tests of its own (37-66 min).

#### Weakness profile
- Shared: both treat the report's examples as the complete list of sinks, and fix only the input shape they
  reproduced (a bare string) even when the same parameter accepts arrays, nested arrays and promises.
- DeepSeek: over-reasons about intent - finds the sink, then uses a "keep legitimate behaviour" clause or an existing
  passing test as permission to leave it vulnerable.
- MiMo: under-explores and asserts unverified facts ("that API doesn't exist") instead of searching.

#### Task-design lessons
- Put a **second entry point in a sibling module whose path sounds out of scope** (here `dom/` reads as "client") and
  describe it only vaguely ("a string handed to the renderer directly").
- Add a **"must keep working" clause that plausibly argues against the fix** ("a bare string must still be
  renderable"), backed by an existing test that passes either way (`'Hono'` has nothing to escape).
- **Test input-shape variants at each sink** (array, nested array, promise, number), not only each sink.
- Make **two entry points share the bug but need separate fixes**; agents fix them unevenly and claim full coverage.
- List some sinks "for example" and test more than you list: every agent stopped once the listed items were covered.

### @modelcontextprotocol/sdk (GHSA-6qxp-vccf-f47h) - REJECTED: MiMo timed out, which is not counted as a failure

- **Task type:** auth / session / credentials; wide multi-layer fix (8 files / 4 dirs / 174 lines); CWE 345, 522; TypeScript
- **Entry point:** Exported client OAuth API fetchToken()/auth() called with a pinned credential provider against an attacker-chosen authorization server
- **Reference fix (source files):** `examples/guides/clients/machine-auth.examples.ts`, `examples/oauth-client-credentials/client.ts`, `examples/oauth/dualModeAuth.ts`, `packages/client/src/client/auth.ts`, `packages/client/src/client/authErrors.ts`, `packages/client/src/client/authExtensions.examples.ts`, `packages/client/src/client/authExtensions.ts`, `packages/client/src/client/crossAppAccess.ts`, `packages/core-internal/src/shared/authUtils.ts`, `packages/core/src/auth.ts`, `packages/server-legacy/src/auth/providers/proxyProvider.ts`

| Model | # | Score | Security | Functional | Existing | Left open | Broke | Source files changed | Time | Turns | Ended |
|---|---|---|---|---|---|---|---|---|---|---|---|
| DeepSeek | 1 | 0.92 | 5/6 | 7/7 | - | schema_roundtrip_keeps_binding | - | `packages/client/src/client/auth.ts`, `packages/client/src/client/authErrors.ts` | 15 min | 88 | failed - stopped on its own |
| DeepSeek | 2 | 0.92 | 5/6 | 7/7 | - | schema_roundtrip_keeps_binding | - | `packages/client/src/client/auth.ts` | 9 min | 80 | failed - stopped on its own |
| DeepSeek | 3 | 0.92 | 5/6 | 7/7 | - | schema_roundtrip_keeps_binding | - | `packages/client/src/client/auth.ts` | 14 min | 73 | failed - stopped on its own |
| MiMo | 1 | 0.50 | 0/6 | 7/7 | - | bound_client_secret_not_sent_to_other_as, bound_credentials_without_metadata, lazily_supplied_client_info_checked, private_key_jwt_not_sent_to_other_as, schema_roundtrip_keeps_binding, static_assertion_not_sent_to_other_as | - | - | 120 min | 46 | timed out (not counted) |
| MiMo | 2 | 0.50 | 0/6 | 7/7 | - | bound_client_secret_not_sent_to_other_as, bound_credentials_without_metadata, lazily_supplied_client_info_checked, private_key_jwt_not_sent_to_other_as, schema_roundtrip_keeps_binding, static_assertion_not_sent_to_other_as | - | - | 120 min | 49 | timed out (not counted) |
| MiMo | 3 | 0.50 | 0/6 | 7/7 | - | bound_client_secret_not_sent_to_other_as, bound_credentials_without_metadata, lazily_supplied_client_info_checked, private_key_jwt_not_sent_to_other_as, schema_roundtrip_keeps_binding, static_assertion_not_sent_to_other_as | - | - | 120 min | 56 | timed out (not counted) |

#### Summary
DeepSeek failed 3/3 (0.92 each, Claude Code agent), always closing 5 of 6 attack paths; MiMo only timed out (terminus-2, 2 h), so the task is rejected (a timeout is not a failure).

#### Why DeepSeek failed
- **Same diagnosis and fix in all 3 attempts:** only `auth()` enforced the issuer binding while the lower-level token
  entry points (`fetchToken`, `exchangeAuthorization`, `refreshAuthorization`, `executeTokenRequest`) did not; it put a
  guard in the shared token-request path, covering every *call path* (mostly `packages/client/src/client/auth.ts`).
- **The missed path is a data path, not a call path:** the SDK's own Zod schemas `.strip()` unknown keys, so a
  credential saved and reloaded through `OAuthClientInformationSchema` loses its `issuer` stamp and looks unbound. None
  of the attempts changed `packages/core/src/auth.ts`, where the schemas live.
- **It saw the gap and argued itself out of it:** it mentioned the schemas or `.strip()` in 12-18 turns per attempt -
  "maybe `.strip()` removes `issuer`..." then "The mention of the schemas probably just guards against an
  implementation that ... validates strictly". The report lists schema-parsed persistence under *legitimate use that
  must keep working*; it read that as a constraint, not as an attack surface. An in-code comment ("intentionally absent
  from the wire-response schema") reinforced it.
- **Stopped when its own tests passed** ("Fix complete and verified end-to-end"), 9-15 min, well inside the limit.

#### Why MiMo failed
- Not a counted failure: with the older terminus-2 harness it ran out of the 2-hour limit in all 3 attempts with 0 of
  6 attack paths closed. It was not re-run with Claude Code.

#### Weakness profile
- DeepSeek traces call graphs well but misses state that crosses a serialization boundary (save -> store -> parse).
- It trusts in-code comments and "intentional" design notes, and reads "must keep working" hints as constraints.
- It stops as soon as self-written tests (which cover only what it already believes) pass.

#### Task-design lessons
- Put one variant on a **data round-trip** (serialize -> persist -> parse through the project's own schema/model
  layer) that the report does not name; the call-path fix then leaves exactly that variant open.
- Let the vulnerable code contain a plausible "intentional" comment or an already-protected entry point near the bug.
- Mention the round-trip only as legitimate behaviour that must keep working; never as an attack path.

### nltk (GHSA-p4rw-rvv2-7xwr) - REJECTED: MiMo solved

- **Task type:** path / file handling; wide multi-layer fix (10 files / 3 dirs / 236 lines); CWE 22, 59; Python
- **Entry point:** Loading a corpus through the public corpus-reader APIs over a directory that contains a symlink, e.g. LinThesaurusCorpusReader(root), CrubadanCorpusReader(root, r'.*\.txt').lang_freq(lang), MTECorpusReader(root, r'.*\.xml').words(), nltk.toolbox.ToolboxData(path).
- **Reference fix (source files):** `nltk/chunk/named_entity.py`, `nltk/corpus/reader/crubadan.py`, `nltk/corpus/reader/ipipan.py`, `nltk/corpus/reader/lin.py`, `nltk/corpus/reader/mte.py`, `nltk/corpus/reader/nkjp.py`, `nltk/corpus/reader/pl196x.py`, `nltk/corpus/reader/xmldocs.py`, `nltk/pathsec.py`, `nltk/toolbox.py`

| Model | # | Score | Security | Functional | Existing | Left open | Broke | Source files changed | Time | Turns | Ended |
|---|---|---|---|---|---|---|---|---|---|---|---|
| DeepSeek | 1 | 0.93 | 4/5 | 5/5 | 118/118 | toolbox_symlink_escape | - | `nltk/corpus/reader/api.py`, `nltk/corpus/reader/crubadan.py`, `nltk/corpus/reader/mte.py`, `nltk/corpus/reader/panlex_lite.py` | 33 min | 100 | failed - stopped on its own |
| DeepSeek | 2 | 0.93 | 4/5 | 5/5 | 118/118 | toolbox_symlink_escape | - | `nltk/corpus/reader/crubadan.py`, `nltk/corpus/reader/lin.py`, `nltk/corpus/reader/mte.py`, `nltk/corpus/reader/nkjp.py`, `nltk/corpus/reader/panlex_lite.py`, `nltk/corpus/reader/xmldocs.py`, `nltk/data.py` | 26 min | 84 | failed - stopped on its own |
| DeepSeek | 3 | 0.93 | 4/5 | 5/5 | 118/118 | toolbox_symlink_escape | - | `nltk/corpus/reader/api.py`, `nltk/corpus/reader/crubadan.py`, `nltk/corpus/reader/lin.py`, `nltk/corpus/reader/mte.py`, `nltk/corpus/reader/panlex_lite.py`, `nltk/corpus/reader/pl196x.py` | 32 min | 109 | failed - stopped on its own |
| MiMo | 1 | 0.87 | 3/5 | 5/5 | 118/118 | mte_words_symlink_escape, toolbox_symlink_escape | - | `nltk/corpus/reader/crubadan.py`, `nltk/corpus/reader/lin.py`, `nltk/corpus/reader/nkjp.py`, `nltk/corpus/reader/toolbox.py`, `nltk/corpus/reader/util.py`, `nltk/corpus/reader/xmldocs.py`, `nltk/data.py`, `nltk/toolbox.py` | 39 min | 86 | failed - stopped on its own |
| MiMo | 2 | 1.00 | 5/5 | 5/5 | 118/118 | - | - | `nltk/corpus/reader/crubadan.py`, `nltk/corpus/reader/lin.py`, `nltk/corpus/reader/util.py`, `nltk/corpus/reader/xmldocs.py`, `nltk/data.py`, `nltk/pathsec.py`, `nltk/toolbox.py` | 61 min | 90 | SOLVED |
| MiMo | 3 | 0.87 | 3/5 | 5/5 | 118/118 | mte_words_symlink_escape, toolbox_symlink_escape | - | `nltk/corpus/reader/crubadan.py`, `nltk/corpus/reader/lin.py`, `nltk/corpus/reader/nkjp.py`, `nltk/corpus/reader/pl196x.py`, `nltk/corpus/reader/util.py`, `nltk/corpus/reader/xmldocs.py`, `nltk/data.py`, `nltk/toolbox.py` | 34 min | 72 | failed - stopped on its own |

#### Summary
DeepSeek failed all 3 attempts (0.93 each, always the toolbox symlink escape left open); MiMo failed 2 (0.87, toolbox + MTE left open) and solved 1. Rejected (MiMo solved). No timeouts; every run stopped on its own.

#### Why DeepSeek failed
- **It audited widely but by call graph from the corpus-reader classes** (~100 turns per run, a grep of every raw
  `open()`, escape/positive probe matrices, a full-suite diff against baseline).
- **It never tried the public low-level constructor the hidden test uses**, `ToolboxData(str(path))`, which reaches a
  raw `codecs.open`. It read `nltk/toolbox.py` and reasoned only about the reader path: "ToolboxCorpusReader uses
  `abspaths` ... abspath validation (new) will cover it"; "ToolboxData with a PathPointer uses `sfm_file.open(...)` ->
  central fix covers it. Good." Systematic: the same miss in 3 of 3 runs.
- **Its probes went through the same entry point as its fix**, so they passed: "Escape probe: 0 leaks, 28 blocked";
  "toolbox PASS" (via the corpus reader) -> "Task complete and verified."
- A trap in the environment: the global sandbox allows `tempfile.gettempdir()`, so "route through the secure open"
  without a required root blocks nothing for a symlink target under /tmp.

#### Why MiMo failed (2 of 3)
- **It found the bare-string leaks itself and talked itself out of fixing them**: "StandardFormat(str path) still
  leaks ... For the string case without required_root - that's direct API use. I'll leave it with global sandbox";
  "defaulting to parent dir is too strict for nested layouts".
- **Its tests bent the environment to pass**: one passed `required_root=...` (not the default call), one
  monkeypatched the allowed roots down to the corpus root.
- **It never checked which readers feed bare strings** to the shared XML view: `MTECorpusReader` builds
  `os.path.join(str(root), f)` strings (the MTE test failed; it never opened `mte.py`).
- **The solving run** treated the same observed leaks as bugs: "I'll add containment to them ... using
  parent-directory as the sandbox", and its own tests failed before the fix and passed after.

#### Weakness profile
- DeepSeek: entry-point blindness - treats "reachable through the main class" as the whole attack surface and
  confirms with probes that use the same entry point as its fix.
- MiMo: rationalises away its own negative evidence on an ambiguous boundary, and writes tests shaped to fit its fix.

#### Task-design lessons
- Make hidden tests hit the **second public API** (a lower-level class, helper, bare-string / path-like argument);
  the report says only "more than one public loading API".
- Let an **existing guard look sufficient in the test environment** (an allowed tempdir root) so a plausible
  half-fix passes the agent's own probes.
- Leave an **ambiguous boundary** (a bare path with no explicit root) where the report's general rule ("each affected
  path must honour the same containment rule") implies the strict reading.
- Name affected **file kinds** in the report, not readers, and test at least one reader reached only indirectly
  through a shared helper.
- Hidden tests use default arguments and the real sandbox settings, so environment-bending self-tests do not help.

### undici (GHSA-vp8m-p9jh-q5pm) - REJECTED: DeepSeek solved

- **Task type:** auth / session / credentials; wide multi-layer fix (10 files / 5 dirs / 120 lines); CWE 346; JavaScript
- **Entry point:** Public undici API: dispatcher.request({origin?, path, method}) on Client/Pool/BalancedPool/Agent/RetryAgent/Dispatcher1Wrapper instances composed with interceptors.cache()/interceptors.deduplicate() (optionally with interceptors.dns()/redirect()), against local HTTP servers
- **Reference fix (source files):** `lib/core/symbols.js`, `lib/dispatcher/balanced-pool.js`, `lib/dispatcher/dispatcher.js`, `lib/dispatcher/dispatcher1-wrapper.js`, `lib/dispatcher/retry-agent.js`, `lib/handler/redirect-handler.js`, `lib/interceptor/cache.js`, `lib/interceptor/deduplicate.js`, `lib/interceptor/dns.js`, `lib/util/cache.js`

| Model | # | Score | Security | Functional | Existing | Left open | Broke | Source files changed | Time | Turns | Ended |
|---|---|---|---|---|---|---|---|---|---|---|---|
| DeepSeek | 1 | 0.86 | 5/7 | 7/7 | - | legacy_wrapped_client_caller_origin, retry_wrapped_client_caller_origin | - | `lib/core/symbols.js`, `lib/dispatcher/dispatcher.js`, `lib/handler/redirect-handler.js`, `lib/interceptor/cache.js`, `lib/interceptor/deduplicate.js`, `lib/interceptor/dns.js`, `lib/util/cache.js`, `types/dispatcher.d.ts` | 56 min | 167 | failed - stopped on its own |
| DeepSeek | 2 | - | - | - | - | - | - | - | 52 min | 223 | cancelled (not graded) |
| DeepSeek | 3 | 1.00 | 7/7 | 7/7 | - | - | - | `lib/core/symbols.js`, `lib/dispatcher/balanced-pool.js`, `lib/dispatcher/dispatcher.js`, `lib/dispatcher/dispatcher1-wrapper.js`, `lib/dispatcher/retry-agent.js`, `lib/interceptor/cache.js`, `lib/interceptor/deduplicate.js`, `lib/interceptor/dns.js` | 49 min | 164 | SOLVED |
| MiMo | 1 | 0.93 | 7/7 | 6/7 | - | - | storage_with_custom_lookup_same_host | `lib/core/symbols.js`, `lib/core/util.js`, `lib/dispatcher/client-h1.js`, `lib/dispatcher/client-h2.js`, `lib/dispatcher/dispatcher.js`, `lib/dispatcher/dispatcher1-wrapper.js`, `lib/dispatcher/retry-agent.js`, `lib/handler/cache-handler.js` | 97 min | 166 | failed - stopped on its own |
| MiMo | 2 | - | - | - | - | - | - | - | 52 min | 68 | cancelled (not graded) |
| MiMo | 3 | - | - | - | - | - | - | - | 51 min | 60 | cancelled (not graded) |

#### Summary
DeepSeek failed attempt 1 (0.86, 5 of 7 attack paths) then solved attempt 2; MiMo failed its one graded attempt (0.93): it closed every attack path but broke a legitimate caching behaviour. Rejected (DeepSeek solved).

#### Why DeepSeek failed (attempt 1)
- **Right root cause:** cache / deduplicate keyed responses on the caller-supplied `opts.origin` label ("Client/Pool
  ignore `opts.origin`... BalancedPool ignores it entirely").
- **Fix (7 lib files):** `compose()` passes the dispatcher to interceptors; cache/dedupe key on `dispatcher[kUrl]`,
  skipping pool-like dispatchers without `kUrl`.
- **Missed the wrappers:** `RetryAgent(Client(A))` and `Dispatcher1Wrapper(Client(A))` have no `kUrl` and are not
  pool-like, so they fell back to the label (both wrapper tests failed). It opened `dispatcher1-wrapper.js` only to
  check it would not break - "Not relevant." - and read the report's "however the client object is wrapped" as
  chained `compose` calls.
- **Stopped on its own 9-scenario repro:** "All 9 pass ... The fix is complete and fully validated."
- **The solving attempt** did the same fix but then enumerated every dispatcher class asking "which ones set `kUrl`?",
  first dismissed the case ("very unlikely"), kept going, and confirmed it from the repo's own usage
  (`test/retry-agent.js`: `new RetryAgent(client, opts)`) - then propagated the real origin through the wrappers.

#### Why MiMo failed
- **Closed all 7 attack paths, broke 1 of 7 functional tests** (`storage_with_custom_lookup_same_host`): the widest
  fix (13 files) added a second, redundant safety layer - `CacheHandler.onRequestStart` re-keys a stored entry to the
  connection's origin "if that disagrees with the key we looked up with". With `compose(cache(), dns({lookup}))` the
  cache sees the resolved IP before dns rewrites it, so same-hostname responses are no longer reused.
- **It had the composition order right early** ("Call order: dns -> cache -> client"), then flipped it ("first
  interceptor in the list is outermost ... Either order should work") and re-added the re-keying it had dropped.
- **Tested only one order** (`compose([dns, cache])`), which passes; stopped after 1 h 40 min: "The origin-validation
  hole is fixed and covered by regression tests."

#### Weakness profile
- DeepSeek: does not enumerate every place the real destination can hide; reads a class-level requirement ("however
  wrapped") narrowly; treats "my own repro passes" as proof of completeness.
- MiMo: over-hardens with redundant defence-in-depth layers; confuses the order of composed layers; tests a legitimate
  configuration in one order only and generalises ("either order should work").

#### Task-design lessons
- Phrase requirements that imply a **class of cases** ("however it is wrapped / combined") and give each member its
  own hidden security test; the example in the report should be only one member.
- Test the same **legitimate behaviour in every supported composition order**: over-restricting fixes fail only in
  the order the agent did not try (this is what breaks MiMo).
- Pair each security test with a "must still work" twin sharing its setup (same host, custom lookup, wrapper).
- Prefer missed cases that appear in the repo's own usage/tests but not in the report's reproduction steps.

