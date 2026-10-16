# Test-quality repair list from post-run audits

_Generated 2026-10-16 from every POSTMORTEM.json (auditor sub-agents, Opus 5.5 high). One section per task; each entry = one audit that flagged a lenient/faulty test or recommended a test change. Source file listed for the full reasoning._

## actualbudget

- **actualbudget__Ddhvfz2** (trustworthy=True, model-solved); flagged: security/03-file-authorization.test.js (3 tests)
  - recommended: Accept the reward as model-solved. Optional test hardening: add cross-user probes for /upload-user-file (overwriting an existing file), /reset-user-file, /download-user-file and /sync, and an unauthenticated probe on a second SimpleFIN/Pluggy endpoint. Also include final-code/changes.patch in future postmortem bundles.
  - source: `~/.tb-graders/cwe/jobs/actualbudget-deepseek-seq1-1791999676/actualbudget__Ddhvfz2/postmortem-20261015T223917Z/POSTMORTEM.json`

## argo-workflows

- **argo-workflows__oovj8GZ** (trustworthy=True, model-solved); flagged: server/sync::TestSecZZSync{Get,Create,Update,Delete}RequiresAuthz; server/workflowtemplate::TestSecZZWorkflowTemplateGetRequiresAuthz + server/clus
  - recommended: Accept reward 1.0 as model-solved, noting that the solve relied on the public upstream fix found online. Separately, consider tightening the SSAR fakes in the sync and template tests so they assert the reviewed resource, verb and namespace, and add evidence/final-code/changes.patch to the postmortem bundle.
  - source: `~/.tb-graders/cwe/jobs/argo-workflows-deepseek-r1-20261015-010213-n001/argo-workflows__oovj8GZ/postmortem-20261015T223917Z/POSTMORTEM.json`

## async-http-client

- **async-http-client__uGhFbba** (trustworthy=True, model-solved)
  - recommended: Accept reward 1.0 as model-solved. Add evidence/final-code/changes.patch to the postmortem package so the exact final diff can be checked. Optionally add a hidden security test with a caller header that mixes an RFC-invalid pair with a valid one, plus a stored cookie of the same name as the invalid pair. That would separate decode-and-re-encode fixes from verbatim-preserving ones. It is not ground
  - source: `~/.tb-graders/cwe/jobs/async-http-client-deepseek-1013-214752/async-http-client__uGhFbba/postmortem-20261015T223918Z/POSTMORTEM.json`
- **async-http-client__tfkenPc** (trustworthy=False, harness-or-infra)
  - recommended: Do not count this trial as model-solved. Recover the graded /app diff (the archived container or image, or regenerate final-code/changes.patch) and compare it with the transcript's last recorded state. Check whether the in-container claude process kept running after AgentTimeoutError, for example from file mtimes on Unauthorized401Interceptor.java and ProxyUnauthorized407Interceptor.java compared 
  - source: `~/.tb-graders/cwe/jobs/async-http-client-mimo-1013-214753/async-http-client__tfkenPc/postmortem-20261015T223918Z/POSTMORTEM.json`

## asyncssh

