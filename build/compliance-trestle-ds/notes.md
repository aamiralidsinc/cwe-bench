# compliance-trestle-ds: build notes

Start (UTC): see `start_utc.txt` (2026-10-18T19:08:03Z)
End (UTC): see `end_utc.txt`

## Advisory / commits
GHSA-R4VP-3VW6-R2X5 / CVE-2026-57171 / PYSEC-2026-4030 — oscal-compass/compliance-trestle,
CWE-22 path traversal / arbitrary file write and directory deletion via CLI output names.
Pinned (vulnerable) `0f82d19bd42f9cc0f1b3acd7fc3f6dafe3b6ae10`, verified sole parent of the
published fix `37ed44f5f2e074202c8eb7c2f203c05d19461cdc`. Track INJECTED, pattern A + B.

This rebuild replaces `compliance-trestle-path-traversal`, which both target models solved on
run 1 (reward 1.0). The base levers are kept and three injected companion-output siblings are
added at the same trust decision (a user-chosen name turned into a location inside the workspace).

## Mechanism (one line)
A name the user gives a command for something the command produces or replaces is joined onto
the workspace (or onto an already-checked output path) without confirming that the result stays
inside the workspace the command runs in; it must be refused when it does not.

## Levers (8; each has a different reason to dismiss it)
- T1 (A, published far site): shared name check `trestle/common/file_utils.py:95-122`, reached by
  component markdown output and docs/folders task names. Dismiss: looks like a naming rule; the
  report lands on the catalog command.
- T2 (A, published far site): `create`/`replicate` output names (`create.py:95`, `replicate.py:90`)
  writing into another trestle workspace. Dismiss: model management, and a plain outside path is
  already refused by the "must be in a trestle project" check.
- T3 (B): `import -o` (`import_.py:81-84`). Dismiss: import reads external content; untouched by
  the published fix.
