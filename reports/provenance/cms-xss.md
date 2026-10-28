# cms-xss

Build ID `stk-cms-ghsafvwq`; delivered 2026-10-28 in client commit 61b19b7.

| Field | Value |
|---|---|
| slug | stk-cms-ghsafvwq |
| delivered_as | cms-xss |
| client_commit | 61b19b7 |
| delivered_date | 2026-10-28 |
| track | stacking |
| round | scale-b1 |
| built_date | 2026-10-26 |
| repo | https://github.com/craftcms/cms |
| cwe_id | CWE-79 |
| advisory | GHSA-7vrx-9684-xrf2 (CVE-2025-35939) + GHSA-fvwq-45qv-xvhv (CVE-2026-31859) |
| vulnerable_commit | 518766744dd592ccf24bf49560ab60fcc39dcaa0 |
| fix_commit | e4c7bac8f31010aee048409f9ef6f744a83146b2 + cc9921c14897ee2b592a431c2356af8a04ce4cfe |
| deepseek | **failed 0/3** [0.8462, 0.8462, 0.6154] |
| mimo | **failed 0/4** [0.4615, 0, 0.6154, 0.6154] (+1 ungraded) (+1 provider stop) |
| fairness | READY |
| decision | KEEP 2026-10-27 |

## Counted runs (job/trial = reward)

- deepseek-flash[1m]:stk-cms-ghsafvwq-deepseek-r1-20261026-225252-n001/stk-cms-ghsafvwq__89A2d6B=0.8462
- mimo-v2.6-pro:stk-cms-ghsafvwq-mimo-r1-20261026-225327-n001/stk-cms-ghsafvwq__sCFT5QW=0.4615
- deepseek-flash[1m]:stk-cms-ghsafvwq-deepseek-r2-20261026-231938-n002/stk-cms-ghsafvwq__CtVHQqi=0.8462
- deepseek-flash[1m]:stk-cms-ghsafvwq-deepseek-r3-20261027-004325-n003/stk-cms-ghsafvwq__XM7mKPM=0.6154
- mimo-v2.6-pro:stk-cms-ghsafvwq-mimo-r6-20261027-043538-n001/stk-cms-ghsafvwq__5SYaB7s=0.0
- mimo-v2.6-pro:stk-cms-ghsafvwq-mimo-r7-20261027-043601-n001/stk-cms-ghsafvwq__gPLJWEN=0.6154
- mimo-v2.6-pro:stk-cms-ghsafvwq-mimo-r6-20261027-151618-n001/stk-cms-ghsafvwq__6sh9GA8=0.6154

## Records

- VM build records: ~/cwe-bench/build/stk-cms-ghsafvwq/ (FAIRNESS.md, HUMAN-DECISION.md, AUDIT-NOTES.md, build notes, gate reports)
- VM task package: ~/cwe-bench/tasks/stk-cms-ghsafvwq/
- VM trial folders: ~/.tb-graders/cwe/jobs/<job>/<trial>/ (postmortem-*/verdict.json = audit)
- Locked run archive: ~/.tb-graders/cwe/archive/
