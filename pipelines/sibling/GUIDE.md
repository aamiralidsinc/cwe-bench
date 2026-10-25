# Sibling-injection pipeline: guide

**One-line summary:** take a real published advisory in a real repo, keep its reported route, and **inject sibling
variants** of the same flaw at other sites in the repo (other routes, forms, layers). The solver sees only the
report of the first one. Hidden behavioural tests check every variant, and check that legitimate use keeps working.
A task counts as a breaker when both DeepSeek V4.1 Flash and MiMo-V2.6-Pro fail it 3/3, fairly.

- Versions of every component (current vs last proven, and where the old versions are): **COMPONENTS.md**.
- Design background: `docs/ALGORITHM.md`, `docs/BETTER-PATTERNS.md`, `reports/SIBLING-INJECTION-PATTERNS.md`.
- Shared infrastructure: `common/README.md`.

Run every command **from the repo root**: `~/cwe-bench` on the VM, or the checkout on the Mac. Agent steps go through
`common/launch/drive.sh <deepseek|mimo> bash <script> <args>`. The launcher sets `MODEL` and the endpoint, and
the launchers refuse to run without `MODEL`; there is no Opus fallback.

## Folders

| Folder | What is in it |
|---|---|
| `1-pick/` | `pick.py`: the next N candidates by index score, one per repo, excluding everything already used. It runs on the **Mac** (the candidate index is there) |
| `2-screen/` | `screen.py`: runs the shared screener (`common/screener/`) into `out/screener/` |
| `3-rank/` | `rerank.py` + `screen-weights.json`: computed ranking of screened hosts (Mac). `build_ledger.py`: the host ledger |
| `4-select/` | `lane.py` (pool + prepare wrapper), `make_pool.py`, `select.sh` + `SELECT-PROMPT.md`: the driver model picks its builds |
| `5-prepare/` | `prepare_lane.py` + `SELFDESIGN-PLAN.md`: writes `build/<slug>/BUILD-PROMPT.md` from `common/builder/TASK-BUILD-PROMPT-v1.md` |
| `6-build/` | `run_pipeline.sh` (per slug: build, then gate), lane runners `run_lane.sh` / `ramp_lane.py`, outage recovery `resume_lane.py` + `resume_pipeline.sh` |
| `9-fairness/` | `run_fairness.sh`: fairness review after a 3/3 fail |
| `10-fairfix/` | `run_fairfix.sh` plus the orchestrators `advance_one.sh` (fairness ⇄ fairfix) and `validate_fresh.sh` / `validate_loop.sh` / `validate_common.sh` |
| `upgrade/` | `run_upgrade.sh` + `UPGRADE-PROMPT.md`: brings an **old** build up to the current builder rules (a utility, not part of a fresh run) |
| `out/` | batch records of the sibling2 fresh batch (2026-10-23/24): screener jobs and records, pool, selections, specs, slug list, build ledger, lane logs |
| `archive/` | old versions, the batch-1 lane pilot (queue.sh), batch-1 one-offs, the dropped hardening step, screener calibration (see `archive/README.md`) |

Steps 7 (trial) and 8 (audit) use shared tools only (`common/trial/`, `common/audit/`), so they have no folder here.

## Run order

```
[Mac] 1-pick -> [VM] 2-screen (Opus) -> [Mac] 3-rank -> [VM] 4-select pool + select (DeepSeek) -> union (by hand)
      -> 5-prepare -> 6-build: [build -> gate] per slug, many in parallel
      == BARRIER: no trials while builds run ==
      7 trial (both models, early-abort) -> 8 audit every graded run (Opus)
      -> 9 fairness, only after both models fail 3/3 -> 10 fairfix if NOT_READY (then re-gate, re-trial)
      -> blind fix, before shipping -> breaker register (reports/BREAKERS.md) after a human decision
```

