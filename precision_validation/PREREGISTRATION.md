# Pre-registration: precision validation

Locked 2026-10-22T22:18:57Z, before any build or trial. Any change to an item below after this
time must be logged here with the reason; changing the rule, arms, builder or criteria after
outcomes exist voids the A-vs-B test.

| Item | Path | sha256 (first 16) |
|---|---|---|
| Pre-build rule | `results/rule.json` | `5947afcc28ea3125` |
| Unseen-100 scores | `results/predictions.csv` | `2b9e98ab5392305d` |
| Stacking-21 scores (group C) | `results/predictions_stacking21.csv` | `3d3f832bb5a0091f` |
| Arm A (21) | `results/arm_A_above_bar.csv` | `e8a5d7e9f3a3dc70` |
| Arm B (40, seed 20261022) | `results/arm_B_control.csv` | `e211b263e691e675` |
| Slugs and build order | `results/build_slugs.csv` | `291c5e03275fa997` |
| Post-build rule | `results/postbuild_rule.json` | `a1263d2af1297f30` |
| Frozen builder + harness + records | `root/{builder,harness,pipeline,sourcer,screener_records}` | `43773b68544a0a46` |
| All 63 specs + BUILD-PROMPTs | `root/build/pv-*/` | `4bbfa3cf7317c8af` |
| Analysis code | `screener/{screen,postbuild,analyze,prepare_builds}.py` | `e14dbf81688df97e` |
| Success criteria text | `PLAN.md section` | `df918b92301a0456` |

## What is fixed

- **Population:** the 93 unseen pool entries not already in the stacking batch. Arm A = all 21 at or above the
  bar (3.8); arm B = 40 drawn from the 72 below (seed 20261022). Group C = 2 stacking-sourced entries above
  the bar, reported separately and not part of the A-vs-B test.
- **Order:** arm A is built and trialed first, as its own batch; then arm B. Group C may run with either.
- **Treatment, both arms:** the frozen builder under `root/` (latest sibling-injection builder with the
  surface rule), DeepSeek V4.1 Flash as the generator; trials offline (model API only), 2 h agent cap,
  DeepSeek first then MiMo-V2.6-Pro, early abort at the first solve; fairness after 3/3 fails on both,
  fairfix + re-trial allowed; **no hardening**; Opus post-run audit; verdicts only from audit_results.py.
- **Exclusions:** none. Every candidate is built; a failed build or unsound gate counts as not a breaker
  (intent to treat), as in batch 2. Per-sound-task rates are reported alongside.
- **Label:** breaker = both models fail all 3 counted runs, fairness READY, every counted run audited.
- **Post-build checkpoint:** `screener/postbuild.py extract` then `predict` after the last gate of an arm
  and before its first trial; the predictions file is hashed with its timestamp.
- **Analysis:** `screener/analyze.py` on `results/outcomes.csv`; reading per the criteria in PLAN.md:
  VALIDATED (A > B, one-sided Fisher p < 0.10, at least 10 points and 1.5x), PARTIAL, or NOT VALIDATED;
  context: A >= 9/21.

## Change log

- 2026-10-22T23:05Z — **Arm A builds run on GitHub Actions**, not klavis-vm (the VM was full: load 71-86 on
  64 CPUs, stacking in its build phase). Public repo `aamiralidsinc/build-matrix-k7`; only the workflow
  and an AES-256 encrypted payload are public; task names and paths masked in logs. One task per job on
  a dedicated 4-vCPU / 15 GB / 116 GB-free runner, Claude Code 2.1.302 and Harbor
  0.23.1.dev202609170426 (= the VM). Builder, prompts and gate unchanged. Probe run 39868708977: Docker
  ok, DeepSeek ok, Harbor smoke reward 1. Build run 39869135267.
  Rules added: (1) every gated task is re-imaged and re-gated on the VM before trials; all trials run on
  the VM, as for arm B. (2) A build stopped by an Actions limit (6 h job cap, disk) or a runner fault is
  re-run on the VM and not counted as a failed build. (3) The builder's own result on Actions (sound /
  unsound / builder failure) counts as for arm B.
  Added to `root/` for this (paths only, logic unchanged): `drive.sh`, `pv_run_build.sh`,
  `pv_pipeline.sh`, `pipeline/pv_gate_one.sh`, `pipeline/agent_status.py`, `pipeline/docker-tuning.env`.
