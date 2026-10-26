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

Project root: `/home/mara/cwe-bench`. Task: `nuxt-mm`. Pattern: `A`. Track: `injected`.

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
- Advisory: ["GHSA-HXVH-4H3W-PRP9", "CVE-2026-71315"]; nuxt/nuxt; authorization bypass via case-sensitivity mismatch between route-rule matcher and case-insensitive vue-router (CWE-178/CWE-863)
- Pinned (vulnerable) commit: unknown (parent of 619963309e082190bac4a26b05f2dd155b039b81; parent_commit null in candidate). Published fix: 619963309e082190bac4a26b05f2dd155b039b81, ad624a75ad2d215f43633f6b40be346a7194d34d.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "11999",
 "advisory_ids": [
  "GHSA-HXVH-4H3W-PRP9",
  "CVE-2026-71315"
 ],
 "repo": "nuxt/nuxt",
 "pinned_commit": "unknown (parent of 619963309e082190bac4a26b05f2dd155b039b81; parent_commit null in candidate)",
 "fix_commits": [
  "619963309e082190bac4a26b05f2dd155b039b81",
  "ad624a75ad2d215f43633f6b40be346a7194d34d"
 ],
 "trust_decision": {
  "summary": "Which route rules (appMiddleware auth gates, redirect, ssr, appLayout, prerender) apply to a request path is decided by a build-time compiled rou3 matcher whose keys are inserted verbatim while the runtime lookup path is lower-cased, so any mixed-case rule key never matches and its middleware is silently dropped.",
  "evidence": [
   "packages/nitro-server/src/index.ts:395-405",
   "packages/nitro-server/src/index.ts:446-450",
   "packages/nuxt/src/app/composables/manifest.ts:68-76",
   "packages/nuxt/src/pages/runtime/plugins/router.ts:245-255"
  ]
 },
 "landing_point": {
  "where": "packages/nuxt/src/app/composables/manifest.ts:71",
  "why": "The summary names route rules and appMiddleware; the appMiddleware merge calls getRouteRules, whose body is the visible `path.toLowerCase()` added by the previous CVE fix."
 },
 "fix_sites": [
  {
   "where": "packages/nitro-server/src/index.ts:395-405",
   "entry_point": "nuxi build / nuxi dev (generation of #build/route-rules.mjs from nitro routeRules keys)",
   "module_kind": "build-time code generator / serializer of the matcher, separate package @nuxt/nitro-server"
  },
  {
   "where": "packages/nitro-server/src/index.ts:446-450",
   "entry_point": "runtime default export of #build/route-rules.mjs, called by getRouteRules, resolveLayoutName and prerender.server.ts on every SSR request and client navigation",
   "module_kind": "generated runtime code (string template)"
  },
  {
   "where": "packages/nitro-server/src/index.ts:533-539",
   "entry_point": "nuxi build / nuxi generate (app manifest prerendered list)",
   "module_kind": "build hook"
  },
  {
   "where": "packages/nuxt/src/app/composables/manifest.ts:71",
   "entry_point": "public auto-imported composable getRouteRules(); also used by router plugins for appMiddleware and by the redirect middleware",
   "module_kind": "public runtime API"
  },
  {
   "where": "packages/nuxt/src/pages/module.ts:527-532",
   "entry_point": "nuxi build (inject pages matching prerender: true rules)",
   "module_kind": "build hook in pages module"
  }
 ],
 "O1_entry_points": 3,
 "O2_out_of_scope_site": {
  "kind": "save_reload_or_serialization",
  "where": "packages/nitro-server/src/index.ts:395-450 (the keys are inserted at build time and serialised into the #build/route-rules.mjs template string; the runtime check in packages/nuxt/src/app/composables/manifest.ts:71 only imports the generated file)"
 },
 "O3_reason_to_dismiss": "The runtime lookup already lower-cases the path (manifest.ts:71, index.ts:449), so a solver can argue the case-insensitivity fix is already done and treat the build-time key insertion and the pages-module prerender router as separate build/prerender features with no auth role.",
 "O4_distance": {
  "files": 3,
  "packages": 2,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "With router.options.sensitive (set in nuxt.config or only at runtime in app/router.options.ts) rules must keep exact casing: /Admin/Dashboard and /admin/dashboard are distinct rules and /ADMIN/DASHBOARD matches neither; always folding keys, or keeping the unconditional lookup lower-casing, breaks this.",
  "where": "fix.diff:28-29; fix.diff:69-79; fix.diff:246-256; packages/nuxt/src/app/composables/manifest.ts:71"
 },
 "O6_input_shapes": [
  "mixed-case static rule key (/Legacy/Home) with any request casing",
  "mixed-case wildcard key (/Secret/Docs/**)",
  "mixed-case keys coming from inline defineRouteRules page paths (packages/nuxt/src/pages/route-rules.ts:20) or kit addRouteRules (packages/kit/src/pages.ts:24-27)",
  "sensitive routing configured statically (nuxt.options.router.options.sensitive) versus at runtime via #build/router.options.mjs",
  "two keys that collide after folding (warning, last wins)",
  "non-string route keys/paths passed through unchanged"
 ],
 "O7_producer": {
  "kind": "serializer",
  "where": "packages/nitro-server/src/index.ts:395-450 (getRouteRulesRouter + compileRouterToString into #build/route-rules.mjs)",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "Server-side renderer reads route rules (ssr: false, noScripts, cache) through nitropack's own getRouteRules(event), not the folded Nuxt matcher; whether nitro matches mixed-case keys case-insensitively was not checked",
   "where": "packages/nitro-server/src/runtime/handlers/renderer.ts:118",
   "reason_to_dismiss": "matching lives in nitropack, another repository, and the advisory is about appMiddleware, which is a client/app concept",
   "distance": "different package (nitro-server runtime) from the landing point in packages/nuxt",
   "present_in_latest": "unknown",
   "latest_where": ""
  }
 ],
 "O8b_injection_room": [
  {
   "where": "packages/nuxt/src/app/composables/layout.ts:20",
   "sibling": "resolveLayoutName imports the compiled matcher directly; a copy could have its own local rou3 lookup with verbatim keys for appLayout",
   "why_realistic": "it already bypasses getRouteRules and imports #build/route-rules.mjs directly, so a maintainer optimising it could have built a local matcher"
  },
  {
   "where": "packages/nuxt/src/pages/module.ts:579-583",
   "sibling": "redirect stub-route injection compares rule keys to page paths with a case-sensitive includes()",
   "why_realistic": "it is another build-time consumer of nitro.options.routeRules keys that sits next to the patched prerender block in the same file"
  },
  {
   "where": "packages/kit/src/pages.ts:24-27",
   "sibling": "addRouteRules (kit lower-level API) could normalise or fail to normalise the key it merges",
   "why_realistic": "module authors register rules with arbitrary casing through this public kit API"
  }
 ],
 "O9_family": "authorization bypass via case-sensitivity mismatch between route-rule matcher and case-insensitive vue-router (CWE-178/CWE-863)",
 "O9_dos": false,
 "O10_build": {
  "language": "TypeScript",
  "toolchain": "Node.js + pnpm monorepo, vitest (projects nuxt, nuxt-universal, nuxt-legacy, nuxt-dev, fixtures)",
  "services": [],
  "offline_after_build": true,
  "project_tests": "test/nuxt/composables.test.ts (app manifests / compiled route rules, runtime project 'nuxt'), test/basic.test.ts 'route rules' (fixture e2e, needs built fixture and playwright for client nav); scripts at fix.diff:6-13"
 },
 "O11_fix_minutes": 45,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "A",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "packages/nitro-server/src/index.ts, packages/nuxt/src/app/composables/manifest.ts, packages/nuxt/src/pages/module.ts",
  "j_sibling_sites": "unknown",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Lower-case the rule keys in getRouteRulesRouter unconditionally (or tweak getRouteRules), ignoring sensitive routing and the separate pages-module prerender router."
 },
 "out_of_scope_notes": [
  "Latest code also percent-decodes keys and lookups (latest normalizeRouteRulePath); encoding variant, not pursued.",
  "Per-route vue-router `sensitive` (definePageMeta) is not considered by the global fold; not pursued."
 ],
 "unverified": [
  "Pinned commit hash not given; repo dir taken as parent of fix commits.",
  "Repo size in MB not measured (no shell).",
  "nitropack's server-side route-rule case handling (renderer.ts:118) not checked; it is in another repository.",
  "Whether the two fix commits split the sites differently was not checked; only the combined diff was read.",
  "Recall risk is a judgement call: the advisory was published 2026-08-05, after the knowledge cutoff."
 ]
}
  ```
- Published fix sites:   - packages/nitro-server/src/index.ts:395-405 — entry point: nuxi build / nuxi dev (generation of #build/route-rules.mjs from nitro routeRules keys) [build-time code generator / serializer of the matcher, separate package @nuxt/nitro-server]
  - packages/nitro-server/src/index.ts:446-450 — entry point: runtime default export of #build/route-rules.mjs, called by getRouteRules, resolveLayoutName and prerender.server.ts on every SSR request and client navigation [generated runtime code (string template)]
  - packages/nitro-server/src/index.ts:533-539 — entry point: nuxi build / nuxi generate (app manifest prerendered list) [build hook]
  - packages/nuxt/src/app/composables/manifest.ts:71 — entry point: public auto-imported composable getRouteRules(); also used by router plugins for appMiddleware and by the redirect middleware [public runtime API]
  - packages/nuxt/src/pages/module.ts:527-532 — entry point: nuxi build (inject pages matching prerender: true rules) [build hook in pages module]
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

## Environment (`tasks/nuxt-mm/environment/Dockerfile`)
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

## Report to the solver (`tasks/nuxt-mm/instruction.md`)
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

## Tests (`tasks/nuxt-mm/tests/`)
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
- **Wrong-fix patches** go in `build/nuxt-mm/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/nuxt-mm/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/nuxt-mm/manifest.json`:**
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

**Also in `build/nuxt-mm/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py nuxt-mm --only static
python3 -I builder/gate.py nuxt-mm --only nop
python3 -I builder/gate.py nuxt-mm --only oracle
python3 -I builder/gate.py nuxt-mm --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/nuxt-mm/`;
  - edit only `tasks/nuxt-mm/`, `build/nuxt-mm/` and, for pattern B, the register;
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
