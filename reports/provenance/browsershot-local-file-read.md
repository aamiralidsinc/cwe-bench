# browsershot-local-file-read

Build ID `browsershot-s3`; delivered 2026-10-28 in client commit 3f7397d.

| Field | Value |
|---|---|
| slug | browsershot-s3 |
| delivered_as | browsershot-local-file-read |
| client_commit | 3f7397d |
| delivered_date | 2026-10-28 |
| track | injection |
| round | scale-b3 |
| built_date | 2026-10-27 |
| repo | https://github.com/spatie/browsershot |
| cwe_id | CWE-200 |
| advisory | GHSA-g2r4-phv7-5fgv / GHSA-c9f5-29f6-c35w |
| vulnerable_commit | bc075ca36411a5df6130e6b2f22b67fd35bd4e7f |
| fix_commit | fae8396641b961f62bd756920b14f01a4391296e / f791ce0ae8dd99367dbfa30588ee31e1196e1728 |
| deepseek | **failed 0/3** [0.8182, 0.8182, 0.8182] |
| mimo | **failed 0/3** [0.8182, 0.8182, 0.8182] |
| fairness | READY |
| decision | KEEP 2026-10-28 |

## Counted runs (job/trial = reward)

- deepseek-flash[1m]:browsershot-s3-deepseek-r1-20261028-005524-n001/browsershot-s3__aXSfmv8=0.8182
- mimo-v2.6-pro:browsershot-s3-mimo-r1-20261028-005532-n001/browsershot-s3__JXJy7kN=0.8182
- deepseek-flash[1m]:browsershot-s3-deepseek-r2-20261028-011457-n002/browsershot-s3__VQEp9sj=0.8182
- deepseek-flash[1m]:browsershot-s3-deepseek-r3-20261028-014210-n003/browsershot-s3__Mx6yYwC=0.8182
- mimo-v2.6-pro:browsershot-s3-mimo-r2-20261028-020928-n002/browsershot-s3__QHtYiAr=0.8182
- mimo-v2.6-pro:browsershot-s3-mimo-r3-20261028-054233-n001/browsershot-s3__EXcNNrV=0.8182

## Records

- VM build records: ~/cwe-bench/build/browsershot-s3/ (FAIRNESS.md, HUMAN-DECISION.md, AUDIT-NOTES.md, build notes, gate reports)
- VM task package: ~/cwe-bench/tasks/browsershot-s3/
- VM trial folders: ~/.tb-graders/cwe/jobs/<job>/<trial>/ (postmortem-*/verdict.json = audit)
- Locked run archive: ~/.tb-graders/cwe/archive/
