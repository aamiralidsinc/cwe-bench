# pipelines/sibling/archive/

Old versions and retired pieces of the sibling-injection pipeline.

**Nothing here is runnable as it is.** These files use the paths from before the 2026-10-25 reorganisation (`builder/`, `pipeline/`, `harness/`, `stacking/`, `sibling2/`, `build/trial.py`, ...). They are kept so that no earlier work is lost and every past run can be traced to the code that ran it. To revive one, port it to `common/paths.py` / `common/paths.sh` first.

## batch1-lane-pilot/

The batch-1 DeepSeek/MiMo lane pilot (2026-10-18..22): its queue (`queue.sh`, `QUEUE.md`), selection and per-slug lane scripts. Replaced by `pipelines/sibling/6-build/` (the sibling2 lane).

| File | Was at | Last modified (UTC) | sha256 |
|---|---|---|---|
| `batch1-lane-pilot/QUEUE.md` | `pipeline/QUEUE.md` | 2026-10-18 22:01 | `6cf365e83c54` |
| `batch1-lane-pilot/queue.sh` | `pipeline/queue.sh` | 2026-10-20 23:30 | `47753c78ef59` |
| `batch1-lane-pilot/run_lane.sh` | `pipeline/run_lane.sh` | 2026-10-18 18:32 | `f523a59e1b62` |
| `batch1-lane-pilot/run_pipeline.sh` | `pipeline/run_pipeline.sh` | 2026-10-21 00:18 | `edc9cd443401` |
| `batch1-lane-pilot/select.sh` | `pipeline/select.sh` | 2026-10-18 18:53 | `dda4b53c3429` |

## batch1-oneoffs/

One-off batch-1 scripts (2026-10-18..22), most with hard-coded slug lists: re-gates, recovery, blind-fix and trial launch waves, phase B/C chains, ticks. Kept as the record of what was run.

