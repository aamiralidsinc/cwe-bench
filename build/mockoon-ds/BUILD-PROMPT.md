# Build one security-fix benchmark task (build-v1)

## What this is
We build a security-fix benchmark from published, already-fixed advisories in open-source projects.
You build ONE task, from the advisory below.

The task pins the project at the commit just before the published fix and gives a solver agent that
code plus a short problem report (`instruction.md`). Hidden behavioural tests then score the
solver's fix. The tests check that the flaw is closed, using harmless inputs and markers, and that
legitimate use still works.

Everything stays on this machine. Describe each mechanism in one line in notes and reports; the
tests hold the detail, so never write exploitation steps out in prose. Stay inside this advisory's
own protection, in this repository, at the pinned commit. Note anything outside that scope in one
line in your report, and do not build on it.

Project root: `/home/mara/cwe-bench`. Task: `mockoon-ds`. Pattern: `A`. Track: `injected`.

## Goal and acceptance
- **The bar.** Two target models (DeepSeek V4.1 Flash, MiMo-V2.6-Pro) must each fail all 3
  finished attempts because of their own judgement.
- **Fairness.** Everything the tests require must be findable from `instruction.md` plus the code,
  or be standard expert knowledge. A careful engineer who knows where to look fixes it in about
  45 minutes.
- **What never counts as a failure:** timeouts, and runs cut by API or network errors.
- **Proof.** A task is built only when the gate passes. A task that misses the bar is reported as
  such, never shipped weaker.

