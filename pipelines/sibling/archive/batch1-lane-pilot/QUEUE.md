# CWE-bench pilot execution queue (priority order) — 2026-10-18

Set by the user. Follow these stages in order. "Build" = model-driven task generation via
`drive.sh <driver> run_build.sh`. "Trial X on Y" = run target model Y (3 runs, --full) against a
task built by X. Breaker = BOTH target models fail 3/3 on one task.

Task sets: **DS-tasks** = `build/*-ds` (built by DeepSeek). **MM-tasks** = `build/*-mm` (built by MiMo).
A task is trial-ready when `build/<slug>/.sound` exists (gate nop+oracle+patches passed).

## Stages

1. **Build all DS-tasks** (DeepSeek-driven). Build + gate only, no trials here. [in progress]
2. **Trial DS-tasks on DeepSeek** (target=deepseek), as each gates sound.
3. **Fairness + fairfix of DS-tasks where DeepSeek FAILED** (deepseek-driven), then re-trial on
   deepseek. Only for tasks DeepSeek did not solve (a DeepSeek-failed task is a breaker lead; make it
   fair so the failure is legitimate). This ends the DeepSeek phase.
4. **Shift to MiMo — two things in PARALLEL:**
   a. **Build all MM-tasks** (MiMo-driven), concurrency 8.
   b. **Trial DS-tasks on MiMo** (target=mimo), concurrency 8.
5. **If 4b (MiMo-on-DS-tasks) finishes before 4a (MM-builds):** start
   - MM-tasks trial on MiMo, 8 at a time, and
   - MM-tasks trial on DeepSeek, 8 at a time (as MM-tasks become sound).
6. **If 4a (MM-builds) finishes first:** same end state —
   - MM-tasks on MiMo = 8, MM-tasks on DeepSeek = 8, DS-tasks on MiMo = 8 (finish 4b).
7. **Concurrency is reducible** as suitable. This box's reliable ceiling is ~12–16 concurrent docker
   jobs (builds+trials+gates combined); above that docker-compose flakes and gating gets unreliable.
   Default each activity to 6–8 and keep total concurrent docker jobs ≲ 16.

## End state (what "done" means)
Full trial matrix recorded: DS×DeepSeek, DS×MiMo, MM×MiMo, MM×DeepSeek, plus fairfix applied to any
DeepSeek-failed DS-task. Breakers (both targets fail 3/3) appended to `reports/BREAKERS.md`.

## Current reconfiguration (2026-10-18, when this queue was set)
- DS builds: keep running (stage 1).
- MiMo builds (8 were running early): PAUSED — deferred to stage 4a.
- Trials that were running `--full` (both models) on DS-tasks: keep the DEEPSEEK run (that is stage 2),
  stop the premature MiMo run on DS-tasks (that is stage 4b).
- run_pipeline.sh changed to build+gate only (writes `.sound`/`.unsound`); trials are driven by the
  separate `trial_set.sh` per stage.

Ledgers: `build/pipeline/ledger_{deepseek,mimo}.tsv`; trial logs `build/<slug>/runs_{deepseek,mimo}.log`.
