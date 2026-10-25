# common/archive/

Old versions and retired pieces of the shared infrastructure (`common/`).

**Nothing here is runnable as it is.** These files use the paths from before the 2026-10-25 reorganisation (`builder/`, `pipeline/`, `harness/`, `stacking/`, `sibling2/`, `build/trial.py`, ...). They are kept so that no earlier work is lost and every past run can be traced to the code that ran it. To revive one, port it to `common/paths.py` / `common/paths.sh` first.

## logs/

Logs that sat in the code folders.

| File | Was at | Last modified (UTC) | sha256 |
|---|---|---|---|
| `logs/apply_docker_tweaks.log` | `pipeline/apply_docker_tweaks.log` | 2026-10-19 21:37 | `d0c09e4a299b` |
| `logs/stop_lane.log` | `pipeline/stop_lane.log` | 2026-10-19 21:39 | `a331495fc3ee` |

## old-prompts/

Superseded prompt drafts: first screener draft, screener v1, the first task-build prompt draft, and the round-1 stacking builder notes.

| File | Was at | Last modified (UTC) | sha256 |
|---|---|---|---|
| `old-prompts/BUILDER-stacking.md` | `builder/BUILDER-stacking.md` | 2026-10-15 15:04 | `9789268f8a13` |
| `old-prompts/PROMPT-screener.md` | `builder/PROMPT-screener.md` | 2026-10-16 19:57 | `598fe38d87dc` |
| `old-prompts/PROMPT-task-build.md` | `builder/PROMPT-task-build.md` | 2026-10-21 14:21 | `2767b5a40a44` |
| `old-prompts/SCREENER-PROMPT-v1.md` | `builder/SCREENER-PROMPT-v1.md` | 2026-10-16 23:49 | `197318d50b9e` |

## templates-frontier-stale/

A stale staging copy of `common/builder/templates/` (its `test.sh` is older).

| File | Was at | Last modified (UTC) | sha256 |
|---|---|---|---|
| `templates-frontier-stale/claude-code.Dockerfile.snippet` | `builder/templates-frontier/claude-code.Dockerfile.snippet` | 2026-10-21 14:05 | `35176b2452e7` |
| `templates-frontier-stale/environment.Dockerfile` | `builder/templates-frontier/environment.Dockerfile` | 2026-10-21 14:03 | `88d32c82c926` |
| `templates-frontier-stale/score.py` | `builder/templates-frontier/score.py` | 2026-10-21 14:04 | `8f9318207774` |
| `templates-frontier-stale/task.toml` | `builder/templates-frontier/task.toml` | 2026-10-21 14:02 | `23dccd1464c8` |
| `templates-frontier-stale/test.sh` | `builder/templates-frontier/test.sh` | 2026-10-21 14:04 | `9402e74cd809` |
| `templates-frontier-stale/tests.Dockerfile` | `builder/templates-frontier/tests.Dockerfile` | 2026-10-21 14:03 | `e8e5f107f57d` |

## versions/

`.bak-*` backups of files that are still live. The live file is the CURRENT version; each backup name carries the date it was replaced (UTC). Compare with `diff` against the live file.

