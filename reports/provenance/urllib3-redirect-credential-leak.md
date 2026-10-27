# urllib3-redirect-credential-leak

Build ID `stk-urllib3-ghsagwvm`; delivered 2026-10-26 in client commit 09aaadd.

| Field | Value |
|---|---|
| slug | stk-urllib3-ghsagwvm |
| delivered_as | urllib3-redirect-credential-leak |
| client_commit | 09aaadd |
| delivered_date | 2026-10-26 |
| track | stacking |
| round | scale-b2 |
| built_date | 2026-10-26 |
| repo | https://github.com/urllib3/urllib3 |
| cwe_id | CWE-200 |
| advisory | GHSA-www2-v7xj-xrc6; GHSA-gwvm-45gx-3cf8 |
| vulnerable_commit | c4f123dcdcad3582561373278d2772f819ec3cb8 |
| fix_commit | 560bd227b90f74417ffaedebf5f8d05a8ee4f532; adb358f8e06865406d1f05e581a16cbea2136fbc |
| deepseek | **failed 0/3** [0.8182, 0.8182, 0.8182] |
| mimo | **failed 0/3** [0.8182, 0.8182, 0] |
| fairness | READY |
| decision | KEEP 2026-10-27 |

## Counted runs (job/trial = reward)

- deepseek-flash[1m]:stk-urllib3-ghsagwvm-deepseek-r3-20261026-205610-n001/stk-urllib3-ghsagwvm__VdLZCsc=0.8182
- mimo-v2.6-pro:stk-urllib3-ghsagwvm-mimo-r1-20261026-205617-n001/stk-urllib3-ghsagwvm__duRKWSu=0.8182
- deepseek-flash[1m]:stk-urllib3-ghsagwvm-deepseek-r4-20261026-213816-n002/stk-urllib3-ghsagwvm__vkFdt99=0.8182
- deepseek-flash[1m]:stk-urllib3-ghsagwvm-deepseek-r5-20261026-220410-n003/stk-urllib3-ghsagwvm__Jxa7Qjv=0.8182
- mimo-v2.6-pro:stk-urllib3-ghsagwvm-mimo-r2-20261026-221457-n002/stk-urllib3-ghsagwvm__F9uY7N7=0.8182
- mimo-v2.6-pro:stk-urllib3-ghsagwvm-mimo-r3-20261026-233643-n003/stk-urllib3-ghsagwvm__3SSiTLt=0.0

## Records

- VM build records: ~/cwe-bench/build/stk-urllib3-ghsagwvm/ (FAIRNESS.md, HUMAN-DECISION.md, AUDIT-NOTES.md, build notes, gate reports)
- VM task package: ~/cwe-bench/tasks/stk-urllib3-ghsagwvm/
- VM trial folders: ~/.tb-graders/cwe/jobs/<job>/<trial>/ (postmortem-*/verdict.json = audit)
- Locked run archive: ~/.tb-graders/cwe/archive/
