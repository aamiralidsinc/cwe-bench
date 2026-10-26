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

Project root: `/home/mara/cwe-bench`. Task: `composer-mm`. Pattern: `A`. Track: `injected`.

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
- Advisory: ["GHSA-96H3-5X6V-M776", "BIT-COMPOSER-2026-59944", "CVE-2026-59944"]; composer/composer; path traversal / symlink following to an out-of-package file (CWE-22/CWE-59) leading to a permission change (CWE-732)
- Pinned (vulnerable) commit: unknown (parent of 53b8bb4c24697b2f00a18cf1ef35a10392701b89; parent_commit is null in the candidate). Published fix: 53b8bb4c24697b2f00a18cf1ef35a10392701b89, ad649fdfdf8ed826d4a34e0e5690c76a0b4833aa.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "33420",
 "advisory_ids": [
  "GHSA-96H3-5X6V-M776",
  "BIT-COMPOSER-2026-59944",
  "CVE-2026-59944"
 ],
 "repo": "composer/composer",
 "pinned_commit": "unknown (parent of 53b8bb4c24697b2f00a18cf1ef35a10392701b89; parent_commit is null in the candidate)",
 "fix_commits": [
  "53b8bb4c24697b2f00a18cf1ef35a10392701b89",
  "ad649fdfdf8ed826d4a34e0e5690c76a0b4833aa"
 ],
 "trust_decision": {
  "summary": "Whether a dependency-declared bin path (metadata string, or the file it names, possibly a symlink) may be chmod'd and proxied; at the pinned commit only a lexical '..' check exists at solver time (ValidatingArrayLoader::validatePackage, via LockTransaction), and the chmod sinks in BinaryInstaller::installBinaries and FileDownloader::install never resolve the real path against the package install dir.",
  "evidence": [
   "src/Composer/Package/Loader/ValidatingArrayLoader.php:545-552",
   "src/Composer/DependencyResolver/LockTransaction.php:75",
   "src/Composer/Installer/BinaryInstaller.php:74-117",
   "src/Composer/Downloader/FileDownloader.php:350-358"
  ]
 },
 "landing_point": {
  "where": "src/Composer/Installer/BinaryInstaller.php:116",
  "why": "The summary names a 'symlinked package bin path' bypass of GHSA-gjfg-22fp-rrxx; installBinaries is where bins are proxied and chmod'd, and the existing '..' check comment (ValidatingArrayLoader.php:545-547) points straight at BinaryInstaller."
 },
 "fix_sites": [
  {
   "where": "src/Composer/Installer/BinaryInstaller.php:80-84",
   "entry_point": "CLI composer install/update/require/reinstall -> LibraryInstaller::install/update (src/Composer/Installer/LibraryInstaller.php:163,191) and Installer ensureBinariesPresence loop (src/Composer/Installer.php:350-352 -> src/Composer/Installer/LibraryInstaller.php:250) -> BinaryInstaller::installBinaries",
   "module_kind": "installer (main implementation of bin handling)"
  },
  {
   "where": "src/Composer/Installer/BinaryInstaller.php:168",
   "entry_point": "new public static API BinaryInstaller::isBinPathInsidePackage (fix.diff:88-98), shared helper",
   "module_kind": "helper / public static API"
  },
  {
   "where": "src/Composer/Downloader/FileDownloader.php:353-356",
   "entry_point": "CLI composer install/update/reinstall of a package whose dist is a single non-archive file -> FileDownloader::install (public DownloaderInterface API)",
   "module_kind": "downloader (second implementation of bin chmod, lower layer, other package)"
  }
 ],
 "O1_entry_points": 4,
 "O2_out_of_scope_site": {
  "kind": "second_implementation",
  "where": "src/Composer/Downloader/FileDownloader.php:350-358"
 },
 "O3_reason_to_dismiss": "FileDownloader only handles single-file dists ('Single files can not have a mode set like files in archives', src/Composer/Downloader/FileDownloader.php:351-352), a single downloaded file cannot be a symlink, and '..' bins are already rejected at solver time (src/Composer/Package/Loader/ValidatingArrayLoader.php:548-551) - so a solver argues the downloader chmod is unreachable; the reinstall/installed.json route that skips validatePackage (src/Composer/Command/ReinstallCommand.php:110-118) defeats that argument.",
 "O4_distance": {
  "files": 2,
  "packages": 2,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Bins that legitimately live inside the package (including in-package symlinks such as bin/tool -> ../src/tool.php), packages installed via a symlinked path repository (install path itself is a symlink), and custom installers returning relative install paths must still get proxies and chmod; an over-broad fix (e.g. rejecting any is_link bin, or comparing unresolved strings) breaks them.",
  "where": "src/Composer/Installer/BinaryInstaller.php:84-90"
 },
 "O6_input_shapes": [
  "bin metadata containing '..' segments reaching install without validatePackage (fix.diff:122-126, fix.diff:208-214)",
  "in-package bin entry that is a symlink resolving outside the package (fix.diff:193-196)",
  "bin path or install path that cannot be resolved by realpath (fail closed, fix.diff:93-96)",
  "relative install path from a custom installer (realpath of both sides, fix.diff:90-91)"
 ],
 "O7_producer": {
  "kind": "serializer",
  "where": "installed.json read by the local repository and fed to ReinstallCommand / ensureBinariesPresence (src/Composer/Command/ReinstallCommand.php:110-118, src/Composer/Installer.php:350-352); the only '..' check lives in src/Composer/Package/Loader/ValidatingArrayLoader.php:548-551, called only from src/Composer/DependencyResolver/LockTransaction.php:75",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [],
 "O8b_injection_room": [
  {
   "where": "src/Composer/Installer/BinaryInstaller.php:226-229",
   "sibling": "a pre-check helper such as determineBinaryCaller/generateWindowsProxyCode reading or chmodding the bin before the containment check",
   "why_realistic": "proxy generation already opens the bin target (src/Composer/Installer/BinaryInstaller.php:158,262); a maintainer adding a 'make target executable before reading shebang' step there is plausible."
  },
  {
   "where": "src/Composer/Downloader/FileDownloader.php:348",
   "sibling": "an archive downloader (e.g. GzipDownloader single-file extraction) given the same 'make bins executable' loop",
   "why_realistic": "the single-file chmod loop is a copyable pattern for other non-archive formats that lose the exec bit."
  },
  {
   "where": "src/Composer/Installer/LibraryInstaller.php:248-251",
   "sibling": "a plugin/custom-installer route that chmods bins itself instead of via BinaryInstaller",
   "why_realistic": "PluginInstaller and third-party installers reuse LibraryInstaller and could add their own permission fixup."
  }
 ],
 "O9_family": "path traversal / symlink following to an out-of-package file (CWE-22/CWE-59) leading to a permission change (CWE-732)",
 "O9_dos": false,
 "O10_build": {
  "language": "PHP",
  "toolchain": "PHP >=5.3.2 (composer.json:25), symfony/phpunit-bridge (composer.json:43)",
  "services": [],
  "offline_after_build": true,
  "project_tests": "tests/Composer/Test/Installer/BinaryInstallerTest.php and tests/Composer/Test/Downloader/FileDownloaderTest.php per fix.diff:166,104; the pinned copy has no tests/ directory"
 },
 "O11_fix_minutes": 35,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "A",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "src/Composer/Installer/BinaryInstaller.php, src/Composer/Downloader/FileDownloader.php",
  "j_sibling_sites": "no",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Add an is_link()/realpath containment check only in BinaryInstaller::installBinaries (or extend the '..' regex in ValidatingArrayLoader) and leave the FileDownloader single-file chmod loop untouched."
 },
 "out_of_scope_notes": [
  "Root-package bins are resolved in EventDispatcher (src/Composer/EventDispatcher/EventDispatcher.php:261-266); root is trusted, not this advisory's scope.",
  "Check-then-chmod between realpath and chmod is a possible race; not pursued."
 ],
 "unverified": [
  "pinned_commit hash not given (parent_commit null) and not derivable without git.",
  "repo_mb unknown: no shell to measure; pinned copy has 317 files and no tests/ directory, so tiny_repo (<5 MB source) may hold but was not measured.",
  "regression_tests_in_pinned_commit could not be compared: pinned copy has no tests/ directory.",
  "O8 empty after grep of getBinaries/chmod/BinaryInstaller usage in src/; archive/VCS/path downloaders were not read line by line.",
  "Recall risk is an estimate; advisory publication and write-ups not checked (no network)."
 ]
}
  ```
- Published fix sites:   - src/Composer/Installer/BinaryInstaller.php:80-84 — entry point: CLI composer install/update/require/reinstall -> LibraryInstaller::install/update (src/Composer/Installer/LibraryInstaller.php:163,191) and Installer ensureBinariesPresence loop (src/Composer/Installer.php:350-352 -> src/Composer/Installer/LibraryInstaller.php:250) -> BinaryInstaller::installBinaries [installer (main implementation of bin handling)]
  - src/Composer/Installer/BinaryInstaller.php:168 — entry point: new public static API BinaryInstaller::isBinPathInsidePackage (fix.diff:88-98), shared helper [helper / public static API]
  - src/Composer/Downloader/FileDownloader.php:353-356 — entry point: CLI composer install/update/reinstall of a package whose dist is a single non-archive file -> FileDownloader::install (public DownloaderInterface API) [downloader (second implementation of bin chmod, lower layer, other package)]
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

## Environment (`tasks/composer-mm/environment/Dockerfile`)
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

## Report to the solver (`tasks/composer-mm/instruction.md`)
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

## Tests (`tasks/composer-mm/tests/`)
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
- **Wrong-fix patches** go in `build/composer-mm/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/composer-mm/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/composer-mm/manifest.json`:**
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

**Also in `build/composer-mm/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py composer-mm --only static
python3 -I builder/gate.py composer-mm --only nop
python3 -I builder/gate.py composer-mm --only oracle
python3 -I builder/gate.py composer-mm --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/composer-mm/`;
  - edit only `tasks/composer-mm/`, `build/composer-mm/` and, for pattern B, the register;
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
