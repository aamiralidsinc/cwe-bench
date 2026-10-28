# hugo-xss

Build ID `hugo-ds`; delivered 2026-10-28 in client commit 3f7397d.

| Field | Value |
|---|---|
| slug | hugo-ds |
| delivered_as | hugo-xss |
| client_commit | 3f7397d |
| delivered_date | 2026-10-28 |
| track | injection |
| round | scale-b4 |
| built_date | 2026-10-24 |
| repo | https://github.com/gohugoio/hugo |
| cwe_id | CWE-79 |
| advisory | GHSA-C54G-XJWJ-8G82 / CVE-2026-50133 / GO-2026-5313 |
| vulnerable_commit | 90d9f812b2cafc79ca125a829936dec9654aec64 |
| fix_commit | e41a06447daa3071a01f333fdcec0a5153c3c8d1 |
| deepseek | **failed 0/3** [0.7, 0.7, 0.6] |
| mimo | **failed 0/3** [0.7, 0.6, 0.7] (+2 provider stop) |
| fairness | READY |
| decision | KEEP 2026-10-28 |

## Counted runs (job/trial = reward)

- deepseek-flash[1m]:hugo-ds-deepseek-r1-20261028-055935-n001/hugo-ds__QakXVhj=0.7
- mimo-v2.6-pro:hugo-ds-mimo-r1-20261028-055937-n001/hugo-ds__YpjVjqE=0.7
- deepseek-flash[1m]:hugo-ds-deepseek-r2-20261028-064735-n002/hugo-ds__jKVDKow=0.7
- deepseek-flash[1m]:hugo-ds-deepseek-r3-20261028-073615-n003/hugo-ds__8q3AJjt=0.6
- mimo-v2.6-pro:hugo-ds-mimo-r2-20261028-102828-n003/hugo-ds__La3FdnH=0.6
- mimo-v2.6-pro:hugo-ds-mimo-r3-20261028-143646-n005/hugo-ds__X5thoFo=0.7

## Records

- VM build records: ~/cwe-bench/build/hugo-ds/ (FAIRNESS.md, HUMAN-DECISION.md, AUDIT-NOTES.md, build notes, gate reports)
- VM task package: ~/cwe-bench/tasks/hugo-ds/
- VM trial folders: ~/.tb-graders/cwe/jobs/<job>/<trial>/ (postmortem-*/verdict.json = audit)
- Locked run archive: ~/.tb-graders/cwe/archive/
