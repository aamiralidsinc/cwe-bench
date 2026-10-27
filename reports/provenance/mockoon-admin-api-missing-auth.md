# mockoon-admin-api-missing-auth

Build ID `mockoon-ds`; delivered 2026-10-21 in client commit ea4ce53.

| Field | Value |
|---|---|
| slug | mockoon-ds |
| delivered_as | mockoon-admin-api-missing-auth |
| client_commit | ea4ce53 |
| delivered_date | 2026-10-21 |
| track | injection |
| round | pre-scale round, built 2026-10-18 |
| built_date | 2026-10-18 |
| repo | https://github.com/mockoon/mockoon |
| cwe_id | CWE-306 |
| advisory | GHSA-RQX4-3F6Q-3X2V / CVE-2026-59148 |
| vulnerable_commit | b42bdfb7f82e83f0e81bea8e6fe41adf5ec82585 |
| fix_commit | c420b5a56918475b8663977b51e5f986e45b3299 |
| deepseek | **failed 0/4** [0.9259, 0.9259, 0.963, 0.9259] |
| mimo | **failed 0/3** [0.9259, 0.9259, 0.963] |
| fairness | READY |
| decision |  |

## Counted runs (job/trial = reward)

- deepseek-flash[1m]:mockoon-ds-deepseek-r1-20261020-233116-n001/mockoon-ds__MiZJ2DC=0.9259
- deepseek-flash[1m]:mockoon-ds-deepseek-r1-20261020-233228-n001/mockoon-ds__jeHdXpm=0.9259
- deepseek-flash[1m]:mockoon-ds-deepseek-r2-20261020-234558-n002/mockoon-ds__YsF4UHu=0.963
- deepseek-flash[1m]:mockoon-ds-deepseek-r3-20261021-001116-n003/mockoon-ds__7MRPvL8=0.9259
- mimo-v2.6-pro:mockoon-ds-mimo-r1-20261021-003227-n004/mockoon-ds__557qJBr=0.9259
- mimo-v2.6-pro:mockoon-ds-mimo-r2-20261021-012054-n005/mockoon-ds__5GyS8nV=0.9259
- mimo-v2.6-pro:mockoon-ds-mimo-r3-20261021-022016-n006/mockoon-ds__u3DAP52=0.963

## Records

- VM build records: ~/cwe-bench/build/mockoon-ds/ (FAIRNESS.md, HUMAN-DECISION.md, AUDIT-NOTES.md, build notes, gate reports)
- VM task package: ~/cwe-bench/tasks/mockoon-ds/
- VM trial folders: ~/.tb-graders/cwe/jobs/<job>/<trial>/ (postmortem-*/verdict.json = audit)
- Locked run archive: ~/.tb-graders/cwe/archive/
