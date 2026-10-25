# cwe-bench

A factory for **security-fix benchmark tasks** in the Harbor format. Each task is a real open-source repository at a
vulnerable commit, plus a realistic vulnerability report. An AI coding agent must fix the flaw without breaking the
product. Hidden behavioural tests attack the flaw through real entry points, and check that legitimate use still
works.

A task is a **breaker** when both target models, DeepSeek V4.1 Flash and Xiaomi MiMo-V2.6-Pro, fail it on 3 of 3
runs, every failing run passes an independent audit, and a fairness review finds the task fair.

## Where to start

| You want to… | Read |
|---|---|
| run or extend the **sibling-injection** pipeline | `pipelines/sibling/GUIDE.md`, then `COMPONENTS.md` |
| run or extend the **stacking** pipeline | `pipelines/stacking/GUIDE.md`, then `COMPONENTS.md` |
| run the **three-step scale run** | `pipelines/router/README.md` |
| understand the shared gate, trial, audit and launch tools | `common/README.md` |
| find new candidate advisories | `sourcer/README.md` |
| see results | `reports/BREAKERS.md`, `reports/SINGLE-MODEL-BREAKERS.md`, `reports/stacking-night-20261025.md` |
| understand the design | `docs/ALGORITHM.md`, `docs/BETTER-PATTERNS.md`, `docs/STACKING-EXPLORATION.md` |

## Layout

```
README.md            this file
.cwe-bench-root      marks the repo root (common/paths.* look for it; do not move it)
common/              shared infrastructure: launch, builder, screener, gate, blindfix, trial, audit, fairness,
                     versioning, util. One copy of each file. paths.py / paths.sh define every location.
pipelines/
  sibling/           sibling-injection: 1-pick 2-screen 3-rank 4-select 5-prepare 6-build 9-fairness 10-fairfix
                     upgrade; out/ (batch records); archive/ (old versions, one-offs)
  stacking/          stacking: 1-select 2-prepare 3-build-gate 4-listing 5-upgrade 6-trial 7-fairness 8-fairfix;
                     out/; archive/
  router/            the three-step scale run: stacking first, sibling on the rest, sibling on solved stacked
                     tasks (README.md, route.py; design in docs/PIPELINE-3STEP-DESIGN.md)
sourcer/             advisory sourcing (OSV index, scoring); reserve/ holds the reserve sources (R1-R5)
experiments/         precision_validation/: a FAILED experiment, kept for the record. Do not use (see its README)
reports/             breaker registers and run reports
docs/                design notes, research, history, peer material
attic/               the round 1/2 driver from before the sibling pipeline (not runnable)
build/               run data: build/<slug>/ (build records, gate markers, manifests), build/pipeline/, build/audit/
tasks/               run data: tasks/<slug>/, the Harbor task packages
```

## The two pipelines

Both pipelines produce the same kind of task and share the build prompt, gate, trial, audit and fairness tools.
They differ in **how the hidden difficulty is made**:

- **Sibling injection:** the reported flaw, plus injected sibling variants of it at other sites in the same repo.
- **Stacking:** several independent real flaws behind one report. Each stacked task has a one-bug `-control` twin
  with a byte-identical instruction, which measures what stacking adds.

## How the code is kept unambiguous

- **One live copy of each component.** Its path is the CURRENT version. Each pipeline's `COMPONENTS.md` names the
  last version proven in real runs, and where every older version is archived.
- **Old versions are never deleted.** They live in the owning `archive/` folder, unchanged, indexed in
  `archive/README.md` (original path, date, sha256). Archived files use the old layout and are not runnable as-is.
- **Every script finds the repo through `common/paths.py` / `common/paths.sh`.** No script builds paths from its own
  location.

## Machines

The pipelines run on the VM (`~/cwe-bench`, a git checkout of this repo since 2026-10-25). The pre-reorganisation tree is
kept read-only at `~/cwe-bench-legacy-20261025`. On the VM, `git status` lists run data as changed or untracked: new
records under `build/`, `tasks/` and `pipelines/*/out/`. That is expected. Code changes outside those folders are not. The Mac checkout holds the sourcer's
candidate index (`sourcer/index/`, git-ignored) and runs the Mac-side steps (picking, ranking, selection reading).

Not in git, because the data is large or secret:
- the candidate indexes;
- trial runs and task versions (`~/.tb-graders/cwe/` on the VM);
- precision_validation's Actions output;
- API keys (see `common/launch/models.env.example`).
