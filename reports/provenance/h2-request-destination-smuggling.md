# h2-request-destination-smuggling

Build ID `h2-s2`; delivered 2026-10-27 in client commit 16a1d56.

| Field | Value |
|---|---|
| slug | h2-s2 |
| delivered_as | h2-request-destination-smuggling |
| client_commit | 16a1d56 |
| delivered_date | 2026-10-27 |
| track | injection |
| round | scale-b2 |
| built_date | 2026-10-26 |
| repo | https://github.com/python-hyper/h2 |
| cwe_id | CWE-444 |
| advisory | GHSA-6HR6-W5QG-QMWG |
| vulnerable_commit | 04d3b87cbc1db020d28c7cfb44fe194558efbdde |
| fix_commit | 292a40829feefda98c8509dcdbbb4a57af9bd6a6 |
| deepseek | **failed 0/3** [0.7143, 0.7143, 0.7143] |
| mimo | **failed 0/3** [0.7143, 0.7143, 0.7143] |
| fairness | READY |
| decision | KEEP 2026-10-27 |

## Counted runs (job/trial = reward)

- deepseek-flash[1m]:h2-s2-deepseek-r1-20261026-222056-n001/h2-s2__D97E5Gw=0.7143
- mimo-v2.6-pro:h2-s2-mimo-r1-20261026-222113-n001/h2-s2__vcWDd3R=0.7143
- deepseek-flash[1m]:h2-s2-deepseek-r2-20261026-224238-n002/h2-s2__3uCoZar=0.7143
- mimo-v2.6-pro:h2-s2-mimo-r2-20261026-224821-n002/h2-s2__8e7cxJp=0.7143
- deepseek-flash[1m]:h2-s2-deepseek-r3-20261026-230144-n003/h2-s2__WiEKoiz=0.7143
- mimo-v2.6-pro:h2-s2-mimo-r3-20261026-232109-n003/h2-s2__UwtXNop=0.7143

## Records

- VM build records: ~/cwe-bench/build/h2-s2/ (FAIRNESS.md, HUMAN-DECISION.md, AUDIT-NOTES.md, build notes, gate reports)
- VM task package: ~/cwe-bench/tasks/h2-s2/
- VM trial folders: ~/.tb-graders/cwe/jobs/<job>/<trial>/ (postmortem-*/verdict.json = audit)
- Locked run archive: ~/.tb-graders/cwe/archive/
