# Sibling-injection pipeline: component versions

**Rule:** always use the CURRENT file, which is the one at its live path. "Last proven" names the version that last
ran for real in this pipeline:
- build, select and screen were last run by the sibling2 batch, 2026-10-23/24;
- trial and fairness were last run by the batch-1 lane, 2026-10-22;
- fairfix, upgrade and blind fix were last run by the batch-1 lane, 2026-10-20.

When the two differ, the current version has fixes that **have not run yet in this pipeline**.

All old versions are in `pipelines/sibling/archive/versions/` or `common/archive/versions/`. Each file name
carries the date it was replaced, and both `archive/README.md` files list every file with its original path, date
and sha256.

| Component | CURRENT (live path) | Status | Last proven | Archived versions |
|---|---|---|---|---|
| Picker | `1-pick/pick.py` | proven (sibling2) | same | none. Older pickers: `common/screener/run_screener.py --pick` (stacking's), and the rerank-v4 host shortlist in `archive/screener-calibration-20261017/` |
| Screener prompt | `common/screener/SCREENER-PROMPT-v2.md` + its `## lessons-v2` block | proven: all 300 sibling2 records say screener-v2 / lessons-v2 / Opus 5.5 | same | `common/archive/versions/builder/SCREENER-PROMPT-v2.md.bak-20261019` (v2 + lessons-v1, ran the 150-host screen on 10-17); `common/archive/old-prompts/SCREENER-PROMPT-v1.md`, `PROMPT-screener.md` |
| Screener runner | `common/screener/run_screener.py` (shared with stacking), wrapped by `2-screen/screen.py` | proven | same | the 10-17 wave scripts in `archive/screener-calibration-20261017/vm/` |
| Rank | `3-rank/rerank.py` + `screen-weights.json` (`screen-w0`, not validated) | proven (sibling2; the command was not recorded) | same | calibration tools in `archive/screener-calibration-20261017/` (`validate_screen.py` reads the **v1** schema) |
| Pool | `4-select/make_pool.py` (driven by `4-select/lane.py pool`) | proven | same | none |
| Select | `4-select/select.sh` + `SELECT-PROMPT.md` | proven | same | `common/archive/versions/builder/SELECT-PROMPT.md.bak-20261019`, `.bak-claude-20261021T1930Z`; batch-1 `select.sh` in `archive/batch1-lane-pilot/` |
| Union | none (by hand) | — | — | — |
| Prepare | `5-prepare/prepare_lane.py` + `SELFDESIGN-PLAN.md` + `common/builder/build_prepare.py` | proven | same | `SELFDESIGN-PLAN.md.bak-20261019`, `.bak-claude-20261021T1930Z` (in `common/archive/versions/builder/`) |
| Build prompt | `common/builder/TASK-BUILD-PROMPT-v1.md` (Frontier format, surface rule, shape traps 7–10, list-every-sibling) | proven (sibling2) | same | `common/archive/versions/builder/TASK-BUILD-PROMPT-v1.md.bak-20261019` (original, **no surface rule**: built batch-1 `-ds`/`-mm` and `-inj`), `.bak-20261021T142112Z`, `.bak-claude-20261021T1930Z` |
| Builder rules | `common/builder/BUILDER.md`, `BRIEF-trap-stack.md`, `FRONTIER-CONFORMANCE-SPEC.md`, `conformance_check.py`, `templates/` | proven | same | `BUILDER.md.bak-*` ×4 in `common/archive/versions/builder/`; `common/archive/templates-frontier-stale/`; `common/archive/versions/builder/templates.bak-*` |
| Build launcher | `common/launch/run_build.sh` via `common/launch/drive.sh` | proven | same | none |
| Build lane | `6-build/run_pipeline.sh`, `ramp_lane.py` (the one actually used), `run_lane.sh` (run 0 was killed), `resume_lane.py` + `resume_pipeline.sh` (outage recovery) | proven | same | `archive/versions/ramp_lane.py.bak-40step`; batch-1 parents `archive/batch1-lane-pilot/run_pipeline.sh`, `run_lane.sh` |
| Gate | `common/gate/gate_one_ds.sh` + `common/gate/gate.py` (blind-skip, harbor retry, allow-agent-host, `GATE_PARALLEL`) | proven: sibling2 gates and every stacking repair | same | 14 `gate.py.bak-*` and 3 `gate_one_ds.sh.bak-*` in `common/archive/versions/` (the ok=None-as-flake bug lives in the old wrappers) |
| Blind fix | `common/blindfix/run_blindfix.sh` + `BLIND-FIX-BRIEF.md` | **not yet run in this pipeline** (current since 10-21; run by stacking) | `common/archive/versions/run_blindfix.sh.bak-20261021T001849Z` (10-20) | `.bak-20261020T223508Z` (the un-injected-tree bug), `.bak-20261021T001849Z` |
| Trial | `common/trial/trial.py` → `common/trial/run_trial.sh` | proven | same | `common/archive/versions/build/trial.py.bak-*` ×3, `harness/run_trial.sh.bak-20261021T141951Z` |
| Audit | `common/audit/postmortem.py` + Opus sub-agents; `common/audit/audit_results.py` | proven | same | `common/archive/versions/build/audit_results.py.bak-20261020T230715Z` |
| Fairness | `9-fairness/run_fairness.sh` + `common/fairness/FAIRNESS-REVIEW-BRIEF.md` (two-gate split) | proven (10-22) | same | `archive/versions/run_fairness.sh.bak-*` ×2; brief `.bak-*` ×3 in `common/archive/versions/builder/` |
| Fairfix | `10-fairfix/run_fairfix.sh` (snapshot first, restore on failure) | **not yet run in this pipeline** (current since 10-21) | `archive/versions/run_fairfix.sh.bak-20261021T001849Z` | `.bak-20261019`, `.bak-20261020T233033Z`, `.bak-20261021T001849Z` |
| Orchestrators | `10-fairfix/advance_one.sh`, `validate_fresh.sh`, `validate_loop.sh`, `validate_common.sh` | proven (10-20) | same | none |
| Upgrade | `upgrade/run_upgrade.sh` + `UPGRADE-PROMPT.md` | **launcher not yet run** (current since 10-21) | `archive/versions/run_upgrade.sh.bak-20261020T233033Z` ran "upgrade run 2" (37 tasks) | `.bak-20261020T233033Z`, `.bak-20261021T001849Z`; batch scripts in `archive/batch1-oneoffs/` |
| Hardening | **dropped** (user, 2026-10-22) | — | — | `archive/hardening-dropped/` |
| Queue | batch-1 `queue.sh` + `QUEUE.md` (archived) | not used for sibling2 | — | `archive/batch1-lane-pilot/` |
