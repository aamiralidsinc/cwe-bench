# cognee-missing-authorization

Build ID `stk-cognee-723`; delivered 2026-10-27 in client commit a74e1ac.

| Field | Value |
|---|---|
| slug | stk-cognee-723 |
| delivered_as | cognee-missing-authorization |
| client_commit | a74e1ac |
| delivered_date | 2026-10-27 |
| track | stacking |
| round | scale-b1 |
| built_date | 2026-10-26 |
| repo | https://github.com/topoteretes/cognee |
| cwe_id | CWE-862 |
| advisory | GHSA-49f7-whx5-4256 / CVE-2026-58473 |
| vulnerable_commit | 4067f0b8a255f3a511a71cc0806b9f20dd73c31b |
| fix_commit | d10b1b77e2157c6238fd4d1acb1923a048991699,10971db1b0bd97e88f96bd2a9ffb3edb7b22bcd0,ebcf82412d0954f5c5018444f7eee8d96fee5113 |
| deepseek | **failed 0/3** [0.75, 0.75, 0.75] (+1 ungraded) |
| mimo | **failed 0/4** [0.75, 0.75, 0.75, 0.75] |
| fairness | READY |
| decision | KEEP 2026-10-27 |

## Counted runs (job/trial = reward)

- mimo-v2.6-pro:stk-cognee-723-mimo-r1-20261027-043647-n001/stk-cognee-723__uBfKHmc=0.75
- deepseek-flash[1m]:stk-cognee-723-deepseek-r1-20261027-153316-n001/stk-cognee-723__z5xrmiL=0.75
- mimo-v2.6-pro:stk-cognee-723-mimo-r1-20261027-153343-n001/stk-cognee-723__492PWhc=0.75
- deepseek-flash[1m]:stk-cognee-723-deepseek-r2-20261027-161218-n002/stk-cognee-723__uwXoxzF=0.75
- mimo-v2.6-pro:stk-cognee-723-mimo-r2-20261027-162342-n002/stk-cognee-723__ygYX67X=0.75
- deepseek-flash[1m]:stk-cognee-723-deepseek-r3-20261027-162546-n003/stk-cognee-723__qMjCvSX=0.75
- mimo-v2.6-pro:stk-cognee-723-mimo-r3-20261027-172816-n003/stk-cognee-723__Ado8PF3=0.75

## Records

- VM build records: ~/cwe-bench/build/stk-cognee-723/ (FAIRNESS.md, HUMAN-DECISION.md, AUDIT-NOTES.md, build notes, gate reports)
- VM task package: ~/cwe-bench/tasks/stk-cognee-723/
- VM trial folders: ~/.tb-graders/cwe/jobs/<job>/<trial>/ (postmortem-*/verdict.json = audit)
- Locked run archive: ~/.tb-graders/cwe/archive/
