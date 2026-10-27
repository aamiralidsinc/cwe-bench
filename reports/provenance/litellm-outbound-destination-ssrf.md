# litellm-outbound-destination-ssrf

Build ID `litellm-ds`; delivered 2026-10-20 in client commit d3e00f6.

| Field | Value |
|---|---|
| slug | litellm-ds |
| delivered_as | litellm-outbound-destination-ssrf |
| client_commit | d3e00f6 |
| delivered_date | 2026-10-20 |
| track | injection |
| round | pre-scale round, built 2026-10-18 |
| built_date | 2026-10-18 |
| repo | https://github.com/berriai/litellm |
| cwe_id | CWE-918 |
| advisory | GHSA-3CV6-JPF6-8222 |
| vulnerable_commit | 76ffefcc1c36f4e78178ca0278d38385cafa6ec6 |
| fix_commit | 473f72e63a9777d793fbbf57194d8ec4fb97bc1b |
| deepseek | **failed 0/3** [0, 0, 0] |
| mimo | **failed 0/3** [0, 0, 0] (+2 ungraded) |
| fairness |  |
| decision |  |

## Counted runs (job/trial = reward)

- deepseek-flash[1m]:litellm-ds-deepseek-r1-20261019-100033-n001/litellm-ds__wi62wLA=0.0
- deepseek-flash[1m]:litellm-ds-deepseek-r2-20261019-103318-n002/litellm-ds__qKQw6JP=0.0
- deepseek-flash[1m]:litellm-ds-deepseek-r3-20261019-114118-n003/litellm-ds__62fz2mf=0.0
- mimo-v2.6-pro:litellm-ds-mimo-r1-20261019-124919-n001/litellm-ds__dk9846F=0.0
- mimo-v2.6-pro:litellm-ds-mimo-r2-20261019-145142-n002/litellm-ds__v5dWanr=0.0
- mimo-v2.6-pro:litellm-ds-mimo-r4-20261020-005629-n001/litellm-ds__rpWfurz=0.0

## Records

- VM build records: ~/cwe-bench/build/litellm-ds/ (FAIRNESS.md, HUMAN-DECISION.md, AUDIT-NOTES.md, build notes, gate reports)
- VM task package: ~/cwe-bench/tasks/litellm-ds/
- VM trial folders: ~/.tb-graders/cwe/jobs/<job>/<trial>/ (postmortem-*/verdict.json = audit)
- Locked run archive: ~/.tb-graders/cwe/archive/
