# fastify-false-schema-validation-bypass

Build ID `fastify-s2`; delivered 2026-10-26 in client commit 9ca29b3.

| Field | Value |
|---|---|
| slug | fastify-s2 |
| delivered_as | fastify-false-schema-validation-bypass |
| client_commit | 9ca29b3 |
| delivered_date | 2026-10-26 |
| track | injection |
| round | scale-b1 |
| built_date | 2026-10-25 |
| repo | https://github.com/fastify/fastify |
| cwe_id | CWE-20 |
| advisory | GHSA-HWR6-493R-VM6H / CVE-2026-84469 |
| vulnerable_commit | 179619c8e99d54924309b9933402151ef9af37e0 |
| fix_commit | 7de6e81697778f9f41bd327a3b1c5c9a0d9637b4 |
| deepseek | **failed 0/3** [0.8462, 0.8462, 0.8462] |
| mimo | **failed 0/3** [0.8462, 0.8462, 0.8462] |
| fairness | READY |
| decision | KEEP 2026-10-26 |

## Counted runs (job/trial = reward)

- deepseek-flash[1m]:fastify-s2-deepseek-r1-20261026-060046-n001/fastify-s2__RasoNpA=0.8462
- mimo-v2.6-pro:fastify-s2-mimo-r1-20261026-060051-n001/fastify-s2__fuGgAQD=0.8462
- deepseek-flash[1m]:fastify-s2-deepseek-r2-20261026-064212-n002/fastify-s2__jpCZmEF=0.8462
- deepseek-flash[1m]:fastify-s2-deepseek-r3-20261026-071835-n003/fastify-s2__wi3ySw3=0.8462
- mimo-v2.6-pro:fastify-s2-mimo-r2-20261026-073554-n002/fastify-s2__HUd2Y6K=0.8462
- mimo-v2.6-pro:fastify-s2-mimo-r3-20261026-085412-n003/fastify-s2__w4JCWTx=0.8462

## Records

- VM build records: ~/cwe-bench/build/fastify-s2/ (FAIRNESS.md, HUMAN-DECISION.md, AUDIT-NOTES.md, build notes, gate reports)
- VM task package: ~/cwe-bench/tasks/fastify-s2/
- VM trial folders: ~/.tb-graders/cwe/jobs/<job>/<trial>/ (postmortem-*/verdict.json = audit)
- Locked run archive: ~/.tb-graders/cwe/archive/