| File | Was at | Last modified (UTC) | sha256 |
|---|---|---|---|
| `versions/build/audit_results.py.bak-20261020T230715Z` | `build/audit_results.py.bak-20261020T230715Z` | 2026-10-20 23:07 | `11198b04f060` |
| `versions/build/harvest_code.py.bak-20261021T141851Z` | `build/harvest_code.py.bak-20261021T141851Z` | 2026-10-21 14:18 | `8e49f2119dcb` |
| `versions/build/queue_offline.py.bak-20261020T190314Z` | `build/queue_offline.py.bak-20261020T190314Z` | 2026-10-16 05:22 | `a03bf1d07d96` |
| `versions/build/regrade.py.bak-root-20261024` | `build/regrade.py.bak-root-20261024` | 2026-10-15 18:40 | `50aee67db62b` |
| `versions/build/regrade_from_code.py.bak-root-20261024` | `build/regrade_from_code.py.bak-root-20261024` | 2026-10-16 01:55 | `f7ccb3091ea2` |
| `versions/build/review_flags.py.bak-20261020T233033Z` | `build/review_flags.py.bak-20261020T233033Z` | 2026-10-15 18:44 | `2c476a0e7c3d` |
| `versions/build/review_flags.py.bak-20261021T001849Z` | `build/review_flags.py.bak-20261021T001849Z` | 2026-10-20 23:30 | `4e4a636d03e0` |
| `versions/build/trial.py.bak-20261020T190314Z` | `build/trial.py.bak-20261020T190314Z` | 2026-10-17 20:01 | `28bf2949bc4d` |
| `versions/build/trial.py.bak-20261020T233033Z` | `build/trial.py.bak-20261020T233033Z` | 2026-10-20 19:17 | `a2e0e88fe1fb` |
| `versions/build/trial.py.bak-20261021T001849Z` | `build/trial.py.bak-20261021T001849Z` | 2026-10-20 23:30 | `152daa34f045` |
| `versions/builder/BLIND-FIX-BRIEF.md.bak-20261020T233354Z` | `builder/BLIND-FIX-BRIEF.md.bak-20261020T233354Z` | 2026-10-16 12:12 | `aded32512c69` |
| `versions/builder/BUILDER.md.bak-20261019` | `builder/BUILDER.md.bak-20261019` | 2026-10-16 13:17 | `7499dc083998` |
| `versions/builder/BUILDER.md.bak-20261020T223912Z` | `builder/BUILDER.md.bak-20261020T223912Z` | 2026-10-20 03:52 | `b92a4d91fa66` |
| `versions/builder/BUILDER.md.bak-20261020T233354Z` | `builder/BUILDER.md.bak-20261020T233354Z` | 2026-10-20 22:39 | `5944951873a0` |
| `versions/builder/BUILDER.md.bak-20261021T142112Z` | `builder/BUILDER.md.bak-20261021T142112Z` | 2026-10-21 14:21 | `c12dfccefb74` |
| `versions/builder/FAIRNESS-REVIEW-BRIEF.md.bak-20261019` | `builder/FAIRNESS-REVIEW-BRIEF.md.bak-20261019` | 2026-10-20 00:54 | `2efe6e4ad59e` |
| `versions/builder/FAIRNESS-REVIEW-BRIEF.md.bak-20261020T000740Z` | `builder/FAIRNESS-REVIEW-BRIEF.md.bak-20261020T000740Z` | 2026-10-20 00:07 | `f3fc0cf47c87` |
| `versions/builder/FAIRNESS-REVIEW-BRIEF.md.bak2-20261020T005424Z` | `builder/FAIRNESS-REVIEW-BRIEF.md.bak2-20261020T005424Z` | 2026-10-20 00:54 | `58d33b92950b` |
| `versions/builder/PROMPT-task-build.md.bak-20261021T142112Z` | `builder/PROMPT-task-build.md.bak-20261021T142112Z` | 2026-10-21 14:21 | `921c633fded4` |
| `versions/builder/SCREENER-PROMPT-v2.md.bak-20261019` | `builder/SCREENER-PROMPT-v2.md.bak-20261019` | 2026-10-17 00:47 | `e53c39d0d8fb` |
| `versions/builder/TASK-BUILD-PROMPT-v1.md.bak-20261019` | `builder/TASK-BUILD-PROMPT-v1.md.bak-20261019` | 2026-10-16 21:23 | `201861742f46` |
| `versions/builder/TASK-BUILD-PROMPT-v1.md.bak-20261021T142112Z` | `builder/TASK-BUILD-PROMPT-v1.md.bak-20261021T142112Z` | 2026-10-21 14:21 | `6f5fc5a60fa7` |
| `versions/builder/TASK-BUILD-PROMPT-v1.md.bak-claude-20261021T1930Z` | `builder/TASK-BUILD-PROMPT-v1.md.bak-claude-20261021T1930Z` | 2026-10-21 14:21 | `8756bdc79458` |
| `versions/builder/gate.py.bak-20261020T071542Z` | `builder/gate.py.bak-20261020T071542Z` | 2026-10-20 07:15 | `bb05cf279f7b` |
| `versions/builder/gate.py.bak-20261020T190314Z` | `builder/gate.py.bak-20261020T190314Z` | 2026-10-20 07:16 | `2d9c38424bd5` |
| `versions/builder/gate.py.bak-20261020T221311Z` | `builder/gate.py.bak-20261020T221311Z` | 2026-10-20 19:17 | `94fc7831b662` |
| `versions/builder/gate.py.bak-20261020T224344Z` | `builder/gate.py.bak-20261020T224344Z` | 2026-10-20 22:13 | `9e88d99953bd` |
| `versions/builder/gate.py.bak-20261020T233354Z` | `builder/gate.py.bak-20261020T233354Z` | 2026-10-20 22:43 | `f8185c85f1e2` |
| `versions/builder/gate.py.bak-20261021T001849Z` | `builder/gate.py.bak-20261021T001849Z` | 2026-10-20 23:33 | `b0f2990905d5` |
| `versions/builder/gate.py.bak-20261021T141851Z` | `builder/gate.py.bak-20261021T141851Z` | 2026-10-21 14:18 | `0319d7203d8a` |
| `versions/builder/gate.py.bak-allowhost` | `builder/gate.py.bak-allowhost` | 2026-10-23 07:58 | `ec3e4d942569` |
| `versions/builder/gate.py.bak-expectfix` | `builder/gate.py.bak-expectfix` | 2026-10-23 00:53 | `1c3b80934c75` |
| `versions/builder/gate.py.bak-harborretry` | `builder/gate.py.bak-harborretry` | 2026-10-23 05:31 | `15cc2bf29981` |
| `versions/builder/gate.py.bak-impfix-20261021T174734Z` | `builder/gate.py.bak-impfix-20261021T174734Z` | 2026-10-21 17:47 | `4c3b1bcdcc67` |
| `versions/builder/gate.py.bak-leaks-20261021T144850Z` | `builder/gate.py.bak-leaks-20261021T144850Z` | 2026-10-21 14:48 | `ec7211a7709e` |
| `versions/builder/gate.py.bak-seq-20261024T084432Z` | `builder/gate.py.bak-seq-20261024T084432Z` | 2026-10-23 07:58 | `b52fea4182f0` |
| `versions/builder/score.py` | `builder/templates.bak-20261021T142205Z/score.py` | 2026-10-13 23:14 | `ad4f3d3a4915` |
| `versions/builder/task.toml` | `builder/templates.bak-20261021T142205Z/task.toml` | 2026-10-16 11:20 | `8024c2a76db8` |
| `versions/builder/test.sh` | `builder/templates.bak-20261021T142205Z/test.sh` | 2026-10-16 11:20 | `3de3b58b2df2` |
| `versions/builder/test.sh.bak-out-20261021T150032Z` | `builder/templates/test.sh.bak-out-20261021T150032Z` | 2026-10-21 15:00 | `7ce3a6332d24` |
| `versions/builder/test.sh.bak-runacc-20261021T145325Z` | `builder/templates/test.sh.bak-runacc-20261021T145325Z` | 2026-10-21 14:53 | `9402e74cd809` |
| `versions/builder/test.sh.bak-scoretail-20261021T150314Z` | `builder/templates/test.sh.bak-scoretail-20261021T150314Z` | 2026-10-21 15:03 | `51aaede85b9f` |
| `versions/harness/claude-code.Dockerfile.snippet.bak-20261021T142205Z` | `harness/claude-code.Dockerfile.snippet.bak-20261021T142205Z` | 2026-10-13 20:07 | `9d3cb7a4eb70` |
| `versions/harness/run_trial.sh.bak-20261021T141951Z` | `harness/run_trial.sh.bak-20261021T141951Z` | 2026-10-21 14:19 | `3679ee04fe66` |
| `versions/pipeline/advance_one.sh.bak-20261020T233033Z` | `pipeline/advance_one.sh.bak-20261020T233033Z` | 2026-10-19 23:16 | `805407503f6a` |
| `versions/pipeline/agent_status.py.bak-20261021T001849Z` | `pipeline/agent_status.py.bak-20261021T001849Z` | 2026-10-20 23:30 | `12cdeaf67fd8` |
| `versions/pipeline/auto_trial_launch.sh.bak-20261020T233033Z` | `pipeline/auto_trial_launch.sh.bak-20261020T233033Z` | 2026-10-20 07:46 | `2cacf2d08ab8` |
| `versions/pipeline/backstage_validate.sh.bak-20261020T233033Z` | `pipeline/backstage_validate.sh.bak-20261020T233033Z` | 2026-10-19 11:02 | `acc608771da8` |
| `versions/pipeline/faircheck_rerun.sh.bak-20261020T233033Z` | `pipeline/faircheck_rerun.sh.bak-20261020T233033Z` | 2026-10-20 00:13 | `f0018caff411` |
| `versions/pipeline/fairness_candidates.sh.bak-20261020T233033Z` | `pipeline/fairness_candidates.sh.bak-20261020T233033Z` | 2026-10-19 22:38 | `4586fd7d4ac2` |
| `versions/pipeline/gate_one_ds.sh.bak-20261020T064511Z` | `pipeline/gate_one_ds.sh.bak-20261020T064511Z` | 2026-10-20 06:45 | `51f218f0abd7` |
| `versions/pipeline/gate_one_ds.sh.bak-20261020T224344Z` | `pipeline/gate_one_ds.sh.bak-20261020T224344Z` | 2026-10-20 06:45 | `9f52db9ea10e` |
| `versions/pipeline/gate_one_ds.sh.bak-20261021T001849Z` | `pipeline/gate_one_ds.sh.bak-20261021T001849Z` | 2026-10-20 22:43 | `ce2c49f915c4` |
| `versions/pipeline/snapshot_experiment.sh.bak-20261020T233033Z` | `pipeline/snapshot_experiment.sh.bak-20261020T233033Z` | 2026-10-20 04:35 | `418246385dbd` |
| `versions/pipeline/snapshot_experiment.sh.bak-ctlglob-20261024` | `pipeline/snapshot_experiment.sh.bak-ctlglob-20261024` | 2026-10-20 23:31 | `b795590b59d9` |
| `versions/pipeline/trial_set.sh.bak-20261020T233033Z` | `pipeline/trial_set.sh.bak-20261020T233033Z` | 2026-10-18 23:54 | `7bef03a222e0` |
| `versions/pipeline/validate_fresh.sh.bak-20261020T233033Z` | `pipeline/validate_fresh.sh.bak-20261020T233033Z` | 2026-10-19 15:23 | `ff6ba58871b2` |
| `versions/pipeline/validate_loop.sh.bak-20261020T233033Z` | `pipeline/validate_loop.sh.bak-20261020T233033Z` | 2026-10-19 15:02 | `8f3aa7b1cf30` |
| `versions/run_blindfix.sh.bak-20261020T223508Z` | `run_blindfix.sh.bak-20261020T223508Z` | 2026-10-17 17:43 | `431d840816b6` |
| `versions/run_blindfix.sh.bak-20261021T001849Z` | `run_blindfix.sh.bak-20261021T001849Z` | 2026-10-20 22:49 | `a6f423184cbb` |
