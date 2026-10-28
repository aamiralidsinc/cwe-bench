# mathlive-xss

Build ID `mathlive-ds`; delivered 2026-10-28 in client commit 3f7397d.

| Field | Value |
|---|---|
| slug | mathlive-ds |
| delivered_as | mathlive-xss |
| client_commit | 3f7397d |
| delivered_date | 2026-10-28 |
| track | injection |
| round | scale-b4 |
| built_date | 2026-10-24 |
| repo | https://github.com/arnog/mathlive |
| cwe_id | CWE-79 |
| advisory | GHSA-FM7P-GW32-828P / CVE-2026-54705 |
| vulnerable_commit | 25db1a836f35e9fc8973599e7cb19be1e4d1b9c7 |
| fix_commit | 5fe1c46153883f9ec0249a5c8c34e64aaae9cfb8 |
| deepseek | **failed 0/3** [0, 0.8889, 0.8519] |
| mimo | **failed 0/3** [0.8519, 0.8889, 0.8889] |
| fairness | READY |
| decision | KEEP 2026-10-28 |

## Counted runs (job/trial = reward)

- deepseek-flash[1m]:mathlive-ds-deepseek-r1-20261028-031846-n001/mathlive-ds__iQt3f4D=0.0
- mimo-v2.6-pro:mathlive-ds-mimo-r1-20261028-031849-n001/mathlive-ds__eL62ZWe=0.8519
- deepseek-flash[1m]:mathlive-ds-deepseek-r2-20261028-033748-n002/mathlive-ds__eZTQqxC=0.8889
- deepseek-flash[1m]:mathlive-ds-deepseek-r3-20261028-035156-n003/mathlive-ds__Y7dWqe2=0.8519
- mimo-v2.6-pro:mathlive-ds-mimo-r2-20261028-040950-n002/mathlive-ds__PYX5bFw=0.8889
- mimo-v2.6-pro:mathlive-ds-mimo-r3-20261028-044853-n003/mathlive-ds__7zWCKEt=0.8889

## Records

- VM build records: ~/cwe-bench/build/mathlive-ds/ (FAIRNESS.md, HUMAN-DECISION.md, AUDIT-NOTES.md, build notes, gate reports)
- VM task package: ~/cwe-bench/tasks/mathlive-ds/
- VM trial folders: ~/.tb-graders/cwe/jobs/<job>/<trial>/ (postmortem-*/verdict.json = audit)
- Locked run archive: ~/.tb-graders/cwe/archive/
