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

Project root: `/home/mara/cwe-bench`. Task: `i18next-ssrf-inj`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: GHSA-XVQ9-WJP8-HWQF / CVE-2026-105800 - i18next/i18next-http-backend - URL/SSRF injection via template interpolation (CWE-918/CWE-74), validated by an incomplete denylist. Per-placeholder denylist checks decide whether an untrusted lng/ns value may be put into the loadPath/addPath template that becomes the request URL; i
- Pinned (vulnerable) commit: 08cb05d3ef8396cb74ab9d6885f4c3ddb43bfbf3. Published fix: 07e028862b25d0b9251bf3cafb92be2d35285f85.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "15041",
 "advisory_ids": [
  "GHSA-XVQ9-WJP8-HWQF",
  "CVE-2026-105800"
 ],
 "repo": "i18next/i18next-http-backend",
 "pinned_commit": "parent of 07e028862b25d0b9251bf3cafb92be2d35285f85 (parent_commit not given in input)",
 "fix_commits": [
  "07e028862b25d0b9251bf3cafb92be2d35285f85"
 ],
 "trust_decision": {
  "summary": "Per-placeholder denylist checks decide whether an untrusted lng/ns value may be put into the loadPath/addPath template that becomes the request URL; interpolateUrl returns null to refuse the request, and _readAny/create skip it.",
  "evidence": [
   "lib/utils.js:26-39",
   "lib/utils.js:46-64",
   "lib/utils.js:147-165",
   "lib/index.js:64-70",
   "lib/index.js:133-138"
  ]
 },
 "landing_point": {
  "where": "lib/utils.js:35",
  "why": "The summary says 'incomplete URL validation'. The shared denylist regex in isSafeUrlSegmentBase is the obvious validator to look at, and the fix tightens it there."
 },
 "fix_sites": [
  {
   "where": "lib/utils.js:35",
   "entry_point": "Backend.read / readMulti / create (and reload via backendConnector.read) -> interpolateUrl; also exported helpers isSafeLangUrlSegment/isSafeNsUrlSegment",
   "module_kind": "core library source (shared validator)"
  },
  {
   "where": "lib/utils.js:62-64",
   "entry_point": "Backend.read / readMulti / create -> interpolateUrl -> isSafeNsUrlSegment for the {{ns}} placeholder",
   "module_kind": "core library source (per-key validator)"
  },
  {
   "where": "i18nextHttpBackend.js:17",
   "entry_point": "Same API, through the browser IIFE bundle (global i18nextHttpBackend)",
   "module_kind": "committed build artifact (second copy of lib/utils.js)"
  },
  {
   "where": "i18nextHttpBackend.js:26-28",
   "entry_point": "Same API, through the browser IIFE bundle",
   "module_kind": "committed build artifact"
  }
 ],
 "O1_entry_points": 3,
 "O2_out_of_scope_site": {
  "kind": "none",
  "where": "The committed bundles i18nextHttpBackend.js:11-28 and i18nextHttpBackend.min.js are built from lib/utils.js, not a separate implementation"
 },
 "O3_reason_to_dismiss": "A template with a leading literal '/' followed directly by {{ns}} (e.g. '/{{ns}}/{{lng}}.json') looks like a 'template with a leading path', which the fix's own changelog declares unaffected (fix.diff:10). Also, ns legitimately allows '/' (lib/utils.js:52-57), so a solver can argue that a single leading slash is a valid nested-namespace shape.",
 "O4_distance": {
  "files": 1,
  "packages": 1,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "ns must keep accepting '/' (nested namespaces like a/b) and '@' (scoped names like @org/pkg), regressions fixed in 3.0.6/4.0.1. Blocking '/' or '@' in ns, or rejecting every URL that is absolute or starts with a protocol, breaks legitimate behaviour: loadPath may legitimately be an absolute cross-origin URL such as https://cdn/... {{lng}}.",
  "where": "lib/utils.js:52-64"
 },
 "O6_input_shapes": [
  "lng value with scheme colon (http:host:port)",
  "ns value with scheme colon",
  "ns value with protocol-relative '//' prefix",
  "'//' inside ns (a//b)",
  "'+'-joined multi-language value with one bad segment (en+http:...), via split at lib/utils.js:155-161",
  "readMulti arrays joined with '+' (lib/index.js:64)"
 ],
 "O7_producer": {
  "kind": "none",
  "where": "",
  "check_calls_producer": null
 },
 "O8_uncovered_routes": [
  {
   "route": "The composed URL is never checked. An ns with a single leading '/' passes the per-value check but, placed after a literal '/' in the template (e.g. '/{{ns}}/{{lng}}.json'), it yields a protocol-relative '//host/...' URL that leaves the origin.",
   "where": "lib/utils.js:147-165",
   "reason_to_dismiss": "The template has a leading '/', which the changelog calls unaffected, and a leading '/' in ns is a legitimate nested-namespace character.",
   "distance": "same file and function as the landing point; the gap is in template/value composition, not in the denylist",
   "present_in_latest": "no",
   "latest_where": "latest/lib/utils.js:176-183"
  },
  {
   "route": "Public Backend.loadUrl(url, ...) sends a caller-supplied URL to options.request with no URL check.",
   "where": "lib/index.js:74-84",
   "reason_to_dismiss": "The caller passes a complete URL, not lng/ns values, so there is nothing to interpolate. It is arguably outside the placeholder-injection protection.",
   "distance": "other file (lib/index.js) from the landing point; public in index.d.ts:126-131",
   "present_in_latest": "unknown",
   "latest_where": ""
  }
 ],
 "O8b_injection_room": [
  {
   "where": "lib/index.js:56-58",
   "sibling": "A function-form loadPath gets the raw languages/namespaces and could return a pre-interpolated string that skips interpolateUrl.",
   "why_realistic": "A maintainer could add a 'pre-built path' fast path for function loadPath results that contain no placeholders."
  },
  {
   "where": "lib/utils.js:134-141",
   "sibling": "The unchecked 'interpolate' helper could be used for addPath or a new path option (e.g. a reload or customPath variant).",
   "why_realistic": "interpolate already exists next to interpolateUrl, and a new option could easily reach for the wrong one."
  }
 ],
 "O9_family": "URL/SSRF injection via template interpolation (CWE-918/CWE-74), validated by an incomplete denylist",
 "O9_dos": false,
 "O10_build": {
  "language": "JavaScript (ESM)",
  "toolchain": "Node >=18, npm, mocha, tsdown, eslint, tsc/tsd",
  "services": [],
  "offline_after_build": true,
  "project_tests": "test/security.spec.js (validators, interpolateUrl, Backend.read with alternateFetch); test/http.spec.js and test/backendConnector.load.spec.js use local fixture server test/fixtures/server.js"
 },
 "O11_fix_minutes": 25,
 "O12_red_flags": [
  "tiny_repo"
 ],
 "O13_recall_risk": "medium",
 "pattern_fit": "B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "lib/utils.js, i18nextHttpBackend.js (+ generated i18nextHttpBackend.min.js)",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 0,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Add ':' (and maybe '//') to the per-value denylist only, without checking the composed URL against the template's own leading form."
 },
 "out_of_scope_notes": [
  "latest/lib/utils.js:180 names a separate later advisory GHSA-9jhj-wvmw-cfx5 for the leading-'//' composition route; it raises recall risk for Pattern B.",
  "addQueryString in lib/request.js:30-44 appends queryStringParams; it is encoded, and it is configuration, not lng/ns."
 ],
 "unverified": [
  "repo_mb not measured (no shell). The source is three files under lib/, so tiny_repo is inferred, not measured.",
  "Whether loadUrl gained a check in latest/lib/index.js was not inspected.",
  "Pinned commit hash not given; assumed to be the fix's parent.",
  "regression_tests_in_pinned_commit checked by grep only: the fix's new test strings (http:127, evil.example, a//b) are absent from repo/test, so the flag does not apply."
 ]
}
  ```
- Published fix sites:   - lib/utils.js:35 — entry point: Backend.read / readMulti / create (and reload via backendConnector.read) -> interpolateUrl; also exported helpers isSafeLangUrlSegment/isSafeNsUrlSegment [core library source (shared validator)]
  - lib/utils.js:62-64 — entry point: Backend.read / readMulti / create -> interpolateUrl -> isSafeNsUrlSegment for the {{ns}} placeholder [core library source (per-key validator)]
  - i18nextHttpBackend.js:17 — entry point: Same API, through the browser IIFE bundle (global i18nextHttpBackend) [committed build artifact (second copy of lib/utils.js)]
  - i18nextHttpBackend.js:26-28 — entry point: Same API, through the browser IIFE bundle [committed build artifact]
- Uncovered routes to confirm (pattern B):   - lib/utils.js:147-165 — The composed URL is never checked. An ns with a single leading '/' passes the per-value check but, placed after a literal '/' in the template (e.g. '/{{ns}}/{{lng}}.json'), it yields a protocol-relative '//host/...' URL that leaves the origin. (reason to dismiss: The template has a leading '/', which the changelog calls unaffected, and a leading '/' in ns is a legitimate nested-namespace character.; still in latest: no)
  - lib/index.js:74-84 — Public Backend.loadUrl(url, ...) sends a caller-supplied URL to options.request with no URL check. (reason to dismiss: The caller passes a complete URL, not lng/ns values, so there is nothing to interpolate. It is arguably outside the placeholder-injection protection.; still in latest: unknown)
- Design plan from the lead: TRACK = INJECTED (breaker recipe; mined tasks were all solved, injected-sibling tasks at a recurring check broke both models).

RECURRING CHECK / PROTECTED SINK: Per-placeholder denylist checks decide whether an untrusted lng/ns value may be put into the loadPath/addPath template that becomes the request URL; interpolateUrl returns null to refuse the request, and _readAny/create skip it.

STEP 1 - confirm the published fix's sites and these uncovered-route leads with tests on the pinned copy: lib/utils.js:147-165 (The composed URL is never checked. An ns with a single ; skip: The template has a leading '/', which the cha); lib/index.js:74-84 (Public Backend.loadUrl(url, ...) sends a caller-supplie; skip: The caller passes a complete URL, not lng/ns ).
STEP 2 - at these recurring sites, add 2 to 4 realistic sibling GAPS in the same protection that a maintainer could plausibly have left unguarded (verify each by reading the code): lib/index.js:56-58 -> A function-form loadPath gets the raw languages/namespaces and could r (realistic: A maintainer could add a 'pre-built path' fast path for func); lib/utils.js:134-141 -> The unchecked 'interpolate' helper could be used for addPath or a new  (realistic: interpolate already exists next to interpolateUrl, and a new). Each added gap MUST be code a maintainer could plausibly have written (no tell-tale names/comments/shortcuts; match surrounding style), reachable through the real public entry point, covered by a stated invariant, left where the published upstream fix never touches, and carry a DIFFERENT plausible reason a solver would skip it (legacy/compat path, internal/trusted caller, unsupported combination, neighbouring feature). Distinct reasons-to-skip are the lever.
STEP 3 - hidden security tests require closing the base flaw, every uncovered route AND every added gap through the real entry point. The oracle closes all; a fix that closes only the obvious sites must score < 1.0 (add a security_fail check patch for that partial fix).
STEP 4 - COUPLED MUST-KEEP-WORKING (one functional test per trap): ns must keep accepting '/' (nested namespaces like a/b) and '@' (scoped names like @org/pkg), regressions fixed in 3.0.6/4.0.1. Blocking '/' or '@' in ns, or rejecting every URL that is absolute or st (near lib/utils.js:52-64); keep every legitimate use working.

Aim for >=3 levers with DIFFERENT reasons a solver would skip them. Every gap must be findable by a blind engineer from instruction.md + code; if not, drop it. instruction.md stays product-level: system, one impact with one user trigger, invariants covering EVERY route/gap (a natural list, no count); never name files/functions/fields/CVEs (all in manifest.leak_terms). Register each added gap and route in build/audit/uncovered-routes.tsv.
- Host notes: Language: JavaScript (ESM). Offline after build, no external services. Added gaps go in OUR copy only, register them. Recurring check (3 entry points). Build+test via real entry points; project's own area tests pass at the pinned commit. Pin at the vulnerable commit; keep unrelated earlier fixes. If the repo is a large monorepo, scope the build/tests to the affected package only.

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

## Environment (`tasks/i18next-ssrf-inj/environment/Dockerfile`)
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

## Report to the solver (`tasks/i18next-ssrf-inj/instruction.md`)
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

## Tests (`tasks/i18next-ssrf-inj/tests/`)
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
- **Wrong-fix patches** go in `build/i18next-ssrf-inj/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/i18next-ssrf-inj/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/i18next-ssrf-inj/manifest.json`:**
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

**Also in `build/i18next-ssrf-inj/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py i18next-ssrf-inj --only static
python3 -I builder/gate.py i18next-ssrf-inj --only nop
python3 -I builder/gate.py i18next-ssrf-inj --only oracle
python3 -I builder/gate.py i18next-ssrf-inj --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/i18next-ssrf-inj/`;
  - edit only `tasks/i18next-ssrf-inj/`, `build/i18next-ssrf-inj/` and, for pattern B, the register;
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
