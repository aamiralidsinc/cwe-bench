# Handoff state — 2026-10-20 19:21:06

Rebuilt by the pipeline from the filesystem; do not edit. Agents signal with `python scripts/handoff.py claim|done <request>`.

**Counts:** consumed 16, in_progress 5, pending 3

## For the Cursor agent (Grok)

- answer: `data/handoff/requests/GHSA-36fc-7wjg-mfvj__c2.md`
- answer: `data/handoff/requests/GHSA-hffm-xvc3-vprc__c2.md`
- answer: `data/handoff/requests/PYSEC-2026-4200__c2.md`

## Next actions

- CURSOR: answer 3 pending request(s) (list above)

## Pipeline

- stage 3: running
- stage 4: running
- stage 5: idle

## Results

- GHSA-59w7-v8rr-pr4p: stage4=-, stage5=-
- GHSA-jmg2-rcxh-w8q3: stage4=failed_oracle, stage5=-
- PYSEC-2026-3837: stage4=-, stage5=-

## Last tick

- stage 3 consumed 5 candidates (rc=0): generated ['GHSA-59w7-v8rr-pr4p'], retired ['GHSA-3vfr-4gwf-qxfp'], answers sent back for retry none
- stage 4 already running; 2 generated tasks wait: ['GHSA-59w7-v8rr-pr4p', 'PYSEC-2026-3837']
- queue top-up: picked 2 new candidates (env build + Grok requests): ['GHSA-5wx6-mg75-v57r', 'GHSA-8wmf-6v46-5gfg']

## Requests

| request | status | claimed |
|---|---|---|
| GHSA-36fc-7wjg-mfvj__c1.md | consumed | 2026-10-20 18:14:33 |
| GHSA-36fc-7wjg-mfvj__c2.md | pending |  |
| GHSA-3vfr-4gwf-qxfp__c1.md | consumed | 2026-10-20 18:14:33 |
| GHSA-59w7-v8rr-pr4p__c1.md | consumed |  |
| GHSA-59w7-v8rr-pr4p__c2.md | consumed | 2026-10-20 18:45:32 |
| GHSA-5p3m-vhh6-9236__c1.md | in_progress | 2026-10-20 19:16:24 |
| GHSA-7w8c-qgxg-m7jx__c1.md | consumed |  |
| GHSA-7w8c-qgxg-m7jx__c2.md | in_progress | 2026-10-20 18:45:32 |
| GHSA-93xw-j965-9mx3__c1.md | consumed | 2026-10-20 18:14:33 |
| GHSA-93xw-j965-9mx3__c2.md | in_progress | 2026-10-20 19:16:24 |
| GHSA-9rh9-hf3w-9fgg__dbd417839d.md | consumed |  |
| GHSA-hffm-xvc3-vprc__c1.md | consumed | 2026-10-20 18:14:33 |
| GHSA-hffm-xvc3-vprc__c2.md | pending |  |
| GHSA-jmg2-rcxh-w8q3__a1bb158a2c.md | consumed |  |
| GHSA-jmg2-rcxh-w8q3__c2.md | consumed |  |
| GHSA-rjg7-r26h-cfp2__c1.md | consumed |  |
| GHSA-rqx4-3f6q-3x2v__c1.md | in_progress | 2026-10-20 19:16:24 |
| GHSA-vrcc-3ch7-hppw__1b834ea3fd.md | consumed |  |
| GO-2026-4966__c1.md | in_progress | 2026-10-20 19:16:24 |
| PYSEC-2026-3837__1be2343f0f.md | consumed |  |
| PYSEC-2026-3837__c2.md | consumed |  |
| PYSEC-2026-4200__c1.md | consumed | 2026-10-20 18:14:33 |
| PYSEC-2026-4200__c2.md | pending |  |
| PYSEC-2026-495__9267adb784.md | consumed |  |

## Candidates

| candidate | generated | retired | stage 4 | stage 5 |
|---|---|---|---|---|
| GHSA-36fc-7wjg-mfvj |  |  |  |  |
| GHSA-3vfr-4gwf-qxfp |  | yes |  |  |
| GHSA-59w7-v8rr-pr4p | yes |  |  |  |
| GHSA-5p3m-vhh6-9236 |  |  |  |  |
| GHSA-7w8c-qgxg-m7jx |  |  |  |  |
| GHSA-93xw-j965-9mx3 |  |  |  |  |
| GHSA-9rh9-hf3w-9fgg |  | yes |  |  |
| GHSA-hffm-xvc3-vprc |  |  |  |  |
| GHSA-jmg2-rcxh-w8q3 | yes |  | failed_oracle |  |
| GHSA-rjg7-r26h-cfp2 |  | yes |  |  |
| GHSA-rqx4-3f6q-3x2v |  |  |  |  |
| GHSA-vrcc-3ch7-hppw |  | yes |  |  |
| GO-2026-4966 |  |  |  |  |
| PYSEC-2026-3837 | yes |  |  |  |
| PYSEC-2026-4200 |  |  |  |  |
| PYSEC-2026-495 |  | yes |  |  |
