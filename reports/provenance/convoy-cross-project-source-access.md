# convoy-cross-project-source-access

Build ID `stk-convoy-18562`; delivered 2026-10-26 in client commit 9ca29b3.

| Field | Value |
|---|---|
| slug | stk-convoy-18562 |
| delivered_as | convoy-cross-project-source-access |
| client_commit | 9ca29b3 |
| delivered_date | 2026-10-26 |
| track | stacking |
| round | scale-b1 |
| built_date | 2026-10-26 |
| repo | https://github.com/frain-dev/convoy |
| cwe_id | CWE-639 |
| advisory | GHSA-p5vg-v7mj-f6q4 |
| vulnerable_commit | 8c38a84fb8e649a5ca500349ef6bc4e8b3bf6be6 |
| fix_commit | 1cc67cd16fb1f8890cc83a3998d3f92dceb7fd06 |
| deepseek | **failed 0/3** [0.5556, 0.8889, 0.8889] |
| mimo | **failed 0/3** [0.7778, 0.7778, 0.7778] (+1 provider stop) |
| fairness | READY |
| decision | KEEP 2026-10-26 |

## Counted runs (job/trial = reward)

- deepseek-flash[1m]:stk-convoy-18562-deepseek-r1-20261026-152044-n001/stk-convoy-18562__dHaec9B=0.5556
- mimo-v2.6-pro:stk-convoy-18562-mimo-r1-20261026-152117-n001/stk-convoy-18562__znQrXXW=0.7778
- deepseek-flash[1m]:stk-convoy-18562-deepseek-r2-20261026-154029-n002/stk-convoy-18562__haLLvZe=0.8889
- deepseek-flash[1m]:stk-convoy-18562-deepseek-r3-20261026-155404-n003/stk-convoy-18562__aLRPYJQ=0.8889
- mimo-v2.6-pro:stk-convoy-18562-mimo-r2-20261026-160010-n002/stk-convoy-18562__oLZnCbd=0.7778
- mimo-v2.6-pro:stk-convoy-18562-mimo-r3-20261026-164835-n004/stk-convoy-18562__WrpyQNb=0.7778

## Records

- VM build records: ~/cwe-bench/build/stk-convoy-18562/ (FAIRNESS.md, HUMAN-DECISION.md, AUDIT-NOTES.md, build notes, gate reports)
- VM task package: ~/cwe-bench/tasks/stk-convoy-18562/
- VM trial folders: ~/.tb-graders/cwe/jobs/<job>/<trial>/ (postmortem-*/verdict.json = audit)
- Locked run archive: ~/.tb-graders/cwe/archive/
