# CWE-Bench task factory - documentation

This folder documents each pipeline stage in detail: what it reads and writes, the exact rules and thresholds, its
configuration, and where the code lives. Start with the project [README](../README.md) for setup and results.

| # | Doc | Stage / topic |
|---|---|---|
| - | **[PIPELINE.md](PIPELINE.md)** | **All stages on one page (2-minute read)** |
| - | **[MODEL_FAILURE_REPORT.md](MODEL_FAILURE_REPORT.md)** | **Why the models fail: results, task dossiers, patterns, recommendations, client FAQ** |
| 1 | [01-mining.md](01-mining.md) | Stage 1: collect advisories and their fix commits |
| 2 | [02-screening.md](02-screening.md) | Stage 2: filter and score candidates |
| 3 | [03-task-builder.md](03-task-builder.md) | Stage 3: pick candidates, prepare the repo, generate the task with Opus |
| 4 | [04-validation.md](04-validation.md) | Stage 4: prove the task is sound before any model sees it |
| 5 | [05-evaluation.md](05-evaluation.md) | Stage 5: run DeepSeek and MiMo through Harbor's Claude Code agent; verdict |
| 6 | [06-packaging.md](06-packaging.md) | Stage 6: write the final Harbor task |
| 7 | [07-knowledge-loop.md](07-knowledge-loop.md) | How every result feeds back into the next generation round |

## End-to-end flow

```
 Stage 1 Mining        OSV / GHSA / huntr advisories (PyPI, npm) -> fix commit(s)       -> data/01_mined/
 Stage 2 Screening     date cutoff, real source change, tests, repo size, score         -> data/02_screened/
 Stage 3 Task builder  learned ranking -> checkout vulnerable commit -> Docker build check
                       -> Opus writes report + hidden tests + check patches             -> data/03_environments/<id>/
 Stage 4 Validation    rubric, recall probe, image scan, oracle x2, pre-patch, existing
                       tests, shallow / removal / alternative fix checks               -> data/03_environments/<id>/validation/
 Stage 5 Evaluation    DeepSeek + MiMo, 3 attempts each, Claude Code agent, isolated
                       network, separate grader, deterministic verdict                 -> data/04_eval_runs/<id>/
 Stage 6 Packaging     final oracle run, Harbor layout + metadata                       -> data/05_accepted_harbor/<id>/
 Knowledge loop        C_RESULTS.md, failure map, failure analyses, technique scoreboard,
                       learned ranking -> read by stage 3 in the next round            -> data/knowledge/, C_RESULTS.md
```

A task moves to the next stage only when the previous stage marked it done. The state lives in
`data/pipeline_state.sqlite3` (table `items`: stage, key, status, attempts, detail), so any stage can be re-run on its
own and finished work is never repeated.

## Data layout

| Path | Written by | Content | In git |
|---|---|---|---|
| `data/01_mined/osv_candidates.json` | stage 1 | mined advisories and their fix commits | yes |
| `data/02_screened/screened.json`, `rejected.json` | stage 2 | candidates that passed or failed screening, with scores | yes |
| `data/03_environments/<id>/repo/` | stage 3 | repo checkout at the vulnerable commit | no |
| `data/03_environments/<id>/{instruction.md, hidden_tests.py, oracle_solution.patch, task_metadata.json, check_patches/}` | stage 3 | the generated task and its reference fix | no |
| `data/03_environments/<id>/{rubric_check.json, recall_probe.json, isolation_audit.json, oracle_validation.json, validation/, attempts/}` | stage 4 | validation records, Harbor runs, archived rewrite rounds | no |
| `data/04_eval_runs/<id>/<model>/<job>/<trial>/` | stage 5 | each attempt: agent trajectory, patch, per-test results, score | no |
| `data/04_eval_runs/<id>/{summary.json, attribution.json}` | stage 5 | per-model results and the deterministic attribution | no |
| `data/05_accepted_harbor/<id>/` | stage 6 | accepted Harbor tasks | yes, without `environment/repo/` |
| `data/knowledge/` | stage 5 + report | knowledge base the generator reads | yes |
| `C_RESULTS.md` | report | results ledger | yes |
| `data/logs/<run>/` | you | one folder per run, numbered step logs | no |

## Conventions

- **Task id** = the advisory id (`GHSA-xxxx-xxxx-xxxx` or `PYSEC-YYYY-NNNN`).
- **Solved** = reward 1.0. Anything below is a failure, unless the attempt hit the 2-hour limit (`TIMEOUT_POLICY=exclude`:
  not counted).
- **Deterministic verdicts.** LLMs write tasks, review task design and write failure analyses, but they never decide
  whether a model passed.
