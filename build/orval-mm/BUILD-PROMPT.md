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

Project root: `/home/mara/cwe-bench`. Task: `orval-mm`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: ["GHSA-2H9G-J24R-H63G", "CVE-2026-71869"]; orval-labs/orval; code injection into generated source (improper output escaping for JS/TS template and string literals; CWE-94/116/1336)
- Pinned (vulnerable) commit: unknown (parent of 8ef1bfdf3f9bcaf9dabfbe2e42887f1c0e159ab6; parent_commit not given). Published fix: 8ef1bfdf3f9bcaf9dabfbe2e42887f1c0e159ab6.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "7522",
 "advisory_ids": [
  "GHSA-2H9G-J24R-H63G",
  "CVE-2026-71869"
 ],
 "repo": "orval-labs/orval",
 "pinned_commit": "unknown (parent of 8ef1bfdf3f9bcaf9dabfbe2e42887f1c0e159ab6; parent_commit not given)",
 "fix_commits": [
  "8ef1bfdf3f9bcaf9dabfbe2e42887f1c0e159ab6"
 ],
 "trust_decision": {
  "summary": "Strings from the OpenAPI document (schema defaults, property names, paths, server URLs/variable defaults) are treated as data and must be escaped for the literal they get embedded in (template literal, single- or double-quoted string, object key) in generated TS modules; decided per emit site in the code generators.",
  "evidence": [
   "packages/zod/src/index.ts:842-846",
   "packages/zod/src/index.ts:817-836",
   "packages/zod/src/index.ts:1521",
   "packages/core/src/getters/keys.ts:4",
   "packages/core/src/getters/route.ts:34-66",
   "packages/core/src/getters/route.ts:94-115",
   "packages/core/src/getters/route.ts:161-179"
  ]
 },
 "landing_point": {
  "where": "packages/zod/src/index.ts:842-846",
  "why": "The summary names 'array-items default -> zod module-level template literal'; this is where stringify() output of schema.default has its single quotes swapped for backticks and is emitted as `export const xDefault = ...`."
 },
 "fix_sites": [
  {
   "where": "packages/zod/src/index.ts:842-846",
   "entry_point": "orval CLI / generate() with output.client 'zod' (schema default -> module-level const)",
   "module_kind": "code generator (zod output package)"
  },
  {
   "where": "packages/zod/src/index.ts:817-836",
   "entry_point": "orval CLI / generate() with client 'zod', object-typed schema default (keys emitted bare)",
   "module_kind": "code generator (zod output package)"
  },
  {
   "where": "packages/zod/src/index.ts:1519-1521",
   "entry_point": "orval CLI / generate() with client 'zod' in zod-mini mode (property-name keys)",
   "module_kind": "code generator (zod output package, mini variant)"
  },
  {
   "where": "packages/zod/src/index.ts:1870",
   "entry_point": "orval CLI / generate() with client 'zod', merged/allOf object properties",
   "module_kind": "code generator (zod output package)"
  },
  {
   "where": "packages/zod/src/index.ts:2054-2056",
   "entry_point": "orval CLI / generate() with client 'zod', classic object properties",
   "module_kind": "code generator (zod output package)"
  },
  {
   "where": "packages/core/src/getters/keys.ts:4",
   "entry_point": "orval CLI / generate(): model types (packages/core/src/getters/object.ts:500), query params (packages/core/src/getters/query-params.ts:191), mock objects (packages/mock/src/faker/getters/object.ts:285)",
   "module_kind": "shared core helper (lower-level getter)"
  },
  {
   "where": "packages/core/src/getters/route.ts:34-66",
   "entry_point": "orval CLI / generate() for every HTTP client; getRoute called at packages/orval/src/api.ts:47",
   "module_kind": "shared core helper (route getter)"
  },
  {
   "where": "packages/core/src/getters/route.ts:94-115",
   "entry_point": "orval CLI / generate() with baseUrl.getBaseUrlFromSpecification (servers[].url and variable defaults); packages/orval/src/api.ts:99",
   "module_kind": "shared core helper (base-URL / defaults route)"
  },
  {
   "where": "packages/core/src/getters/route.ts:161-179",
   "entry_point": "orval CLI / generate() with react-query/vue-query clients (query keys), packages/query/src/frameworks/index.ts:81",
   "module_kind": "shared core helper (route-as-array)"
  },
  {
   "where": "packages/query/src/mutation-generator.ts:353",
   "entry_point": "orval CLI / generate() with query client and mutation invalidation config",
   "module_kind": "wrapper/composition in query package"
  }
 ],
 "O1_entry_points": 5,
 "O2_out_of_scope_site": {
  "kind": "defaults_or_merge_route",
  "where": "packages/core/src/getters/route.ts:94-115 (servers[].url / server variable defaults reached only with baseUrl.getBaseUrlFromSpecification); also lower-level getter packages/core/src/getters/keys.ts:4"
 },
 "O3_reason_to_dismiss": "The report is about zod schema defaults; route/server-URL handling and the shared getKey helper live in @orval/core, are used by every client and look like a separate 'path/baseUrl' feature, and the effect package is a different output target that 'is not zod'.",
 "O4_distance": {
  "files": 4,
  "packages": 3,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Legitimate {param} path templates must still become ${param} interpolations (and query-key array elements) while static text is escaped; `$` without `{` stays literal; backslashes in defaults (e.g. 'C:\\logs\\') must round-trip; non-string defaults (numbers, booleans, nested objects) and array-with-enum-items inlining must keep working.",
  "where": "packages/core/src/getters/route.ts:49-51; packages/core/src/getters/route.ts:170-176; packages/zod/src/index.ts:849-859"
 },
 "O6_input_shapes": [
  "string schema default (backtick / ${ / backslash)",
  "array-of-string default and arrays containing nested arrays/objects",
  "enum-typed string default",
  "object default keys (non-identifier keys)",
  "schema property names containing double quotes",
  "non-identifier keys with single quote/backslash (getKey)",
  "path static segments and mixed segments with ${...} before {param}",
  "servers[].url without variables and with variable defaults",
  "single quote in route segments for query-key arrays",
  "mutation-invalidation prefix that bypassed getRoute"
 ],
 "O7_producer": {
  "kind": "serializer",
  "where": "packages/core/src/utils/string.ts:23-72 (stringify escapes for single-quoted literals only; zod then swaps quotes to backticks at packages/zod/src/index.ts:846)",
  "check_calls_producer": true
 },
 "O8_uncovered_routes": [
  {
   "route": "Effect output generator emits schema.default via stringify() with ' swapped for backticks into a module-level const - the identical template-literal sink, untouched by the fix.",
   "where": "packages/effect/src/index.ts:298-302",
   "reason_to_dismiss": "Advisory title says 'zod'; effect is a separate output target package, and its object-default branch already uses JSON.stringify keys (packages/effect/src/index.ts:273), so it looks already hardened.",
   "distance": "different package (packages/effect vs packages/zod), same shape of code",
   "present_in_latest": "no",
   "latest_where": "latest/packages/effect/src/index.ts:436-443"
  },
  {
   "route": "Hono generator embeds getRoute() output in single-quoted literals (route registration and Context type); the fix escapes only for backtick context, so ' in a spec path is unescaped there.",
   "where": "packages/hono/src/index.ts:170-172",
   "reason_to_dismiss": "Hono is a server-side generator, not a client/zod; getRoute was 'already fixed' in core, and the second site is in a type position.",
   "distance": "different package (packages/hono), consumes the fixed core getter",
   "present_in_latest": "no",
   "latest_where": "latest/packages/hono/src/index.ts:186-192"
  },
  {
   "route": "Hono Context type string '${getRoute(pathRoute)}' - same single-quote context, also untouched.",
   "where": "packages/hono/src/index.ts:756-758",
   "reason_to_dismiss": "It is a TypeScript type argument, so a solver may argue nothing executes there.",
   "distance": "same file as previous route",
   "present_in_latest": "no",
   "latest_where": "latest/packages/hono/src/index.ts:779-780"
  }
 ],
 "O8b_injection_room": [
  {
   "where": "packages/zod/src/index.ts:454-456",
   "sibling": "the $ref-sibling default path could plausibly be written with the same backtick swap as the main default path",
   "why_realistic": "It is a second default-emission path in the same file, written separately from the main one; a maintainer copying the main path would carry the replaceAll over."
  },
  {
   "where": "packages/core/src/generators/factory.ts:486-492",
   "sibling": "date-typed default emitted raw inside new Date('...')",
   "why_realistic": "Same pattern as zod's isDateType branch but hand-quoted instead of JSON.stringify; already looks like this at the pinned commit (noted out of scope, see notes)."
  }
 ],
 "O9_family": "code injection into generated source (improper output escaping for JS/TS template and string literals; CWE-94/116/1336)",
 "O9_dos": false,
 "O10_build": {
  "language": "TypeScript",
  "toolchain": "bun 1.3.14 (packageManager) + vite-plus 'vp run' monorepo scripts, vitest",
  "services": [],
  "offline_after_build": true,
  "project_tests": "vitest unit tests: packages/zod/src/zod.test.ts, packages/core/src/getters/route.test.ts, packages/core/src/utils/string.test.ts; root 'test' script at package.json:23"
 },
 "O11_fix_minutes": 75,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "packages/zod/src/index.ts, packages/core/src/getters/route.ts, packages/core/src/getters/keys.ts, packages/query/src/mutation-generator.ts",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Escape backticks and ${ only for the string default at packages/zod/src/index.ts:846 (or drop the backtick swap), leaving array items, object/property keys, core route/server-URL getters, effect and hono untouched."
 },
 "out_of_scope_notes": [
  "packages/core/src/generators/factory.ts:491 emits a date default unescaped inside new Date('...'); this is a different generator, not pursued.",
  "c_sibling_advisories=8 and the route.test.ts describe names GHSA-88f2-fpv8-89q2 (fix.diff:108); this fix bundles changes for at least one sibling advisory, so some fix sites belong to siblings rather than this GHSA."
 ],
 "unverified": [
  "pinned commit hash not provided (parent_commit null); no git access used.",
  "repo size in MB not measured (no shell/du).",
  "O1 count is an estimate from callers of the changed helpers (zod client, all HTTP clients via getRoute, baseUrl-from-spec, query-key arrays, getKey via models/mock/query params).",
  "Whether a single quote in a hono route can actually break out in the generated file was not exercised; inferred from the source and the later latest/ fix.",
  "Whether the effect sink is covered by one of the 8 sibling advisories was not checked; the latest code fixes it with a comment that describes the same mechanism.",
  "Offline build assumes dependencies are pre-installed; bun/vite-plus offline behaviour not tested."
 ]
}
  ```
- Published fix sites:   - packages/zod/src/index.ts:842-846 — entry point: orval CLI / generate() with output.client 'zod' (schema default -> module-level const) [code generator (zod output package)]
  - packages/zod/src/index.ts:817-836 — entry point: orval CLI / generate() with client 'zod', object-typed schema default (keys emitted bare) [code generator (zod output package)]
  - packages/zod/src/index.ts:1519-1521 — entry point: orval CLI / generate() with client 'zod' in zod-mini mode (property-name keys) [code generator (zod output package, mini variant)]
  - packages/zod/src/index.ts:1870 — entry point: orval CLI / generate() with client 'zod', merged/allOf object properties [code generator (zod output package)]
  - packages/zod/src/index.ts:2054-2056 — entry point: orval CLI / generate() with client 'zod', classic object properties [code generator (zod output package)]
  - packages/core/src/getters/keys.ts:4 — entry point: orval CLI / generate(): model types (packages/core/src/getters/object.ts:500), query params (packages/core/src/getters/query-params.ts:191), mock objects (packages/mock/src/faker/getters/object.ts:285) [shared core helper (lower-level getter)]
  - packages/core/src/getters/route.ts:34-66 — entry point: orval CLI / generate() for every HTTP client; getRoute called at packages/orval/src/api.ts:47 [shared core helper (route getter)]
  - packages/core/src/getters/route.ts:94-115 — entry point: orval CLI / generate() with baseUrl.getBaseUrlFromSpecification (servers[].url and variable defaults); packages/orval/src/api.ts:99 [shared core helper (base-URL / defaults route)]
  - packages/core/src/getters/route.ts:161-179 — entry point: orval CLI / generate() with react-query/vue-query clients (query keys), packages/query/src/frameworks/index.ts:81 [shared core helper (route-as-array)]
  - packages/query/src/mutation-generator.ts:353 — entry point: orval CLI / generate() with query client and mutation invalidation config [wrapper/composition in query package]
- Uncovered routes to confirm (pattern B):   - packages/effect/src/index.ts:298-302 — Effect output generator emits schema.default via stringify() with ' swapped for backticks into a module-level const - the identical template-literal sink, untouched by the fix. (reason to dismiss: Advisory title says 'zod'; effect is a separate output target package, and its object-default branch already uses JSON.stringify keys (packages/effect/src/index.ts:273), so it looks already hardened.; still in latest: no)
  - packages/hono/src/index.ts:170-172 — Hono generator embeds getRoute() output in single-quoted literals (route registration and Context type); the fix escapes only for backtick context, so ' in a spec path is unescaped there. (reason to dismiss: Hono is a server-side generator, not a client/zod; getRoute was 'already fixed' in core, and the second site is in a type position.; still in latest: no)
  - packages/hono/src/index.ts:756-758 — Hono Context type string '${getRoute(pathRoute)}' - same single-quote context, also untouched. (reason to dismiss: It is a TypeScript type argument, so a solver may argue nothing executes there.; still in latest: no)
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

## Environment (`tasks/orval-mm/environment/Dockerfile`)
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

## Report to the solver (`tasks/orval-mm/instruction.md`)
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

## Tests (`tasks/orval-mm/tests/`)
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
- **Wrong-fix patches** go in `build/orval-mm/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/orval-mm/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/orval-mm/manifest.json`:**
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

**Also in `build/orval-mm/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py orval-mm --only static
python3 -I builder/gate.py orval-mm --only nop
python3 -I builder/gate.py orval-mm --only oracle
python3 -I builder/gate.py orval-mm --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/orval-mm/`;
  - edit only `tasks/orval-mm/`, `build/orval-mm/` and, for pattern B, the register;
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