- T4 (B, producer off the check's path): save-by-name mapper `model_utils.py:635-648`, used by
  catalog/component/profile assemble, profile-resolve/inherit and ssp-filter. Dismiss: assemble
  writes a model by name, not markdown; a model name is not a path.
- T5 (B): component `--force-overwrite` clears the named folder before the name is accepted
  (`component.py:63-77`). Dismiss: opt-in flag and the command already checks the name.
- S1 (injected): ssp generation's inheritance view folder name is joined onto the generated
  markdown folder unchecked (option at `ssp.py:95-104`, use at `ssp.py:238-240`). Dismiss:
  auxiliary subfolder under an already-checked output; only reached with a leveraged ssp.
- S2 (injected): the assembled output file name is joined into the project dist folder unchecked
  (`assemble.py:43`, use `assemble.py:94-96`). Dismiss: internal derived-data folder; looks like
  a cosmetic rename.
- S3 (injected): the companion index file name is joined onto the workspace unchecked
  (`component.py:58-63`, use `component.py:89-91`). Dismiss: a small convenience file next to the
  main result, not one of the command's named outputs.

Coupled must-keep-working: nested inside names and task names, force-overwrite inside the
workspace, workspace-wide header validation without a task name, reserved names still refused,
default inheritance/inheritance-view naming, custom inside output names, the project suite.

## Verified
- Pinned+injected tree: all 38 security testcases fail by their side-effect assertion; all 17 task
  functional tests pass; 409 selected project area tests pass.
- Reference fix: 38/38 security, 17/17 functional, 409/409 project area tests pass.
- Each injected sibling reproduces through the real CLI (absolute and `..` spellings; S2 targets a
  second trestle workspace because the path-creation action refuses a plain non-project path).
- A symlinked directory inside the workspace pointing outside is refused by the reference fix and
  written through on the vulnerable tree.
- All 18 check patches apply with `patch -p1` on the pinned+injected tree; each was run against the
  hidden suites locally and behaves as declared (see `check-logs/`).
- The project test copies under `tests/functional/project/tests` are byte-identical to the pinned
  checkout; `test.sh` restores them before running the project group.
- No regression tests for the advisory exist at the pinned commit (fix commit is its child).

## Could not verify
- No target-model trials were run (per instructions). The bar is decided by the later trial stage.
- `present_in_latest` for T3-T5 is taken from the prior build's read-only look at upstream
  `a92c5955` (still HEAD); the injected siblings are our-copy-only (`n/a`).
- Whether a public upstream report exists for T3-T5 (no search done).

## Out of scope (one line each)
- Read-side traversal via model names/hrefs (catalog/profile `-n`, replicate `-n`, import `-f`).
- Control ids, group titles and component titles used as markdown path components: model content,
  not a CLI output name.
- Explicit file paths (`canonicalize -o`, `create -f`, `validate -f`): a path the user names
  directly, not a name placed inside the workspace.
- Task-module configuration output paths (`trestle task`).

## Fairness notes
- Every lever is reachable through the real CLI and covered by the stated invariant ("no name a
  user gives a command for something it produces or replaces ... whichever command, option or
  mode"). The injected options are visible in the commands' own option lists and code.
- The instruction names no internal identifier, route or command beyond the single public example.

## Gate
- static: PASSED except the two intentionally-later items (blind patch, FAIRNESS.md).
- nop: PASSED (security 38/38 fail on the pinned+injected tree; functional 426/426 pass).
- oracle: PASSED (3 runs, identical; security 38/38, functional 426/426, reward 1.0)
- patches: the full 17-check run was cut twice by Docker-network races on the shared machine
  ("network not found" between compose create and start, an infrastructure error, not a task
  failure). The gated set was reduced to the 12 essential checks and run one check per gate
  invocation; per-check results are saved as gate_report.<check>.json. no_helper (0.9211),
  no_create_replicate (0.8684) and no_import (0.9474) behaved as security_fail in the aborted
  stage runs (job dirs compliance-trestle-ds-chk-no_helper-1792355515, -no_create_replicate-1792355915,
  -no_import-1792356175).
  Gated one per invocation: no_mapper, no_inheritance_view, no_assemble_output, no_component_index,
  check_after_clear, refuse_all, no_separators (functional_fail), hardening (pass, 1.0) and
  alt_workspace_helper (pass, 1.0). The only failures seen were the Docker-network race above.

## Upgrade 2026-10-20 (sibling-injection compliance, BETTER-PATTERNS §2-§8)
- instruction.md: the route-naming "Observed impact" block and every route/option-shaped
  must-keep-working clause were removed. The security property is now stated once, generally,
  over names the command turns into workspace locations; the coupled contracts remain general.
- Levers unchanged; the task already carries how-type levers: T4 (a save-by-name producer the
  shared check never calls, M6), T5 (validation ordered after the destructive overwrite) and the
  T1/headers.py coupled caller adaptation (M11).
- Coverage: added `test_sec_task_names.py::test_headers_setup_task_outside` (absolute and
  nested-parent shapes), the last task-name producer reachable through the shared check that was
  not yet asserted. Same lever as T1, so no new security_fail patch is needed; no_helper.patch
  still turns it red. Pinned+injected: the outside directory is created (fails); reference fix:
  refused in `_initialize` with exit 1 before any write.
- manifest.json: leak_terms gained the removed route/option tokens (catalog-generate,
  --force-overwrite, -fo, -o, "output folder", "output file", "task name", trestle init);
  T1 now lists the headers setup route; security testcase count 38 -> 40.
- No repo code, fix.patch or environment change; image not rebuilt. Full container gate still
  needed because tests/ changed.


## Hardening 2026-10-21 (Frontier delivery format + two new levers)
- Reformatted to schema 1.4: /workspace workdir, separate offline verifier (`tests/Dockerfile`,
  artifacts restore), uid-1000 non-root grading, dual scoring (`metrics.json`), fresh canary GUID,
  B7 metadata, instruction without any test/grading mention and with "There is no network access."
- Two new fair levers, both real unmodified upstream code that the existing reference fix left open:
  - T6 (wrong object): `clear_folder(pathlib.Path(args.output))` in catalog/profile/component
    generate resolves the destructive overwrite against the current directory, while the command
    writes the same name inside the workspace. Run with `--trestle-root <ws>` from another directory
    and `-fo`, a plain inside name deletes an unrelated same-named folder outside the workspace.
    Reason to dismiss: the name is checked and is an ordinary inside name; the overwrite is opt-in
    and the new check sits right before it. Security test:
    `test_sec_force_overwrite.py::test_force_overwrite_clears_workspace_folder` (catalog and
    component). Coupled functional: overwriting from another directory still succeeds and clears
    the result inside the workspace. Check patch: `no_clear_base.patch`.
  - T7 (uncovered route + link-following): the governed-document task path is joined from the task
    name and only string-checked (`author/common.py`); `docs create-sample` (shutil.copy) and
    `folders create-sample` (shutil.copytree) then write through an existing link inside the
    workspace that points outside it. Reason to dismiss: the task name passes the shared naming
    rule, `setup` writes only inside `.trestle`, and `create-sample` is a convenience mode.
    Security tests: `test_sec_task_sample.py` (docs and folders). Coupled functional:
    `test_func_tasks.py::test_docs_create_sample_inside` and `::test_folders_create_sample_inside`
    (nested task names keep working). Check patch: `no_task_link.patch`.
- `solution/fix.patch` extended: the three overwrites now clear `trestle_root / <name>`, and the
  governed-document task path is resolved and refused when it leaves the workspace.
- Pass patches `hardening.patch` and `alt_workspace_helper.patch` extended to the new levers; a
  third independent fix, `blind.patch` (kind=blind), added and verified at 1.0.
- Verified locally (dev image, oracle tree): 44/44 security, 20/20 task functional, 409/409 project
  area tests; on the pinned+injected tree 44/44 security fail and 20/20 functional pass.
- Security testcases: 40 -> 44. Functional task tests: 17 -> 20.
