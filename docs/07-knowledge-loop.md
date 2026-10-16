# Knowledge loop

The knowledge loop turns every evaluation result into guidance for the next generation round. Stage 5 results are read back from the raw trials and condensed into deterministic reports: `C_RESULTS.md`, the model failure map, the technique scoreboard and the ledger. They are also condensed into LLM-written notes: per-task failure analyses and the lessons file. The task generator (stage 3) puts a size-capped bundle of these files into its prompt. Candidate selection in stages 2 and 3 is re-ranked with the measured outcomes. None of this affects a verdict: acceptance stays deterministic (see [05-evaluation.md](05-evaluation.md)).

## Inputs and outputs

| File | Writer (function) | Kind | When it is (re)written | Read by |
|---|---|---|---|---|
| `data/knowledge/task_outcomes.jsonl` | `knowledge.record_outcome` (stages 3, 4, 5, `reverdict`) | deterministic, append-only | every recorded outcome | `update_lessons` (last 150 rows), `load_priors` (stage 2) |
| `data/knowledge/results.md` | `knowledge.append_results` | deterministic, append-only | end of each stage-4 and stage-5 run | humans only |
| `C_RESULTS.md` (project root) | `results_report.main` | deterministic, overwritten | after each task (`refresh_knowledge`) and at the end of each stage-5 run | humans |
| `data/knowledge/model_failure_map.md` | `results_report.main` -> `render_failure_map` | deterministic | same as `C_RESULTS.md` | `lessons_for_prompt` |
| `data/knowledge/technique_scoreboard.md` | `results_report.main` -> `render_technique_scoreboard` | deterministic | same as `C_RESULTS.md` | `lessons_for_prompt` |
| `data/knowledge/ledger.md` | `ledger.main` | deterministic | end of each stage-5 run | humans |
| `data/knowledge/failure_analyses/<ID>.md` | `failure_analyst.analyse` (LLM) or a human | LLM or curated | after each task's evaluation, if the file is absent or still has `AUTO_MARKER` | `failure_analysis_lessons`, `C_RESULTS.md` failure details |
| `skills/lessons_learned.md` | `knowledge.update_lessons` (LLM) | LLM, validated | end of each stage-5 run (unless `--skip-lessons`), or `run_pipeline.py --update-lessons` | `lessons_for_prompt` |
| `data/knowledge/lessons_history/` | `update_lessons` | backups | `lessons_<ts>.md` (previous file) on each accepted rewrite; `rejected_<ts>.md` on each rejected one | humans |
| `data/knowledge/archive/rejected_tasks/<id>/` | `harbor_packager.unpublish` | moved task | `--reverdict --apply` with a non-accepted verdict | none (git-ignored) |
| `skills/task_design_techniques.md` | humans | curated | manually | `lessons_for_prompt`; `results_report.technique_names` (scoreboard, backfill) |
| `skills/PROJECT_CONTEXT.md`, `skills/adversarial_research.md` | humans | curated | manually | not read by code (only cited in comments and docstrings) |
| `<env>/task_metadata.json` `techniques` / `techniques_inferred` | stage-3 generator / `technique_backfill.infer` (LLM) | self-reported / inferred | at generation / on demand | `results_report.task_techniques` |

Other files that exist in `lessons_history/` and `archive/` (`truncated_lessons_*`, `lessons_before_cleanup_*`, `removed_logs_*.tar.gz`, `results_raw_log_*`, `task_outcomes_excluded.jsonl`) are not produced by the current code. They look like manual cleanups. The four current `failure_analyses/*.md` files start with `#### Summary` and carry no `AUTO_MARKER`, so `analyse` treats them as hand-written and never overwrites them.

## How it works

1. **Outcome rows.** Each stage calls `record_outcome`. The row is `{ts, osv_id, stage, status, detail[:600]}` plus `task_features` (CWE, ecosystem, package, repo, sources, severity, fix size) and extras. Stage 5 adds `models`, `model_verdicts`, `pattern`, `task_type`, `entry_point`, `model_results`, and optionally `technique` / `why_easy`. The verdict step adds `failure_classes`.
2. **Per task, after evaluation** (`model_runner.refresh_knowledge`). `failure_analyst.analyse(cfg, id)`, then `results_report.main()`. Follow mode runs this in a single background thread as each task ends. Normal mode runs it for every task after the pool finishes.
3. **End of a stage-5 run** (`model_runner.main`):
   1. `append_results("Stage 5 - DeepSeek / MiMo evaluation", ...)`
   2. `ledger.main()`
   3. `results_report.main()`
   4. `knowledge.update_lessons(cfg, CliBackend(claude, 900 s), --model or ANTHROPIC_MODEL)` if there was work and `--skip-lessons` is not set.
