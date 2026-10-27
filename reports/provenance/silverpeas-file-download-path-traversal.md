# silverpeas-file-download-path-traversal

Build ID `stk-silverpeas-core-27788`; delivered 2026-10-26 in client commit 9ca29b3.

| Field | Value |
|---|---|
| slug | stk-silverpeas-core-27788 |
| delivered_as | silverpeas-file-download-path-traversal |
| client_commit | 9ca29b3 |
| delivered_date | 2026-10-26 |
| track | stacking |
| round | scale-b1 |
| built_date | 2026-10-26 |
| repo | https://github.com/silverpeas/silverpeas-core |
| cwe_id | CWE-36 |
| advisory | GHSA-QV8H-RQR3-MPH9 / CVE-2026-53698 |
| vulnerable_commit | b1d65df25a0b8f0e3fde7fa5b57452eadffc644c |
| fix_commit | caa6e6d1ac967ebd29b39e11c2ef5e7fd0047eec |
| deepseek | **failed 0/3** [0, 0.2857, 0.2857] |
| mimo | **failed 0/3** [0.4286, 0.5714, 0.5714] |
| fairness | NOT_READY |
| decision | KEEP 2026-10-26 |

## Counted runs (job/trial = reward)

- deepseek-flash[1m]:stk-silverpeas-core-27788-deepseek-r1-20261026-121305-n001/stk-silverpeas-core-27788__E35KsaW=0.0
- mimo-v2.6-pro:stk-silverpeas-core-27788-mimo-r1-20261026-121313-n001/stk-silverpeas-core-27788__tpJsWbK=0.4286
- deepseek-flash[1m]:stk-silverpeas-core-27788-deepseek-r2-20261026-132123-n002/stk-silverpeas-core-27788__UB7nYqi=0.2857
- deepseek-flash[1m]:stk-silverpeas-core-27788-deepseek-r3-20261026-134902-n003/stk-silverpeas-core-27788__KDt4VgM=0.2857
- mimo-v2.6-pro:stk-silverpeas-core-27788-mimo-r2-20261026-134956-n002/stk-silverpeas-core-27788__6Vs8xgE=0.5714
- mimo-v2.6-pro:stk-silverpeas-core-27788-mimo-r3-20261026-143003-n003/stk-silverpeas-core-27788__JAG5Czi=0.5714

## Records

- VM build records: ~/cwe-bench/build/stk-silverpeas-core-27788/ (FAIRNESS.md, HUMAN-DECISION.md, AUDIT-NOTES.md, build notes, gate reports)
- VM task package: ~/cwe-bench/tasks/stk-silverpeas-core-27788/
- VM trial folders: ~/.tb-graders/cwe/jobs/<job>/<trial>/ (postmortem-*/verdict.json = audit)
- Locked run archive: ~/.tb-graders/cwe/archive/
