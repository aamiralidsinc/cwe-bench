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

Project root: `/home/mara/cwe-bench`. Task: `airflow-mm`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: ["GHSA-C56V-8W4G-3MFM", "BIT-AIRFLOW-2026-65017", "CVE-2026-65017", "PYSEC-2026-3993"]; apache/airflow; CWE-200 sensitive information exposure via incomplete redaction (sensitivity check misses alternate name spellings)
- Pinned (vulnerable) commit: unknown (parent of 62d37d52bf4df38b6acd3a1e73203508878f36c4; parent_commit not given). Published fix: 62d37d52bf4df38b6acd3a1e73203508878f36c4, d41ac7b6d213682db3ef4d21bbb33e013dde4af4.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "2694",
 "advisory_ids": [
  "GHSA-C56V-8W4G-3MFM",
  "BIT-AIRFLOW-2026-65017",
  "CVE-2026-65017",
  "PYSEC-2026-3993"
 ],
 "repo": "apache/airflow",
 "pinned_commit": "unknown (parent of 62d37d52bf4df38b6acd3a1e73203508878f36c4; parent_commit not given)",
 "fix_commits": [
  "62d37d52bf4df38b6acd3a1e73203508878f36c4",
  "d41ac7b6d213682db3ef4d21bbb33e013dde4af4"
 ],
 "trust_decision": {
  "summary": "Whether a config value is shown or replaced with '< hidden >' is decided by a literal (section, key) lookup in AirflowConfigParser.sensitive_config_values, which holds only base section names, so team-scoped spellings ([team=section] file sections, AIRFLOW__TEAM___SECTION__KEY env vars, team _cmd/_secret entries) are not recognised as sensitive.",
  "evidence": [
   "shared/configuration/src/airflow_shared/configuration/parser.py:546-563",
   "airflow-core/src/airflow/api_fastapi/core_api/routes/public/config.py:155-161",
   "shared/configuration/src/airflow_shared/configuration/parser.py:790-794",
   "shared/configuration/src/airflow_shared/configuration/parser.py:1792-1803",
   "shared/configuration/src/airflow_shared/configuration/parser.py:2035-2038"
  ]
 },
 "landing_point": {
  "where": "airflow-core/src/airflow/api_fastapi/core_api/routes/public/config.py:156",
  "why": "The summary names the 'Config API'; the single-option endpoint's literal sensitive_config_values check is the visible masking decision in the API layer."
 },
 "fix_sites": [
  {
   "where": "airflow-core/src/airflow/api_fastapi/core_api/routes/public/config.py:156",
   "entry_point": "GET /config/section/{section}/option/{option}",
   "module_kind": "HTTP route handler (airflow-core API)"
  },
  {
   "where": "shared/configuration/src/airflow_shared/configuration/parser.py:790-794",
   "entry_point": "AirflowConfigParser.as_dict(display_sensitive=False) via GET /config (env-var collection in _include_envs)",
   "module_kind": "shared lower-level config parser library (separate shared/configuration distribution)"
  },
  {
   "where": "shared/configuration/src/airflow_shared/configuration/parser.py:1792-1803",
   "entry_point": "AirflowConfigParser.as_dict(display_sensitive=False) via GET /config",
   "module_kind": "shared lower-level config parser library"
  },
  {
   "where": "shared/configuration/src/airflow_shared/configuration/parser.py:2035-2038",
   "entry_point": "CLI `airflow config list` (config_command.show_config -> conf.write(hide_sensitive=...))",
   "module_kind": "shared lower-level config parser library (write/render path)"
  }
 ],
 "O1_entry_points": 4,
 "O2_out_of_scope_site": {
  "kind": "lower_level_api",
  "where": "shared/configuration/src/airflow_shared/configuration/parser.py:2035-2038 (write(), reached by `airflow config list` at airflow-core/src/airflow/cli/commands/config_command.py:49-61) and parser.py:790-794 (_include_envs team env-var spelling)"
 },
 "O3_reason_to_dismiss": "The advisory names the Config API; `airflow config list` is a local admin CLI run by someone who already owns airflow.cfg, and the env-var path reports team values under an odd section name ('team_a', '_section__key') that looks like an unknown/ignored option rather than a sensitive one.",
 "O4_distance": {
  "files": 2,
  "packages": 2,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Non-sensitive team-scoped options (e.g. [team_a=core] parallelism) must stay readable through the API, display_sensitive=True callers must still get real values (kube_config and config lint call as_dict(display_sensitive=True)); masking every '='-section or every '___' env var breaks these.",
  "where": "fix.diff:139-145; providers/cncf/kubernetes/src/airflow/providers/cncf/kubernetes/kube_config.py:47; airflow-core/src/airflow/cli/commands/config_command.py:1002-1008"
 },
 "O6_input_shapes": [
  "[<team>=<section>] config-file section holding a sensitive key",
  "AIRFLOW__<TEAM>___<SECTION>__<KEY> environment variable (reported under section '<team>', key '_<section>__<key>')",
  "team-scoped <key>_cmd and <key>_secret fallbacks, in file sections and as env vars (_CMD/_SECRET), which are not resolved for teams",
  "team names containing '-', '_' or the '=' separator itself",
  "mixed-case section/key spellings (lower-cased before lookup)"
 ],
 "O7_producer": {
  "kind": "config_loader",
  "where": "shared/configuration/src/airflow_shared/configuration/parser.py:779-802 (_include_envs splits a team env var into section/key) and parser.py:1037-1040 (_env_var_name builds the TEAM___ spelling)",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "Core mask_secrets registers only base-section sensitive values with the log secrets masker; team-scoped values of the same options are never registered.",
   "where": "airflow-core/src/airflow/configuration.py:443-455",
   "reason_to_dismiss": "Different output channel (task/process logs, not config display); the advisory is about the Config API.",
   "distance": "different package (airflow-core/src/airflow/configuration.py vs api_fastapi routes), subclass of the shared parser",
   "present_in_latest": "yes",
   "latest_where": "latest/airflow-core/src/airflow/configuration.py:444"
  },
  {
   "route": "Task SDK mask_secrets: second implementation of the same base-only loop for worker-side log masking.",
   "where": "task-sdk/src/airflow/sdk/configuration.py:179-192",
   "reason_to_dismiss": "Separate distribution (task-sdk) and a log-masking concern rather than config exposure.",
   "distance": "different distribution (task-sdk) from both landing point and fix sites",
   "present_in_latest": "yes",
   "latest_where": "latest/task-sdk/src/airflow/sdk/configuration.py:179"
  },
  {
   "route": "Per-key secrets-backend kwarg masking matches literal 'secrets'/'workers' sections only, so a team-scoped AIRFLOW__<TEAM>___SECRETS__BACKEND_KWARG__* env var surfaced by as_dict under section '<team>' is not masked in GET /config.",
   "where": "airflow-core/src/airflow/api_fastapi/core_api/services/public/config.py:34-58",
   "reason_to_dismiss": "The published fix itself documents it as not leaking because the secrets backend is not team aware (fix.diff:59-63).",
   "distance": "same airflow-core API package as landing point (services module), sink in shared parser _include_envs",
   "present_in_latest": "yes",
   "latest_where": "latest/airflow-core/src/airflow/api_fastapi/core_api/services/public/config.py:39"
  }
 ],
 "O8b_injection_room": [
  {
   "where": "airflow-core/src/airflow/api_fastapi/core_api/routes/public/config.py:109-112",
   "sibling": "A team filter on GET /config (or a team-scoped single-option lookup via conf.get(..., team_name=)) that masks with the base (section, key) tuple only.",
   "why_realistic": "Multi-team config is new and conf.get already takes team_name (parser.py:1121-1124 hunk in fix.diff:270-272); a maintainer adding team views would reuse the existing literal lookup."
  },
  {
   "where": "shared/configuration/src/airflow_shared/configuration/parser.py:829-849",
   "sibling": "_filter_by_source / include_* =False branch made team-aware for sources but keyed on base sensitive tuples.",
   "why_realistic": "It already iterates sensitive_config_values by base name, the same idiom the fix had to replace in as_dict."
  }
 ],
 "O9_family": "CWE-200 sensitive information exposure via incomplete redaction (sensitivity check misses alternate name spellings)",
 "O9_dos": false,
 "O10_build": {
  "language": "Python",
  "toolchain": "uv / hatch workspace, pytest (breeze optional)",
  "services": [],
  "offline_after_build": true,
  "project_tests": "shared/configuration/tests/configuration/test_parser.py (pure parser, no DB); airflow-core/tests/unit/api_fastapi/core_api/routes/public/test_config.py (db_test, FastAPI TestClient, sqlite)"
 },
 "O11_fix_minutes": 50,
 "O12_red_flags": [],
 "O13_recall_risk": "low",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "airflow-core/src/airflow/api_fastapi/core_api/routes/public/config.py; shared/configuration/src/airflow_shared/configuration/parser.py (services/public/config.py comment only)",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Strip the '<team>=' prefix before the lookup in get_config_value only, leaving as_dict's env-var path, the _cmd/_secret fallbacks and write() unmasked."
 },
 "out_of_scope_notes": [
  "`airflow config get-value` (airflow-core/src/airflow/cli/commands/config_command.py:70-81) prints raw values by design; not part of this protection."
 ],
 "unverified": [
  "pinned_commit hash not provided; repo treated as parent of 62d37d52.",
  "repo size in MB not measured (no shell); Airflow monorepo is large but likely under 1.5 GB, so giant_repo not flagged.",
  "Whether team-scoped sensitive values are actually read at runtime via conf.get(team_name=) such that mask_secrets omission reaches logs was not traced.",
  "Whether get_sections_including_defaults() yields [team=section] file sections in write() was not traced; assumed from fix test fix.diff:449-476.",
  "Project docs were not checked for a 'sensitive values always hidden' statement (protection_documented_without_exceptions).",
  "Contents of the second fix commit d41ac7b6 are assumed to be included in fix.diff."
 ]
}
  ```
- Published fix sites:   - airflow-core/src/airflow/api_fastapi/core_api/routes/public/config.py:156 — entry point: GET /config/section/{section}/option/{option} [HTTP route handler (airflow-core API)]
  - shared/configuration/src/airflow_shared/configuration/parser.py:790-794 — entry point: AirflowConfigParser.as_dict(display_sensitive=False) via GET /config (env-var collection in _include_envs) [shared lower-level config parser library (separate shared/configuration distribution)]
  - shared/configuration/src/airflow_shared/configuration/parser.py:1792-1803 — entry point: AirflowConfigParser.as_dict(display_sensitive=False) via GET /config [shared lower-level config parser library]
  - shared/configuration/src/airflow_shared/configuration/parser.py:2035-2038 — entry point: CLI `airflow config list` (config_command.show_config -> conf.write(hide_sensitive=...)) [shared lower-level config parser library (write/render path)]
- Uncovered routes to confirm (pattern B):   - airflow-core/src/airflow/configuration.py:443-455 — Core mask_secrets registers only base-section sensitive values with the log secrets masker; team-scoped values of the same options are never registered. (reason to dismiss: Different output channel (task/process logs, not config display); the advisory is about the Config API.; still in latest: yes)
  - task-sdk/src/airflow/sdk/configuration.py:179-192 — Task SDK mask_secrets: second implementation of the same base-only loop for worker-side log masking. (reason to dismiss: Separate distribution (task-sdk) and a log-masking concern rather than config exposure.; still in latest: yes)
  - airflow-core/src/airflow/api_fastapi/core_api/services/public/config.py:34-58 — Per-key secrets-backend kwarg masking matches literal 'secrets'/'workers' sections only, so a team-scoped AIRFLOW__<TEAM>___SECRETS__BACKEND_KWARG__* env var surfaced by as_dict under section '<team>' is not masked in GET /config. (reason to dismiss: The published fix itself documents it as not leaking because the secrets backend is not team aware (fix.diff:59-63).; still in latest: yes)
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

## Environment (`tasks/airflow-mm/environment/Dockerfile`)
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

## Report to the solver (`tasks/airflow-mm/instruction.md`)
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

## Tests (`tasks/airflow-mm/tests/`)
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
- **Wrong-fix patches** go in `build/airflow-mm/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/airflow-mm/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/airflow-mm/manifest.json`:**
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

**Also in `build/airflow-mm/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py airflow-mm --only static
python3 -I builder/gate.py airflow-mm --only nop
python3 -I builder/gate.py airflow-mm --only oracle
python3 -I builder/gate.py airflow-mm --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/airflow-mm/`;
  - edit only `tasks/airflow-mm/`, `build/airflow-mm/` and, for pattern B, the register;
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
