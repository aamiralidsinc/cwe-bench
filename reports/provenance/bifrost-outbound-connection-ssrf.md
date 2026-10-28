# bifrost-outbound-connection-ssrf

Build ID `bifrost-s2`; delivered 2026-10-28 in client commit 3f7397d.

| Field | Value |
|---|---|
| slug | bifrost-s2 |
| delivered_as | bifrost-outbound-connection-ssrf |
| client_commit | 3f7397d |
| delivered_date | 2026-10-28 |
| track | injection |
| round | scale-b2 |
| built_date | 2026-10-26 |
| repo | https://github.com/maximhq/bifrost |
| cwe_id | CWE-918 |
| advisory | GHSA-W98G-5W9P-P3RC, CVE-2026-55245, GO-2026-6320 |
| vulnerable_commit | 9dda29f586ff8c989c03264aedfbb6914b00fbad |
| fix_commit | 54ec431fc5255ff42c36420d88549477e0b33d89 |
| deepseek | **failed 0/3** [0.4839, 0.4194, 0.4194] (+1 ungraded) |
| mimo | **failed 0/3** [0.4194, 0.6774, 0.6774] |
| fairness | READY |
| decision | KEEP 2026-10-28 |

## Counted runs (job/trial = reward)

- deepseek-flash[1m]:bifrost-s2-deepseek-r1-20261026-222648-n001/bifrost-s2__fNGdYB5=0.4839
- mimo-v2.6-pro:bifrost-s2-mimo-r1-20261026-222707-n001/bifrost-s2__x83LEiF=0.4194
- deepseek-flash[1m]:bifrost-s2-deepseek-r2-20261027-000453-n003/bifrost-s2__P6XetQu=0.4194
- mimo-v2.6-pro:bifrost-s2-mimo-r2-20261027-004954-n002/bifrost-s2__wmw2yRm=0.6774
- deepseek-flash[1m]:bifrost-s2-deepseek-r3-20261027-013102-n004/bifrost-s2__VCnGNnR=0.4194
- mimo-v2.6-pro:bifrost-s2-mimo-r3-20261027-031629-n003/bifrost-s2__NcSCpkV=0.6774

## Records

- VM build records: ~/cwe-bench/build/bifrost-s2/ (FAIRNESS.md, HUMAN-DECISION.md, AUDIT-NOTES.md, build notes, gate reports)
- VM task package: ~/cwe-bench/tasks/bifrost-s2/
- VM trial folders: ~/.tb-graders/cwe/jobs/<job>/<trial>/ (postmortem-*/verdict.json = audit)
- Locked run archive: ~/.tb-graders/cwe/archive/
