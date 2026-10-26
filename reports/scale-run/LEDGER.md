# Scale-run ledger

_Generated 2026-10-26 15:11 UTC by pipelines/router/scale_ledger.py from build/audit/ledger.md._

Verdicts: both models must fail 3/3 with every failing run audited trustworthy (solves are counted without audit, owner rule 2026-10-25); a breaker is final once fairness is READY (human decisions included).

## Summary

| | scale-b1 | scale-b2 | all |
|---|---|---|---|
| Verdict: - | 41 | 60 | 101 |
| Verdict: solved by both | 12 | 0 | 12 |
| Verdict: one model 0/3, other open | 4 | 0 | 4 |
| Verdict: BOTH-MODEL BREAKER | 3 | 0 | 3 |
| Verdict: not a breaker (one solved; other open) | 2 | 0 | 2 |
| Verdict: DeepSeek-only breaker | 1 | 0 | 1 |
| Verdict: trialling | 1 | 0 | 1 |
| Gate: checks or re-gate pending | 33 | 8 | 41 |
| Gate: building | 0 | 31 | 31 |
| Gate: sound | 23 | 0 | 23 |
| Gate: queued | 0 | 17 | 17 |
| Gate: gate error | 7 | 0 | 7 |
| Gate: declined by builder | 0 | 3 | 3 |
| Gate: unsound | 1 | 0 | 1 |
| Gate: listing hold | 0 | 1 | 1 |

## Breakers

