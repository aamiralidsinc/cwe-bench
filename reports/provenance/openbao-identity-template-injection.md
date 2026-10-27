# openbao-identity-template-injection

Build ID `openbao-ds`; delivered 2026-10-21 in client commit ea4ce53.

| Field | Value |
|---|---|
| slug | openbao-ds |
| delivered_as | openbao-identity-template-injection |
| client_commit | ea4ce53 |
| delivered_date | 2026-10-21 |
| track | injection |
| round | pre-scale round, built 2026-10-19 |
| built_date | 2026-10-19 |
| repo | https://github.com/openbao/openbao |
| cwe_id | CWE-863 |
| advisory | GHSA-59W7-V8RR-PR4P / CVE-2026-71543 / GO-2026-6556 |
| vulnerable_commit | 681f6e2730f03f9cd2a5ce7d056fc957622cfe81 |
| fix_commit | 2d4ebafec5c524408b3d4ac1198df909cb7ac8c1 |
| deepseek | **failed 0/3** [0, 0, 0] |
| mimo | **failed 0/3** [0, 0, 0] |
| fairness | READY |
| decision |  |

## Counted runs (job/trial = reward)

- deepseek-flash[1m]:openbao-ds-deepseek-r1-20261021-043026-n001/openbao-ds__chkPmCb=0.0
- deepseek-flash[1m]:openbao-ds-deepseek-r2-20261021-045134-n002/openbao-ds__oozABht=0.0
- deepseek-flash[1m]:openbao-ds-deepseek-r3-20261021-050621-n003/openbao-ds__5bt7kLc=0.0
- mimo-v2.6-pro:openbao-ds-mimo-r1-20261021-054054-n004/openbao-ds__vA95ggc=0.0
- mimo-v2.6-pro:openbao-ds-mimo-r2-20261021-070110-n005/openbao-ds__kZALizL=0.0
- mimo-v2.6-pro:openbao-ds-mimo-r3-20261021-075219-n006/openbao-ds__rkUeVh5=0.0

## Records

- VM build records: ~/cwe-bench/build/openbao-ds/ (FAIRNESS.md, HUMAN-DECISION.md, AUDIT-NOTES.md, build notes, gate reports)
- VM task package: ~/cwe-bench/tasks/openbao-ds/
- VM trial folders: ~/.tb-graders/cwe/jobs/<job>/<trial>/ (postmortem-*/verdict.json = audit)
- Locked run archive: ~/.tb-graders/cwe/archive/
