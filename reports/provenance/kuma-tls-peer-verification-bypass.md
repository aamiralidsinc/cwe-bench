# kuma-tls-peer-verification-bypass

Build ID `kuma-s2`; delivered 2026-10-28 in client commit 3f7397d.

| Field | Value |
|---|---|
| slug | kuma-s2 |
| delivered_as | kuma-tls-peer-verification-bypass |
| client_commit | 3f7397d |
| delivered_date | 2026-10-28 |
| track | injection |
| round | scale-b5 |
| built_date | 2026-10-28 |
| repo | https://github.com/kumahq/kuma |
| cwe_id | CWE-295 |
| advisory | GHSA-V95X-XHQ5-4929 |
| vulnerable_commit | 7aaf172cf61e3b1fff312a9167a8f9f0747c228e |
| fix_commit | 2ecadac1aa2fd8cded4c2ab768949f4c2ec83e2a |
| deepseek | **failed 0/3** [0.8333, 0.8333, 0.8333] |
| mimo | **failed 0/3** [0.6667, 0.6667, 0.6667] |
| fairness | READY |
| decision | KEEP 2026-10-28 |

## Counted runs (job/trial = reward)

- deepseek-flash[1m]:kuma-s2-deepseek-r1-20261028-143255-n001/kuma-s2__ZGwkdfj=0.8333
- mimo-v2.6-pro:kuma-s2-mimo-r1-20261028-143301-n001/kuma-s2__SRpVvKf=0.6667
- deepseek-flash[1m]:kuma-s2-deepseek-r2-20261028-150650-n002/kuma-s2__4Ak8Ghr=0.8333
- deepseek-flash[1m]:kuma-s2-deepseek-r3-20261028-153216-n003/kuma-s2__v22stw9=0.8333
- mimo-v2.6-pro:kuma-s2-mimo-r2-20261028-153559-n002/kuma-s2__z9jZ6wG=0.6667
- mimo-v2.6-pro:kuma-s2-mimo-r3-20261028-163011-n003/kuma-s2__Z2NBHED=0.6667

## Records

- VM build records: ~/cwe-bench/build/kuma-s2/ (FAIRNESS.md, HUMAN-DECISION.md, AUDIT-NOTES.md, build notes, gate reports)
- VM task package: ~/cwe-bench/tasks/kuma-s2/
- VM trial folders: ~/.tb-graders/cwe/jobs/<job>/<trial>/ (postmortem-*/verdict.json = audit)
- Locked run archive: ~/.tb-graders/cwe/archive/
