# ip-address-private-range-ssrf

Build ID `stk-ip-address-ghsa2vr4`; delivered 2026-10-26 in client commit a979ef5.

| Field | Value |
|---|---|
| slug | stk-ip-address-ghsa2vr4 |
| delivered_as | ip-address-private-range-ssrf |
| client_commit | a979ef5 |
| delivered_date | 2026-10-26 |
| track | stacking |
| round | scale-b1 |
| built_date | 2026-10-26 |
| repo | https://github.com/beaugunderson/ip-address |
| cwe_id | CWE-918 |
| advisory | GHSA-22jq-vg5j-6vgg; GHSA-2vr4-cq9g-pvrc |
| vulnerable_commit | e82a6812ac9d16f1300d3c2051fe2cc88c5d9161 |
| fix_commit | 4a1f613f4c1bec915677dea923c10aaa09361ef9, ab3dc88bcf5374344168a2ba075ca7ac4ff257f8 |
| deepseek | **failed 0/3** [0.32, 0.4, 0.56] |
| mimo | **failed 0/3** [0.24, 0.56, 0.24] |
| fairness | READY |
| decision | KEEP 2026-10-26 |

## Counted runs (job/trial = reward)

- deepseek-flash[1m]:stk-ip-address-ghsa2vr4-deepseek-r1-20261026-182928-n001/stk-ip-address-ghsa2vr4__nbkUCfT=0.32
- mimo-v2.6-pro:stk-ip-address-ghsa2vr4-mimo-r1-20261026-182945-n001/stk-ip-address-ghsa2vr4__UPttA44=0.24
- deepseek-flash[1m]:stk-ip-address-ghsa2vr4-deepseek-r2-20261026-184656-n002/stk-ip-address-ghsa2vr4__SU8npM7=0.4
- deepseek-flash[1m]:stk-ip-address-ghsa2vr4-deepseek-r3-20261026-185854-n003/stk-ip-address-ghsa2vr4__gbMTDH8=0.56
- mimo-v2.6-pro:stk-ip-address-ghsa2vr4-mimo-r2-20261026-191039-n002/stk-ip-address-ghsa2vr4__xfXtieU=0.56
- mimo-v2.6-pro:stk-ip-address-ghsa2vr4-mimo-r3-20261026-200613-n003/stk-ip-address-ghsa2vr4__CLFVhjG=0.24

## Records

- VM build records: ~/cwe-bench/build/stk-ip-address-ghsa2vr4/ (FAIRNESS.md, HUMAN-DECISION.md, AUDIT-NOTES.md, build notes, gate reports)
- VM task package: ~/cwe-bench/tasks/stk-ip-address-ghsa2vr4/
- VM trial folders: ~/.tb-graders/cwe/jobs/<job>/<trial>/ (postmortem-*/verdict.json = audit)
- Locked run archive: ~/.tb-graders/cwe/archive/
