# svgo-script-removal-xss

Build ID `pv-svgo`; delivered 2026-10-27 in client commit 335d156.

| Field | Value |
|---|---|
| slug | pv-svgo |
| delivered_as | svgo-script-removal-xss |
| client_commit | 335d156 |
| delivered_date | 2026-10-27 |
| track | precision-validation |
| round | precision-validation (GitHub Actions) |
| built_date | 2026-10-23 |
| repo | https://github.com/svg/svgo |
| cwe_id | CWE-79 |
| advisory | GHSA-4VPR-X523-8J87 / CVE-2026-84369 |
| vulnerable_commit | 72a23886b4698b27624b936f3a15a80afd36d75f |
| fix_commit | 994a9f00d79ddec68ce19a1ce9eb8ca08d747e4f |
| deepseek | **failed 0/3** [0, 0, 0] |
| mimo | **failed 0/4** [0, 0, 0, 0] |
| fairness | NOT_READY |
| decision | KEEP 2026-10-25 |

## Counted runs (job/trial = reward)

- mimo-v2.6-pro:ext-actions-pv-svgo-mimo-a1/pv-svgo__tsNFVLu=0.0
- deepseek-flash[1m]:ext-actions-pv-svgo-deepseek-a1/pv-svgo__c6ac489=0.0
- deepseek-flash[1m]:ext-actions-pv-svgo-deepseek-a2/pv-svgo__VLeh4Sm=0.0
- deepseek-flash[1m]:ext-actions-pv-svgo-deepseek-a3/pv-svgo__i4MVw8E=0.0
- mimo-v2.6-pro:ext-actions-pv-svgo-mimo-a2/pv-svgo__cHvP7C5=0.0
- mimo-v2.6-pro:ext-actions-pv-svgo-mimo-a3/pv-svgo__vxrqG3Z=0.0
- mimo-v2.6-pro:ext-actions-pv-svgo-mimo-a4/pv-svgo__GSLpupC=0.0

## Records

- VM build records: ~/cwe-bench/build/pv-svgo/ (FAIRNESS.md, HUMAN-DECISION.md, AUDIT-NOTES.md, build notes, gate reports)
- VM task package: ~/cwe-bench/tasks/pv-svgo/
- VM trial folders: ~/.tb-graders/cwe/jobs/<job>/<trial>/ (postmortem-*/verdict.json = audit)
- Locked run archive: ~/.tb-graders/cwe/archive/
