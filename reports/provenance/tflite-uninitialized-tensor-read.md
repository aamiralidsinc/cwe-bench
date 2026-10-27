# tflite-uninitialized-tensor-read

Build ID `stk-tensorflow-ghsajjr8`; delivered 2026-10-27 in client commit 16a1d56.

| Field | Value |
|---|---|
| slug | stk-tensorflow-ghsajjr8 |
| delivered_as | tflite-uninitialized-tensor-read |
| client_commit | 16a1d56 |
| delivered_date | 2026-10-27 |
| track | stacking |
| round | pre-scale round, built 2026-10-23 |
| built_date | 2026-10-23 |
| repo | https://github.com/tensorflow/tensorflow |
| cwe_id | CWE-476 |
| advisory | GHSA-qh32-6jjc-qprm / GHSA-jjr8-m8g8-p6wv |
| vulnerable_commit | 00a5ef689b0080ae2a73fe81da4673985078ec5c |
| fix_commit | 0b5662bc2be1 / f8378920345f |
| deepseek | **failed 0/3** [0, 0, 0] |
| mimo | **failed 0/5** [0, 0, 0.8, 0.8, 0.8] (+1 ungraded) (+1 timed out, re-run at 3 h) |
| fairness | READY |
| decision | KEEP 2026-10-25 |

## Counted runs (job/trial = reward)

- deepseek-flash[1m]:stk-tensorflow-ghsajjr8-deepseek-r1-20261023-130917-n001/stk-tensorflow-ghsajjr8__4mfsxw9=0.0
- deepseek-flash[1m]:stk-tensorflow-ghsajjr8-deepseek-r2-20261023-133753-n002/stk-tensorflow-ghsajjr8__ZJwrggc=0.0
- deepseek-flash[1m]:stk-tensorflow-ghsajjr8-deepseek-r3-20261023-135655-n003/stk-tensorflow-ghsajjr8__QveGCY3=0.0
- mimo-v2.6-pro:stk-tensorflow-ghsajjr8-mimo-r2-20261023-152441-n002/stk-tensorflow-ghsajjr8__rf4ZvyQ=0.0
- mimo-v2.6-pro:stk-tensorflow-ghsajjr8-mimo-r3-20261023-164434-n003/stk-tensorflow-ghsajjr8__Bbyg8Mi=0.0
- mimo-v2.6-pro:stk-tensorflow-ghsajjr8-mimo-r4-20261025-001127-n001/stk-tensorflow-ghsajjr8__qyEpY3K=0.8
- mimo-v2.6-pro:stk-tensorflow-ghsajjr8-mimo-r5-20261025-024257-n002/stk-tensorflow-ghsajjr8__mqMQZ6X=0.8
- mimo-v2.6-pro:stk-tensorflow-ghsajjr8-mimo-r6-20261025-044851-n003/stk-tensorflow-ghsajjr8__yLzwtgp=0.8

## Records

- VM build records: ~/cwe-bench/build/stk-tensorflow-ghsajjr8/ (FAIRNESS.md, HUMAN-DECISION.md, AUDIT-NOTES.md, build notes, gate reports)
- VM task package: ~/cwe-bench/tasks/stk-tensorflow-ghsajjr8/
- VM trial folders: ~/.tb-graders/cwe/jobs/<job>/<trial>/ (postmortem-*/verdict.json = audit)
- Locked run archive: ~/.tb-graders/cwe/archive/
