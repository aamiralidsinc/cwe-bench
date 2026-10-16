# Stage 2 - Screening

Stage 2 removes mined candidates that cannot become a fair, runnable task. It rejects fixes that are too old, fixes that are not real source changes, fixes that are too small or too large, and repositories that are too large or have no build manifest or tests. Each surviving candidate gets a ranking score, and at most N candidates are kept per repository. All data comes from the GitHub REST API, with responses cached on disk. Nothing is cloned, and "buildable" here is only a structural check of the file tree; the real Docker build happens later (`src/stage2_screening/screener.py`, module docstring).

## Inputs and outputs

| What | Path / format |
|---|---|
| Candidates (input) | `data/01_mined/osv_candidates.json` (`vulnerabilities` list from stage 1) |
| Accepted (output, cumulative) | `data/02_screened/screened.json`: `{generated_at, count, vulnerabilities}`; each record is the stage-1 record plus a `screening` object |
| Rejected (output, cumulative) | `data/02_screened/rejected.json`: `{osv_id: [reason, ...]}` |
| GitHub response cache | `data/.cache/gh/{commit_<sha>, compare_<a12>_<b12>, repo_<owner>__<repo>, tree_<sha>}.json` (`GitHubClient.get_json`) |
| Learned prior (input) | `data/knowledge/task_outcomes.jsonl` (`knowledge.load_priors`) |
| State | `data/pipeline_state.sqlite3`, stage `stage2_screening`, key = `osv_id` |

## How it works

1. `screen` loads the candidates. If there are none, it returns exit code 2.
2. It keeps only the records for which `state.should_process("stage2_screening", osv_id, 3)` is true.
3. The cutoff is `--published-after`, or `PUBLISHED_AFTER` if the flag is not given. The priors are loaded once with `knowledge.load_priors(cfg)`.
4. Records are screened in a thread pool (`--workers`). For each record, `work` runs these checks in order:
   1. reject if the advisory `published` date is before the cutoff;
   2. `screen_one` fetches the fix commit, or the compare range `pre_patch...fixed` when `len(fix_commits) > 1`;
   3. reject if the earliest author/committer date across those commits is before the cutoff;
   4. `evaluate_diff`;
   5. fetch `/repos/{owner}/{repo}` and check the size;
   6. fetch the recursive tree at `pre_patch_commit` and run `evaluate_tree`;
   7. compute `score + prior_bonus`.
5. Errors are handled per record:
   - `PermanentError` (HTTP 404, 409, 410, 422, 451): `REJECTED` with reason `github: ...`;
   - `TransientError` or any other exception: `FAILED`, retried on the next run while attempts < 3.
6. The new results are merged into the previous `screened.json`: records rejected in this run are removed, and newly accepted ones are added or replaced.
7. `apply_repo_cap` sorts all records by stored `score` (highest first) and keeps at most `--max-per-repo` per `repo_url` (compared in lower case). The dropped ones are recorded as `repo cap reached` and marked `REJECTED`.
8. Kept records are marked `DONE` with payload `{score}`. `screened.json` is written atomically and `rejected.json` is merged and written. The return code is 0 if any record is kept, otherwise 1, which stops `run_pipeline.py`.

## Rules and techniques

**Rejection rules.** The reason strings come from the code. Rules in one group can add several reasons at once.

