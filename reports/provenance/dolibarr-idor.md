# dolibarr-idor

Build ID `dolibarr-ds`; delivered 2026-10-28 in client commit 3f7397d.

| Field | Value |
|---|---|
| slug | dolibarr-ds |
| delivered_as | dolibarr-idor |
| client_commit | 3f7397d |
| delivered_date | 2026-10-28 |
| track | injection |
| round | scale-b4 |
| built_date | 2026-10-24 |
| repo | https://github.com/dolibarr/dolibarr |
| cwe_id | CWE-639 |
| advisory | GHSA-7FG5-VC77-69FP / CVE-2026-10215 |
| vulnerable_commit | 3566f80aa88fd26b295ad8762d02327915ee79ec |
| fix_commit | ee93b6f2f9dd0f6aeefe9d718ab3ab0a44326b73 |
| deepseek | **failed 0/3** [0.9688, 0.9688, 0.9688] |
| mimo | **failed 0/3** [0.9688, 0.9688, 0.9688] |
| fairness | READY |
| decision | KEEP 2026-10-28 |

## Counted runs (job/trial = reward)

- deepseek-flash[1m]:dolibarr-ds-deepseek-r1-20261028-075017-n001/dolibarr-ds__R9zeNUG=0.9688
- mimo-v2.6-pro:dolibarr-ds-mimo-r1-20261028-075025-n001/dolibarr-ds__cXPsJiM=0.9688
- deepseek-flash[1m]:dolibarr-ds-deepseek-r2-20261028-080847-n002/dolibarr-ds__rbqaAhY=0.9688
- deepseek-flash[1m]:dolibarr-ds-deepseek-r3-20261028-083355-n003/dolibarr-ds__rd4WNvj=0.9688
- mimo-v2.6-pro:dolibarr-ds-mimo-r2-20261028-091810-n002/dolibarr-ds__2EWqmpV=0.9688
- mimo-v2.6-pro:dolibarr-ds-mimo-r3-20261028-102624-n003/dolibarr-ds__9iuWXnH=0.9688

## Records

- VM build records: ~/cwe-bench/build/dolibarr-ds/ (FAIRNESS.md, HUMAN-DECISION.md, AUDIT-NOTES.md, build notes, gate reports)
- VM task package: ~/cwe-bench/tasks/dolibarr-ds/
- VM trial folders: ~/.tb-graders/cwe/jobs/<job>/<trial>/ (postmortem-*/verdict.json = audit)
- Locked run archive: ~/.tb-graders/cwe/archive/
