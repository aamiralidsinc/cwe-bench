# gitpython-option-injection

Build ID `stk-gitpython-ghsawvpp`; delivered 2026-10-27 in client commit 16a1d56.

| Field | Value |
|---|---|
| slug | stk-gitpython-ghsawvpp |
| delivered_as | gitpython-option-injection |
| client_commit | 16a1d56 |
| delivered_date | 2026-10-27 |
| track | stacking |
| round | pre-scale round, built 2026-10-23 |
| built_date | 2026-10-23 |
| repo | https://github.com/gitpython-developers/GitPython |
| cwe_id | CWE-88 |
| advisory | GHSA-r9mr-m37c-5fr3; GHSA-wvpp-8hx9-p66j |
| vulnerable_commit | faf3c09038b03bc2bdd8545ef34bbf6d7f1cd11f |
| fix_commit | e8d0fbf774d1, 96a888f4d782 |
| deepseek | **failed 0/3** [0.875, 0.875, 0.875] |
| mimo | **failed 0/3** [0.375, 0.625, 0.375] |
| fairness | READY |
| decision | KEEP 2026-10-25 |

## Counted runs (job/trial = reward)

- deepseek-flash[1m]:stk-gitpython-ghsawvpp-deepseek-r1-20261024-201811-n001/stk-gitpython-ghsawvpp__MbQUFwq=0.875
- mimo-v2.6-pro:stk-gitpython-ghsawvpp-mimo-r1-20261024-201829-n001/stk-gitpython-ghsawvpp__t7FwJLz=0.375
- deepseek-flash[1m]:stk-gitpython-ghsawvpp-deepseek-r2-20261024-204907-n002/stk-gitpython-ghsawvpp__L2bPJkW=0.875
- deepseek-flash[1m]:stk-gitpython-ghsawvpp-deepseek-r3-20261024-211440-n003/stk-gitpython-ghsawvpp__45AJbAx=0.875
- mimo-v2.6-pro:stk-gitpython-ghsawvpp-mimo-r2-20261024-212805-n002/stk-gitpython-ghsawvpp__9uCYzSR=0.625
- mimo-v2.6-pro:stk-gitpython-ghsawvpp-mimo-r3-20261024-224627-n003/stk-gitpython-ghsawvpp__9XKXPoa=0.375

## Records

- VM build records: ~/cwe-bench/build/stk-gitpython-ghsawvpp/ (FAIRNESS.md, HUMAN-DECISION.md, AUDIT-NOTES.md, build notes, gate reports)
- VM task package: ~/cwe-bench/tasks/stk-gitpython-ghsawvpp/
- VM trial folders: ~/.tb-graders/cwe/jobs/<job>/<trial>/ (postmortem-*/verdict.json = audit)
- Locked run archive: ~/.tb-graders/cwe/archive/