| Check | Rule | Function |
|---|---|---|
| Advisory age | `published[:10] < cutoff` -> "advisory published ..., before ..." (a missing date counts as `9999`, so the record passes) | `screen.work` |
| Fix age | earliest commit date `< cutoff` -> "fix committed ..., before ..." | `screen_one` |
| Diff file count | `>= 300` files -> "diff too large (>= 300 files)", because GitHub truncates the list at 300 | `evaluate_diff` |
| Empty diff | no files -> "empty diff" | `evaluate_diff` |
| Whole-diff size | sum of `changes` over all files (tests and fixtures included) `> 2500` -> "whole fix diff too large" | `evaluate_diff` |
| No source file | only manifest (+test) -> "dependency/manifest-only change"; only docs (+test) -> "documentation-only change"; only manifest/docs/config/generated/test -> "non-code change ..."; anything else -> "no source file in a supported language for <eco>" | `evaluate_diff` |
| Template-dominated | template lines `>` source lines -> "fix lives mostly in code-generation templates" | `evaluate_diff` |
| Too small / too large | source lines `< --min-lines` (4) -> "trivial fix"; `> --max-lines` (400) -> "fix too large" | `evaluate_diff` |
| Repo size | GitHub `size` (KB, includes history) / 1024 `> --max-repo-mb` (150; 0 = no limit) -> "repo too large for local runs" | `screen_one` |
| Root manifest | none at repo root -> "no root build manifest for <eco> (monorepo or unusual layout)" | `evaluate_tree` |
| Repo tests | 0 test files and the tree is not truncated -> "no test files found in repo" | `evaluate_tree` |
| Repo cap | more than `--max-per-repo` (3) accepted records for one repo -> "repo cap reached (3 per repository)" | `apply_repo_cap` |

**File classification** (`src/common/classify.py: classify`). Rules are checked in this order; the first match wins:
- `generated`: `node_modules`, `vendor`, `_vendor`, `third_party`, `dist`, `build`, `*.min.js` / `*.min.css`, `.map`, `.snap`;
- `test`: matches `TEST_PATH_RE`;
- `manifest`: a name in `MANIFEST_NAMES`, or `requirements*.txt|.in`, or `constraints*.txt`;
- `docs`: `.md`, `.rst`, `.txt`, `docs/`, `examples/`, `README`, `CHANGELOG` and similar;
- `source`: extension `.py` for PyPI, or `.js .mjs .cjs .jsx .ts .tsx` for npm;
- `config`: matches `CONFIG_RE`;
- everything else: `other_code`.

Source lines are additions + deletions over `source` files only.

**Template-dominated fix detection.** `TEMPLATE_RE` matches the extensions `.ejs .hbs .handlebars .mustache .jinja .jinja2 .j2 .njk .tmpl .tpl .liquid .eta` (case-insensitive). Template lines are additions + deletions over matching files. The rule only runs when the diff has at least one source file. The reason given in the code: a code generator's fix mostly in templates can only be checked with text checks bound to the implementation, not through a real entry point.

**Tree checks** (`evaluate_tree`):
- Root manifests are `pyproject.toml`, `setup.py`, `setup.cfg`, `requirements.txt` or `requirements*.txt` for PyPI, and `package.json` for npm.
- Test files are matched by `TEST_FILE_RE`:
  - PyPI: `test_*.py`, `*_test.py`, `conftest.py`;
  - npm: `*.test|spec.[cm]?[jt]sx?`, `__tests__/`, `test(s)/*.[cm]?[jt]sx?`.
- `has_dockerfile` is recorded for information only.

**Score formula** (`score`). Variables: F = number of source files, D = number of source directories, L = source lines, T = `test_files_in_repo`.

```
score = 8 * min(F, 8)
      + 6 * min(max(D - 1, 0), 4)
      + (10 if 100 <= L <= 400 else 5 if 40 <= L < 100 else 0)
      - (25 if F <= 3 and L <= 35 else 0)
      + (3 if T >= 5 else 0)
stored score = score + prior_bonus
```

The base score ranges from -17 to 101. The docstring explains the calibration (from `skills/lessons_learned.md`): DeepSeek solved every fix of 5 or fewer source files, the only task both models failed spanned 8 files / 174 lines / 4 dirs, and none of the 8 fixes of 3 or fewer files and 35 or fewer lines gave a usable task. Stage 3 re-ranks with the current `score()` on the stored diff facts plus the stored `prior` (`src/stage3_task_builder/__init__.py: current_score`). The repo cap, however, uses the stored score.

**Learned prior** (`knowledge.load_priors`, `knowledge.prior_bonus`):
- Input rows are those in `task_outcomes.jsonl` with `stage == "stage5_evaluator"` and a `pattern` other than `unknown`. Only the latest row per `osv_id` is used.
- A hit is `pattern == "both_fail"`. The overall rate is hits / total, and a hit rate is computed per CWE.
- For the CWEs of a candidate that have n >= 3 outcomes: `bonus = clamp(round(25 * (mean(cwe_rate) - overall)), -10, +15)`.
- The bonus is 0 if there are no outcomes or no CWE with n >= 3.