4. **Next stage-2 run.** `load_priors` + `prior_bonus` adjust each candidate's screening score.
5. **Next stage-3 run.** `learned_ranking` + `selection_adjustment` re-rank the candidates. Then `task_generator.main` calls `lessons_for_prompt(Config.load())` once at startup and appends the text to every task's prompt (`feedback = regeneration_feedback(env_dir) + LESSONS_TEXT`).
6. **Optional backfill.** `python -m src.common.technique_backfill [ids]` infers techniques for evaluated tasks that have neither `techniques` nor `techniques_inferred`.

## Rules and techniques

### What the generator reads (`knowledge.lessons_for_prompt`)

Sections are appended in this order. Each is cut by plain slicing at the cap:

| # | Heading in the prompt | Source | Cap (chars) |
|---|---|---|---|
| 1 | `# Task-design techniques (curated - follow them)` | `skills/task_design_techniques.md` | 9000 (`MAX_TECHNIQUES_CHARS`) |
| 2 | `# Which task types each evaluated agent could not repair completely (measured results)` | `model_failure_map.md` | 5000 |
| 3 | `# Which techniques have broken the evaluated agents so far (measured)` | `technique_scoreboard.md` | 4000 |
| 4 | `# Why the evaluated agents failed real tasks (curated from their trajectories - design for these)` | `failure_analysis_lessons()` | 7000 (`MAX_ANALYSIS_CHARS`) |
| 5 | `# Lessons from previous runs (auto-generated from real DeepSeek/MiMo results - follow them)` | `skills/lessons_learned.md` | 8000 (`MAX_LESSONS_CHARS`) |

The maximum total is about 33,000 characters plus headings. Empty or missing files are skipped. `failure_analysis_lessons` keeps, from each analysis, the `#### Summary` paragraph (used as the title) and the `#### Weakness...` and `#### Task-design lessons` sections. Files whose summary mentions "both" in its first 200 characters come first.

### Lessons file (`knowledge.update_lessons`)

- **Input.** The last 150 outcome rows (`max_rows`), reduced to 20 keys and capped at 60,000 characters, plus the current file. If the current file fails validation, a "previous file was damaged" placeholder is sent instead.
- **Prompt rules** (`LESSONS_PROMPT`). Evidence only, with counts like `(n=3)`; `n<3` is marked "tentative". Keep one technique list per model and say which techniques to combine. Add selection hints. Aim for about 4500 characters. Use exactly these 6 sections in order: `## Breaks BOTH models (replicate)`, `## Breaks only DeepSeek (MiMo solves)`, `## Breaks only MiMo (DeepSeek solves)`, `## Solved by both (avoid)`, `## Task-quality pitfalls (rubric / oracle failures)`, `## Selection hints`.
- **Validation** (`lessons_problems`). The text must start with the first section, contain all 6 sections in order and be at most 8000 characters. A response that uses at least 98% of `LESSONS_MAX_TOKENS = 12000` output tokens is also rejected. A rejected text goes to `lessons_history/rejected_<ts>.md` and the old file stays. An accepted text backs up the previous text to `lessons_<ts>.md` and is written atomically (`.tmp` then `replace`).

### Failure analyses (`failure_analyst.analyse`)

