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

Project root: `/home/mara/cwe-bench`. Task: `izpack-zip-path-inj`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: GHSA-F63G-88CJ-HJF9 / CVE-2026-54550 - izpack/izpack - path traversal / arbitrary file write (CWE-22, zip-slip-like archive entry extraction). Whether a pack-entry target path read from the compiled installer's packs.info (after ${VAR} translation) may contain '..' segments before the install
- Pinned (vulnerable) commit: e431c892d9114bd10ab75dda50a4086463a75b6e. Published fix: 4233ba38d0f1825f9cf3e0204e5261a5498e29d8.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "25438",
 "advisory_ids": [
  "GHSA-F63G-88CJ-HJF9",
  "CVE-2026-54550"
 ],
 "repo": "izpack/izpack",
 "pinned_commit": "parent of 4233ba38d0f1825f9cf3e0204e5261a5498e29d8 (parent_commit not given in candidate; tree at /home/mara/screen3/hosts/25438/repo)",
 "fix_commits": [
  "4233ba38d0f1825f9cf3e0204e5261a5498e29d8",
  "8b7c6792c4fe85e3b1759c106aae39b904848466"
 ],
 "trust_decision": {
  "summary": "Whether a pack-entry target path read from the compiled installer's packs.info (after ${VAR} translation) may contain '..' segments before the installer creates directories and writes the file; decided nowhere at the pinned commit \u2014 the fix adds it at install time in UnpackerBase.unpack(PackFile,...) and at compile time in the PackFile constructor.",
  "evidence": [
   "izpack-installer/src/main/java/com/izforge/izpack/installer/unpacker/UnpackerBase.java:620-631",
   "izpack-installer/src/main/java/com/izforge/izpack/installer/unpacker/UnpackerBase.java:311-313",
   "izpack-api/src/main/java/com/izforge/izpack/api/data/PackFile.java:164-186",
   "fix.diff:552",
   "fix.diff:27"
  ]
 },
 "landing_point": {
  "where": "izpack-installer/src/main/java/com/izforge/izpack/installer/unpacker/UnpackerBase.java:617-631",
  "why": "The advisory names UnpackerBase and 'malicious pack entries'; unpack(PackFile,...) translates getTargetPath() and immediately builds the File, creates directories and extracts."
 },
 "fix_sites": [
  {
   "where": "izpack-installer/src/main/java/com/izforge/izpack/installer/unpacker/UnpackerBase.java:623",
   "entry_point": "Installer run (GUI/console/auto) -> IUnpacker.run() -> UnpackerBase.unpack() -> unpack(PackFile,...); shared by Unpacker and MultiVolumeUnpacker",
   "module_kind": "installer runtime, main implementation (fix.diff:552, new private validateTargetPath fix.diff:593-643)"
  },
  {
   "where": "izpack-api/src/main/java/com/izforge/izpack/api/data/PackFile.java:164-177",
   "entry_point": "Compiler CLI/Ant/Maven -> CompilerConfig -> PackInfo.addFile (izpack-api/src/main/java/com/izforge/izpack/api/data/PackInfo.java:158) -> PackFile constructor; also public API new PackFile(...)",
   "module_kind": "lower-level public data API in another module (izpack-api), compile-time (fix.diff:27, fix.diff:35-60)"
  },
  {
   "where": "izpack-tools/src/main/java/com/izforge/izpack/util/FileUtil.java:244-252",
   "entry_point": "FileUtil.getRelativeFileName, called from PackFile constructors (izpack-api/src/main/java/com/izforge/izpack/api/data/PackFile.java:149)",
   "module_kind": "utility in a third module; string-prefix base-dir check replaced by Path.startsWith/relativize (fix.diff:1537-1548)"
  },
  {
   "where": "izpack-installer/src/main/java/com/izforge/izpack/util/TemporaryDirectory.java:83-85",
   "entry_point": "Installer temporary directory creation",
   "module_kind": "unrelated hardening (temp dir creation race), not this protection (fix.diff:1402-1405)"
  }
 ],
 "O1_entry_points": 3,
 "O2_out_of_scope_site": {
  "kind": "lower_level_api",
  "where": "izpack-api/src/main/java/com/izforge/izpack/api/data/PackFile.java:164-177 (compile-time constructor in the izpack-api module; the advisory names only the installer's UnpackerBase)"
 },
 "O3_reason_to_dismiss": "The installer-side check already blocks traversal at extraction time, and the compiler runs on the installer author's own trusted descriptor, so a solver can argue that validating PackFile at compile time (and the override-rename / parsable paths) is redundant or 'not a pack entry'.",
 "O4_distance": {
  "files": 3,
  "packages": 3,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Pack entries may legitimately target absolute paths outside INSTALL_PATH (e.g. /etc/myapp/config.properties); the fix only logs an AUDIT warning for these and the fix's test requires them to keep installing. A 'must stay under INSTALL_PATH' fix breaks this; regular nested targets like subdir/file.txt must also keep working.",
  "where": "fix.diff:626-642; fix.diff:1440-1444; fix.diff:92-97"
 },
 "O6_input_shapes": [
  "'..' segment with forward slashes (subdir/../escape) \u2014 fix.diff:100-105",
  "'..' segment with backslashes (subdir\\..\\escape) \u2014 fix.diff:50, fix.diff:108-113",
  "traversal appearing only after ${VAR} translation (check runs on the translated path) \u2014 fix.diff:551-552",
  "Windows-only: trailing dot/space filenames and reserved device names (CON, NUL, COM1..9, LPT1..9) \u2014 fix.diff:605-623",
  "absolute target outside install root: allowed, logged only \u2014 fix.diff:634-642"
 ],
 "O7_producer": {
  "kind": "serializer",
  "where": "packs.info is written by Java serialization at izpack-compiler/src/main/java/com/izforge/izpack/compiler/packager/impl/Packager.java:262 and read back at izpack-installer/src/main/java/com/izforge/izpack/installer/unpacker/UnpackerBase.java:311-313; deserialization does not run the PackFile constructor, so the compile-time check (fix.diff:27) never sees a crafted packs.info",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "Override-rename: overrideRenameTo from packs.info is glob-mapped and joined to the target's parent, then the existing file is deleted/renamed there, with no traversal check.",
   "where": "izpack-installer/src/main/java/com/izforge/izpack/installer/unpacker/UnpackerBase.java:1322-1345",
   "reason_to_dismiss": "Only runs when the target file already exists and override is set; it 'renames a backup', not a pack entry write.",
   "distance": "same file as landing point, separate method reached from unpack() at line 656",
   "present_in_latest": "yes",
   "latest_where": "latest/izpack-installer/src/main/java/com/izforge/izpack/installer/unpacker/UnpackerBase.java:1230"
  },
  {
   "route": "Parsable files: ParsableFile path from packs.info is variable-translated and later rewritten in place by ScriptParser (temp file + rename), with no traversal check.",
   "where": "izpack-installer/src/main/java/com/izforge/izpack/installer/unpacker/UnpackerBase.java:1361-1374",
   "reason_to_dismiss": "Only rewrites files that already exist; parsables are a neighbouring feature, not pack entries; compile-time targetfile (izpack-compiler/src/main/java/com/izforge/izpack/compiler/CompilerConfig.java:1435-1442) is also unchecked.",
   "distance": "same file; write happens in izpack-installer/src/main/java/com/izforge/izpack/installer/unpacker/ScriptParser.java:80-121",
   "present_in_latest": "yes",
   "latest_where": "latest/izpack-installer/src/main/java/com/izforge/izpack/installer/unpacker/UnpackerBase.java:1257"
  }
 ],
 "O8b_injection_room": [
  {
   "where": "izpack-installer/src/main/java/com/izforge/izpack/installer/unpacker/LooseFileUnpacker.java:85-108",
   "sibling": "Loose-pack copy path that resolves its own destination from the PackFile instead of using the passed target.",
   "why_realistic": "LooseFileUnpacker already rebuilds the PackFile from targetPath at line 104; a maintainer adding loose-file relocation could plausibly recompute the destination there."
  },
  {
   "where": "izpack-installer/src/main/java/com/izforge/izpack/installer/multiunpacker/MultiVolumeUnpacker.java:62",
   "sibling": "MultiVolumeUnpacker override of unpack(PackFile,...) that duplicates the base logic without the check.",
   "why_realistic": "The subclass already overrides createFileUnpacker/skip/preUnpack; a second implementation of the per-file step is a natural addition."
  }
 ],
 "O9_family": "path traversal / arbitrary file write (CWE-22, zip-slip-like archive entry extraction)",
 "O9_dos": false,
 "O10_build": {
  "language": "Java (release 8)",
  "toolchain": "Maven multi-module (pom.xml:470-472)",
  "services": [],
  "offline_after_build": true,
  "project_tests": "JUnit in izpack-installer/src/test/java/com/izforge/izpack/installer/unpacker/ (DefaultFileUnpackerTest, LooseFileUnpackerTest, ScriptParserTest...); fix adds PackFileTest and UnpackerBaseTest (fix.diff:78, fix.diff:1413)"
 },
 "O11_fix_minutes": 40,
 "O12_red_flags": [],
 "O13_recall_risk": "low",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "izpack-installer/.../unpacker/UnpackerBase.java; izpack-api/.../data/PackFile.java; izpack-tools/.../util/FileUtil.java; izpack-installer/.../util/TemporaryDirectory.java (AbstractInstallDataProvider.java: imports only)",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 0,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Add a canonical 'target must start with INSTALL_PATH' check in UnpackerBase.unpack(PackFile,...) only \u2014 breaks legitimate absolute targets and leaves the PackFile API, override-rename and parsable routes open."
 },
 "out_of_scope_notes": [
  "TemporaryDirectory createTempFile/delete/mkdir race (CWE-377) fixed in the same commit, separate weakness.",
  "readExecutableFiles runs paths from packs.info; a code-execution concern, not this protection.",
  "performUpdateChecks deletes files matched by include patterns from packs.info under the install dir; not examined.",
  "LooseFileUnpacker reads relativeSourcePath relative to looseFilesDir (read-side path handling); not examined.",
  "LooseFileUnpacker.java:104 passes getAdditionals() into the 8-arg constructor whose last parameter is pack200Properties; looks like a functional bug, not pursued."
 ],
 "unverified": [
  "repo_mb not measured (no shell); the tree has over 1700 files, so tiny_repo is unlikely but not confirmed.",
  "Exact pinned commit hash not given in the candidate; assumed to be the parent of the first fix commit.",
  "Whether GlobPatternMapper output can contain path separators for overrideRenameTo values was not run, only read.",
  "Recall risk is based on the publication date (2026-08-26) only; write-ups not checked."
 ]
}
  ```
- Published fix sites:   - izpack-installer/src/main/java/com/izforge/izpack/installer/unpacker/UnpackerBase.java:623 — entry point: Installer run (GUI/console/auto) -> IUnpacker.run() -> UnpackerBase.unpack() -> unpack(PackFile,...); shared by Unpacker and MultiVolumeUnpacker [installer runtime, main implementation (fix.diff:552, new private validateTargetPath fix.diff:593-643)]
  - izpack-api/src/main/java/com/izforge/izpack/api/data/PackFile.java:164-177 — entry point: Compiler CLI/Ant/Maven -> CompilerConfig -> PackInfo.addFile (izpack-api/src/main/java/com/izforge/izpack/api/data/PackInfo.java:158) -> PackFile constructor; also public API new PackFile(...) [lower-level public data API in another module (izpack-api), compile-time (fix.diff:27, fix.diff:35-60)]
  - izpack-tools/src/main/java/com/izforge/izpack/util/FileUtil.java:244-252 — entry point: FileUtil.getRelativeFileName, called from PackFile constructors (izpack-api/src/main/java/com/izforge/izpack/api/data/PackFile.java:149) [utility in a third module; string-prefix base-dir check replaced by Path.startsWith/relativize (fix.diff:1537-1548)]
  - izpack-installer/src/main/java/com/izforge/izpack/util/TemporaryDirectory.java:83-85 — entry point: Installer temporary directory creation [unrelated hardening (temp dir creation race), not this protection (fix.diff:1402-1405)]
- Uncovered routes to confirm (pattern B):   - izpack-installer/src/main/java/com/izforge/izpack/installer/unpacker/UnpackerBase.java:1322-1345 — Override-rename: overrideRenameTo from packs.info is glob-mapped and joined to the target's parent, then the existing file is deleted/renamed there, with no traversal check. (reason to dismiss: Only runs when the target file already exists and override is set; it 'renames a backup', not a pack entry write.; still in latest: yes)
  - izpack-installer/src/main/java/com/izforge/izpack/installer/unpacker/UnpackerBase.java:1361-1374 — Parsable files: ParsableFile path from packs.info is variable-translated and later rewritten in place by ScriptParser (temp file + rename), with no traversal check. (reason to dismiss: Only rewrites files that already exist; parsables are a neighbouring feature, not pack entries; compile-time targetfile (izpack-compiler/src/main/java/com/izforge/izpack/compiler/CompilerConfig.java:1435-1442) is also unchecked.; still in latest: yes)
- Design plan from the lead: TRACK = INJECTED (breaker recipe: only injected-sibling tasks at a recurring check have beaten both models; the mined batch was all solved).

RECURRING CHECK / PROTECTED SINK: Whether a pack-entry target path read from the compiled installer's packs.info (after ${VAR} translation) may contain '..' segments before the installer creates directories and writes the file; decided nowhere at the pinned commit — the fix adds it at install 

STEP 1 - confirm the published fix's sites and these uncovered-route leads with tests on the pinned copy: izpack-installer/src/main/java/com/izforge/izpack/installer/unpacker/UnpackerBase.java:1322-1345 (Override-rename: overrideRenameTo from packs.info is gl; dismiss: Only runs when the target file already exists); izpack-installer/src/main/java/com/izforge/izpack/installer/unpacker/UnpackerBase.java:1361-1374 (Parsable files: ParsableFile path from packs.info is va; dismiss: Only rewrites files that already exist; parsa).
STEP 2 - at these recurring sites, add 2 to 4 realistic sibling GAPS in the same protection that a maintainer could plausibly have left unguarded (verify each by reading the code): izpack-installer/src/main/java/com/izforge/izpack/installer/unpacker/LooseFileUnpacker.java:85-108 -> Loose-pack copy path that resolves its own destination from the PackFi (realistic: LooseFileUnpacker already rebuilds the PackFile from targetP); izpack-installer/src/main/java/com/izforge/izpack/installer/multiunpacker/MultiVolumeUnpacker.java:62 -> MultiVolumeUnpacker override of unpack(PackFile,...) that duplicates t (realistic: The subclass already overrides createFileUnpacker/skip/preUn). Each added gap MUST be code a maintainer could plausibly have written (no tell-tale names/comments/shortcuts; match surrounding style), reachable through the real public entry point, covered by a stated invariant, left where the published upstream fix never touches, and carry a DIFFERENT plausible reason a solver would skip it (legacy/compat path, internal/trusted caller, unsupported combination, neighbouring feature). Distinct reasons-to-skip are the lever.
STEP 3 - hidden security tests require closing the base flaw, every uncovered route AND every added gap through the real entry point. The oracle closes all; a fix that closes only the obvious sites must score < 1.0 (add a security_fail check patch for that partial fix).
STEP 4 - COUPLED MUST-KEEP-WORKING (one functional test per trap): Pack entries may legitimately target absolute paths outside INSTALL_PATH (e.g. /etc/myapp/config.properties); the fix only logs an AUDIT warning for these and the fix's test requires them to keep inst (near fix.diff:626-642; fix.diff:1440-1444; fix.diff:92-); keep every legitimate use working.

Aim for >=3 levers with DIFFERENT reasons a solver would skip them. Every gap must be findable by a blind engineer from instruction.md + code; if not, drop it. instruction.md stays product-level: system, one impact with one user trigger, invariants covering EVERY route/gap (a natural list, no count); never name files/functions/fields/CVEs (all in manifest.leak_terms). Register each added gap and route in build/audit/uncovered-routes.tsv.
- Host notes: Language: Java (release 8). Offline after build, no external services. Added gaps go in OUR copy only, register them. Recurring check (3 entry points) + screener injection room. Build+test via real entry points; project's own area tests pass at the pinned commit. Pin at the vulnerable commit; keep unrelated earlier fixes.

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

## Environment (`tasks/izpack-zip-path-inj/environment/Dockerfile`)
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

## Report to the solver (`tasks/izpack-zip-path-inj/instruction.md`)
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

## Tests (`tasks/izpack-zip-path-inj/tests/`)
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
- **Wrong-fix patches** go in `build/izpack-zip-path-inj/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/izpack-zip-path-inj/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/izpack-zip-path-inj/manifest.json`:**
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

**Also in `build/izpack-zip-path-inj/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py izpack-zip-path-inj --only static
python3 -I builder/gate.py izpack-zip-path-inj --only nop
python3 -I builder/gate.py izpack-zip-path-inj --only oracle
python3 -I builder/gate.py izpack-zip-path-inj --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/izpack-zip-path-inj/`;
  - edit only `tasks/izpack-zip-path-inj/`, `build/izpack-zip-path-inj/` and, for pattern B, the register;
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
