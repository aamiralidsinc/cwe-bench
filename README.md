# cwe-bench task pipeline

A pipeline that generates Harbor-format **security-fix** benchmark tasks: a real
open-source repo checked out at a vulnerable commit plus a realistic
vulnerability report; an AI coding agent must fix it; hidden tests exploit the
hole through a real entry point and confirm the feature still works. A task is
accepted only when it is failed on 3/3 runs by both target models
(DeepSeek V4.1 Flash and Xiaomi MiMo-V2.6-Pro).

See **[ALGORITHM.md](ALGORITHM.md)** for the full design, the three task-shape
branches, the scoring model, and the learning loop.

## Pipeline

```
sourcer ──► screener/scoring ──► builder ──► gate ──► trial (early-abort) ──► verdict
```

Driver (mode-selectable, resumable from filesystem state):

```
python3 build/run.py simple   <slug>     # mined-only (Branch A, baseline)
python3 build/run.py sibling  <slug>     # mined + injected sibling (Branch B)
python3 build/run.py stacking <slug>     # several real co-present vulns (Branch C)
python3 build/run.py screen   <mined|stacking>
python3 build/run.py status   <slug>
```

## Layout

| Path | What |
|---|---|
| `ALGORITHM.md` | design: pipeline, branches, scoring, learning loop |
| `sourcer/` | OSV sourcer, candidate index, `weights.json` scoring config, screeners |
| `sourcer/stacking_screener.py` | Branch C: rank small repos with co-present real vulns |
| `builder/BUILDER.md`, `BUILDER-stacking.md` | briefs a builder agent follows |
| `builder/gate.py` | scripted acceptance gate (static → nop → oracle → patches) |
| `builder/templates/` | task skeleton: `task.toml`, `test.sh`, `score.py` |
| `build/run.py`, `trial.py`, `status.py` | driver, sequential early-abort trial runner, status |
| `build/<slug>/` | per-task build artifacts: manifest, checks, gate report |
| `tasks/<slug>/` | the Harbor tasks (instruction, env, solution, tests) |
| `harness/run_trial.sh` | run a task with Claude Code driving DeepSeek/MiMo |

## Not in the repo (reproducible / secret)

- `sourcer/index/` (the candidate SQLite/TSV) — regenerate by running the sourcer.
- OSV dumps, Docker images, clones, build caches — live outside the tree.
- API keys (`.env`) — see `harness/models.env.example` for the variables.

## Status (pilot)

6 mined-only tasks built: all solved by both models (mined difficulty alone does
not clear the bar — the fix is derivable). The injected-sibling and stacking
branches are the path to breakers; see ALGORITHM.md and `build/queue.json`.
