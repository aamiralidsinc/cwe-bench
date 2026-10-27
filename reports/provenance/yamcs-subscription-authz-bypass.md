# yamcs-subscription-authz-bypass

Build ID `yamcs-ds`; delivered 2026-10-21 in client commit ea4ce53.

| Field | Value |
|---|---|
| slug | yamcs-ds |
| delivered_as | yamcs-subscription-authz-bypass |
| client_commit | ea4ce53 |
| delivered_date | 2026-10-21 |
| track | injection |
| round | pre-scale round, built 2026-10-19 |
| built_date | 2026-10-19 |
| repo | https://github.com/yamcs/yamcs |
| cwe_id | CWE-862 |
| advisory | GHSA-FWWW-CP23-7F5G |
| vulnerable_commit | b566beceba98cc35514b0e1519be126b8c5a0438 |
| fix_commit | 0691731846c5a0aca81b88fabbd2cd51d56fe076 |
| deepseek | SOLVED 1/4 (1 solves counted, not audited) |
| mimo | SOLVED 1/4 (1 solves counted, not audited) |
| fairness | READY |
| decision |  |

## Counted runs (job/trial = reward)

- deepseek-flash[1m]:yamcs-ds-deepseek-r1-20261021-043051-n001/yamcs-ds__spukAwY=0.0
- deepseek-flash[1m]:yamcs-ds-deepseek-r2-20261021-050437-n002/yamcs-ds__2kahZX6=0.0
- deepseek-flash[1m]:yamcs-ds-deepseek-r3-20261021-053106-n003/yamcs-ds__qPTdHrn=0.0
- mimo-v2.6-pro:yamcs-ds-mimo-r1-20261021-060031-n004/yamcs-ds__rdkeUSP=0.0
- mimo-v2.6-pro:yamcs-ds-mimo-r2-20261021-080139-n005/yamcs-ds__6SKJdUw=0.0
- mimo-v2.6-pro:yamcs-ds-mimo-r3-20261021-090125-n006/yamcs-ds__hrdXXZU=0.0
- deepseek-flash[1m]:ext-actions-atrisk-yamcs-ds-deepseek-a1/yamcs-subscription-authz-bypass__wyAjpoM=1.0
- mimo-v2.6-pro:ext-actions-atrisk-yamcs-ds-mimo-a1/yamcs-subscription-authz-bypass__QhB86xk=1.0

## Records

- VM build records: ~/cwe-bench/build/yamcs-ds/ (FAIRNESS.md, HUMAN-DECISION.md, AUDIT-NOTES.md, build notes, gate reports)
- VM task package: ~/cwe-bench/tasks/yamcs-ds/
- VM trial folders: ~/.tb-graders/cwe/jobs/<job>/<trial>/ (postmortem-*/verdict.json = audit)
- Locked run archive: ~/.tb-graders/cwe/archive/
