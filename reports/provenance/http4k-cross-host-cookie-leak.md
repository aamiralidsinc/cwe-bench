# http4k-cross-host-cookie-leak

Build ID `http4k-s2`; delivered 2026-10-28 in client commit 3f7397d.

| Field | Value |
|---|---|
| slug | http4k-s2 |
| delivered_as | http4k-cross-host-cookie-leak |
| client_commit | 3f7397d |
| delivered_date | 2026-10-28 |
| track | injection |
| round | scale-b3 |
| built_date | 2026-10-27 |
| repo | https://github.com/http4k/http4k |
| cwe_id | CWE-200 |
| advisory | GHSA-PR33-38XX-6R26 / CVE-2026-100725 |
| vulnerable_commit | 665b64e00c73491052d4d75e25720f6af739dada |
| fix_commit | 6a9b44d74342879ece808de00a66ec30e2b9da23 |
| deepseek | **failed 0/3** [0.8462, 0.9231, 0.8462] |
| mimo | **failed 0/3** [0.8462, 0.8462, 0.8462] |
| fairness | READY |
| decision | KEEP 2026-10-28 |

## Counted runs (job/trial = reward)

- deepseek-flash[1m]:http4k-s2-deepseek-r1-20261028-051651-n001/http4k-s2__ST87Cos=0.8462
- mimo-v2.6-pro:http4k-s2-mimo-r1-20261028-051654-n001/http4k-s2__5YL4cYR=0.8462
- deepseek-flash[1m]:http4k-s2-deepseek-r2-20261028-054555-n002/http4k-s2__jvVTD7M=0.9231
- deepseek-flash[1m]:http4k-s2-deepseek-r3-20261028-061638-n003/http4k-s2__vG2HjcX=0.8462
- mimo-v2.6-pro:http4k-s2-mimo-r2-20261028-071436-n002/http4k-s2__tRAsK6d=0.8462
- mimo-v2.6-pro:http4k-s2-mimo-r3-20261028-102113-n003/http4k-s2__YoeoYEy=0.8462

## Records

- VM build records: ~/cwe-bench/build/http4k-s2/ (FAIRNESS.md, HUMAN-DECISION.md, AUDIT-NOTES.md, build notes, gate reports)
- VM task package: ~/cwe-bench/tasks/http4k-s2/
- VM trial folders: ~/.tb-graders/cwe/jobs/<job>/<trial>/ (postmortem-*/verdict.json = audit)
- Locked run archive: ~/.tb-graders/cwe/archive/
