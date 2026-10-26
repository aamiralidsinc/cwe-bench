# mockoon-ds — build notes

- Start (UTC): 2026-10-18T23:35:44Z (pipeline start; design work from 2026-10-18T23:40Z)
- End (UTC): 2026-10-19T02:05Z

## What the task is

Mockoon's server runtime (`@mockoon/commons-server`) serves user mock APIs and a management API
(`/mockoon-admin*`) used by the desktop app, CLI and scripts to read/change global variables,
environment variables, data buckets and the environment, read transaction logs and subscribe to
live events. At the pinned commit that management API has no authentication, grants CORS to every
origin, exposes recorded request/response headers (credentials, cookies, API keys) in logs and
live events, and lets a caller write arbitrary process environment variables. The runtime also
prints transaction details when transaction logging is enabled.

## Levers (each with a different reason a solver skips it)

| id | pattern | shape | where | reason to dismiss |
|----|---------|-------|-------|-------------------|
| T1 | A (landing) | unauthenticated management request is answered (reads, writes, SSE) | `packages/commons-server/src/libs/server/admin-api.ts:63` middleware + every route | reported site; the lever is covering every route/verb, including mutations and the event stream, not the example |
| T2 | A far site | runtime transaction logging prints `cookie` / `x-api-key` values | `packages/commons-server/src/libs/server/events-listeners.ts:15-25` (second redaction implementation) | "operator's own local stdout/file"; authorization is already masked there, so it reads as a separate logging feature |
| T3 | A far site | SSE replay and live events carry raw sensitive headers | `admin-api.ts:41-61` (replay) and `:88-92` (live emitter) | "I redacted the logs endpoint"; the event stream is a separate serialization path |
| T4 | A far site | env-var write of a key outside the configured prefix reaches `process.env` | `admin-api.ts:151-166` (write handler) | the report headline is auth/CORS; the prefix reads as a documented operator setting, and reads already auto-prefix |
| T5 | A host/wrapper site | serverless request listener does not convey the configured token/origins to the runtime (legit token refused) | `packages/serverless/src/libs/serverless.ts:36-59` | "the library fix covers every host"; the wrapper is assumed to be a pass-through |
| T6 | injected sibling (transport bypass) | management WebSocket log stream answers without a token and streams raw transactions | injected in `server.ts` upgrade path (`createWebsocketRoutes` / `webSocketUpgradeHandler`), outside Express | the admin router's middleware is assumed to cover every management path; upgrade requests never traverse Express |
| T7 | injected sibling (handler bypass) | bulk env-var import route writes arbitrary keys outside the prefix | injected in `admin-api.ts`, next to the other env-var routes | "I fixed the env-var handler"; an import helper looks like a convenience wrapper around it |

T6 and T7 are our copy only (injection.patch, applied in the image before the agent starts). They
are realistic maintainer code: live log streaming next to the existing user WebSocket routes, and
a bulk importer next to the env-var CRUD routes. The published fix never touches those lines; the
oracle patch does.

## Design choices

- Token contract (needed by the tests, so stated in the report): server option `adminApiAuthToken`,
  environment variable `MOCKOON_ADMIN_API_TOKEN` for the CLI/serverless runtime, auto-generated
  when absent (fail closed). Ordinary HTTP management endpoints take `Authorization: Bearer <token>`;
  live/streaming endpoints take `?token=<token>` because such clients cannot set request headers.
- CORS contract: `adminApiCorsOrigins` array; `'*'` is an explicit opt-in; default denies.
- Security tests assert the attack is blocked as *any 4xx plus no side effect*, never one status.
- Functional tests drive legitimate use and the coupled behaviour next to every lever (mock routes
  and their environment CORS, admin with token, SSE/WS stream with token, env read auto-prefix,
  prefixed writes, runtime logging, serverless with token).

## Verified before building

- Pinned tree installs offline-after-build with Node 24 (`npm ci` for commons, commons-server,
  serverless, cli workspaces: 832 packages), commons builds, and the project's
  `commons-server/test/specs/server/admin-api/*.test.ts` pass at the pinned commit.
- `node --test-reporter=junit` emits JUnit XML on Node 20/24 (used by `tests/test.sh`).
- `ws` is already a dependency of `@mockoon/commons-server`, so the injected stream can use it.

## Verified after building (Docker image `mockoon-ds-test`)

- Image builds (node:24-bookworm-slim, npm ci for the four workspaces, commons +
  commons-server + serverless built, `.git` removed).
- Untouched pinned+injected tree through the real `tests/test.sh`: security 0/26, functional
  15/15, reward 0.0 (the gate's nop shape).
- Oracle (`solution/solve.sh` then `tests/test.sh`): security 26/26, functional 15/15,
  reward 1.0.
- The pinned project's admin-api suites (global-vars, env-vars, logs, data-buckets,
  global-state, disable-api) and the serverless suite pass on the pinned+injected image.
- Gate static: only the two downstream-owned items remain (`kind=blind` patch and
  `FAIRNESS.md`); every other static check passes (leaks, exact-status assertions, hidden-test
  isolation, task.toml, offline allowlist, kill block).

## Checks patches (build/mockoon-ds/checks/)

Each patch is the oracle plus one deliberate defect, applied to the injected baseline.

