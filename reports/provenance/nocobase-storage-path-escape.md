# nocobase-storage-path-escape

Build ID `nocobase-ds`; delivered 2026-10-28 in client commit 3f7397d.

| Field | Value |
|---|---|
| slug | nocobase-ds |
| delivered_as | nocobase-storage-path-escape |
| client_commit | 3f7397d |
| delivered_date | 2026-10-28 |
| track | injection |
| round | scale-b4 |
| built_date | 2026-10-24 |
| repo | https://github.com/nocobase/nocobase |
| cwe_id | CWE-73 |
| advisory | GHSA-GHVF-QF6H-G8X5 |
| vulnerable_commit | 7257be6c97b67335d4451c477b26d265a2c54a93 |
| fix_commit | 7c9ffe1427a529d62576b83c35222ba7ef9b8d11, a89e5a999b608bcb4ec67a845e924af0fb58a7c7 |
| deepseek | **failed 0/3** [0.4167, 0.4167, 0.5833] |
| mimo | **failed 0/3** [0.4167, 0.5, 0.5] (+1 provider stop) |
| fairness | READY |
| decision | KEEP 2026-10-28 |

## Counted runs (job/trial = reward)

- deepseek-flash[1m]:nocobase-ds-deepseek-r1-20261028-071355-n001/nocobase-ds__vGVFxuj=0.4167
- mimo-v2.6-pro:nocobase-ds-mimo-r1-20261028-071400-n001/nocobase-ds__ZwXzPBi=0.4167
- deepseek-flash[1m]:nocobase-ds-deepseek-r2-20261028-075613-n002/nocobase-ds__si5jDut=0.4167
- deepseek-flash[1m]:nocobase-ds-deepseek-r3-20261028-084702-n003/nocobase-ds__rp7dDTq=0.5833
- mimo-v2.6-pro:nocobase-ds-mimo-r2-20261028-093720-n003/nocobase-ds__kun9bxW=0.5
- mimo-v2.6-pro:nocobase-ds-mimo-r3-20261028-112938-n004/nocobase-ds__Lejioxp=0.5

## Records

- VM build records: ~/cwe-bench/build/nocobase-ds/ (FAIRNESS.md, HUMAN-DECISION.md, AUDIT-NOTES.md, build notes, gate reports)
- VM task package: ~/cwe-bench/tasks/nocobase-ds/
- VM trial folders: ~/.tb-graders/cwe/jobs/<job>/<trial>/ (postmortem-*/verdict.json = audit)
- Locked run archive: ~/.tb-graders/cwe/archive/