1. **Pick (Mac).** First regenerate `out/vm_used.json` from the VM (the slugs and ids already used there). Then run
   `python3 -I pipelines/sibling/1-pick/pick.py --n 300`. It writes `out/screener_jobs.jsonl` and `out/exclusion.json`;
   copy them to the VM.
   `pick.py` excludes everything already screened or built. That includes the precision_validation candidates
   (`experiments/precision_validation/`), so keep those paths.
2. **Screen (VM, Opus 5.5).**
   `CLAUDE_BIN=... python3 -I pipelines/sibling/2-screen/screen.py --run --parallel 4 --model claude-opus-5-5`.
   This writes `out/screener/<entry_id>.json`. Clones are shared with stacking in `~/.tb-graders/cwe/stacking/clones`.
3. **Rank (Mac).**
   `python3 -I pipelines/sibling/3-rank/rerank.py sourcer/index/candidates.sqlite pipelines/sibling/out/rerank --screened pipelines/sibling/out/screener`.
   ⚠ The exact command used for sibling2 was not recorded; this is the documented form.
4. **Pool and select (VM).**
   - Pool: `python3 -I pipelines/sibling/4-select/lane.py pool`.
   - Select: `bash pipelines/sibling/4-select/select.sh deepseek`. This writes `out/pipeline/selection_deepseek.json`,
     the model's top 50.
   - **Union (by hand, no script):** for sibling2 the build list was the DeepSeek top 50 ∪ the rerank top 50, 74
     slugs in all. Keep the model's own list as `selection_deepseek.model.json` and record the sources in
     `selection_sources.tsv`.
5. **Prepare (VM).** `python3 -I pipelines/sibling/4-select/lane.py prepare deepseek` (it runs
   `5-prepare/prepare_lane.py`). This writes `build/<slug>/BUILD-PROMPT.md`, `out/pipeline/specs_deepseek/` and
   `out/pipeline/slugs_deepseek.txt`. Slugs whose `build/<slug>` already exists are skipped.
6. **Build + gate (VM).** `python3 -I pipelines/sibling/6-build/ramp_lane.py`, or the flat lane
   `bash pipelines/sibling/6-build/run_lane.sh deepseek 16`.
   - Each slug runs `bash pipelines/sibling/6-build/run_pipeline.sh deepseek <slug>`: claim, then
     `common/launch/run_build.sh` (DeepSeek builder), then `common/util/agent_status.py`, then
     `common/gate/gate_one_ds.sh`.
   - The gate leaves exactly one of `.sound` (exit 0), `.unsound` (1) or `.gate_error` (2), plus a ledger row in
     `out/pipeline/ledger_deepseek.tsv`.
   - After an outage (builds frozen), resume the sessions with `python3 -I pipelines/sibling/6-build/resume_lane.py`
     (from `out/pipeline/resume_jobs.tsv`).
   - **Stagger starts** (0–45 s jitter). Don't start trials while builds are running.
7. **Trial (VM).**
   - Per slug, both models, early-abort: `CWE_AGENT_TIMEOUT_MULT=1.5 python3 common/trial/trial.py <slug>`.
   - Or as a stage: `bash common/trial/trial_set.sh '<glob>' <model> <C>`.
   - ⚠ `-ds` names two batches (batch-1 and sibling2). Drive trials from `out/pipeline/slugs_deepseek.txt`, not
     from a glob. **No list-driven sibling2 trial launcher exists yet.**
8. **Audit every graded run.**
   1. `python3 common/audit/postmortem.py pending` lists the runs that need an audit.
   2. `postmortem.py prepare <trial_dir>`.
   3. One **Opus 5.5 (high)** sub-agent per folder writes `verdict.json`. Give each auditor its own scratch folder.
   4. `postmortem.py record-ready`.
   5. Read verdicts **only** from `python3 common/audit/audit_results.py`, which writes `build/audit/ledger.md`.
9. **Fairness** (only after both models fail 3/3, every run audited):
   `common/launch/drive.sh deepseek bash pipelines/sibling/9-fairness/run_fairness.sh <slug>`, then
   `python3 common/fairness/fairness_verdict.py <slug>` (READY / NOT_READY / ERROR). If NOT_READY, an Opus
   leniency validation decides whether the defect is real.
