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

Project root: `/home/mara/cwe-bench`. Task: `handlebars-path-read-inj`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: GHSA-G29J-RWFV-H99W / CVE-2026-63490 - jknack/handlebars.java - path traversal / suffix-truncation file read in a template loader (CWE-22/23/552). Whether a template name (view name, partial name or compile() argument) may resolve to a Spring resource outside the configured prefix/suffix; decided
- Pinned (vulnerable) commit: c95855064f48f1a66af2a5da5a9c1522d7f57264. Published fix: 61f43423a337b87db5fec1fe59f0725aaaa38df5.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "25719",
 "advisory_ids": [
  "GHSA-G29J-RWFV-H99W",
  "CVE-2026-63490"
 ],
 "repo": "jknack/handlebars.java",
 "pinned_commit": "parent of 61f43423a337b87db5fec1fe59f0725aaaa38df5",
 "fix_commits": [
  "61f43423a337b87db5fec1fe59f0725aaaa38df5"
 ],
 "trust_decision": {
  "summary": "Whether a template name (view name, partial name or compile() argument) may resolve to a Spring resource outside the configured prefix/suffix; decided in SpringTemplateLoader.resolve/getResource, which keeps a caller-supplied 'file:'/'classpath:' protocol and hands the location to Spring with no boundary, fragment or query check (fixed there, plus a view-name check in HandlebarsViewResolver.configure).",
  "evidence": [
   "handlebars-springmvc/src/main/java/com/github/jknack/handlebars/springmvc/SpringTemplateLoader.java:57-63",
   "handlebars-springmvc/src/main/java/com/github/jknack/handlebars/springmvc/SpringTemplateLoader.java:65-77",
   "handlebars-springmvc/src/main/java/com/github/jknack/handlebars/springmvc/HandlebarsViewResolver.java:163-178",
   "fix.diff:47-115",
   "fix.diff:9-16"
  ]
 },
 "landing_point": {
  "where": "handlebars-springmvc/src/main/java/com/github/jknack/handlebars/springmvc/SpringTemplateLoader.java:57-63",
  "why": "The summary names SpringTemplateLoader and a URL-fragment suffix bypass; getResource is where the location becomes a Spring Resource/URL."
 },
 "fix_sites": [
  {
   "where": "handlebars-springmvc/src/main/java/com/github/jknack/handlebars/springmvc/SpringTemplateLoader.java:57-63",
   "entry_point": "Public API: new Handlebars(new SpringTemplateLoader(ctx)).compile(name) / precompile(name), {{> partial}} and {{embedded}} helper, all via URLTemplateLoader.sourceAt (handlebars/src/main/java/com/github/jknack/handlebars/io/URLTemplateLoader.java:50-58)",
   "module_kind": "lower-level library loader (Spring integration module)"
  },
  {
   "where": "handlebars-springmvc/src/main/java/com/github/jknack/handlebars/springmvc/SpringTemplateLoader.java:65-77",
   "entry_point": "Same as above; resolve() is called from URLTemplateLoader.sourceAt before getResource (fix removes the protocol-preserving override)",
   "module_kind": "name-to-location mapper in the loader"
  },
  {
   "where": "handlebars-springmvc/src/main/java/com/github/jknack/handlebars/springmvc/HandlebarsViewResolver.java:163-178",
   "entry_point": "Spring MVC: controller-returned view name -> ViewResolver -> buildView (HandlebarsViewResolver.java:152-154) -> configure -> handlebars.compile",
   "module_kind": "web-layer wrapper (view resolver)"
  }
 ],
 "O1_entry_points": 5,
 "O2_out_of_scope_site": {
  "kind": "wrapper_or_composition",
  "where": "handlebars-springmvc/src/main/java/com/github/jknack/handlebars/springmvc/HandlebarsViewResolver.java:163-178"
 },
 "O3_reason_to_dismiss": "Once SpringTemplateLoader rejects fragments/queries/escapes for every caller, a second view-name check in the resolver looks redundant; and the root-prefix/empty-suffix guard missing on the Spring loader looks like a developer configuration choice, not attacker input.",
 "O4_distance": {
  "files": 2,
  "packages": 1,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Protocol-qualified configured prefixes (e.g. 'classpath:/templates/', 'file:C:/...') and nested view names ('home/index') must keep resolving; a fix that rejects ':' or '/' anywhere in the full location, or strips every protocol, breaks the documented URL/classpath support.",
  "where": "handlebars-springmvc/src/main/java/com/github/jknack/handlebars/springmvc/SpringTemplateLoader.java:23-27"
 },
 "O6_input_shapes": [
  "URL fragment '#' in the name, cutting off the suffix",
  "URL query '?' in the name, cutting off the suffix",
  "'..' relative traversal escaping the prefix",
  "caller-supplied protocol in the name ('file:' / 'classpath:') kept at the front by resolve()",
  "view names containing ':', '#' or '..' at the resolver layer"
 ],
 "O7_producer": {
  "kind": "mapper",
  "where": "handlebars-springmvc/src/main/java/com/github/jknack/handlebars/springmvc/SpringTemplateLoader.java:65-77 (with handlebars/src/main/java/com/github/jknack/handlebars/io/AbstractTemplateLoader.java:48-50)",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "SpringTemplateLoader never applies the root-prefix + empty-suffix guard (validatePrefixSuffix) that the sibling ClassPath/ServletContext loaders apply, and the fix's new boundary check is skipped when the prefix is '/', which is the resolver default.",
   "where": "handlebars-springmvc/src/main/java/com/github/jknack/handlebars/springmvc/SpringTemplateLoader.java:43-54",
   "reason_to_dismiss": "Prefix/suffix are set by the developer (HandlebarsViewResolver.java:283-284), not by the attacker, and the advisory is about the fragment bypass, not about configuration.",
   "distance": "Guard lives in core module handlebars/.../io/URLTemplateLoader.java:95-101, called at ClassPathTemplateLoader.java:28 and ServletContextTemplateLoader.java:39; one module away from the landing point.",
   "present_in_latest": "yes",
   "latest_where": "latest/handlebars-springmvc/src/main/java/com/github/jknack/handlebars/springmvc/SpringTemplateLoader.java:36"
  }
 ],
 "O8b_injection_room": [
  {
   "where": "handlebars/src/main/java/com/github/jknack/handlebars/io/FileTemplateLoader.java:67-86",
   "sibling": "A resolve() override that keeps a 'file:' prefix and builds the URL with new URL(location), which inherits the fragment/query suffix bypass.",
   "why_realistic": "The Spring loader already does exactly this for 'file:'/'classpath:' names; a maintainer adding URI-style name support to the file loader would copy that override."
  },
  {
   "where": "handlebars/src/main/java/com/github/jknack/handlebars/io/ServletContextTemplateLoader.java:61-64",
   "sibling": "Resolving through ServletContext.getResource and then re-resolving the returned URL string (e.g. for jar:/war: paths) without a getRef()/getQuery() check.",
   "why_realistic": "Servlet containers return URLs for packaged resources, and a maintainer handling exploded vs packaged WARs could plausibly re-parse them."
  }
 ],
 "O9_family": "path traversal / suffix-truncation file read in a template loader (CWE-22/23/552)",
 "O9_dos": false,
 "O10_build": {
  "language": "Java 17",
  "toolchain": "Maven multi-module (pom.xml), Spring 6.2.9, JUnit 5 + Mockito",
  "services": [],
  "offline_after_build": true,
  "project_tests": "handlebars-springmvc/src/test/java/com/github/jknack/handlebars/springmvc/SpringTemplateLoaderTest.java, HandlebarsViewResolverIntegrationTest.java, HandlebarsViewTest.java"
 },
 "O11_fix_minutes": 35,
 "O12_red_flags": [],
 "O13_recall_risk": "low",
 "pattern_fit": "A",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "handlebars-springmvc/src/main/java/com/github/jknack/handlebars/springmvc/SpringTemplateLoader.java, handlebars-springmvc/src/main/java/com/github/jknack/handlebars/springmvc/HandlebarsViewResolver.java",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Reject '#' (only) in the location in SpringTemplateLoader.getResource, leaving '?', the protocol-preserving resolve() override and the view-resolver entry open."
 },
 "out_of_scope_notes": [
  "Handlebars.handlebarsJsFile loads a developer-configured classpath file via getClass().getResource (handlebars/src/main/java/com/github/jknack/handlebars/Handlebars.java:1155); not followed."
 ],
 "unverified": [
  "repo_mb not measured (no shell use); tiny_repo/giant_repo not assessed.",
  "O8 route is an adjacent guard (root classpath exposure), not the fragment check itself; whether it counts as 'the same protection' is a judgement call, so pattern_fit is A rather than A+B.",
  "j_defence_ineffective=1 rests on the core loaders' boundary check (URLTemplateLoader.classpathResource, 'parity with d177cdee' at fix.diff:48) existing at the pinned commit but never being applied in SpringTemplateLoader; Spring ResourceLoader's handling of '#'/'?' in file: URLs was not verified against Spring source.",
  "O1 counts view-name resolution, compile(), precompile(), partials and the embedded helper; caching wrappers (Guava/Caffeine/Composite) delegate to the same sourceAt and are not counted separately.",
  "O13 recall risk estimated from the publish date (2026-09-02) and the project being niche; not checked against write-ups."
 ]
}
  ```
- Published fix sites:   - handlebars-springmvc/src/main/java/com/github/jknack/handlebars/springmvc/SpringTemplateLoader.java:57-63 — entry point: Public API: new Handlebars(new SpringTemplateLoader(ctx)).compile(name) / precompile(name), {{> partial}} and {{embedded}} helper, all via URLTemplateLoader.sourceAt (handlebars/src/main/java/com/github/jknack/handlebars/io/URLTemplateLoader.java:50-58) [lower-level library loader (Spring integration module)]
  - handlebars-springmvc/src/main/java/com/github/jknack/handlebars/springmvc/SpringTemplateLoader.java:65-77 — entry point: Same as above; resolve() is called from URLTemplateLoader.sourceAt before getResource (fix removes the protocol-preserving override) [name-to-location mapper in the loader]
  - handlebars-springmvc/src/main/java/com/github/jknack/handlebars/springmvc/HandlebarsViewResolver.java:163-178 — entry point: Spring MVC: controller-returned view name -> ViewResolver -> buildView (HandlebarsViewResolver.java:152-154) -> configure -> handlebars.compile [web-layer wrapper (view resolver)]
- Uncovered routes to confirm (pattern B):   - handlebars-springmvc/src/main/java/com/github/jknack/handlebars/springmvc/SpringTemplateLoader.java:43-54 — SpringTemplateLoader never applies the root-prefix + empty-suffix guard (validatePrefixSuffix) that the sibling ClassPath/ServletContext loaders apply, and the fix's new boundary check is skipped when the prefix is '/', which is the resolver default. (reason to dismiss: Prefix/suffix are set by the developer (HandlebarsViewResolver.java:283-284), not by the attacker, and the advisory is about the fragment bypass, not about configuration.; still in latest: yes)
- Design plan from the lead: TRACK = INJECTED (breaker recipe; the mined batch was all solved, injected-sibling tasks at a recurring check broke both models).

RECURRING CHECK / PROTECTED SINK: Whether a template name (view name, partial name or compile() argument) may resolve to a Spring resource outside the configured prefix/suffix; decided in SpringTemplateLoader.resolve/getResource, which keeps a caller-supplied 'file:'/'classpath:' protocol and 

STEP 1 - confirm the published fix's sites and these uncovered-route leads with tests on the pinned copy: handlebars-springmvc/src/main/java/com/github/jknack/handlebars/springmvc/SpringTemplateLoader.java:43-54 (SpringTemplateLoader never applies the root-prefix + em; skip: Prefix/suffix are set by the developer (Handl).
STEP 2 - at these recurring sites, add 2 to 4 realistic sibling GAPS in the same protection that a maintainer could plausibly have left unguarded (verify each by reading the code): handlebars/src/main/java/com/github/jknack/handlebars/io/FileTemplateLoader.java:67-86 -> A resolve() override that keeps a 'file:' prefix and builds the URL wi (realistic: The Spring loader already does exactly this for 'file:'/'cla); handlebars/src/main/java/com/github/jknack/handlebars/io/ServletContextTemplateLoader.java:61-64 -> Resolving through ServletContext.getResource and then re-resolving the (realistic: Servlet containers return URLs for packaged resources, and a). Each added gap MUST be code a maintainer could plausibly have written (no tell-tale names/comments/shortcuts; match surrounding style), reachable through the real public entry point, covered by a stated invariant, left where the published upstream fix never touches, and carry a DIFFERENT plausible reason a solver would skip it (legacy/compat path, internal/trusted caller, unsupported combination, neighbouring feature). Distinct reasons-to-skip are the lever.
STEP 3 - hidden security tests require closing the base flaw, every uncovered route AND every added gap through the real entry point. The oracle closes all; a fix that closes only the obvious sites must score < 1.0 (add a security_fail check patch for that partial fix).
STEP 4 - COUPLED MUST-KEEP-WORKING (one functional test per trap): Protocol-qualified configured prefixes (e.g. 'classpath:/templates/', 'file:C:/...') and nested view names ('home/index') must keep resolving; a fix that rejects ':' or '/' anywhere in the full locati (near handlebars-springmvc/src/main/java/com/github/jkna); keep every legitimate use working.

Aim for >=3 levers with DIFFERENT reasons a solver would skip them. Every gap must be findable by a blind engineer from instruction.md + code; if not, drop it. instruction.md stays product-level: system, one impact with one user trigger, invariants covering EVERY route/gap (a natural list, no count); never name files/functions/fields/CVEs (all in manifest.leak_terms). Register each added gap and route in build/audit/uncovered-routes.tsv.
- Host notes: Language: Java 17. Offline after build, no external services. Added gaps go in OUR copy only, register them. Recurring check (5 entry points). Build+test via real entry points; project's own area tests pass at the pinned commit. Pin at the vulnerable commit; keep unrelated earlier fixes.

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

## Environment (`tasks/handlebars-path-read-inj/environment/Dockerfile`)
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

## Report to the solver (`tasks/handlebars-path-read-inj/instruction.md`)
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

## Tests (`tasks/handlebars-path-read-inj/tests/`)
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
- **Wrong-fix patches** go in `build/handlebars-path-read-inj/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/handlebars-path-read-inj/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/handlebars-path-read-inj/manifest.json`:**
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

**Also in `build/handlebars-path-read-inj/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py handlebars-path-read-inj --only static
python3 -I builder/gate.py handlebars-path-read-inj --only nop
python3 -I builder/gate.py handlebars-path-read-inj --only oracle
python3 -I builder/gate.py handlebars-path-read-inj --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/handlebars-path-read-inj/`;
  - edit only `tasks/handlebars-path-read-inj/`, `build/handlebars-path-read-inj/` and, for pattern B, the register;
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
