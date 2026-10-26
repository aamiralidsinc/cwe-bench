_Generated 2026-10-26 12:53 from 621 raw trials by common/audit/audit_results.py_

## Tasks where one model failed (the other solved)

| Track | Task | DeepSeek | MiMo | Who failed |
|---|---|---|---|---|
| mined | electron-builder-credential-leakage | SOLVED 1/1 | **failed 0/3** [0.8, 0.9, 0.8] | MiMo |
| stacking | stk-avideo-ghsawc3f | SOLVED 1/1 | **failed 0/3** [0.875, 0.875, 0.875] (+1 ungraded) | MiMo |
| stacking | stk-elfinder-ghsa44p8 | **failed 0/3** [0, 0, 0.9] | SOLVED 1/1 | DeepSeek |
| stacking | stk-fabio-ghsafq95 | **failed 0/3** [0.6364, 0.6364, 0.6364] | SOLVED 1/1 | DeepSeek |
| stacking | stk-kyverno-ghsacvq5 | SOLVED 1/1 | **failed 0/3** [0, 0.9091, 0] | MiMo |
| stacking | stk-langflow-794 | **failed 0/3** [0.8889, 0.8889, 0.8889] | SOLVED 1/1 | DeepSeek |
| stacking | stk-mlflow-3745 | SOLVED 1/3 | **failed 0/3** [0.7778, 0, 0] | MiMo |
| stacking | stk-mlflow-3745-control | **failed 0/3** [0, 0, 0] | SOLVED 1/2 | DeepSeek |
| stacking | stk-tensorflow-ghsajjr8-control | **failed 0/3** [0, 0, 0] | SOLVED 1/1 | DeepSeek |
| stacking | stk-uri-js-ghsagcv8 | SOLVED 1/2 | **failed 0/3** [0.8, 0.5667, 0.9] | MiMo |
| injection | airflow-ds | **failed 0/3** [0, 0, 0.825] | SOLVED 1/2 | DeepSeek |
| injection | airflow-info-exposure-inj | SOLVED 1/1 | **failed 0/3** [0.1304, 0.8261, 0] | MiMo |
| injection | backstage-ds | **failed 0/3** [0, 0.6604, 0] | SOLVED 1/1 | DeepSeek |
| injection | django-cms-ds | **failed 0/3** [0.95, 0.9, 0.95] | SOLVED 1/1 | DeepSeek |
| injection | flyto-core-ds | **failed 0/3** [0.9231, 0, 0.9487] | SOLVED 1/2 | DeepSeek |
| injection | keras-ds | **failed 0/3** [0.9048, 0.8095, 0.8095] | SOLVED 1/2 (+1 audit: untrusted) | DeepSeek |
| injection | knowns-ds | **failed 0/3** [0.8929, 0.8571, 0.8571] | SOLVED 1/4 (1 solves counted, not audited) | DeepSeek |
| injection | orval-ds | SOLVED 1/1 | **failed 0/3** [0.84, 0.8, 0.6] | MiMo |
| injection | pimcore-ds | SOLVED 1/2 | **failed 0/3** [0, 0, 0.9583] | MiMo |
| injection | prompty-ds | SOLVED 1/1 | **failed 0/3** [0.7857, 0.6071, 0.7857] | MiMo |
| injection | typo3-ds | **failed 0/3** [0.7273, 0.7273, 0.7273] | SOLVED 1/1 | DeepSeek |
| precision-validation | pv-spring-ws | **failed 0/3** [0.8, 0.8, 0.6] | SOLVED 1/4 (1 solves counted, not audited) | DeepSeek |

## All tasks