**Stored per accepted candidate.** All stage-1 fields, plus `screening`:

| Key | Content |
|---|---|
| `diff` | `counts` per class, `source_files`, `test_files`, `source_lines`, `source_dirs`, `total_changed_lines`, `template_lines` |
| `repo` | `truncated`, `root_manifests`, `test_files_in_repo`, `has_dockerfile` |
| `score` | base score + prior |
| `prior` | the prior bonus |
| `fix_commit_date` | the earliest commit date used for the cutoff |

## Configuration

| Key / flag | Default | Effect |
|---|---|---|
| `GITHUB_TOKEN` (env) | unset | Auth. Without it, a warning says GitHub allows 60 calls/hour. |
| `PUBLISHED_AFTER` (env) / `--published-after` | `''` | Date cutoff; the flag overrides the env value. Project setting: `2026-08-01` (`.env.example`). |
| `MAX_REPO_MB` (env) / `--max-repo-mb` | 150 | Repo size limit; 0 disables it. Read with `os.environ` in `parse_args`. Project setting: `400` (`.env.example`). |
| `--min-lines` / `--max-lines` | 4 / 400 | Source-line bounds. |
| `--max-per-repo` | 3 | Repo cap. |
| `--workers` | 4 | Thread pool size. |
| `--github-rps` | 3.0 with token, 0.5 without | Request rate. |
| `--ignore-state` | off | Screen every record and write no state. |
| `--input` / `--output` / `--rejected` | paths above | File locations. |

`run_pipeline.py --stage 2` passes only `--workers`, `--published-after` and `--ignore-state` (`src/stage2_screening/__init__.py: run`). For the other flags, run `python -m src.stage2_screening.screener`. `--reset-state` clears all `stage2_screening` rows.

## Code map

| File | Function | Role |
|---|---|---|
| `src/stage2_screening/screener.py` | `GitHubClient.get_json` | Cached GitHub GET: 4 attempts, rate-limit sleep, permanent vs transient errors. |
| | `summarize_files` | Per-class file lists, source lines, source dirs. |
| | `evaluate_diff` | Diff rejection rules. |
| | `evaluate_tree` | Root manifest and test-file checks. |
| | `score` | Ranking formula. |
| | `screen_one` | Per-record pipeline: dates, diff, size, tree, score. |
| | `apply_repo_cap` | Keep the best N per repository. |
| | `screen` | Orchestration, merge, state, output. |
| | `parse_args`, `main` | CLI and lifecycle. |
| `src/common/classify.py` | `classify` | Path classes. |
| `src/common/knowledge.py` | `load_priors`, `prior_bonus` | Learned per-CWE prior. |
| `src/stage1_mining/osv_miner.py` | `make_session`, `RateLimiter`, `GitHubResolver._is_rate_limited` / `_sleep_until_reset` | Reused HTTP helpers. |

## Known limitations

- The GitHub cache under `data/.cache/gh` never expires. Changes on GitHub after the first fetch (for example a repo growing) are not seen.
- `REJECTED` is terminal. A record dropped by the repo cap stays rejected even if the higher-scored records for that repo are later removed.
- `rejected.json` only grows. An ID rejected in an earlier run and accepted later stays in it: at the time of writing, 92 of the 161 IDs in `screened.json` also appear in `rejected.json`. Why each one was rejected and then accepted was not verified.
- The two date checks treat a missing date differently: stage 1 skips an advisory with no `published` date, while stage 2 lets it pass.
- `skills/adversarial_research.md` section 6 also lists binary changes, a pre-patch tree that already contains the fix, and "runnable offline" tests. `screener.py` does not implement these checks.
- When the tree is truncated, a repo with no visible test files is not rejected.
- No record in the current `screened.json` has a `template_lines` key, and 38 records have no `prior`. They were screened before those rules existed.
