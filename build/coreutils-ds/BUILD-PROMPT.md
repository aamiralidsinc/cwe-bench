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

Project root: `/home/mara/cwe-bench`. Task: `coreutils-ds`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: ["GHSA-GWM6-Q8CH-HCFR", "CVE-2026-35356"]; uutils/coreutils; CWE-367/CWE-59 TOCTOU symlink-following in path-based directory creation and file write (link following / filesystem race)
- Pinned (vulnerable) commit: parent of 0c41299975f3c1e21cf5ca968d42cad55ceb42a1 (parent hash not supplied; tree at /home/mara/screen5/hosts/21068/repo). Published fix: 0c41299975f3c1e21cf5ca968d42cad55ceb42a1.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "21068",
 "advisory_ids": [
  "GHSA-GWM6-Q8CH-HCFR",
  "CVE-2026-35356"
 ],
 "repo": "uutils/coreutils",
 "pinned_commit": "parent of 0c41299975f3c1e21cf5ca968d42cad55ceb42a1 (parent hash not supplied; tree at /home/mara/screen5/hosts/21068/repo)",
 "fix_commits": [
  "0c41299975f3c1e21cf5ca968d42cad55ceb42a1"
 ],
 "trust_decision": {
  "summary": "install -D trusts that every component of the destination's parent path is a real directory and not an attacker-swappable symlink; this is decided implicitly in standard() by a path-based fs::create_dir_all followed by a path-based create of the destination file, both of which follow symlinks.",
  "evidence": [
   "src/uu/install/src/install.rs:624-643",
   "src/uu/install/src/install.rs:681-682",
   "src/uu/install/src/install.rs:845-849"
  ]
 },
 "landing_point": {
  "where": "src/uu/install/src/install.rs:641",
  "why": "The summary names 'install -D' and 'directory creation'; the only directory-creation call under b.create_leading is fs::create_dir_all here."
 },
 "fix_sites": [
  {
   "where": "src/uu/install/src/install.rs:641",
   "entry_point": "CLI: install -D SRC DEST (also install -D -t DIR SRC...)",
   "module_kind": "CLI utility, primary implementation (dir creation replaced by create_dir_all_safe, fix.diff:212-251)"
  },
  {
   "where": "src/uu/install/src/install.rs:624",
   "entry_point": "CLI: install -D SRC DEST where parent already exists",
   "module_kind": "CLI utility (existing-dir branch now rejects a symlinked final component and opens it O_NOFOLLOW, fix.diff:179-201)"
  },
  {
   "where": "src/uu/install/src/install.rs:681-682",
   "entry_point": "CLI: install -D SRC DEST, single source, no -t",
   "module_kind": "CLI utility (file write moved to fd-anchored copy_file_safe, fix.diff:287-311, 323-353)"
  },
  {
   "where": "src/uu/install/src/install.rs:653-659",
   "entry_point": "CLI: install -D -t DIR SRC",
   "module_kind": "CLI utility (target-is-file check moved before creation, fix.diff:163-166)"
  },
  {
   "where": "src/uucore/src/lib/features/safe_traversal.rs:108-109",
   "entry_point": "uucore public API DirFd::open / open_subdir (used by install, rm, du, chmod, chown)",
   "module_kind": "shared lower-level library crate (adds SymlinkBehavior/O_NOFOLLOW, mkdir_at, open_file_at, create_dir_all_safe; fix.diff:608-633, 648-675, 741-774, 783-927)"
  }
 ],
 "O1_entry_points": 2,
 "O2_out_of_scope_site": {
  "kind": "lower_level_api",
  "where": "src/uucore/src/lib/features/safe_traversal.rs:108-120 (DirFd::open/open_subdir have no no-follow mode; fix adds it plus create_dir_all_safe in the shared uucore crate, fix.diff:648-675, 917-927)"
 },
 "O3_reason_to_dismiss": "install -d is the separate 'directory mode' (the advisory says -D), and -t / multi-source installs into a directory the user named explicitly, so a solver can argue both are outside the '-D creates the leading directories of DEST' race.",
 "O4_distance": {
  "files": 2,
  "packages": 2,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Installing through legitimate pre-existing directory symlinks in the ancestor path (e.g. /var -> /private/var, a symlinked prefix) and overwriting an existing DEST with -b backup / -C compare must keep working; an over-broad fix that refuses every symlink in the path, or unlinks before backup, breaks these.",
  "where": "src/uu/install/src/install.rs:782-801 (perform_backup renames by path), src/uu/install/src/install.rs:964-971 (compare/backup before copy); fix.diff:906-907 documents the follow-existing-symlinks intent"
 },
 "O6_input_shapes": [
  "missing intermediate directories (plain create)",
  "pre-existing symlink as an intermediate component (fix.diff:871-875)",
  "symlink as the final to_create component (fix.diff:179-185)",
  "existing non-directory where a component should be (AlreadyExists -> NotADirectory, fix.diff:236-244)",
  "trailing-slash parent path (install.rs:611-622)",
  "relative path with empty parent resolved to '.' (fix.diff:807-810)",
  "-t DIR combined with -D, DIR existing as file (fix.diff:163-166)"
 ],
 "O7_producer": {
  "kind": "none",
  "where": "",
  "check_calls_producer": null
 },
 "O8_uncovered_routes": [
  {
   "route": "install -d DIR creates all ancestors with path-based fs::create_dir_all, then chmod/chown by path; the fix only changed a cfg attribute here.",
   "where": "src/uu/install/src/install.rs:485",
   "reason_to_dismiss": "-d is directory mode, not -D; the code comment at install.rs:481-484 even calls create_dir_all 'safe' here.",
   "distance": "same file, ~150 lines above the landing point, different function (directory())",
   "present_in_latest": "yes",
   "latest_where": "latest/src/uu/install/src/install.rs:528"
  },
  {
   "route": "install -D -t DIR SRC... and -D with multiple sources: directories are created safely but the file write goes through path-based copy_files_into_dir -> copy -> copy_file, re-resolving the (swappable) path.",
   "where": "src/uu/install/src/install.rs:722",
   "reason_to_dismiss": "the published fix explicitly gates the fd path on target_dir.is_none() && sources.len()==1 (fix.diff:190-192, 218-220), so a solver mirroring it sees -t/multi-source as a deliberately unsupported combination.",
   "distance": "same file, different function (copy_files_into_dir)",
   "present_in_latest": "yes",
   "latest_where": "latest/src/uu/install/src/install.rs:914"
  },
  {
   "route": "post-copy chmod/chown/strip/timestamp run by path on DEST after the fd-anchored write, so a parent swapped after creation redirects metadata changes.",
   "where": "src/uu/install/src/install.rs:973-982",
   "reason_to_dismiss": "the advisory is about file overwrite during directory creation, and metadata ops on an already-written file look like a neighbouring feature.",
   "distance": "same file; mode::chmod sits in uucore (src/uucore/src/lib/features/mode.rs)",
   "present_in_latest": "yes",
   "latest_where": "latest/src/uu/install/src/install.rs:1204"
  }
 ],
 "O8b_injection_room": [
  {
   "where": "src/uu/install/src/install.rs:699-722",
   "sibling": "copy_files_into_dir keeps a path-based write into a -D-created directory",
   "why_realistic": "it already exists at the latest release; a maintainer porting the single-file fd path would naturally leave the loop path-based."
  },
  {
   "where": "src/uu/install/src/install.rs:782-796",
   "sibling": "perform_backup renames DEST by path inside a -D-created parent",
   "why_realistic": "backup is a separate helper that takes a Path, so it is easy to leave out of an fd-anchored refactor."
  }
 ],
 "O9_family": "CWE-367/CWE-59 TOCTOU symlink-following in path-based directory creation and file write (link following / filesystem race)",
 "O9_dos": false,
 "O10_build": {
  "language": "Rust",
  "toolchain": "cargo (stable Rust; workspace of ~116 crates), crate uu_install + uucore features safe_traversal",
  "services": [],
  "offline_after_build": true,
  "project_tests": "tests/by-util/test_install.rs (integration via TestScenario; e.g. test_install_normal_file_replaces_symlink at tests/by-util/test_install.rs:2550) and unit tests in src/uucore/src/lib/features/safe_traversal.rs mod tests"
 },
 "O11_fix_minutes": 75,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "src/uu/install/src/install.rs, src/uucore/src/lib/features/safe_traversal.rs (plus mechanical signature updates in src/uu/chmod/src/chmod.rs, src/uu/du/src/du.rs, src/uu/rm/src/platform/unix.rs, src/uucore/src/lib/features/perms.rs)",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 0,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Add a symlink_metadata/is_symlink check on each component before fs::create_dir_all at install.rs:641 (still racy, and leaves install -d, -t and the path-based write open)."
 },
 "out_of_scope_notes": [
  "mkdir -p builds parents path-based via DirBuilder (src/uu/mkdir/src/mkdir.rs:281-288); same mechanism in another utility, not pursued.",
  "The published create_dir_all_safe unlinks any pre-existing symlinked ancestor and replaces it with an empty directory (fix.diff:796-805, 871-874), contrary to its own doc comment (fix.diff:906-907); hidden tests built on the published fix would encode that behaviour."
 ],
 "unverified": [
  "pinned commit hash: parent_commit is null in the candidate; only the tree was inspected.",
  "repo_mb: size not measured (no shell); uutils/coreutils source is likely tens of MB, so not tiny/giant, but unconfirmed.",
  "O11 estimate assumes the solver must write fd-anchored helpers in uucore themselves (none exist at the pinned commit).",
  "Whether hidden tests can exercise a real race deterministically; the published tests use pre-existing symlinks only (fix.diff:1309-1398).",
  "O13: CVE publication and blog coverage not checked (no network)."
 ]
}
  ```
- Published fix sites:   - src/uu/install/src/install.rs:641 — entry point: CLI: install -D SRC DEST (also install -D -t DIR SRC...) [CLI utility, primary implementation (dir creation replaced by create_dir_all_safe, fix.diff:212-251)]
  - src/uu/install/src/install.rs:624 — entry point: CLI: install -D SRC DEST where parent already exists [CLI utility (existing-dir branch now rejects a symlinked final component and opens it O_NOFOLLOW, fix.diff:179-201)]
  - src/uu/install/src/install.rs:681-682 — entry point: CLI: install -D SRC DEST, single source, no -t [CLI utility (file write moved to fd-anchored copy_file_safe, fix.diff:287-311, 323-353)]
  - src/uu/install/src/install.rs:653-659 — entry point: CLI: install -D -t DIR SRC [CLI utility (target-is-file check moved before creation, fix.diff:163-166)]
  - src/uucore/src/lib/features/safe_traversal.rs:108-109 — entry point: uucore public API DirFd::open / open_subdir (used by install, rm, du, chmod, chown) [shared lower-level library crate (adds SymlinkBehavior/O_NOFOLLOW, mkdir_at, open_file_at, create_dir_all_safe; fix.diff:608-633, 648-675, 741-774, 783-927)]
- Uncovered routes to confirm (pattern B):   - src/uu/install/src/install.rs:485 — install -d DIR creates all ancestors with path-based fs::create_dir_all, then chmod/chown by path; the fix only changed a cfg attribute here. (reason to dismiss: -d is directory mode, not -D; the code comment at install.rs:481-484 even calls create_dir_all 'safe' here.; still in latest: yes)
  - src/uu/install/src/install.rs:722 — install -D -t DIR SRC... and -D with multiple sources: directories are created safely but the file write goes through path-based copy_files_into_dir -> copy -> copy_file, re-resolving the (swappable) path. (reason to dismiss: the published fix explicitly gates the fd path on target_dir.is_none() && sources.len()==1 (fix.diff:190-192, 218-220), so a solver mirroring it sees -t/multi-source as a deliberately unsupported combination.; still in latest: yes)
  - src/uu/install/src/install.rs:973-982 — post-copy chmod/chown/strip/timestamp run by path on DEST after the fd-anchored write, so a parent swapped after creation redirects metadata changes. (reason to dismiss: the advisory is about file overwrite during directory creation, and metadata ops on an already-written file look like a neighbouring feature.; still in latest: yes)
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

## Environment (`tasks/coreutils-ds/environment/Dockerfile`)
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

## Report to the solver (`tasks/coreutils-ds/instruction.md`)
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

## Tests (`tasks/coreutils-ds/tests/`)
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
- **Wrong-fix patches** go in `build/coreutils-ds/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/coreutils-ds/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/coreutils-ds/manifest.json`:**
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

**Also in `build/coreutils-ds/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py coreutils-ds --only static
python3 -I builder/gate.py coreutils-ds --only nop
python3 -I builder/gate.py coreutils-ds --only oracle
python3 -I builder/gate.py coreutils-ds --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/coreutils-ds/`;
  - edit only `tasks/coreutils-ds/`, `build/coreutils-ds/` and, for pattern B, the register;
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
