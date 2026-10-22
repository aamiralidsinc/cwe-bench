# Screened hosts: ranking and how to move forward

Generated 2026-10-17 01:45 UTC by `sourcer/rerank-v4-draft/screen_report.py`.
**Internal.** It counts uncovered routes in named projects that may not be publicly reported. Do not
share it outside the project until the client has decided on disclosure (NEXT-STEPS item 4).

## What this is
- 150 published, already-fixed advisories screened as task hosts by Opus 5.5 with
  `builder/SCREENER-PROMPT-v2.md` (the model the v2 calibration rule ranked third on fact precision,
  chosen by the user to keep GPT limits free). 149 records are valid and ranked below.
- Hosts came from the computed rerank in three batches of 50 (ranks 1-149, 64-309, 128-454; one
  advisory per repo; repos already built and the 37 calibration hosts left out).
- **Score** = `score_read` from `rerank.py --screened`: the screener's observations × draft weights
  `screen-w0` (not fitted) + the advisory's weakness terms. On the calibration hosts this score
  ranked hosts that beat a model above solved ones about 75% of the time (Opus, 90% interval
  0.58-0.90). Scores cluster: order within a score is not meaningful.
- Evidence checked by script against the pinned and current-upstream code: under 1% of file:line
  references are wrong in every batch.

Score distribution: 23: 11, 22: 3, 21: 22, 20: 15, 19: 14, 18: 11, 17: 12, 16: 9, 15: 9, 14: 13, 13: 5, 12: 5, 11: 5, 10: 2, 9: 1, 7: 2, 6: 4, 4: 1, 3: 1, 2: 2, 1: 1, -2: 1.

## The upstream ratio
An uncovered route (pattern B) is a route into the advisory's own protected sink that the
published fix left untouched. The screener also checked whether each route is still present in
current upstream code (default-branch HEAD, 2026-10-17).

| Hosts | All 149 | Score ≥ 21 (36) |
|---|---|---|
| No uncovered routes (pattern A only) | 53 (36%) | 0 (0%) |
| Routes, all fixed upstream since | 20 (13%) | 6 (17%) |
| At least one route still upstream | 69 (46%) | 27 (75%) |
| Presence unknown or mixed | 7 (5%) | 3 (8%) |

Routes claimed: 247 (still upstream 138, fixed 92, unknown
17). These are the screener's leads, not confirmed: in the blind fact check, 4 of 6
Opus route claims held on hosts that beat a model, 1 of 3 on solved hosts. A builder confirms each
route with a test before it counts.

Pattern fit: A+B 49, A 61, B 19, injection only 13, none 7.

**The score favours pattern B.** Uncovered routes earn up to +6 in `screen-w0`, so no host without
routes reaches 21. For a policy that builds pattern A only on some hosts (P1, P3), pick those
hosts by the **A-only score** column (the same score without the route points), not by Score.

## How to move forward
### 1. Choose a policy for routes still upstream
| Policy | What gets built | Shareable now | Cost |
|---|---|---|---|
| **P1, pattern A only** | Every host on the published fix's own sites | All | Drops pattern B, the strongest single lever so far (DeepSeek 0/6 on jackson-sib; both models 0/3 on sib2) |
| **P2, A+B everywhere** | Every host with its routes | Hosts with no route still upstream | 27 of the 36 top hosts are held until the client decides |
| **P3, mixed** | A+B where routes are fixed upstream or absent; A only where a route is still upstream; upgrade to A+B after the client decides | All | Weaker tasks on the held hosts until then |

Recommendation: **P3 now, and put the disclosure question to the client at once** (it is already
NEXT-STEPS item 4). The ratio above is what the client needs to see: most strong hosts carry
routes still present upstream, so the client's decision decides how many tasks can use pattern B.
Whatever the policy, every route a task uses gets a row in `build/audit/uncovered-routes.tsv`.

### 2. Choose the build machine
Building and trials need Docker and Harbor. Options: install both on the client VM (32 CPU, trials
in parallel; needs your approval) or use the Mac's shared Docker VM (8 CPU, one build at a time).

### 3. First build batch
Pick 6-8 hosts from the top of the table under the chosen policy: fix estimate 60 minutes or less,
no DoS flag, offline build, and a mix of languages. Each goes through the pipeline in
`builder/NEXT-STEPS.md`: build (`builder/TASK-BUILD-PROMPT-v1.md`), blind fix, fairness review,
strict gate, trials on DeepSeek and MiMo (up to 3 runs each, offline, 2 h), and an audit of every
graded run. Builder and auditor runs use Opus, so keep watching the weekly usage.

### 4. Learn from the outcomes
After the batch's trials, add the outcomes to the calibration set, refit `screen-weights.json`
(screen-w1), and re-rank. The ranking below is only as good as the unfitted weights.

## Ranking (149 hosts)
Routes = uncovered routes still upstream / fixed upstream / unknown. Fix = the screener's estimate
for a careful engineer who knows where to look. Recall = how widely the advisory is written up.

