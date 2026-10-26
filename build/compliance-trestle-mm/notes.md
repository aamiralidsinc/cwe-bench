# compliance-trestle-mm — build notes

Start (UTC): 2026-10-18T19:12:12Z (driver launch); builder session began 2026-10-18T19:30Z.

Task: `compliance-trestle-mm`. Pattern: `A+B`. Track: `injected`.
Advisory: GHSA-R4VP-3VW6-R2X5 / CVE-2026-57171 / PYSEC-2026-4030 — path traversal / arbitrary
file write and directory deletion via CLI output names (CWE-22), oscal-compass/compliance-trestle.
Pinned (vulnerable) commit: `0f82d19bd42f9cc0f1b3acd7fc3f6dafe3b6ae10` (verified sole parent of
fix commit `37ed44f5f2e074202c8eb7c2f203c05d19461cdc`).

## PLAN (written before build)

### Recurring trust decision
"May this name become a path under the workspace?" — decided at two places: the shared name rule
`file_utils.is_directory_name_allowed` (string level) and `PathSecurityValidator.validate_local_path`
(resolved-path level). Every lever below is an instance of that decision taken without either check,
or with the wrong one.

### Levers (each one line: pattern, shape, where, reason to dismiss)

Real, published-fix landscape:

- T1 (A) far site, shared name rule: `component-generate -o` and `docs`/`folders` `--task-name` go
  through `trestle/common/file_utils.py:95` `is_directory_name_allowed`, which only rejects reserved
  OSCAL folder names. Dismiss: the report lands on `catalog-generate`; the shared rule reads like a
  naming convention, and the generate commands look fixable locally.
- T2 (A) far site, non-author model commands: `trestle create -t -o` and `trestle replicate -n -o`
  write into any other trestle workspace (`trestle/core/commands/create.py:95`,
  `trestle/core/commands/replicate.py:90`). Dismiss: model management, not markdown generation; a
  plain outside path is already refused by the "must be in a trestle project" check, so the commands
  look safe.
- T3 (B) uncovered route: `trestle import -f -o` writes into another workspace
  (`trestle/core/commands/import_.py:81-84`). Dismiss: import reads external content; output naming
  is model management; the published fix never touches it.
- T4 (B) producer off the check's path: the save-by-name mapper
  `trestle/common/model_utils.py:635-648` `_root_path_for_top_level_model` turns a model name into
  `<ws>/<models-dir>/<name>`; assemble/resolve commands write there and rmtree the existing parent.
  Dismiss: a model name is not a path; "generate" is what the report talks about.
- T5 (B) uncovered route: `component-generate --force-overwrite` clears the named folder before the
  command's own name rule runs (`trestle/core/commands/author/component.py:63-77`). Dismiss:
  force-overwrite is opt-in, and the command already has a name check.
- T6 (B) uncovered route, content-derived name: `component.title` from the component-definition JSON
  becomes a markdown subdirectory (`trestle/core/commands/author/component.py:89`). Dismiss: titles
  are display text; the report is about command-line names. Also defeats a CLI-argument prober.

Injected siblings (added at the same recurring trust decision; placed where the published fix never
touches; each reachable through the real `trestle` CLI; each covered by the stated invariant):

- T7 (inj) file name under an already-created task folder: `author docs create-sample --sample-name`
  writes the template copy to `<task folder>/<name>` with no workspace check
  (`trestle/core/commands/author/docs.py`). Dismiss: it names a markdown file, and the task folder it
  lands in was created from an already-validated task name.
- T8 (inj) nested instance folder under an already-validated task folder: `author folders setup
  --instance-name` creates `<task folder>/<name>` and writes the versioned templates there
  (`trestle/core/commands/author/folders.py`). Dismiss: the command already refuses reserved task
  names through the shared name rule, so the command looks covered.
- T9 (inj) coupled visible/hidden binding: `author component-generate --component-name` selects a
  subfolder under the already-validated `-o` output folder, with no check of its own
  (`trestle/core/commands/author/component.py`). Dismiss: `-o` is the documented output and is
  validated; this only selects a subfolder beneath it.

### Input shapes the security tests cover
- absolute name (`/tmp/...`)
- leading `..` relative name (`../../x`)
- non-leading `..` component (`sub/../../x`) — beats a first-component-only rule
- a neighbouring trestle workspace (create/replicate/import), so a "must already be a trestle
  project" check does not cover it

