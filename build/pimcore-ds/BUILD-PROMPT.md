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

Project root: `/home/mara/cwe-bench`. Task: `pimcore-ds`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: ["GHSA-9X44-4GXF-8C25", "CVE-2026-55634"]; pimcore/pimcore; injection (CWE-94 code injection into generated PHP class files; CWE-89 SQL injection into DDL identifiers)
- Pinned (vulnerable) commit: parent of a4f8c3cfee58b7d5fe4873d67782eff58dae9b9d (parent_commit not given; tree at /home/mara/screen4/hosts/33655/repo). Published fix: a4f8c3cfee58b7d5fe4873d67782eff58dae9b9d.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "33655",
 "advisory_ids": [
  "GHSA-9X44-4GXF-8C25",
  "CVE-2026-55634"
 ],
 "repo": "pimcore/pimcore",
 "pinned_commit": "parent of a4f8c3cfee58b7d5fe4873d67782eff58dae9b9d (parent_commit not given; tree at /home/mara/screen4/hosts/33655/repo)",
 "fix_commits": [
  "a4f8c3cfee58b7d5fe4873d67782eff58dae9b9d"
 ],
 "trust_decision": {
  "summary": "A DataObject class-definition field name (admin/import controlled) is trusted as a safe identifier and emitted verbatim into generated PHP class files and into ALTER TABLE DDL; decided nowhere at the pinned commit (Data::setName stores it as-is, Helper\\Dao backtick-wraps it without escaping).",
  "evidence": [
   "models/DataObject/ClassDefinition/Data.php:167-172",
   "models/DataObject/ClassDefinition/Helper/Dao.php:101",
   "models/DataObject/ClassDefinition/Helper/Dao.php:105",
   "lib/DataObject/ClassBuilder/FieldDefinitionPropertiesBuilder.php:27-31",
   "fix.diff:21-23"
  ]
 },
 "landing_point": {
  "where": "models/DataObject/ClassDefinition/Data.php:167",
  "why": "Advisory names 'DataObject Class-Definition Field Name' and RCE; Data::setName is the obvious setter for a field name and the place to add an identifier check; DDL in the Helper\\Dao trait is a second, SQL-flavoured sink in another file."
 },
 "fix_sites": [
  {
   "where": "models/DataObject/ClassDefinition/Data.php:167",
   "entry_point": "CLI pimcore:definition:import:class / :fieldcollection / :objectbrick (Service::generateLayoutTreeFromArray -> setValues -> setName), pimcore:deployment:classes-rebuild (definition file __set_state -> setValues -> setName), public API Data::setName + ClassDefinition::save; admin class editor (separate bundle)",
   "module_kind": "model setter (validation at write path)"
  },
  {
   "where": "models/DataObject/ClassDefinition/Helper/Dao.php:51",
   "entry_point": "ClassDefinition/Fieldcollection/Objectbrick/Localizedfield Dao update on definition save -> addIndexToField (add index, multi-column)",
   "module_kind": "lower-level shared DDL trait"
  },
  {
   "where": "models/DataObject/ClassDefinition/Helper/Dao.php:66",
   "entry_point": "same as above -> addIndexToField (add index, single-column)",
   "module_kind": "lower-level shared DDL trait"
  },
  {
   "where": "models/DataObject/ClassDefinition/Helper/Dao.php:75",
   "entry_point": "same as above -> addIndexToField (drop index, multi/single column, lines 75 and 82)",
   "module_kind": "lower-level shared DDL trait"
  },
  {
   "where": "models/DataObject/ClassDefinition/Helper/Dao.php:101",
   "entry_point": "definition save -> addModifyColumn (ADD COLUMN / CHANGE COLUMN at 105), called from models/DataObject/ClassDefinition/Dao.php:223-243, models/DataObject/Fieldcollection/Definition/Dao.php:72-77, models/DataObject/Objectbrick/Definition/Dao.php:101-121, models/DataObject/Localizedfield/Dao.php:857-930",
   "module_kind": "lower-level shared DDL trait"
  }
 ],
 "O1_entry_points": 5,
 "O2_out_of_scope_site": {
  "kind": "lower_level_api",
  "where": "models/DataObject/ClassDefinition/Helper/Dao.php:89-108 (shared @internal DDL trait used by four separate Dao classes; fix quotes identifiers here although the report is about PHP code generation)"
 },
 "O3_reason_to_dismiss": "Once setName validates the name, the DDL in the @internal Helper\\Dao trait 'only ever sees valid identifiers', and other DDL inputs (column types, StructuredTable keys, existing DB column names on drop, classificationstore names) belong to neighbouring features, not to 'the field name'.",
 "O4_distance": {
  "files": 2,
  "packages": 2,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "StructuredTable row/col keys are only lower-cased and become column names containing '#' (and possibly '.'), Date/Datetime/DateRange legitimately set column types like 'bigint(20)', Localizedfields must stay named 'localizedfields' and the empty name must be accepted transiently; an over-broad identifier regex on all DDL column names, or quoting that splits on '.', breaks these.",
  "where": "models/DataObject/ClassDefinition/Data/StructuredTable.php:92-130"
 },
 "O6_input_shapes": [
  "field name with PHP metacharacters (semicolon, braces, comment) - code generation",
  "field name with backtick - DDL identifier breakout",
  "leading digit, space, dash, over-long (>63) names",
  "single-column vs multi-column (array columnType, name__key) index/column names",
  "unique composite index with localized 'language' / fieldcollection 'fieldname' column",
  "ADD COLUMN vs CHANGE COLUMN (existing column name read back from DB)"
 ],
 "O7_producer": {
  "kind": "config_loader",
  "where": "models/DataObject/ClassDefinition/Helper/VarExport.php:39-45 (definition files reloaded via __set_state -> setValues at models/DataObject/ClassDefinition/Data.php:207-219)",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "Classificationstore overrides setName without calling parent, so its field name bypasses the new check and still reaches generated getter code",
   "where": "models/DataObject/ClassDefinition/Data/Classificationstore.php:557-562",
   "reason_to_dismiss": "Classificationstore is a separate key/group store feature; its name looks like a data value, not a generated identifier",
   "distance": "same package, different file (Data/Classificationstore.php, 1100+ lines; sink at :1127 and :1132)",
   "present_in_latest": "no",
   "latest_where": "latest/models/DataObject/ClassDefinition/Data/Classificationstore.php:564"
  },
  {
   "route": "Date/Datetime/DateRange setColumnType stores an arbitrary string that addModifyColumn concatenates raw as the column type into ALTER TABLE",
   "where": "models/DataObject/ClassDefinition/Data/Date.php:402-405",
   "reason_to_dismiss": "Advisory is about the field name; column type is a different property and 'not an identifier'",
   "distance": "3 type files (Date.php, Datetime.php:422, DateRange.php:356) plus Helper/Dao.php:101,105",
   "present_in_latest": "no",
   "latest_where": "latest/models/DataObject/ClassDefinition/Helper/Dao.php:98-109"
  },
  {
   "route": "removeUnusedColumns / removeIndices still backtick-wrap column names read back from the DB (second-order: a StructuredTable key with a backtick is created quoted, then dropped unquoted)",
   "where": "models/DataObject/ClassDefinition/Helper/Dao.php:120",
   "reason_to_dismiss": "Names come from information_schema, i.e. 'trusted' existing columns; drop path is cleanup, not the reported creation path",
   "distance": "same file as fix, different functions (lines 120, 125, 176)",
   "present_in_latest": "no",
   "latest_where": "latest/models/DataObject/ClassDefinition/Helper/Dao.php:144"
  },
  {
   "route": "Objectbrick Definition Dao has its own removeIndices override with unquoted DROP INDEX",
   "where": "models/DataObject/Objectbrick/Definition/Dao.php:159",
   "reason_to_dismiss": "Second implementation in another package; uses queryIgnoreError so looks best-effort/legacy",
   "distance": "different package (Objectbrick/Definition) from landing point",
   "present_in_latest": "no",
   "latest_where": "latest/models/DataObject/Objectbrick/Definition/Dao.php:164"
  }
 ],
 "O8b_injection_room": [
  {
   "where": "lib/DataObject/ClassBuilder/FieldDefinitionPropertiesBuilder.php:27-31",
   "sibling": "builder emits the fieldDefinitions array key (not getName()) as a property; a merge/defaults route that keys definitions by raw import key would bypass setName",
   "why_realistic": "the builder already uses $key rather than $def->getName(); a maintainer adding a definition-merge helper could key by user-supplied names"
  },
  {
   "where": "models/DataObject/ClassDefinition/Data/StructuredTable.php:92-130",
   "sibling": "row/col keys reach DDL column names with only strtolower",
   "why_realistic": "keys are treated as labels/data, so a maintainer would not think to validate them as identifiers"
  }
 ],
 "O9_family": "injection (CWE-94 code injection into generated PHP class files; CWE-89 SQL injection into DDL identifiers)",
 "O9_dos": false,
 "O10_build": {
  "language": "PHP",
  "toolchain": "PHP ~8.3/8.4, Composer (Symfony 6.4/7.x, doctrine/dbal ^4), Codeception/PHPUnit",
  "services": [
   "MySQL/MariaDB (for DDL and class-save tests)"
  ],
  "offline_after_build": true,
  "project_tests": "tests/Model/DataObject/ClassDefinitionTest.php (DB-backed); the fix adds a DB-free unit test tests/Unit/Models/DataObject/ClassDefinition/SetNameValidationTest.php"
 },
 "O11_fix_minutes": 60,
 "O12_red_flags": [],
 "O13_recall_risk": "low",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "models/DataObject/ClassDefinition/Data.php, models/DataObject/ClassDefinition/Helper/Dao.php",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 0,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Add an identifier regex to Data::setName (or escape in the class builder) and stop, leaving Classificationstore's override, DDL quoting, column types and the drop paths open."
 },
 "out_of_scope_notes": [
  "Layout::setName and CustomLayout::setName also store names unvalidated (models/DataObject/ClassDefinition/Layout.php:134-139); not checked whether they reach a code or DDL sink.",
  "Migrations in bundles/CoreBundle/src/Migrations build ALTER TABLE with backticks from schema-derived table names; not attacker-controlled, ignored."
 ],
 "unverified": [
  "Exact pinned commit hash not given (parent_commit null).",
  "Published regex uses '$' which also matches before a trailing newline; latest switched to '\\z' (latest/models/DataObject/ClassDefinition/Data.php:176). Whether a trailing newline is exploitable in generated code was not checked.",
  "quoteIdentifier splits on '.', so the published fix may break StructuredTable keys containing '.'; latest switches drop paths to quoteSingleIdentifier but addModifyColumn still uses quoteIdentifier (latest/models/DataObject/ClassDefinition/Helper/Dao.php:121); impact not verified.",
  "Admin class-editor HTTP route lives in a separate bundle (admin-ui-classic-bundle), not in this repo; counted as an entry point without file evidence.",
  "Repo size in MB not measured; tiny_repo/giant_repo not assessed (pimcore core is large but not expected over 1.5 GB).",
  "Whether the 4 sibling advisories (c_sibling_advisories) correspond to the O8 routes above was not checked."
 ]
}
  ```
- Published fix sites:   - models/DataObject/ClassDefinition/Data.php:167 — entry point: CLI pimcore:definition:import:class / :fieldcollection / :objectbrick (Service::generateLayoutTreeFromArray -> setValues -> setName), pimcore:deployment:classes-rebuild (definition file __set_state -> setValues -> setName), public API Data::setName + ClassDefinition::save; admin class editor (separate bundle) [model setter (validation at write path)]
  - models/DataObject/ClassDefinition/Helper/Dao.php:51 — entry point: ClassDefinition/Fieldcollection/Objectbrick/Localizedfield Dao update on definition save -> addIndexToField (add index, multi-column) [lower-level shared DDL trait]
  - models/DataObject/ClassDefinition/Helper/Dao.php:66 — entry point: same as above -> addIndexToField (add index, single-column) [lower-level shared DDL trait]
  - models/DataObject/ClassDefinition/Helper/Dao.php:75 — entry point: same as above -> addIndexToField (drop index, multi/single column, lines 75 and 82) [lower-level shared DDL trait]
  - models/DataObject/ClassDefinition/Helper/Dao.php:101 — entry point: definition save -> addModifyColumn (ADD COLUMN / CHANGE COLUMN at 105), called from models/DataObject/ClassDefinition/Dao.php:223-243, models/DataObject/Fieldcollection/Definition/Dao.php:72-77, models/DataObject/Objectbrick/Definition/Dao.php:101-121, models/DataObject/Localizedfield/Dao.php:857-930 [lower-level shared DDL trait]
- Uncovered routes to confirm (pattern B):   - models/DataObject/ClassDefinition/Data/Classificationstore.php:557-562 — Classificationstore overrides setName without calling parent, so its field name bypasses the new check and still reaches generated getter code (reason to dismiss: Classificationstore is a separate key/group store feature; its name looks like a data value, not a generated identifier; still in latest: no)
  - models/DataObject/ClassDefinition/Data/Date.php:402-405 — Date/Datetime/DateRange setColumnType stores an arbitrary string that addModifyColumn concatenates raw as the column type into ALTER TABLE (reason to dismiss: Advisory is about the field name; column type is a different property and 'not an identifier'; still in latest: no)
  - models/DataObject/ClassDefinition/Helper/Dao.php:120 — removeUnusedColumns / removeIndices still backtick-wrap column names read back from the DB (second-order: a StructuredTable key with a backtick is created quoted, then dropped unquoted) (reason to dismiss: Names come from information_schema, i.e. 'trusted' existing columns; drop path is cleanup, not the reported creation path; still in latest: no)
  - models/DataObject/Objectbrick/Definition/Dao.php:159 — Objectbrick Definition Dao has its own removeIndices override with unquoted DROP INDEX (reason to dismiss: Second implementation in another package; uses queryIgnoreError so looks best-effort/legacy; still in latest: no)
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

## Environment (`tasks/pimcore-ds/environment/Dockerfile`)
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

## Report to the solver (`tasks/pimcore-ds/instruction.md`)
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

## Tests (`tasks/pimcore-ds/tests/`)
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
- **Wrong-fix patches** go in `build/pimcore-ds/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/pimcore-ds/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/pimcore-ds/manifest.json`:**
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

**Also in `build/pimcore-ds/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py pimcore-ds --only static
python3 -I builder/gate.py pimcore-ds --only nop
python3 -I builder/gate.py pimcore-ds --only oracle
python3 -I builder/gate.py pimcore-ds --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/pimcore-ds/`;
  - edit only `tasks/pimcore-ds/`, `build/pimcore-ds/` and, for pattern B, the register;
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
