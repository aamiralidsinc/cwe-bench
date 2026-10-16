# Stage 3 - Task builder

Stage 3 turns screened candidates into task folders under `data/03_environments/<OSV-ID>/`. It does four things in order. It picks the best-ranked candidates (pilot mode). It checks out each repository at the pre-patch commit, with the human fix kept outside `repo/` (`environment_builder.py`). It proves in Docker that the repository installs (`build_check.py`). Then it asks Claude (Opus) to write the agent-visible bug report, the hidden pytest suite and three "check patches" that stage 4 runs (`task_generator.py`). Every output the model returns goes through deterministic validators. Rejected output is sent back to the model with the reason. Candidates that keep failing are retired, and the knowledge base records why, so later rounds learn from it.

## Inputs and outputs

| What | Path / format |
|---|---|
| Candidates (input) | `data/02_screened/screened.json` (`{"vulnerabilities": [...]}`); `data/01_mined/osv_candidates.json` only with `--allow-unscreened` (`__init__._input_file`) |
| Pilot subset (intermediate) | `data/.cache/stage3_subset.json` (`_limit_to_top_n`) |
| Pre-patch checkout | `<env>/repo/`, a single `Snapshot` commit, so the fix history is unreachable (`environment_builder.sanitize_history`) |
| Answer key | `<env>/oracle_solution.patch` = `git diff --binary --full-index pre..fixed`, with generated-file chunks removed (`build_environment`, `strip_generated`) |
| Build-check cache | `<env>/build_check.json` `{ok, detail}`; transient results are not cached (`build_check.run_checks`) |
| Build-timeout strikes | `<env>/build_timeouts.txt` (integer) (`_buildable_ids`) |
| Bug report | `<env>/instruction.md`. It is written last, and its presence marks completion (`task_generator.process`) |
| Hidden tests | `<env>/hidden_tests.py` |
| Task metadata | `<env>/task_metadata.json` `{entry_point, techniques[]}` |
| Check patches | `<env>/check_patches/{shallow,removal,alternative}.patch` (unified diffs) |
| Generation metadata | `<env>/generation_meta.json` (model, backend, tokens, attempts, models tried) |
| Diagnostics / markers | `generation_rejected_<ts>_<n>.txt`, `generation_refused_<ts>_<n>.txt`, `generation_unsuitable.txt`, `safeguards_flagged.txt` |
| State | `data/pipeline_state.sqlite3`, stage key `stage3_task_builder` (DONE / FAILED / REJECTED) |
| Knowledge rows | `data/knowledge/task_outcomes.jsonl` via `knowledge.record_outcome` |

## How it works

1. **Load candidates** (`_input_file`). If `screened.json` is missing, the stage exits with code 2 unless `--allow-unscreened` is set.
2. **Pick the pilot subset** (`_limit_to_top_n`, only with `--max-tasks/--pilot/--batch` or `--only`). With `--only`, those IDs are used as given. Otherwise:
   - Drop candidates that already have `instruction.md` + `hidden_tests.py`.
   - Drop candidates with `>= MAX_REFUSALS` (3) `generation_refused_*.txt` files.
   - Drop candidates whose stage 3, 4 or 5 state is `rejected`, `rejected_too_easy`, `failed_oracle` or `accepted`.
   - Skip whole repositories that already proved unusable: any stage-3 REJECTED record whose detail contains `safeguards`, `docker build`, `build timed out` or `unbuildable` excludes every candidate with the same `repo_url`.
   - Sort by `current_score(r) + selection_adjustment(...)[0]` in descending order.
   - Take at most one candidate per repository until N candidates are picked.
