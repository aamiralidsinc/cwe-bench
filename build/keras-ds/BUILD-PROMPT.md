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

Project root: `/home/mara/cwe-bench`. Task: `keras-ds`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: ["GHSA-26C4-7VV6-867J", "CVE-2026-12480", "PYSEC-2026-3629"]; keras-team/keras; CWE-73 external control of file path: untrusted HDF5 weights file can make the loader read other local files through virtual datasets, external storage or soft/external links (local file disclosure into model weights)
- Pinned (vulnerable) commit: unknown (parent of 8f987f11bf7512f0df4774a8f1557bba07dc2b49; pinned tree is release 3.12.1 per fix.diff:1315). Published fix: 8f987f11bf7512f0df4774a8f1557bba07dc2b49, d5a88bdb137c0d3039b8f4bbbe8c7099925cc10c.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "65",
 "advisory_ids": [
  "GHSA-26C4-7VV6-867J",
  "CVE-2026-12480",
  "PYSEC-2026-3629"
 ],
 "repo": "keras-team/keras",
 "pinned_commit": "unknown (parent of 8f987f11bf7512f0df4774a8f1557bba07dc2b49; pinned tree is release 3.12.1 per fix.diff:1315)",
 "fix_commits": [
  "8f987f11bf7512f0df4774a8f1557bba07dc2b49",
  "d5a88bdb137c0d3039b8f4bbbe8c7099925cc10c"
 ],
 "trust_decision": {
  "summary": "When Keras loads weights from an untrusted HDF5 file, it decides whether each group/dataset it reads may follow a soft/external link or pull data from outside the file (external storage or virtual-dataset sources). At the pinned commit this check is H5IOStore._verify_dataset/_verify_group, which checks external storage only. The legacy .h5 loader has no check at all.",
  "evidence": [
   "keras/src/saving/saving_lib.py:1040-1057",
   "keras/src/saving/saving_lib.py:1162-1163",
   "keras/src/legacy/saving/legacy_h5_format.py:582",
   "fix.diff:655-684"
  ]
 },
 "landing_point": {
  "where": "keras/src/saving/saving_lib.py:1047",
  "why": "H5IOStore._verify_dataset already rejects `dataset.external`. Anyone searching for 'external'/HDF5 dataset validation lands there, and the obvious fix is to add `is_virtual` next to it."
 },
 "fix_sites": [
  {
   "where": "keras/src/saving/saving_lib.py:1047-1057",
   "entry_point": "keras.saving.load_model (.keras) / keras.saving.load_weights & Model.load_weights (.weights.h5, .keras) via H5IOStore.__getitem__",
   "module_kind": "core serialization store (replaced by module-level safe_get_h5_dataset, fix.diff:655-684)"
  },
  {
   "where": "keras/src/saving/saving_lib.py:1114-1131",
   "entry_point": "keras.saving.load_model / load_weights via H5IOStore.get (group lookup incl. 2.13 _layer_checkpoint_dependencies compat path)",
   "module_kind": "core serialization store"
  },
  {
   "where": "keras/src/saving/saving_lib.py:1163",
   "entry_point": "keras.saving.load_weights / load_model, dataset read in H5IOStore.__getitem__",
   "module_kind": "core serialization store"
  },
  {
   "where": "keras/src/saving/saving_lib.py:1387-1391",
   "entry_point": "keras.saving.load_weights on sharded .weights.json via ShardedH5IOStore._get_h5_group",
   "module_kind": "subclass / second store implementation (sharded)"
  },
  {
   "where": "keras/src/legacy/saving/legacy_h5_format.py:142",
   "entry_point": "keras.saving.load_model on legacy .h5/.hdf5 (saving_api.py:196)",
   "module_kind": "legacy loader"
  },
  {
   "where": "keras/src/legacy/saving/legacy_h5_format.py:361",
   "entry_point": "keras.saving.load_weights legacy .h5 topological (saving_api.py:308) and load_model .h5",
   "module_kind": "legacy loader"
  },
  {
   "where": "keras/src/legacy/saving/legacy_h5_format.py:374",
   "entry_point": "same as above",
   "module_kind": "legacy loader"
  },
  {
   "where": "keras/src/legacy/saving/legacy_h5_format.py:401",
   "entry_point": "same as above (top_level_model_weights)",
   "module_kind": "legacy loader"
  },
  {
   "where": "keras/src/legacy/saving/legacy_h5_format.py:504",
   "entry_point": "keras.saving.load_weights legacy .h5 with by_name=True (saving_api.py:303-306)",
   "module_kind": "legacy loader"
  },
  {
   "where": "keras/src/legacy/saving/legacy_h5_format.py:538",
   "entry_point": "same as above (top_level_model_weights, by_name)",
   "module_kind": "legacy loader"
  },
  {
   "where": "keras/src/legacy/saving/legacy_h5_format.py:582",
   "entry_point": "all legacy .h5 weight loads (load_subset_weights_from_hdf5_group)",
   "module_kind": "legacy loader"
  },
  {
   "where": "keras/src/legacy/saving/legacy_h5_format.py:594-599",
   "entry_point": "keras.saving.load_model .h5 with compile=True and optimizer_weights (legacy_h5_format.py:166-186)",
   "module_kind": "legacy loader, optimizer state"
  }
 ],
 "O1_entry_points": 3,
 "O2_out_of_scope_site": {
  "kind": "legacy_path",
  "where": "keras/src/legacy/saving/legacy_h5_format.py:582 (also :142, :361, :374, :401, :504, :538, :594-599); reached from keras/src/saving/saving_api.py:196 and :300-310"
 },
 "O3_reason_to_dismiss": "The legacy .h5 format lives in keras/src/legacy and is a Keras 2 backward-compatibility path. The report is about the Keras 3 .keras/.weights.h5 store, so a solver can argue the legacy loader is out of scope. It had no _verify_* check at all, so it does not look like 'the' protection.",
 "O4_distance": {
  "files": 4,
  "packages": 2,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Ordinary members must still load: h5py `get(..., getlink=True)` returns HardLink for every normal group/dataset, so a fix that rejects any link class (not only SoftLink/ExternalLink) breaks every load. Other loads that must keep working: the 2.13 `_layer_checkpoint_dependencies` fallback, bfloat16 datasets, and empty-group defaults.",
  "where": "keras/src/saving/saving_lib.py:1123-1130, keras/src/saving/saving_lib.py:1164-1169, fix.diff:643-645"
 },
 "O6_input_shapes": [
  "virtual dataset (is_virtual)",
  "dataset with external raw storage (dataset.external)",
  "h5py.SoftLink at group or dataset position",
  "h5py.ExternalLink at group or dataset position",
  "object of wrong type (Dataset where Group expected and vice versa)",
  "missing key (KeyError preserved for empty-dict default)"
 ],
 "O7_producer": {
  "kind": "none",
  "where": "",
  "check_calls_producer": null
 },
 "O8_uncovered_routes": [
  {
   "route": "KerasFileEditor reads every dataset of an H5 weights file recursively, rejecting only external storage (no virtual-dataset or Soft/ExternalLink check). The fix touched only its import.",
   "where": "keras/src/saving/file_editor.py:476-519",
   "reason_to_dismiss": "KerasFileEditor is an inspection/editing utility, not a model loader, and it already has its own 'external' check, so it looks deliberately handled.",
   "distance": "different file in the same package (keras/src/saving/file_editor.py vs saving_lib.py); public API keras.saving.KerasFileEditor (file_editor.py:37), loads at construction (file_editor.py:92-101)",
   "present_in_latest": "no",
   "latest_where": "latest/keras/src/saving/file_editor.py:542"
  },
  {
   "route": "saving_api.load_weights on legacy .h5 fetches the 'model_weights' group with raw indexing, without the link/type check the fix applied to the same lookup in load_model_from_hdf5.",
   "where": "keras/src/saving/saving_api.py:300-302",
   "reason_to_dismiss": "The downstream legacy loader now checks every layer group and dataset, so a solver can argue the top-level group lookup is just a dispatch step.",
   "distance": "different file (saving_api.py) from both the landing point and the legacy loader",
   "present_in_latest": "no",
   "latest_where": "latest/keras/src/saving/saving_api.py:327"
  }
 ],
 "O8b_injection_room": [
  {
   "where": "keras/src/saving/saving_lib.py:1421-1432",
   "sibling": "ShardedH5IOStore.__getitem__ could read a cross-shard dataset with a direct `self._h5_entry_group[key]` instead of going through the base __getitem__",
   "why_realistic": "Shard switching is its own code path, and a maintainer optimising for speed could plausibly index directly after _switch_h5_file."
  },
  {
   "where": "keras/src/saving/file_editor.py:487-494",
   "sibling": "the 'vars' sub-group lookup uses raw `value[\"vars\"]` (upstream later switched it to safe_get_h5_group)",
   "why_realistic": "It is already a raw group lookup at the pinned commit, so it is a natural place for a group-level sibling."
  }
 ],
 "O9_family": "CWE-73 external control of file path: untrusted HDF5 weights file can make the loader read other local files through virtual datasets, external storage or soft/external links (local file disclosure into model weights)",
 "O9_dos": false,
 "O10_build": {
  "language": "Python",
  "toolchain": "pip install -r requirements.txt (h5py, numpy, ml_dtypes, a CPU backend: jax/tensorflow/torch)",
  "services": [],
  "offline_after_build": true,
  "project_tests": "keras/src/saving/saving_lib_test.py, keras/src/saving/file_editor_test.py, keras/src/saving/saving_api_test.py, keras/src/legacy/saving/legacy_h5_format_test.py (some cases need tf_keras)"
 },
 "O11_fix_minutes": 40,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "keras/src/saving/saving_lib.py, keras/src/legacy/saving/legacy_h5_format.py (plus import-only/unrelated: keras/src/saving/file_editor.py, keras/src/utils/module_utils.py, keras/src/models/functional.py, keras/src/utils/file_utils.py, keras/src/export/openvino.py, keras/src/version.py)",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Add `if dataset.is_virtual: raise` to H5IOStore._verify_dataset only, leaving links, the legacy .h5 loader, KerasFileEditor and the load_weights legacy branch open."
 },
 "out_of_scope_notes": [
  "fix.diff also bundles unrelated hardening: Functional.from_config loop/missing-node detection (keras/src/models/functional.py) and archive extraction base-dir check (keras/src/utils/file_utils.py); these belong to other advisories.",
  "keras/src/datasets/*.py open downloaded npz files with f[...] indexing; npz, not HDF5, so not this sink."
 ],
 "unverified": [
  "Exact pinned commit hash: parent_commit is null and the repo copy has no git metadata that I checked.",
  "repo_mb not measured (no shell use).",
  "The fix diff adds no regression tests for virtual/external/link rejection (only skipif decorators in legacy_h5_format_test.py), so the hidden tests would be ours to write; not confirmed whether the second fix commit adds tests elsewhere.",
  "O1 counts public API functions (keras.saving.load_model, keras.saving.load_weights, Model.load_weights at keras/src/models/model.py:376/418); by file format there are about 5 routes (.keras, .weights.h5, sharded .weights.json, legacy .h5 load_model, legacy .h5 load_weights).",
  "Whether an ExternalLink at the saving_api.py:302 group lets downstream reads reach another file was reasoned from h5py semantics, not executed."
 ]
}
  ```
- Published fix sites:   - keras/src/saving/saving_lib.py:1047-1057 — entry point: keras.saving.load_model (.keras) / keras.saving.load_weights & Model.load_weights (.weights.h5, .keras) via H5IOStore.__getitem__ [core serialization store (replaced by module-level safe_get_h5_dataset, fix.diff:655-684)]
  - keras/src/saving/saving_lib.py:1114-1131 — entry point: keras.saving.load_model / load_weights via H5IOStore.get (group lookup incl. 2.13 _layer_checkpoint_dependencies compat path) [core serialization store]
  - keras/src/saving/saving_lib.py:1163 — entry point: keras.saving.load_weights / load_model, dataset read in H5IOStore.__getitem__ [core serialization store]
  - keras/src/saving/saving_lib.py:1387-1391 — entry point: keras.saving.load_weights on sharded .weights.json via ShardedH5IOStore._get_h5_group [subclass / second store implementation (sharded)]
  - keras/src/legacy/saving/legacy_h5_format.py:142 — entry point: keras.saving.load_model on legacy .h5/.hdf5 (saving_api.py:196) [legacy loader]
  - keras/src/legacy/saving/legacy_h5_format.py:361 — entry point: keras.saving.load_weights legacy .h5 topological (saving_api.py:308) and load_model .h5 [legacy loader]
  - keras/src/legacy/saving/legacy_h5_format.py:374 — entry point: same as above [legacy loader]
  - keras/src/legacy/saving/legacy_h5_format.py:401 — entry point: same as above (top_level_model_weights) [legacy loader]
  - keras/src/legacy/saving/legacy_h5_format.py:504 — entry point: keras.saving.load_weights legacy .h5 with by_name=True (saving_api.py:303-306) [legacy loader]
  - keras/src/legacy/saving/legacy_h5_format.py:538 — entry point: same as above (top_level_model_weights, by_name) [legacy loader]
  - keras/src/legacy/saving/legacy_h5_format.py:582 — entry point: all legacy .h5 weight loads (load_subset_weights_from_hdf5_group) [legacy loader]
  - keras/src/legacy/saving/legacy_h5_format.py:594-599 — entry point: keras.saving.load_model .h5 with compile=True and optimizer_weights (legacy_h5_format.py:166-186) [legacy loader, optimizer state]
- Uncovered routes to confirm (pattern B):   - keras/src/saving/file_editor.py:476-519 — KerasFileEditor reads every dataset of an H5 weights file recursively, rejecting only external storage (no virtual-dataset or Soft/ExternalLink check). The fix touched only its import. (reason to dismiss: KerasFileEditor is an inspection/editing utility, not a model loader, and it already has its own 'external' check, so it looks deliberately handled.; still in latest: no)
  - keras/src/saving/saving_api.py:300-302 — saving_api.load_weights on legacy .h5 fetches the 'model_weights' group with raw indexing, without the link/type check the fix applied to the same lookup in load_model_from_hdf5. (reason to dismiss: The downstream legacy loader now checks every layer group and dataset, so a solver can argue the top-level group lookup is just a dispatch step.; still in latest: no)
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

## Environment (`tasks/keras-ds/environment/Dockerfile`)
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

## Report to the solver (`tasks/keras-ds/instruction.md`)
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

## Tests (`tasks/keras-ds/tests/`)
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
- **Wrong-fix patches** go in `build/keras-ds/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/keras-ds/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/keras-ds/manifest.json`:**
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

**Also in `build/keras-ds/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py keras-ds --only static
python3 -I builder/gate.py keras-ds --only nop
python3 -I builder/gate.py keras-ds --only oracle
python3 -I builder/gate.py keras-ds --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/keras-ds/`;
  - edit only `tasks/keras-ds/`, `build/keras-ds/` and, for pattern B, the register;
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
