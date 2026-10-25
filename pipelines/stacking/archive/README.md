# pipelines/stacking/archive/

Old versions and retired pieces of the stacking pipeline.

**Nothing here is runnable as it is.** These files use the paths from before the 2026-10-25 reorganisation (`builder/`, `pipeline/`, `harness/`, `stacking/`, `sibling2/`, `build/trial.py`, ...). They are kept so that no earlier work is lost and every past run can be traced to the code that ran it. To revive one, port it to `common/paths.py` / `common/paths.sh` first.

## (top level)



| File | Was at | Last modified (UTC) | sha256 |
|---|---|---|---|
| `README-before-reorg.md` | `stacking/README.md` | 2026-10-24 18:42 | `0319e849ce0d` |

## night-chains-20261024/

One-off repair chains from the 2026-10-24/25 stacking night (fairfix, then gate, then unhold, then re-trial for single tasks). Their logs stay in `pipelines/stacking/out/`. The reusable pattern is documented in the stacking GUIDE.md (repair loop).

| File | Was at | Last modified (UTC) | sha256 |
|---|---|---|---|
| `night-chains-20261024/av_chain_20261024.sh` | `stacking/out/av_chain_20261024.sh` | 2026-10-24 21:23 | `c3d1670f4bc1` |
| `night-chains-20261024/comfyui_chain_20261024.sh` | `stacking/out/comfyui_chain_20261024.sh` | 2026-10-24 20:50 | `dc96e9d072a6` |
| `night-chains-20261024/held3_chain_20261025.sh` | `stacking/out/held3_chain_20261025.sh` | 2026-10-25 02:31 | `527aad584d10` |
| `night-chains-20261024/jenkins_chain_20261024.sh` | `stacking/out/jenkins_chain_20261024.sh` | 2026-10-25 00:00 | `6743063f9e6b` |
| `night-chains-20261024/kv_chain_20261024.sh` | `stacking/out/kv_chain_20261024.sh` | 2026-10-24 21:24 | `43a062dae450` |
| `night-chains-20261024/mjml_chain_20261024.sh` | `stacking/out/mjml_chain_20261024.sh` | 2026-10-24 20:28 | `3e3e7e0fa205` |
| `night-chains-20261024/mjml_regrade2_20261024.sh` | `stacking/out/mjml_regrade2_20261024.sh` | 2026-10-24 20:54 | `1e56ad11e27c` |
| `night-chains-20261024/mlflow_chain_20261025.sh` | `stacking/out/mlflow_chain_20261025.sh` | 2026-10-25 05:39 | `217357835d79` |
| `night-chains-20261024/py_chain_20261024.sh` | `stacking/out/py_chain_20261024.sh` | 2026-10-24 22:49 | `ebd58a5a021f` |
| `night-chains-20261024/relaunch_probe_20261025.sh` | `stacking/out/relaunch_probe_20261025.sh` | 2026-10-25 00:11 | `a66b23c92485` |
| `night-chains-20261024/reword_batch_20261024.sh` | `stacking/out/reword_batch_20261024.sh` | 2026-10-24 21:36 | `05632fc9fca8` |
| `night-chains-20261024/reword_chain_20261024.sh` | `stacking/out/reword_chain_20261024.sh` | 2026-10-24 21:36 | `15fbc79aabb7` |
| `night-chains-20261024/ride_along_20261024.sh` | `stacking/out/ride_along_20261024.sh` | 2026-10-24 18:58 | `11a8f9d69faf` |
| `night-chains-20261024/senaite_harness_chain_20261025.sh` | `stacking/out/senaite_harness_chain_20261025.sh` | 2026-10-25 01:48 | `b1afec6fed53` |
| `night-chains-20261024/siyuan_ctl_chain_20261025.sh` | `stacking/out/siyuan_ctl_chain_20261025.sh` | 2026-10-25 00:13 | `2554bcf129af` |
| `night-chains-20261024/sn_sy_chain_20261024.sh` | `stacking/out/sn_sy_chain_20261024.sh` | 2026-10-24 23:19 | `eb71a8e99a11` |

## one-off/

One-off stacking scripts (2026-10-23): regate batches, the 6-task fairness batch, candidate backup, and `stacking_restart.sh` (destructive: kills the queue and deletes builds; left non-executable).

| File | Was at | Last modified (UTC) | sha256 |
|---|---|---|---|
| `one-off/backup_candidates.sh` | `stacking/backup_candidates.sh` | 2026-10-23 20:20 | `71ea7181bf6f` |
| `one-off/fairness_batch.sh` | `stacking/fairness_batch.sh` | 2026-10-23 15:39 | `9dbe48859d7e` |
| `one-off/regate.sh` | `stacking/regate.sh` | 2026-10-23 14:50 | `fb8cf1028477` |
| `one-off/regate_batch.sh` | `stacking/regate_batch.sh` | 2026-10-23 14:53 | `d43b05bb904c` |
| `one-off/regate_fixed2.sh` | `stacking/regate_fixed2.sh` | 2026-10-23 15:18 | `d9f1f2b7235e` |
| `one-off/stacking_restart.sh` | `stacking/stacking_restart.sh` | 2026-10-23 02:57 | `ef2b07cfc825` |