3. **Build environments** (`environment_builder.main`, `--workers` = the pipeline's `--workers`, default 4):
   - Validate each entry (`validate_entry`): safe `osv_id` (`^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$`), a `https://github.com/owner/repo` URL, two different 40-character SHAs.
   - An entry whose patch already exists and is non-empty is skipped (`already_done`).
   - Fetch both commits shallowly by SHA, falling back to a full fetch (`git_tools.fetch_commits`).
   - Diff, strip generated chunks, and fail on an empty diff. Check out the pre-patch commit and replace `.git` with one snapshot commit.
   - The result is moved into place atomically from `.<id>.partial`.
4. **Fail-fast build check** (`_buildable_ids`). It covers pending IDs, meaning those that have a patch, have no task yet and are not stage-3 REJECTED.
   - It is skipped with `--skip-build-check` or `--dry-run`, and also (with a warning) when `docker info` fails.
   - Up to 3 Docker builds run in parallel. Results are handled as follows:
     - ok: the ID goes on to generation.
     - Transient timeout: one strike, and the candidate is retired at `MAX_BUILD_TIMEOUTS` (2).
     - Other transient error: retried on the next run.
     - Anything else: REJECTED, plus an outcome row `rejected_unbuildable`.
5. **Generate** (`task_generator.main`). Workers = `min(--workers, 3)`. Each environment gets `build_context`, and then `generate` makes up to 3 attempts (+1 on a fallback switch).
   - Each attempt is validated (see the validator table). The files are written atomically, with `instruction.md` last.
6. **Record state** (`_record_state`). An environment with both task files is marked DONE if `should_process` allows it.
7. **Record failures** (`_record_failures`), for every ID passed to the generator that still has no `instruction.md`:
   - `safeguards_flagged.txt` present: REJECTED (`rejected_safeguards_flagged`).
   - `generation_unsuitable.txt` present: REJECTED (`rejected_unsuitable`).
   - `>= 3` refusal files in total: REJECTED (`rejected_classifier_blocked`).
   - Otherwise this run is counted (previous FAILED attempts + 1). The candidate is REJECTED at `MAX_GEN_FAILURES` (3) runs (`rejected_generation_failed`), and FAILED before that.

## Rules and techniques

**Selection and build**
- `current_score`: recomputes `src/stage2_screening/screener.score(diff, repo)` from the stored `screening.diff` facts and adds the stored `screening.prior`. If no `source_files` are stored, it falls back to the stored `screening.score`.
- `selection_adjustment` (`knowledge.py`) is clamped to [-30, +30]. It applies two adjustments:
  - Per CWE family with `n >= 3` evaluated tasks: `25 * broke/n`, minus 15 if `broke == 0` and `n >= 4`. Families are averaged.
  - Same package/repo seen before: +5 if any task there broke a model, otherwise -15.
- `learned_ranking` counts graded tasks from `results_report.collect`. A task counts as "broke" when any model's verdict is `failed` or `failed+timed_out`.
- Strict build Dockerfile (`build_check.PY_STRICT` / `NODE_STRICT`). Unlike the task image, install failures are not tolerated.
  - PyPI: `FROM python_base_image(repo)`, `SETUPTOOLS_SCM_PRETEND_VERSION=999.0.0 PBR_VERSION=999.0.0`, then `(UV_WORKSPACE_INSTALL) || pip install -e . || pip install -r requirements.txt`.
  - npm: `node:22-bookworm` + `NODE_INSTALL` (bun / pnpm / yarn / npm, frozen lockfile first).
  - A `Dockerfile.override` in the env folder is used as-is.
- `python_base_image` (`harbor_packager.py`) reads only `requires-python` in `pyproject.toml`; with no match it uses `python:3.11-slim-bookworm`.
  - Lower bound: the largest `>=`/`~=`/`==` version, or `>X.Y` → `X.(Y+1)`, never below 3.11, then capped at 3.13.
  - Upper bound: a `<X.Y` bound gives `X.(Y-1)`, and `<=X.Y` keeps `X.Y`.
- `UV_WORKSPACE_INSTALL` applies only when `pyproject.toml` has `[tool.uv.workspace]` and `uv.lock` exists.
  - It installs uv, sets `UV_PROJECT_ENVIRONMENT=/usr/local`, then runs `uv sync --frozen --inexact --all-packages --all-extras --all-groups`. If that fails, it retries without extras/groups.
- Build check limits: a 1800 s timeout. Errors that match `TRANSIENT_RE` (network/registry/daemon) are retried 3 times, sleeping 30 s × attempt.

**Prompt construction** (`build_context`, `USER_PROMPT_TEMPLATE`)
- The system prompt (`SYSTEM_PROMPT`) frames the work as defensive QA. It asks for the bug report, the hidden suite and three candidate fixes, and says tests use harmless sentinels and run offline.
- User prompt sections, in order:
  - Template sections: vulnerability metadata, the oracle patch, pre-patch sources of the changed non-test files, callers, the repository map, package manifests, other context (touched test files, top-level entries), the project's test examples, artifact specs 1-3, the four "hard rules", the entry-point rule and the strict output format.
  - Appended after the template: `stage4_checks_text()` (the rubric criteria and the execution checks), then `regeneration_feedback()`, then `LESSONS_TEXT`.
- Size caps:
  - Source files: 40,000 characters per file and 160,000 in total.
  - Repo map: 14,000.
  - Callers: 60,000 in total and 12,000 per file; files over 400 KB are skipped.
  - Manifests: 6,000.
  - Test examples: 12,000 (up to 2 `conftest.py` under 40 KB, plus the most related test file under 60 KB).
  - A patch over 80,000 characters raises "too large" and writes `generation_unsuitable.txt`.
- `LESSONS_TEXT` = `knowledge.lessons_for_prompt`, appended in this order:
  - `skills/task_design_techniques.md` (≤ 9,000 characters)
  - `data/knowledge/model_failure_map.md` (≤ 5,000)
  - `data/knowledge/technique_scoreboard.md` (≤ 4,000). This file and the failure map are written by `results_report.py`.
  - `failure_analysis_lessons`: from `data/knowledge/failure_analyses/*.md`, the Summary plus the `#### Weakness` / `#### Task-design lessons` sections, tasks that broke both models first, ≤ 7,000.
  - `skills/lessons_learned.md` (≤ 8,000)

**Rules the generator is told to follow** (prompt text)
- Report:
  - 150-400 words in Markdown with a title, in the model's own words.
  - It must not name files, paths, modules, changed functions or classes, line numbers, or the CVE/GHSA ID.
  - It must not prescribe the fix or describe the hidden variants.
  - Every behaviour a functional test needs must be derivable from the report.
- Tests:
  - Pure pytest, deterministic and offline, using `tmp_path` and black-box public entry points.
  - They must never import or assert anything the patch adds, and never assert exact error text.
  - Non-Python projects are driven through `subprocess` calling `node`.
  - The oracle must pass every test, and the pre-patch code must fail every `test_security_*`.
- Counts: `test_security_*` ≥ 3 (ideally 4-8), with variants beyond the report. `test_functional_*` ≥ 3 (ideally 4-8), with legitimate uses near the boundary.
- Hard rules:
  1. Implementation-agnostic.
  2. Solvable from the report.
  3. The harness must run (build the app once per module where global state exists).
  4. JS/TS projects are tested from source, never `dist/`.
- Output: exactly four blocks: `<instruction_md>`, `<hidden_tests_py>`, `<task_metadata_json>` (`entry_point`, `techniques`) and `<check_patches_json>` (`shallow` / `removal` / `alternative`, each a list of `{file, search, replace}`).

**Validators applied to every attempt** (`generate`, in order). Any failure is `GenerationInvalid`, and the message is sent back to the model.

| Check | Rule (function) |
|---|---|
| Truncation guard | `output_tokens >= 0.98 * max_tokens` (62,720 of 64,000) rejects the attempt; the API backend also rejects `stop_reason == "max_tokens"` (`generate`, `ApiBackend.complete`) |
| Blocks present | both `<instruction_md>` and `<hidden_tests_py>`; a ```` ``` ```` fence around the code is stripped (`extract_blocks`) |
| Auto-repairs | `ensure_pytest_import` adds a missing `import pytest`; `no_silent_skips` turns `pytest.skip(` into `pytest.fail(`, `importorskip("x")` into `importlib.import_module("x")`, and removes `skip`/`skipif` markers and `allow_module_level=True` |
| Metadata | valid JSON; `entry_point` is a string of 5-300 characters; `techniques` keeps integers 1-49 only (`extract_metadata`) |
| Advisory copy | no shared 8-word n-gram with the advisory summary + description (`validate_instruction`, `_ngrams`) |
| Path leak | no changed-file path, and no changed-file basename of ≥ 4 characters, as a substring of the lowercased report (all changed files) |
| Identifier leak | `identifier_leaks` against `localizing_identifiers(patch)`: source-file stems and defined/edited names (≥ 4 characters, `GENERIC_NAMES` excluded) from non-test source files. Code-like names (camelCase, `_`, digits, inner capital) leak as whole words; plain words leak only inside backticks or as `name(` |
| Line numbers | regex `line(s) N`, `.ext:N` or `L` followed by 2+ digits |
| Length | ≥ 60 words |
| Test suite | parses; ≥ 3 `test_security_*` and ≥ 3 `test_functional_*` function names; imports pytest; no remaining `importorskip`, `pytest.skip(`, `mark.skip(if)`, `xfail` or `allow_module_level`; never mentions `oracle_solution` (`validate_tests`) |
| Check patches | valid JSON; all three kinds are non-empty lists. Each edit has string `file`/`search`/`replace`; it targets a non-test, existing file without `..`; and `search` occurs exactly once (after the earlier edits). The diff is non-empty and passes `git apply --check` on `repo/`; the three diffs differ (`extract_check_patches`, `edits_to_patch`) |

**Refusals, fallback, safeguards**
- A refusal is a `GenerationInvalid` whose raw text matches `REFUSAL_RE` in its first 600 characters and lacks `<instruction_md>` in its first 200.
  - It is saved as `generation_refused_*.txt` and not treated as feedback.
  - The next attempt resends the original prompt plus `REFUSAL_RETRY_NOTE`.
  - On the first refusal by the primary model, the run switches to `--fallback-model` (default `claude-opus-4-8`), and the attempt budget grows by 1.
- If every attempt was a refusal, the message is "declined by the safety filter on all N attempts".
- A refusal reported by the API (`stop_reason == "refusal"`) or as a CLI error is a `RuntimeError`, not `GenerationInvalid`. It ends the candidate for this run as an "API FAILURE" without a fallback.
- `SafeguardsFlagged` is raised when the CLI error contains `safeguards flagged` or `legal/aup`.
  - It writes `safeguards_flagged.txt` and sets `ABORT`, so no further folders run in this process.
  - There is no retry and no fallback. Later, `_record_failures` retires the candidate, and step 2 skips the repository.
- `QuotaExhausted` (`usage limit`, `limit reached`, `quota`, `credit balance`) also sets `ABORT`.

**Regeneration rounds** (`regeneration_feedback`). When stage 4 archived earlier attempts to `attempts/round_N`, only the last round is used.
- It adds the rubric's `blocking_issues` (if the rubric failed) and `execution_feedback.txt`.
  - Feedback starting with `FIX-CHECK` is included up to 4,000 characters.
  - Other feedback is shown as real pytest output (≤ 3,500 characters) plus harness advice.
- It also includes the previous `instruction.md` and `hidden_tests.py`, under "REVISION REQUIRED".

**Curated techniques** (`skills/task_design_techniques.md`, injected verbatim). Grading contract: only reward 1.0 is a solve; partial and over-broad fixes are failures.
1. Unnamed sibling path (second entry point / code path / round-trip).
2. Already-protected-looking code.
3. Fix across a layer boundary.
4. One test per variant.
5. Boundary-hugging functional tests.
6. Behavioural report, no localization.
7. Parallel implementation.
8. Second public API / input-shape variants.
9. A "must keep working" clause that argues against the fix.
10. Prefer big fixes (≥ 6 source files, ≥ 100 lines, ≥ 3-4 directories).

The file also contains these rule groups, which apply in addition to the techniques:
- Check-patch meaning.
- Fairness rules: never test a number the report does not state; variants must share the root cause; "must keep working" must be true today; no races, network or randomness.
- Answer-key hygiene.

## Configuration

| Key / flag | Default | Effect |
|---|---|---|
| `ANTHROPIC_MODEL` / `--model` | `claude-opus-5-5` | Generation model (`Config.load`, `task_generator.DEFAULT_MODEL`) |
| `GEN_FALLBACK_MODEL` / `--fallback-model` | `claude-opus-4-8` | Model used after a refusal; `''` disables the fallback |
| `TASK_GEN_BACKEND` / `--backend` | `cli` | `cli` = headless `claude -p` (tools off, empty temp cwd, API keys stripped); `api` = Anthropic SDK (needs `ANTHROPIC_API_KEY`) |
| `CLAUDE_BIN` / `--claude-bin` | `claude` | CLI binary |
| `CWE_DATA_DIR` / `--data-dir` | `./data` | Data root |
| `--pilot`/`--max-tasks N`, `--batch N` | none | Pilot subset size (`--batch` sets it to N) |
| `--only ID...` | none | Restrict to these IDs (ranking is skipped) |
| `--allow-unscreened`, `--skip-build-check`, `--dry-run` | off | Use stage 1 output / skip Docker check / print the prompt with no model call |
| `--workers` | 4 | Env builder workers; generator uses `min(workers, 3)` |
| task_generator only: `--max-tokens`, `--max-attempts`, `--timeout` | 64000, 3, 3600 s | Not passed by `run_pipeline.py`, so the defaults apply there |
| env builder only: `--timeout`, `--retries`, `--keep-git-history` | 900 s, 3, off | Per git command / network retries / keep real history (leaks the fix) |

## Code map

| File | Key functions |
|---|---|
| `src/stage3_task_builder/__init__.py` | `run` (orchestration); `_limit_to_top_n` (selection); `current_score`; `_buildable_ids` (build check + strikes); `_record_state`; `_record_failures`; `refusals` |
| `src/stage3_task_builder/environment_builder.py` | `load_entries`/`validate_entry`; `build_environment` (fetch, diff, checkout, atomic promote); `strip_generated`; `sanitize_history` |
| `src/stage3_task_builder/build_check.py` | `docker_available`; `check_buildable` (strict image, retries); `run_checks` (cache); `TRANSIENT_RE` |
| `src/stage3_task_builder/task_generator.py` | `build_context` and its section builders; `generate` (attempt loop, refusal/fallback); the validators listed above; `process` (write files, safeguards/quota abort) |
| `src/common/knowledge.py` | `learned_ranking`, `selection_adjustment`, `lessons_for_prompt`, `failure_analysis_lessons`, `record_outcome` |
| `src/common/llm.py` | `CliBackend.complete` (retries 3×, 5 s × 2^n backoff on transient errors); `SafeguardsFlagged`, `QuotaExhausted`; `normalize_model` |
| `src/stage6_packager/harbor_packager.py` | `python_base_image`, `UV_WORKSPACE_INSTALL`, `NODE_INSTALL`, `DOCKERFILE_OVERRIDE` (shared with the task image) |

## Known limitations

- **Environment-build failures are not recorded.** `environment_builder` only logs them. A candidate whose fetch or diff fails gets no state record, so step 2 can pick it again in every run.
- **Aborted runs count against candidates.** `_record_failures` counts any "no `instruction.md`" outcome as a generation run. That includes quota/safeguards aborts, API failures and context errors, so these can push an unrelated candidate towards `MAX_GEN_FAILURES`.
- **The safety-filter fallback only reacts to refusal text.** It triggers only on a textual refusal. A refusal signalled as an API `stop_reason` or a CLI error ends the attempt loop without one.
- **Regenerated candidates get no priority.** After stage 4 archives a task, it re-enters normal ranking and must win a pilot slot again. Only the last archived round is fed back.
- **Some prompt rules have no validator.** The validator enforces ≥ 60 words, while the prompt asks for 150-400. There is no check for the CVE/GHSA ID appearing in the report.
- **Test-file detection differs between modules.** `task_generator.TEST_PATH_RE` (used for check-patch file rules and the source context) is narrower than `src/common/classify.TEST_PATH_RE`: it lacks `testing/` and `conftest.py`.
- **The technique list is truncated.** It is cut at 9,000 characters (the current file is about 6,400, so this is not an issue today).
- **Garbled comment in `__init__.py`.** The comment on `MAX_BUILD_TIMEOUTS` also carries the comment that belongs to `MAX_GEN_FAILURES`. The behaviour is as described above.
