# liferay-unsanctioned-redirect

Build ID `stk-liferay-portal-ghsa3qq5`; delivered 2026-10-27 in client commit 8143235.

| Field | Value |
|---|---|
| slug | stk-liferay-portal-ghsa3qq5 |
| delivered_as | liferay-unsanctioned-redirect |
| client_commit | 8143235 |
| delivered_date | 2026-10-27 |
| track | stacking |
| round | scale-b1 |
| built_date | 2026-10-26 |
| repo | https://github.com/liferay/liferay-portal |
| cwe_id | CWE-601 |
| advisory | GHSA-w397-9p2j-6x23 / GHSA-3qq5-wcrx-4h8r |
| vulnerable_commit | 1f8273638314df2094ece27d9193ea121b431d19 |
| fix_commit | 8aa3fd76f34d / 638988547641 / 242e8bcabe3e / 7aca15e7195a / 66f3ae610c24 / dca931af71a3 / 3c5ee2054b44 / 5c9655c941b1 / 702a1e358966 / f015ad20bd9e |
| deepseek | **failed 0/3** [0.4286, 0.4286, 0.4286] |
| mimo | **failed 0/3** [0.4286, 0.4286, 0.4286] |
| fairness | READY |
| decision | KEEP 2026-10-27 |

## Counted runs (job/trial = reward)

- deepseek-flash[1m]:stk-liferay-portal-ghsa3qq5-deepseek-r1-20261026-195845-n001/stk-liferay-portal-ghsa3qq5__m52noHy=0.4286
- mimo-v2.6-pro:stk-liferay-portal-ghsa3qq5-mimo-r1-20261026-195916-n001/stk-liferay-portal-ghsa3qq5__CjMyUVG=0.4286
- deepseek-flash[1m]:stk-liferay-portal-ghsa3qq5-deepseek-r2-20261026-202848-n002/stk-liferay-portal-ghsa3qq5__5sqYzjm=0.4286
- deepseek-flash[1m]:stk-liferay-portal-ghsa3qq5-deepseek-r3-20261026-210547-n003/stk-liferay-portal-ghsa3qq5__uzYcmVd=0.4286
- mimo-v2.6-pro:stk-liferay-portal-ghsa3qq5-mimo-r2-20261026-214201-n002/stk-liferay-portal-ghsa3qq5__Hxb2qZ5=0.4286
- mimo-v2.6-pro:stk-liferay-portal-ghsa3qq5-mimo-r3-20261027-004325-n003/stk-liferay-portal-ghsa3qq5__cuS2YLq=0.4286

## Records

- VM build records: ~/cwe-bench/build/stk-liferay-portal-ghsa3qq5/ (FAIRNESS.md, HUMAN-DECISION.md, AUDIT-NOTES.md, build notes, gate reports)
- VM task package: ~/cwe-bench/tasks/stk-liferay-portal-ghsa3qq5/
- VM trial folders: ~/.tb-graders/cwe/jobs/<job>/<trial>/ (postmortem-*/verdict.json = audit)
- Locked run archive: ~/.tb-graders/cwe/archive/
