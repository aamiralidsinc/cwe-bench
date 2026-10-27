# vikunja-unconfirmed-account-auth

Build ID `stk-vikunja-ghsaxv7q`; delivered 2026-10-27 in client commit 16a1d56.

| Field | Value |
|---|---|
| slug | stk-vikunja-ghsaxv7q |
| delivered_as | vikunja-unconfirmed-account-auth |
| client_commit | 16a1d56 |
| delivered_date | 2026-10-27 |
| track | stacking |
| round | pre-scale round, built 2026-10-23 |
| built_date | 2026-10-23 |
| repo | https://github.com/go-vikunja/vikunja |
| cwe_id | CWE-287 |
| advisory | GHSA-8jvc-mcx6-r4cg + GHSA-xv7q-fvmc-jx96 |
| vulnerable_commit | 546db0dc219c736a34336dab9f3411ee7b821fde |
| fix_commit | b642b2a4536a, 7854f2729ab7 |
| deepseek | **failed 0/3** [0.8333, 0.8333, 0] |
| mimo | **failed 0/3** [0.8333, 0, 0.8333] |
| fairness | READY |
| decision | KEEP 2026-10-25 |

## Counted runs (job/trial = reward)

- deepseek-flash[1m]:stk-vikunja-ghsaxv7q-deepseek-r1-20261025-001737-n001/stk-vikunja-ghsaxv7q__cpcBNth=0.8333
- mimo-v2.6-pro:stk-vikunja-ghsaxv7q-mimo-r1-20261025-001853-n001/stk-vikunja-ghsaxv7q__uYwfy7U=0.8333
- deepseek-flash[1m]:stk-vikunja-ghsaxv7q-deepseek-r2-20261025-010320-n002/stk-vikunja-ghsaxv7q__UAHu5fa=0.8333
- deepseek-flash[1m]:stk-vikunja-ghsaxv7q-deepseek-r3-20261025-012108-n003/stk-vikunja-ghsaxv7q__MiooNq4=0.0
- mimo-v2.6-pro:stk-vikunja-ghsaxv7q-mimo-r2-20261025-012101-n002/stk-vikunja-ghsaxv7q__HBsiVvQ=0.0
- mimo-v2.6-pro:stk-vikunja-ghsaxv7q-mimo-r3-20261025-021933-n003/stk-vikunja-ghsaxv7q__FHAzcvU=0.8333

## Records

- VM build records: ~/cwe-bench/build/stk-vikunja-ghsaxv7q/ (FAIRNESS.md, HUMAN-DECISION.md, AUDIT-NOTES.md, build notes, gate reports)
- VM task package: ~/cwe-bench/tasks/stk-vikunja-ghsaxv7q/
- VM trial folders: ~/.tb-graders/cwe/jobs/<job>/<trial>/ (postmortem-*/verdict.json = audit)
- Locked run archive: ~/.tb-graders/cwe/archive/
