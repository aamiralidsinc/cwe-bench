# trigger-dev stacking task — BUILT, gate PASSED

Status: **BUILT — `builder/gate.py trigger-dev` printed PASSED** (see
gate_report.json). 4 co-present advisory vulns, all exploited through real HTTP
entry points. static ok; nop = 8 security fail + 5 functional pass; oracle = reward
1.0 twice, identically (8/8 security + 5/5 functional); subset_fix -> security_fail
(0.875, batch check-completion left failing); disable_feature -> functional_fail;
alt_correct_fix -> reward 1.0. The monorepo installs, builds and boots fully
offline (Postgres + Redis + dummy ClickHouse). Details below.

## Commit C
`bb450e608de2da1219af66a11d3a02c26a9f930b` = parent of the v4.5.2 security
release `34b1a181c2a1d33a53ebab88f84b05f81fea4254` (PR #4199), ~v4.5.1.
All four included vulns are OPEN here (verified by live reproduction).

## Co-present vulns reproduced at C (all live, offline, via real HTTP API)
1. **SSRF via webhook alert-channel URL** — CWE-918 — GHSA-q567-cr4x-96w4 /
   GHSA-xxv7-2vv3-h682. `POST /api/v1/projects/<ref>/alertChannels` (PAT auth)
   with `channel:webhook, channelData.url` pointing at an internal host.
   Reproduced: 169.254.169.254, 127.0.0.1:6379, 10.0.0.5, 192.168.1.1, [::1] all
   accepted HTTP 200 (channel stored). Fix rejects with 422.
   Fix commit 34b1a18: new `apps/webapp/app/v3/services/alerts/safeWebhookUrl.server.ts`
   + `safeWebhookFetch.server.ts`; `createAlertChannel.server.ts` validates at
   creation (`assertSafeWebhookUrl` -> ServiceValidationError -> 422); delivery
   call-sites `deliverAlert.server.ts` / `deliverErrorGroupAlert.server.ts`.
   MANY variants (private ranges + encodings) => strong against a shallow fix.
2. **Cross-environment deployment cancel** — CWE-639 — GHSA-4672-hwv6-gq62.
   `POST /api/v1/deployments/<id>/cancel`. `DeploymentService.getDeployment`
   filters by `projectId` only (no environmentId). Reproduced: created a
   deployment with the PROD env key, canceled it with the DEV env key (same
   project) -> HTTP 204, DB status=CANCELED. Same-env cancel (legit) -> 204.
   Fix commit 6997aeb: `api.v1.deployments.$deploymentId.cancel.ts` passes
   `{ id: authenticatedEnv.id }` and `deployment.server.ts` scopes by env id.
3. **Unauthenticated realtime stream injection** — CWE-306 — GHSA-59h8-w5q6-mfmp.
   `POST /realtime/v1/streams/<runFriendlyId>/<streamId>` has a plain `action`
   with no auth wrapper; looks up the run by friendlyId only. Reproduced: seeded
   one TaskRun row, POST with NO auth -> HTTP 200 (data ingested to the Redis
   stream); nonexistent run -> 404 (confirms handler ran). Fix commit 73d966a
   deletes the `action` handler (POST then -> 405); the authenticated GET loader
   stays.
4. **Batch check-completion missing authorization** — CWE-862 — GHSA-pp95-gc86-jq6q
   (the batch sibling of the run-replay IDOR). `POST /resources/batches/<batchId>/check-completion`
   has NO auth at C. Reproduced: unauth POST -> 302 to the submitted redirectUrl
   (/orgs), i.e. the action ran; an auth-required route -> 302 /login. Fix
   commit 34b1a18 adds `requireUserId` + `findBatchRunIdForUser` org-scoping
   (+ `sanitizeRedirectPath`).

Candidate 5th (not yet reproduced): **GHSA-qxpp-qjg8-x4jv** replay cross-env
write (CWE-639), fix in `replayTaskRun.server.ts` (34b1a18) — needs a seeded
run + the replay service path; deeper, left for the build.

## Dropped (not reachable offline / not a clean code fix)
- **9q4r** SQLi in TSQL -> ClickHouse `POST /api/v1/query`: needs a live
  ClickHouse (CLICKHOUSE_URL is required as a string but the connection is lazy,
  so boot works with a dummy; the query path itself needs CH). Dropped to stay
  lean/offline.
- **gg6r** V1 coordinator Socket.IO default-secret: EOL V1 stack, needs Run
  Engine 1.0 self-host wiring. Drop.
- **pqxw** docker-compose default secrets / magic-link forgery: the 6997aeb fix
  is largely config/.env.example + env hardening, not a clean app-logic fix.
- **fj2x** CLI debug-log secret exposure: CLI entry point, not the HTTP API.

The pp95/qxpp run-replay *route* was refactored before C (already uses
`dashboardAction` with membership checks), so the advisory's original
manifestation moved to `replayTaskRun.server.ts` (qxpp) and
`check-completion.ts` (pp95). Verify shapes against C, not advisory line nums.

## PROVEN offline build+boot recipe (see recipe/Dockerfile.proven, recipe/boot.sh)
Base `node:22-bookworm`; apt: postgresql, redis-server, build-essential, patch,
curl, git, python3. `corepack prepare pnpm@10.33.2`. Then:
- `pnpm install --frozen-lockfile`  (2.5 min, reproducible, offline after cache)
- generate ALL clients: `@trigger.dev/database`, `@internal/run-ops-database`,
  `@internal/llm-model-catalog`  (missing run-ops client breaks the turbo build)
- bundle externalized dep: `sed` add `/^eventsource-parser.*/` to
  `serverDependenciesToBundle` in `apps/webapp/remix.config.js`
- `pnpm run build --filter webapp`  (~1 min; build/server.js)
- RUNTIME: set `NODE_PATH=/app/node_modules/.pnpm/node_modules` so the bundled
  server resolves transitive deps of the bundled @trigger.dev/*/@internal/* pkgs
  (@jsonhero/path etc.) that pnpm's isolated store hides.
Services in-image, no network at run time: postgres (initdb -A trust) + redis +
DUMMY `CLICKHOUSE_URL` (connection is lazy; do NOT set RUN_REPLICATION_* so
replication stays off). Gated-off: S2_ENABLED=0, GITHUB_APP_ENABLED=0.
Single process (clustering is off unless ENABLE_CLUSTER=1) -> modest memory
(ran under --memory=6g fine). ENCRYPTION_KEY = 32-char string.
Boot: `prisma migrate deploy` (main db), `pnpm db:seed`, `node build/server.js`
on PORT=3030. `/login` -> 200 confirms up.

## Auth / preconditions (all via the seed)
`pnpm --filter webapp db:seed` creates org "References", projects (hello-world =
`proj_rrkpdguyagvsoktglnod`), each with DEVELOPMENT/PRODUCTION/STAGING/PREVIEW
env API keys (`tr_dev_*`, `tr_prod_*`, ...). A PAT (`tr_pat_*`) is minted only
when NODE_ENV!=production AND APP_ORIGIN host is localhost — for the tests,
either run seed with NODE_ENV=development, or mint a PAT with the inline snippet
(see recipe notes). Env API keys authenticate /api/v1/deployments; the PAT
authenticates /api/v1/projects/:ref/alertChannels. TaskRun/BatchTaskRun for
vulns 3/4 are seeded directly via SQL (TaskRun needs only id, payload,
runtimeEnvironmentId, projectId, updatedAt, taskIdentifier, friendlyId, spanId,
traceId, queue; everything else has defaults).

## Remaining work to gate PASS (est. several hours incl. gate iterations)
1. tests/security: one group per vuln (ssrf x~5 variants, deploy-cancel,
   realtime-unauth, batch-check-completion-unauth) + functional (seed-driven
   setup; legit webhook with a public IP literal e.g. 8.8.8.8 so the fix's
   validator passes offline; same-env cancel 204; authenticated stream GET;
   authenticated batch completion). Mirror cloudreve's tests/lib/*.py + test.sh
   pattern (rebuild webapp from /app, start pg+redis, seed, drive HTTP).
2. solution/fix.patch: SOURCE-only hunks for the 4 vulns extracted from
   34b1a18 (safeWebhookUrl/Fetch + createAlertChannel + deliver* ; check-completion)
   + 73d966a (realtime action removal) + 6997aeb (cancel route + deployment.server).
   Exclude the dozens of unrelated hardening hunks in those commits.
3. build/checks: subset_fix (fix 3 of 4), disable_feature (over-block a feature),
   alt_correct_fix (second valid layer).
4. instruction.md (no CVE/GHSA/file/function/count leaks), task.toml
   (source="mined+stacking"), manifest.json with leak_terms.
5. `python3 -I builder/gate.py trigger-dev`.

Risk note: each gate trial rebuilds the remix webapp from /app (~1 min) + pg
init + migrate + seed + boot; 6 trials/run. Keep SSRF tested at CREATION
(synchronous) to avoid async alert-worker flakiness (oracle must pass 2x
identically).

## 2026-10-16 test repair

Brief: `build/audit/REPAIR-BRIEF-2026-10-16.md`. Sources: `build/audit/lenient_items_2026-10-16.txt`
(trigger-dev sections), `research/own-runs/TEST-REPAIRS.md` (## trigger-dev), audit verdicts of
aoMpPQa (deepseek r11), Gts23hz (deepseek r2), xG36wVE (mimo r1), iNC3Sbj (mimo r11).

### Items and decisions
| # | item (source) | decision |
|---|---|---|
| 1 | Batch security test: anonymous refusal must accept any 4xx or a /login redirect, not one status (aoMpPQa REC) | already fixed (earlier today); now also checks the batch state did not change |
| 2 | Batch functional test must accept either id form (aoMpPQa REC) | already fixed (earlier today) |
| 3 | No logged-in member of a DIFFERENT org is tried; a requireUserId-only fix scores 1.0 (aoMpPQa, Gts23hz, xG36wVE, iNC3Sbj) | **fixed**: `test_other_org_member_check_completion_blocked`. fixtures.ts adds user `outsider@example.com`, admin of their own org "Outsider Org", plus two more PENDING batches in the hello-world DEV env (`probebatch0002` for the anonymous test, `probebatch0003` for the cross-org test). The outsider logs in by magic link (a sanity GET /account confirms the session), POSTs check-completion under both id forms, and the test reads the batch status straight from Postgres: it must still be PENDING. The response form is not checked (the reference answers 302 + error flash to the same redirectUrl, like the vulnerable success path). Stated in the instruction ("belongs to the owning organization"). |
| 4 | Authed functional batch test accepts any non-login 302, so "error message for every member" passes (aoMpPQa REC) | **fixed**: the owner's call must take effect (the seeded dev batch with no child runs leaves PENDING, which is what the original code does). |
| 5 | No functional authenticated same-environment stream write; deleting every write route passes (iNC3Sbj) | **fixed**: `functional/test_realtime_authed_write.py`. DEV key writes into the DEV run's stream on `/realtime/v1/streams/<run>/self/<stream>` (an API-key route already present at C), or on the original route if the fix put auth on it; either one must answer 2xx and a Redis key with the fresh stream name must exist. The reference removes only the anonymous route, so it passes. Stated: "Authenticated, correctly scoped access to stream data must continue to function." |
| 6 | (review) Stream write: a fix that demands *some* credential but does not scope the run to it would pass | **fixed**: `test_other_environment_key_stream_write_blocked` (PROD key writes into the DEV run on the formerly anonymous route: must be 4xx and leave no Redis key). The anonymous test also now checks no Redis key appears. Stated: "correctly scoped". |
| 7 | (review) SSRF: an IP-literal-only / string blocklist passes (Gts23hz, xG36wVE RECs) | **fixed**: three more spellings: `http://localhost:6379/`, `http://2130706433/` (decimal 127.0.0.1), `http://[::ffff:169.254.169.254]/latest/`. Stated: "resolves to an internal / loopback / link-local / private address". All five saved model fixes and the reference handle them. |
| 8 | Postmortem packager should snapshot the graded test version; final-code missing for xG36wVE (xG36wVE REC a) | skip: tooling, outside tasks/ and build/SLUG/ |

### Patch checks
- `alt_correct_fix.patch` (pass) **changed**: its batch hunk was requireUserId only, which the
  instruction rules out (it would now fail item 3). It now checks membership inline in the route
  via Prisma (a different layer from the reference's helper). The old form is kept as:
- `login_only_batch_fix.patch` (security_fail, new): reference, but check-completion only requires a login.
- `member_refused_batch_fix.patch` (functional_fail, new): reference with a membership query on the
  wrong field (orgMember.organizationId = environment id), so every member gets an error redirect.
- `unscoped_stream_auth.patch` (security_fail, new): formerly anonymous route demands a valid API key
  but looks the run up without environment scoping.
- `no_stream_writes.patch` (functional_fail, new): reference plus removing the `/self` write action.
- `ssrf_string_blocklist.patch` (security_fail, new): validator regex-matches the raw URL for private prefixes.
- Kept unchanged: subset_fix (security_fail), disable_feature (functional_fail), auth_required_stream_fix (pass).

test.sh: only the fixture-variable line changed (also exports TR_BATCH_ANON, TR_BATCH_XORG,
TR_OUTSIDER_EMAIL). tr.py gained `batch_status` (psql), `redis_keys_containing` (redis-cli
--scan), `batch_refs`, and a `target` argument on `stream_write`. No instruction change.
Counts now: security 13 (was 8), functional 7 (was 6).

Probe before the gate (reference fix, fresh container): security 13/13, functional 7/7, reward 1.0;
DB afterwards: probebatch0001 COMPLETED, 0002/0003 PENDING; Redis held
`tr:realtime:streams:stream:run_probefixture0001:legit…` only.

### Flaky same-env cancel test (found by this repair's gate, fixed)
Gate try 3 (gate-20261016-repair-try3-deploy500.log): oracle1 (gate-jobs/trigger-dev-oracle1-1792135009,
verifier 07:16:57-07:18:51 UTC, outside the disk-full windows) scored 0.0 on
`test_same_env_cancel_works` ("deploy create failed: 500"), oracle2 (…-1792135145) scored 1.0.
Evidence of a clock step: oracle1's functional session reports "6 passed in -0.97s".
Cause: the product numbers a deployment from the environment's latest-by-createdAt deployment
(`calculateNextBuildVersion`). Three PROD deployments were created per run (security cross-env
test, test_create_deployment, test_same_env_cancel). If the container clock steps back between
the first two, the second gets an earlier createdAt; the third is then numbered from the first
again and collides with the second on (environmentId, version) on every retry -> 500.
Reproduced on the reference fix: after setting the first PROD deployment's createdAt one hour
ahead, the next POST /api/v1/deployments answered HTTP 500.
Fix (tests only): fixtures.ts adds a STAGING environment to hello-world via Prisma (the seed has
DEV/PROD only) and exports TR_STAGING_KEY; test_same_env_cancel now creates and cancels in
STAGING. Each environment now gets at most two deployments, and the second is numbered from the
only existing one, so a clock step can no longer collide. Same property, same assertion.
Earlier gate tries: try 1 oracle2 "network_mode='allowlist' is not supported" (Harbor egress
probe under load, no trial ran); try 2 nop ran 05:57-06:28 UTC in the disk-full window
(webapp build, seed and fixtures failed) -> both infra, not test results.

### auth_required_stream_fix variant corrected (gate try 4)
Gate try 4 (gate-20261016-repair-try4-authvariant.log): nop and both oracles OK; the `pass`
variant auth_required_stream_fix scored 0.9231, failing test_other_environment_key_stream_write_blocked.
That variant (added earlier today to prove a 401 refusal is accepted) only checked that an
Authorization header was present, so a PROD key (or any header) still wrote into the DEV run:
a real defect under "requires proper authorization" / "correctly scoped". The variant now
authenticates the API key (401 otherwise) and refuses runs outside the key's environment (404);
the header-presence form is kept as header_presence_stream_fix.patch (security_fail).

### Gate result: PASSED (try 5, gate-20261016-repair.log, `slot.py 2`)
| run | reward | sec | fun | failing |
|---|---|---|---|---|
| nop | 0.0 | 0/13 | 7/7 | all security |
| oracle1 / oracle2 | 1.0 / 1.0 | 13/13 | 7/7 | - |
| subset_fix (security_fail) | 0.8462 | 11/13 | 7/7 | both batch security tests |
| disable_feature (functional_fail) | 0.0 | 8/13 | 6/7 | public webhook accepted |
| alt_correct_fix (pass, updated) | 1.0 | 13/13 | 7/7 | - |
| auth_required_stream_fix (pass, updated) | 1.0 | 13/13 | 7/7 | - |
| login_only_batch_fix (security_fail, new) | 0.9231 | 12/13 | 7/7 | other-org member |
| member_refused_batch_fix (functional_fail, new) | 0.0 | 13/13 | 6/7 | member check-completion takes effect |
| unscoped_stream_auth (security_fail, new) | 0.9231 | 12/13 | 7/7 | other-environment key write |
| no_stream_writes (functional_fail, new) | 0.0 | 13/13 | 6/7 | authed same-env stream write |
| ssrf_string_blocklist (security_fail, new) | 0.7692 | 10/13 | 7/7 | localhost, 2130706433, [::ffff:169.254.169.254] |
| header_presence_stream_fix (security_fail, new) | 0.9231 | 12/13 | 7/7 | other-environment key write |

### Regrade of saved runs (final tests; test.sh sha256 4ab452a8…)
Runs with final-code/changes.patch: all five were at 1.0; no test was relaxed in a way that
could raise a run below 1.0 (none with saved code are below 1.0), so only these were regraded.
| trial | old | new | failing tests |
|---|---|---|---|
| deepseek r11 aoMpPQa | 1.0 | 1.0 (regrade-20261016T091741Z) | - |
| deepseek r2 Gts23hz | 1.0 | 1.0 (regrade-20261016T091846Z) | - |
| deepseek r3 Eyc3WUE | 1.0 | 1.0 (regrade-20261016T092002Z) | - |
| deepseek r4 eQ9xLN3 | 1.0 | 1.0 (regrade-20261016T092114Z) | - |
| mimo r11 iNC3Sbj | 1.0 | 1.0 (regrade-20261016T092228Z) | - |
Earlier regrades today with an intermediate test version (before the STAGING change) also all
scored 1.0 (regrade-20261016T051417Z, T052626Z, T054854Z, T062229Z, T071515Z); two first
attempts for eQ9xLN3/iNC3Sbj failed at image build (disk full, apt "invalid signature") and
left no regrade dir. Not regradable (no saved final code): mimo r1 xG36wVE (verifier 1.0),
and the older runs wEafvJY, gUuxW3Q, Jqy5Sqn, TBQ5WXA, ceXhxYf, bb9jAbj.
No drops: every model fix checks org membership, scopes stream writes to the key's environment,
and its SSRF validator handles names, decimal and IPv4-mapped spellings.
