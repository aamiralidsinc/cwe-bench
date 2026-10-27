# seaweedfs-table-storage-authz

Build ID `seaweedfs-ds`; delivered 2026-10-20 in client commit d3e00f6.

| Field | Value |
|---|---|
| slug | seaweedfs-ds |
| delivered_as | seaweedfs-table-storage-authz |
| client_commit | d3e00f6 |
| delivered_date | 2026-10-20 |
| track | injection |
| round | pre-scale round, built 2026-10-19 |
| built_date | 2026-10-19 |
| repo | https://github.com/seaweedfs/seaweedfs |
| cwe_id | CWE-863 |
| advisory | GHSA-HGPF-8634-G44C |
| vulnerable_commit | b56d155b315777dab97caea4380528ace087b529 |
| fix_commit | b13463880c1fa62e255c058a9228b63cc95b4b36 |
| deepseek | **failed 0/3** [0, 0, 0] |
| mimo | **failed 0/3** [0.9032, 0.871, 0] (+1 ungraded) |
| fairness | READY |
| decision | KEEP 2026-10-20 |

## Counted runs (job/trial = reward)

- deepseek-flash[1m]:seaweedfs-ds-deepseek-r1-20261020-074640-n001/seaweedfs-ds__DQWJ9cT=0.0
- deepseek-flash[1m]:seaweedfs-ds-deepseek-r2-20261020-082205-n002/seaweedfs-ds__s9Gjvht=0.0
- deepseek-flash[1m]:seaweedfs-ds-deepseek-r3-20261020-090018-n003/seaweedfs-ds__k8CqdcR=0.0
- mimo-v2.6-pro:seaweedfs-ds-mimo-r1-20261020-093340-n005/seaweedfs-ds__rerrMS9=0.9032
- mimo-v2.6-pro:seaweedfs-ds-mimo-r2-20261020-111746-n006/seaweedfs-ds__dtCgcaP=0.871
- mimo-v2.6-pro:seaweedfs-ds-mimo-r3-20261020-124944-n007/seaweedfs-ds__ohbLUZ2=0.0

## Records

- VM build records: ~/cwe-bench/build/seaweedfs-ds/ (FAIRNESS.md, HUMAN-DECISION.md, AUDIT-NOTES.md, build notes, gate reports)
- VM task package: ~/cwe-bench/tasks/seaweedfs-ds/
- VM trial folders: ~/.tb-graders/cwe/jobs/<job>/<trial>/ (postmortem-*/verdict.json = audit)
- Locked run archive: ~/.tb-graders/cwe/archive/
