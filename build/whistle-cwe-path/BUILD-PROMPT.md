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

Project root: `/home/mara/cwe-bench`. Task: `whistle-cwe-path`. Pattern: `A+B`. Track: `mined`.

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
- Advisory: GHSA-3VFR-4GWF-QXFP / CVE-2026-55629 - avwo/whistle - CWE-22 path traversal / arbitrary local file read through an unauthenticated internal service route. Whether a caller may make the forked service child read a file outside temp_files: /cgi-bin/temp/get passes any non-temp 'filename' raw to getFile; the only guard is in the webui proxy (no-login mode only), and the service port itself accep
- Pinned (vulnerable) commit: 826b59bf14b7f3eca56dd5f1cc7f3152e3983005. Published fix: 777bcf69bae2972aa7138a158c91619185653cf5.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "8032",
 "advisory_ids": [
  "GHSA-3VFR-4GWF-QXFP",
  "CVE-2026-55629"
 ],
 "repo": "avwo/whistle",
 "pinned_commit": "parent of 777bcf69bae2972aa7138a158c91619185653cf5 (parent_commit not given in candidate)",
 "fix_commits": [
  "777bcf69bae2972aa7138a158c91619185653cf5"
 ],
 "trust_decision": {
  "summary": "Whether a caller may make the forked service child read a file outside temp_files: /cgi-bin/temp/get passes any non-temp 'filename' raw to getFile; the only guard is in the webui proxy (no-login mode only), and the service port itself accepted any request until the fix added a uid-header gate.",
  "evidence": [
   "lib/service/service.js:458-462",
   "lib/service/service.js:133-151",
   "lib/service/service.js:305-312",
   "biz/webui/lib/index.js:74-88",
   "fix.diff:719-722"
  ]
 },
 "landing_point": {
  "where": "lib/service/service.js:451-468",
  "why": "The /cgi-bin/temp/get handler joins temp names and otherwise hands req.query.filename straight to getFile; this is the obvious path-traversal sink."
 },
 "fix_sites": [
  {
   "where": "fix.diff:719-722",
   "entry_point": "any HTTP request sent directly to the service child's local port (lib/service/service.js:305-313, all routes)",
   "module_kind": "internal forked service server (lower-level API under the webui proxy)"
  },
  {
   "where": "fix.diff:732-734",
   "entry_point": "GET /cgi-bin/temp/get?filename= (via biz/webui/lib/index.js:539) and GET /cgi-bin/import-remote?url= (biz/webui/lib/index.js:432-435)",
   "module_kind": "service route handler"
  },
  {
   "where": "fix.diff:701-702",
   "entry_point": "GET /cgi-bin/temp/get?files=a,b,c (lib/service/service.js:452-456)",
   "module_kind": "service helper"
  },
  {
   "where": "fix.diff:872",
   "entry_point": "common.getTempFile, used by the webui guard biz/webui/lib/index.js:66-72 and by the service handlers",
   "module_kind": "shared util (temp-name shape regex)"
  },
  {
   "where": "fix.diff:878-884",
   "entry_point": "same as above (isTempFile renamed to getTempFile, returns the extracted hash)",
   "module_kind": "shared util"
  },
  {
   "where": "fix.diff:942-947",
   "entry_point": "POST /cgi-bin/temp/create (lib/service/service.js:470-480); refactor only, the temp dir constant moved into common",
   "module_kind": "shared util (writer)"
  },
  {
   "where": "fix.diff:560-562",
   "entry_point": "plugin discovery at startup/refresh (lib/plugins/get-plugins.js, get-plugins-sync.js); plugin-precedence check, not the file-read sink",
   "module_kind": "plugin loader"
  }
 ],
 "O1_entry_points": 3,
 "O2_out_of_scope_site": {
  "kind": "lower_level_api",
  "where": "lib/service/service.js:305-312 (gate added at fix.diff:719-722); the forked service server that the webui proxies into"
 },
 "O3_reason_to_dismiss": "The service child only listens on a random loopback port and is meant to be reached through webui's sendToService, which already rejects non-temp filenames, so a solver can argue that hardening the internal server is out of scope.",
 "O4_distance": {
  "files": 3,
  "packages": 2,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Reading a local file by absolute path through temp/get / import-remote is a deliberate feature when login is configured (getFile on a raw filename). The temp/create output 'temp/<hash>' must still resolve. The main process's own POST to /cgi-bin/service/save sends no uid header. An over-broad fix (always confine to temp_files, or a gate that rejects internal callers) breaks these.",
  "where": "lib/service/service.js:458-466; lib/service/service.js:477; lib/service/index.js:168-175"
 },
 "O6_input_shapes": [
  "bare 64-hex temp name",
  "'temp/<hex>' prefix (as returned by temp/create)",
  "'/temp/<hex>' leading-slash prefix",
  "'<hex>.<ext>' suffix",
  "'filename' single value vs 'files' comma-separated list",
  "import-remote 'url' parameter rewritten into temp/get filename"
 ],
 "O7_producer": {
  "kind": "serializer",
  "where": "lib/service/index.js:17-32 (string config, including uid and TEMP_FILES_PATH, copied into the fork options read at lib/service/service.js:609-613)",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "GET /cgi-bin/import-remote is registered before the login middleware, so when login is configured the no-login guard is skipped and no auth runs before a local-path temp/get read",
   "where": "biz/webui/lib/index.js:414-439",
   "reason_to_dismiss": "import-remote looks like a remote-URL importer, and the advisory's guard is about no-login mode; the login-configured case looks protected by the auth middleware (biz/webui/lib/index.js:504-530), which actually sits after it",
   "distance": "different package (biz/webui) from the landing point (lib/service); same file as the existing guard",
   "present_in_latest": "no",
   "latest_where": "latest/biz/webui/lib/index.js:513"
  }
 ],
 "O8b_injection_room": [
  {
   "where": "lib/service/service.js:439-450",
   "sibling": "saved/sessions read path built from query filename; a variant that skips INVALID_NAME_RE sanitising would be a sibling traversal into the same read sink",
   "why_realistic": "it sits next to temp/get and builds a path from request input the same way; a maintainer adding a 'raw filename' option is plausible"
  },
  {
   "where": "lib/plugins/load-plugin.js:1203-1206",
   "sibling": "plugin-facing getTempFilePath helper; a sibling that falls back to the raw path when the temp regex misses would mirror the temp/get flaw",
   "why_realistic": "it is the same temp-path resolution exposed through the plugin API, a natural place for a convenience fallback"
  },
  {
   "where": "lib/util/index.js:1163-1168",
   "sibling": "rule-side getTempFilePath; same temp-name resolution for rule values",
   "why_realistic": "a third copy of the temp-path logic, so a divergent regex is easy to introduce"
  }
 ],
 "O9_family": "CWE-22 path traversal / arbitrary local file read through an unauthenticated internal service route",
 "O9_dos": false,
 "O10_build": {
  "language": "JavaScript (Node.js >= 8.8)",
  "toolchain": "npm install (no node_modules in the pinned tree); tape tests via node test/index.test.js",
  "services": [],
  "offline_after_build": true,
  "project_tests": "test/units/*.test.js (tape); none cover temp/get, import-remote, isTempFile or the service child"
 },
 "O11_fix_minutes": 40,
 "O12_red_flags": [],
 "O13_recall_risk": "low",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "lib/service/service.js, lib/util/common.js, lib/service/util.js, lib/config.js, lib/util/index.js, lib/plugins/load-plugin.js, lib/plugins/util.js, lib/plugins/get-plugins.js, lib/plugins/get-plugins-sync.js, lib/plugins/module-paths.js, lib/index.js (plus unrelated noise in lib/inspectors/*, lib/https/*, lib/rules/*, lib/service/composer.js, lib/socket-mgr.js, lib/handlers/file-proxy.js)",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Force temp/get to always path.join under temp_files (or block absolute paths) in the service handler; this breaks the logged-in local-import feature and leaves the service port and import-remote ordering unaddressed."
 },
 "out_of_scope_notes": [
  "/service/*, /cgi-bin/service/*, /cgi-bin/sessions/*, /cgi-bin/log/* and /cgi-bin/plugins/install are also registered before the login middleware (biz/webui/lib/index.js:440-444); other sinks, not pursued.",
  "readPluginPage joins plugin.path with a request-derived path (biz/webui/lib/index.js:455-456); a different sink, not pursued.",
  "The published commit mixes in many unrelated changes (SSE frame parsing, proxy-authorization, DNS cache, cookie Max-Age, matchFilter chance bug)."
 ],
 "unverified": [
  "PINNED TREE IS INCONSISTENT: biz/webui/lib/index.js:71 and :84 already call common.getTempFile and common.WHISTLE_UID_HEADER, but lib/util/common.js:73-77 at the pinned commit only defines isTempFile. The webui half of the fix seems to have landed in an earlier commit, so the pinned code likely throws a TypeError on the no-login temp/get guard. Our copy would need the biz side reverted or the lib side partly restored. None of the defined red flags covers this, but it is the biggest risk for this host.",
  "lib/service/index.js:168-175 (the main process's own POST to /cgi-bin/service/save) sends no uid header, and latest still lacks it per grep, so the published gate may break cloud-data sync. This was not run.",
  "Bind address of the service child (hagent getServer) not checked: node_modules is absent.",
  "Advisory text not available; the flaw was identified from the diff and the code only.",
  "repo_mb unknown (no shell size check); the tree has about 1,900 files including built htdocs bundles, so tiny_repo is unlikely.",
  "pinned_commit SHA not provided in the inputs."
 ]
}
  ```
- Published fix sites:   - fix.diff:719-722 — entry point: any HTTP request sent directly to the service child's local port (lib/service/service.js:305-313, all routes) [internal forked service server (lower-level API under the webui proxy)]
  - fix.diff:732-734 — entry point: GET /cgi-bin/temp/get?filename= (via biz/webui/lib/index.js:539) and GET /cgi-bin/import-remote?url= (biz/webui/lib/index.js:432-435) [service route handler]
  - fix.diff:701-702 — entry point: GET /cgi-bin/temp/get?files=a,b,c (lib/service/service.js:452-456) [service helper]
  - fix.diff:872 — entry point: common.getTempFile, used by the webui guard biz/webui/lib/index.js:66-72 and by the service handlers [shared util (temp-name shape regex)]
  - fix.diff:878-884 — entry point: same as above (isTempFile renamed to getTempFile, returns the extracted hash) [shared util]
  - fix.diff:942-947 — entry point: POST /cgi-bin/temp/create (lib/service/service.js:470-480); refactor only, the temp dir constant moved into common [shared util (writer)]
  - fix.diff:560-562 — entry point: plugin discovery at startup/refresh (lib/plugins/get-plugins.js, get-plugins-sync.js); plugin-precedence check, not the file-read sink [plugin loader]
- Uncovered routes to confirm (pattern B):   - biz/webui/lib/index.js:414-439 — GET /cgi-bin/import-remote is registered before the login middleware, so when login is configured the no-login guard is skipped and no auth runs before a local-path temp/get read (reason to dismiss: import-remote looks like a remote-URL importer, and the advisory's guard is about no-login mode; the login-configured case looks protected by the auth middleware (biz/webui/lib/index.js:504-530), which actually sits after it; still in latest: no)
- Design plan from the lead: MAIN LEVER: the published fix must be reproduced in full. The hidden tests require closing EVERY published fix site through its real entry point, including the site that looks out of scope (lower_level_api at lib/service/service.js:305-312 (gate added at fix.diff:719-722); the forked serv; a solver may dismiss it because: The service child only listens on a random loopback port and is meant to be reached through webui's sendToService, which already rejects non-temp filenames, so a solver can argue that hardening the in). The tempting wrong fix that must FAIL: Force temp/get to always path.join under temp_files (or block absolute paths) in the service handler; this breaks the logged-in local-import feature and leaves the service port and import-remote order.

INPUT-SHAPE / ROUTE VARIANTS (one security test each, driven through the real entry point, failing on the pinned code and passing on a correct fix): bare 64-hex temp name; 'temp/<hex>' prefix (as returned by temp/create); '/temp/<hex>' leading-slash prefix; '<hex>.<ext>' suffix; 'filename' single value vs 'files' comma-separated list; import-remote 'url' parameter rewritten into temp/get filename.

PRODUCER OFF THE CHECK'S PATH: the state is produced by a serializer at lib/service/index.js:17-32 (string config, including uid and TEMP_FILES_PATH, co that the check does not call; a fix only at the check misses it.

PATTERN B UNCOVERED ROUTES - confirm each with a behavioural test on the pinned copy before relying on it, then add one row per route to build/audit/uncovered-routes.tsv: biz/webui/lib/index.js:414-439 (dismiss: import-remote looks like a remote-URL importer, and the advisory's guard is abou; latest=no). These are unmodified upstream code the published fix did not touch; the task's reference fix closes them too.

COUPLED MUST-KEEP-WORKING (one functional test per trap so an over-broad fix fails): Reading a local file by absolute path through temp/get / import-remote is a deliberate feature when login is configured (getFile on a raw filename). The temp/create output 'temp/<hash>' must still resolve. The main proce (near lib/service/service.js:458-466; lib/service/service.js:477; ).

Aim for at least two levers with DIFFERENT reasons to dismiss. instruction.md stays at product level: state the system, one observed impact with one user-level trigger, and the security property as invariants worded to cover every tested route and shape; keep legitimate use working; never name files/functions/fields/CVEs (put every such identifier in manifest.leak_terms).
- Host notes: Language: JavaScript (Node.js >= 8.8). Offline after build (no external services). Security logic is testable without a live server/cluster - call the validation/transform functions directly with crafted inputs. The project's own tests for the area must pass at the pinned commit. Confirm each pattern-B route with a test on the pinned copy; most are fixed in current upstream. Pin at the given vulnerable commit; keep any unrelated earlier fixes present.

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

## Environment (`tasks/whistle-cwe-path/environment/Dockerfile`)
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

## Report to the solver (`tasks/whistle-cwe-path/instruction.md`)
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

## Tests (`tasks/whistle-cwe-path/tests/`)
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
- **Wrong-fix patches** go in `build/whistle-cwe-path/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/whistle-cwe-path/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/whistle-cwe-path/manifest.json`:**
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

**Also in `build/whistle-cwe-path/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py whistle-cwe-path --only static
python3 -I builder/gate.py whistle-cwe-path --only nop
python3 -I builder/gate.py whistle-cwe-path --only oracle
python3 -I builder/gate.py whistle-cwe-path --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/whistle-cwe-path/`;
  - edit only `tasks/whistle-cwe-path/`, `build/whistle-cwe-path/` and, for pattern B, the register;
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
