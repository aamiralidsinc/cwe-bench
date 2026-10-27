# budibase-datasource-credential-leak

Build ID `stk-budibase-12672`; delivered 2026-10-27 in client commit 16a1d56.

| Field | Value |
|---|---|
| slug | stk-budibase-12672 |
| delivered_as | budibase-datasource-credential-leak |
| client_commit | 16a1d56 |
| delivered_date | 2026-10-27 |
| track | stacking |
| round | scale-b1 |
| built_date | 2026-10-26 |
| repo | https://github.com/budibase/budibase |
| cwe_id | CWE-200 |
| advisory | GHSA-MQHR-6J6H-74P5 |
| vulnerable_commit | 5e19b935536d6d1be1f47100e43c6fb30917826e |
| fix_commit | 8b1bca71501b11c68310351ef4f2c3028b2d5f08 |
| deepseek | **failed 0/3** [0.8889, 0.6667, 0.8889] |
| mimo | **failed 0/3** [0.8889, 0.6667, 0.8889] |
| fairness | READY |
| decision | KEEP 2026-10-27 |

## Counted runs (job/trial = reward)

- deepseek-flash[1m]:stk-budibase-12672-deepseek-r1-20261026-205641-n002/stk-budibase-12672__HNSVVXs=0.8889
- mimo-v2.6-pro:stk-budibase-12672-mimo-r1-20261026-205209-n001/stk-budibase-12672__Fzxd3DE=0.8889
- deepseek-flash[1m]:stk-budibase-12672-deepseek-r2-20261026-214330-n003/stk-budibase-12672__Mfw7AyG=0.6667
- deepseek-flash[1m]:stk-budibase-12672-deepseek-r3-20261026-221546-n004/stk-budibase-12672__ZCifyuE=0.8889
- mimo-v2.6-pro:stk-budibase-12672-mimo-r2-20261026-230323-n002/stk-budibase-12672__gSiBxAp=0.6667
- mimo-v2.6-pro:stk-budibase-12672-mimo-r3-20261027-004034-n004/stk-budibase-12672__oqzdmSq=0.8889

## Records

- VM build records: ~/cwe-bench/build/stk-budibase-12672/ (FAIRNESS.md, HUMAN-DECISION.md, AUDIT-NOTES.md, build notes, gate reports)
- VM task package: ~/cwe-bench/tasks/stk-budibase-12672/
- VM trial folders: ~/.tb-graders/cwe/jobs/<job>/<trial>/ (postmortem-*/verdict.json = audit)
- Locked run archive: ~/.tb-graders/cwe/archive/
