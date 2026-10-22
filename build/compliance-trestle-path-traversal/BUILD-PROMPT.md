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

Project root: `/home/mara/cwe-bench`. Task: `compliance-trestle-path-traversal`. Pattern: `A+B`. Track: `mined`.

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
- Advisory: GHSA-R4VP-3VW6-R2X5 / CVE-2026-57171 / PYSEC-2026-4030 - oscal-compass/compliance-trestle - path traversal / arbitrary file write and directory deletion via CLI output names (CWE-22). Whether a user-supplied output/task name (CLI -o / task-name), joined onto trestle_root, stays inside the trestle workspace before markdown dirs or model files are created, overwritten or deleted; decided per command (PathSecurityValidator.
- Pinned (vulnerable) commit: 0f82d19bd42f9cc0f1b3acd7fc3f6dafe3b6ae10. Published fix: 37ed44f5f2e074202c8eb7c2f203c05d19461cdc.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "5302",
 "advisory_ids": [
  "GHSA-R4VP-3VW6-R2X5",
  "CVE-2026-57171",
  "PYSEC-2026-4030"
 ],
 "repo": "oscal-compass/compliance-trestle",
 "pinned_commit": "parent of 37ed44f5f2e074202c8eb7c2f203c05d19461cdc (parent_commit not given in input)",
 "fix_commits": [
  "37ed44f5f2e074202c8eb7c2f203c05d19461cdc",
  "5335ff873a2a68eb7de43df029bea09cadff22fd"
 ],
 "trust_decision": {
  "summary": "Whether a user-supplied output/task name (CLI -o / task-name), joined onto trestle_root, stays inside the trestle workspace before markdown dirs or model files are created, overwritten or deleted; decided per command (PathSecurityValidator.validate_local_path) and in the shared name helper file_utils.is_directory_name_allowed.",
  "evidence": [
   "trestle/core/remote/security.py:400-435",
   "trestle/common/file_utils.py:95-122",
   "trestle/core/commands/author/catalog.py:69-90",
   "fix.diff:27-36",
   "fix.diff:57-58"
  ]
 },
 "landing_point": {
  "where": "trestle/core/commands/author/catalog.py:90",
  "why": "Summary says 'author generate commands'; catalog-generate builds markdown_path = trestle_root / args.output with only the reserved-name check at catalog.py:69."
 },
 "fix_sites": [
  {
   "where": "trestle/common/file_utils.py:95-122",
   "entry_point": "lower-level helper is_directory_name_allowed: reached by author catalog-generate/profile-generate/ssp-generate (-o), author component-generate (-o, component.py:77), author docs/folders/headers --task-name (common.py:54)",
   "module_kind": "shared utility (trestle/common), lower-level API"
  },
  {
   "where": "trestle/core/commands/author/catalog.py:90",
   "entry_point": "CLI: trestle author catalog-generate -o",
   "module_kind": "author CLI command"
  },
  {
   "where": "trestle/core/commands/author/prof.py:110",
   "entry_point": "CLI: trestle author profile-generate -o",
   "module_kind": "author CLI command"
  },
  {
   "where": "trestle/core/commands/author/ssp.py:111",
   "entry_point": "CLI: trestle author ssp-generate -o",
   "module_kind": "author CLI command"
  },
  {
   "where": "trestle/core/commands/author/headers.py:318",
   "entry_point": "CLI: trestle author headers validate (no task name, iterates root dirs)",
   "module_kind": "author CLI command; caller adapted (passes relative path) so the hardened helper does not reject legitimate absolute iterdir paths"
  },
  {
   "where": "trestle/core/commands/create.py:95",
   "entry_point": "CLI: trestle create -t <type> -o <name>",
   "module_kind": "top-level (non-author) CLI command"
  },
  {
   "where": "trestle/core/commands/replicate.py:90",
   "entry_point": "CLI: trestle replicate <type> -n <name> -o <output>",
   "module_kind": "top-level (non-author) CLI command"
  }
 ],
 "O1_entry_points": 9,
 "O2_out_of_scope_site": {
  "kind": "lower_level_api",
  "where": "trestle/common/file_utils.py:95-122 (shared name helper, reached by component-generate at trestle/core/commands/author/component.py:77 and task-name commands at trestle/core/commands/author/common.py:54); also non-author commands trestle/core/commands/create.py:95 and trestle/core/commands/replicate.py:90 that look outside 'author generate' scope"
 },
 "O3_reason_to_dismiss": "The report says 'author generate commands'; create/replicate/import and the *-assemble/profile-resolve/ssp-filter commands write OSCAL model JSON by 'model name' into catalogs/ profiles/ etc., so a solver can argue they are a different feature (model management, not markdown generation) and that a model name is not a path.",
 "O4_distance": {
  "files": 7,
  "packages": 3,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Nested relative task/output names like 'task/name' must stay allowed (fs_test expects True), and 'author headers validate' without task name passes iterdir() paths to the helper; rejecting absolute paths or any separator in the helper breaks these unless callers pass relative paths (the fix adapts headers.py).",
  "where": "tests/trestle/utils/fs_test.py:617; trestle/core/commands/author/headers.py:313-319"
 },
 "O6_input_shapes": [
  "leading '..' relative path (../../x)",
  "non-leading '..' component (sub/../../x)",
  "absolute POSIX path (/tmp/x)",
  "path starting with '/' on Windows (name.startswith('/'))",
  "resolved-path escape via validate_local_path (covers symlinked or otherwise non-normalised paths resolved by Path.resolve)"
 ],
 "O7_producer": {
  "kind": "mapper",
  "where": "trestle/common/model_utils.py:635-648 (_root_path_for_top_level_model maps model name to trestle_root/<models-dir>/<name>), used by save_top_level_model at trestle/common/model_utils.py:302-314",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "author catalog-assemble -o: model name mapped to path, existing parent dir rmtree'd, catalog.json written",
   "where": "trestle/core/commands/author/catalog.py:249-258",
   "reason_to_dismiss": "assemble writes an OSCAL model by name, not 'generate' markdown output",
   "distance": "same file as landing point, different command class",
   "present_in_latest": "yes",
   "latest_where": "latest/trestle/core/commands/author/catalog.py:262"
  },
  {
   "route": "author profile-assemble -o: same rmtree + write via model name",
   "where": "trestle/core/commands/author/prof.py:409-412",
   "reason_to_dismiss": "assemble, not generate",
   "distance": "fix-site file, different class",
   "present_in_latest": "yes",
   "latest_where": "latest/trestle/core/commands/author/prof.py:427"
  },
  {
   "route": "author component-assemble -o: same rmtree + write via model name",
   "where": "trestle/core/commands/author/component.py:251-254",
   "reason_to_dismiss": "component.py not touched by fix; assemble, not generate",
   "distance": "unfixed file in author package",
   "present_in_latest": "yes",
   "latest_where": "latest/trestle/core/commands/author/component.py:254"
  },
  {
   "route": "author ssp-assemble -o: save_top_level_model with output name",
   "where": "trestle/core/commands/author/ssp.py:530",
   "reason_to_dismiss": "assemble, not generate",
   "distance": "fix-site file, different class",
   "present_in_latest": "yes",
   "latest_where": "latest/trestle/core/commands/author/ssp.py:689"
  },
  {
   "route": "author ssp-filter -o: save_top_level_model with output name",
   "where": "trestle/core/commands/author/ssp.py:746",
   "reason_to_dismiss": "filter of existing model, neighbouring feature",
   "distance": "fix-site file, different class",
   "present_in_latest": "yes",
   "latest_where": "latest/trestle/core/commands/author/ssp.py:972"
  },
  {
   "route": "author profile-resolve -o: resolved catalog saved by name",
   "where": "trestle/core/commands/author/prof.py:479",
   "reason_to_dismiss": "resolve output is a catalog model, not markdown",
   "distance": "fix-site file, different class",
   "present_in_latest": "yes",
   "latest_where": "latest/trestle/core/commands/author/prof.py:574"
  },
  {
   "route": "author profile-inherit -o: profile saved by name",
   "where": "trestle/core/commands/author/prof.py:771",
   "reason_to_dismiss": "inherit is a neighbouring feature, output is model JSON",
   "distance": "fix-site file, different class",
   "present_in_latest": "yes",
   "latest_where": "latest/trestle/core/commands/author/prof.py:827"
  },
  {
   "route": "import -o: output name joined under model dir and written; sibling of create/replicate which were fixed",
   "where": "trestle/core/commands/import_.py:81-84",
   "reason_to_dismiss": "import reads external content; output naming seen as model management",
   "distance": "trestle/core/commands, unfixed file, two packages from landing",
   "present_in_latest": "yes",
   "latest_where": "latest/trestle/core/commands/import_.py:81"
  },
  {
   "route": "author component-generate --force-overwrite: clear_folder(args.output) runs before the name check",
   "where": "trestle/core/commands/author/component.py:63-77",
   "reason_to_dismiss": "force-overwrite is an opt-in flag and the name check exists in the same command",
   "distance": "unfixed file in author package",
   "present_in_latest": "yes",
   "latest_where": "latest/trestle/core/commands/author/component.py:66"
  }
 ],
 "O8b_injection_room": [
  {
   "where": "trestle/core/commands/author/component.py:89",
   "sibling": "component.title from the comp-def JSON used as a markdown subdirectory name",
   "why_realistic": "model content becomes a path segment across a load boundary; a maintainer treats titles as display text"
  },
  {
   "where": "trestle/common/model_utils.py:302-314",
   "sibling": "a save-by-name helper that callers assume validates names",
   "why_realistic": "central mapper used by many commands; plausible to add a new caller that relies on the helper"
  }
 ],
 "O9_family": "path traversal / arbitrary file write and directory deletion via CLI output names (CWE-22)",
 "O9_dos": false,
 "O10_build": {
  "language": "Python (>=3.10)",
  "toolchain": "pip/pyproject (pytest>=8.1, pytest-xdist, pytest-randomly)",
  "services": [],
  "offline_after_build": true,
  "project_tests": "tests/trestle/utils/fs_test.py (test_allowed_task_name), tests/trestle/core/commands/author/{catalog,prof,ssp,component,headers,docs,folders}_test.py, tests/trestle/core/commands/{create,replicate}_test.py"
 },
 "O11_fix_minutes": 50,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "trestle/common/file_utils.py, trestle/core/commands/author/catalog.py, trestle/core/commands/author/headers.py, trestle/core/commands/author/prof.py, trestle/core/commands/author/ssp.py, trestle/core/commands/create.py, trestle/core/commands/replicate.py",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Add validate_local_path to the three author *-generate commands only (like the earlier jinja fix), leaving the shared helper, create/replicate and component-generate open."
 },
 "out_of_scope_notes": [
  "replicate -n input path (trestle/core/commands/replicate.py:77) and catalog/profile -n read paths are read-side traversal, not this write protection.",
  "clear_folder(pathlib.Path(args.output)) resolves relative to cwd, not trestle_root (trestle/core/commands/author/catalog.py:75); not pursued."
 ],
 "unverified": [
  "pinned_commit hash not provided; assumed parent of first fix commit.",
  "repo_mb not measured (no shell).",
  "Whether the second fix commit 5335ff8 differs from the combined diff was not checked separately.",
  "split/merge/assemble top-level commands and the markdown file names derived from control/group ids were not traced.",
  "O1 counts: catalog/profile/ssp/component-generate, author docs/folders/headers task-name (3), create, replicate = 9; headers validate is counted within headers."
 ]
}
  ```
- Published fix sites:   - trestle/common/file_utils.py:95-122 — entry point: lower-level helper is_directory_name_allowed: reached by author catalog-generate/profile-generate/ssp-generate (-o), author component-generate (-o, component.py:77), author docs/folders/headers --task-name (common.py:54) [shared utility (trestle/common), lower-level API]
  - trestle/core/commands/author/catalog.py:90 — entry point: CLI: trestle author catalog-generate -o [author CLI command]
  - trestle/core/commands/author/prof.py:110 — entry point: CLI: trestle author profile-generate -o [author CLI command]
  - trestle/core/commands/author/ssp.py:111 — entry point: CLI: trestle author ssp-generate -o [author CLI command]
  - trestle/core/commands/author/headers.py:318 — entry point: CLI: trestle author headers validate (no task name, iterates root dirs) [author CLI command; caller adapted (passes relative path) so the hardened helper does not reject legitimate absolute iterdir paths]
  - trestle/core/commands/create.py:95 — entry point: CLI: trestle create -t <type> -o <name> [top-level (non-author) CLI command]
  - trestle/core/commands/replicate.py:90 — entry point: CLI: trestle replicate <type> -n <name> -o <output> [top-level (non-author) CLI command]
- Uncovered routes to confirm (pattern B):   - trestle/core/commands/author/catalog.py:249-258 — author catalog-assemble -o: model name mapped to path, existing parent dir rmtree'd, catalog.json written (reason to dismiss: assemble writes an OSCAL model by name, not 'generate' markdown output; still in latest: yes)
  - trestle/core/commands/author/prof.py:409-412 — author profile-assemble -o: same rmtree + write via model name (reason to dismiss: assemble, not generate; still in latest: yes)
  - trestle/core/commands/author/component.py:251-254 — author component-assemble -o: same rmtree + write via model name (reason to dismiss: component.py not touched by fix; assemble, not generate; still in latest: yes)
  - trestle/core/commands/author/ssp.py:530 — author ssp-assemble -o: save_top_level_model with output name (reason to dismiss: assemble, not generate; still in latest: yes)
  - trestle/core/commands/author/ssp.py:746 — author ssp-filter -o: save_top_level_model with output name (reason to dismiss: filter of existing model, neighbouring feature; still in latest: yes)
  - trestle/core/commands/author/prof.py:479 — author profile-resolve -o: resolved catalog saved by name (reason to dismiss: resolve output is a catalog model, not markdown; still in latest: yes)
  - trestle/core/commands/author/prof.py:771 — author profile-inherit -o: profile saved by name (reason to dismiss: inherit is a neighbouring feature, output is model JSON; still in latest: yes)
  - trestle/core/commands/import_.py:81-84 — import -o: output name joined under model dir and written; sibling of create/replicate which were fixed (reason to dismiss: import reads external content; output naming seen as model management; still in latest: yes)
  - trestle/core/commands/author/component.py:63-77 — author component-generate --force-overwrite: clear_folder(args.output) runs before the name check (reason to dismiss: force-overwrite is an opt-in flag and the name check exists in the same command; still in latest: yes)
- Design plan from the lead: MAIN LEVER: the published fix must be reproduced in full. The hidden tests require closing EVERY published fix site through its real entry point, including the site that looks out of scope (lower_level_api at trestle/common/file_utils.py:95-122 (shared name helper, reached by component-ge; a solver may dismiss it because: The report says 'author generate commands'; create/replicate/import and the *-assemble/profile-resolve/ssp-filter commands write OSCAL model JSON by 'model name' into catalogs/ profiles/ etc., so a so). The tempting wrong fix that must FAIL: Add validate_local_path to the three author *-generate commands only (like the earlier jinja fix), leaving the shared helper, create/replicate and component-generate open..

INPUT-SHAPE / ROUTE VARIANTS (one security test each, driven through the real entry point, failing on the pinned code and passing on a correct fix): leading '..' relative path (../../x); non-leading '..' component (sub/../../x); absolute POSIX path (/tmp/x); path starting with '/' on Windows (name.startswith('/')); resolved-path escape via validate_local_path (covers symlinked or otherwise non-normalised paths resolved by Path.resolve).

PRODUCER OFF THE CHECK'S PATH: the state is produced by a mapper at trestle/common/model_utils.py:635-648 (_root_path_for_top_level_model maps model that the check does not call; a fix only at the check misses it.

PATTERN B UNCOVERED ROUTES - confirm each with a behavioural test on the pinned copy before relying on it, then add one row per route to build/audit/uncovered-routes.tsv: trestle/core/commands/author/catalog.py:249-258 (dismiss: assemble writes an OSCAL model by name, not 'generate' markdown output; latest=yes); trestle/core/commands/author/prof.py:409-412 (dismiss: assemble, not generate; latest=yes); trestle/core/commands/author/component.py:251-254 (dismiss: component.py not touched by fix; assemble, not generate; latest=yes); trestle/core/commands/author/ssp.py:530 (dismiss: assemble, not generate; latest=yes); trestle/core/commands/author/ssp.py:746 (dismiss: filter of existing model, neighbouring feature; latest=yes); trestle/core/commands/author/prof.py:479 (dismiss: resolve output is a catalog model, not markdown; latest=yes); trestle/core/commands/author/prof.py:771 (dismiss: inherit is a neighbouring feature, output is model JSON; latest=yes); trestle/core/commands/import_.py:81-84 (dismiss: import reads external content; output naming seen as model management; latest=yes); trestle/core/commands/author/component.py:63-77 (dismiss: force-overwrite is an opt-in flag and the name check exists in the same command; latest=yes). These are unmodified upstream code the published fix did not touch; the task's reference fix closes them too.

COUPLED MUST-KEEP-WORKING (one functional test per trap so an over-broad fix fails): Nested relative task/output names like 'task/name' must stay allowed (fs_test expects True), and 'author headers validate' without task name passes iterdir() paths to the helper; rejecting absolute paths or any separator (near tests/trestle/utils/fs_test.py:617; trestle/core/commands/au).

Aim for at least two levers with DIFFERENT reasons to dismiss. instruction.md stays at product level: state the system, one observed impact with one user-level trigger, and the security property as invariants worded to cover every tested route and shape; keep legitimate use working; never name files/functions/fields/CVEs (put every such identifier in manifest.leak_terms).
- Host notes: Language: Python (>=3.10). Offline after build (no external services). Security logic is testable without a live server/cluster - call the validation/transform functions directly with crafted inputs. The project's own tests for the area must pass at the pinned commit. Confirm each pattern-B route with a test on the pinned copy; most are fixed in current upstream. Pin at the given vulnerable commit; keep any unrelated earlier fixes present.

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

## Environment (`tasks/compliance-trestle-path-traversal/environment/Dockerfile`)
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

## Report to the solver (`tasks/compliance-trestle-path-traversal/instruction.md`)
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

## Tests (`tasks/compliance-trestle-path-traversal/tests/`)
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
- **Wrong-fix patches** go in `build/compliance-trestle-path-traversal/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/compliance-trestle-path-traversal/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/compliance-trestle-path-traversal/manifest.json`:**
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

**Also in `build/compliance-trestle-path-traversal/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py compliance-trestle-path-traversal --only static
python3 -I builder/gate.py compliance-trestle-path-traversal --only nop
python3 -I builder/gate.py compliance-trestle-path-traversal --only oracle
python3 -I builder/gate.py compliance-trestle-path-traversal --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/compliance-trestle-path-traversal/`;
  - edit only `tasks/compliance-trestle-path-traversal/`, `build/compliance-trestle-path-traversal/` and, for pattern B, the register;
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