| patch | expect | defect |
|-------|--------|--------|
| sf-miss-http-auth | security_fail | HTTP management authentication bypassed |
| sf-miss-runtime-log | security_fail | runtime transaction redaction reverted to the pinned second implementation |
| sf-miss-stream-redaction | security_fail | event-stream replay/live redaction removed |
| sf-miss-env-prefix | security_fail | env-var write handler writes the raw key |
| sf-miss-bulk-prefix | security_fail | bulk import writes raw keys |
| sf-miss-ws-auth | security_fail | management WebSocket stream without token check or redaction |
| sf-crash-refusal | security_fail | invalid token throws (500) instead of a client error |
| sf-logs-only | security_fail | only the logs route is authenticated |
| sf-reads-only | security_fail | only GET is authenticated; writes bypass |
| sf-presence-only | security_fail | any non-empty Authorization header accepted |
| sf-fail-open | security_fail | no configured token means allow |
| ff-miss-serverless | functional_fail | wrapper does not convey the configured token |
| ff-refuse-all | functional_fail | every management request refused |
| ff-adjacent | functional_fail | token required on mock routes too (over-broad) |
| hardening | pass | oracle plus extra sensitive-header names and `Cache-Control: no-store` |
| alt-fix | pass | outside-prefix writes rejected instead of auto-prefixed |

## Could not verify / out of scope

- Desktop app (Electron GUI) changes from the published fix are not built or tested; GUI entry is
  out of scope for this task.
- CLI flag wiring from the published fix is included in the oracle patch for fidelity but is not
  exercised by hidden tests (no CLI build in the image).

## Report scope note

The advisory also covers the desktop renderer's local IPC log view (unredacted by design upstream)
and environment-level CORS for user mock routes (intended mock behaviour). Neither is built on.

## Gate results (2026-10-19)

| stage | result |
|-------|--------|
| static | PASS except the two items owned downstream (`kind=blind` patch, `FAIRNESS.md`); leaks, exact-status, hidden-test isolation, metadata, offline allowlist and kill block all pass |
| nop | PASS — security 0/26 (all fail on the pinned+injected tree), functional 15/15, reward 0.0 |
| oracle | PASS — 3/3 runs reward 1.0, identical results |
| patches | PASS — 16/16 checks matched: 11 security_fail (each lever and catalogue class), 3 functional_fail (refuse-all, over-broad, wrapper), hardening pass 1.0, alternative fix pass 1.0 |

Infrastructure note: the first attempts of `nop`/`oracle`/`patches` failed with
`docker compose ... network ... not found` — the shared 8-CPU VM runs several other builders whose
gate stages call `docker network prune` at trial start. These were retried; no task change was made
and no task test failed for that reason.

## Register (pattern B)

No pattern-B routes: the only same-sink route the screener flagged (`GET env-vars/:key` with an
empty configured prefix) is authenticated after the fix and is a documented operator opt-out, so
it was not built. Both injected siblings are in the injected-sibling category, not pattern B.

## Upgrade 2026-10-20 (BETTER-PATTERNS §2–§8)

- Instruction rewritten: the property is stated once over the protected data/outcome — state
  and recorded traffic exposed to remote callers are accessible only with the configured secret;
  no record of served traffic, in any form or for any consumer, may contain a sensitive header
  value; process-environment writes only under the operator's prefix. Removed the product and
  channel framing ("management API", the operation/object-kind list, event stream, transaction
  log, the library/CLI/serverless run-mode list, the example origin, and the header-slot
  description). Coupled contracts kept in general terms: token/query-token forms, CORS
  allowlist/wildcard/preflight, 4xx with no side effect, header names and non-sensitive values,
  automatic prefixed reads, prefixed writes, and untouched user mock traffic.
- Levers: T1–T7 unchanged (where-type: extra entry points / planted copies). New how-type lever
  T8 (M6/M4): a templated mocked response can reproduce an incoming sensitive header in its
  body, so the recorded credential lands in a field the header-slot redaction never visits. The
  producer is the existing response templating; the published fix and the previous oracle both
  leave it open. No repo change: the pinned tree already contains the producer.
- Coverage: added
  `security/admin_redaction.test.ts::transaction redaction::a credential reproduced in a
  recorded response is redacted wherever it is exposed`. It drives the real mock route and
  asserts the echoed values are absent from the stored listing, SSE live and replayed updates,
  the management stream and the runtime transaction log. Added
  `checks/sf-miss-echo.patch` (the previous oracle: header-slot redaction only), expect
  `security_fail`, wired into `manifest.patch_checks`; new trap T8 added.
- `solution/fix.patch` extended: `redactTransaction` now collects the raw sensitive header
  values, redacts the header entries, then scrubs those values (and the scheme-stripped
  credential) from every string in the record; `events-listeners` uses the same function for
  the runtime transaction log.
- Counts now 27 security / 15 functional.
- Verified locally against the prebuilt tree (sources, matching the image's test.sh rebuild):
  pinned+injected 0/27 security + 15/15 functional; extended oracle 27/27 + 15/15;
  `sf-miss-echo` (previous oracle) 26/27 security with only the new test failing. `tsc` builds
  of commons and commons-server pass.
- `environment/` and repo code unchanged, so the prebuilt image is reused; no rebuild.
- Static gate: only the two downstream-owned items remain (blind pass patch, FAIRNESS.md); no
  leak term occurs in instruction.md.
