# grav-information-exposure

Build ID `grav-ds`; delivered 2026-10-27 in client commit a74e1ac.

| Field | Value |
|---|---|
| slug | grav-ds |
| delivered_as | grav-information-exposure |
| client_commit | a74e1ac |
| delivered_date | 2026-10-27 |
| track | injection |
| round | pre-scale round, built 2026-10-18 |
| built_date | 2026-10-18 |
| repo | https://github.com/getgrav/grav |
| cwe_id | CWE-200 |
| advisory | GHSA-MC5Q-6HPJ-RP7J / CVE-2026-61450 / CVE-2026-61842 |
| vulnerable_commit | 734f7f4c266693a486198047c10f79d3e175e90c |
| fix_commit | 7efe70574e4cf01a251318478c13673029e93eb6 |
| deepseek | **failed 0/3** [0, 0.8696, 0] |
| mimo | **failed 0/3** [0.6087, 0, 0.6957] |
| fairness | READY |
| decision | KEEP 2026-10-27 |

## Counted runs (job/trial = reward)

- deepseek-flash[1m]:grav-ds-deepseek-r1-20261022-051235-n001/grav-ds__Z5na8dz=0.0
- deepseek-flash[1m]:grav-ds-deepseek-r2-20261022-053048-n002/grav-ds__Qsc8LCF=0.8696
- deepseek-flash[1m]:grav-ds-deepseek-r3-20261022-055352-n003/grav-ds__kJ94WFZ=0.0
- mimo-v2.6-pro:grav-ds-mimo-r1-20261022-061850-n004/grav-ds__cuJg56e=0.6087
- mimo-v2.6-pro:grav-ds-mimo-r2-20261022-081225-n005/grav-ds__8DKmUpU=0.0
- mimo-v2.6-pro:grav-ds-mimo-r3-20261022-092621-n006/grav-ds__cuvQjpE=0.6957

## Records

- VM build records: ~/cwe-bench/build/grav-ds/ (FAIRNESS.md, HUMAN-DECISION.md, AUDIT-NOTES.md, build notes, gate reports)
- VM task package: ~/cwe-bench/tasks/grav-ds/
- VM trial folders: ~/.tb-graders/cwe/jobs/<job>/<trial>/ (postmortem-*/verdict.json = audit)
- Locked run archive: ~/.tb-graders/cwe/archive/
