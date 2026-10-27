# dbhub-readonly-mode-write-bypass

Build ID `stk-dbhub-12733`; delivered 2026-10-26 in client commit 09aaadd.

| Field | Value |
|---|---|
| slug | stk-dbhub-12733 |
| delivered_as | dbhub-readonly-mode-write-bypass |
| client_commit | 09aaadd |
| delivered_date | 2026-10-26 |
| track | stacking |
| round | scale-b1 |
| built_date | 2026-10-26 |
| repo | https://github.com/bytebase/dbhub |
| cwe_id | CWE-863 |
| advisory | GHSA-mwwr-p57h-56pf / GHSA-7rgf-cwgq-c2qc / GHSA-m689-287g-5xpc / GHSA-j656-3hf2-fvjc |
| vulnerable_commit | d65c6b424e9d10678fb6f7dda93fba180d7baff9 |
| fix_commit | 872bb338f7d31f6afe517a076ac3e3edafaaaf08 |
| deepseek | **failed 0/3** [0, 0.8947, 0] |
| mimo | **failed 0/3** [0.7368, 0.5789, 0.8947] |
| fairness | READY |
| decision | KEEP 2026-10-27 |

## Counted runs (job/trial = reward)

- deepseek-flash[1m]:stk-dbhub-12733-deepseek-r1-20261026-155314-n001/stk-dbhub-12733__HmACosb=0.0
- mimo-v2.6-pro:stk-dbhub-12733-mimo-r1-20261026-155354-n001/stk-dbhub-12733__eNS4Do4=0.7368
- deepseek-flash[1m]:stk-dbhub-12733-deepseek-r2-20261026-161350-n002/stk-dbhub-12733__Quf5cVY=0.8947
- mimo-v2.6-pro:stk-dbhub-12733-mimo-r2-20261026-163640-n002/stk-dbhub-12733__WhNnuw9=0.5789
- deepseek-flash[1m]:stk-dbhub-12733-deepseek-r3-20261026-163718-n003/stk-dbhub-12733__S54KTDg=0.0
- mimo-v2.6-pro:stk-dbhub-12733-mimo-r3-20261026-225017-n001/stk-dbhub-12733__j9Fdpfy=0.8947

## Records

- VM build records: ~/cwe-bench/build/stk-dbhub-12733/ (FAIRNESS.md, HUMAN-DECISION.md, AUDIT-NOTES.md, build notes, gate reports)
- VM task package: ~/cwe-bench/tasks/stk-dbhub-12733/
- VM trial folders: ~/.tb-graders/cwe/jobs/<job>/<trial>/ (postmortem-*/verdict.json = audit)
- Locked run archive: ~/.tb-graders/cwe/archive/