| File | Was at | Last modified (UTC) | sha256 |
|---|---|---|---|
| `batch1-oneoffs/auto_trial_launch.sh` | `pipeline/auto_trial_launch.sh` | 2026-10-20 23:30 | `3a3361564175` |
| `batch1-oneoffs/backstage_validate.sh` | `pipeline/backstage_validate.sh` | 2026-10-20 23:30 | `7cde766a94f9` |
| `batch1-oneoffs/blind_informed.sh` | `pipeline/blind_informed.sh` | 2026-10-20 17:00 | `1f9477c44323` |
| `batch1-oneoffs/blind_informed_ctr.sh` | `pipeline/blind_informed_ctr.sh` | 2026-10-21 00:18 | `5b5801c4375d` |
| `batch1-oneoffs/blindfix12.sh` | `pipeline/blindfix12.sh` | 2026-10-20 07:18 | `ec6da99ddb92` |
| `batch1-oneoffs/blindfix_ds.sh` | `pipeline/blindfix_ds.sh` | 2026-10-20 22:37 | `6358fa63a33f` |
| `batch1-oneoffs/bs_v3_launch.sh` | `pipeline/bs_v3_launch.sh` | 2026-10-20 21:34 | `8b5075f1d64d` |
| `batch1-oneoffs/bs_verify_gate.sh` | `pipeline/bs_verify_gate.sh` | 2026-10-21 00:26 | `76ff2e956a2e` |
| `batch1-oneoffs/classify_candidates.py` | `pipeline/classify_candidates.py` | 2026-10-19 22:36 | `6bcb8e3b86c3` |
| `batch1-oneoffs/ds_matrix.py` | `pipeline/ds_matrix.py` | 2026-10-19 05:19 | `496994a5e1cb` |
| `batch1-oneoffs/faircheck_rerun.sh` | `pipeline/faircheck_rerun.sh` | 2026-10-20 23:30 | `61719224d47d` |
| `batch1-oneoffs/fairness_candidates.sh` | `pipeline/fairness_candidates.sh` | 2026-10-20 23:30 | `feeeb6b7ccfa` |
| `batch1-oneoffs/fix_openbao.sh` | `pipeline/fix_openbao.sh` | 2026-10-19 22:08 | `3f0ee5312535` |
| `batch1-oneoffs/launch_batch.sh` | `pipeline/launch_batch.sh` | 2026-10-21 04:30 | `39d154246cd5` |
| `batch1-oneoffs/parallel_recover.sh` | `pipeline/parallel_recover.sh` | 2026-10-20 17:26 | `8256c528a701` |
| `batch1-oneoffs/pause_builds.sh` | `pipeline/pause_builds.sh` | 2026-10-19 00:29 | `df1f7d84afa7` |
| `batch1-oneoffs/phaseB_mimo_chain.sh` | `pipeline/phaseB_mimo_chain.sh` | 2026-10-22 06:03 | `57527b7aef02` |
| `batch1-oneoffs/phaseB_mimo_now.sh` | `pipeline/phaseB_mimo_now.sh` | 2026-10-22 13:02 | `b6f9c291d790` |
| `batch1-oneoffs/phaseB_trials.sh` | `pipeline/phaseB_trials.sh` | 2026-10-22 05:11 | `7da77fd23f6b` |
| `batch1-oneoffs/reconfigure.sh` | `pipeline/reconfigure.sh` | 2026-10-18 22:06 | `6f067b0e8001` |
| `batch1-oneoffs/recover_ds.sh` | `pipeline/recover_ds.sh` | 2026-10-18 22:12 | `ca9053fcd1ec` |
| `batch1-oneoffs/regate5.sh` | `pipeline/regate5.sh` | 2026-10-20 16:55 | `b726eec6c9b0` |
| `batch1-oneoffs/regate7.sh` | `pipeline/regate7.sh` | 2026-10-19 21:40 | `6a7afd99a2f6` |
| `batch1-oneoffs/regate7_patched.sh` | `pipeline/regate7_patched.sh` | 2026-10-20 06:45 | `424136240044` |
| `batch1-oneoffs/regate8.sh` | `pipeline/regate8.sh` | 2026-10-19 22:31 | `497c9c399048` |
| `batch1-oneoffs/regate_all_ds.sh` | `pipeline/regate_all_ds.sh` | 2026-10-19 05:24 | `d400f15a704e` |
| `batch1-oneoffs/regate_serial.sh` | `pipeline/regate_serial.sh` | 2026-10-20 18:47 | `81168095f1d8` |
| `batch1-oneoffs/regate_unsound.sh` | `pipeline/regate_unsound.sh` | 2026-10-20 07:18 | `e3a50f94a2c8` |
| `batch1-oneoffs/regen2.sh` | `pipeline/regen2.sh` | 2026-10-20 23:41 | `3b9251b68a8e` |
| `batch1-oneoffs/relaunch_p20.sh` | `pipeline/relaunch_p20.sh` | 2026-10-20 05:51 | `a433bed3135a` |
| `batch1-oneoffs/reset_all6.sh` | `pipeline/reset_all6.sh` | 2026-10-20 00:12 | `e5520c1b200e` |
| `batch1-oneoffs/retrial_stage.sh` | `pipeline/retrial_stage.sh` | 2026-10-20 03:36 | `c4babd795366` |
| `batch1-oneoffs/run_ds_fairness.sh` | `pipeline/run_ds_fairness.sh` | 2026-10-19 03:35 | `94c7d3b1396e` |
| `batch1-oneoffs/six_trials.sh` | `pipeline/six_trials.sh` | 2026-10-20 23:31 | `cf8694d8dc69` |
| `batch1-oneoffs/split_stale_runs.py` | `pipeline/split_stale_runs.py` | 2026-10-20 23:30 | `d4ea5782eb9a` |
| `batch1-oneoffs/stop_regate_fairfix.sh` | `pipeline/stop_regate_fairfix.sh` | 2026-10-20 02:27 | `1dbf2736be62` |
| `batch1-oneoffs/theia_fairfix.sh` | `pipeline/theia_fairfix.sh` | 2026-10-20 22:52 | `d7b288366bb9` |
| `batch1-oneoffs/tick10.sh` | `pipeline/tick10.sh` | 2026-10-20 12:14 | `5780f3f31691` |
| `batch1-oneoffs/tick12.sh` | `pipeline/tick12.sh` | 2026-10-20 13:14 | `057bc690eeee` |
| `batch1-oneoffs/tick16.sh` | `pipeline/tick16.sh` | 2026-10-20 15:44 | `576101f0a1fd` |
| `batch1-oneoffs/tick3.sh` | `pipeline/tick3.sh` | 2026-10-20 08:47 | `edae6c35ce4f` |
| `batch1-oneoffs/tick4.sh` | `pipeline/tick4.sh` | 2026-10-20 09:14 | `8abaf4272609` |
| `batch1-oneoffs/tick7.sh` | `pipeline/tick7.sh` | 2026-10-20 10:44 | `72bacb6fdd62` |
| `batch1-oneoffs/tick9.sh` | `pipeline/tick9.sh` | 2026-10-20 11:44 | `6d5015ff4ee4` |
| `batch1-oneoffs/undo_retrial.sh` | `pipeline/undo_retrial.sh` | 2026-10-20 03:39 | `14c7ea9a00d3` |
| `batch1-oneoffs/upgrade_batch.sh` | `pipeline/upgrade_batch.sh` | 2026-10-20 05:09 | `e2eb9a5bb204` |
| `batch1-oneoffs/upgrade_breakers.sh` | `pipeline/upgrade_breakers.sh` | 2026-10-20 07:18 | `144efcd2d533` |
| `batch1-oneoffs/verify_regate.sh` | `pipeline/verify_regate.sh` | 2026-10-21 01:55 | `72dea3268716` |
| `batch1-oneoffs/wire_snapshot.sh` | `pipeline/wire_snapshot.sh` | 2026-10-20 04:41 | `9b1ca2fd6657` |

