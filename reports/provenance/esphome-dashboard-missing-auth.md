# esphome-dashboard-missing-auth

Build ID `pv-device-builder`; delivered 2026-10-27 in client commit 335d156.

| Field | Value |
|---|---|
| slug | pv-device-builder |
| delivered_as | esphome-dashboard-missing-auth |
| client_commit | 335d156 |
| delivered_date | 2026-10-27 |
| track | precision-validation |
| round | precision-validation (GitHub Actions) |
| built_date | 2026-10-23 |
| repo | https://github.com/esphome/device-builder |
| cwe_id | CWE-306 |
| advisory | GHSA-RRXG-G2PF-6HH4 / CVE-2026-59178 / PYSEC-2026-4049 |
| vulnerable_commit | 04bcde551ad1ff3f6e94279f8aac65effcd2977e |
| fix_commit | 9e294f729c3eb7334bb57b9fc49b75b728052f52 |
| deepseek | **failed 0/3** [0, 0.6, 0.6] |
| mimo | **failed 0/3** [0.8, 0.6, 0.6] |
| fairness | READY |
| decision | KEEP 2026-10-27 |

## Counted runs (job/trial = reward)

- deepseek-flash[1m]:ext-actions-pv-device-builder-deepseek-a1/pv-device-builder__NPtGkx6=0.0
- mimo-v2.6-pro:ext-actions-pv-device-builder-mimo-a1/pv-device-builder__4SytfVC=0.8
- deepseek-flash[1m]:ext-actions-pv-device-builder-deepseek-a2/pv-device-builder__hGURxEj=0.6
- deepseek-flash[1m]:ext-actions-pv-device-builder-deepseek-a3/pv-device-builder__FNznaDJ=0.6
- mimo-v2.6-pro:ext-actions-pv-device-builder-mimo-a2/pv-device-builder__bauuUfn=0.6
- mimo-v2.6-pro:ext-actions-pv-device-builder-mimo-a3/pv-device-builder__xL2L2k5=0.6

## Records

- VM build records: ~/cwe-bench/build/pv-device-builder/ (FAIRNESS.md, HUMAN-DECISION.md, AUDIT-NOTES.md, build notes, gate reports)
- VM task package: ~/cwe-bench/tasks/pv-device-builder/
- VM trial folders: ~/.tb-graders/cwe/jobs/<job>/<trial>/ (postmortem-*/verdict.json = audit)
- Locked run archive: ~/.tb-graders/cwe/archive/