- **Trigger.** Runs when some model's verdict for the task is `failed` or `failed+timed_out` (`results_report.collect`). Skipped if the file exists without `AUTO_MARKER` (unless `force`).
- **Evidence per counted failed attempt** (reward < 1.0, not timed out), plus one solving attempt for contrast: reward, failing hidden tests, minutes, the source files changed vs reference-fix files not changed, and the patch (up to 1500 characters per file, 6000 total). The trajectory is condensed (`condense`) to the first 4 steps, the last 3, and every step that mentions a keyword (an untouched fix file, or a word longer than 4 characters from a missed test's name). Each attempt is capped at 12,000 characters, and the whole prompt at 90,000.
- **Model.** `ANTHROPIC_MODEL`, then `GEN_FALLBACK_MODEL` (default `claude-opus-4-8`), via `CliBackend(claude, 1800 s)` with 6000 max tokens. The output must contain `#### Summary` and `#### Task-design lessons`. A `SafeguardsFlagged` error stops the analysis without a retry. The file is written as `AUTO_MARKER` followed by the text from `#### Summary` on. Delete the marker line to keep manual edits.

### Technique scoreboard (`results_report.render_technique_scoreboard`)

- **Inputs.** Technique names come from `skills/task_design_techniques.md` lines `N. **Name.**` (`technique_names`). A task's techniques are `task_metadata.json` `techniques`, else `techniques_inferred`.
- **Outcome per task** (`outcome_class`). `broke_both` if both models `failed`/`failed+timed_out`, `broke_<tag>` if only one did, otherwise `solved` or `no_result`.
- **Baseline.** `base = tagged tasks that broke at least one model / tagged tasks`.
- **Reading.** The first rule that matches wins:

| Order | Condition | Reading |
|---|---|---|
| 1 | uses >= 0.8 x tagged tasks | `BASELINE (in u/n tasks): necessary, not sufficient` |
| 2 | uses < 3 | `too few uses to judge` (+ "but broke both models" if any) |
| 3 | 0 breaks | `WEAK alone: never broke a model - combine with a USE technique` |
| 4 | break rate >= 1.5 x base | `USE: r% break rate vs b% baseline` |
| 5 | otherwise | `neutral: r% break rate` |

The counts are per task. The names of the packages that were broken are appended to each row, and the footer counts the untagged tasks.

### Learned candidate ranking (`knowledge`)

- **Stage 3.** `learned_ranking` covers every evaluated task with at least one graded model. It counts `[tasks, broke]` per CWE family (`results_report.cwe_family`) and per package and repo URL. `broke` means some model's verdict is `failed` or `failed+timed_out`. `selection_adjustment` averages `25*broke/n` over the candidate's families that have `n >= 3`. It subtracts 15 when `broke == 0` and `n >= 4`. It adds +5 if the same package/repo broke a model before, or -15 if it never did. The result is clamped to [-30, +30]. Candidates are sorted by `current_score + adjustment`, with at most one task per repo per batch.
- **Stage 2.** `load_priors` takes the latest stage-5 row per task whose `pattern` is not `unknown`. It computes the overall `both_fail` rate, plus a rate per CWE. `prior_bonus = round(25 * (mean CWE rate - overall))`, using only CWEs with `n >= 3`, clamped to [-10, +15].

### Deterministic reports (`results_report`, `ledger`)

- **Per model, latest run only** (`model_result`, `latest_trials` groups the `-a`/`-b` phases of one run id). The verdict is `solved` (any reward >= 1.0), `failed`, `timed_out`, `failed+timed_out` or `not graded`. Ungraded = no reward, or a non-timeout exception. Existing tests count only if they are in `existing_expected.txt`.
- **Task type** (`task_type`). The CWE family comes from `CWE_FAMILIES` (9 families, else `other`). Breadth is `wide multi-layer fix` if files >= 6 or dirs >= 4, `multi-file fix` if files >= 3, otherwise `local fix`.
- **`C_RESULTS.md` sections** (`render_results` + `render_failure_details`):
  - Title, a generated-at line, and the definitions paragraph.
  - `## Executive summary`: accepted out of trialed.
  - `## All trialed tasks`: `# | Task | Language | CWE | Task type | DeepSeek | MiMo | Final verdict | How it failed | Image build (cached / longest)`.
  - `## What breaks which model`: `Task | Task type | Entry point | Model | Result | How it failed | Other model`.
  - `## Failure details`: one `###` per task a model failed. Accepted tasks come first, then tasks nobody solved, then the rest. Each has task type, entry point and reference-fix files, a per-attempt table (`Model | # | Score | Security | Functional | Existing | Left open | Broke | Source files changed | Time | Turns | Ended`), and the failure-analysis file inlined.
- **Final verdict strings** (`final_verdict`). `**ACCEPTED**`, `REJECTED: <model> solved`, `REJECTED: <model> timed out ...`, `NEEDS REVIEW: ...`, `IN PROGRESS` (state empty, `done` or `failed`), or `REJECTED: <detail>`.
- **`ledger.md`.** Same latest-run rule. A task is `BREAKER` only if both models have graded runs with no solve and the stage-5 state is `accepted`.

## Configuration

| Key / command | Default | Effect |
|---|---|---|
| `ANTHROPIC_MODEL` / stage-5 `--model` | `claude-opus-5-5` | lessons + failure analyses (first choice) |
| `GEN_FALLBACK_MODEL` | `claude-opus-4-8` | fallback for failure analyses and backfill |
| `CLAUDE_BIN` | `claude` | CLI used by `CliBackend` |
| `TIMEOUT_POLICY`, `FULL_BUDGET_SEC` | `exclude`, 7000 | `model_verdicts` and the ledger's timeout counting |
| `--skip-lessons` | off | stage 5 does not rewrite `lessons_learned.md` |
| `--update-lessons` | | `run_pipeline.py`: rewrite the lessons from the recorded outcomes and exit |
| `--skip-analysis` | off | skips only the `technique` / `why_easy` notes (`analyze_split` / `analyze_solved`) |
| `python -m src.common.results_report` | | rebuild `C_RESULTS.md`, the failure map and the scoreboard |
| `python -m src.common.ledger` | | rebuild `ledger.md` |
| `python -m src.stage5_evaluator.failure_analyst <ID>...` | | write the failure analyses |
| `python -m src.common.technique_backfill [ID...]` | all evaluated `GHSA-*`/`PYSEC-*` | infer `techniques_inferred` |

## Code map

| File | Key functions |
|---|---|
| `src/common/knowledge.py` | `record_outcome`, `append_results`, `model_verdicts`, `pattern_of`, `task_profile`, `lessons_for_prompt`, `failure_analysis_lessons`, `update_lessons`, `lessons_problems`, `learned_ranking`, `selection_adjustment`, `load_priors`, `prior_bonus` |
| `src/common/results_report.py` | `collect`, `model_result`, `task_type`, `cwe_family`, `final_verdict`, `render_results`, `render_failure_details`, `render_failure_map`, `render_technique_scoreboard`, `technique_names`, `task_techniques`, `outcome_class`, `main` |
| `src/stage5_evaluator/failure_analyst.py` | `analyse`, `attempt_evidence`, `condense` |
| `src/common/technique_backfill.py` | `infer`, `main` |
| `src/common/ledger.py` | `collect`, `verdict`, `render`, `main` |
| `src/stage5_evaluator/model_runner.py` | `refresh_knowledge`, end-of-run calls in `main` |
| `src/stage3_task_builder/task_generator.py` / `__init__.py` | loads `lessons_for_prompt`; applies `selection_adjustment` |
| `src/stage2_screening/screener.py` | applies `prior_bonus` |

## Known limitations

- **Read once per run.** `task_generator.main` reads the bundle once per stage-3 run. A rebuild made while that run is going (follow mode) reaches only the next stage-3 run.
- **Hard truncation.** The caps slice text mid-section. `failure_analysis_lessons` is cut at 7000 characters, so later analyses can be dropped completely.
- **Self-reported techniques.** The scoreboard uses the generator's own technique list, or an LLM's inference. Nothing checks that a task really applies a technique.
- **Backup on a damaged file.** When the current lessons file is damaged, `update_lessons` backs up the placeholder text, not the damaged original.
- **Data-source gaps.** `results.md` grows without limit and no code reads it. Its current header was edited by hand. `ledger.collect` reads metadata only from `01_mined` (not `02_screened`).
- **Hardcoded text and partial skip flag.** `C_RESULTS.md` hardcodes "the 2-hour agent limit" whatever `AGENT_TIMEOUT_SEC` is. `--skip-analysis` does not stop `failure_analyst` LLM calls.
- **Unreachable status in the prompt.** The `LESSONS_PROMPT` mentions a `rejected_task_defect` status that stage 5 never assigns.
