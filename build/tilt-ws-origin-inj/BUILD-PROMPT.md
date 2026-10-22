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

Project root: `/home/mara/cwe-bench`. Task: `tilt-ws-origin-inj`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: GHSA-6M68-R693-78QX / CVE-2026-55883 - tilt-dev/tilt - CSRF / cross-site WebSocket hijacking (missing origin/token authentication on local web UI). Whether a request may open the HUD websocket / read HUD state is decided in the upgrader's CheckOrigin (csrf query param OR same-origin fallback that 
- Pinned (vulnerable) commit: 65ddaecbdbe3bc733ddaed6ea471afb1ebd4307d. Published fix: 47393fba7f6ef5e305d5e814551feef8e4acbc0a.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "16199",
 "advisory_ids": [
  "GHSA-6M68-R693-78QX",
  "CVE-2026-55883",
  "GO-2026-5181"
 ],
 "repo": "tilt-dev/tilt",
 "pinned_commit": "parent of 47393fba7f6ef5e305d5e814551feef8e4acbc0a (parent_commit not given in candidate)",
 "fix_commits": [
  "47393fba7f6ef5e305d5e814551feef8e4acbc0a"
 ],
 "trust_decision": {
  "summary": "Whether a request may open the HUD websocket / read HUD state is decided in the upgrader's CheckOrigin (csrf query param OR same-origin fallback that passes when Origin is absent), and the HUD HTTP routes, including the csrf-token issuer /api/websocket_token, have no session-token check at all.",
  "evidence": [
   "internal/hud/server/websocket.go:49-56",
   "internal/hud/server/gorilla/origin.go:16-25",
   "internal/hud/server/server.go:84-94",
   "internal/hud/server/server.go:307-310"
  ]
 },
 "landing_point": {
  "where": "internal/hud/server/websocket.go:49-56",
  "why": "The summary names cross-site WebSocket hijacking of the HUD stream; the upgrader's CheckOrigin with its origin fallback is the obvious first stop."
 },
 "fix_sites": [
  {
   "where": "internal/hud/server/websocket.go:49-56",
   "entry_point": "GET /ws/view (websocket upgrade, HUD stream)",
   "module_kind": "websocket handler config (core)"
  },
  {
   "where": "internal/hud/server/server.go:92",
   "entry_point": "GET /api/websocket_token (issuer of the websocket csrf token)",
   "module_kind": "HTTP route registration (core)"
  },
  {
   "where": "internal/hud/server/server.go:84",
   "entry_point": "GET /api/view",
   "module_kind": "HTTP route registration"
  },
  {
   "where": "internal/hud/server/server.go:85",
   "entry_point": "GET /api/dump/engine",
   "module_kind": "HTTP route registration"
  },
  {
   "where": "internal/hud/server/server.go:91",
   "entry_point": "GET /api/snapshot/{snapshot_id}",
   "module_kind": "HTTP route registration (dev-only route per comment at server.go:90)"
  },
  {
   "where": "internal/hud/server/server.go:86-89",
   "entry_point": "POST /api/analytics, /api/analytics_opt, /api/trigger, /api/override/trigger_mode",
   "module_kind": "HTTP route registration (state-changing)"
  },
  {
   "where": "internal/hud/server/server.go:94",
   "entry_point": "POST /api/set_tiltfile_args",
   "module_kind": "HTTP route registration (state-changing)"
  },
  {
   "where": "internal/hud/server/server.go:74",
   "entry_point": "all HUD router routes (new originCheckMiddleware, fix.diff:230)",
   "module_kind": "router middleware"
  },
  {
   "where": "internal/hud/server/server.go:109-116",
   "entry_point": "GET / (asset server; sets Tilt-Token cookie, fix adds SameSite=Strict)",
   "module_kind": "cookie wrapper"
  },
  {
   "where": "internal/hud/server/controller.go:163",
   "entry_point": "/proxy/* on web port (proxy to tilt apiserver uibuttons)",
   "module_kind": "wrapper_or_composition (kubectl proxy handler in separate controller file)"
  },
  {
   "where": "internal/hud/server/controller.go:144",
   "entry_point": "/debug/pprof on apiserver port",
   "module_kind": "debug mux (loopbackOnly)"
  },
  {
   "where": "internal/hud/server/controller.go:160",
   "entry_point": "/debug/pprof on web port",
   "module_kind": "debug mux (loopbackOnly)"
  },
  {
   "where": "internal/cli/utils.go:21-45",
   "entry_point": "CLI: tilt dump view/engine, tilt trigger, tilt snapshot create (apiGet/apiPostJson)",
   "module_kind": "client side, must send X-Tilt-Token to keep working"
  }
 ],
 "O1_entry_points": 5,
 "O2_out_of_scope_site": {
  "kind": "wrapper_or_composition",
  "where": "internal/hud/server/controller.go:163 (/proxy handler composed onto web router outside HeadsUpServer.Router); also the csrf-token issuer route internal/hud/server/server.go:92"
 },
 "O3_reason_to_dismiss": "/proxy only forwards uibuttons to the apiserver and its comment (internal/hud/server/controller.go:275-280) argues same-origin policy is sufficient; /api/websocket_token looks harmless because a cross-site page cannot read its response.",
 "O4_distance": {
  "files": 4,
  "packages": 2,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "The CLI 'tilt logs' dials /ws/view with no csrf param and no Origin header, relying on the origin fallback; 'tilt dump'/'tilt trigger' call HUD routes with no token; the web HUD fetches /api/websocket_token with the cookie then opens the socket with ?csrf=. A fix that drops the fallback or gates routes without updating clients breaks these. The published fix itself did not update tilt logs; upstream later added a csrf fetch (latest/internal/hud/client/log_streamer.go:41).",
  "where": "internal/hud/client/log_streamer.go:36-50; internal/cli/utils.go:21-45; web/src/AppController.ts:43-46"
 },
 "O6_input_shapes": [
  "websocket upgrade with Origin header absent (non-browser client)",
  "websocket upgrade with Origin matching Host (same-origin / host-header-controlled)",
  "websocket upgrade with valid ?csrf= query param",
  "session token presented via X-Tilt-Token header",
  "session token presented via Tilt-Token cookie",
  "cross-origin Origin header on any HUD route (originCheckMiddleware)"
 ],
 "O7_producer": {
  "kind": "config_loader",
  "where": "internal/token/token.go:19 (GetOrCreateToken from ~/.tilt-dev; CLI must load it to send X-Tilt-Token, fix.diff:40-50)",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [],
 "O8b_injection_room": [
  {
   "where": "internal/hud/server/server.go:84-94",
   "sibling": "an additional read-only HUD JSON route (e.g. a per-resource view or log dump) registered with plain HandleFunc",
   "why_realistic": "Routes are registered ad hoc in one list; a maintainer adding a debug/view endpoint would copy the HandleFunc style."
  },
  {
   "where": "internal/hud/server/controller.go:159-164",
   "sibling": "a second composed handler on webRouter (e.g. another apiserver proxy prefix) mounted outside HeadsUpServer.Router",
   "why_realistic": "/proxy already shows this composition pattern, bypassing anything applied only inside the HUD router."
  },
  {
   "where": "internal/snapshots/server.go:61-69",
   "sibling": "a websocket/live-view endpoint on the snapshot view server",
   "why_realistic": "A second server reusing the HUD assets; a maintainer could add a live stream there without the HUD's token plumbing."
  }
 ],
 "O9_family": "CSRF / cross-site WebSocket hijacking (missing origin/token authentication on local web UI)",
 "O9_dos": false,
 "O10_build": {
  "language": "Go (plus TypeScript web UI, not needed for the server tests)",
  "toolchain": "go 1.25.5 (go.mod:3), vendored modules",
  "services": [],
  "offline_after_build": true,
  "project_tests": "internal/hud/server/server_test.go, internal/hud/server/apiserver_test.go, internal/hud/server/websocket_test.go, internal/hud/client/log_streamer_test.go; fix adds TestRequireToken* in internal/hud/server/server_test.go (absent at pinned commit)"
 },
 "O11_fix_minutes": 45,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "A",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "internal/hud/server/websocket.go, internal/hud/server/server.go, internal/hud/server/controller.go, internal/hud/server/gorilla/origin.go (deleted), internal/cli/utils.go, internal/cli/flags.go (help text only)",
  "j_sibling_sites": "no",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Delete the origin fallback in CheckOrigin (or reject empty Origin) and stop, leaving /api/websocket_token, /api/view, /api/dump/engine, /api/snapshot and /proxy ungated and clients unupdated."
 },
 "out_of_scope_notes": [
  "cookieWrapper (internal/hud/server/server.go:109-116) hands the session token to any unauthenticated GET /, so a non-browser network client can obtain the token requireToken checks; fix only adds SameSite, still present in latest/internal/hud/server/server.go:140-152.",
  "requireToken is bypassable by env TILT_DISABLE_HUD_AUTH=1 (fix.diff:315), a deliberate operator switch.",
  "/debug/pprof exposure (controller.go:144,160) is an information-exposure issue bundled into the same fix."
 ],
 "unverified": [
  "pinned_commit hash not given (parent_commit null); assumed the repo dir is the fix's parent.",
  "repo_mb not measured (no shell); tilt with vendor/ is likely well above 5 MB, giant_repo not expected.",
  "Fairness risk: the published fix breaks 'tilt logs' (internal/hud/client/log_streamer.go:42 dials without csrf); hidden tests must either not require tilt logs or the reference fix must include the later log_streamer change.",
  "O1 counts read paths into HUD state (/ws/view, /api/websocket_token, /api/view, /api/dump/engine, /api/snapshot); the fix gates ~12 routes in total."
 ]
}
  ```
- Published fix sites:   - internal/hud/server/websocket.go:49-56 — entry point: GET /ws/view (websocket upgrade, HUD stream) [websocket handler config (core)]
  - internal/hud/server/server.go:92 — entry point: GET /api/websocket_token (issuer of the websocket csrf token) [HTTP route registration (core)]
  - internal/hud/server/server.go:84 — entry point: GET /api/view [HTTP route registration]
  - internal/hud/server/server.go:85 — entry point: GET /api/dump/engine [HTTP route registration]
  - internal/hud/server/server.go:91 — entry point: GET /api/snapshot/{snapshot_id} [HTTP route registration (dev-only route per comment at server.go:90)]
  - internal/hud/server/server.go:86-89 — entry point: POST /api/analytics, /api/analytics_opt, /api/trigger, /api/override/trigger_mode [HTTP route registration (state-changing)]
  - internal/hud/server/server.go:94 — entry point: POST /api/set_tiltfile_args [HTTP route registration (state-changing)]
  - internal/hud/server/server.go:74 — entry point: all HUD router routes (new originCheckMiddleware, fix.diff:230) [router middleware]
  - internal/hud/server/server.go:109-116 — entry point: GET / (asset server; sets Tilt-Token cookie, fix adds SameSite=Strict) [cookie wrapper]
  - internal/hud/server/controller.go:163 — entry point: /proxy/* on web port (proxy to tilt apiserver uibuttons) [wrapper_or_composition (kubectl proxy handler in separate controller file)]
  - internal/hud/server/controller.go:144 — entry point: /debug/pprof on apiserver port [debug mux (loopbackOnly)]
  - internal/hud/server/controller.go:160 — entry point: /debug/pprof on web port [debug mux (loopbackOnly)]
  - internal/cli/utils.go:21-45 — entry point: CLI: tilt dump view/engine, tilt trigger, tilt snapshot create (apiGet/apiPostJson) [client side, must send X-Tilt-Token to keep working]
- Uncovered routes to confirm (pattern B): none
- Design plan from the lead: TRACK = INJECTED (breaker recipe: only injected-sibling tasks at a recurring trust decision have beaten both models; the mined batch was all solved).

RECURRING DECISION / PROTECTED SINK: Whether a request may open the HUD websocket / read HUD state is decided in the upgrader's CheckOrigin (csrf query param OR same-origin fallback that passes when Origin is absent), and the HUD HTTP routes, including the csrf-token issuer /api/websocket_token, 

STEP 1 - confirm the published fix's sites and these uncovered-route leads with tests on the pinned copy: none noted.
STEP 2 - INJECT 2 to 4 sibling vulnerabilities of the SAME mechanism into our pinned copy at these recurring sites (verify each by reading the code): internal/hud/server/server.go:84-94 -> an additional read-only HUD JSON route (e.g. a per-resource view or lo (realistic: Routes are registered ad hoc in one list; a maintainer addin); internal/hud/server/controller.go:159-164 -> a second composed handler on webRouter (e.g. another apiserver proxy p (realistic: /proxy already shows this composition pattern, bypassing any); internal/snapshots/server.go:61-69 -> a websocket/live-view endpoint on the snapshot view server (realistic: A second server reusing the HUD assets; a maintainer could a). Each sibling MUST be code a maintainer could plausibly have written (no tell-tale names/comments/shortcuts; match surrounding style), reachable through the real public entry point, covered by a stated invariant, placed where the published upstream fix never touches, and carry a DIFFERENT plausible reason-to-dismiss from the others (legacy/compat path, internal/trusted caller, unsupported combination, neighbouring feature). Distinct reasons-to-dismiss are the lever.
STEP 3 - hidden security tests require closing the base flaw, every uncovered route AND every injected sibling through the real entry point. The oracle closes all; a fix that closes only the obvious sites must score < 1.0 (add a security_fail check patch for exactly that partial fix).
STEP 4 - COUPLED MUST-KEEP-WORKING (one functional test per trap): The CLI 'tilt logs' dials /ws/view with no csrf param and no Origin header, relying on the origin fallback; 'tilt dump'/'tilt trigger' call HUD routes with no token; the web HUD fetches /api/websocket (near internal/hud/client/log_streamer.go:36-50; interna); keep every legitimate use of the mechanism working.

Aim for >=3 levers with DIFFERENT reasons to dismiss. Every sibling must be findable by a blind engineer from instruction.md + code; if not, drop it. instruction.md stays product-level: system, one impact with one user trigger, invariants covering EVERY route/sibling (a natural list, no count); never name files/functions/fields/CVEs (all in manifest.leak_terms). Register each sibling and route in build/audit/uncovered-routes.tsv.
- Host notes: Language: Go (plus TypeScript web UI, not needed for the server tests). Offline after build, no external services. INJECTED: siblings go in OUR copy only, register them. Recurring trust decision (5 entry points) + screener injection room. Build+test via real entry points; project's own area tests pass at the pinned commit. Pin at the vulnerable commit; keep unrelated earlier fixes.

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

## Environment (`tasks/tilt-ws-origin-inj/environment/Dockerfile`)
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

## Report to the solver (`tasks/tilt-ws-origin-inj/instruction.md`)
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

## Tests (`tasks/tilt-ws-origin-inj/tests/`)
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
- **Wrong-fix patches** go in `build/tilt-ws-origin-inj/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/tilt-ws-origin-inj/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/tilt-ws-origin-inj/manifest.json`:**
- `slug`, `candidate`;
- `pattern`: `A+B`;
- `builder_prompt_version`: `build-v1`;
- `"strict_gate": true`;
- `verified`: entry point, sites, routes, services, project tests run;
- `leak_terms`, `patch_checks`, `wrong_fix_catalogue`;
- `traps`: one entry per lever, with `shape`, `where` (file:line), `security_tests`,
  `coupled_functional_tests`, `security_fail_patch`, and `realistic_because` (for pattern B: "real,
  unmodified upstream code");
- `status`.

**Also in `build/tilt-ws-origin-inj/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py tilt-ws-origin-inj --only static
python3 -I builder/gate.py tilt-ws-origin-inj --only nop
python3 -I builder/gate.py tilt-ws-origin-inj --only oracle
python3 -I builder/gate.py tilt-ws-origin-inj --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/tilt-ws-origin-inj/`;
  - edit only `tasks/tilt-ws-origin-inj/`, `build/tilt-ws-origin-inj/` and, for pattern B, the register;
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
