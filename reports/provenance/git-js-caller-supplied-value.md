# git-js-caller-supplied-value

Build ID `stk-git-js-14793`; delivered 2026-10-27 in client commit a74e1ac.

| Field | Value |
|---|---|
| slug | stk-git-js-14793 |
| delivered_as | git-js-caller-supplied-value |
| client_commit | a74e1ac |
| delivered_date | 2026-10-27 |
| track | stacking |
| round | scale-b1 |
| built_date | 2026-10-26 |
| repo | https://github.com/steveukx/git-js |
| cwe_id | CWE-184 |
| advisory | GHSA-X6JW-M9V5-85VH / CVE-2026-102828 |
| vulnerable_commit | 76f308ed445013d8dd973bc515e7815b59426e3e |
| fix_commit | d762810c13b331ff1e5eb24c0b434646d2a8d1b3 |
| deepseek | **failed 0/3** [0.4783, 0.6087, 0.4783] |
| mimo | **failed 0/3** [0.3043, 0.6087, 0] (+1 ungraded) |
| fairness | READY |
| decision | KEEP 2026-10-27 |

## Counted runs (job/trial = reward)

- deepseek-flash[1m]:stk-git-js-14793-deepseek-r1-20261027-002744-n001/stk-git-js-14793__d7xDyGB=0.4783
- mimo-v2.6-pro:stk-git-js-14793-mimo-r1-20261027-002808-n001/stk-git-js-14793__eJjPf4C=0.3043
- deepseek-flash[1m]:stk-git-js-14793-deepseek-r2-20261027-010517-n002/stk-git-js-14793__4t663bm=0.6087
- deepseek-flash[1m]:stk-git-js-14793-deepseek-r3-20261027-014214-n003/stk-git-js-14793__qRuz8ds=0.4783
- mimo-v2.6-pro:stk-git-js-14793-mimo-r2-20261027-150915-n001/stk-git-js-14793__ESaCU5y=0.6087
- mimo-v2.6-pro:stk-git-js-14793-mimo-r3-20261027-150955-n001/stk-git-js-14793__tvnbWnA=0.0

## Records

- VM build records: ~/cwe-bench/build/stk-git-js-14793/ (FAIRNESS.md, HUMAN-DECISION.md, AUDIT-NOTES.md, build notes, gate reports)
- VM task package: ~/cwe-bench/tasks/stk-git-js-14793/
- VM trial folders: ~/.tb-graders/cwe/jobs/<job>/<trial>/ (postmortem-*/verdict.json = audit)
- Locked run archive: ~/.tb-graders/cwe/archive/
