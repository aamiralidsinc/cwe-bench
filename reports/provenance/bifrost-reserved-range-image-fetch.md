# bifrost-reserved-range-image-fetch

Build ID `stk-bifrost-19592`; delivered 2026-10-28 in client commit 3f7397d.

| Field | Value |
|---|---|
| slug | stk-bifrost-19592 |
| delivered_as | bifrost-reserved-range-image-fetch |
| client_commit | 3f7397d |
| delivered_date | 2026-10-28 |
| track | stacking |
| round | scale-b2 |
| built_date | 2026-10-26 |
| repo | https://github.com/maximhq/bifrost |
| cwe_id | CWE-918 |
| advisory | 19592 |
| vulnerable_commit | 9dda29f586ff8c989c03264aedfbb6914b00fbad |
| fix_commit | 54ec431fc5255ff42c36420d88549477e0b33d89 |
| deepseek | **failed 0/3** [0.3913, 0, 0] |
| mimo | **failed 0/3** [0.5652, 0.7391, 0.8261] |
| fairness | READY |
| decision | KEEP 2026-10-28 |

## Counted runs (job/trial = reward)

- deepseek-flash[1m]:stk-bifrost-19592-deepseek-r1-20261027-150918-n001/stk-bifrost-19592__C5mGU7V=0.3913
- mimo-v2.6-pro:stk-bifrost-19592-mimo-r1-20261027-150944-n001/stk-bifrost-19592__DheeLZt=0.5652
- deepseek-flash[1m]:stk-bifrost-19592-deepseek-r2-20261027-154753-n002/stk-bifrost-19592__4ysF6qQ=0.0
- deepseek-flash[1m]:stk-bifrost-19592-deepseek-r3-20261027-161158-n003/stk-bifrost-19592__fvWPoMT=0.0
- mimo-v2.6-pro:stk-bifrost-19592-mimo-r2-20261027-203151-n001/stk-bifrost-19592__3FbxCK7=0.7391
- mimo-v2.6-pro:stk-bifrost-19592-mimo-r3-20261027-203158-n001/stk-bifrost-19592__6RxjZwe=0.8261

## Records

- VM build records: ~/cwe-bench/build/stk-bifrost-19592/ (FAIRNESS.md, HUMAN-DECISION.md, AUDIT-NOTES.md, build notes, gate reports)
- VM task package: ~/cwe-bench/tasks/stk-bifrost-19592/
- VM trial folders: ~/.tb-graders/cwe/jobs/<job>/<trial>/ (postmortem-*/verdict.json = audit)
- Locked run archive: ~/.tb-graders/cwe/archive/