## hardening-dropped/

The hardening step. Dropped from production by the user on 2026-10-22 (2 breakers in 33 tasks).

| File | Was at | Last modified (UTC) | sha256 |
|---|---|---|---|
| `hardening-dropped/HARDENING-PROMPT.md` | `builder/HARDENING-PROMPT.md` | 2026-10-21 19:34 | `3a7b15a9d310` |
| `hardening-dropped/harden_solved.sh` | `pipeline/harden_solved.sh` | 2026-10-21 15:41 | `d9c63bb809e6` |
| `hardening-dropped/run_harden.sh` | `pipeline/run_harden.sh` | 2026-10-21 19:31 | `29b951103d28` |

## screener-calibration-20261017/

Screener calibration and the 10-17 production screen waves (`rerank-v4-draft`): calibration, choose and report tools, the VM wave scripts, the batch-1 host rankings.

| File | Was at | Last modified (UTC) | sha256 |
|---|---|---|---|
| `screener-calibration-20261017/screen_calibrate.py` | `sourcer/rerank-v4-draft/screen_calibrate.py` | 2026-10-17 00:01 | `d68c3a0b8ec7` |
| `screener-calibration-20261017/screen_choose.py` | `sourcer/rerank-v4-draft/screen_choose.py` | 2026-10-17 00:04 | `445c961b0e81` |
| `screener-calibration-20261017/screen_prepare.py` | `sourcer/rerank-v4-draft/screen_prepare.py` | 2026-10-17 00:01 | `7ed5871d7f2f` |
| `screener-calibration-20261017/screen_report.py` | `sourcer/rerank-v4-draft/screen_report.py` | 2026-10-19 16:38 | `34fc562b857b` |
| `screener-calibration-20261017/vm/fetch_hosts.sh` | `sourcer/rerank-v4-draft/vm/fetch_hosts.sh` | 2026-10-17 00:02 | `1c8d92732af4` |
| `screener-calibration-20261017/vm/run_screen.sh` | `sourcer/rerank-v4-draft/vm/run_screen.sh` | 2026-10-17 00:01 | `e9f4257d00fd` |
| `screener-calibration-20261017/vm/screen_waves.sh` | `sourcer/rerank-v4-draft/vm/screen_waves.sh` | 2026-10-16 23:07 | `fc8e9163728c` |

## versions/

`.bak-*` backups of files that are still live. The live file is the CURRENT version; each backup name carries the date it was replaced (UTC). Compare with `diff` against the live file.

