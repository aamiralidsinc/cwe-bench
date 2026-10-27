# tinacms-storage-path-traversal

Build ID `tinacms-ds`; delivered 2026-10-21 in client commit ea4ce53.

| Field | Value |
|---|---|
| slug | tinacms-ds |
| delivered_as | tinacms-storage-path-traversal |
| client_commit | ea4ce53 |
| delivered_date | 2026-10-21 |
| track | injection |
| round | pre-scale round, built 2026-10-18 |
| built_date | 2026-10-18 |
| repo | https://github.com/tinacms/tinacms |
| cwe_id | CWE-639 |
| advisory | GHSA-8MQ9-5FW2-5RM4 |
| vulnerable_commit | d08ffb40de47f8c8296646b9076af79a26d76c47 |
| fix_commit | d44558e9b4502d4f4fc2c970d22985339fe2b6ce |
| deepseek | **failed 0/3** [0, 0, 0] |
| mimo | **failed 0/3** [0.9726, 0, 0] |
| fairness | READY |
| decision |  |

## Counted runs (job/trial = reward)

- deepseek-flash[1m]:tinacms-ds-deepseek-r1-20261021-043049-n001/tinacms-ds__KhQA87G=0.0
- deepseek-flash[1m]:tinacms-ds-deepseek-r2-20261021-044142-n002/tinacms-ds__3QABXUL=0.0
- deepseek-flash[1m]:tinacms-ds-deepseek-r3-20261021-045241-n003/tinacms-ds__K29jHnf=0.0
- mimo-v2.6-pro:tinacms-ds-mimo-r1-20261021-050531-n004/tinacms-ds__wCerrMz=0.9726
- mimo-v2.6-pro:tinacms-ds-mimo-r2-20261021-061354-n005/tinacms-ds__JWvZsmx=0.0
- mimo-v2.6-pro:tinacms-ds-mimo-r3-20261021-080649-n006/tinacms-ds__VA3pTgP=0.0

## Records

- VM build records: ~/cwe-bench/build/tinacms-ds/ (FAIRNESS.md, HUMAN-DECISION.md, AUDIT-NOTES.md, build notes, gate reports)
- VM task package: ~/cwe-bench/tasks/tinacms-ds/
- VM trial folders: ~/.tb-graders/cwe/jobs/<job>/<trial>/ (postmortem-*/verdict.json = audit)
- Locked run archive: ~/.tb-graders/cwe/archive/
