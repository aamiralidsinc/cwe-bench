# ansible-code-injection

Build ID `stk-ansible-ghsa66c7`; delivered 2026-10-28 in client commit 3f7397d.

| Field | Value |
|---|---|
| slug | stk-ansible-ghsa66c7 |
| delivered_as | ansible-code-injection |
| client_commit | 3f7397d |
| delivered_date | 2026-10-28 |
| track | stacking |
| round | scale-b1 |
| built_date | 2026-10-26 |
| repo | https://github.com/ansible/ansible |
| cwe_id | CWE-94 |
| advisory | GHSA-qg47-5px9-32g7 + GHSA-66c7-5pwv-mm3j |
| vulnerable_commit | 157b783521b52d9c3f357e811f6be0ec7600a89e |
| fix_commit | 998793fd0ab5, 5429b85b9f6c |
| deepseek | **failed 0/3** [0.8333, 0.8333, 0.8333] |
| mimo | **failed 0/4** [0.8333, 0.6667, 0.8333, 0.8333] |
| fairness | READY |
| decision | KEEP 2026-10-28 |

## Counted runs (job/trial = reward)

- deepseek-flash[1m]:stk-ansible-ghsa66c7-deepseek-r1-20261027-003155-n001/stk-ansible-ghsa66c7__bAkrBQM=0.8333
- mimo-v2.6-pro:stk-ansible-ghsa66c7-mimo-r1-20261027-003211-n001/stk-ansible-ghsa66c7__R3ikqEL=0.8333
- deepseek-flash[1m]:stk-ansible-ghsa66c7-deepseek-r2-20261027-010740-n002/stk-ansible-ghsa66c7__VEWVvdL=0.8333
- deepseek-flash[1m]:stk-ansible-ghsa66c7-deepseek-r3-20261027-013136-n003/stk-ansible-ghsa66c7__SA7gLCQ=0.8333
- mimo-v2.6-pro:stk-ansible-ghsa66c7-mimo-r2-20261027-031851-n002/stk-ansible-ghsa66c7__oGowRjy=0.6667
- mimo-v2.6-pro:stk-ansible-ghsa66c7-mimo-r3-20261027-051254-n003/stk-ansible-ghsa66c7__tA5JvYt=0.8333
- mimo-v2.6-pro:stk-ansible-ghsa66c7-mimo-r3-20261027-151040-n001/stk-ansible-ghsa66c7__7zCmVMe=0.8333

## Records

- VM build records: ~/cwe-bench/build/stk-ansible-ghsa66c7/ (FAIRNESS.md, HUMAN-DECISION.md, AUDIT-NOTES.md, build notes, gate reports)
- VM task package: ~/cwe-bench/tasks/stk-ansible-ghsa66c7/
- VM trial folders: ~/.tb-graders/cwe/jobs/<job>/<trial>/ (postmortem-*/verdict.json = audit)
- Locked run archive: ~/.tb-graders/cwe/archive/
