# lemur-acme-directory-ssrf

Build ID `stk-lemur-5644`; delivered 2026-10-27 in client commit 16a1d56.

| Field | Value |
|---|---|
| slug | stk-lemur-5644 |
| delivered_as | lemur-acme-directory-ssrf |
| client_commit | 16a1d56 |
| delivered_date | 2026-10-27 |
| track | stacking |
| round | pre-scale round, built 2026-10-23 |
| built_date | 2026-10-23 |
| repo | https://github.com/netflix/lemur |
| cwe_id | CWE-918 |
| advisory | GHSA-v5rc-cpwc-cfpr |
| vulnerable_commit | e9ade7dad5c9bc1369a831554ed6df3277c9cbae |
| fix_commit | edca0390f930344d65ff4ca37a669c2320e3dfad |
| deepseek | **failed 0/3** [0, 0, 0] |
| mimo | **failed 0/3** [0, 0, 0] |
| fairness | READY |
| decision | KEEP 2026-10-25 |

## Counted runs (job/trial = reward)

- deepseek-flash[1m]:stk-lemur-5644-deepseek-r1-20261024-231710-n001/stk-lemur-5644__ojuj8Hj=0.0
- mimo-v2.6-pro:stk-lemur-5644-mimo-r1-20261024-231730-n001/stk-lemur-5644__RKHokQy=0.0
- deepseek-flash[1m]:stk-lemur-5644-deepseek-r2-20261024-234101-n002/stk-lemur-5644__SDLjc5u=0.0
- deepseek-flash[1m]:stk-lemur-5644-deepseek-r3-20261025-000034-n003/stk-lemur-5644__zgVBaEq=0.0
- mimo-v2.6-pro:stk-lemur-5644-mimo-r2-20261025-001832-n002/stk-lemur-5644__bTkPioE=0.0
- mimo-v2.6-pro:stk-lemur-5644-mimo-r3-20261025-012245-n003/stk-lemur-5644__qKzAbqZ=0.0

## Records

- VM build records: ~/cwe-bench/build/stk-lemur-5644/ (FAIRNESS.md, HUMAN-DECISION.md, AUDIT-NOTES.md, build notes, gate reports)
- VM task package: ~/cwe-bench/tasks/stk-lemur-5644/
- VM trial folders: ~/.tb-graders/cwe/jobs/<job>/<trial>/ (postmortem-*/verdict.json = audit)
- Locked run archive: ~/.tb-graders/cwe/archive/
