# uri-js-host-spoofing

Build ID `uri.js-s3`; delivered 2026-10-28 in client commit 3f7397d.

| Field | Value |
|---|---|
| slug | uri.js-s3 |
| delivered_as | uri-js-host-spoofing |
| client_commit | 3f7397d |
| delivered_date | 2026-10-28 |
| track | injection |
| round | scale-b3 |
| built_date | 2026-10-27 |
| repo | https://github.com/medialize/URI.js |
| cwe_id | CWE-639 |
| advisory | GHSA-89gv-h8wf-cg8r / GHSA-gcv8-gh4r-25x6 |
| vulnerable_commit | 622db6d8d6e650d6de4300c97779de50e3331095 |
| fix_commit | ac43ca8f80c042f0256fb551ea5203863dec4481 / 6ea641cc8648b025ed5f30b090c2abd4d1a5249f |
| deepseek | **failed 0/3** [0.6122, 0.551, 0.6122] |
| mimo | **failed 0/3** [0.551, 0.8776, 0.551] |
| fairness | READY |
| decision | KEEP 2026-10-28 |

## Counted runs (job/trial = reward)

- deepseek-flash[1m]:uri.js-s3-deepseek-r1-20261028-014510-n001/uri.js-s3__3rZNiC3=0.6122
- mimo-v2.6-pro:uri.js-s3-mimo-r1-20261028-014515-n001/uri.js-s3__dqmuWwz=0.551
- deepseek-flash[1m]:uri.js-s3-deepseek-r2-20261028-015633-n002/uri.js-s3__qMqYS3S=0.551
- deepseek-flash[1m]:uri.js-s3-deepseek-r3-20261028-021220-n003/uri.js-s3__RGZpx4H=0.6122
- mimo-v2.6-pro:uri.js-s3-mimo-r2-20261028-024807-n002/uri.js-s3__wGRnnbC=0.8776
- mimo-v2.6-pro:uri.js-s3-mimo-r3-20261028-035414-n003/uri.js-s3__AmJhtmr=0.551

## Records

- VM build records: ~/cwe-bench/build/uri.js-s3/ (FAIRNESS.md, HUMAN-DECISION.md, AUDIT-NOTES.md, build notes, gate reports)
- VM task package: ~/cwe-bench/tasks/uri.js-s3/
- VM trial folders: ~/.tb-graders/cwe/jobs/<job>/<trial>/ (postmortem-*/verdict.json = audit)
- Locked run archive: ~/.tb-graders/cwe/archive/
