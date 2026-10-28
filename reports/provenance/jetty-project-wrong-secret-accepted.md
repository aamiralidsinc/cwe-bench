# jetty-project-wrong-secret-accepted

Build ID `jetty.project-ds`; delivered 2026-10-28 in client commit 61b19b7.

| Field | Value |
|---|---|
| slug | jetty.project-ds |
| delivered_as | jetty-project-wrong-secret-accepted |
| client_commit | 61b19b7 |
| delivered_date | 2026-10-28 |
| track | injection |
| round | pre-scale round, built 2026-10-18 |
| built_date | 2026-10-18 |
| repo | https://github.com/jetty/jetty.project |
| cwe_id | CWE-173 |
| advisory | GHSA-2FVJ-HGJ9-J2GR |
| vulnerable_commit | 341a3175c4344a5122fcf5c302074309f8f284c6 |
| fix_commit | 4bcdbc7db387ce9e20e2c7571a7250280466221d |
| deepseek | **failed 0/3** [0.8889, 0.8889, 0.8889] |
| mimo | **failed 0/3** [0.8889, 0.8889, 0.8889] |
| fairness | READY |
| decision | KEEP 2026-10-27 |

## Counted runs (job/trial = reward)

- deepseek-flash[1m]:jetty.project-ds-deepseek-r1-20261022-053400-n001/jetty.project-ds__agQ5Cco=0.8889
- deepseek-flash[1m]:jetty.project-ds-deepseek-r2-20261022-055933-n002/jetty.project-ds__h4JaRuj=0.8889
- deepseek-flash[1m]:jetty.project-ds-deepseek-r3-20261022-062431-n003/jetty.project-ds__smL3U8g=0.8889
- mimo-v2.6-pro:jetty.project-ds-mimo-r1-20261022-065442-n004/jetty.project-ds__YdE98WC=0.8889
- mimo-v2.6-pro:jetty.project-ds-mimo-r2-20261022-090643-n005/jetty.project-ds__mXYSoPz=0.8889
- mimo-v2.6-pro:jetty.project-ds-mimo-r3-20261022-104102-n006/jetty.project-ds__RDzWBtt=0.8889

## Records

- VM build records: ~/cwe-bench/build/jetty.project-ds/ (FAIRNESS.md, HUMAN-DECISION.md, AUDIT-NOTES.md, build notes, gate reports)
- VM task package: ~/cwe-bench/tasks/jetty.project-ds/
- VM trial folders: ~/.tb-graders/cwe/jobs/<job>/<trial>/ (postmortem-*/verdict.json = audit)
- Locked run archive: ~/.tb-graders/cwe/archive/