| Task | Step | Batch | DeepSeek | MiMo | Audits | Fairness |
|---|---|---|---|---|---|---|
| stk-froxlor-ghsa75h4 | 1 stacking | scale-b1 | BOTH-MODEL BREAKER — failed 0/3 [0.875, 0.75, 0.875] | failed 0/3 [0.875, 0.75, 0.75] | 6 trusted / 0 untrusted / 0 pending | READY (human decision KEEP 2026-10-26; review said READY ) |
| stk-ansible-ghsavp9j | 1 stacking | scale-b1 | DeepSeek-only breaker — failed 0/3 [0.75, 0.75, 0.75] | SOLVED 1/1 (1 solves counted, not audite | 3 trusted / 0 untrusted / 0 pending | - |
| stk-passenger-ghsaqw8w | 1 stacking | scale-b1 | BOTH-MODEL BREAKER — failed 0/3 [0.8333, 0.8333, 0.8333] | failed 0/3 [0.6667, 0.8333, 0.8333] | 6 trusted / 0 untrusted / 0 pending | - |
| fastify-s2 | dry run | scale-b1 | BOTH-MODEL BREAKER — failed 0/3 [0.7857, 0.7857, 0.8571] | failed 0/3 [0.7857, 0.7857, 0.7857] | 6 trusted / 0 untrusted / 0 pending | READY (human decision KEEP 2026-10-26; review said READY ) |

## All tasks

| Task | Batch | Step | Gate | DeepSeek | MiMo | Verdict | Audits | Fairness | Notes |
|---|---|---|---|---|---|---|---|---|---|
| stk-tract-21634 | scale-b1 | 1 stacking | sound | SOLVED 1/1 (1 solves counted, not audited) | SOLVED 1/1 (1 solves counted, not audited) | solved by both | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-october-ghsar89v | scale-b1 | 1 stacking | sound | SOLVED 1/1 (1 solves counted, not audited) | 0/1 so far, needs 3 [0] | not a breaker (one solved; other open) | 1 trusted / 0 untrusted / 0 pending | - |  |
| stk-gonic-15195 | scale-b1 | 1 stacking | sound | SOLVED 1/1 (1 solves counted, not audited) | SOLVED 1/1 (1 solves counted, not audited) | solved by both | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-froxlor-ghsa75h4 | scale-b1 | 1 stacking | sound | failed 0/3 [0.875, 0.75, 0.875] | failed 0/3 [0.875, 0.75, 0.75] | BOTH-MODEL BREAKER | 6 trusted / 0 untrusted / 0 pending | READY (human decision KEEP 2026-10-26; review said READY ) |  |
| stk-ansible-ghsavp9j | scale-b1 | 1 stacking | sound | failed 0/3 [0.75, 0.75, 0.75] | SOLVED 1/1 (1 solves counted, not audited) | DeepSeek-only breaker | 3 trusted / 0 untrusted / 0 pending | - |  |
| stk-spark-2338 | scale-b1 | 1 stacking | sound | SOLVED 1/1 (1 solves counted, not audited) | SOLVED 1/1 (1 solves counted, not audited) | solved by both | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-silverpeas-core-27788 | scale-b1 | 1 stacking | sound | failed 0/3 [0, 0.2857, 0.2857] | 0/2 so far, needs 3 [0.2857, 0.5714] | one model 0/3, other open | 5 trusted / 0 untrusted / 0 pending | - |  |
| stk-cms-ghsagp2f | scale-b1 | 1 stacking | sound | failed 0/3 [0, 0, 0] | 0/2 so far, needs 3 [0, 0.625] (+1 audit: untrusted) | one model 0/3, other open | 5 trusted / 1 untrusted / 0 pending | - |  |
| stk-tomcat-ghsap26v | scale-b1 | 1 stacking | sound | failed 0/3 [0.9091, 0.9091, 0.4545] | 0/1 so far, needs 3 [0.9091] | one model 0/3, other open | 4 trusted / 0 untrusted / 0 pending | - |  |
| stk-convoy-18562 | scale-b1 | 1 stacking | checks or re-gate pending | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-oras-go-ghsam37j | scale-b1 | 1 stacking | sound | SOLVED 1/1 (1 solves counted, not audited) | 0/1 so far, needs 3 [0] | not a breaker (one solved; other open) | 1 trusted / 0 untrusted / 0 pending | - |  |
| stk-browsershot-ghsac9f5 | scale-b1 | 1 stacking | sound | SOLVED 1/1 (1 solves counted, not audited) | SOLVED 1/1 (1 solves counted, not audited) | solved by both | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-git-js-ghsa9p95 | scale-b1 | 1 stacking | sound | SOLVED 1/2 (+1 awaiting audit) (1 solves counted, not audited) (+2 NEEDS REVIEW) | SOLVED 1/1 (1 solves counted, not audited) | solved by both | 1 trusted / 0 untrusted / 3 pending | - |  |
| stk-dompurify-ghsap98j | scale-b1 | 1 stacking | sound | SOLVED 1/1 (1 solves counted, not audited) | SOLVED 1/1 (1 solves counted, not audited) | solved by both | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-dbhub-12733 | scale-b1 | 1 stacking | checks or re-gate pending | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-cms-ghsa7jx7 | scale-b1 | 1 stacking | sound | SOLVED 3/3 (3 solves counted, not audited) | SOLVED 2/2 (2 solves counted, not audited) | solved by both | 0 trusted / 0 untrusted / 0 pending | - | tests removed (removed-tests-20261026) |
| stk-i18next-http-backend-ghsaxvq9 | scale-b1 | 1 stacking | checks or re-gate pending | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-git-js-14793 | scale-b1 | 1 stacking | gate error | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-budibase-12672 | scale-b1 | 1 stacking | checks or re-gate pending | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-passenger-ghsaqw8w | scale-b1 | 1 stacking | sound | failed 0/3 [0.8333, 0.8333, 0.8333] | failed 0/3 [0.6667, 0.8333, 0.8333] | BOTH-MODEL BREAKER | 6 trusted / 0 untrusted / 0 pending | - |  |
| stk-go-git-18880 | scale-b1 | 1 stacking | sound | no graded run (+1 awaiting audit) | not run | trialling | 0 trusted / 0 untrusted / 1 pending | - |  |
| stk-flask-reuploaded-ghsa937x | scale-b1 | 1 stacking | gate error | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-tonapi-439 | scale-b1 | 1 stacking | gate error | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-ansible-ghsa6fq2 | scale-b1 | 1 stacking | sound | SOLVED 1/1 (1 solves counted, not audited) | SOLVED 1/1 (1 solves counted, not audited) | solved by both | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-mailpit-ghsa8r62 | scale-b1 | 1 stacking | checks or re-gate pending | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-payara-29001 | scale-b1 | 1 stacking | sound | failed 0/3 [0.625, 0.375, 0.375] | 0/1 so far, needs 3 [0.375] (+2 NEEDS REVIEW) | one model 0/3, other open | 4 trusted / 0 untrusted / 2 pending | - |  |
| stk-yt-dlp-ghsac6mh | scale-b1 | 1 stacking | checks or re-gate pending | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-skipper-15921 | scale-b1 | 1 stacking | gate error | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-glance-ghsavwr9 | scale-b1 | 1 stacking | checks or re-gate pending | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-git-js-ghsahffm | scale-b1 | 1 stacking | gate error | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-locutus-ghsavc8f | scale-b1 | 1 stacking | checks or re-gate pending | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-matrix-appservice-irc-ghsaw9mh | scale-b1 | 1 stacking | checks or re-gate pending | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-ansible-ghsa66c7 | scale-b1 | 1 stacking | checks or re-gate pending | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-tomcat-ghsa69r9 | scale-b1 | 1 stacking | checks or re-gate pending | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-koel-ghsa6qvr | scale-b1 | 1 stacking | checks or re-gate pending | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-virtualenv-2350 | scale-b1 | 1 stacking | checks or re-gate pending | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-djust-6530 | scale-b1 | 1 stacking | checks or re-gate pending | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-liferay-portal-ghsa3qq5 | scale-b1 | 1 stacking | gate error | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-copyparty-6317 | scale-b1 | 1 stacking | checks or re-gate pending | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-blender-mcp-787 | scale-b1 | 1 stacking | checks or re-gate pending | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-spring-ldap-26731 | scale-b1 | 1 stacking | unsound | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-ultrajson-480 | scale-b1 | 1 stacking | checks or re-gate pending | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-antisamy-ghsavp37 | scale-b1 | 1 stacking | checks or re-gate pending | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-ip-address-ghsa2vr4 | scale-b1 | 1 stacking | checks or re-gate pending | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-aqua-18379 | scale-b1 | 1 stacking | sound | SOLVED 1/1 (+1 awaiting audit) (1 solves counted, not audited) | SOLVED 1/1 (+2 awaiting audit) (1 solves counted, not audited) | solved by both | 0 trusted / 0 untrusted / 3 pending | - |  |
| stk-kirby-32469 | scale-b1 | 1 stacking | checks or re-gate pending | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-tomcat-ghsa8mc5 | scale-b1 | 1 stacking | checks or re-gate pending | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-cms-ghsaqx2q | scale-b1 | 1 stacking | checks or re-gate pending | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-rancher-15705 | scale-b1 | 1 stacking | checks or re-gate pending | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-katex-7340 | scale-b1 | 1 stacking | gate error | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-nanoid-7632 | scale-b1 | 1 stacking | checks or re-gate pending | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-moby-ghsax744 | scale-b1 | 1 stacking | checks or re-gate pending | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-mdc-12748 | scale-b1 | 1 stacking | checks or re-gate pending | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-tiptap-php-31762 | scale-b1 | 1 stacking | checks or re-gate pending | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-yt-dlp-2714 | scale-b1 | 1 stacking | checks or re-gate pending | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-github-branch-source-plu-25812 | scale-b1 | 1 stacking | checks or re-gate pending | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-cms-ghsafvwq | scale-b1 | 1 stacking | checks or re-gate pending | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-postcss-ghsafxqj | scale-b1 | 1 stacking | checks or re-gate pending | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-commonmark-ghsajjv6 | scale-b1 | 1 stacking | checks or re-gate pending | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-cognee-723 | scale-b1 | 1 stacking | checks or re-gate pending | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-social-core-5847 | scale-b1 | dry run | sound | SOLVED 1/3 (1 solves counted, not audited) | SOLVED 1/3 (1 solves counted, not audited) | solved by both | 4 trusted / 0 untrusted / 0 pending | - | tests removed (removed-tests-20261026) |
| fastify-s2 | scale-b1 | dry run | sound | failed 0/3 [0.7857, 0.7857, 0.8571] | failed 0/3 [0.7857, 0.7857, 0.7857] | BOTH-MODEL BREAKER | 6 trusted / 0 untrusted / 0 pending | READY (human decision KEEP 2026-10-26; review said READY ) |  |
| nuxt-s2 | scale-b1 | dry run | sound | SOLVED 1/1 (1 solves counted, not audited) | SOLVED 1/1 (1 solves counted, not audited) (+1 NEEDS REVIEW) | solved by both | 0 trusted / 0 untrusted / 1 pending | - |  |
| nuclei-s3 | scale-b1 | dry run | sound | SOLVED 1/1 (1 solves counted, not audited) | SOLVED 1/1 (+1 awaiting audit) (1 solves counted, not audited) | solved by both | 0 trusted / 0 untrusted / 1 pending | - |  |
| stk-bbot-ghsa3vgw | scale-b2 | 1 stacking | building | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-mongoose-ghsavg7j | scale-b2 | 1 stacking | building | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-spring-framework-ghsa4gc7 | scale-b2 | 1 stacking | building | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-kafka-python-4355 | scale-b2 | 1 stacking | checks or re-gate pending | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-bifrost-19592 | scale-b2 | 1 stacking | building | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-privatebin-ghsaf2xf | scale-b2 | 1 stacking | building | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-n8n-node-sqlite3-13223 | scale-b2 | 1 stacking | listing hold | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-bmoor-ghsa4m8h | scale-b2 | 1 stacking | building | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-dssrf-js-10670 | scale-b2 | 1 stacking | queued | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-mcp-118 | scale-b2 | 1 stacking | building | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-fast-xml-parser-ghsa8gc5 | scale-b2 | 1 stacking | checks or re-gate pending | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-camel-ghsajg2m | scale-b2 | 1 stacking | building | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-mcp-for-stata-839 | scale-b2 | 1 stacking | building | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-go-base-18459 | scale-b2 | 1 stacking | declined by builder | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-pocket-id-15304 | scale-b2 | 1 stacking | building | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-hypequery-9256 | scale-b2 | 1 stacking | building | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-kiota-typescript-7845 | scale-b2 | 1 stacking | building | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-notebook-ghsarcx2 | scale-b2 | 1 stacking | checks or re-gate pending | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-urllib3-ghsagwvm | scale-b2 | 1 stacking | building | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-framework-ghsaxjvc | scale-b2 | 1 stacking | building | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-camaleon-cms-ghsajw5g | scale-b2 | 1 stacking | building | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-mout-ghsavvv8 | scale-b2 | 1 stacking | building | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-sublinear-time-solver-14848 | scale-b2 | 1 stacking | building | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-lucene-solr-ghsa45w3 | scale-b2 | 1 stacking | building | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-link-preview-js-ghsacpjf | scale-b2 | 1 stacking | building | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-adm-zip-ghsarcw4 | scale-b2 | 1 stacking | checks or re-gate pending | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-spring-framework-ghsa8cmm | scale-b2 | 1 stacking | building | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-camel-ghsav7h8 | scale-b2 | 1 stacking | building | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-phpspreadsheet-31240 | scale-b2 | 1 stacking | building | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-serialize-javascript-ghsa5c6j | scale-b2 | 1 stacking | building | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-vault-secrets-webhook-19004 | scale-b2 | 1 stacking | building | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-pillow-ghsa57h3 | scale-b2 | 1 stacking | building | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-wire-ghsa9rm7 | scale-b2 | 1 stacking | declined by builder | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-org-hl7-fhir-core-25984 | scale-b2 | 1 stacking | building | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-nogginlessdom-7688 | scale-b2 | 1 stacking | checks or re-gate pending | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-mantisbt-ghsa3qv7 | scale-b2 | 1 stacking | building | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-jwcrypto-ghsafjrm | scale-b2 | 1 stacking | checks or re-gate pending | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-set-in-ghsa6956 | scale-b2 | 1 stacking | declined by builder | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| stk-fast-xml-parser-ghsam7jm | scale-b2 | 1 stacking | building | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| defuddle-s2 | scale-b2 | 2 sibling | building | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| handlebars.js-s2 | scale-b2 | 2 sibling | building | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| h2-s2 | scale-b2 | 2 sibling | checks or re-gate pending | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| semaphore-s2 | scale-b2 | 2 sibling | checks or re-gate pending | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| authelia-s2 | scale-b2 | 2 sibling | building | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| bifrost-s2 | scale-b2 | 2 sibling | queued | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| view-component-s2 | scale-b2 | 2 sibling | queued | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| oauth-s2 | scale-b2 | 2 sibling | queued | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| openlist-s2 | scale-b2 | 2 sibling | queued | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| skillctl-s2 | scale-b2 | 2 sibling | queued | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| psr7-s2 | scale-b2 | 2 sibling | queued | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| note-mark-s2 | scale-b2 | 2 sibling | queued | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| reactpress-s2 | scale-b2 | 2 sibling | queued | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| mantisbt-s2 | scale-b2 | 2 sibling | queued | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| easyappointments-s2 | scale-b2 | 2 sibling | queued | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| ip-address-s2 | scale-b2 | 2 sibling | queued | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| jsonata-s2 | scale-b2 | 2 sibling | queued | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| n8n-mcp-s2 | scale-b2 | 2 sibling | queued | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| grav-plugin-login-s2 | scale-b2 | 2 sibling | queued | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| open-webui-s2 | scale-b2 | 2 sibling | queued | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
| bbot-s2 | scale-b2 | 2 sibling | queued | - | - | - | 0 trusted / 0 untrusted / 0 pending | - |  |
