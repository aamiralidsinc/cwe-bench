# passenger-temp-dir-symlink-reuse

Build ID `stk-passenger-ghsaqw8w`; delivered 2026-10-26 in client commit 9ca29b3.

| Field | Value |
|---|---|
| slug | stk-passenger-ghsaqw8w |
| delivered_as | passenger-temp-dir-symlink-reuse |
| client_commit | 9ca29b3 |
| delivered_date | 2026-10-26 |
| track | stacking |
| round | scale-b1 |
| built_date | 2026-10-26 |
| repo | https://github.com/phusion/passenger |
| cwe_id | CWE-59 |
| advisory | GHSA-c7j7-p5jq-26ff; GHSA-qw8w-2xcp-xg59 |
| vulnerable_commit | 74ed789f36fe7f697b2c95c8cd1cda3c48882857 |
| fix_commit | 34b1087870c2, 94428057c602 |
| deepseek | **failed 0/3** [0.8333, 0.8333, 0.8333] |
| mimo | **failed 0/3** [0.6667, 0.8333, 0.8333] |
| fairness | READY |
| decision | KEEP 2026-10-26 |

## Counted runs (job/trial = reward)

- deepseek-flash[1m]:stk-passenger-ghsaqw8w-deepseek-r1-20261026-121334-n001/stk-passenger-ghsaqw8w__ijKQCLf=0.8333
- mimo-v2.6-pro:stk-passenger-ghsaqw8w-mimo-r1-20261026-121340-n001/stk-passenger-ghsaqw8w__Veh7QtJ=0.6667
- deepseek-flash[1m]:stk-passenger-ghsaqw8w-deepseek-r2-20261026-124651-n002/stk-passenger-ghsaqw8w__xKsqnk2=0.8333
- mimo-v2.6-pro:stk-passenger-ghsaqw8w-mimo-r2-20261026-131117-n002/stk-passenger-ghsaqw8w__zFE7WDG=0.8333
- deepseek-flash[1m]:stk-passenger-ghsaqw8w-deepseek-r3-20261026-132159-n003/stk-passenger-ghsaqw8w__3Egpq5s=0.8333
- mimo-v2.6-pro:stk-passenger-ghsaqw8w-mimo-r3-20261026-135738-n003/stk-passenger-ghsaqw8w__JyvfmbZ=0.8333

## Records

- VM build records: ~/cwe-bench/build/stk-passenger-ghsaqw8w/ (FAIRNESS.md, HUMAN-DECISION.md, AUDIT-NOTES.md, build notes, gate reports)
- VM task package: ~/cwe-bench/tasks/stk-passenger-ghsaqw8w/
- VM trial folders: ~/.tb-graders/cwe/jobs/<job>/<trial>/ (postmortem-*/verdict.json = audit)
- Locked run archive: ~/.tb-graders/cwe/archive/
