# spring-framework-binding-exclusion-bypass

Build ID `stk-spring-framework-ghsa4gc7`; delivered 2026-10-26 in client commit c83e5c1.

| Field | Value |
|---|---|
| slug | stk-spring-framework-ghsa4gc7 |
| delivered_as | spring-framework-binding-exclusion-bypass |
| client_commit | c83e5c1 |
| delivered_date | 2026-10-26 |
| track | stacking |
| round | scale-b2 |
| built_date | 2026-10-26 |
| repo | https://github.com/spring-projects/spring-framework |
| cwe_id | CWE-178 |
| advisory | GHSA-g5mm-vmx4-3rg7 + GHSA-4gc7-5j7h-4qph |
| vulnerable_commit | 0cf7f7bd890504061883c48e382dc23e0c5d4df0 |
| fix_commit | a7cf19cec5ebd270f97a194d749e2d5701ad2ab7 (CVE-2022-22968, 5.3 line) + 23656aebc6c7d0f9faff1080981eb4d55eff296c (CVE-2024-38820) |
| deepseek | **failed 0/3** [0.75, 0.75, 0.75] |
| mimo | **failed 0/3** [0, 0, 0] |
| fairness | READY |
| decision | KEEP 2026-10-27 |

## Counted runs (job/trial = reward)

- deepseek-flash[1m]:stk-spring-framework-ghsa4gc7-deepseek-r1-20261026-200529-n001/stk-spring-framework-ghsa4gc7__DQKLHTL=0.75
- mimo-v2.6-pro:stk-spring-framework-ghsa4gc7-mimo-r1-20261026-200537-n001/stk-spring-framework-ghsa4gc7__EdAA473=0.0
- deepseek-flash[1m]:stk-spring-framework-ghsa4gc7-deepseek-r2-20261026-203208-n002/stk-spring-framework-ghsa4gc7__9k6P3L7=0.75
- deepseek-flash[1m]:stk-spring-framework-ghsa4gc7-deepseek-r3-20261026-205859-n003/stk-spring-framework-ghsa4gc7__tqwVv4L=0.75
- mimo-v2.6-pro:stk-spring-framework-ghsa4gc7-mimo-r2-20261026-211931-n002/stk-spring-framework-ghsa4gc7__aWP2Bcg=0.0
- mimo-v2.6-pro:stk-spring-framework-ghsa4gc7-mimo-r3-20261026-221722-n003/stk-spring-framework-ghsa4gc7__nSaS4Ty=0.0

## Records

- VM build records: ~/cwe-bench/build/stk-spring-framework-ghsa4gc7/ (FAIRNESS.md, HUMAN-DECISION.md, AUDIT-NOTES.md, build notes, gate reports)
- VM task package: ~/cwe-bench/tasks/stk-spring-framework-ghsa4gc7/
- VM trial folders: ~/.tb-graders/cwe/jobs/<job>/<trial>/ (postmortem-*/verdict.json = audit)
- Locked run archive: ~/.tb-graders/cwe/archive/
