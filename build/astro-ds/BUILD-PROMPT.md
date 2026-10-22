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

Project root: `/home/mara/cwe-bench`. Task: `astro-ds`. Pattern: `A`. Track: `injected`.

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
- Advisory: ["GHSA-8MV7-9C27-98VC", "CVE-2026-73423"]; withastro/astro; CSRF / missing origin check on alternate request-pipeline composition (CWE-352, authorization check placement)
- Pinned (vulnerable) commit: parent of 0b30b35f864310bee8485c952d1877e82e2b9b1a (parent_commit not given in candidate). Published fix: 0b30b35f864310bee8485c952d1877e82e2b9b1a.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "9987",
 "advisory_ids": [
  "GHSA-8MV7-9C27-98VC",
  "CVE-2026-73423"
 ],
 "repo": "withastro/astro",
 "pinned_commit": "parent of 0b30b35f864310bee8485c952d1877e82e2b9b1a (parent_commit not given in candidate)",
 "fix_commits": [
  "0b30b35f864310bee8485c952d1877e82e2b9b1a"
 ],
 "trust_decision": {
  "summary": "Whether a non-safe-method, form-like (or content-type-less) request on an on-demand route is same-origin before an action or endpoint/page runs. At the pinned commit this is decided only in the origin-check middleware, which is installed only inside the pipeline's resolved middleware chain, so composable dispatch primitives that do not go through that chain never check it.",
  "evidence": [
   "packages/astro/src/core/app/middlewares.ts:24-55",
   "packages/astro/src/core/base-pipeline.ts:265-278",
   "packages/astro/src/core/middleware/astro-middleware.ts:68-74"
  ]
 },
 "landing_point": {
  "where": "packages/astro/src/core/hono/index.ts:58-90",
  "why": "The summary names the composable `astro/hono` pipeline and the order of `middleware()`, so an engineer opens the Hono primitives (`middleware()`, `actions()`, `pages()`) first."
 },
 "fix_sites": [
  {
   "where": "packages/astro/src/actions/handler.ts:33-45",
   "entry_point": "astro/hono `actions()` (packages/astro/src/core/hono/index.ts:75-84) and the lower-level astro/fetch `actions(state)` (packages/astro/src/core/fetch/index.ts:146-154); also reached by the standard AstroHandler path (packages/astro/src/core/routing/handler.ts:59-67)",
   "module_kind": "shared handler module in another directory (src/actions), below the Hono wrapper"
  },
  {
   "where": "packages/astro/src/core/pages/handler.ts:110-120",
   "entry_point": "astro/hono `pages()` (packages/astro/src/core/hono/index.ts:86-90) and astro/fetch `pages(state)` (packages/astro/src/core/fetch/index.ts:102-110)",
   "module_kind": "shared dispatch handler (handleWithErrorFallback used only by the composable entry point)"
  },
  {
   "where": "packages/astro/src/core/app/middlewares.ts:1-66",
   "entry_point": "refactor: the check is pulled out into a shared predicate in the new core/app/origin-check.ts (fix.diff:156-188); the middleware keeps the same behaviour",
   "module_kind": "shared check module (refactor, no behaviour change)"
  },
  {
   "where": "packages/astro/src/core/base-pipeline.ts:14",
   "entry_point": "import path change only (fix.diff:223-224)",
   "module_kind": "pipeline core (no behaviour change)"
  }
 ],
 "O1_entry_points": 4,
 "O2_out_of_scope_site": {
  "kind": "lower_level_api",
  "where": "packages/astro/src/core/fetch/index.ts:1-8 (public `astro/fetch` API whose `actions()`/`pages()` at :102-110 and :146-154 reach the sinks); the fix lands in packages/astro/src/actions/handler.ts:33-45 and packages/astro/src/core/pages/handler.ts:110-120 rather than in the Hono wrapper"
 },
 "O3_reason_to_dismiss": "The report is about `astro/hono` ordering, so fixing it in hono/index.ts (reordering, or calling the origin check from the Hono `actions()`/`pages()` wrappers) looks complete. The lower-level `astro/fetch` primitives and the 'pages() with no middleware() at all' composition look like a different, unsupported setup, since users are 'supposed' to mount `middleware()`.",
 "O4_distance": {
  "files": 4,
  "packages": 1,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Same-origin form POSTs must still reach actions and endpoints. Cross-origin requests with a non-form content-type (for example application/json RPC or API calls), safe methods (GET/HEAD/OPTIONS), prerendered routes and `checkOrigin: false` must all pass. A fix that rejects every cross-origin non-GET request, or that ignores the manifest flag, breaks these.",
  "where": "packages/astro/src/core/app/middlewares.ts:10-17, packages/astro/src/core/app/middlewares.ts:28-50, packages/astro/src/types/public/config.ts:607-612"
 },
 "O6_input_shapes": [
  "content-type application/x-www-form-urlencoded, multipart/form-data or text/plain, matched case-insensitively as a substring (packages/astro/src/core/app/middlewares.ts:57-66)",
  "missing content-type header: rejected unless same-origin (packages/astro/src/core/app/middlewares.ts:45-50)",
  "any non-safe method: POST/PUT/PATCH/DELETE (packages/astro/src/core/app/middlewares.ts:17, :32-34)",
  "RPC action (`/_actions/<name>`) vs form action (`?_action=` on a page route) (packages/astro/src/actions/handler.ts:7-17)",
  "endpoint vs page route dispatched by pages() (packages/astro/src/core/pages/handler.ts:42-80)",
  "composition variants: actions() before middleware() (examples/advanced-routing/src/fetch.ts:24-27), or pages() with no middleware() (fix.diff:434-448)"
 ],
 "O7_producer": {
  "kind": "config_loader",
  "where": "packages/astro/src/manifest/serialized.ts:207-208 and packages/astro/src/core/build/plugins/plugin-manifest.ts:380-381 produce manifest.checkOrigin (true only for server build output)",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "Standard AstroHandler path (app.render / Hono `astro()`) when pipeline.middleware is undefined: getMiddleware returns a no-op without the origin check, and the endpoint/page dispatch via PagesHandler.handle is still unchecked after the fix (the fix checks only in handleWithErrorFallback).",
   "where": "packages/astro/src/core/base-pipeline.ts:263-278",
   "reason_to_dismiss": "The comment says middleware is undefined only for edge middleware, where the adapter is assumed to run the middleware (and the check) elsewhere.",
   "distance": "core/base-pipeline.ts plus core/routing/handler.ts:59-67, away from the hono/ landing point",
   "present_in_latest": "yes",
   "latest_where": "latest/packages/astro/src/core/middleware/load.ts:26-28"
  }
 ],
 "O8b_injection_room": [
  {
   "where": "packages/astro/src/core/hono/index.ts:44-48",
   "sibling": "A further composable primitive (for example a server-islands or endpoints-only dispatcher) that calls PagesHandler.handle directly instead of handleWithErrorFallback.",
   "why_realistic": "The primitives are thin wrappers added one at a time. A maintainer adding a new dispatcher would copy the `astro()`/`pages()` shape and reach PagesHandler.handle, which carries no check."
  },
  {
   "where": "packages/astro/src/core/rewrites/handler.ts:105-115",
   "sibling": "A rewrite path that dispatches through PagesHandler.handle while skipping the middleware chain (as the error handlers do with skipMiddleware).",
   "why_realistic": "The error handlers already set skipMiddleware (packages/astro/src/core/errors/default-handler.ts:116), so a maintainer could plausibly reuse that flag for rewrites, which drops the origin check."
  },
  {
   "where": "packages/astro/src/core/fetch/index.ts:146-154",
   "sibling": "A separate form-action helper in astro/fetch that runs getActionContext(...).action.handler() itself, without going through ActionHandler.handle.",
   "why_realistic": "The fetch API is documented as thin delegations to handlers, and an alternate action entry (for example for host-framework form posts) is a natural addition."
  }
 ],
 "O9_family": "CSRF / missing origin check on alternate request-pipeline composition (CWE-352, authorization check placement)",
 "O9_dos": false,
 "O10_build": {
  "language": "TypeScript",
  "toolchain": "Node.js + pnpm monorepo; the unit tests import from packages/astro/dist, so the package must be built first; hono is a test dependency",
  "services": [],
  "offline_after_build": true,
  "project_tests": "node:test units in packages/astro/test/units/app/csrf.test.ts (existing); the fix adds packages/astro/test/units/actions/action-origin-check.test.ts and packages/astro/test/units/hono/pages-origin-check.test.ts"
 },
 "O11_fix_minutes": 35,
 "O12_red_flags": [],
 "O13_recall_risk": "low",
 "pattern_fit": "A",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "packages/astro/src/actions/handler.ts, packages/astro/src/core/pages/handler.ts, packages/astro/src/core/app/middlewares.ts (moved to origin-check.ts), packages/astro/src/core/base-pipeline.ts",
  "j_sibling_sites": "unknown",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Reorder or patch only the Hono wrappers in core/hono/index.ts (or fix only actions(), as in the example) and leave the astro/fetch primitives and the pages()-without-middleware() endpoint dispatch unchecked."
 },
 "out_of_scope_notes": [
  "The container API hard-codes checkOrigin: false (packages/astro/src/container/index.ts:172); this is intentional for a test/render API and was not pursued.",
  "The docs say the check applies only to form content-types (packages/astro/src/types/public/config.ts:609-610), but the code also rejects cross-origin requests with no content-type (packages/astro/src/core/app/middlewares.ts:45-50); this is a doc/code mismatch and was not pursued."
 ],
 "unverified": [
  "pinned_commit SHA: parent_commit is null in the candidate and git was not run; the pinned tree is assumed to be the fix's parent.",
  "O8 edge route: whether pipeline.middleware is actually undefined at runtime in edge middleware mode, and whether the edge adapter runs the origin check, was not traced (packages/astro/src/core/build/plugins/plugin-manifest.ts:88-95 only hints at it); j_sibling_sites is therefore unknown.",
  "repo_mb: the repository size was not measured (no shell); the tiny/giant flags were not assessed but are unlikely for the astro monorepo.",
  "Whether the fix's ActionHandler check double-runs harmlessly on the standard AstroHandler path was reasoned from code, not tested."
 ]
}
  ```
- Published fix sites:   - packages/astro/src/actions/handler.ts:33-45 — entry point: astro/hono `actions()` (packages/astro/src/core/hono/index.ts:75-84) and the lower-level astro/fetch `actions(state)` (packages/astro/src/core/fetch/index.ts:146-154); also reached by the standard AstroHandler path (packages/astro/src/core/routing/handler.ts:59-67) [shared handler module in another directory (src/actions), below the Hono wrapper]
  - packages/astro/src/core/pages/handler.ts:110-120 — entry point: astro/hono `pages()` (packages/astro/src/core/hono/index.ts:86-90) and astro/fetch `pages(state)` (packages/astro/src/core/fetch/index.ts:102-110) [shared dispatch handler (handleWithErrorFallback used only by the composable entry point)]
  - packages/astro/src/core/app/middlewares.ts:1-66 — entry point: refactor: the check is pulled out into a shared predicate in the new core/app/origin-check.ts (fix.diff:156-188); the middleware keeps the same behaviour [shared check module (refactor, no behaviour change)]
  - packages/astro/src/core/base-pipeline.ts:14 — entry point: import path change only (fix.diff:223-224) [pipeline core (no behaviour change)]
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

## Environment (`tasks/astro-ds/environment/Dockerfile`)
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

## Report to the solver (`tasks/astro-ds/instruction.md`)
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

## Tests (`tasks/astro-ds/tests/`)
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
- **Wrong-fix patches** go in `build/astro-ds/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/astro-ds/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/astro-ds/manifest.json`:**
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

**Also in `build/astro-ds/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py astro-ds --only static
python3 -I builder/gate.py astro-ds --only nop
python3 -I builder/gate.py astro-ds --only oracle
python3 -I builder/gate.py astro-ds --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/astro-ds/`;
  - edit only `tasks/astro-ds/`, `build/astro-ds/` and, for pattern B, the register;
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
