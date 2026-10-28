# bc-java-name-constraints-bypass

Build ID `bc-java-ds`; delivered 2026-10-28 in client commit 3f7397d.

| Field | Value |
|---|---|
| slug | bc-java-ds |
| delivered_as | bc-java-name-constraints-bypass |
| client_commit | 3f7397d |
| delivered_date | 2026-10-28 |
| track | injection |
| round | scale-b4 |
| built_date | 2026-10-24 |
| repo | https://github.com/bcgit/bc-java |
| cwe_id | CWE-295 |
| advisory | GHSA-9PWP-9QQC-PR26 |
| vulnerable_commit | 822b2478b131097368a56290f5728e28dd042989 |
| fix_commit | 2c28b253a44681fbbc562561eab6ad383d2ae558 |
| deepseek | **failed 0/3** [0.7273, 0.7273, 0.5909] |
| mimo | **failed 0/3** [0.5, 0.5909, 0.5909] |
| fairness | READY |
| decision | KEEP 2026-10-28 |

## Counted runs (job/trial = reward)

- deepseek-flash[1m]:bc-java-ds-deepseek-r1-20261028-112615-n001/bc-java-ds__MKAZ3NH=0.7273
- mimo-v2.6-pro:bc-java-ds-mimo-r1-20261028-112950-n001/bc-java-ds__AXYEQ5L=0.5
- deepseek-flash[1m]:bc-java-ds-deepseek-r2-20261028-115821-n002/bc-java-ds__KzDh9oU=0.7273
- mimo-v2.6-pro:bc-java-ds-mimo-r2-20261028-121323-n002/bc-java-ds__AW6DD56=0.5909
- deepseek-flash[1m]:bc-java-ds-deepseek-r3-20261028-122715-n003/bc-java-ds__N5jAmdo=0.5909
- mimo-v2.6-pro:bc-java-ds-mimo-r3-20261028-131354-n003/bc-java-ds__CZDB78N=0.5909

## Records

- VM build records: ~/cwe-bench/build/bc-java-ds/ (FAIRNESS.md, HUMAN-DECISION.md, AUDIT-NOTES.md, build notes, gate reports)
- VM task package: ~/cwe-bench/tasks/bc-java-ds/
- VM trial folders: ~/.tb-graders/cwe/jobs/<job>/<trial>/ (postmortem-*/verdict.json = audit)
- Locked run archive: ~/.tb-graders/cwe/archive/
