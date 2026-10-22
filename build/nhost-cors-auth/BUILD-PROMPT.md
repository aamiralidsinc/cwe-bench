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

Project root: `/home/mara/cwe-bench`. Task: `nhost-cors-auth`. Pattern: `A`. Track: `mined`.

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
- Advisory: GHSA-64CJ-QVX5-M4F3 / CVE-2026-47671 / GO-2026-5166 - nhost/nhost - missing authentication / overly permissive CORS on a local admin API (CWE-306, CWE-942-like), with secret exposure through the API. Which browser origins the local configserver (GraphQL config/secrets API plus logs API) answers is decided only by the engine-wide CORS middleware in serve(); the GraphQL auth directives are no-op stubs, and secrets are loaded in full into 
- Pinned (vulnerable) commit: da4e00011f773a2f219150549b2d32a1bd5ef582. Published fix: e407511627d2c2c1137a70e9ca1ca31095d23479.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "16048",
 "advisory_ids": [
  "GHSA-64CJ-QVX5-M4F3",
  "CVE-2026-47671",
  "GO-2026-5166"
 ],
 "repo": "nhost/nhost",
 "pinned_commit": "parent of e407511627d2c2c1137a70e9ca1ca31095d23479 (parent_commit not given in candidate)",
 "fix_commits": [
  "e407511627d2c2c1137a70e9ca1ca31095d23479"
 ],
 "trust_decision": {
  "summary": "Which browser origins the local configserver (GraphQL config/secrets API plus logs API) answers is decided only by the engine-wide CORS middleware in serve(); the GraphQL auth directives are no-op stubs, and secrets are loaded in full into the in-memory store that every resolver reads from.",
  "evidence": [
   "cli/cmd/configserver/configserver.go:161-171",
   "cli/cmd/configserver/configserver.go:83-98",
   "cli/cmd/configserver/local.go:94-105",
   "cli/cmd/configserver/local.go:132",
   "vendor/github.com/nhost/be/services/mimir/graph/router.go:34-36"
  ]
 },
 "landing_point": {
  "where": "cli/cmd/configserver/configserver.go:170",
  "why": "The summary says 'cross-origin unauthenticated'. `cors.Default()` (allow-all origins) is the only origin control on the configserver router, so this is the first place to look."
 },
 "fix_sites": [
  {
   "where": "cli/cmd/configserver/configserver.go:170",
   "entry_point": "HTTP POST /v1/configserver/graphql and /v1/logs/graphql (engine-wide middleware), started by hidden CLI `nhost configserver`",
   "module_kind": "server setup / router middleware"
  },
  {
   "where": "internal/lib/oapi/middleware/cors.go:87-92",
   "entry_point": "public Go API oapimw.CORS(CORSOptions) (shared with services/auth and services/storage); new AllowOriginFunc",
   "module_kind": "lower-level shared library"
  },
  {
   "where": "cli/cmd/configserver/local.go:94-105",
   "entry_point": "GetApps loader at configserver startup; feeds GraphQL appSecrets/appsSecrets/config(resolve)/configRawJSON(resolve)/runServiceConfig(resolve)",
   "module_kind": "config loader (storage plugin)"
  },
  {
   "where": "cli/cmd/configserver/local.go:164-180",
   "entry_point": "GraphQL mutations insertSecret/updateSecret/deleteSecret -> plugin UpdateSecrets (persist to .secrets)",
   "module_kind": "save/persist path (storage plugin)"
  },
  {
   "where": "cli/cmd/configserver/local.go:134",
   "entry_point": "GraphQL queries/mutations keyed by appID (was fixed zero UUID)",
   "module_kind": "config loader"
  },
  {
   "where": "cli/cmd/configserver/configserver.go:147",
   "entry_point": "CLI `nhost configserver` new --app-id / NHOST_APP_ID flag",
   "module_kind": "CLI command"
  },
  {
   "where": "cli/cmd/dev/up.go:440",
   "entry_point": "CLI `nhost dev up` (creates .nhost/app_id via new cli/clienv/appid.go, fix.diff:43-69)",
   "module_kind": "CLI command / wiring"
  },
  {
   "where": "cli/cmd/dev/cloud.go:191",
   "entry_point": "CLI `nhost dev cloud` (passes proj.GetID() as app ID)",
   "module_kind": "CLI command / wiring"
  },
  {
   "where": "cli/dockercompose/configserver.go:85-88",
   "entry_point": "compose generation for `nhost dev up`/`cloud` (NHOST_APP_ID env)",
   "module_kind": "deployment wiring"
  },
  {
   "where": "cli/dockercompose/compose.go:341-344",
   "entry_point": "compose generation, dashboard env NEXT_PUBLIC_NHOST_APP_ID",
   "module_kind": "deployment wiring"
  },
  {
   "where": "fix.diff:869-886",
   "entry_point": "dashboard frontend getLocalAppId() (dashboard/src/utils/env/env.ts)",
   "module_kind": "frontend client"
  }
 ],
 "O1_entry_points": 2,
 "O2_out_of_scope_site": {
  "kind": "save_reload_or_serialization",
  "where": "cli/cmd/configserver/local.go:164-180 (UpdateSecrets writes newApp.Secrets back to .secrets). Once the loader redacts, this path must merge placeholders with the on-disk values (fix.diff:340-369). Second out-of-scope site: the shared lower-level CORS library internal/lib/oapi/middleware/cors.go:87-92, which had no predicate-based origin option."
 },
 "O3_reason_to_dismiss": "The report is about cross-origin access, so a solver sees restricting CORS in serve() as the complete fix: secret redaction in the loader and the save-path merge look like a separate 'secrets at rest' hardening, and the shared oapi CORS lib (used by auth/storage) looks like another product's code.",
 "O4_distance": {
  "files": 4,
  "packages": 3,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "The local dashboard at https://local.dashboard.local.nhost.run[:port], <sub>.dashboard.local.nhost.run and local.dashboard.nhost.run must keep making credentialed cross-origin GraphQL calls. Its updateSecret/insertSecret/deleteSecret mutations send the whole secrets list back, so a secret that comes back as the placeholder must keep its real on-disk value rather than being overwritten. Deny-all CORS or refusing placeholder-valued writes would break the dashboard.",
  "where": "cli/dockercompose/compose.go:347-349; cli/dockercompose/configserver.go:91-105; cli/cmd/configserver/local.go:164-180"
 },
 "O6_input_shapes": [
  "Origin with http or https scheme",
  "Origin with an optional non-standard port",
  "single-label <sub>.dashboard.local.nhost.run and bare local.dashboard.nhost.run (accepted)",
  "suffix-appended host (dashboard.local.nhost.run.evil.com), trailing path, multi-label subdomain, sibling host attacker.local.nhost.run, bare dashboard.local.nhost.run, localhost, empty origin (all rejected; fix.diff:215-237)",
  "secret mutation payload values: placeholder (keep on-disk value), real new value (write through), new name (insert), name omitted (delete) (fix.diff:505-554)"
 ],
 "O7_producer": {
  "kind": "config_loader",
  "where": "cli/cmd/configserver/local.go:94-105 (GetApps parses .secrets into the MapStore that all mimir resolvers read, including resolve:true config rendering at vendor/github.com/nhost/be/services/mimir/graph/schema.resolvers.go:146-161)",
  "check_calls_producer": true
 },
 "O8_uncovered_routes": [
  {
   "route": "The logs GraphQL websocket on the same configserver process has its own origin check, which accepts any http://localhost or 127.0.0.1 port and multi-label *.dashboard.local.nhost.run origins. That is looser than the new CORS regex, and the fix did not touch it.",
   "where": "cli/cmd/configserver/logsapi/router.go:27-44",
   "reason_to_dismiss": "It already has a deliberate, commented origin check. It serves container logs, not configuration or secrets. And the advisory's own test rejects http://localhost:3000 only for CORS (fix.diff:230).",
   "distance": "different package (cli/cmd/configserver/logsapi) from the landing point; 1 file",
   "present_in_latest": "yes",
   "latest_where": "latest/cli/cmd/configserver/logsapi/router.go:31-47"
  },
  {
   "route": "The fix randomises the app ID, but list queries that need no appID (configs, appsSecrets) return it, and their @hasRole guard is the no-op dummyMiddleware2. A same-origin or allowed caller can enumerate the ID.",
   "where": "vendor/github.com/nhost/be/services/mimir/schema/schema.graphqls:50-59",
   "reason_to_dismiss": "The app ID is not meant to be a secret, CORS is the real gate, and the schema is vendored upstream code.",
   "distance": "vendored package github.com/nhost/be/services/mimir; 2 files from landing point",
   "present_in_latest": "yes",
   "latest_where": "latest/vendor/github.com/nhost/be/services/mimir/schema/schema.graphqls:50-59"
  }
 ],
 "O8b_injection_room": [
  {
   "where": "cli/cmd/configserver/logsapi/router.go:59-65",
   "sibling": "Add a gqlgen multipart/form transport (or a REST import endpoint) on the configserver or logs router. It accepts CORS-safelisted content types, so a cross-origin write reaches the plugin without a preflight even with the new CORS.",
   "why_realistic": "Maintainers add multipart transports for uploads and import endpoints routinely. The mimir POST transport only accepts application/json (vendor/github.com/99designs/gqlgen/graphql/handler/transport/http_post.go:31-41), and that is what makes CORS sufficient today."
  },
  {
   "where": "cli/cmd/configserver/local.go:188-206",
   "sibling": "A run-service config persist path that writes resolved or secret-bearing env values back to disk, needing the same placeholder merge as UpdateSecrets.",
   "why_realistic": "UpdateRunServiceConfig is the parallel persist path in the same plugin. Run-service env values can carry secrets, and a maintainer adding redaction would naturally cover only .secrets."
  }
 ],
 "O9_family": "missing authentication / overly permissive CORS on a local admin API (CWE-306, CWE-942-like), with secret exposure through the API",
 "O9_dos": false,
 "O10_build": {
  "language": "Go (plus TypeScript dashboard, not needed for tests)",
  "toolchain": "go toolchain with vendored modules (vendor/), nix project files present",
  "services": [],
  "offline_after_build": true,
  "project_tests": "cli/cmd/configserver/local_test.go (GetApps/UpdateSecrets), cli/cmd/configserver/logsapi/router_test.go, internal/lib/oapi/middleware/cors_test.go; fix adds cli/cmd/configserver/configserver_test.go"
 },
 "O11_fix_minutes": 60,
 "O12_red_flags": [],
 "O13_recall_risk": "low",
 "pattern_fit": "A",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "cli/cmd/configserver/configserver.go, cli/cmd/configserver/local.go, internal/lib/oapi/middleware/cors.go, cli/clienv/appid.go, cli/clienv/filesystem.go, cli/cmd/dev/up.go, cli/cmd/dev/cloud.go, cli/dockercompose/compose.go, cli/dockercompose/compose_cloud.go, cli/dockercompose/configserver.go, services/auth/go/cmd/serve.go, services/storage/cmd/serve.go, dashboard/src/utils/env/env.ts, dashboard/src/features/orgs/utils/local-dashboard/index.ts, dashboard/docker-entrypoint.sh",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 0,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Replace cors.Default() with an origin allow-list (often a loose HasSuffix check or one copied from the websocket checker that admits localhost) and stop there, leaving secrets unredacted in the loader and the UpdateSecrets save path unmerged."
 },
 "out_of_scope_notes": [
  "The dashboard compose env embeds the Hasura admin secret as NEXT_PUBLIC_NHOST_ADMIN_SECRET (cli/dockercompose/compose.go:344); this is a separate exposure and was not pursued.",
  "services/auth uses CORS AllowedOrigins '*' (fix.diff:1065-1070); different service, not pursued."
 ],
 "unverified": [
  "pinned_commit hash not given (parent_commit null); assumed the repo tree is the parent of the fix commit.",
  "repo_mb not measured (no shell size tool used); monorepo with vendor/ and dashboard/ is very likely above 5 MB and below 1.5 GB.",
  "Did not trace whether mimir passes resolved (secret-substituted) config into UpdateConfig/UpdateRunServiceConfig; the O8b run-service sibling rests on code shape only.",
  "Hidden tests for O8 route 1 (websocket origin) would be behavioural over gorilla upgrader; feasibility assumed from existing logsapi/router_test.go, not read.",
  "O1 counts the two HTTP GraphQL endpoints behind the engine-wide CORS middleware; the CLI commands only wire the app ID and are not counted as flaw entry points.",
  "O7 check_calls_producer=true refers to the published redaction check living inside the loader; the CORS check itself does not call the loader."
 ]
}
  ```
- Published fix sites:   - cli/cmd/configserver/configserver.go:170 — entry point: HTTP POST /v1/configserver/graphql and /v1/logs/graphql (engine-wide middleware), started by hidden CLI `nhost configserver` [server setup / router middleware]
  - internal/lib/oapi/middleware/cors.go:87-92 — entry point: public Go API oapimw.CORS(CORSOptions) (shared with services/auth and services/storage); new AllowOriginFunc [lower-level shared library]
  - cli/cmd/configserver/local.go:94-105 — entry point: GetApps loader at configserver startup; feeds GraphQL appSecrets/appsSecrets/config(resolve)/configRawJSON(resolve)/runServiceConfig(resolve) [config loader (storage plugin)]
  - cli/cmd/configserver/local.go:164-180 — entry point: GraphQL mutations insertSecret/updateSecret/deleteSecret -> plugin UpdateSecrets (persist to .secrets) [save/persist path (storage plugin)]
  - cli/cmd/configserver/local.go:134 — entry point: GraphQL queries/mutations keyed by appID (was fixed zero UUID) [config loader]
  - cli/cmd/configserver/configserver.go:147 — entry point: CLI `nhost configserver` new --app-id / NHOST_APP_ID flag [CLI command]
  - cli/cmd/dev/up.go:440 — entry point: CLI `nhost dev up` (creates .nhost/app_id via new cli/clienv/appid.go, fix.diff:43-69) [CLI command / wiring]
  - cli/cmd/dev/cloud.go:191 — entry point: CLI `nhost dev cloud` (passes proj.GetID() as app ID) [CLI command / wiring]
  - cli/dockercompose/configserver.go:85-88 — entry point: compose generation for `nhost dev up`/`cloud` (NHOST_APP_ID env) [deployment wiring]
  - cli/dockercompose/compose.go:341-344 — entry point: compose generation, dashboard env NEXT_PUBLIC_NHOST_APP_ID [deployment wiring]
  - fix.diff:869-886 — entry point: dashboard frontend getLocalAppId() (dashboard/src/utils/env/env.ts) [frontend client]
- Uncovered routes to confirm (pattern B): none
- Design plan from the lead: MAIN LEVER: reproduce the published fix in full. Hidden tests require closing EVERY published fix site through its real entry point, including the out-of-scope-looking site (save_reload_or_serialization at cli/cmd/configserver/local.go:164-180 (UpdateSecrets writes newApp.Secrets back ; dismissable because: The report is about cross-origin access, so a solver sees restricting CORS in serve() as the complete fix: secret redaction in the loader and the save-path merge look like a separate 'secrets at rest'). Tempting wrong fix that must FAIL: Replace cors.Default() with an origin allow-list (often a loose HasSuffix check or one copied from the websocket checker that admits localhost) and stop there, leaving secrets unredacted in the loader.

INPUT-SHAPE / ROUTE VARIANTS (one security test each, through the real entry point, failing on pinned, passing on a correct fix): Origin with http or https scheme; Origin with an optional non-standard port; single-label <sub>.dashboard.local.nhost.run and bare local.dashboard.nhost.run (accepted); suffix-appended host (dashboard.local.nhost.run.evil.com), trailing path, multi-label subdomain, sibling host attacker.local.nhost.run, bare dashboard.local.nhost.run, localhost, empty origin (all rejected; fix.diff:215-237); secret mutation payload values: placeholder (keep on-disk value), real new value (write through), new name (insert), name omitted (delete) (fix.diff:505-554).

COUPLED MUST-KEEP-WORKING (one functional test per trap so an over-broad fix fails): The local dashboard at https://local.dashboard.local.nhost.run[:port], <sub>.dashboard.local.nhost.run and local.dashboard.nhost.run must keep making credentialed cross-origin GraphQL calls. Its updateSecret/insertSecret (near cli/dockercompose/compose.go:347-349; cli/dockercompose/conf).

Aim for at least two levers with DIFFERENT reasons to dismiss. instruction.md stays at product level: system, one observed impact with one user-level trigger, security property as invariants covering every tested route/shape; keep legitimate use working; never name files/functions/fields/CVEs (all such identifiers go in manifest.leak_terms).
- Host notes: Language: Go (plus TypeScript dashboard, not needed for tests). Offline after build, no external services. Test the security logic by calling the relevant functions/handlers directly with crafted inputs - do not stand up external services. Project's own tests for the area must pass at the pinned commit. Confirm each pattern-B route with a test on the pinned copy. Pin at the vulnerable commit; keep unrelated earlier fixes present.

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

## Environment (`tasks/nhost-cors-auth/environment/Dockerfile`)
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

## Report to the solver (`tasks/nhost-cors-auth/instruction.md`)
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

## Tests (`tasks/nhost-cors-auth/tests/`)
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
- **Wrong-fix patches** go in `build/nhost-cors-auth/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/nhost-cors-auth/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/nhost-cors-auth/manifest.json`:**
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

**Also in `build/nhost-cors-auth/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py nhost-cors-auth --only static
python3 -I builder/gate.py nhost-cors-auth --only nop
python3 -I builder/gate.py nhost-cors-auth --only oracle
python3 -I builder/gate.py nhost-cors-auth --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/nhost-cors-auth/`;
  - edit only `tasks/nhost-cors-auth/`, `build/nhost-cors-auth/` and, for pattern B, the register;
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
