# snowflake-sqlalchemy-sql-injection

Build ID `snowflake-sqlalchemy-ds`; delivered 2026-10-28 in client commit 3f7397d.

| Field | Value |
|---|---|
| slug | snowflake-sqlalchemy-ds |
| delivered_as | snowflake-sqlalchemy-sql-injection |
| client_commit | 3f7397d |
| delivered_date | 2026-10-28 |
| track | injection |
| round | scale-b4 |
| built_date | 2026-10-24 |
| repo | https://github.com/snowflakedb/snowflake-sqlalchemy |
| cwe_id | CWE-89 |
| advisory | GHSA-8G6F-QW9X-4Q6Q |
| vulnerable_commit | 20ad218611bad394db55b1e1530e6d4853d2ab6d |
| fix_commit | 2c33792c91449e746a2c7ef24c25f0ede0a4a875 |
| deepseek | **failed 0/3** [0, 0.9412, 0] |
| mimo | **failed 0/3** [0, 0.9118, 0.9118] |
| fairness | READY |
| decision | KEEP 2026-10-28 |

## Counted runs (job/trial = reward)

- deepseek-flash[1m]:snowflake-sqlalchemy-ds-deepseek-r1-20261028-100142-n001/snowflake-sqlalchemy-ds__KoXpE6b=0.0
- mimo-v2.6-pro:snowflake-sqlalchemy-ds-mimo-r1-20261028-100144-n001/snowflake-sqlalchemy-ds__HcN8QgD=0.0
- deepseek-flash[1m]:snowflake-sqlalchemy-ds-deepseek-r2-20261028-102447-n002/snowflake-sqlalchemy-ds__74RZAHD=0.9412
- deepseek-flash[1m]:snowflake-sqlalchemy-ds-deepseek-r3-20261028-104542-n003/snowflake-sqlalchemy-ds__duMaMxX=0.0
- mimo-v2.6-pro:snowflake-sqlalchemy-ds-mimo-r2-20261028-113706-n002/snowflake-sqlalchemy-ds__89Ncqv9=0.9118
- mimo-v2.6-pro:snowflake-sqlalchemy-ds-mimo-r3-20261028-124915-n003/snowflake-sqlalchemy-ds__pc4QaDx=0.9118

## Records

- VM build records: ~/cwe-bench/build/snowflake-sqlalchemy-ds/ (FAIRNESS.md, HUMAN-DECISION.md, AUDIT-NOTES.md, build notes, gate reports)
- VM task package: ~/cwe-bench/tasks/snowflake-sqlalchemy-ds/
- VM trial folders: ~/.tb-graders/cwe/jobs/<job>/<trial>/ (postmortem-*/verdict.json = audit)
- Locked run archive: ~/.tb-graders/cwe/archive/