| Track | Task | DeepSeek | MiMo | Verdict |
|---|---|---|---|---|
| mined | astro-csrf-origin | SOLVED 1/1 (+1 solved using the internet) | SOLVED 1/1 (+1 solved using the internet) | rejected (both solved) |
| mined | compliance-trestle-path-traversal | SOLVED 2/2 | SOLVED 2/2 | rejected (both solved) |
| mined | django-cms-object-level | SOLVED 2/2 | SOLVED 2/2 | rejected (both solved) |
| mined | docling-file-disclosure | no graded run (+1 solved using the internet) | no graded run (+1 solved using the internet) | open |
| mined | electron-builder-credential-leakage | SOLVED 1/1 | **failed 0/3** [0.8, 0.9, 0.8] | rejected (DeepSeek solved) |
| mined | fission-podspec-passthrough | SOLVED 2/2 | SOLVED 2/2 | rejected (both solved) |
| mined | flyto-core-path-traversal | 0/2 so far, needs 3 [0, 0.96] (+2 audit: untrusted) (+1 solved using the internet) | 0/1 so far, needs 3 [0.96] (+2 solved using the internet) | open |
| mined | nhost-cors-auth | no graded run (+1 solved using the internet) | SOLVED 1/1 | rejected (MiMo solved) |
| mined | seaweedfs-s3tables-authz | SOLVED 1/1 | SOLVED 1/1 | rejected (both solved) |
| mined | traefik-header-name | SOLVED 1/1 (+1 solved using the internet) | SOLVED 1/1 (+1 audit: untrusted) | rejected (both solved) |
| mined | vibe-trading-path-read | SOLVED 1/2 | SOLVED 1/1 | rejected (both solved) |
| mined | whistle-cwe-path | SOLVED 2/2 | SOLVED 2/2 | rejected (both solved) |
| stacking | stk-ansible-ghsa6fq2 | SOLVED 1/1 (1 solves counted, not audited) | not run | rejected (DeepSeek solved) |
| stacking | stk-ansible-ghsavp9j | no graded run (+2 awaiting audit) | not run | open |
| stacking | stk-aqua-18379 | SOLVED 1/1 (+1 awaiting audit) (1 solves counted, not audited) | SOLVED 1/1 (+2 awaiting audit) (1 solves counted, not audited) | rejected (both solved) |
| stacking | stk-avideo-ghsaghcv | SOLVED 1/2 | SOLVED 1/1 | rejected (both solved) |
| stacking | stk-avideo-ghsaghcv-control | SOLVED 1/1 | SOLVED 1/1 | rejected (both solved) |
| stacking | stk-avideo-ghsawc3f | SOLVED 1/1 | **failed 0/3** [0.875, 0.875, 0.875] (+1 ungraded) | rejected (DeepSeek solved) |
| stacking | stk-avideo-ghsawc3f-control | SOLVED 1/1 | SOLVED 1/1 | rejected (both solved) |
| stacking | stk-cms-ghsa7jx7 | no graded run (+2 awaiting audit) | not run | open |
| stacking | stk-cms-ghsagp2f | **failed 0/3** [0, 0, 0] | 0/2 so far, needs 3 [0, 0.625] (+1 audit: untrusted) | open |
| stacking | stk-comfyui-manager-2366 | SOLVED 1/1 | 0/2 so far, needs 3 [0.9, 0.9] (+1 timed out, re-run at 3 h) | rejected (DeepSeek solved) |
| stacking | stk-comfyui-manager-2366-control | SOLVED 1/1 | SOLVED 1/1 (+1 provider stop) | rejected (both solved) |
| stacking | stk-dagu-ghsaph8x | **failed 0/3** [0.8, 0.8, 0.8] | **failed 0/3** [0.8, 0.8, 0.8] | **BREAKER candidate** |
| stacking | stk-dottie-js-ghsar5mx | SOLVED 1/1 | SOLVED 1/1 | rejected (both solved) |
| stacking | stk-dottie-js-ghsar5mx-control | SOLVED 1/1 | SOLVED 1/1 | rejected (both solved) |
| stacking | stk-elfinder-ghsa44p8 | **failed 0/3** [0, 0, 0.9] | SOLVED 1/1 | rejected (MiMo solved) |
| stacking | stk-elfinder-ghsa44p8-control | SOLVED 1/4 | SOLVED 2/2 | rejected (both solved) |
| stacking | stk-fabio-ghsafq95 | **failed 0/3** [0.6364, 0.6364, 0.6364] | SOLVED 1/1 | rejected (MiMo solved) |
| stacking | stk-fabio-ghsafq95-control | SOLVED 1/1 | SOLVED 1/1 | rejected (both solved) |
| stacking | stk-filebrowser-ghsa8wc8 | **failed 0/3** [0.8571, 0.7143, 0.8571] | **failed 0/3** [0.8571, 0.8571, 0.8571] | **BREAKER candidate** |
| stacking | stk-filebrowser-ghsa8wc8-control | SOLVED 1/2 | SOLVED 1/1 | rejected (both solved) |
| stacking | stk-froxlor-ghsa75h4 | no graded run (+2 awaiting audit) | no graded run (+1 awaiting audit) | open |
| stacking | stk-gitea-ghsaq9pg | SOLVED 1/1 | SOLVED 1/1 | rejected (both solved) |
| stacking | stk-gitea-ghsaq9pg-control | SOLVED 1/1 | SOLVED 1/1 | rejected (both solved) |
| stacking | stk-gitpython-ghsawvpp | **failed 0/3** [0.875, 0.875, 0.875] | **failed 0/3** [0.375, 0.625, 0.375] | **BREAKER candidate** |
| stacking | stk-gonic-15195 | SOLVED 1/1 (1 solves counted, not audited) | SOLVED 1/1 (1 solves counted, not audited) | rejected (both solved) |
| stacking | stk-jenkins-ghsa7fpg | SOLVED 1/1 | SOLVED 1/2 | rejected (both solved) |
| stacking | stk-jenkins-ghsa7fpg-control | SOLVED 1/1 | SOLVED 1/1 | rejected (both solved) |
| stacking | stk-jsonpath-ghsahw8r | SOLVED 1/1 | SOLVED 1/1 | rejected (both solved) |
| stacking | stk-jsonpath-ghsahw8r-control | SOLVED 1/1 | SOLVED 1/1 | rejected (both solved) |
| stacking | stk-kyverno-ghsacvq5 | SOLVED 1/1 | **failed 0/3** [0, 0.9091, 0] | rejected (DeepSeek solved) |
| stacking | stk-kyverno-ghsacvq5-control | SOLVED 1/1 | SOLVED 1/2 | rejected (both solved) |
| stacking | stk-langflow-794 | **failed 0/3** [0.8889, 0.8889, 0.8889] | SOLVED 1/1 | rejected (MiMo solved) |
| stacking | stk-langflow-794-control | SOLVED 1/1 | SOLVED 1/4 | rejected (both solved) |
| stacking | stk-lemur-5644 | **failed 0/3** [0, 0, 0] | **failed 0/3** [0, 0, 0] | **BREAKER candidate** |
| stacking | stk-lobe-chat-ghsa3fc8 | SOLVED 1/1 (+1 ungraded) | SOLVED 1/1 | rejected (both solved) |
| stacking | stk-lobe-chat-ghsa3fc8-control | SOLVED 1/1 | SOLVED 1/1 | rejected (both solved) |
| stacking | stk-mistral-rs-21576 | **failed 0/3** [0, 0, 0] | **failed 0/3** [0, 0, 0] | **BREAKER candidate** |
| stacking | stk-mjml-ghsa45h5 | SOLVED 1/1 | SOLVED 1/1 | rejected (both solved) |
| stacking | stk-mjml-ghsa45h5-control | SOLVED 1/1 | SOLVED 1/1 | rejected (both solved) |
| stacking | stk-mlflow-3745 | SOLVED 1/3 | **failed 0/3** [0.7778, 0, 0] | rejected (DeepSeek solved) |
| stacking | stk-mlflow-3745-control | **failed 0/3** [0, 0, 0] | SOLVED 1/2 | rejected (MiMo solved) |
| stacking | stk-nova-ghsaxc4g | SOLVED 1/1 | SOLVED 1/1 | rejected (both solved) |
| stacking | stk-nuclei-ghsajpvm | SOLVED 1/1 | SOLVED 1/2 | rejected (both solved) |
| stacking | stk-nuclei-ghsajpvm-control | SOLVED 2/2 | SOLVED 1/1 | rejected (both solved) |
| stacking | stk-openbao-ghsac36x | SOLVED 1/1 | SOLVED 1/1 | rejected (both solved) |
| stacking | stk-openbao-ghsac36x-control | SOLVED 1/1 | no graded run (+1 audit: untrusted) | rejected (DeepSeek solved) |
| stacking | stk-openremote-29156 | SOLVED 1/2 | SOLVED 1/1 | rejected (both solved) |
| stacking | stk-openremote-29156-control | SOLVED 2/2 | SOLVED 2/2 | rejected (both solved) |
| stacking | stk-passenger-ghsaqw8w | no graded run (+1 awaiting audit) | not run | open |
| stacking | stk-payara-29001 | **failed 0/3** [0.625, 0.375, 0.375] | 0/1 so far, needs 3 [0.375] (+2 NEEDS REVIEW) | open |
| stacking | stk-pyload-ghsa4744 | SOLVED 1/1 | SOLVED 1/1 | rejected (both solved) |
| stacking | stk-pyload-ghsa4744-control | SOLVED 1/1 | SOLVED 2/2 (+1 audit: untrusted) | rejected (both solved) |
| stacking | stk-pyload-ghsa7gvf | SOLVED 1/1 | SOLVED 1/1 | rejected (both solved) |
| stacking | stk-pyload-ghsa7gvf-control | SOLVED 1/1 | SOLVED 1/1 | rejected (both solved) |
| stacking | stk-senaite-core-4280 | **failed 0/3** [0.8182, 0.8182, 0.8182] | **failed 0/3** [0.8182, 0.8182, 0.8182] (+1 ungraded) (+1 audit: untrusted) | **BREAKER candidate** |
| stacking | stk-senaite-core-4280-control | SOLVED 1/1 | SOLVED 1/1 | rejected (both solved) |
| stacking | stk-siyuan-ghsa4mx9 | SOLVED 1/1 | SOLVED 1/2 | rejected (both solved) |
| stacking | stk-siyuan-ghsa4mx9-control | SOLVED 1/1 | SOLVED 1/1 | rejected (both solved) |
| stacking | stk-social-core-5847 | SOLVED 1/3 (1 solves counted, not audited) | SOLVED 1/3 (1 solves counted, not audited) | rejected (both solved) |
| stacking | stk-spark-2338 | SOLVED 1/1 (1 solves counted, not audited) | SOLVED 1/1 (1 solves counted, not audited) | rejected (both solved) |
| stacking | stk-tensorflow-ghsajjr8 | **failed 0/3** [0, 0, 0] | **failed 0/5** [0, 0, 0.8, 0.8, 0.8] (+1 ungraded) (+1 timed out, re-run at 3 h) | **BREAKER candidate** |
| stacking | stk-tensorflow-ghsajjr8-control | **failed 0/3** [0, 0, 0] | SOLVED 1/1 | rejected (MiMo solved) |
| stacking | stk-uri-js-ghsagcv8 | SOLVED 1/2 | **failed 0/3** [0.8, 0.5667, 0.9] | rejected (DeepSeek solved) |
| stacking | stk-uri-js-ghsagcv8-control | SOLVED 1/1 | SOLVED 1/1 | rejected (both solved) |
| stacking | stk-vikunja-ghsaxv7q | **failed 0/3** [0.8333, 0.8333, 0] | **failed 0/3** [0.8333, 0, 0.8333] | **BREAKER candidate** |
| injection | airflow-ds | **failed 0/3** [0, 0, 0.825] | SOLVED 1/2 | rejected (MiMo solved) |
| injection | airflow-info-exposure-inj | SOLVED 1/1 | **failed 0/3** [0.1304, 0.8261, 0] | rejected (DeepSeek solved) |
| injection | arc-ds | SOLVED 1/2 | SOLVED 1/1 | rejected (both solved) |
| injection | astro-ds | SOLVED 1/1 | SOLVED 1/1 | rejected (both solved) |
| injection | backstage-ds | **failed 0/3** [0, 0.6604, 0] | SOLVED 1/1 | rejected (MiMo solved) |
| injection | ckan-mcp-server-ds | SOLVED 1/1 (+2 audit: untrusted) | SOLVED 1/1 | rejected (both solved) |
| injection | compliance-trestle-ds | SOLVED 1/1 | SOLVED 1/1 | rejected (both solved) |
| injection | composer-symlink-path-inj | SOLVED 2/2 (+1 solved using the internet) | SOLVED 3/3 | rejected (both solved) |
| injection | coreutils-ds | SOLVED 1/1 | SOLVED 1/1 | rejected (both solved) |
| injection | django-cms-ds | **failed 0/3** [0.95, 0.9, 0.95] | SOLVED 1/1 | rejected (MiMo solved) |
| injection | ec2-fleet-plugin-ds | no graded run (+2 solved using the internet) | not run | open |
| injection | electron-builder-ds | **failed 0/3** [0.7222, 0.6111, 0.7222] | **failed 0/3** [0.6111, 0.6111, 0.6111] | **BREAKER candidate** |
| injection | fastify-s2 | **failed 0/3** [0.7857, 0.7857, 0.8571] | **failed 0/3** [0.7857, 0.7857, 0.7857] | **BREAKER candidate** |
| injection | fission-ds | SOLVED 1/1 | SOLVED 1/1 | rejected (both solved) |
| injection | flowise-cross-tenant-inj | SOLVED 1/1 (+1 NEEDS REVIEW) | no graded run (+1 timed out, re-run at 3 h) (+2 NEEDS REVIEW) | rejected (DeepSeek solved) |
| injection | flowise-ds | SOLVED 1/2 (+2 audit: untrusted) | no graded run (+3 NEEDS REVIEW) | rejected (DeepSeek solved) |
| injection | flyto-core-ds | **failed 0/3** [0.9231, 0, 0.9487] | SOLVED 1/2 | rejected (MiMo solved) |
| injection | ghost-ds | SOLVED 1/3 | SOLVED 1/3 | rejected (both solved) |
| injection | gogs-ds | SOLVED 1/1 | SOLVED 1/1 (+2 audit: untrusted) | rejected (both solved) |
| injection | grav-ds | **failed 0/3** [0, 0.8696, 0] | **failed 0/3** [0.6087, 0, 0.6957] | **BREAKER candidate** |
| injection | grav-info-exposure-inj | SOLVED 3/4 (+3 audit: untrusted) | SOLVED 3/3 (+3 audit: untrusted) (+1 solved using the internet) | rejected (both solved) |
| injection | hazelcast-ds | SOLVED 1/1 | 0/2 so far, needs 3 [0.8095, 0.9048] (+1 audit: untrusted) | rejected (DeepSeek solved) |
| injection | hermes-agent-ds | **failed 0/4** [0, 0.3929, 0, 0.4643] | no graded run (+3 audit: untrusted) | open |
| injection | hubuum-client-rust-ds | **failed 0/4** [0, 0, 0, 0] | **failed 0/3** [0, 0, 0] | **BREAKER candidate** |
| injection | jenkins-ec2fleet-authz-inj | no graded run (+3 audit: untrusted) (+3 solved using the internet) | no graded run (+3 audit: untrusted) (+3 solved using the internet) | open |
| injection | jetty.project-ds | **failed 0/3** [0.8889, 0.8889, 0.8889] | **failed 0/3** [0.8889, 0.8889, 0.8889] | **BREAKER candidate** |
| injection | keras-ds | **failed 0/3** [0.9048, 0.8095, 0.8095] | SOLVED 1/2 (+1 audit: untrusted) | rejected (MiMo solved) |
| injection | knowns-ds | **failed 0/3** [0.8929, 0.8571, 0.8571] | SOLVED 1/4 (1 solves counted, not audited) | rejected (MiMo solved) |
| injection | langchain-ds | SOLVED 1/1 | SOLVED 1/1 | rejected (both solved) |
| injection | langchain-path-escape-inj | SOLVED 1/1 | SOLVED 1/1 | rejected (both solved) |
| injection | limesurvey-ds | SOLVED 1/2 | SOLVED 1/1 | rejected (both solved) |
| injection | litellm-ds | **failed 0/3** [0, 0, 0] | **failed 0/3** [0, 0, 0] (+2 ungraded) | **BREAKER candidate** |
| injection | mcp-atlassian-path-inj | no graded run (+1 audit: untrusted) (+2 solved using the internet) | SOLVED 2/2 (+1 audit: untrusted) | rejected (MiMo solved) |
| injection | mockoon-ds | **failed 0/4** [0.9259, 0.9259, 0.963, 0.9259] | **failed 0/3** [0.9259, 0.9259, 0.963] | **BREAKER candidate** |
| injection | n8n-ds | SOLVED 1/1 | SOLVED 1/1 | rejected (both solved) |
| injection | new-api-ds | SOLVED 1/1 | SOLVED 1/1 | rejected (both solved) |
| injection | nuclei-s3 | SOLVED 1/1 (1 solves counted, not audited) | SOLVED 1/1 (+1 awaiting audit) (1 solves counted, not audited) | rejected (both solved) |
| injection | nuxt-s2 | SOLVED 1/1 (1 solves counted, not audited) | SOLVED 1/1 (1 solves counted, not audited) (+1 NEEDS REVIEW) | rejected (both solved) |
| injection | openbao-ds | **failed 0/3** [0, 0, 0] | **failed 0/3** [0, 0, 0] | **BREAKER candidate** |
| injection | orval-ds | SOLVED 1/1 | **failed 0/3** [0.84, 0.8, 0.6] | rejected (DeepSeek solved) |
| injection | pimcore-ds | SOLVED 1/2 | **failed 0/3** [0, 0, 0.9583] | rejected (DeepSeek solved) |
| injection | portainer-ds | no graded run (+3 audit: untrusted) | no graded run (+3 audit: untrusted) | open |
| injection | prompty-ds | SOLVED 1/1 | **failed 0/3** [0.7857, 0.6071, 0.7857] | rejected (DeepSeek solved) |
| injection | prompty-path-read-inj | SOLVED 1/1 (+1 audit: untrusted) | no graded run (+3 audit: untrusted) | rejected (DeepSeek solved) |
| injection | protobuf.js-ds | **failed 0/3** [0.9412, 0.9118, 0.9118] | **failed 0/3** [0.4706, 0.9118, 0.7941] | **BREAKER candidate** |
| injection | rsdoctor-ds | SOLVED 1/1 | SOLVED 1/1 | rejected (both solved) |
| injection | seaweedfs-ds | **failed 0/3** [0, 0, 0] | **failed 0/3** [0.9032, 0.871, 0] (+1 ungraded) | **BREAKER candidate** |
| injection | siyuan-ds | **failed 0/4** [0, 0, 0, 0] | **failed 0/3** [0, 0, 0] | **BREAKER candidate** |
| injection | summarize-ds | no graded run (+1 solved using the internet) | not run | open |
| injection | suneditor-xss-inj | SOLVED 1/1 (+2 solved using the internet) | SOLVED 1/1 (+1 solved using the internet) (+1 NEEDS REVIEW) | rejected (both solved) |
| injection | surrealdb-ds | no graded run (+3 audit: untrusted) (+1 NEEDS REVIEW) | no graded run (+3 audit: untrusted) | open |
| injection | theia-ds | **failed 0/3** [0, 0, 0] | **failed 0/3** [0, 0, 0] | **BREAKER candidate** |
| injection | tinacms-ds | **failed 0/3** [0, 0, 0] | **failed 0/3** [0.9726, 0, 0] | **BREAKER candidate** |
| injection | traefik-ds | 0/1 so far, needs 3 [0.9783] (+1 ungraded) (+3 solved using the internet) | not run | open |
| injection | trivy-ds | SOLVED 1/1 | not run | rejected (DeepSeek solved) |
| injection | trivy-path-traversal-inj | SOLVED 1/1 | SOLVED 1/1 | rejected (both solved) |
| injection | typo3-ds | **failed 0/3** [0.7273, 0.7273, 0.7273] | SOLVED 1/1 | rejected (MiMo solved) |
| injection | vibe-trading-ds | SOLVED 1/2 | SOLVED 1/1 | rejected (both solved) |
| injection | vitest-api-fs-authz-inj | no graded run (+6 audit: untrusted) | SOLVED 2/2 (+4 audit: untrusted) | rejected (MiMo solved) |
| injection | vitest-ds | SOLVED 1/2 | SOLVED 1/1 | rejected (both solved) |
| injection | whistle-ds | SOLVED 1/1 | SOLVED 1/1 | rejected (both solved) |
| injection | yamcs-ds | SOLVED 1/4 (1 solves counted, not audited) | SOLVED 1/4 (1 solves counted, not audited) | rejected (both solved) |
| precision-validation | pv-apostrophe | **failed 0/3** [0.7, 0.95, 0.95] | **failed 0/3** [0.75, 0.65, 0.7] | **BREAKER candidate** |
| precision-validation | pv-device-builder | **failed 0/3** [0, 0.6, 0.6] | **failed 0/3** [0.8, 0.6, 0.6] | **BREAKER candidate** |
| precision-validation | pv-nx | no graded run (+3 audit: untrusted) | no graded run (+2 audit: untrusted) (+1 grader fault) | open |
| precision-validation | pv-pacioli | **failed 0/3** [0.75, 0.75, 0.875] | **failed 0/3** [0.875, 0.75, 0.75] | **BREAKER candidate** |
| precision-validation | pv-quarkus | **failed 0/3** [0, 0.9091, 0.7273] | **failed 0/3** [0, 0, 0] | **BREAKER candidate** |
| precision-validation | pv-spring-ws | **failed 0/3** [0.8, 0.8, 0.6] | SOLVED 1/4 (1 solves counted, not audited) | rejected (MiMo solved) |
| precision-validation | pv-svgo | **failed 0/3** [0, 0, 0] | **failed 0/4** [0, 0, 0, 0] | **BREAKER candidate** |