- **asyncssh__Pwh2zVS** (trustworthy=True, model-solved)
  - recommended: Accept the reward 1.0 as model-solved for (asyncssh, mimo-v2.6-pro). Fix the post-mortem tooling: evidence/final-code/changes.patch was missing and had to be rebuilt from the transcript. Optionally, to harden the task for future runs, add SCP cases for absolute and embedded traversal ('/tmp/x', 'a/../../x'), add a second injected message type per direction (such as SERVICE_REQUEST or CHANNEL_OPEN 
  - source: `~/.tb-graders/cwe/jobs/asyncssh-mimo-r1-20261015-102205-n001/asyncssh__Pwh2zVS/postmortem-20261015T223918Z/POSTMORTEM.json`

## cloudreve

- **cloudreve__JwDetgF** (trustworthy=True, model-solved)
  - recommended: Accept reward 1.0 as a genuine model solve for (cloudreve, deepseek-flash[1m]). Optional hardening of the task, which does not affect this verdict: add a 'banned' status case to the search test, and a backslash or absolute-path SuggestedTarget case to the traversal test. Also fix the postmortem packager so it includes final-code/changes.patch.
  - source: `~/.tb-graders/cwe/jobs/cloudreve-deepseek-seq1-1792023049/cloudreve__JwDetgF/postmortem-20261015T223918Z/POSTMORTEM.json`
- **cloudreve__TFwPvkf** (trustworthy=True, model-solved); flagged: security/test_thumbnail_pixel_bomb::test_pixel_bomb_thumbnail_refused
  - recommended: Accept as a genuine solve for the pair (cloudreve, mimo-v2.6-pro). Add final-code/changes.patch to the postmortem bundle generator so future audits do not have to rebuild the diff. Optionally tighten test_thumbnail_pixel_bomb by also asserting that a moderately large but plausible image (for example 6000x4000) still thumbnails, which would separate over-restrictive caps from correct ones.
  - source: `~/.tb-graders/cwe/jobs/cloudreve-mimo-r1-20261015-031109-n002/cloudreve__TFwPvkf/postmortem-20261015T223918Z/POSTMORTEM.json`

## hickory-dns

- **hickory-dns__pJXHdmD** (trustworthy=True, model-solved); flagged: functional::* (5 tests, all on non-validating resolvers)
  - recommended: Accept reward 1.0 as model-solved via the upstream fix. Optional test hardening: add a functional test that uses a validating resolver with an answer that is legitimately insecure or indeterminate and must still resolve. Also consider making the grader clean or isolate /opt/target before compiling, so agent builds cannot shadow test binaries.
  - source: `~/.tb-graders/cwe/jobs/hickory-dns-deepseek-r1-20261015-112539-n001/hickory-dns__pJXHdmD/postmortem-20261015T223919Z/POSTMORTEM.json`
- **hickory-dns__K6AyPff** (trustworthy=True, model-solved); flagged: security::{lookup_a_bogus_is_rejected, lookup_txt_bogus_is_rejected, lookup_ip_b; functional::{unsigned_lookup_a_succeeds, unsigned_lookup_ip_succeeds, unsigned_l
  - recommended: Accept the 1.0 as model-solved. Harden the task for later runs: (a) add functional tests with a validating resolver that returns a legitimately Insecure (proven unsigned) answer and a Secure answer, so 'fail every validating lookup' cannot pass; (b) assert that the security error is a DNSSEC/validation error, not just any error; (c) add a security variant with a Bogus CNAME whose target needs a se
  - source: `~/.tb-graders/cwe/jobs/hickory-dns-mimo-r1-20261015-114706-n001/hickory-dns__K6AyPff/postmortem-20261015T223919Z/POSTMORTEM.json`

## jackson-databind

- **jackson-databind__8hjvYno** (trustworthy=True, model-solved)
  - recommended: Keep the reward of 1.0 and count this as a genuine model solve for (jackson-databind, deepseek-flash). Fix the postmortem packager so that evidence/final-code/changes.patch is included. A minor optional hardening for the task: add a security variant with the value before the discriminator in the JSON for the default-constructor bean, which exercises the handlePropertyValue buffering path rather th
  - source: `~/.tb-graders/cwe/jobs/jackson-databind-deepseek-1014-051410/jackson-databind__8hjvYno/postmortem-20261015T223919Z/POSTMORTEM.json`
- **jackson-databind__kaRv44B** (trustworthy=True, model-solved)
  - recommended: Accept the reward as a genuine model-solved result for mimo-v2.6-pro on jackson-databind. Optional test hardening: add a security case with 'asset' before 'kind' on the default-constructor or builder bean, so the buffered complete(bean) path is tested on its own. Also fix the postmortem packager so it includes final-code/changes.patch.
  - source: `~/.tb-graders/cwe/jobs/jackson-databind-mimo-1014-051410/jackson-databind__kaRv44B/postmortem-20261015T223919Z/POSTMORTEM.json`

## rclone

- **rclone__a4P8Fc2** (trustworthy=True, model-solved); flagged: functional::TestProxyWrongSecretRefused / TestProxyNoAuthRefused / TestProxyUnkn
  - recommended: Accept reward 1.0 as model-solved: the agent applied the upstream fix, which is allowed. Separately, make the grader stricter: add a positive proxy-mode functional test (correct secret -> 200), even though it cannot pass on the vulnerable code, or score it in its own group, so that a deny-all proxy fix can no longer earn full reward. Also consider saving final-code/changes.patch in future evidence
  - source: `~/.tb-graders/cwe/jobs/rclone-deepseek-seq1-1791950746/rclone__a4P8Fc2/postmortem-20261015T223920Z/POSTMORTEM.json`
- **rclone__q4t49md** (trustworthy=True, model-solved); flagged: functional::TestProxyWrongSecretRefused / TestProxyNoAuthRefused / TestProxyUnkn
  - recommended: Accept the result as model-solved. For the task: consider adding a proxy-mode positive test (alice with her correct secret must get 200) that runs only on the fixed side, or a grading check that rejects deny-all proxy fixes. As written, a fix that denies every proxy request scores 1.0. Also include final-code/changes.patch in future postmortem bundles.
  - source: `~/.tb-graders/cwe/jobs/rclone-mimo-r1-20261015-120241-n001/rclone__q4t49md/postmortem-20261015T223920Z/POSTMORTEM.json`

## rclone-sib

- **rclone-sib__ypUhTQw** (trustworthy=False, test-fault); flagged: security::TestS3ListBucketsAliceEmptySecret / TestS3GetObjectAliceEmptySecret / ; functional::TestS3ProxyWrongSecretRefused / TestS3ProxyNoAuthRefused / TestS3Pro
  - recommended: Do not count this trial as a solve. Add a functional test, e.g. TestS3ProxyCorrectSecretIsServed: GET / and GET /alicebucket/readable.txt as AliceKey/AliceSecret against StartProxyServer expect 200 plus content, ideally for bob as well. Also add a reject-all-proxy patch to the manifest patch_checks, expected to give functional_fail. Then re-grade this trial with /regrade. Under the model's patch t
  - source: `~/.tb-graders/cwe/jobs/rclone-sib-mimo-seq1-1792025341/rclone-sib__ypUhTQw/postmortem-20261015T223920Z/POSTMORTEM.json`

## ruby-saml

- **ruby-saml__jZ9jGb7** (trustworthy=True, model-solved)
  - recommended: Accept reward 1.0 as model-solved. Optional task hygiene: add final-code/changes.patch to the postmortem bundle; correct build-notes.md ('No network at run time' does not match the run); consider either relaxing the /exceed/i message requirement or stating in the instruction that rejection raises ValidationError; and, if bounded decompression matters, add a test that tells streaming abort apart fr
  - source: `~/.tb-graders/cwe/jobs/ruby-saml-deepseek-seq1-1791990964/ruby-saml__jZ9jGb7/postmortem-20261015T223920Z/POSTMORTEM.json`
- **ruby-saml__WGgGoMj** (trustworthy=True, model-solved); flagged: security::resource: oversized message is rejected before expensive processing
  - recommended: Accept reward 1.0 as model-solved. Optional hardening: (1) have the oversized-input test check that base64_encoded? or parsing is not reached, or time-bound it, so the 'before expensive processing' clause is enforced; (2) include final-code/changes.patch in future postmortem evidence packs.
  - source: `~/.tb-graders/cwe/jobs/ruby-saml-mimo-seq1-1792005093/ruby-saml__WGgGoMj/postmortem-20261015T223920Z/POSTMORTEM.json`

## russh

- **russh__6zvdBLF** (trustworthy=True, model-solved)
  - recommended: Accept the reward as model-solved. Separately, look into the agent-environment disk exhaustion (container overlay at 100% during the run). It did not change this outcome, but it could make other trials fail through infra. Optionally, to strengthen the task, add a security assertion that the failure is a negotiation error (e.g. NoCommonAlgo) rather than any handshake failure.
  - source: `~/.tb-graders/cwe/jobs/russh-deepseek-1013-221533/russh__6zvdBLF/postmortem-20261015T223920Z/POSTMORTEM.json`
- **russh__t2scdx3** (trustworthy=True, model-solved); flagged: russh-sec-harness::security::aes256_ctr_with_none_mac_refused_server_side (and _
  - recommended: Accept the result as model-solved (pass) for (russh, mimo-v2.6-pro). Separately, for task hygiene: (1) fix the harness so evidence/final-code/changes.patch is captured; (2) note that the directional security tests cannot detect a one-role-only fix because both peers run the patched library. Consider a test where one peer is a raw/unpatched KEXINIT sender, as with the in-crate raw_no_crypto helper.
  - source: `~/.tb-graders/cwe/jobs/russh-mimo-1013-221533/russh__t2scdx3/postmortem-20261015T223921Z/POSTMORTEM.json`

## trigger-dev

- **trigger-dev__xG36wVE** (trustworthy=True, model-solved); flagged: security/test_batch_check_completion_unauth::test_unauthenticated_check_completi
  - recommended: Accept reward 1.0 as model-solved for mimo-v2.6-pro on trigger-dev. Separately: (a) the postmortem packager should snapshot the exact test and fixture versions that were graded, because evidence/tests here is a later revision (6 functional tests, TR_BATCH) than the one that ran (5 functional tests, no TR_BATCH); (b) consider adding a security test where a logged-in user from another org drives che
  - source: `~/.tb-graders/cwe/jobs/trigger-dev-mimo-r1-20261015-030631-n002/trigger-dev__xG36wVE/postmortem-20261015T223921Z/POSTMORTEM.json`

## webob

- **webob__ksABBkj** (trustworthy=True, model-solved)
  - recommended: Accept reward 1.0 as model-solved for (webob, mimo-v2.6-pro). Fix the task image separately: remove the upstream regression tests for GHSA-6hx8 (and the comments that describe the fix) from /app/tests at the vulnerable commit. They hand over the expected outputs and the fix design, so the task is weaker than intended for every model. Also add final-code/changes.patch to future postmortem bundles.
  - source: `~/.tb-graders/cwe/jobs/webob-mimo-1014-045733/webob__ksABBkj/postmortem-20261015T223921Z/POSTMORTEM.json`
- **webob__GTgqHjZ** (r12, trustworthy=True, model-solved, 2026-10-16)
  - recommended: add a functional test that `Request.relative_url("//other.host/x")` keeps standard
    RFC 3986 resolution (the instruction says relative resolution works "exactly as it does today");
    MiMo's fix sends a bare `//host` to the request's own host and no test noticed. Does not change
    this run's score.
  - source: `~/.tb-graders/cwe/jobs/webob-mimo-r12-20261015-223000-n001/webob__GTgqHjZ/postmortem-20261016T041058Z/verdict.json`
- **rclone__ByW3teV** (rclone MiMo r21, trustworthy=True, model-solved, 2026-10-16)
  - recommended: the correct-secret tests check GET only; add a positive PUT/DELETE with the correct
    secret so a fix that verifies reads but refuses writes cannot pass. Does not change this score.
  - source: `~/.tb-graders/cwe/jobs/rclone-mimo-r21-20261015-231118-n001/rclone__ByW3teV/postmortem-20261016T043358Z/verdict.json`
- **trigger-dev__iNC3Sbj** (trigger-dev MiMo r11, trustworthy=True, model-solved, 2026-10-16)
  - recommended: (1) batch check-completion security test should also try a logged-in member of a
    DIFFERENT org (a requireUserId-only fix passes today); (2) add a functional authenticated
    same-environment stream write (deleting the write route passes today). Neither changes this score.
  - source: `~/.tb-graders/cwe/jobs/trigger-dev-mimo-r11-20261015-225101-n001/trigger-dev__iNC3Sbj/postmortem-20261016T043357Z/verdict.json`
