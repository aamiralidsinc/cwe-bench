# electron-builder-credential-exposure

Build ID `electron-builder-ds`; delivered 2026-10-20 in client commit d3e00f6.

| Field | Value |
|---|---|
| slug | electron-builder-ds |
| delivered_as | electron-builder-credential-exposure |
| client_commit | d3e00f6 |
| delivered_date | 2026-10-20 |
| track | injection |
| round | pre-scale round, built 2026-10-18 |
| built_date | 2026-10-18 |
| repo | https://github.com/electron-userland/electron-builder |
| cwe_id | CWE-200 |
| advisory | GHSA-P2F4-R6V6-J797 |
| vulnerable_commit | 8a035f836bb79d5346c69246530190dd72ec4519 |
| fix_commit | 22a7532bd01b9fb42cff7c58d599c7ad683569fe |
| deepseek | **failed 0/3** [0.7222, 0.6111, 0.7222] |
| mimo | **failed 0/3** [0.6111, 0.6111, 0.6111] |
| fairness | READY |
| decision | KEEP 2026-10-20 |

## Counted runs (job/trial = reward)

- deepseek-flash[1m]:electron-builder-ds-deepseek-r1-20261020-074655-n001/electron-builder-ds__UxTqx9g=0.7222
- deepseek-flash[1m]:electron-builder-ds-deepseek-r2-20261020-081533-n002/electron-builder-ds__YkKUyBm=0.6111
- deepseek-flash[1m]:electron-builder-ds-deepseek-r3-20261020-083617-n003/electron-builder-ds__TpTFfT8=0.7222
- mimo-v2.6-pro:electron-builder-ds-mimo-r1-20261020-085635-n004/electron-builder-ds__rNFeEdd=0.6111
- mimo-v2.6-pro:electron-builder-ds-mimo-r2-20261020-094957-n005/electron-builder-ds__Q2xxAEU=0.6111
- mimo-v2.6-pro:electron-builder-ds-mimo-r3-20261020-103026-n006/electron-builder-ds__LAKH2Xk=0.6111

## Records

- VM build records: ~/cwe-bench/build/electron-builder-ds/ (FAIRNESS.md, HUMAN-DECISION.md, AUDIT-NOTES.md, build notes, gate reports)
- VM task package: ~/cwe-bench/tasks/electron-builder-ds/
- VM trial folders: ~/.tb-graders/cwe/jobs/<job>/<trial>/ (postmortem-*/verdict.json = audit)
- Locked run archive: ~/.tb-graders/cwe/archive/
