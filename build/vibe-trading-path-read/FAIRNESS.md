# FAIRNESS review: vibe-trading-path-read

Reviewer: pre-trial fairness and leniency gate (BUILDER.md 3h). Static review only. I ran no Docker, trials, gates or tests, and I did not look up the upstream fix.
Inputs read: instruction.md, tests/ (security, functional, functional/project/tests, conftest, test.sh,
score.py, pytest.ini), solution/fix.patch, manifest.json, notes.md, checks/*.patch.
The repository source is not available locally (the Dockerfile clones it), so I could not inspect some tool signatures, for example the shadow report tool's arguments. I flag those below as unverified.

Grading facts that matter: any functional failure, including in `project.xml`, sets the reward to 0. Hidden tests call
`call_tool` in one pytest process and set `HOME` and `VIBE_TRADING_ALLOWED_FILE_ROOTS` with `monkeypatch`
after the product modules have been imported (the first `call_tool` imports them lazily). The project tests run from
pristine copies with `VIBE_TRADING_ALLOWED_FILE_ROOTS=/tmp/vt-grading/project`. The solver is never told about that setting.

## 1. Per-test table

### tests/security/test_tool_path_confinement.py

| Test | Asserts | Instruction basis | Could a correct fix fail? | Risk |
|---|---|---|---|---|
| test_document_absolute_path_in_home | read_document on `$HOME/private/credentials.txt` gives an error with no marker | "No argument … may make the tool read … outside the areas above … absolute … paths"; the Observed impact example | no | low |
| test_document_relative_to_working_directory | relative `vtgrade_x/config/service.env` (under CWD=/app/agent) refused | "absolute or relative paths" | no. A fix that resolves relative paths against the upload area gets "not found", which is still an error | low |
| test_document_dot_dot_out_of_upload_area | `<uploads>/../../…/notes.txt` refused | "`..` segments" | no | low |
| test_document_symlink_in_upload_area_pointing_outside | symlink placed in uploads pointing to an outside file is refused | "links that point somewhere else" (also standard expert knowledge: resolve before checking containment) | no | low |
| test_document_sibling_of_configured_directory | env=`home/imports`; `home/imports-old/notes.txt` refused | "A directory whose name merely starts with … is not inside it" | no | low |
| test_trade_statement_elsewhere_in_home | analyze_trade_journal on `$HOME/Documents/x.csv` refused, no records returned | general rule; HOME is not a listed area | no | low |
| test_trade_statement_home_shorthand | `~/Desktop/trades.csv` refused | "`~`" in the spelling list | no | low |
| test_trade_statement_relative_to_working_directory | CWD-relative CSV refused | "relative paths" | no | low |
| test_shadow_profile_from_statement_elsewhere_in_home | extract_shadow_strategy refused, and no profile is written to `~/.vibe-trading/shadow_accounts` | general rule plus "without creating or modifying anything" | no | low |
| test_read_file_with_workspace_set_to_other_directory | read_file with run_dir=outside refused, no marker | "a workspace to work in"; "must be inside run storage" | no | low |
| test_read_file_with_relative_workspace_climbing_out | run_dir=`../../…/outside` (resolved by the loop against the current run) refused | same, plus "`..` segments" | no | low |
| test_write_file_with_workspace_set_to_other_directory | refused, and the outside tree stays empty | "create or change"; "must be inside run storage" | no | low |
| test_edit_file_with_workspace_set_to_other_directory | refused, file unchanged, old content not echoed | same | no | low |
| test_pattern_scan_on_other_directory | pattern run_dir=outside refused, symbol not leaked | "read, list … a workspace to work in" | no | low |
| test_backtest_on_other_directory | backtest run_dir=outside refused, outside tree unchanged | "run … a workspace to work in" | no | low |
| test_factor_inputs_from_home | factor CSVs in `$HOME/data` refused, and no ic_series written | general rule ("a file to read") | no | low |
| test_factor_output_to_other_directory | output_dir outside run storage refused and not created | "a place to write output"; "write into must be inside run storage" | no | low |

### tests/functional/test_legitimate_tool_use.py

| Test | Asserts | Instruction basis | Could a correct fix fail? | Risk |
|---|---|---|---|---|
| test_uploaded_text_document_is_readable | upload, then read_document by the returned path | "uploaded files by the path the upload returned" | no | low |
| test_uploaded_spreadsheet_document_is_readable | same, for CSV | same | no | low |
| test_upload_area_path_with_dot_segments_staying_inside | `<uploads>/./sub/../name` readable | "Paths whose `.` or `..` segments stay inside an area keep working" | no | low |
| test_document_in_current_run_workspace_is_readable | read_document on `<run>/report.md` | "files in the current run's workspace" | no. A fix that limits read_document to uploads and configured dirs would fail, but the instruction lists this case | low |
| test_uploaded_trade_statement_is_analysed | journal tool on an upload returns 30 records | uploads bullet | no | low |
| test_uploaded_trade_statement_builds_shadow_profile | shadow tool on an upload returns ok | uploads bullet | no | low |
| test_configured_directories_are_readable | env `"a, b"` set by monkeypatch after import; doc and journal reads ok | configured-dirs bullet (comma, spaces) | **yes**. A fix that reads the env var once at import (a module constant, a common operator-config idiom) fails, because the product was imported earlier in the same process with the var unset | **medium** |
| test_configured_directory_with_home_shorthand | env `~/broker-exports` with monkeypatched HOME; `~/broker-exports/trades.csv` analysed | "entries may start with `~`"; "works exactly as today" (the journal tool expands `~` today) | **yes**, for the same import-time caching reason (env value and HOME). A fix that refuses every `~` argument also fails; the "as today" wording covers that case | **medium** |
| test_read_file_in_current_run_default_workspace | read_file with no run_dir | "files in the current run's workspace" | no | low |
| test_read_file_with_relative_and_absolute_workspace | run_dir `.`, `code`, absolute current run | stated explicitly ("such as `.` or a subdirectory, or by its absolute path") | no | low |
| test_read_file_bundled_skill_docs | `name/SKILL.md` and `skills/name/SKILL.md` via read_file | "bundled skill documentation, which the agent may read" | no. A run-storage check added inside the shared workspace helper breaks this, which is a real regression | low |
| test_write_and_edit_file_in_current_run | write then edit in the current run | current run workspace | no | low |
| test_pattern_scan_on_current_run | pattern on the current run's artifacts | same | no | low |
| test_backtest_runs_in_current_run | runner leaves `logs/runner_stdout.txt` in the run | same | no | low |
| test_factor_analysis_on_run_artifacts | inputs and output in the current run | same | no | low |
| test_factor_analysis_on_uploaded_csvs | inputs uploaded, output in run | uploads plus run storage | no | low |

### Project tests (pristine copies; any failure means reward 0)

| Test | Asserts | Basis | Could a correct fix fail? | Risk |
|---|---|---|---|---|
| test_doc_reader.py (all functions except test_missing_file) | read_document on pytest tmp files under `/tmp/vt-grading/project` (allowed only through the env var set by test.sh) | configured-dirs bullet | no, if the env var is honoured. **But** in the repo the solver sees these tests fail under any correct fix (tmp_path is outside every area) and has no way to know the grader configures the var. That pushes the solver to widen the boundary (allow `/tmp`), which the security tests then catch. test_directory_rejected also pins the substring "not a file" | **medium** (instruction gap) |
| test_shadow_account.py (all) | library and tool behaviour; the tool reads a journal in the allowed tmp dir; library `render_shadow_report(output_dir=tmp_path)` writes to tmp | as above | maybe. A solver who confines output dirs inside the **library** reporter (not the tool) fails three report tests. I could not verify whether the render tool exposes an output-dir argument, which would make that confinement look required | low–medium |
| test_upload_api.py (4) | upload streaming and size limits | out of scope; untouched | no | low |
| test_loop_helpers.py: estimate/microcompact/collapse/fix_pairs/is_success | pure helpers | untouched | no | low |
| test_loop_helpers.py::TestNormalizeToolRunDir::test_preserves_absolute_run_dir | the loop's run_dir mapper passes `/var/tmp/custom_run` through unchanged | **none**. It pins the exact pass-through that the instruction ("must be inside run storage") makes unsafe | **yes**. A loop-level fix that validates in the mapper and returns an error result is correct by the instruction and fails this test. The other three TestNormalizeToolRunDir tests use `/tmp/run_123` as the memory run dir; they fail too if the mapper validates its output | **high** |
| test_path_safety.py::TestSafePath (7) | `safe_path(p, tmp_path)` accepts any workdir; module-level `from … import safe_path, safe_user_path` | none (internal helper API) | **yes**. (a) A fix that adds the run-storage check inside the shared workspace helper (and exempts skills) is correct and fails every case, because tmp_path is outside run storage. (b) A fix that renames or removes the broker-file helper breaks module import, so every case errors | **medium** |

## 2. Leniency

| Property / trap | Most plausible wrong fix | Caught? |
|---|---|---|
| T1 document reader | check only absolute paths; or fail open when the env var is unset | yes: test_document_relative_to_working_directory, test_document_absolute_path_in_home (sf-unset-config-fail-open, sf-check-differs-from-open) |
| T2 broker-file validator (HOME ∪ CWD) | patch only the document reader | yes: test_trade_statement_* and test_shadow_profile_* (sf-document-only, sf-no-broker-file-roots) |
| T3 workspace tools plus loop producer | confine `path` to run_dir but trust run_dir; check only absolute run_dir in the loop; raise instead of returning an error | yes: read/write/edit_file_with_workspace_*, relative_climbing_out (sf-no-run-dir-file-tools, sf-loop-absolute-only, sf-loop-raises, sf-reads-only) |
| T4 pattern/backtest | treat them as non-readers and skip them | yes: test_pattern_scan_on_other_directory, test_backtest_on_other_directory (sf-no-analysis-run-dir) |
| T5 factor analysis | skip it entirely; or check output only | yes: test_factor_inputs_from_home, test_factor_output_to_other_directory (sf-no-factor, sf-factor-output-only) |
| T6 symlink | lexical normalisation without resolving links | yes: test_document_symlink_in_upload_area_pointing_outside (sf-lexical-no-symlinks) |
| T7 prefix | `str.startswith(root)` | yes, for configured dirs only: test_document_sibling_of_configured_directory (sf-prefix-startswith) |
| Refuse-all / over-tight | refuse absolute paths; refuse `..`; run storage only; check inside the shared helper | yes: functional (ff-refuse-all, ff-no-absolute-paths, ff-no-dotdot, ff-run-storage-only, ff-shared-helper-run-roots) |

Wrong fixes that no test catches:
- A startswith check on the **run storage** root (for example `/app/agent/runs_x` accepted). T7 is tested only against a configured directory.
- Resolving links in the document path but checking broker-file, factor-input or configured-dir paths lexically. The only symlink test goes through the document reader and the upload area.
- `..` or symlink escapes through write_file/edit_file/pattern/backtest via a relative run_dir. Only read_file has a relative climbing test; the loop canonicalises run_dir, so this is low impact.
- Tools not exercised at all: run_shadow_backtest, render_shadow_report (any output or journal path arguments, unverified), and the MCP transport.
- Allowing all of `~/.vibe-trading/` (shadow profiles and other app state) as a file root.
- A fix that confines the backtest runner to `agent/runs` only and so breaks real shadow backtests in `~/.vibe-trading/shadow_runs`. This is a functional regression no test catches; the oracle allows that root but the instruction never names it.

## 3. Hints in instruction.md

| Quote | Issue | Proposed wording |
|---|---|---|
| "A directory whose name merely starts with the name of an allowed directory is not inside it." | Names trap T7 almost verbatim | Remove. The test stays fair on standard expert knowledge: containment is per path component |
| "whatever the spelling: absolute or relative paths, `~`, `..` segments, or links that point somewhere else." | Enumerates the tested variant list, including T6 | "whatever the path's spelling or wherever it ultimately resolves." |
| "(a file to read, a workspace to work in, a place to write output)" | Paraphrases the three argument classes (file_path / run_dir / output_dir) and points at T3–T5 | Acceptable as scope, but more neutral wording is "(any file or directory argument)". Keep "A directory a tool is told to work in or write into must be inside run storage": it is a spec the tests need |
| "including when the model names the workspace relative to the current run … or by its absolute path" | Describes the loop mapper (T3 producer) | Keep. It is needed for fairness of test_read_file_with_relative_and_absolute_workspace |
| `VIBE_TRADING_ALLOWED_FILE_ROOTS` | Names a mechanism | Keep. It is an operator interface the tests require |

No flaw count is given. File names and function names are not mentioned.

## 4. Realism

T1–T4 are published fix sites in unmodified upstream code at the pinned commit. T5 is real upstream code, unchanged on main. T6 and T7 are shapes, not planted code. There are no injected siblings: the Dockerfile clones the pinned commit as-is. Every trap is reached through the real path (AgentLoop with build_registry and POST /upload). Nothing looks contrived.

Note: the oracle allows roots the instruction never names (CWD/uploads, CWD/data, CWD/runs, ~/.vibe-trading/{uploads,imports,shadow_runs}, VIBE_TRADING_ALLOWED_RUN_ROOTS). Tests neither require nor forbid them, so this is consistent, but it is worth knowing.

## 5. Verdict: NOT READY

Required changes:
1. **Project tests:** remove `test_loop_helpers.py::TestNormalizeToolRunDir` (at least `test_preserves_absolute_run_dir`) from the graded set. It pins the unsafe pass-through. The loop "drop it" variants are already caught by security tests (sf-loop-absolute-only, sf-loop-raises) or are acceptable refusals.
2. **Project tests:** remove `test_path_safety.py::TestSafePath` from the graded set. It pins an internal helper's signature and envelope, and a module-level import of the broker helper. The hidden skill-docs test already covers over-tightening of that helper.
3. **Hidden functional tests:** make the configured-directory tests independent of when the product reads its configuration. Either run each `call_tool` that sets `VIBE_TRADING_ALLOWED_FILE_ROOTS` or `HOME` in a fresh subprocess with the environment set before import, or set the variable before the first product import (for example a separate pytest invocation, as test.sh already does for the project tests). Otherwise a correct import-time configuration read scores 0.
4. **instruction.md, add:** "Some existing project tests exercise tools on files outside these areas or assert the previous behaviour; such failures are expected and must not be resolved by widening the areas." Without it the solver has to choose between the visible test_doc_reader failures and a correct boundary.
5. **instruction.md, remove** the prefix sentence (T7 hint). Replace the spelling list with "whatever the path's spelling or wherever it ultimately resolves."

Recommended, not blocking: add a security test for a run-storage sibling prefix (for example `runs_evil`) and one for a symlinked broker-file or factor input. Confirm from source whether the render_shadow_report tool takes an output directory, and test it if it does.