## versions/

`.bak-*` backups of files that are still live. The live file is the CURRENT version; each backup name carries the date it was replaced (UTC). Compare with `diff` against the live file.

| File | Was at | Last modified (UTC) | sha256 |
|---|---|---|---|
| `versions/README.md.bak-20261024T0900Z` | `stacking/README.md.bak-20261024T0900Z` | 2026-10-22 19:05 | `d0790d864659` |
| `versions/README.md.bak-20261024T1809Z` | `stacking/README.md.bak-20261024T1809Z` | 2026-10-24 16:57 | `dee1bc57756e` |
| `versions/README.md.bak-upgrade-20261024` | `stacking/README.md.bak-upgrade-20261024` | 2026-10-24 18:10 | `9a21feb356fa` |
| `versions/STACKING-BUILD-ADDENDUM.md.bak-20261024T0900Z` | `stacking/STACKING-BUILD-ADDENDUM.md.bak-20261024T0900Z` | 2026-10-22 23:52 | `9f1cf4946c5f` |
| `versions/STACKING-BUILD-ADDENDUM.md.bak-20261024T1809Z` | `stacking/STACKING-BUILD-ADDENDUM.md.bak-20261024T1809Z` | 2026-10-24 16:57 | `7eebf50c2ae6` |
| `versions/STACKING-FAIRNESS-ADDENDUM.md.bak-20261024T0900Z` | `stacking/STACKING-FAIRNESS-ADDENDUM.md.bak-20261024T0900Z` | 2026-10-22 12:24 | `2139185cf712` |
| `versions/STACKING-FAIRNESS-ADDENDUM.md.bak-20261024T1809Z` | `stacking/STACKING-FAIRNESS-ADDENDUM.md.bak-20261024T1809Z` | 2026-10-24 16:57 | `84f60f8de660` |
| `versions/STACKING-LISTING-CHECK.md.bak-20261024T1809Z` | `stacking/STACKING-LISTING-CHECK.md.bak-20261024T1809Z` | 2026-10-24 16:57 | `d2c160fc7c72` |
| `versions/STACKING-LISTING-CHECK.md.bak-v1-20261024` | `stacking/STACKING-LISTING-CHECK.md.bak-v1-20261024` | 2026-10-24 18:09 | `d4a24b98a09a` |
| `versions/STACKING-LISTING-CHECK.md.bak-v2-20261024` | `stacking/STACKING-LISTING-CHECK.md.bak-v2-20261024` | 2026-10-24 18:21 | `91b6b2f7a85c` |
| `versions/STACKING-UPGRADE-PROMPT.md.bak-v1-20261024` | `stacking/STACKING-UPGRADE-PROMPT.md.bak-v1-20261024` | 2026-10-24 18:41 | `8333a18e644d` |
| `versions/check_stack.py.bak-20261024T1809Z` | `stacking/check_stack.py.bak-20261024T1809Z` | 2026-10-22 23:52 | `be73927dd3fb` |
| `versions/listing_verdict.py.bak-20261024T1809Z` | `stacking/listing_verdict.py.bak-20261024T1809Z` | 2026-10-24 16:57 | `37429120c1cb` |
| `versions/run_fairfix_stack.sh.bak-20261024T1809Z` | `stacking/run_fairfix_stack.sh.bak-20261024T1809Z` | 2026-10-22 17:54 | `1b4571d4fc01` |
| `versions/run_fairfix_stack.sh.bak-brief-20261024` | `stacking/run_fairfix_stack.sh.bak-brief-20261024` | 2026-10-24 18:09 | `e44ed39baf69` |
| `versions/run_listing_check.sh.bak-20261024T1809Z` | `stacking/run_listing_check.sh.bak-20261024T1809Z` | 2026-10-24 16:57 | `9b6f3df71d27` |
| `versions/run_stack_pipeline.sh.bak-20261024T0900Z` | `stacking/run_stack_pipeline.sh.bak-20261024T0900Z` | 2026-10-22 23:52 | `bac85e509d0b` |
| `versions/run_stack_pipeline.sh.bak-20261024T1809Z` | `stacking/run_stack_pipeline.sh.bak-20261024T1809Z` | 2026-10-24 16:57 | `11c6540ffb5d` |
| `versions/stk_queue.py.bak-20261024T0900Z` | `stacking/stk_queue.py.bak-20261024T0900Z` | 2026-10-22 19:02 | `011a7d3aa7c2` |