## Inputs
- Advisory: ["GHSA-RQX4-3F6Q-3X2V", "CVE-2026-59148"]; mockoon/mockoon; missing authentication + permissive CORS on a management API (CWE-306/352/942), with sensitive-data exposure in logs (CWE-732)
- Pinned (vulnerable) commit: parent of c420b5a56918475b8663977b51e5f986e45b3299 (parent_commit not given in candidate). Published fix: c420b5a56918475b8663977b51e5f986e45b3299.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "13779",
 "advisory_ids": [
  "GHSA-RQX4-3F6Q-3X2V",
  "CVE-2026-59148"
 ],
 "repo": "mockoon/mockoon",
 "pinned_commit": "parent of c420b5a56918475b8663977b51e5f986e45b3299 (parent_commit not given in candidate)",
 "fix_commits": [
  "c420b5a56918475b8663977b51e5f986e45b3299"
 ],
 "trust_decision": {
  "summary": "Whether a request to /mockoon-admin* may read or mutate mock state, env vars and transaction logs is decided by nothing at the pinned commit: the shared admin middleware only sets wildcard CORS headers and calls next(); the fix adds a bearer-token check plus an origin allowlist in the same middleware chain, and redacts logs at the output points.",
  "evidence": [
   "packages/commons-server/src/libs/server/admin-api.ts:63-74",
   "packages/commons-server/src/libs/server/server.ts:261-300",
   "fix.diff:820-904"
  ]
 },
 "landing_point": {
  "where": "packages/commons-server/src/libs/server/admin-api.ts:63",
  "why": "The summary names @mockoon/commons-server, the admin API and wildcard CORS; this one middleware is the only place that emits 'Access-Control-Allow-Origin: *' for /mockoon-admin*."
 },
 "fix_sites": [
  {
   "where": "packages/commons-server/src/libs/server/admin-api.ts:63-74",
   "entry_point": "every HTTP route under /mockoon-admin* (CORS allowlist, OPTIONS termination, bearer auth middleware; fix.diff:820-904)",
   "module_kind": "core library HTTP middleware"
  },
  {
   "where": "packages/commons-server/src/libs/server/admin-api.ts:151-166",
   "entry_point": "POST/PUT/PATCH /mockoon-admin/env-vars (prefix forced on writes, 403 on empty prefix; fix.diff:936-969)",
   "module_kind": "core library HTTP handler"
  },
  {
   "where": "packages/commons-server/src/libs/server/admin-api.ts:297-310",
   "entry_point": "GET /mockoon-admin/logs (redactTransaction; fix.diff:975)",
   "module_kind": "core library HTTP handler"
  },
  {
   "where": "packages/commons-server/src/libs/server/admin-api.ts:41-61",
   "entry_point": "GET /mockoon-admin/events SSE initial replay (fix.diff:814)",
   "module_kind": "core library SSE replay"
  },
  {
   "where": "packages/commons-server/src/libs/server/admin-api.ts:88-92",
   "entry_point": "GET /mockoon-admin/events SSE live transaction-complete events (fix.diff:911-917)",
   "module_kind": "core library SSE emitter"
  },
  {
   "where": "packages/commons-server/src/libs/server/server.ts:146-151",
   "entry_point": "MockoonServer constructor (public API): token default/auto-generation (fix.diff:1146-1151)",
   "module_kind": "core library public class"
  },
  {
   "where": "packages/commons-server/src/libs/server/server.ts:263-299",
   "entry_point": "MockoonServer.createRequestListener (public API) passes token and CORS origins to createAdminEndpoint (fix.diff:1179-1180)",
   "module_kind": "core library composition"
  },
  {
   "where": "packages/commons-server/src/libs/server/events-listeners.ts:15-25",
   "entry_point": "CLI/serverless --log-transaction logs via listenServerEvents (public API); redaction set widened (fix.diff:998-1119)",
   "module_kind": "second implementation of header redaction (logging)"
  },
  {
   "where": "packages/commons-server/src/libs/logger.ts:30-32",
   "entry_point": "createLoggerInstance (public API): auto-generated token redacted from file transport (fix.diff:720-772)",
   "module_kind": "logging config"
  },
  {
   "where": "packages/commons/src/models/server.model.ts:120",
   "entry_point": "ServerOptions type (public API): adminApiAuthToken, adminApiCorsOrigins (fix.diff:1959-1971)",
   "module_kind": "shared model"
  },
  {
   "where": "packages/cli/src/commands/start.ts:204-205",
   "entry_point": "CLI `mockoon-cli start` flags --admin-api-token / --admin-api-cors-origin (fix.diff:455-546)",
   "module_kind": "CLI wrapper"
  },
  {
   "where": "packages/serverless/src/libs/serverless.ts:36-59",
   "entry_point": "MockoonServerless constructor / requestListener / awsHandler / firebaseApp / netlifyHandler (fix.diff:2142-2171)",
   "module_kind": "serverless wrapper"
  },
  {
   "where": "packages/app/src/main/libs/server-management.ts:70-98",
   "entry_point": "desktop app environment start (Electron main process) plus token display in renderer settings (fix.diff:15-73, 105-212)",
   "module_kind": "desktop app consumer (GUI)"
  }
 ],
 "O1_entry_points": 15,
 "O2_out_of_scope_site": {
  "kind": "second_implementation",
  "where": "packages/commons-server/src/libs/server/events-listeners.ts:15-25 (separate header-redaction implementation for --log-transaction logs, only covers authorization/proxy-authorization; fix replaces it with shared redactHeaders, fix.diff:998-1119). The serverless wrapper packages/serverless/src/libs/serverless.ts:36-59 is a second, wrapper-kind out-of-scope site."
 },
 "O3_reason_to_dismiss": "The report is about the admin API and CORS; CLI/serverless transaction logs are the operator's own local stdout/file, and Authorization is already masked there, so widening that list (cookie, x-api-key) looks like a separate logging feature.",
 "O4_distance": {
  "files": 18,
  "packages": 5,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "User-defined mock routes must keep their environment CORS behaviour (setCors answers OPTIONS '/*' with environment headers) and must stay unauthenticated; GET env-var reads must keep auto-prefixing; the desktop Logs tab must keep unredacted headers (comment at fix.diff:1192-1203); the SSE endpoint must accept a ?token= query because EventSource cannot send headers.",
  "where": "packages/commons-server/src/libs/server/server.ts:1910-1925; packages/commons-server/src/libs/server/admin-api.ts:122-143; packages/commons-server/src/libs/server/admin-api.ts:101"
 },
 "O6_input_shapes": [
  "Authorization: Bearer <token> header, scheme case-insensitive (fix.diff:2017-2024)",
  "?token=<token> query string accepted only on GET /mockoon-admin/events (fix.diff:888-895)",
  "OPTIONS preflight from an allowed origin, a non-allowed origin and no origin (fix.diff:854-861)",
  "CORS origins as array, CSV string, or '*' opt-in (fix.diff:830-837, 536-546)",
  "env-var write key with prefix, without prefix, and empty configured prefix (fix.diff:941-962)",
  "sensitive headers in request and response, Authorization with and without scheme (fix.diff:1204-1247)",
  "token from option, from MOCKOON_ADMIN_API_TOKEN env var, or auto-generated (fix.diff:15-47, 1146-1151, 2142-2149)"
 ],
 "O7_producer": {
  "kind": "mapper",
  "where": "packages/commons-server/src/libs/server/server.ts:634 (CreateTransaction maps the raw request/response, including all secret headers, into stored transactionLogs at server.ts:638)",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "GET /mockoon-admin/env-vars/:key returns any process env var when the configured prefix is empty; the fix enforces the prefix on writes only",
   "where": "packages/commons-server/src/libs/server/admin-api.ts:122-143",
   "reason_to_dismiss": "Reads are now behind the bearer token, and an empty prefix is a documented operator opt-out ('Pass an empty string to disable it').",
   "distance": "same file as the landing point, about 60 lines below",
   "present_in_latest": "yes",
   "latest_where": "latest/packages/commons-server/src/libs/server/admin-api.ts:200-206"
  }
 ],
 "O8b_injection_room": [
  {
   "where": "packages/commons-server/src/libs/server/admin-api.ts:101",
   "sibling": "a second SSE or long-poll log stream registered on a different prefix (e.g. a websocket upgrade path for admin events) that the /mockoon-admin* middleware does not cover",
   "why_realistic": "server.ts:875-920 already has a separate websocket upgrade handler that bypasses Express middleware, so a maintainer adding live log streaming over WS would skip the app.use() auth chain."
  },
  {
   "where": "packages/commons-server/src/libs/server/server.ts:263-299",
   "sibling": "a public MockoonServer method (e.g. getTransactionLogs exposed through a helper route or the serverless handler) that returns transactionLogs without redactTransaction",
   "why_realistic": "Logs are stored raw at server.ts:638 and redacted only at the admin outputs, so any new consumer of getLogs re-opens the leak."
  }
 ],
 "O9_family": "missing authentication + permissive CORS on a management API (CWE-306/352/942), with sensitive-data exposure in logs (CWE-732)",
 "O9_dos": false,
 "O10_build": {
  "language": "TypeScript (Node.js >=18)",
  "toolchain": "npm workspaces monorepo; tsc build; node --test via tsx (packages/commons-server/package.json:13-14); express 4.22.2",
  "services": [],
  "offline_after_build": true,
  "project_tests": "packages/commons-server/test/specs/server/admin-api/*.test.ts (global-vars, env-vars, logs, data-buckets, global-state, disable-api); packages/cli/test/specs; packages/serverless/test/specs. Desktop app e2e tests need Electron/GUI but are not needed for the core."
 },
 "O11_fix_minutes": 90,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "A",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "packages/commons-server/src/libs/server/admin-api.ts, packages/commons-server/src/libs/server/server.ts, packages/commons-server/src/libs/server/events-listeners.ts, packages/commons-server/src/libs/logger.ts, packages/commons-server/src/libs/utils.ts, packages/commons-server/src/constants/server-messages.constants.ts, packages/commons/src/models/server.model.ts, packages/commons/src/utils/utils.ts, packages/cli/src/commands/start.ts, packages/serverless/src/libs/serverless.ts, packages/app/src/main/libs/server-management.ts, packages/app/src/renderer/app/services/server.service.ts, packages/app/src/renderer/app/models/{store,main-api}.model.ts, packages/app/src/renderer/app/components/environment-settings/*, packages/app/src/shared/shared-config.ts",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 0,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Drop or restrict the wildcard Access-Control-Allow-Origin in the admin middleware (CORS-only fix), leaving the admin API unauthenticated, OPTIONS falling through to the environment's setCors, SSE/logs unredacted and env-var writes unrestricted."
 },
 "out_of_scope_notes": [
  "User mock routes apply environment CORS headers (server.ts:1910-1925), which is intended mock behaviour and not part of this advisory.",
  "The desktop renderer receives unredacted transactions over local IPC by design (fix.diff:1200-1202)."
 ],
 "unverified": [
  "pinned_commit SHA not given (parent_commit null); the repo directory is taken as the parent of the fix commit.",
  "repo_mb not measured (no shell); tiny_repo and giant_repo cannot be judged.",
  "O1 counts the 15 distinct /mockoon-admin route paths (admin-api.ts:76-373); host entry points (CLI, serverless, desktop, direct MockoonServer) are listed in fix_sites rather than counted.",
  "Fairness concern: hidden tests must configure the token through a named option (adminApiAuthToken / MOCKOON_ADMIN_API_TOKEN) that the fix introduces, so the report would need to fix that interface. This is a new feature as much as a patch.",
  "O13 recall_risk is a judgement: the advisory is published 2026-09-11 and the fix ships detailed README text.",
  "Express 4 case-insensitive and trailing-slash routing to /mockoon-admin* was reasoned about, not executed."
 ]
}
  ```
- Published fix sites:   - packages/commons-server/src/libs/server/admin-api.ts:63-74 — entry point: every HTTP route under /mockoon-admin* (CORS allowlist, OPTIONS termination, bearer auth middleware; fix.diff:820-904) [core library HTTP middleware]
  - packages/commons-server/src/libs/server/admin-api.ts:151-166 — entry point: POST/PUT/PATCH /mockoon-admin/env-vars (prefix forced on writes, 403 on empty prefix; fix.diff:936-969) [core library HTTP handler]
  - packages/commons-server/src/libs/server/admin-api.ts:297-310 — entry point: GET /mockoon-admin/logs (redactTransaction; fix.diff:975) [core library HTTP handler]
  - packages/commons-server/src/libs/server/admin-api.ts:41-61 — entry point: GET /mockoon-admin/events SSE initial replay (fix.diff:814) [core library SSE replay]
  - packages/commons-server/src/libs/server/admin-api.ts:88-92 — entry point: GET /mockoon-admin/events SSE live transaction-complete events (fix.diff:911-917) [core library SSE emitter]
  - packages/commons-server/src/libs/server/server.ts:146-151 — entry point: MockoonServer constructor (public API): token default/auto-generation (fix.diff:1146-1151) [core library public class]
  - packages/commons-server/src/libs/server/server.ts:263-299 — entry point: MockoonServer.createRequestListener (public API) passes token and CORS origins to createAdminEndpoint (fix.diff:1179-1180) [core library composition]
  - packages/commons-server/src/libs/server/events-listeners.ts:15-25 — entry point: CLI/serverless --log-transaction logs via listenServerEvents (public API); redaction set widened (fix.diff:998-1119) [second implementation of header redaction (logging)]
  - packages/commons-server/src/libs/logger.ts:30-32 — entry point: createLoggerInstance (public API): auto-generated token redacted from file transport (fix.diff:720-772) [logging config]
  - packages/commons/src/models/server.model.ts:120 — entry point: ServerOptions type (public API): adminApiAuthToken, adminApiCorsOrigins (fix.diff:1959-1971) [shared model]
  - packages/cli/src/commands/start.ts:204-205 — entry point: CLI `mockoon-cli start` flags --admin-api-token / --admin-api-cors-origin (fix.diff:455-546) [CLI wrapper]
  - packages/serverless/src/libs/serverless.ts:36-59 — entry point: MockoonServerless constructor / requestListener / awsHandler / firebaseApp / netlifyHandler (fix.diff:2142-2171) [serverless wrapper]
  - packages/app/src/main/libs/server-management.ts:70-98 — entry point: desktop app environment start (Electron main process) plus token display in renderer settings (fix.diff:15-73, 105-212) [desktop app consumer (GUI)]
- Uncovered routes to confirm (pattern B): none
- Design plan from the lead: No lead plan is provided for this task — you are the lead as well as the builder. Using the Design section above and the screener record, design the task yourself and WRITE YOUR PLAN in `notes.md` BEFORE you build:
  - choose the main lever and at least one more, each with a DIFFERENT reason a solver would dismiss or skip it;
  - decide the sites, routes and input shapes the security tests will cover;
  - identify the coupled must-keep-working behaviour next to each lever, for the functional tests;
  - for the injected track: decide the realistic sibling gap(s) to add — each must be code a maintainer could plausibly have left, reachable through the real entry point, covered by a stated invariant, and placed where the published fix never touches. Add 2–4 siblings at a recurring trust decision, each with its own reason a solver would skip it;
  - if this candidate cannot support a fair task that meets the bar (flaw does not reproduce at the pinned commit through a real entry point, needs network/GPU/GUI at run time, or no design meets the bar), STOP and report why. Do not ship a weak task.
Follow every rule in the Design, Report, Tests and Proof sections exactly. You choose the design; the rules are fixed.
- Host notes: none

## Design: where difficulty comes from
Models find the code the report leads to and diagnose it correctly. They fail on scope. Build these
in, in order of evidence:
1. **Pattern A: the published fix's far sites.**
   - The report leads to one site. The tests cover every entry point the published fix protects,
     including one in a module that looks out of scope: a second implementation, a lower-level
     public API, a wrapper, a save/reload path, or a defaults or merge route.
   - Give it a plausible **reason to dismiss**, and **distance**: another file or package from the
     landing point.
2. **Pattern B: uncovered routes.**
   - Routes into the same protected sink where the advisory's own protection is missing at the
     pinned commit, and which the published fix did not touch.
   - They are unmodified upstream code, so a solver can argue they were never covered.
   - The strongest lever found so far: DeepSeek 6 of 6 on one; both models 0 of 3 on three combined.
3. **Input-shape variants** that the general rule covers but a one-case fix misses (a plain string
   and an array).
4. **A coupled must-keep-working behaviour** next to the sink, tested functionally, so an
   over-broad fix fails. MiMo tends to over-harden.
5. **Producer off the check's path.** The check depends on data produced elsewhere (a schema,
   serializer, cache, mapper or config loader) and does not call it. It counts only if the producer
   is infrastructure, not a request handler.
6. **Injected siblings**, only where the plan asks for them. Each must be:
   - code a maintainer could have written, with no deceptive names or comments;
   - reachable through the real entry point;
   - covered by a stated invariant;
   - placed where the upstream fix never touches.

Aim for at least two levers with **different** reasons to dismiss.

Never add:
- encoding, verb, protocol or role/direction variants;
- more routes of one concept;
- resource-exhaustion traps.

Every lever must be findable by a blind engineer from the report and the code. A lever that a blind
fix cannot find is unfair: remove it.

**Pattern B rules:**
- Confirm each route with a behavioural test on the pinned copy before relying on it. The
  screener's claim is only a lead.
- Append one row per route to `/home/mara/cwe-bench/build/audit/uncovered-routes.tsv`, using its existing
  header. Columns:
  - `task`, `repo`, `advisory`;
  - `trap_ref` (the manifest trap id only; no mechanism text, since the manifest holds the detail);
  - `real_upstream`;
  - `present_in_latest` (`yes`, `no` or `unknown`, from a read-only look at current upstream code if
    you can reach it);
  - `public_upstream_report`, `in_current_scope`, `built`, `note`;
  - `disclosure_status` (`pending client decision`).

## Environment (`tasks/mockoon-ds/environment/Dockerfile`)
- **Base and code.** A small official base image. The repo goes into `/app` at the pinned commit,
  and `/app/.git` is then deleted.
- **Offline.** Install every dependency, tool and service the project and tests need; nothing may
  be downloaded at test time. Services start from `test.sh`.
- **Packages:** `patch`, `curl`, `ca-certificates`, `bash`, `git`.
- **Agent layer.** Append `harness/claude-code.Dockerfile.snippet` unchanged at the end.
- **No test code in the image.** The agent shares the container. Pre-build against stubs; `test.sh`
  copies the real tests in at grading time.
- **Project tests.** The project's own tests for the affected area must pass in the image at the
  pinned commit.
- **No leaked regression tests.** The pinned commit must not already contain the advisory's
  regression tests (check `git log` between the pinned and fix commits).

## Report to the solver (`tasks/mockoon-ds/instruction.md`)
**Write:**
- what the system is, at product level;
- one observed impact, with ONE concrete trigger at user level (HTTP request, CLI call or public API
  use);
- the security properties as **invariants**: who may do what to which data, or what attacker input
  must never achieve. Word each so it covers every tested route and shape ("no value of X may …").
  If there are several, give one natural list, never a count;
- every **contract** the tests need:
  - the refusal form ("a client error with no side effect");
  - any interface or field name a test uses;
  - preservation clauses ("works exactly as today");
  - a legitimate magnitude next to any attack magnitude;
- that examples are examples, not the full set;
- the standard constraints block: fix the problem and its close variants; keep legitimate use
  working; do not modify or add tests; do not look up the upstream fix; do not special-case the
  example.

**Never write:**
- file, package, function, class, field or parameter names a user would not see;
- line numbers, the root cause, the fix approach, or a CVE or GHSA id;
- a list of routes, spellings or roles;
- restricting adverbs ("directly", "only via");
- anything that names or paraphrases a far site, an uncovered route or an injected sibling.

Put every identifier that must not appear in `manifest.leak_terms`.

## Tests (`tasks/mockoon-ds/tests/`)
- **`security/`:** one test per site, route, input shape and form. Each one:
  - goes through the real entry point;
  - fails on the pinned code and passes on a correct fix;
  - asserts the attack is blocked: any client error plus no side effect, never one exact status.
- **`functional/`:**
  - legitimate use, including the coupled behaviour of every lever;
  - where they exist, the project's own tests for the area.
- **No product code in a test's bookkeeping.** Compute expected values and clean-ups in the test
  itself, because a hardened helper must not crash a test.
- **Stubs** of permission or authority answer per resource and verb, like the real thing.
- **Scope.** A test may vary only what the instruction names, and drive only the entry point it
  names.
- **No network**, and nothing that depends on the fix commit being present.
- **Templates.** JUnit XML into the two directories the template names. Copy `score.py` unchanged.
  Edit only the marked command lines of `test.sh`, and keep its agent-kill block.

## Proof
- **The oracle.** `solution/fix.patch` is the published fix reduced to source changes, plus fixes
  for every uncovered route and injected sibling in the task. `solution/solve.sh` applies it to
  `/app`.
- **Wrong-fix patches** go in `build/mockoon-ds/checks/`, listed in `manifest.patch_checks`:
  - one `security_fail` per lever (the fix that misses only that lever);
  - a `functional_fail` (an over-broad or feature-removing fix);
  - a `pass` of kind `hardening` (the oracle plus defensive hardening of the product code the
    security tests import);
  - a `pass` alternative fix where a second valid design is plausible.
- **`manifest.wrong_fix_catalogue`:** for each class, a `checks/` patch, or `n/a: <why>`:
  `refuse_all`, `crash_as_refusal`, `wrong_resource`, `one_role_or_direction`, `reads_only`,
  `check_after_adjustment`, `unlisted_route`, `malformed_identity`, `missing_authority`,
  `adjacent_api`.

## Deliverables
**`tasks/mockoon-ds/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/mockoon-ds/manifest.json`:**
- `slug`, `candidate`;
- `pattern`: `A`;
- `builder_prompt_version`: `build-v1`;
- `"strict_gate": true`;
- `verified`: entry point, sites, routes, services, project tests run;
- `leak_terms`, `patch_checks`, `wrong_fix_catalogue`;
- `traps`: one entry per lever, with `shape`, `where` (file:line), `security_tests`,
  `coupled_functional_tests`, `security_fail_patch`, and `realistic_because` (for pattern B: "real,
  unmodified upstream code");
- `status`.

**Also in `build/mockoon-ds/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py mockoon-ds --only static
python3 -I builder/gate.py mockoon-ds --only nop
python3 -I builder/gate.py mockoon-ds --only oracle
python3 -I builder/gate.py mockoon-ds --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/mockoon-ds/`;
  - edit only `tasks/mockoon-ds/`, `build/mockoon-ds/` and, for pattern B, the register;
  - do not commit.

## Stop and report instead of shipping when
- the flaw does not reproduce through a real entry point at the pinned commit;
- a planned route or site is not reachable, or the check calls the producer directly (substitute
  another lever the code supports if you can, and say so);
- the task needs network at run time, or a GPU, kernel or GUI;
- the tests are flaky;
- no design meets the bar.

## Report back (under 400 words)
- The gate result for each stage.
- Each lever in one line: pattern, shape, file:line, reason to dismiss.
- Pattern B: each register row.
- The instruction's word count.
- Every guess you could not verify.
- Any fairness concern you see yourself.
- Anything noticed outside the scope, in one line.
- If abandoned, exactly why.
