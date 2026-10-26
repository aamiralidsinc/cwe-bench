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

Project root: `/home/mara/cwe-bench`. Task: `wakaru-mm`. Pattern: `A`. Track: `injected`.

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
- Advisory: ["GHSA-7WPJ-VVMV-PGM8", "CVE-2026-54545"]; pionxzh/wakaru; path traversal / arbitrary file write (CWE-22) via attacker-controlled archive-like entry names (zip-slip analogue) plus symlink-following
- Pinned (vulnerable) commit: parent of 1d30383b20a6f768786b8ada2f1b0945de13c316 (parent_commit not given in input). Published fix: 1d30383b20a6f768786b8ada2f1b0945de13c316.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "9641",
 "advisory_ids": [
  "GHSA-7WPJ-VVMV-PGM8",
  "CVE-2026-54545"
 ],
 "repo": "pionxzh/wakaru",
 "pinned_commit": "parent of 1d30383b20a6f768786b8ada2f1b0945de13c316 (parent_commit not given in input)",
 "fix_commits": [
  "1d30383b20a6f768786b8ada2f1b0945de13c316"
 ],
 "trust_decision": {
  "summary": "Bundle-supplied module ids/names (webpack4/5 string keys, SystemJS register names, esbuild __commonJS keys) are trusted as relative output filenames; the unpackers' replace/trim-based sanitizers and the CLI's out_dir.join() decide whether the written path stays inside -o, with no component-based or canonical containment check.",
  "evidence": [
   "crates/core/src/unpacker/webpack5.rs:1156-1164",
   "crates/core/src/unpacker/webpack4.rs:840-848",
   "crates/core/src/unpacker/systemjs.rs:810-821",
   "crates/core/src/unpacker/esbuild.rs:579-591",
   "crates/cli/src/main.rs:236-259"
  ]
 },
 "landing_point": {
  "where": "crates/cli/src/main.rs:239",
  "why": "Advisory says '@wakaru/cli arbitrary file write during bundle unpack'; the --unpack branch of run_default is where module filenames are joined to the output dir and written."
 },
 "fix_sites": [
  {
   "where": "crates/cli/src/main.rs:213-259",
   "entry_point": "CLI `wakaru <bundle> --unpack -o <dir>` (run_default); fix adds canonical out_dir, component check and per-parent symlink containment (fix.diff:17-43, fix.diff:51-152)",
   "module_kind": "cli_writer (sink)"
  },
  {
   "where": "crates/core/src/unpacker/mod.rs:23-26",
   "entry_point": "shared helper sanitize_relative_path added (fix.diff:421-437); reached via core public API unpack/unpack_raw/unpack_files and wasm unpack",
   "module_kind": "shared_core_helper"
  },
  {
   "where": "crates/core/src/unpacker/webpack5.rs:1156",
   "entry_point": "CLI --unpack / core unpack() on webpack5 bundle with string module ids (callers webpack5.rs:576-577, webpack5.rs:634-635)",
   "module_kind": "bundler_format_parser"
  },
  {
   "where": "crates/core/src/unpacker/webpack4.rs:840",
   "entry_point": "CLI --unpack / core unpack() / public unpack_webpack4 on webpack4 bundle with string keys (callers webpack4.rs:639, webpack4.rs:710)",
   "module_kind": "bundler_format_parser"
  },
  {
   "where": "crates/core/src/unpacker/systemjs.rs:810",
   "entry_point": "CLI --unpack / core unpack() on System.register(\"name\", ...) bundle (caller systemjs.rs:803)",
   "module_kind": "bundler_format_parser (second implementation)"
  },
  {
   "where": "crates/core/src/unpacker/esbuild.rs:579",
   "entry_point": "CLI --unpack / core unpack() on esbuild __commonJS({\"path\"(){}}) bundle (caller esbuild.rs:474-476)",
   "module_kind": "bundler_format_parser (second implementation, different sanitizer shape)"
  }
 ],
 "O1_entry_points": 4,
 "O2_out_of_scope_site": {
  "kind": "second_implementation",
  "where": "crates/core/src/unpacker/esbuild.rs:579-591 and crates/core/src/unpacker/systemjs.rs:810-821 (separate per-bundler sanitizers in core crate, away from the CLI landing point); also the CLI-side symlink containment, crates/cli/src/main.rs:244-259"
 },
 "O3_reason_to_dismiss": "Advisory example and payload are webpack5 ('....//node_modules/...'); esbuild's sanitize_path already strips '../' with a comment claiming it 'doesn't escape' (esbuild.rs:584-585) and systemjs trims slashes, so a solver can argue those formats are already safe or not the reported bundler; the symlink-parent case can be argued as 'attacker cannot create symlinks in my output dir'.",
 "O4_distance": {
  "files": 6,
  "packages": 2,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Legitimate nested module paths must still be written in subdirectories (src/index.js, node_modules/...), names like '....' are ordinary directories and must be kept (fix test expects '..../node_modules/...' under out_dir), and case-collision dedup (index_2.js) must still work; an over-broad fix that rejects any '..' substring, flattens paths, or bails on all dots breaks these.",
  "where": "crates/cli/src/main.rs:595-616; fix.diff:183-203; fix.diff:264-285; fix.diff:446-460"
 },
 "O6_input_shapes": [
  "overlapping dots '....//x' that collapse to '../x' after single-pass replace (fix.diff:449-450)",
  "backslash separators '.\\..\\x' (fix.diff:453-454, fix.diff:576-578)",
  "mid-path '..' components 'src/../utils' (fix.diff:457)",
  "absolute paths '/tmp/escape.js' rejected at CLI (fix.diff:205-225)",
  "Windows drive prefixes 'C:\\...' (fix.diff:227-243)",
  "traversal-only/empty ids fall back to default name (fix.diff:463-468)",
  "existing symlinked parent directory inside out_dir pointing outside (fix.diff:323-346)",
  "existing parent path that is a file (fix.diff:245-261)"
 ],
 "O7_producer": {
  "kind": "mapper",
  "where": "crates/core/src/unpacker/webpack5.rs:576-579, crates/core/src/unpacker/webpack4.rs:637-640, crates/core/src/unpacker/systemjs.rs:803, crates/core/src/unpacker/esbuild.rs:474-476 (module id -> filename mappers in core); CLI check at crates/cli/src/main.rs:239 consumes their output",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "`wakaru extract <map> -o <dir>` writes source-map `sources` entries via create_dir_all+fs::write with only lexical component filtering; no canonical/symlink-parent containment like the fix added for --unpack.",
   "where": "crates/cli/src/main.rs:328-344",
   "reason_to_dismiss": "Different subcommand (source-map extract, not bundle unpack) and resolve_source_path already drops '..'/root components (crates/core/src/sourcemap_rename.rs:64-88), so it looks already fixed; only the symlink-in-output-dir variant remains, which needs --force on a non-empty dir.",
   "distance": "same file as landing point, different subcommand; path logic in crates/core/src/sourcemap_rename.rs (other crate)",
   "present_in_latest": "yes",
   "latest_where": "latest/crates/cli/src/main.rs:852-854"
  }
 ],
 "O8b_injection_room": [
  {
   "where": "crates/core/src/unpacker/browserify.rs:89-95",
   "sibling": "browserify unpacker could name modules from string keys or the require map's path strings with a local replace-based sanitizer",
   "why_realistic": "Browserify bundles carry original paths in dependency maps; a maintainer wanting nicer filenames would copy the webpack sanitize_filename pattern."
  },
  {
   "where": "crates/core/src/sourcemap_rename.rs:64-88",
   "sibling": "a sourcemap-driven module rename in the unpack path (use original `sources` path as output filename) reusing a trim-based strip",
   "why_realistic": "--unpack already accepts --source-map (crates/cli/src/main.rs:199-206); deriving module filenames from it is a natural feature."
  },
  {
   "where": "crates/core/src/driver/unpack.rs:328-351",
   "sibling": "multi-input unpack prefixing module filenames with the input file's relative directory (input_group) without component checks",
   "why_realistic": "unpack_files already groups modules by input parent dir (crates/core/src/driver/unpack.rs:353-358) and dedups filenames there."
  }
 ],
 "O9_family": "path traversal / arbitrary file write (CWE-22) via attacker-controlled archive-like entry names (zip-slip analogue) plus symlink-following",
 "O9_dos": false,
 "O10_build": {
  "language": "Rust",
  "toolchain": "cargo (workspace crates/core, crates/cli, crates/wasm; swc_core)",
  "services": [],
  "offline_after_build": true,
  "project_tests": "cargo test: unit tests in crates/core/src/unpacker/{webpack4,webpack5,systemjs}.rs (e.g. crates/core/src/unpacker/webpack5.rs:1470-1497), integration tests crates/core/tests/bundle_unpack.rs, CLI tests in crates/cli/src/main.rs mod tests"
 },
 "O11_fix_minutes": 45,
 "O12_red_flags": [],
 "O13_recall_risk": "low",
 "pattern_fit": "A",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "crates/cli/src/main.rs, crates/core/src/unpacker/mod.rs, crates/core/src/unpacker/esbuild.rs, crates/core/src/unpacker/systemjs.rs, crates/core/src/unpacker/webpack4.rs, crates/core/src/unpacker/webpack5.rs",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Loop the replace(\"../\") in webpack5 sanitize_filename until stable (or add a '..' check only in webpack5), leaving esbuild/systemjs/webpack4 sanitizers and the CLI symlink-parent escape untouched."
 },
 "out_of_scope_notes": [
  "crates/cli/src/main.rs:625 creates --profile file at a user-supplied path (user-controlled, not bundle-controlled); not pursued.",
  "wasm crate exposes unpack (crates/wasm/src/lib.rs:67) returning filenames to JS callers; any JS-side writer is outside this repo's scope."
 ],
 "unverified": [
  "pinned_commit hash not provided (parent_commit null); assumed repo dir is the fix's parent.",
  "repo_mb not measured (no shell); tiny_repo/giant_repo not assessed.",
  "Exact Windows behaviour of backslash ids on Unix not exercised; on Unix '\\' is a Normal path byte, so backslash variants matter mainly for Windows.",
  "Whether README/docs describe the output-dir containment guarantee was not checked; protection_documented_without_exceptions not flagged.",
  "O8 extract route: only the symlink-parent variant is uncovered; lexical traversal is already blocked there (crates/core/src/sourcemap_rename.rs:74-86). Weak Pattern B.",
  "recall_risk 'low' is an estimate: advisory published 2026-07-28, after likely training cutoffs; not verified."
 ]
}
  ```
- Published fix sites:   - crates/cli/src/main.rs:213-259 — entry point: CLI `wakaru <bundle> --unpack -o <dir>` (run_default); fix adds canonical out_dir, component check and per-parent symlink containment (fix.diff:17-43, fix.diff:51-152) [cli_writer (sink)]
  - crates/core/src/unpacker/mod.rs:23-26 — entry point: shared helper sanitize_relative_path added (fix.diff:421-437); reached via core public API unpack/unpack_raw/unpack_files and wasm unpack [shared_core_helper]
  - crates/core/src/unpacker/webpack5.rs:1156 — entry point: CLI --unpack / core unpack() on webpack5 bundle with string module ids (callers webpack5.rs:576-577, webpack5.rs:634-635) [bundler_format_parser]
  - crates/core/src/unpacker/webpack4.rs:840 — entry point: CLI --unpack / core unpack() / public unpack_webpack4 on webpack4 bundle with string keys (callers webpack4.rs:639, webpack4.rs:710) [bundler_format_parser]
  - crates/core/src/unpacker/systemjs.rs:810 — entry point: CLI --unpack / core unpack() on System.register("name", ...) bundle (caller systemjs.rs:803) [bundler_format_parser (second implementation)]
  - crates/core/src/unpacker/esbuild.rs:579 — entry point: CLI --unpack / core unpack() on esbuild __commonJS({"path"(){}}) bundle (caller esbuild.rs:474-476) [bundler_format_parser (second implementation, different sanitizer shape)]
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

## Environment (`tasks/wakaru-mm/environment/Dockerfile`)
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

## Report to the solver (`tasks/wakaru-mm/instruction.md`)
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

## Tests (`tasks/wakaru-mm/tests/`)
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
- **Wrong-fix patches** go in `build/wakaru-mm/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/wakaru-mm/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/wakaru-mm/manifest.json`:**
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

**Also in `build/wakaru-mm/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py wakaru-mm --only static
python3 -I builder/gate.py wakaru-mm --only nop
python3 -I builder/gate.py wakaru-mm --only oracle
python3 -I builder/gate.py wakaru-mm --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/wakaru-mm/`;
  - edit only `tasks/wakaru-mm/`, `build/wakaru-mm/` and, for pattern B, the register;
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
