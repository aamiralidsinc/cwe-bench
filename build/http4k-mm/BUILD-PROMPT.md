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

Project root: `/home/mara/cwe-bench`. Task: `http4k-mm`. Pattern: `B`. Track: `injected`.

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
- Advisory: ["GHSA-PR33-38XX-6R26", "CVE-2026-100725"]; http4k/http4k; CWE-200 information exposure: client cookie jar with no RFC 6265 origin scoping (credentials leak across origins)
- Pinned (vulnerable) commit: parent of 6a9b44d74342879ece808de00a66ec30e2b9da23 (parent_commit null in candidate; tree at /home/mara/screen4/hosts/27402/repo). Published fix: 6a9b44d74342879ece808de00a66ec30e2b9da23.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "27402",
 "advisory_ids": [
  "GHSA-PR33-38XX-6R26",
  "CVE-2026-100725"
 ],
 "repo": "http4k/http4k",
 "pinned_commit": "parent of 6a9b44d74342879ece808de00a66ec30e2b9da23 (parent_commit null in candidate; tree at /home/mara/screen4/hosts/27402/repo)",
 "fix_commits": [
  "6a9b44d74342879ece808de00a66ec30e2b9da23"
 ],
 "trust_decision": {
  "summary": "Which stored client-side cookies go on an outgoing request is decided by CookieStorage.retrieve(), which at the pinned commit takes no request URI and returns every cookie regardless of the origin's domain, path or scheme; ClientFilters.Cookies attaches everything it gets back.",
  "evidence": [
   "core/core/src/main/kotlin/org/http4k/filter/cookie/clientCookies.kt:20-24",
   "core/core/src/main/kotlin/org/http4k/filter/cookie/clientCookies.kt:26-36",
   "core/core/src/main/kotlin/org/http4k/filter/ClientFilters.kt:262-280"
  ]
 },
 "landing_point": {
  "where": "core/core/src/main/kotlin/org/http4k/filter/cookie/clientCookies.kt:26",
  "why": "The summary names BasicCookieStorage, and it is defined here. The default wiring sits next door at core/core/src/main/kotlin/org/http4k/filter/ClientFilters.kt:259."
 },
 "fix_sites": [
  {
   "where": "core/core/src/main/kotlin/org/http4k/filter/cookie/clientCookies.kt:8",
   "entry_point": "public API: LocalCookie(cookie, created) data class, which gains an origin Uri (fix.diff:111)",
   "module_kind": "core library model (http4k-core)"
  },
  {
   "where": "core/core/src/main/kotlin/org/http4k/filter/cookie/clientCookies.kt:20-24",
   "entry_point": "public API: CookieStorage.retrieve(), whose signature becomes retrieve(uri: Uri) (fix.diff:120)",
   "module_kind": "core library interface (http4k-core)"
  },
  {
   "where": "core/core/src/main/kotlin/org/http4k/filter/cookie/clientCookies.kt:26-36",
   "entry_point": "public API: BasicCookieStorage() is renamed to InsecureCookieStorage, and a new DefaultCookieStorage scopes by domain, path and Secure (fix.diff:123-227)",
   "module_kind": "core library implementation (http4k-core)"
  },
  {
   "where": "core/core/src/main/kotlin/org/http4k/filter/ClientFilters.kt:257-260",
   "entry_point": "public API: ClientFilters.Cookies(clock, storage) default storage (fix.diff:65)",
   "module_kind": "core client filter (http4k-core)"
  },
  {
   "where": "core/core/src/main/kotlin/org/http4k/filter/ClientFilters.kt:262-280",
   "entry_point": "public API: ClientFilters.Cookies(timeSource, storage), which now passes request.uri to store, retrieve and removeExpired (fix.diff:71-93)",
   "module_kind": "core client filter (http4k-core)"
  },
  {
   "where": "core/testing/webdriver/src/main/kotlin/org/http4k/webdriver/Http4kWebDriver.kt:205-245",
   "entry_point": "public API: Http4kWebDriver(handler) browser simulator; manage().addCookie and the internal cookieStorage() change signature only and stay unscoped (fix.diff:588,597)",
   "module_kind": "testing module, second CookieStorage implementation (http4k-testing-webdriver)"
  }
 ],
 "O1_entry_points": 3,
 "O2_out_of_scope_site": {
  "kind": "second_implementation",
  "where": "core/testing/webdriver/src/main/kotlin/org/http4k/webdriver/Http4kWebDriver.kt:235-245 (anonymous CookieStorage wired into ClientFilters.Cookies at core/testing/webdriver/src/main/kotlin/org/http4k/webdriver/Http4kWebDriver.kt:43)"
 },
 "O3_reason_to_dismiss": "Http4kWebDriver is a testing-only in-memory browser for one app under test, so cross-origin cookie scoping looks irrelevant there; the published fix itself only changed its signature and still ignores the uri (fix.diff:597).",
 "O4_distance": {
  "files": 3,
  "packages": 3,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Several behaviours must keep working. Cookies with a Domain attribute must still reach subdomains. Requests with relative or host-less URIs (Request(GET, \"/set\") then \"/get\") must still round-trip cookies. Expiry removal must keep working. LocalCookie must still survive a Jackson round trip. Http4kWebDriver must keep cookies across page navigations and redirects. An over-broad fix (exact host plus exact path only, or dropping cookies when the host is empty) breaks these.",
  "where": "core/core/src/test/kotlin/org/http4k/filter/ClientCookiesTest.kt:46-62; core/core/src/test/kotlin/org/http4k/filter/cookie/LocalCookieTest.kt:51; fix.diff:336-349; core/testing/webdriver/src/main/kotlin/org/http4k/webdriver/Http4kWebDriver.kt:40-45"
 },
 "O6_input_shapes": [
  "host-only cookie (no Domain attribute) must match the exact host only (fix.diff:173-174,196)",
  "Domain attribute with or without a leading dot, in mixed case (fix.diff:176)",
  "Domain cookie to a subdomain, rejecting a suffix-only match such as notevil.com vs evil.com (fix.diff:197,424-428)",
  "Path attribute given vs default path derived from the request path (fix.diff:209-216)",
  "path prefix without a slash boundary, /apiv2 vs /api (fix.diff:219-225)",
  "Secure flag vs http/https scheme, case-insensitive (fix.diff:187,193)",
  "same cookie name from two origins stored independently (fix.diff:165,179)"
 ],
 "O7_producer": {
  "kind": "mapper",
  "where": "core/core/src/main/kotlin/org/http4k/core/cookie/Cookie.kt:47-69 (Set-Cookie parser producing domain, path and secure)",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "Http4kWebDriver's own CookieStorage returns every cookie for every request URI, and manage().addCookie stores cookies with no origin, so cookies reach any host the driver navigates or redirects to.",
   "where": "core/testing/webdriver/src/main/kotlin/org/http4k/webdriver/Http4kWebDriver.kt:235-245",
   "reason_to_dismiss": "It is a test-only browser simulator, not a production HTTP client; the advisory names BasicCookieStorage and the defaults, not webdriver.",
   "distance": "different Gradle module (core/testing/webdriver) and package (org.http4k.webdriver) from the landing point in core/core org.http4k.filter.cookie",
   "present_in_latest": "yes",
   "latest_where": "latest/core/testing/webdriver/src/main/kotlin/org/http4k/webdriver/Http4kWebDriver.kt:260"
  }
 ],
 "O8b_injection_room": [
  {
   "where": "core/core/src/main/kotlin/org/http4k/filter/cookie/clientCookies.kt:26-36",
   "sibling": "Store-side Domain validation: a response from host X sets Domain=Y for an unrelated Y, and the cookie is then sent to Y. The published DefaultCookieStorage.store accepts any Domain (fix.diff:175-177); upstream added a domain-match check later (latest/core/core/src/main/kotlin/org/http4k/filter/cookie/clientCookies.kt:79,88-89).",
   "why_realistic": "Engineers focus on retrieve-side matching and take the server's Domain attribute at face value; the published fix shipped exactly this gap."
  },
  {
   "where": "core/core/src/main/kotlin/org/http4k/filter/ClientFilters.kt:220-230",
   "sibling": "FollowRedirects keeps an already-attached Cookie header when it follows a redirect to a different host, so a Cookies filter placed outside FollowRedirects scopes only the first hop.",
   "why_realistic": "Filter ordering is user-chosen and the redirect code copies the whole request; upstream later added crossOriginSensitiveHeaders including Cookie (latest/core/core/src/main/kotlin/org/http4k/filter/ClientFilters.kt:171). This is arguably a separate redirect-header protection."
  },
  {
   "where": "core/core/src/main/kotlin/org/http4k/filter/ClientFilters.kt:279-280",
   "sibling": "Expiry removal and remove(name) work by name across all origins, so an expired cookie from one origin evicts a same-named live cookie of another.",
   "why_realistic": "The remove(name) interface has no origin parameter, and the fix keeps it (fix.diff:205-207); maintainers could easily leave it as is."
  }
 ],
 "O9_family": "CWE-200 information exposure: client cookie jar with no RFC 6265 origin scoping (credentials leak across origins)",
 "O9_dos": false,
 "O10_build": {
  "language": "Kotlin (JVM)",
  "toolchain": "Gradle wrapper (gradlew, settings.gradle.kts) with a JDK; modules core/core and core/testing/webdriver",
  "services": [],
  "offline_after_build": true,
  "project_tests": "core/core/src/test/kotlin/org/http4k/filter/ClientCookiesTest.kt and core/core/src/test/kotlin/org/http4k/filter/cookie/LocalCookieTest.kt (in-memory handlers, no network); there are no cookie-specific webdriver tests matching *ookie*"
 },
 "O11_fix_minutes": 60,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "core/core/src/main/kotlin/org/http4k/filter/cookie/clientCookies.kt, core/core/src/main/kotlin/org/http4k/filter/ClientFilters.kt, core/testing/webdriver/src/main/kotlin/org/http4k/webdriver/Http4kWebDriver.kt",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 0,
  "j_defence_ineffective": 0,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Filter cookies by exact request host inside ClientFilters.Cookies (or a new scoped storage) and leave the webdriver's own CookieStorage and the store-side Domain validation untouched."
 },
 "out_of_scope_notes": [
  "FollowRedirects forwards Authorization and Proxy-Authorization headers to cross-origin redirect targets at the pinned commit (core/core/src/main/kotlin/org/http4k/filter/ClientFilters.kt:220-230); this is a separate redirect-header protection and was not pursued."
 ],
 "unverified": [
  "repo_mb not measured (no shell use); http4k is a large multi-module monorepo, so tiny_repo is very unlikely, but this was not checked.",
  "pinned_commit SHA not given (parent_commit null); assumed to be the tree at hosts/27402/repo, which matches the fix.diff preimage at the cited lines.",
  "Fairness: the fix changes public API shape (CookieStorage.retrieve(uri), a third LocalCookie constructor arg). Hidden tests that call these signatures would dictate the API, so the report must state them or the tests must go through ClientFilters.Cookies only.",
  "O1 counts ClientFilters.Cookies (two overloads, counted once), direct CookieStorage/BasicCookieStorage use, and Http4kWebDriver; other modules calling ClientFilters.Cookies from src/main were searched and none found outside webdriver.",
  "recall_risk medium is a judgement: the advisory was published 2026-06-19 and the rename to InsecureCookieStorage is distinctive."
 ]
}
  ```
- Published fix sites:   - core/core/src/main/kotlin/org/http4k/filter/cookie/clientCookies.kt:8 — entry point: public API: LocalCookie(cookie, created) data class, which gains an origin Uri (fix.diff:111) [core library model (http4k-core)]
  - core/core/src/main/kotlin/org/http4k/filter/cookie/clientCookies.kt:20-24 — entry point: public API: CookieStorage.retrieve(), whose signature becomes retrieve(uri: Uri) (fix.diff:120) [core library interface (http4k-core)]
  - core/core/src/main/kotlin/org/http4k/filter/cookie/clientCookies.kt:26-36 — entry point: public API: BasicCookieStorage() is renamed to InsecureCookieStorage, and a new DefaultCookieStorage scopes by domain, path and Secure (fix.diff:123-227) [core library implementation (http4k-core)]
  - core/core/src/main/kotlin/org/http4k/filter/ClientFilters.kt:257-260 — entry point: public API: ClientFilters.Cookies(clock, storage) default storage (fix.diff:65) [core client filter (http4k-core)]
  - core/core/src/main/kotlin/org/http4k/filter/ClientFilters.kt:262-280 — entry point: public API: ClientFilters.Cookies(timeSource, storage), which now passes request.uri to store, retrieve and removeExpired (fix.diff:71-93) [core client filter (http4k-core)]
  - core/testing/webdriver/src/main/kotlin/org/http4k/webdriver/Http4kWebDriver.kt:205-245 — entry point: public API: Http4kWebDriver(handler) browser simulator; manage().addCookie and the internal cookieStorage() change signature only and stay unscoped (fix.diff:588,597) [testing module, second CookieStorage implementation (http4k-testing-webdriver)]
- Uncovered routes to confirm (pattern B):   - core/testing/webdriver/src/main/kotlin/org/http4k/webdriver/Http4kWebDriver.kt:235-245 — Http4kWebDriver's own CookieStorage returns every cookie for every request URI, and manage().addCookie stores cookies with no origin, so cookies reach any host the driver navigates or redirects to. (reason to dismiss: It is a test-only browser simulator, not a production HTTP client; the advisory names BasicCookieStorage and the defaults, not webdriver.; still in latest: yes)
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

## Environment (`tasks/http4k-mm/environment/Dockerfile`)
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

## Report to the solver (`tasks/http4k-mm/instruction.md`)
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

## Tests (`tasks/http4k-mm/tests/`)
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
- **Wrong-fix patches** go in `build/http4k-mm/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/http4k-mm/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/http4k-mm/manifest.json`:**
- `slug`, `candidate`;
- `pattern`: `B`;
- `builder_prompt_version`: `build-v1`;
- `"strict_gate": true`;
- `verified`: entry point, sites, routes, services, project tests run;
- `leak_terms`, `patch_checks`, `wrong_fix_catalogue`;
- `traps`: one entry per lever, with `shape`, `where` (file:line), `security_tests`,
  `coupled_functional_tests`, `security_fail_patch`, and `realistic_because` (for pattern B: "real,
  unmodified upstream code");
- `status`.

**Also in `build/http4k-mm/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py http4k-mm --only static
python3 -I builder/gate.py http4k-mm --only nop
python3 -I builder/gate.py http4k-mm --only oracle
python3 -I builder/gate.py http4k-mm --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/http4k-mm/`;
  - edit only `tasks/http4k-mm/`, `build/http4k-mm/` and, for pattern B, the register;
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
