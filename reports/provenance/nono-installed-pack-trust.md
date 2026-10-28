# nono-installed-pack-trust

Build ID `nono-s2`; delivered 2026-10-28 in client commit 3f7397d.

| Field | Value |
|---|---|
| slug | nono-s2 |
| delivered_as | nono-installed-pack-trust |
| client_commit | 3f7397d |
| delivered_date | 2026-10-28 |
| track | injection |
| round | scale-b3 |
| built_date | 2026-10-27 |
| repo | https://github.com/nolabs-ai/nono |
| cwe_id | CWE-636 |
| advisory | GHSA-HC4M-Q9JH-XW4J |
| vulnerable_commit | 61a589f4b2e4022637ef3460e527ad774ed95635 |
| fix_commit | db07375031642f089d549b4f7b9abece87e39f87 |
| deepseek | **failed 0/3** [0.9412, 0.8824, 0.9412] |
| mimo | **failed 0/3** [0.9412, 0.9412, 0.9412] |
| fairness | READY |
| decision | KEEP 2026-10-28 |

## Counted runs (job/trial = reward)

- deepseek-flash[1m]:nono-s2-deepseek-r1-20261028-001754-n001/nono-s2__5kYNZZU=0.9412
- mimo-v2.6-pro:nono-s2-mimo-r1-20261028-001801-n001/nono-s2__bysDTHH=0.9412
- deepseek-flash[1m]:nono-s2-deepseek-r2-20261028-005155-n002/nono-s2__vZQaX8V=0.8824
- deepseek-flash[1m]:nono-s2-deepseek-r3-20261028-012431-n003/nono-s2__BQk3Tub=0.9412
- mimo-v2.6-pro:nono-s2-mimo-r2-20261028-013144-n002/nono-s2__mC9Vabt=0.9412
- mimo-v2.6-pro:nono-s2-mimo-r3-20261028-021922-n003/nono-s2__zXUPDUf=0.9412

## Records

- VM build records: ~/cwe-bench/build/nono-s2/ (FAIRNESS.md, HUMAN-DECISION.md, AUDIT-NOTES.md, build notes, gate reports)
- VM task package: ~/cwe-bench/tasks/nono-s2/
- VM trial folders: ~/.tb-graders/cwe/jobs/<job>/<trial>/ (postmortem-*/verdict.json = audit)
- Locked run archive: ~/.tb-graders/cwe/archive/