| File | Was at | Last modified (UTC) | sha256 |
|---|---|---|---|
| `versions/builder/HARDENING-PROMPT.md.bak-20261019` | `builder/HARDENING-PROMPT.md.bak-20261019` | 2026-10-19 15:23 | `a8fd5927c887` |
| `versions/builder/HARDENING-PROMPT.md.bak-20261020T233354Z` | `builder/HARDENING-PROMPT.md.bak-20261020T233354Z` | 2026-10-20 03:55 | `5105ebb5b88d` |
| `versions/builder/HARDENING-PROMPT.md.bak-20261021T154104Z` | `builder/HARDENING-PROMPT.md.bak-20261021T154104Z` | 2026-10-21 15:41 | `a35f829971dd` |
| `versions/builder/HARDENING-PROMPT.md.bak-claude-20261021T1930Z` | `builder/HARDENING-PROMPT.md.bak-claude-20261021T1930Z` | 2026-10-21 15:41 | `ffeb176335c2` |
| `versions/builder/SELECT-PROMPT.md.bak-20261019` | `builder/SELECT-PROMPT.md.bak-20261019` | 2026-10-18 18:32 | `319b9b441ac2` |
| `versions/builder/SELECT-PROMPT.md.bak-claude-20261021T1930Z` | `builder/SELECT-PROMPT.md.bak-claude-20261021T1930Z` | 2026-10-20 03:52 | `dd553bbf6b06` |
| `versions/builder/SELFDESIGN-PLAN.md.bak-20261019` | `builder/SELFDESIGN-PLAN.md.bak-20261019` | 2026-10-18 18:32 | `1a6cf95e329f` |
| `versions/builder/SELFDESIGN-PLAN.md.bak-claude-20261021T1930Z` | `builder/SELFDESIGN-PLAN.md.bak-claude-20261021T1930Z` | 2026-10-20 03:52 | `ed4493015915` |
| `versions/pipeline/blind_informed.sh.bak-20261020T190405Z` | `pipeline/blind_informed.sh.bak-20261020T190405Z` | 2026-10-20 19:04 | `1f9477c44323` |
| `versions/pipeline/blind_informed_ctr.sh.bak-20261020T213434Z` | `pipeline/blind_informed_ctr.sh.bak-20261020T213434Z` | 2026-10-20 21:34 | `d5bcf175a08f` |
| `versions/pipeline/blind_informed_ctr.sh.bak-20261020T233033Z` | `pipeline/blind_informed_ctr.sh.bak-20261020T233033Z` | 2026-10-20 21:34 | `5d5d1056e245` |
| `versions/pipeline/blind_informed_ctr.sh.bak-20261021T001849Z` | `pipeline/blind_informed_ctr.sh.bak-20261021T001849Z` | 2026-10-20 23:30 | `8c1b0e82a2da` |
| `versions/pipeline/harden_solved.sh.bak-20261020T233033Z` | `pipeline/harden_solved.sh.bak-20261020T233033Z` | 2026-10-20 08:16 | `f4985deb5766` |
| `versions/pipeline/harden_solved.sh.bak-20261021T154104Z` | `pipeline/harden_solved.sh.bak-20261021T154104Z` | 2026-10-21 15:41 | `306deb034717` |
| `versions/pipeline/queue.sh.bak-20261020T233033Z` | `pipeline/queue.sh.bak-20261020T233033Z` | 2026-10-18 22:03 | `1e1ec824aa01` |
| `versions/pipeline/run_harden.sh.bak-20261020T233033Z` | `pipeline/run_harden.sh.bak-20261020T233033Z` | 2026-10-20 04:41 | `71724993d442` |
| `versions/pipeline/run_harden.sh.bak-20261021` | `pipeline/run_harden.sh.bak-20261021` | 2026-10-21 15:41 | `644b3e393543` |
| `versions/pipeline/run_harden.sh.bak-20261021T001849Z` | `pipeline/run_harden.sh.bak-20261021T001849Z` | 2026-10-20 23:30 | `337942fdbaa2` |
| `versions/pipeline/run_harden.sh.bak-20261021T154104Z` | `pipeline/run_harden.sh.bak-20261021T154104Z` | 2026-10-21 15:41 | `82785e93e4e8` |
| `versions/pipeline/run_pipeline.sh.bak-20261020T224344Z` | `pipeline/run_pipeline.sh.bak-20261020T224344Z` | 2026-10-19 21:36 | `b7292dfbec3e` |
| `versions/pipeline/run_pipeline.sh.bak-20261020T233033Z` | `pipeline/run_pipeline.sh.bak-20261020T233033Z` | 2026-10-20 22:43 | `57516b62ea43` |
| `versions/pipeline/run_pipeline.sh.bak-20261021T001849Z` | `pipeline/run_pipeline.sh.bak-20261021T001849Z` | 2026-10-20 23:30 | `b33483afbccd` |
| `versions/pipeline/trial_summary.py.bak-20261021` | `pipeline/trial_summary.py.bak-20261021` | 2026-10-21 19:30 | `25aed3f11ce0` |
| `versions/ramp_lane.py.bak-40step` | `sibling2/ramp_lane.py.bak-40step` | 2026-10-24 05:15 | `e981d785e3c4` |
| `versions/run_fairfix.sh.bak-20261019` | `run_fairfix.sh.bak-20261019` | 2026-10-17 22:43 | `778a1b072fb9` |
| `versions/run_fairfix.sh.bak-20261020T233033Z` | `run_fairfix.sh.bak-20261020T233033Z` | 2026-10-20 04:41 | `f6364bc3501f` |
| `versions/run_fairfix.sh.bak-20261021T001849Z` | `run_fairfix.sh.bak-20261021T001849Z` | 2026-10-20 23:30 | `ed5b07e834f3` |
| `versions/run_fairness.sh.bak-20261020T233033Z` | `run_fairness.sh.bak-20261020T233033Z` | 2026-10-17 07:52 | `532f08285453` |
| `versions/run_fairness.sh.bak-20261021T001849Z` | `run_fairness.sh.bak-20261021T001849Z` | 2026-10-20 23:30 | `54474ba2de6d` |
| `versions/run_upgrade.sh.bak-20261020T233033Z` | `run_upgrade.sh.bak-20261020T233033Z` | 2026-10-20 05:08 | `6ed901ca9406` |
| `versions/run_upgrade.sh.bak-20261021T001849Z` | `run_upgrade.sh.bak-20261021T001849Z` | 2026-10-20 23:30 | `8fff4dedd325` |
