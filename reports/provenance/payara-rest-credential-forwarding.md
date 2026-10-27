# payara-rest-credential-forwarding

Build ID `stk-payara-29001`; delivered 2026-10-26 in client commit 09aaadd.

| Field | Value |
|---|---|
| slug | stk-payara-29001 |
| delivered_as | payara-rest-credential-forwarding |
| client_commit | 09aaadd |
| delivered_date | 2026-10-26 |
| track | stacking |
| round | scale-b1 |
| built_date | 2026-10-26 |
| repo | https://github.com/payara/payara |
| cwe_id | CWE-352 |
| advisory | GHSA-X939-7FQ5-V9V6 (CVE-2026-12986) |
| vulnerable_commit | a67eae17e621925b072fbc5880f6bd70a4dad5b6 |
| fix_commit | be83ab093692bafb09125323f3fdefaeab9cc398 |
| deepseek | **failed 0/3** [0.625, 0.375, 0.375] |
| mimo | **failed 0/3** [0.375, 0.375, 0.375] |
| fairness | READY |
| decision | KEEP 2026-10-27 |

## Counted runs (job/trial = reward)

- deepseek-flash[1m]:stk-payara-29001-deepseek-r1-20261026-060013-n001/stk-payara-29001__rYCUyTB=0.625
- mimo-v2.6-pro:stk-payara-29001-mimo-r1-20261026-060016-n001/stk-payara-29001__pf9t7Ds=0.375
- deepseek-flash[1m]:stk-payara-29001-deepseek-r2-20261026-064216-n002/stk-payara-29001__4ned6mF=0.375
- mimo-v2.6-pro:stk-payara-29001-mimo-r2-20261026-064320-n002/stk-payara-29001__fpEnk6G=0.375
- deepseek-flash[1m]:stk-payara-29001-deepseek-r3-20261026-065959-n003/stk-payara-29001__VE5n7xT=0.375
- mimo-v2.6-pro:stk-payara-29001-mimo-r3-20261026-071059-n003/stk-payara-29001__6BsPjFj=0.375

## Records

- VM build records: ~/cwe-bench/build/stk-payara-29001/ (FAIRNESS.md, HUMAN-DECISION.md, AUDIT-NOTES.md, build notes, gate reports)
- VM task package: ~/cwe-bench/tasks/stk-payara-29001/
- VM trial folders: ~/.tb-graders/cwe/jobs/<job>/<trial>/ (postmortem-*/verdict.json = audit)
- Locked run archive: ~/.tb-graders/cwe/archive/