| # | Score | A-only score | Repo | Advisory | Language | CVE | Pattern | Entry points | Out-of-scope site | Routes | Fix | Red flags | Recall | DoS |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 23 | 17 | flytohub/flyto-core | GHSA-2956-977x-2w3r | Python (>=3.9) | CVE-2026-67429 | A+B | 13 | save reload or serialization | 0/10/0 | 60m | - | low | - |
| 2 | 23 | 17 | apache/airflow | GHSA-c56v-8w4g-3mfm | Python | CVE-2026-65017 | A+B | 4 | lower level api | 3/0/0 | 50m | - | low | - |
| 3 | 23 | 17 | oscal-compass/compliance-trestle | GHSA-r4vp-3vw6-r2x5 | Python (>=3.10) | CVE-2026-57171 | A+B | 9 | lower level api | 9/0/0 | 50m | - | medium | - |
| 4 | 23 | 17 | knowns-dev/knowns | GHSA-9gfj-28hw-jchp | Go | CVE-2026-86439 | A | 10 | save reload or serialization | 1/0/1 | 60m | - | low | - |
| 5 | 23 | 17 | electron-userland/electron-builder | GHSA-p2f4-r6v6-j797 | TypeScript | CVE-2026-54673 | A+B | 4 | wrapper or composition | 2/0/1 | 45m | - | low | - |
| 6 | 23 | 17 | nrwl/nx | GHSA-vp3h-ghgh-jr7g | Rust (napi-rs nati | CVE-2026-71476 | A+B | 4 | lower level api | 2/0/0 | 60m | - | medium | - |
| 7 | 23 | 17 | fission/fission | GHSA-gx55-f84r-v3r7 | Go | CVE-2026-50564 | A+B | 4 | defaults or merge route | 0/2/0 | 45m | - | medium | - |
| 8 | 23 | 17 | traefik/traefik | GHSA-x677-9fxg-v5c5 | Go | CVE-2026-54763 | B | 3 | wrapper or composition | 4/0/0 | 45m | - | medium | - |
| 9 | 23 | 17 | jenkinsci/ec2-fleet-plugin | GHSA-2x9c-vp3g-hvv2 | Java | CVE-2026-57295 | A | 5 | second implementation | 2/0/0 | 60m | - | medium | - |
| 10 | 23 | 17 | izpack/izpack | GHSA-f63g-88cj-hjf9 | Java (release 8) | CVE-2026-54550 | A+B | 3 | lower level api | 2/0/0 | 40m | - | low | - |
| 11 | 23 | 17 | limesurvey/limesurvey | GHSA-5c37-5j7w-8mh8 | PHP | CVE-2026-50635 | A | 4 | second implementation | 4/0/0 | 45m | - | medium | - |
| 12 | 22 | 16 | nousresearch/hermes-agent | GHSA-33qv-c5qm-799v | Python (>=3.11) | CVE-2026-10223 | A+B | 5 | save reload or serialization | 3/0/2 | 60m | - | medium | - |
| 13 | 22 | 16 | seaweedfs/seaweedfs | GHSA-hgpf-8634-g44c | Go | CVE-2026-55873 | A+B | 2 | defaults or merge route | 1/1/0 | 50m | - | medium | - |
| 14 | 22 | 16 | jetty/jetty.project | GHSA-2fvj-hgj9-j2gr | Java | CVE-2026-10050 | A+B | 3 | second implementation | 2/0/0 | 50m | - | medium | - |
| 15 | 21 | 15 | langflow-ai/langflow | GHSA-4hmc-cfm3-w43c | Python (backend) w | CVE-2026-105699 | A+B | 5 | second implementation | 1/1/0 | 50m | - | medium | - |
| 16 | 21 | 17 | hkuds/vibe-trading | GHSA-5rmq-chc7-m22f | Python (plus TypeS | - | A+B | 9 | second implementation | 1/0/0 | 40m | - | low | - |
| 17 | 21 | 15 | django-cms/django-cms | GHSA-6x92-6vx4-5fwr | Python | CVE-2026-63003 | A+B | 3 | wrapper or composition | 0/4/0 | 40m | - | medium | - |
| 18 | 21 | 15 | startreedata/mcp-pinot | GHSA-73cv-556c-w3g6 | Python 3.12 | CVE-2026-49257 | A | 4 | defaults or merge route | 2/0/0 | 35m | tiny repo | low | - |
| 19 | 21 | 15 | senaite/senaite.core | GHSA-jrw6-7x4q-w25j | Python 2.7 (interf | CVE-2026-54569 | B | 6 | wrapper or composition | 3/0/0 | 40m | - | medium | - |
| 20 | 21 | 15 | docling-project/docling | GHSA-p944-4xh2-x776 | Python (>=3.10) | CVE-2026-105748 | B | 3 | defaults or merge route | 2/0/0 | 40m | - | low | - |
| 21 | 21 | 15 | microsoft/prompty | GHSA-wxhm-2mq7-7697 | Python, TypeScript | CVE-2026-53598 | A+B | 9 | second implementation | 0/6/0 | 75m | - | medium | - |
| 22 | 21 | 17 | avwo/whistle | GHSA-3vfr-4gwf-qxfp | JavaScript (Node.j | CVE-2026-55629 | A+B | 3 | lower level api | 0/1/0 | 40m | - | low | - |
| 23 | 21 | 15 | pnpm/pnpm | GHSA-5wx6-mg75-v57r | TypeScript (Node.j | CVE-2026-55487 | A+B | 5 | second implementation | 0/0/2 | 150m | - | low | - |
| 24 | 21 | 15 | vitest-dev/vitest | GHSA-5xrq-8626-4rwp | TypeScript | CVE-2026-47429 | A+B | 12 | second implementation | 3/3/0 | 75m | - | medium | - |
| 25 | 21 | 17 | pionxzh/wakaru | GHSA-7wpj-vvmv-pgm8 | Rust | CVE-2026-54545 | A | 4 | second implementation | 1/0/0 | 45m | - | low | - |
| 26 | 21 | 17 | withastro/astro | GHSA-8mv7-9c27-98vc | TypeScript | CVE-2026-73423 | A | 4 | lower level api | 1/0/0 | 35m | - | low | - |
| 27 | 21 | 15 | flowiseai/flowise | GHSA-chm3-vqcf-52rx | TypeScript (Node ^ | CVE-2026-70472 | A+B | 8 | wrapper or composition | 1/4/0 | 50m | - | medium | - |
| 28 | 21 | 17 | nuxt/nuxt | GHSA-hxvh-4h3w-prp9 | TypeScript | CVE-2026-71315 | A | 3 | save reload or serialization | 0/0/1 | 45m | - | medium | - |
| 29 | 21 | 15 | web-infra-dev/rsdoctor | GHSA-jmg2-rcxh-w8q3 | TypeScript (Node.j | CVE-2026-61782 | A | 6 | lower level api | 1/1/0 | 75m | - | low | - |
| 30 | 21 | 17 | budibase/budibase | GHSA-mqhr-6j6h-74p5 | TypeScript (Node.j | CVE-2026-73407 | A+B | 5 | lower level api | 1/0/0 | 45m | - | low | - |
| 31 | 21 | 17 | quantumnous/new-api | GHSA-6x2c-phff-wx57 | Go | CVE-2026-64859 | B | 4 | lower level api | 1/0/0 | 30m | - | medium | - |
| 32 | 21 | 15 | basekick-labs/arc | GHSA-p2j4-c4g6-rpf5 | Go (cgo) | CVE-2026-47735 | A+B | 5 | lower level api | 0/3/1 | 75m | - | medium | - |
| 33 | 21 | 15 | yamcs/yamcs | GHSA-fwww-cp23-7f5g | Java | CVE-2026-55545 | B | 3 | lower level api | 2/2/0 | 35m | - | low | - |
| 34 | 21 | 17 | http4k/http4k | GHSA-pr33-38xx-6r26 | Kotlin (JVM) | CVE-2026-100725 | B | 3 | second implementation | 1/0/0 | 60m | - | medium | - |
| 35 | 21 | 15 | pimcore/pimcore | GHSA-9x44-4gxf-8c25 | PHP | CVE-2026-55634 | A+B | 5 | lower level api | 0/4/0 | 60m | - | low | - |
| 36 | 21 | 15 | getgrav/grav | GHSA-mc5q-6hpj-rp7j | PHP 8.3 | CVE-2026-61450, CVE-2026-61842 | A+B | 7 | defaults or merge route | 1/3/0 | 70m | - | medium | - |
| 37 | 20 | 14 | keras-team/keras | GHSA-26c4-7vv6-867j | Python | CVE-2026-12480 | A+B | 3 | legacy path | 0/2/0 | 40m | - | medium | - |
| 38 | 20 | 14 | mervinpraison/praisonai | GHSA-2gpf-2492-q9jh | Python | CVE-2026-61435 | B | 7 | - | 0/2/0 | 35m | - | medium | - |
| 39 | 20 | 16 | berriai/litellm | GHSA-3cv6-jpf6-8222 | Python | CVE-2026-84377 | A+B | 6 | second implementation | 1/0/0 | 60m | - | medium | - |
| 40 | 20 | 14 | comfy-org/comfyui-manager | GHSA-95pq-hr8p-f5g7 | Python (plus JS UI | CVE-2025-67303 | A+B | 3 | second implementation | 2/0/0 | 50m | - | medium | - |
| 41 | 20 | 14 | sync-in/server | GHSA-29hq-23m2-2j47 | TypeScript (NestJS | CVE-2026-58272 | A+B | 4 | second implementation | 0/2/0 | 45m | - | medium | - |
| 42 | 20 | 14 | eclipse-theia/theia | GHSA-3jww-hxqj-wfq2 | TypeScript | CVE-2026-44688 | A+B | 9 | defaults or merge route | 5/0/0 | 120m | - | medium | - |
| 43 | 20 | 16 | tryghost/ghost | GHSA-hqq2-xqr2-fmx2 | JavaScript / TypeS | CVE-2026-105644 | A | 7 | second implementation | 0/0/1 | 60m | - | medium | - |
| 44 | 20 | 16 | protobufjs/protobuf.js | GHSA-jfj6-75fj-8934 | JavaScript (Node.j | CVE-2026-59876 | A | 7 | lower level api | 1/0/0 | 50m | - | medium | - |
| 45 | 20 | 14 | nhost/nhost | GHSA-64cj-qvx5-m4f3 | Go (plus TypeScrip | CVE-2026-47671 | A | 2 | save reload or serialization | 2/0/0 | 60m | - | low | - |
| 46 | 20 | 14 | grpc/grpc-go | GHSA-hrxh-6v49-42gf | Go | - | A+B | 3 | lower level api | 0/3/0 | 60m | - | medium | yes |
| 47 | 20 | 14 | hubuum/hubuum-client-rust | GHSA-2625-rw7m-5q5x | Rust (edition 2024 | - | A+B | 12 | second implementation | 4/0/1 | 90m | - | low | - |
| 48 | 20 | 14 | hazelcast/hazelcast | GHSA-6v25-8wq6-xq4j | Java (17+; records | CVE-2026-107726 | A+B | 5 | second implementation | 1/4/0 | 75m | - | low | - |
| 49 | 20 | 16 | jknack/handlebars.java | GHSA-g29j-rwfv-h99w | Java 17 | CVE-2026-63490 | A | 5 | wrapper or composition | 1/0/0 | 35m | - | low | - |
| 50 | 20 | 14 | wintercms/winter | GHSA-8cfw-pcwh-v63w | PHP (>=8.1) | CVE-2026-79774 | A+B | 3 | wrapper or composition | 2/0/0 | 150m | - | medium | - |
| 51 | 20 | 14 | typo3/typo3 | GHSA-jh32-v29g-68pq | PHP 8.2+ | CVE-2026-49741 | A | 3 | lower level api | 2/0/1 | 60m | - | medium | - |
| 52 | 19 | 15 | koxudaxi/datamodel-code-generator | GHSA-5578-w22f-pfx9 | Python | CVE-2026-55415 | A+B | 2 | second implementation | 0/1/0 | 40m | - | medium | - |
| 53 | 19 | 15 | langchain-ai/langchain | GHSA-gr75-jv2w-4656 | Python (>=3.10) | CVE-2026-55443 | A | 4 | second implementation | 0/1/0 | 40m | - | medium | - |
| 54 | 19 | 15 | backstage/backstage | GHSA-29gx-h2m3-xw44 | TypeScript (Node.j | CVE-2026-106462 | A | 35 | second implementation | 1/0/0 | 90m | - | low | - |
| 55 | 19 | 15 | n8n-io/n8n | GHSA-2x35-3fw4-9jr4 | TypeScript | CVE-2026-72766 | A+B | 3 | legacy path | 0/1/0 | 40m | - | medium | - |
| 56 | 19 | 13 | axios/axios | GHSA-42h9-826w-cgv3 | JavaScript (ESM) | CVE-2026-67313 | A+B | 6 | second implementation | 2/1/0 | 40m | - | medium | yes |
| 57 | 19 | 13 | ondata/ckan-mcp-server | GHSA-798p-78g2-v556 | TypeScript (ESM, N | CVE-2026-61612 | A+B | 2 | second implementation | 0/3/1 | 60m | - | medium | - |
| 58 | 19 | 13 | that1drifter/browse-mcp | GHSA-m9mq-7m7q-xc6p | TypeScript (ESM) | CVE-2026-55557 | A+B | 4 | second implementation | 4/0/0 | 40m | tiny repo | low | - |
| 59 | 19 | 15 | mockoon/mockoon | GHSA-rqx4-3f6q-3x2v | TypeScript (Node.j | CVE-2026-59148 | A | 15 | second implementation | 1/0/0 | 90m | - | medium | - |
| 60 | 19 | 15 | openbao/openbao | GHSA-59w7-v8rr-pr4p | Go | CVE-2026-71543 | A | 5 | second implementation | 1/0/0 | 75m | - | medium | - |
| 61 | 19 | 13 | siyuan-note/siyuan | GHSA-fgmr-7w36-9qfq | Go (kernel); TypeS | CVE-2026-72796 | A+B | 6 | legacy path | 1/2/0 | 75m | - | medium | - |
| 62 | 19 | 13 | surrealdb/surrealdb | GHSA-66r2-5gwj-gxm2 | Rust | CVE-2026-63733 | A+B | 8 | second implementation | 8/0/0 | 80m | protection documented without exceptions | low | - |
| 63 | 19 | 13 | umanio-agency/skillctl | GHSA-wx3m-whqv-xv47 | Rust (edition 2024 | - | A+B | 4 | save reload or serialization | 2/1/0 | 40m | tiny repo | low | - |
| 64 | 19 | 15 | mantisbt/mantisbt | GHSA-3v2j-6fw9-f57c | PHP | CVE-2026-52882 | A+B | 6 | second implementation | 1/0/0 | 35m | - | low | - |
| 65 | 19 | 13 | grokability/snipe-it | GHSA-6f75-x745-xcpr | PHP ^8.2 (composer | CVE-2026-48507 | A+B | 2 | - | 1/2/0 | 40m | - | medium | - |
| 66 | 18 | 14 | john-broadway/pacioli | GHSA-3hj7-6vmj-h8v4 | Python (>=3.10) | CVE-2026-107841 | A | 2 | lower level api | 1/0/0 | 60m | - | low | - |
| 67 | 18 | 14 | universal-tool-calling-protocol/python-utcp | GHSA-8cp3-qxj6-px34 | Python >=3.10 | - | A | 6 | second implementation | 0/1/0 | 50m | tiny repo | low | - |
| 68 | 18 | 12 | orval-labs/orval | GHSA-2h9g-j24r-h63g | TypeScript | CVE-2026-71869 | A+B | 5 | defaults or merge route | 0/3/0 | 75m | - | medium | - |
| 69 | 18 | 12 | steipete/summarize | GHSA-3vx2-vqx8-jxfg | TypeScript (Node > | CVE-2026-53782 | A+B | 3 | wrapper or composition | 3/0/1 | 75m | - | medium | - |
| 70 | 18 | 12 | ether/etherpad | GHSA-fjgc-3mj7-8rg8 | TypeScript (Node.j | CVE-2026-55087 | B | 2 | second implementation | 0/3/0 | 30m | - | medium | - |
| 71 | 18 | 14 | aquasecurity/trivy | GHSA-8rc5-4fr6-64pw | Go | CVE-2026-63328 | A | 8 | save reload or serialization | 1/0/0 | 40m | - | medium | - |
| 72 | 18 | 14 | openchoreo/openchoreo | GHSA-c5f6-2rm9-2w8g | Go | CVE-2026-73840 | A | 1 | defaults or merge route | 1/0/0 | 50m | - | low | - |
| 73 | 18 | 12 | uutils/coreutils | GHSA-gwm6-q8ch-hcfr | Rust | CVE-2026-35356 | A+B | 2 | lower level api | 3/0/0 | 75m | - | medium | - |
| 74 | 18 | 12 | ericlbuehler/mistral.rs | GHSA-wfgq-w7cq-qj7j | Rust | - | A | 5 | second implementation | 2/0/0 | 75m | - | medium | - |
| 75 | 18 | 14 | openremote/openremote | GHSA-xqr9-4wvv-gvch | Java (+ Groovy Spo | CVE-2026-54641 | A+B | 8 | wrapper or composition | 0/1/0 | 30m | - | medium | - |
| 76 | 18 | 12 | starcitizenwiki/mediawiki-extensions-embedvideo | GHSA-5c7p-g73q-rpg5 | PHP (plus Resource | CVE-2026-55692 | A | 6 | lower level api | 2/0/0 | 45m | tiny repo | low | - |
| 77 | 17 | 11 | ibm/mcp-context-forge | GHSA-vwf3-4xxj-qg6h | Python (plus unrel | - | injection_only | 4 | - | 3/0/0 | 20m | - | high | - |
| 78 | 17 | 17 | tinacms/tinacms | GHSA-8mq9-5fw2-5rm4 | TypeScript | CVE-2026-59992 | A | 12 | second implementation | - | 50m | - | low | - |
| 79 | 17 | 11 | gogs/gogs | GHSA-5c3f-6486-3g7g | Go | CVE-2026-52809 | B | 1 | wrapper or composition | 4/0/0 | 35m | - | medium | - |
| 80 | 17 | 17 | 0xjacky/nginx-ui | GHSA-9h23-53f4-q947 | Go (backend); Type | CVE-2026-107804 | injection_only | 5 | defaults or merge route | - | 35m | - | low | - |
| 81 | 17 | 17 | spring-projects/spring-hateoas | GHSA-7fxc-486f-32q9 | Java | CVE-2026-41006 | A | 8 | lower level api | - | 40m | - | low | - |
| 82 | 17 | 17 | jenkinsci/contrast-continuous-application-security-plugin | GHSA-8263-qv4g-vfxr | Java | CVE-2026-57299 | A | 11 | wrapper or composition | - | 30m | - | low | - |
| 83 | 17 | 17 | sakaiproject/sakai | GHSA-9284-fjc3-fmmj | Java | CVE-2026-54050 | A | 3 | lower level api | - | 20m | - | low | - |
| 84 | 17 | 11 | http4s/http4s | GHSA-cp4q-fqw9-4hf6 | Scala (2.13 / 3 cr | CVE-2026-69218 | A+B | 4 | defaults or merge route | 0/3/0 | 75m | - | medium | yes |
| 85 | 17 | 17 | hs-web/hsweb-framework | GHSA-fxr3-gvm4-m8vc | Java 17 | CVE-2026-11477 | A | 3 | save reload or serialization | - | 60m | - | low | - |
| 86 | 17 | 17 | quarkusio/quarkus | GHSA-qcxp-gm7m-4j5v | Java | CVE-2026-50559 | A | 5 | second implementation | - | 35m | - | medium | - |
| 87 | 17 | 17 | getkirby/kirby | GHSA-67mx-6wf2-92xp | PHP 8.2+ | CVE-2026-71415 | A | 5 | wrapper or composition | - | 50m | - | low | - |
| 88 | 17 | 17 | composer/composer | GHSA-96h3-5x6v-m776 | PHP | CVE-2026-59944 | A | 4 | second implementation | - | 35m | - | medium | - |
| 89 | 16 | 16 | python-social-auth/social-core | GHSA-vqg6-3fw6-j9jg | Python (>=3.10) | CVE-2026-57179 | A | 2 | save reload or serialization | - | 60m | - | low | - |
| 90 | 16 | 10 | svg/svgo | GHSA-4vpr-x523-8j87 | JavaScript (Node.j | CVE-2026-84369 | A+B | 2 | second implementation | 4/0/0 | 40m | tiny repo | medium | - |
| 91 | 16 | 16 | unleash/unleash | GHSA-5vf6-jrqr-78fj | TypeScript (ESM) | CVE-2026-63004 | A | 3 | save reload or serialization | - | 60m | - | medium | - |
| 92 | 16 | 16 | nuxt-modules/og-image | GHSA-q8hw-4fvp-9rwv | TypeScript | CVE-2026-61793 | A | 2 | second implementation | - | 45m | - | low | - |
| 93 | 16 | 16 | tinyauthapp/tinyauth | GHSA-328g-jx67-v94g | Go | CVE-2026-77560 | A | 2 | second implementation | - | 40m | - | medium | - |
| 94 | 16 | 16 | tilt-dev/tilt | GHSA-6m68-r693-78qx | Go (plus TypeScrip | CVE-2026-55883 | A | 5 | wrapper or composition | - | 45m | - | medium | - |
| 95 | 16 | 16 | olivetin/olivetin | GHSA-prj9-97mp-mwh2 | Go (service); Vue/ | CVE-2026-53541 | A | 4 | second implementation | - | 40m | - | medium | - |
| 96 | 16 | 16 | portainer/portainer | GHSA-x626-fcwx-f5pc | Go (backend), plus | CVE-2026-55761 | A | 2 | second implementation | - | 45m | - | medium | - |
| 97 | 16 | 16 | spring-attic/spring-statemachine | GHSA-85qj-f5wg-rwp9 | Java | CVE-2026-41862 | A | 7 | second implementation | - | 45m | - | medium | - |
| 98 | 15 | 15 | sooperset/mcp-atlassian | GHSA-2xj6-xx86-cwwc | Python (>=3.10) | CVE-2026-77255 | A | 5 | second implementation | - | 30m | - | medium | - |
| 99 | 15 | 15 | unstructured-io/unstructured | GHSA-4mvj-m6j5-pmf7 | Python | CVE-2026-71428 | A | 3 | second implementation | - | 45m | - | medium | - |
| 100 | 15 | 11 | remix-run/react-router | GHSA-chx6-hx7r-mcp5 | TypeScript | CVE-2026-55685 | A+B | 3 | second implementation | 1/0/0 | 60m | - | medium | yes |
| 101 | 15 | 15 | projectdiscovery/nuclei | GHSA-jpvm-9frm-hjcq | Go | CVE-2026-76805 | A | 13 | defaults or merge route | - | 240m | - | medium | - |
| 102 | 15 | 15 | mattermost/mattermost | GHSA-rp4v-qc77-phm4 | Go (server); TypeS | CVE-2026-3433 | A | 4 | save reload or serialization | - | 75m | - | low | - |
| 103 | 15 | 11 | square/wire | GHSA-9rm7-3qhh-h2mc | Kotlin (multiplatf | CVE-2026-63126 | A | 6 | second implementation | 1/0/0 | 60m | - | medium | yes |
| 104 | 15 | 9 | graylog2/graylog2-server | GHSA-m9c2-85gv-8xr5 | Java (backend) + T | CVE-2026-69190 | B | 1 | - | 1/1/1 | 20m | - | medium | - |
| 105 | 15 | 11 | buddypress/buddypress | GHSA-j3j5-5m8v-7gvc | PHP (WordPress plu | CVE-2026-53673 | injection_only | 3 | - | 1/0/0 | 25m | - | medium | - |
| 106 | 15 | 9 | verbb/formie | GHSA-v3f3-cmj4-cvj9 | PHP 8.2 (+ Vue/JS  | CVE-2026-76086 | B | 1 | - | 1/0/1 | 45m | - | low | - |
| 107 | 14 | 10 | open-webui/open-webui | GHSA-3pf7-q2g3-wj28 | Python (FastAPI, a | CVE-2026-87997 | B | 2 | - | 0/1/0 | 25m | - | medium | - |
| 108 | 14 | 14 | jupyterlab/jupyterlab | GHSA-6966-vjj6-99xv | TypeScript | CVE-2026-102831 | A | 5 | lower level api | - | 40m | - | low | - |
| 109 | 14 | 14 | flyfish-dev/file-viewer | GHSA-3753-m2x2-q623 | TypeScript | CVE-2026-91127 | A | 6 | wrapper or composition | - | 70m | - | low | - |
| 110 | 14 | 14 | cline/cline | GHSA-3cj3-hqcr-g934 | TypeScript | CVE-2026-59723 | A | 1 | defaults or merge route | - | 40m | - | medium | - |
| 111 | 14 | 14 | patriksimek/vm2 | GHSA-8hr7-r645-pc6w | JavaScript | CVE-2026-92935 | A | 3 | lower level api | - | 20m | - | medium | - |
| 112 | 14 | 14 | angular/angular | GHSA-hh8m-fm6v-7cvg | TypeScript | CVE-2026-88057 | A | 3 | second implementation | - | 150m | - | medium | - |
| 113 | 14 | 8 | jihong88/suneditor | GHSA-w93q-cq9w-58p7 | JavaScript (ES mod | CVE-2026-54606 | B | 2 | - | 3/0/0 | 35m | - | low | - |
| 114 | 14 | 8 | i18next/i18next-http-backend | GHSA-xvq9-wjp8-hwqf | JavaScript (ESM) | CVE-2026-105800 | B | 3 | - | 0/1/1 | 25m | tiny repo | medium | - |
| 115 | 14 | 14 | zalando/skipper | GHSA-5gpm-rgj3-9q76 | Go | CVE-2026-86043 | A | 2 | second implementation | - | 40m | - | medium | - |
| 116 | 14 | 14 | klever-io/klever-go | GHSA-cgc5-v3f2-8m2v | Go | CVE-2026-54755 | A | 7 | second implementation | - | 45m | - | medium | - |
| 117 | 14 | 14 | fabiolb/fabio | GHSA-fq95-v8xc-jm3v | Go | CVE-2026-62987 | injection_only | 1 | defaults or merge route | - | 15m | - | medium | - |
| 118 | 14 | 14 | forgekeep/nebula-mesh | GHSA-g4x6-jcvr-9m3g | Go | CVE-2026-55513 | A | 1 | defaults or merge route | - | 20m | - | low | - |
| 119 | 14 | 14 | openc3/cosmos | GHSA-vp3w-52v9-q57f | Ruby (plus a POSIX | CVE-2026-77601 | injection_only | 3 | second implementation | - | 20m | - | low | - |
| 120 | 13 | 7 | lepture/mistune | GHSA-4j32-57v6-6g45 | Python (>=3.8) | CVE-2026-59925 | B | 4 | wrapper or composition | 1/1/0 | 240m | tiny repo | medium | yes |
| 121 | 13 | 7 | netflix/lemur | GHSA-v5rc-cpwc-cfpr | Python | CVE-2026-71303 | B | 1 | - | 1/1/0 | 20m | - | medium | - |
| 122 | 13 | 13 | acacode/swagger-typescript-api | GHSA-38c3-wv3c-v3xj | TypeScript (Node > | CVE-2026-54661 | A | 2 | second implementation | - | 15m | - | medium | - |
| 123 | 13 | 7 | apostrophecms/apostrophe | GHSA-g8qq-57p8-ggw5 | JavaScript (Node.j | CVE-2026-84371 | B | 1 | - | 1/1/0 | 35m | - | medium | - |
| 124 | 13 | 9 | adawolfa/isdoc | GHSA-xg43-5579-qw6v | PHP >= 8.4 | - | A+B | 6 | second implementation | 1/0/0 | 60m | tiny repo | low | yes |
| 125 | 12 | 12 | middleapi/orpc | GHSA-gcgf-fh7c-8gf2 | TypeScript | CVE-2026-103918 | A | 2 | second implementation | - | 15m | - | medium | - |
| 126 | 12 | 8 | authorizerdev/authorizer | GHSA-29rf-f4vv-pvq6 | Go | CVE-2026-35511 | A | 2 | - | 1/0/0 | 75m | - | medium | - |
| 127 | 12 | 12 | identrail/identrail | GHSA-cp3j-m783-3ph5 | Go (plus TypeScrip | CVE-2026-59185 | A | 2 | second implementation | - | 75m | - | low | - |
| 128 | 12 | 12 | keycloak/keycloak | GHSA-794g-x443-36f7 | Java | CVE-2026-2092 | A | 4 | second implementation | - | 75m | - | medium | - |
| 129 | 12 | 12 | spring-projects/spring-ws | GHSA-whpp-xv3h-rwxf | Java | CVE-2026-40999 | A | 3 | second implementation | - | 75m | - | medium | - |
| 130 | 11 | 11 | ueberdosis/tiptap | GHSA-j95f-988m-3j2f | TypeScript | - | A | 5 | second implementation | - | 40m | - | medium | yes |
| 131 | 11 | 7 | corazawaf/coraza | GHSA-3wr7-993q-jrff | Go | - | B | 2 | - | 1/0/0 | 75m | - | low | - |
| 132 | 11 | 11 | hatchet-dev/hatchet | GHSA-g26x-m427-f48f | Go (plus generated | CVE-2026-63342 | injection_only | 1 | - | - | 15m | - | low | - |
| 133 | 11 | 11 | bytecodealliance/wasmtime | GHSA-2hw9-mc66-jc2q | Rust | CVE-2026-104855 | A | 16 | wrapper or composition | - | 75m | - | medium | - |
| 134 | 11 | 11 | micrometer-metrics/micrometer | GHSA-g3pr-3p32-fp23 | Java (Java 17+ nee | CVE-2026-40984 | A | 6 | second implementation | - | 25m | - | medium | yes |
| 135 | 10 | 4 | mlflow/mlflow | GHSA-h7x2-h6g9-p789 | Python | CVE-2026-71211 | none | 0 | - | 0/4/1 | 60m | - | medium | - |
| 136 | 10 | 10 | projectcapsule/capsule | GHSA-gjw4-3v3v-rqxg | Go | CVE-2026-61672 | injection_only | 3 | - | - | 10m | single site | medium | - |
| 137 | 9 | 9 | netty/netty | GHSA-272m-gcwp-mpwg | Java | CVE-2026-56820 | injection_only | 1 | - | - | 25m | - | medium | - |
| 138 | 7 | 7 | apache/camel | GHSA-vvwm-3j43-7pfm | Java | CVE-2026-63621 | injection_only | 1 | - | - | 15m | - | medium | - |
| 139 | 7 | 7 | guzzle/guzzle | GHSA-f7vp-7xgx-4w4r | PHP | CVE-2026-69245 | injection_only | 3 | - | - | 20m | single site, tiny repo | medium | - |
| 140 | 6 | 6 | vllm-project/vllm | GHSA-935w-9g4m-p28p | Python | CVE-2026-105752 | injection_only | 1 | - | - | 10m | single site | medium | - |
| 141 | 6 | 6 | strawberry-graphql/strawberry | GHSA-pfvf-fwfp-25mp | Python (>=3.10) | CVE-2026-107728 | injection_only | 1 | - | - | 15m | single site | medium | - |
| 142 | 6 | 6 | esphome/device-builder | GHSA-rrxg-g2pf-6hh4 | Python | CVE-2026-59178 | none | 1 | - | - | 25m | - | low | - |
| 143 | 6 | 2 | wwbn/avideo | GHSA-95jh-7r58-xmxw | PHP | CVE-2026-33731 | B | 1 | lower level api | 0/1/0 | 40m | needs network at runtime | medium | - |
| 144 | 4 | 4 | nezhahq/nezha | GHSA-rf68-8gjr-36q7 | Go | CVE-2026-101090 | none | 1 | - | - | 15m | single site | low | - |
| 145 | 3 | 3 | cure53/dompurify | GHSA-c2j3-45gr-mqc4 | TypeScript | CVE-2026-66010 | injection_only | 1 | - | - | 10m | single site, tiny repo | medium | - |
| 146 | 2 | 2 | fasterxml/jackson-core | GHSA-r7wm-3cxj-wff9 | Java | CVE-2026-68494 | none | 2 | - | - | 15m | - | medium | yes |
| 147 | 2 | 2 | thephpleague/commonmark | GHSA-jjv6-8j6v-6j52 | PHP (^7.4 // ^8.0, | CVE-2026-86429 | none | 1 | - | - | 60m | - | medium | yes |
| 148 | 1 | 1 | issdandavis/scbe-aethermoore | GHSA-q986-4x7x-gx39 | Python (+ static H | CVE-2026-57443 | none | 0 | - | - | 0m | single site | low | - |
| 149 | -2 | -2 | lucasdillmann/nginx-ignition | GHSA-hf33-q6cf-c66f | Go (multi-module g | CVE-2026-61630 | none | 0 | - | - | 0m | - | low | - |

Not ranked (invalid record, re-screen): entry 18575 (openlistteam/openlist).
