# cline-hub-dashboard-cross-site-access

Build ID `cline-s2`; delivered 2026-10-28 in client commit 3f7397d.

| Field | Value |
|---|---|
| slug | cline-s2 |
| delivered_as | cline-hub-dashboard-cross-site-access |
| client_commit | 3f7397d |
| delivered_date | 2026-10-28 |
| track | injection |
| round | scale-b3 |
| built_date | 2026-10-27 |
| repo | https://github.com/cline/cline |
| cwe_id | CWE-346 |
| advisory | GHSA-3CJ3-HQCR-G934 / CVE-2026-59723 |
| vulnerable_commit | 23c9bf1c05bfb116e843d18e1268304b00131e69 |
| fix_commit | d09270940f5746f288cfc4a5039b46a2f4d5d01e |
| deepseek | **failed 0/3** [0, 0.9, 0] |
| mimo | **failed 0/3** [0, 0, 0.9] |
| fairness | READY |
| decision | KEEP 2026-10-28 |

## Counted runs (job/trial = reward)

- deepseek-flash[1m]:cline-s2-deepseek-r1-20261028-033312-n001/cline-s2__2bg629C=0.0
- mimo-v2.6-pro:cline-s2-mimo-r1-20261028-033319-n001/cline-s2__rxpjrcY=0.0
- deepseek-flash[1m]:cline-s2-deepseek-r2-20261028-035507-n002/cline-s2__2d2g3pQ=0.9
- deepseek-flash[1m]:cline-s2-deepseek-r3-20261028-040655-n003/cline-s2__ML4swkP=0.0
- mimo-v2.6-pro:cline-s2-mimo-r2-20261028-042932-n002/cline-s2__paEe7JP=0.0
- mimo-v2.6-pro:cline-s2-mimo-r3-20261028-065321-n003/cline-s2__iZu3hwL=0.9

## Records

- VM build records: ~/cwe-bench/build/cline-s2/ (FAIRNESS.md, HUMAN-DECISION.md, AUDIT-NOTES.md, build notes, gate reports)
- VM task package: ~/cwe-bench/tasks/cline-s2/
- VM trial folders: ~/.tb-graders/cwe/jobs/<job>/<trial>/ (postmortem-*/verdict.json = audit)
- Locked run archive: ~/.tb-graders/cwe/archive/