10. **Fairfix** (NOT_READY, or an audit test fault):
    `common/launch/drive.sh deepseek bash pipelines/sibling/10-fairfix/run_fairfix.sh <slug>`. Then run
    `bash common/gate/gate_one_ds.sh <slug>` and re-trial; re-grade only if only the tests changed.
    `advance_one.sh` runs fairness ⇄ fairfix twice without a trial. `validate_fresh.sh` / `validate_loop.sh` run
    gate, then trial, then fairness, end to end.
11. **Blind fix before shipping** (the strict-gate prerequisite):
    `common/launch/drive.sh deepseek bash common/blindfix/run_blindfix.sh <slug>`, then
    `python3 -I common/gate/gate.py <slug>` (all stages, including static).
12. **Register:** after a human decision, add the breaker to `reports/BREAKERS.md` / `SINGLE-MODEL-BREAKERS.md`.

**Upgrade (utility for old builds):** `common/launch/drive.sh deepseek bash pipelines/sibling/upgrade/run_upgrade.sh <slug>`.
It snapshots, runs the agent, then a gate (static only, or the full `gate_one_ds.sh`), and bumps `VERSION`.
Exit codes 0/1/3/4.

## Marker and state files (in `build/<slug>/` unless noted)

| File | Meaning |
|---|---|
| `.lockdir/` | the slug is claimed by a lane worker |
| `build-run.json`, `build_status.json`, `start_utc.txt`, `end_utc.txt` | builder run record |
| `.sound` / `.unsound` / `.gate_error`, `gate_verdict.json` | gate result (exactly one marker) |
| `runs_<model>.log`, `trial_detail*.json`, `evidence/` | trial records (runs are in `~/.tb-graders/cwe/jobs/`) |
| `hold_<model>` | `common/trial/run_trial.sh` refuses new runs for that model |
| `FAIRNESS.md` (+ `.prev-<UTC>`), `fairness_status.txt` | fairness review |
| `VERSION`, `.last_snapshot` | task version; earlier versions are in `~/.tb-graders/cwe/experiments/<slug>/` |
| `checks/blind.patch`, `blind_status.txt` | blind fix |
| `pipelines/sibling/out/pipeline/ledger_deepseek.tsv` | per-slug build/gate ledger of the sibling2 batch |

## Environment

| Setting | Effect |
|---|---|
| `common/launch/drive.sh` | Reads `$CWE_MODELS_ENV`, `~/.tb-graders/cwe/models.env`, `~/cwe-bench/.env`, then `~/.env`. Sets DeepSeek's output and thinking token caps and `API_TIMEOUT_MS=1200000` |
| `common/gate/docker-tuning.env` | Sourced by every Docker-touching script: client/compose timeouts 300 s, BuildKit off. **Dockerfile heredocs are not allowed**; the classic builder drops them |
| Timeouts | `BUILD_TIMEOUT`, `FAIRFIX_TIMEOUT` and `UPGRADE_TIMEOUT` default to 10800 s; fairness 2400 s; blind fix 5400 s |
| Trials | `CWE_AGENT_TIMEOUT_MULT=1.5` gives a 3 h agent limit; **a 3 h timeout counts as a fail** |
| Gate | `GATE_PARALLEL` caps how many gate checks run in parallel |

## Known gaps

- **No list-driven trial launcher, no audit launcher, no post-trial orchestrator** for sibling2. The 74-task batch
  stops at the gate: 68 `.sound`.
- **The union step (step 4) has no script.**
- **The rerank command for sibling2 was not recorded.**
- **The current fairfix / upgrade / blind fix launchers (2026-10-21) have not yet run in this pipeline.** The last
  real runs (2026-10-20) used the versions in `archive/versions/`.
- **Split machines:** the index and rerank run on the Mac; the screen and builds run on the VM. Files are copied by
  hand both ways.
