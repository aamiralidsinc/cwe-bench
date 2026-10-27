# protobufjs-prototype-pollution

Build ID `protobuf.js-ds`; delivered 2026-10-20 in client commit d3e00f6.

| Field | Value |
|---|---|
| slug | protobuf.js-ds |
| delivered_as | protobufjs-prototype-pollution |
| client_commit | d3e00f6 |
| delivered_date | 2026-10-20 |
| track | injection |
| round | pre-scale round, built 2026-10-18 |
| built_date | 2026-10-18 |
| repo | https://github.com/protobufjs/protobuf.js |
| cwe_id | CWE-1321 |
| advisory | GHSA-JFJ6-75FJ-8934 |
| vulnerable_commit | 1aca107aa7938d1e49a25f9653186db2f40a0253 |
| fix_commit | 9f97fe413072d3beb52c74e62d88ea8adc9444d8 |
| deepseek | **failed 0/3** [0.9412, 0.9118, 0.9118] |
| mimo | **failed 0/3** [0.4706, 0.9118, 0.7941] |
| fairness | READY |
| decision | KEEP 2026-10-20 |

## Counted runs (job/trial = reward)

- deepseek-flash[1m]:protobuf.js-ds-deepseek-r1-20261020-074647-n001/protobuf.js-ds__SwQxHsZ=0.9412
- deepseek-flash[1m]:protobuf.js-ds-deepseek-r2-20261020-081907-n002/protobuf.js-ds__EJWhkJu=0.9118
- deepseek-flash[1m]:protobuf.js-ds-deepseek-r3-20261020-091514-n003/protobuf.js-ds__Nj4aqUm=0.9118
- mimo-v2.6-pro:protobuf.js-ds-mimo-r1-20261020-094807-n004/protobuf.js-ds__EP5yghL=0.4706
- mimo-v2.6-pro:protobuf.js-ds-mimo-r2-20261020-124638-n005/protobuf.js-ds__9FouLXP=0.9118
- mimo-v2.6-pro:protobuf.js-ds-mimo-r3-20261020-134834-n006/protobuf.js-ds__2RTfZoF=0.7941

## Records

- VM build records: ~/cwe-bench/build/protobuf.js-ds/ (FAIRNESS.md, HUMAN-DECISION.md, AUDIT-NOTES.md, build notes, gate reports)
- VM task package: ~/cwe-bench/tasks/protobuf.js-ds/
- VM trial folders: ~/.tb-graders/cwe/jobs/<job>/<trial>/ (postmortem-*/verdict.json = audit)
- Locked run archive: ~/.tb-graders/cwe/archive/