### Coupled must-keep-working behaviour (functional tests)
- nested names stay valid: `-o markdown/catalogs/nist`, task names `policies/access`,
  `architecture/diagrams`, and the injected options with ordinary nested names
- `--force-overwrite` on a folder inside the workspace, and re-running so a command replaces its own
  earlier result
- workspace-wide governed-document validation without naming a task still examines root folders
  (the shared name rule is handed relative paths there)
- reserved names are still refused (`catalogs`, `__global__`, dotted names)
- component markdown is still generated per component, and component-assemble still round-trips

### Project tests that must keep passing
`tests/trestle/utils/fs_test.py` (incl. `test_allowed_task_name`, which expects nested names True),
`tests/trestle/core/commands/author/{catalog,prof,ssp,component,headers,docs,folders}_test.py`,
`tests/trestle/core/commands/{create,replicate,import__}_test.py`.

### What I will verify
- the flaw reproduces through the real CLI at the pinned commit for every lever
- no regression tests for the advisory exist at the pinned commit (fix commit is the direct child)
- every security case fails on the pinned+injected image and passes on the oracle
- every check patch behaves as declared
- project tests pass offline at the pinned commit

### Out of scope (one line each)
- read-side traversal: `-n`/`-m`/`-f` input names of replicate, catalog/profile assemble, import.
- `clear_folder` on generate `-fo` resolves relative to the cwd rather than the workspace root.
- symlink-based escapes (outside this advisory's spelled-name scope).

### Injection realism
T7–T9 are ordinary feature code a maintainer would write (a named sample file, a named template
instance, a single-component generate), with no misleading names or comments. Each sits in a file
the published fix never modifies (`docs.py`, `folders.py`, `component.py`). Each is reachable from
the real CLI. Each is covered by the invariant "no name trestle turns into a path … may cause a file
or directory outside the workspace to be created, modified or deleted".

---

## BUILD RESULT (written after the build)

End (UTC): 2026-10-18T21:20Z (pre-gate; gate stages still to run).

### Verified
- Exploitability matrix on the pinned+injected tree: 53/53 probe cases change something outside
  the workspace (writes, or an outside folder emptied first). On the oracle-fixed tree 53/53 are
  refused with nothing outside changed and legitimate use intact.
- Injection is three CLI naming options in `docs.py`, `folders.py` and `component.py`, applied by
  `environment/injection.patch` onto the pinned commit before `pip install`.
- The published fix (`37ed44f5`) covers the shared name rule, the headers caller, create/replicate
  and the three generate commands. It does not touch `import_.py`, `model_utils.py`, `component.py`,
  `docs.py` or `folders.py` — that split is the A/B boundary.
- Project tests run offline at the pinned+injected commit except 7 network-dependent tests
  (deselected in `tests/test.sh`). `tests/test.sh` restores pristine copies before the functional
  group so the agent cannot have altered them.
- No regression tests for the advisory exist at the pinned commit: the fix commit is the direct
  child, and the image drops `.git` before the agent sees it.

### Check patches (20)
15 `security_fail`, 3 `functional_fail`, 2 `pass` (one `hardening`, one `alternative`).
`blind.patch` and `FAIRNESS.md` are for whoever writes those after me.
The alternative fix uses a different design: one realpath/relative_to helper in the shared
utilities, a lexical rule in the name check, the judgement in the public save/lookup APIs rather
than the private mapper, and the folder cleared only after the name is accepted.

### One-line mechanism summaries (detail lives in the tests)
- T1 shared name rule accepts absolute and inner-`..` spellings (A).
- T2 create/replicate write into a neighbouring trestle workspace (A).
- T3 import writes there too (B).
- T4 the save-by-name mapper turns an output model name into a folder (B, producer off the check's path).
- T5 replace empties the folder before the name is judged (B).
- T6 a name taken from the model content becomes a markdown subfolder (B).
- T7-T9 naming options that join onto an already-judged folder (injected siblings).

### Register
Pattern B and injected rows appended to `build/audit/uncovered-routes.tsv` (T3-T9).
`disclosure_status = pending client decision` throughout.

### Scope note (one line)
Read-side traversal on input names, `clear_folder` resolving `-fo` against the cwd rather than the
workspace root, and symlink escapes are outside this advisory's spelled-name scope and were not built on.
