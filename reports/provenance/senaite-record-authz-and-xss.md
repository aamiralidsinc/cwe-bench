# senaite-record-authz-and-xss

Build ID `stk-senaite-core-4280`; delivered 2026-10-27 in client commit 16a1d56.

| Field | Value |
|---|---|
| slug | stk-senaite-core-4280 |
| delivered_as | senaite-record-authz-and-xss |
| client_commit | 16a1d56 |
| delivered_date | 2026-10-27 |
| track | stacking |
| round | pre-scale round, built 2026-10-23 |
| built_date | 2026-10-23 |
| repo | https://github.com/senaite/senaite.core |
| cwe_id | CWE-862 |
| advisory | GHSA-jrw6-7x4q-w25j |
| vulnerable_commit | 3195f890fe591c0e962294edc013f77826209c5c |
| fix_commit | a24d65e99a17ac43c5374ed9f0a60d0fe60d2f74,ef4b6d73575b0fbc0edc6114e5e025089aaf9eb7 |
| deepseek | **failed 0/3** [0.8182, 0.8182, 0.8182] |
| mimo | **failed 0/3** [0.8182, 0.8182, 0.8182] (+1 ungraded) (+1 audit: untrusted) |
| fairness | READY |
| decision | KEEP 2026-10-25 |

## Counted runs (job/trial = reward)

- deepseek-flash[1m]:stk-senaite-core-4280-deepseek-r1-20261024-213525-n001/stk-senaite-core-4280__QMj8AV3=0.8182
- deepseek-flash[1m]:stk-senaite-core-4280-deepseek-r2-20261024-214624-n002/stk-senaite-core-4280__Quny6gX=0.8182
- deepseek-flash[1m]:stk-senaite-core-4280-deepseek-r3-20261024-220003-n003/stk-senaite-core-4280__6jxaAau=0.8182
- mimo-v2.6-pro:stk-senaite-core-4280-mimo-r2-20261024-233025-n001/stk-senaite-core-4280__KPumnqB=0.8182
- mimo-v2.6-pro:stk-senaite-core-4280-mimo-r3-20261025-000551-n002/stk-senaite-core-4280__oZeuFaK=0.8182
- mimo-v2.6-pro:stk-senaite-core-4280-mimo-r4-20261025-003631-n003/stk-senaite-core-4280__yCKs2Ah=0.8182

## Records

- VM build records: ~/cwe-bench/build/stk-senaite-core-4280/ (FAIRNESS.md, HUMAN-DECISION.md, AUDIT-NOTES.md, build notes, gate reports)
- VM task package: ~/cwe-bench/tasks/stk-senaite-core-4280/
- VM trial folders: ~/.tb-graders/cwe/jobs/<job>/<trial>/ (postmortem-*/verdict.json = audit)
- Locked run archive: ~/.tb-graders/cwe/archive/
