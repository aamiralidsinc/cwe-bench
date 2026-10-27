# tomcat-servlet-constraint-bypass

Build ID `stk-tomcat-ghsap26v`; delivered 2026-10-26 in client commit 9ca29b3.

| Field | Value |
|---|---|
| slug | stk-tomcat-ghsap26v |
| delivered_as | tomcat-servlet-constraint-bypass |
| client_commit | 9ca29b3 |
| delivered_date | 2026-10-26 |
| track | stacking |
| round | scale-b1 |
| built_date | 2026-10-26 |
| repo | https://github.com/apache/tomcat |
| cwe_id | CWE-863 |
| advisory | GHSA-mg4v-rf8p-ghqq / GHSA-p26v-97vp-jcx6 |
| vulnerable_commit | b39a8d8272b5f3fdf024e7cc6b6f4c2b1a97955a |
| fix_commit | f528992ec6cd / ee6274125702 / ece65c1a4280 / dd10265436ea / dbac5e247599 / b1d1047a4c0a / 9c90bdc1ad94 / 880b1a4fc424 / 63fd724e129b / 5c8560f30549 / 3e5b0455483e / 3ac2b5c1611a / 2d7dbfe4c63a / 1b2d5e90d271 / 149af600532d / 13fe121edb6f / 0ff4905158b7 / 0f95cb7401ac / 0a5a19f0c3b8 / 02780bbc6089 / b7b5c63a932f |
| deepseek | **failed 0/3** [0.9091, 0.9091, 0.4545] |
| mimo | **failed 0/3** [0.9091, 0.9091, 0] |
| fairness | READY |
| decision | KEEP 2026-10-26 |

## Counted runs (job/trial = reward)

- deepseek-flash[1m]:stk-tomcat-ghsap26v-deepseek-r1-20261026-133032-n001/stk-tomcat-ghsap26v__s3xZqMt=0.9091
- mimo-v2.6-pro:stk-tomcat-ghsap26v-mimo-r1-20261026-133037-n001/stk-tomcat-ghsap26v__5HJxZiv=0.9091
- deepseek-flash[1m]:stk-tomcat-ghsap26v-deepseek-r2-20261026-135748-n002/stk-tomcat-ghsap26v__PhXCbwu=0.9091
- mimo-v2.6-pro:stk-tomcat-ghsap26v-mimo-r2-20261026-143129-n002/stk-tomcat-ghsap26v__d2q7HEq=0.9091
- deepseek-flash[1m]:stk-tomcat-ghsap26v-deepseek-r3-20261026-143439-n003/stk-tomcat-ghsap26v__QBjxfDD=0.4545
- mimo-v2.6-pro:stk-tomcat-ghsap26v-mimo-r3-20261026-153636-n003/stk-tomcat-ghsap26v__RYf32sP=0.0

## Records

- VM build records: ~/cwe-bench/build/stk-tomcat-ghsap26v/ (FAIRNESS.md, HUMAN-DECISION.md, AUDIT-NOTES.md, build notes, gate reports)
- VM task package: ~/cwe-bench/tasks/stk-tomcat-ghsap26v/
- VM trial folders: ~/.tb-graders/cwe/jobs/<job>/<trial>/ (postmortem-*/verdict.json = audit)
- Locked run archive: ~/.tb-graders/cwe/archive/
