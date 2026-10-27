# mistral-rs-image-source-file-read

Build ID `stk-mistral-rs-21576`; delivered 2026-10-27 in client commit 16a1d56.

| Field | Value |
|---|---|
| slug | stk-mistral-rs-21576 |
| delivered_as | mistral-rs-image-source-file-read |
| client_commit | 16a1d56 |
| delivered_date | 2026-10-27 |
| track | stacking |
| round | pre-scale round, built 2026-10-23 |
| built_date | 2026-10-23 |
| repo | https://github.com/EricLBuehler/mistral.rs |
| cwe_id | CWE-918 |
| advisory | 21576 (SSRF and arbitrary local file read through an untrusted media source) |
| vulnerable_commit | 7af17b627a88533d2fe6e192ed8db6c908e5ce5a |
| fix_commit | 74793379649febc758b6a0d4b71aa6aeabc80f9c |
| deepseek | **failed 0/3** [0, 0, 0] |
| mimo | **failed 0/3** [0, 0, 0] |
| fairness | READY |
| decision | KEEP 2026-10-25 |

## Counted runs (job/trial = reward)

- deepseek-flash[1m]:stk-mistral-rs-21576-deepseek-r1-20261024-212410-n001/stk-mistral-rs-21576__GeiSnUS=0.0
- mimo-v2.6-pro:stk-mistral-rs-21576-mimo-r1-20261024-212414-n001/stk-mistral-rs-21576__ANefqcE=0.0
- deepseek-flash[1m]:stk-mistral-rs-21576-deepseek-r2-20261024-224148-n002/stk-mistral-rs-21576__o9BJxQZ=0.0
- mimo-v2.6-pro:stk-mistral-rs-21576-mimo-r2-20261024-224146-n002/stk-mistral-rs-21576__NpKStp8=0
- deepseek-flash[1m]:stk-mistral-rs-21576-deepseek-r3-20261024-232220-n003/stk-mistral-rs-21576__jqCKVoS=0.0
- mimo-v2.6-pro:stk-mistral-rs-21576-mimo-r3-20261024-232809-n003/stk-mistral-rs-21576__Pp7EDuc=0.0

## Records

- VM build records: ~/cwe-bench/build/stk-mistral-rs-21576/ (FAIRNESS.md, HUMAN-DECISION.md, AUDIT-NOTES.md, build notes, gate reports)
- VM task package: ~/cwe-bench/tasks/stk-mistral-rs-21576/
- VM trial folders: ~/.tb-graders/cwe/jobs/<job>/<trial>/ (postmortem-*/verdict.json = audit)
- Locked run archive: ~/.tb-graders/cwe/archive/
