# katex-trust-setting-pollution

Build ID `katex-s2`; delivered 2026-10-28 in client commit 3f7397d.

| Field | Value |
|---|---|
| slug | katex-s2 |
| delivered_as | katex-trust-setting-pollution |
| client_commit | 3f7397d |
| delivered_date | 2026-10-28 |
| track | injection |
| round | scale-b3 |
| built_date | 2026-10-27 |
| repo | https://github.com/KaTeX/KaTeX |
| cwe_id | CWE-807 |
| advisory | GHSA-238P-PMPM-9MQ7 / CVE-2026-103923 |
| vulnerable_commit | 5a5bf2060431aaed5eb3b549f6fab24f55e9e70a |
| fix_commit | 0adf7e77db6915d991803b29699f82b1ccf8d4f4 |
| deepseek | **failed 0/3** [0.9091, 0.9091, 0.9091] |
| mimo | **failed 0/3** [0.9091, 0.7727, 0.8636] |
| fairness | READY |
| decision | KEEP 2026-10-28 |

## Counted runs (job/trial = reward)

- deepseek-flash[1m]:katex-s2-deepseek-r1-20261027-202931-n001/katex-s2__tLhapPF=0.9091
- mimo-v2.6-pro:katex-s2-mimo-r1-20261027-202936-n001/katex-s2__BtqWXdX=0.9091
- deepseek-flash[1m]:katex-s2-deepseek-r2-20261027-205940-n002/katex-s2__WGKsxgh=0.9091
- deepseek-flash[1m]:katex-s2-deepseek-r3-20261027-212554-n003/katex-s2__gA47JsT=0.9091
- mimo-v2.6-pro:katex-s2-mimo-r2-20261027-214008-n002/katex-s2__XnoZ9n7=0.7727
- mimo-v2.6-pro:katex-s2-mimo-r3-20261027-231500-n003/katex-s2__oCvTARX=0.8636

## Records

- VM build records: ~/cwe-bench/build/katex-s2/ (FAIRNESS.md, HUMAN-DECISION.md, AUDIT-NOTES.md, build notes, gate reports)
- VM task package: ~/cwe-bench/tasks/katex-s2/
- VM trial folders: ~/.tb-graders/cwe/jobs/<job>/<trial>/ (postmortem-*/verdict.json = audit)
- Locked run archive: ~/.tb-graders/cwe/archive/
