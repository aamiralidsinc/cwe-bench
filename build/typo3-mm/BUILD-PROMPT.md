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

Project root: `/home/mara/cwe-bench`. Task: `typo3-mm`. Pattern: `A`. Track: `injected`.

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
- Advisory: ["GHSA-JH32-V29G-68PQ", "CVE-2026-49741"]; typo3/typo3; missing authorization / validation bypass on persisted configuration (CWE-862), leading to an SQL identifier injection sink in SaveToDatabaseFinisher (CWE-89)
- Pinned (vulnerable) commit: unknown. Published fix: c90493c13b633f328cf2c066182c90a1655ff0fc.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "35083",
 "advisory_ids": [
  "GHSA-JH32-V29G-68PQ",
  "CVE-2026-49741"
 ],
 "repo": "typo3/typo3",
 "pinned_commit": "unknown",
 "fix_commits": [
  "c90493c13b633f328cf2c066182c90a1655ff0fc"
 ],
 "trust_decision": {
  "summary": "Whether a create/update/delete of a form_definition row came through the form persistence path (FormDefinitionRepository via DatabaseStorageAdapter, after editor validation and permission checks) or directly through core DataHandler. Before the fix nothing decides this: any backend user with tables_modify on form_definition can write arbitrary configuration JSON (e.g. SaveToDatabaseFinisher table/column/whereClause options) through DataHandler. The fix decides it in a DataHandler hook against a per-invocation HMAC grant issued by the repository.",
  "evidence": [
   "typo3/sysext/form/Classes/Domain/Repository/FormDefinitionRepository.php:180-204",
   "typo3/sysext/form/Classes/Domain/Repository/FormDefinitionRepository.php:236-249",
   "typo3/sysext/form/Classes/Domain/Repository/FormDefinitionRepository.php:259-281",
   "typo3/sysext/form/Classes/Mvc/Property/TypeConverter/FormDefinitionArrayConverter.php:77-88",
   "typo3/sysext/core/Classes/DataHandling/DataHandler.php:708-709",
   "typo3/sysext/core/Classes/DataHandling/DataHandler.php:3233-3241",
   "typo3/sysext/form/Classes/Domain/Finishers/SaveToDatabaseFinisher.php:324-338",
   "fix.diff:174-206",
   "fix.diff:215-243",
   "fix.diff:664-666"
  ]
 },
 "landing_point": {
  "where": "typo3/sysext/form/Classes/Mvc/Property/TypeConverter/FormDefinitionArrayConverter.php:88",
  "why": "The advisory names privilege escalation plus SQL injection in the Form Framework. An engineer would look first at the editor's validation of form-definition properties (or at SaveToDatabaseFinisher:324-338, where the configured table, columns and whereClause reach the DB). The actual gap is that the core DataHandler writes form_definition rows directly and skips that validation."
 },
 "fix_sites": [
  {
   "where": "typo3/sysext/form/Classes/Domain/Repository/FormDefinitionRepository.php:180",
   "entry_point": "FormPersistenceManager::save -> DatabaseStorageAdapter::write (new) from the form editor saveForm / form manager create+duplicate routes and the form:definition:transfer CLI",
   "module_kind": "repository (grant issuer, create)"
  },
  {
   "where": "typo3/sysext/form/Classes/Domain/Repository/FormDefinitionRepository.php:236",
   "entry_point": "FormPersistenceManager::delete -> DatabaseStorageAdapter::delete from the form manager delete action / form:definition:transfer --move",
   "module_kind": "repository (grant issuer, delete)"
  },
  {
   "where": "typo3/sysext/form/Classes/Domain/Repository/FormDefinitionRepository.php:259",
   "entry_point": "DatabaseStorageAdapter::write (existing uid) from the form editor saveForm action",
   "module_kind": "repository (grant issuer, update)"
  },
  {
   "where": "fix.diff:174",
   "entry_point": "DataHandler process_datamap (backend /record/commit and the list module, impexp import, history rollback, copy via inner datamap)",
   "module_kind": "new DataHandler hook in form ext (create/update guard)"
  },
  {
   "where": "fix.diff:215",
   "entry_point": "DataHandler process_cmdmap 'delete' (backend /record/commit, list module, clipboard)",
   "module_kind": "new DataHandler hook in form ext (delete guard)"
  },
  {
   "where": "fix.diff:287",
   "entry_point": "internal (FormDefinitionPersistenceGuard + Command enum)",
   "module_kind": "new guard service"
  },
  {
   "where": "fix.diff:664-666",
   "entry_point": "global hook registration that applies to every DataHandler caller",
   "module_kind": "extension bootstrap / config"
  }
 ],
 "O1_entry_points": 3,
 "O2_out_of_scope_site": {
  "kind": "lower_level_api",
  "where": "typo3/sysext/core/Classes/DataHandling/DataHandler.php:708-709 and typo3/sysext/core/Classes/DataHandling/DataHandler.php:3233-3241 (core DataHandler hook points). The fix closes them from the form extension: fix.diff:664-666."
 },
 "O3_reason_to_dismiss": "form_definition is already 'protected': its TCA fields are readOnly, the New Record wizard denies the table, and the list module removes edit/delete actions. A solver can argue that direct DataHandler/record-commit writes are a generic core feature gated by tables_modify, so they are out of scope for a Form Framework fix, and harden only the editor/finisher.",
 "O4_distance": {
  "files": 4,
  "packages": 2,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "FormDefinitionRepository::add/update/remove persist through DataHandler themselves. The form editor save, form manager create/duplicate/delete and the CLI transfer must keep working. A fix that simply denies all DataHandler writes to form_definition, or that sets TCA to forbid modification, breaks them.",
  "where": "typo3/sysext/form/Classes/Domain/Repository/FormDefinitionRepository.php:183-195"
 },
 "O6_input_shapes": [
  "datamap create with a NEW-prefixed id (full field set)",
  "datamap update with an integer uid and a partial field set (e.g. label only)",
  "datamap update with a changed configuration JSON (fields HMAC-bound, so tampering with any one field is rejected)",
  "cmdmap delete with an integer uid"
 ],
 "O7_producer": {
  "kind": "handler",
  "where": "typo3/sysext/form/Classes/Mvc/Property/TypeConverter/FormDefinitionArrayConverter.php:77-113 validates and sanitises the definition, but only on the editor save route; the stored JSON is consumed at typo3/sysext/form/Classes/Storage/DatabaseStorageAdapter.php:105-124 without revalidation",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "DataHandler cmdmap 'undelete' (recycler / history restore) re-activates a soft-deleted form_definition row without a grant; the hook returns early for any command other than 'delete'",
   "where": "typo3/sysext/core/Classes/DataHandling/DataHandler.php:3303-3305",
   "reason_to_dismiss": "Restoring a row writes no new configuration; the content was persisted earlier, so it is a 'neighbouring feature'.",
   "distance": "core DataHandler (other package) vs fix hook in form ext",
   "present_in_latest": "yes",
   "latest_where": "latest/typo3/sysext/form/Classes/Hooks/FormDefinitionDataHandlerHook.php:106"
  },
  {
   "route": "DataHandler cmdmap 'move' changes a form_definition row's pid without a grant; DatabasePermissionChecker decides read/write access by pid",
   "where": "typo3/sysext/core/Classes/DataHandling/DataHandler.php:3245-3246",
   "reason_to_dismiss": "Move changes no configuration; the table is rootLevel and move is a generic core command.",
   "distance": "core DataHandler (other package) vs typo3/sysext/form/Classes/Storage/Permission/DatabasePermissionChecker.php:111-131",
   "present_in_latest": "yes",
   "latest_where": "latest/typo3/sysext/form/Classes/Hooks/FormDefinitionDataHandlerHook.php:106"
  },
  {
   "route": "FormDefinitionRepository::addRaw inserts rows with a raw connection insert, bypassing DataHandler and the hook (used by the upgrade wizard)",
   "where": "typo3/sysext/form/Classes/Domain/Repository/FormDefinitionRepository.php:214-228",
   "reason_to_dismiss": "Install-tool/admin-only legacy migration path; the source is already-stored file definitions.",
   "distance": "same file as the fix sites",
   "present_in_latest": "unknown",
   "latest_where": ""
  }
 ],
 "O8b_injection_room": [
  {
   "where": "typo3/sysext/form/Classes/Domain/Repository/FormDefinitionRepository.php:214",
   "sibling": "a second repository write method (e.g. a 'duplicate' or 'restore' helper) that issues a DataHandler copy/undelete for form_definition",
   "why_realistic": "The repository already has two write styles (DataHandler and raw insert); a maintainer adding duplicate-on-copy via DataHandler 'copy' would be natural."
  },
  {
   "where": "typo3/sysext/form/Classes/Service/FormTransferService.php:132",
   "sibling": "a transfer/import path that writes the target row via DataHandler or a raw connection instead of the storage adapter",
   "why_realistic": "The service already does raw connection updates on tt_content (FormTransferService.php:271); a bulk-import optimisation would plausibly do the same on form_definition."
  },
  {
   "where": "typo3/sysext/form/Classes/Hooks/ImportExportHook.php:26",
   "sibling": "an impexp hook that pre-grants form_definition imports (mirroring the FAL grant it already issues)",
   "why_realistic": "The same hook already whitelists FAL form-file imports through FilePersistenceSlot::allowInvocation."
  }
 ],
 "O9_family": "missing authorization / validation bypass on persisted configuration (CWE-862), leading to an SQL identifier injection sink in SaveToDatabaseFinisher (CWE-89)",
 "O9_dos": false,
 "O10_build": {
  "language": "PHP 8.2+",
  "toolchain": "composer install; phpunit with typo3/testing-framework (functional tests)",
  "services": [
   "SQLite (functional tests can run on sqlite) or MySQL/MariaDB/PostgreSQL"
  ],
  "offline_after_build": true,
  "project_tests": "typo3/sysext/form/Tests/Functional and Tests/Unit; the fix adds Tests/Functional/Storage/FormDefinitionDataHandlerHookTest.php and FormDefinitionRepositoryTest.php"
 },
 "O11_fix_minutes": 60,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "A",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "typo3/sysext/form/Classes/Domain/Repository/FormDefinitionRepository.php, typo3/sysext/form/Classes/Hooks/FormDefinitionDataHandlerHook.php (new), typo3/sysext/form/Classes/Storage/Security/FormDefinitionPersistenceGuard.php (new), typo3/sysext/form/Classes/Storage/Security/FormDefinitionPersistenceCommand.php (new), typo3/sysext/form/ext_localconf.php",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Validate or restrict SaveToDatabaseFinisher options (table/column/whereClause) or editor input, leaving direct DataHandler writes to form_definition open; or deny all DataHandler writes, which breaks the repository."
 },
 "out_of_scope_notes": [
  "Existing UI-only defences (TCA readOnly at typo3/sysext/form/Configuration/TCA/form_definition.php:34,44,52; deniedNewTables at typo3/sysext/form/Configuration/page.tsconfig:4; removed list actions at typo3/sysext/form/Classes/EventListener/ModifyFormDefinitionRecordActionsEventListener.php:75,90-91) did not stop DataHandler writes; that is why j_defence_ineffective is 1.",
  "Frontend read skips permission checks by design (typo3/sysext/form/Classes/Storage/DatabaseStorageAdapter.php:98-103); not pursued.",
  "Deleting a parent page may cascade-delete form_definition rows on pid>0 through deleteRecord rather than the cmdmap hook; not verified."
 ],
 "unverified": [
  "pinned_commit hash: repo copy has no git metadata and parent_commit is null.",
  "Repo size in MB not measured (about 26.7k files in the tree); tiny/giant flags not asserted.",
  "Test fixtures Fixtures/be_users.csv and form_definition.csv used by the new tests are not in fix.diff; their presence at the fix commit is unknown.",
  "Whether DataHandler's 'move' is actually permitted for this rootLevel=1 table with ignoreRootLevelRestriction was not traced end to end.",
  "addRaw presence in latest/ not checked.",
  "Advisory text itself was not available; trust decision derived from the fix diff and code comments (fix.diff:145-150, 310-317)."
 ]
}
  ```
- Published fix sites:   - typo3/sysext/form/Classes/Domain/Repository/FormDefinitionRepository.php:180 — entry point: FormPersistenceManager::save -> DatabaseStorageAdapter::write (new) from the form editor saveForm / form manager create+duplicate routes and the form:definition:transfer CLI [repository (grant issuer, create)]
  - typo3/sysext/form/Classes/Domain/Repository/FormDefinitionRepository.php:236 — entry point: FormPersistenceManager::delete -> DatabaseStorageAdapter::delete from the form manager delete action / form:definition:transfer --move [repository (grant issuer, delete)]
  - typo3/sysext/form/Classes/Domain/Repository/FormDefinitionRepository.php:259 — entry point: DatabaseStorageAdapter::write (existing uid) from the form editor saveForm action [repository (grant issuer, update)]
  - fix.diff:174 — entry point: DataHandler process_datamap (backend /record/commit and the list module, impexp import, history rollback, copy via inner datamap) [new DataHandler hook in form ext (create/update guard)]
  - fix.diff:215 — entry point: DataHandler process_cmdmap 'delete' (backend /record/commit, list module, clipboard) [new DataHandler hook in form ext (delete guard)]
  - fix.diff:287 — entry point: internal (FormDefinitionPersistenceGuard + Command enum) [new guard service]
  - fix.diff:664-666 — entry point: global hook registration that applies to every DataHandler caller [extension bootstrap / config]
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

## Environment (`tasks/typo3-mm/environment/Dockerfile`)
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

## Report to the solver (`tasks/typo3-mm/instruction.md`)
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

## Tests (`tasks/typo3-mm/tests/`)
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
- **Wrong-fix patches** go in `build/typo3-mm/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/typo3-mm/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/typo3-mm/manifest.json`:**
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

**Also in `build/typo3-mm/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py typo3-mm --only static
python3 -I builder/gate.py typo3-mm --only nop
python3 -I builder/gate.py typo3-mm --only oracle
python3 -I builder/gate.py typo3-mm --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/typo3-mm/`;
  - edit only `tasks/typo3-mm/`, `build/typo3-mm/` and, for pattern B, the register;
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
