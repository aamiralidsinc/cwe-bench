# tomcat-cluster-encryption-bypass

Build ID `stk-tomcat-ghsa69r9`; delivered 2026-10-27 in client commit 8143235.

| Field | Value |
|---|---|
| slug | stk-tomcat-ghsa69r9 |
| delivered_as | tomcat-cluster-encryption-bypass |
| client_commit | 8143235 |
| delivered_date | 2026-10-27 |
| track | stacking |
| round | scale-b1 |
| built_date | 2026-10-26 |
| repo | https://github.com/apache/tomcat |
| cwe_id | CWE-311 |
| advisory | GHSA-h468-7pvh-8vr8; GHSA-69r9-qgr7-g2wj |
| vulnerable_commit | 81c7afb323cf4f12f8b49a422962ad3588917e9c |
| fix_commit | 0112ed22abfc;607ebc0fa522;6d955cceca84;1fab40ccc752;55f3eb914823;776e12b3e2b0 |
| deepseek | **failed 0/3** [0.8571, 0, 0] |
| mimo | **failed 0/3** [0.8571, 0.8571, 0.8571] |
| fairness | READY |
| decision | KEEP 2026-10-27 |

## Counted runs (job/trial = reward)

- deepseek-flash[1m]:stk-tomcat-ghsa69r9-deepseek-r1-20261027-003245-n001/stk-tomcat-ghsa69r9__Pm5R9Ao=0.8571
- mimo-v2.6-pro:stk-tomcat-ghsa69r9-mimo-r1-20261027-003303-n001/stk-tomcat-ghsa69r9__N5sgkgJ=0.8571
- deepseek-flash[1m]:stk-tomcat-ghsa69r9-deepseek-r2-20261027-010456-n002/stk-tomcat-ghsa69r9__4brEuo7=0.0
- deepseek-flash[1m]:stk-tomcat-ghsa69r9-deepseek-r3-20261027-013136-n003/stk-tomcat-ghsa69r9__kQSzrqc=0.0
- mimo-v2.6-pro:stk-tomcat-ghsa69r9-mimo-r2-20261027-015650-n002/stk-tomcat-ghsa69r9__y8PDRE5=0.8571
- mimo-v2.6-pro:stk-tomcat-ghsa69r9-mimo-r3-20261027-023158-n003/stk-tomcat-ghsa69r9__oVTWLej=0.8571

## Records

- VM build records: ~/cwe-bench/build/stk-tomcat-ghsa69r9/ (FAIRNESS.md, HUMAN-DECISION.md, AUDIT-NOTES.md, build notes, gate reports)
- VM task package: ~/cwe-bench/tasks/stk-tomcat-ghsa69r9/
- VM trial folders: ~/.tb-graders/cwe/jobs/<job>/<trial>/ (postmortem-*/verdict.json = audit)
- Locked run archive: ~/.tb-graders/cwe/archive/
