# knowns-memory-id-path-injection

Build ID `knowns-ds`; delivered 2026-10-21 in client commit ea4ce53.

| Field | Value |
|---|---|
| slug | knowns-ds |
| delivered_as | knowns-memory-id-path-injection |
| client_commit | ea4ce53 |
| delivered_date | 2026-10-21 |
| track | injection |
| round | pre-scale round, built 2026-10-18 |
| built_date | 2026-10-18 |
| repo | https://github.com/knowns-dev/knowns |
| cwe_id | CWE-22 |
| advisory | GHSA-9GFJ-28HW-JCHP |
| vulnerable_commit | d3989829fb5095666d23d005b2f78a082832a396 |
| fix_commit | 09c5a96fd5817b941dc86669278c1a17db10ed4e |
| deepseek | **failed 0/3** [0.8929, 0.8571, 0.8571] |
| mimo | SOLVED 1/4 (1 solves counted, not audited) |
| fairness | READY |
| decision |  |

## Counted runs (job/trial = reward)

- deepseek-flash[1m]:knowns-ds-deepseek-r1-20261021-043055-n001/knowns-ds__PFwG9XX=0.8929
- deepseek-flash[1m]:knowns-ds-deepseek-r2-20261021-044914-n002/knowns-ds__oGcj5QB=0.8571
- deepseek-flash[1m]:knowns-ds-deepseek-r3-20261021-050419-n003/knowns-ds__TrrW9i5=0.8571
- mimo-v2.6-pro:knowns-ds-mimo-r1-20261021-052608-n004/knowns-ds__KDguecQ=0.8571
- mimo-v2.6-pro:knowns-ds-mimo-r2-20261021-064818-n005/knowns-ds__34zUiZN=0.8571
- mimo-v2.6-pro:knowns-ds-mimo-r3-20261021-080533-n006/knowns-ds__xD5bCkG=0.9643
- mimo-v2.6-pro:ext-actions-atrisk-knowns-ds-mimo-a2/knowns-memory-id-path-injection__cqu8Efc=1.0

## Records

- VM build records: ~/cwe-bench/build/knowns-ds/ (FAIRNESS.md, HUMAN-DECISION.md, AUDIT-NOTES.md, build notes, gate reports)
- VM task package: ~/cwe-bench/tasks/knowns-ds/
- VM trial folders: ~/.tb-graders/cwe/jobs/<job>/<trial>/ (postmortem-*/verdict.json = audit)
- Locked run archive: ~/.tb-graders/cwe/archive/
