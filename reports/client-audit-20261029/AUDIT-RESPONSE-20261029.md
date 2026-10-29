# Response to the audit of delivered CWE-bench tasks

*2026-10-29*

Thank you for the audit. We re-checked all 69 delivered tasks, not only the examples you named, and every saved graded
run: 437 runs across both models.

This note covers:
- what we found for each finding (PO-1, PO-2, PO-3);
- what this update changes;
- what follows in the next update;
- how we review tasks from now on.

The current list of breakers, with their confidence labels, and the list of withdrawn tasks are in
[`RESULTS.md`](../RESULTS.md).

## At a glance

| Finding | Our re-check | Outcome |
|---|---|---|
| PO-1: the scorer does not know which tests should have run | Confirmed as a grader weakness. In practice only 2 of 437 runs had a missing test, and both still score 0 when missing tests count as failures. | No verdict changes. The fix is planned (section 1). |
| PO-2: infrastructure faults could look like model failures | Confirmed for the collect-style packages as delivered. Hardened graders are included in this update. Every run behind the seven collect-style verdicts was regraded under them. | No verdict changes. hono-jsx-xss is withdrawn after a fresh trial. |
| PO-3: tests tied to one implementation | Confirmed for a subset. Some tasks are withdrawn; others get test-only fixes and a regrade. | 14 tasks withdrawn here; hono-jsx-xss makes 15 in all. Test fixes for 5 tasks are in this update, and 5 more follow. |

After this update, 54 tasks remain delivered.

## 1. PO-1: the scorer does not know which tests should have run

**The finding is correct.** No delivered task carries a complete list of the tests it expects. None records the test
runners' exit codes in a way that catches a missing test, and in some tasks a test key can repeat. So if part of a
test group never ran, the scorer could not tell.

**The effect on delivered results is small.**
- In every task, a crash or timeout of a whole test group already ends as a trial error or a score of 0.
- The risk is a *partial* drop inside a group that has several units.
- We compared the tests each graded run reported with the task's full set:

| | Count |
|---|---|
| Graded runs checked | 437 |
| Runs with tests missing | 2 (0.5 %) |
| Rewards that change when missing tests count as failures | 0 |
| Verdict changes | 0 |
| Runs where a repeated test key hid a failing result | 0 |

Both runs with missing tests were counted failures with reward 0:
- **One run crashed.** A panic in the product code stopped its test binary.
- **One run did not compile.** The model changed public signatures, so the tests could not build, which is the
  intended path for that case.

**The planned fix** is not part of this update:
1. **An expected-test manifest per task.** It will be generated from the test sources, not copied from a reference
   run. A test in the manifest that does not report counts as a failure.
2. **Runner exit codes recorded** for every runner invocation, with per-unit guards in place of "any results file
   is enough".
3. **Unique test keys**, so a repeated name can never overwrite a result.

The fix can only add failures. It therefore cannot turn a delivered failure into a pass. We will re-establish the
verdicts by rescoring the saved per-test results against the manifests.

## 2. PO-2: infrastructure faults could look like model failures

**This update includes hardened graders for nine tasks.**

**Collect-style tasks:**
- electron-builder-credential-exposure
- hubuum-error-log-secret-exposure
- jackson-databind-jsonview-bypass
- mockoon-admin-api-missing-auth
- seaweedfs-table-storage-authz
- siyuan-unpublished-resource-exposure
- theia-workspace-trust-bypass

What changed in these packages:
- **The collect hook writes a completion marker** only after it has a complete diff of the agent's container. Any
  failure is recorded in `collect_error.txt`, and no marker is written.
- **The verifier grades only a complete transfer.** In these cases it writes **no reward** and exits with an error,
  so the run is recorded as a trial error rather than a score:
  - collection failed;
  - the marker or the patch is missing;
  - the patch does not apply cleanly;
  - `/app` is absent;
  - the scorer crashes.
- **The partial-apply (`--reject`) fallback is removed.**
- **An empty patch** counts as "no agent changes" only when the collect hook confirmed a complete transfer.

**Overlay tasks** (katex-trust-setting-pollution, nocobase-storage-path-escape): an empty or incomplete restored
`/workspace` is refused before it is laid over the pristine sources.

**Nothing else changed in these packages:** instructions, security and functional tests, environments and scoring
are as delivered. In each collect-style `task.toml`, only the collect hook changed.

**How we verified the change:**
- **Fault injection.** For every package we injected each transfer fault, and each one now produces no reward. The
  faults were: collect error, missing marker, missing patch, a patch that does not apply, missing `/app`, a scorer
  crash, and an empty or partial workspace.
- **Behaviour otherwise unchanged.** Unmodified code still fails the security tests. The reference fix still scores
  1.0, and every check patch gives its declared result.
- **Every run behind the seven collect-style verdicts was regraded.** That is three runs per model per task, 42 runs
  in all, each through the updated package's collect path using its saved final code. Every reward is identical to
  the original grading, and no run changed between pass and fail. All seven tasks remain both-model breakers.

**hono-jsx-xss is withdrawn.** On the fixed package, a fresh DeepSeek trial solved it, so it is no longer a
both-model breaker.

## 3. PO-3: tests tied to one implementation

**Our rule from now on:** if a test and the instruction disagree, the failure is unfair, and that run counts as a
solve.

### 3.1 Tasks delivered before a recorded ruling was required

In our first two deliveries (20 and 21 October), a recorded ruling on every open fairness question was not yet a
hard condition for delivery. Five tasks went out while their fairness review still had a question open. All five
are withdrawn.

| Task | What happened | Status |
|---|---|---|
| knowns-memory-id-path-injection | One security test refuses an identifier that the keep-working list allows, and its subtests share state. A later re-trial (24 October) also produced a MiMo solve. | Withdrawn |
| litellm-outbound-destination-ssrf | One functional test requires the configured key to be sent to a caller-chosen endpoint, which the security rule forbids. All three counted MiMo failures were agent timeouts. | Withdrawn |
| openbao-identity-template-injection | Two functional tests require substituting a value that contains `/`, which the instruction lists as a forbidden character. The review asked for a ruling on this before delivery, and none was recorded. | Withdrawn |
| tinacms-storage-path-traversal | Two tests contradict sentences of the instruction: one about an absolute directory, one about an empty key. The review asked for a ruling, and none was recorded. | Withdrawn |
| yamcs-subscription-authz-bypass | One functional test requires a delivery that a sibling security test forbids. Later re-trials (24 October) produced solves for both models. | Withdrawn |

Since 25 October every delivered task has carried a recorded ruling. Section 5 describes how the delivery step now
enforces this.

### 3.2 Arguable tests that our review raised and a ruling kept

In each task below, our fairness review had already raised the test you flagged, and our ruling kept the task. Your
audit reads the instruction the other way. We re-reviewed each one under the rule above, rather than defending the
earlier call.

| Task | The question | Decision |
|---|---|---|
| cline-hub-dashboard-cross-site-access | Whether "an address that carries no explicit port" means the dashboard's port or port 80 | **Kept, confidence thin margin.** This is a difference in reading. Two runs, one per model, fail only this test. |
| jetty-project-wrong-secret-accepted | Whether a trailing space before the comma belongs to the configured secret, given that Jetty's realm format trims it | **Withdrawn.** The test conflicts with the realm format and with the keep-working clause, so both models would solve. |
| mistral-rs-image-source-file-read | Which public function keeps loading local files | **Withdrawn.** The tests fix one implementation, so both models would solve. |
| protobufjs-prototype-pollution | Storing `constructor` in the fill-only-absent case, and whether an unsafe final name must create an empty container | **Withdrawn.** DeepSeek would solve, so only one model fails it. |
| quarkus-path-authorization-bypass | Whether a `%00` path segment must be refused | **Withdrawn.** The case accepts only the reference fix's behaviour. DeepSeek would solve, so only one model fails it. |
| virtualenv-unauthenticated-seed-wheels | A configured private-index wheel whose digest differs from the public record for the same file name | **Withdrawn.** MiMo would solve, so only one model fails it. |

dbhub-readonly-mode-write-bypass was also in this group. On re-review we agree that its control-character test is
too strict. With that test set aside, DeepSeek solves the task, so it is withdrawn: only one model fails it fairly.

### 3.3 Further withdrawals from our own re-check

| Task | Reason | Status |
|---|---|---|
| passenger-temp-dir-symlink-reuse | The deciding test is outside the instruction's scope. Without it, five runs would be solves. | Withdrawn |
| rancher-github-team-membership | The test needs a state that the pinned code cannot create, so every run would be a solve. | Withdrawn |
| jackson-databind-sib | MiMo solved it once, so only one model fails it. | Withdrawn |

With hono-jsx-xss (section 2), 15 tasks are withdrawn in all. `RESULTS.md` lists each one with its reason.

### 3.4 Flagged tasks we keep: a difference in reading, not a defect

| Task | Why it was flagged | Why we keep it |
|---|---|---|
| lemur-acme-directory-ssrf | The probe sends an explicitly empty `acmeUrl`, which fixes how an empty field is treated. | Today an empty `acmeUrl` means "use the operator's configured directory", and the instruction keeps today's behaviour working. The security rule judges addresses that arrive in a request, and an empty value is not an address. |
| nono-installed-pack-trust | The dry-run test requires a non-zero exit. | The instruction states it directly: the command "must instead fail with a client error". |
| silverpeas-file-download-path-traversal | Requests that name no space are refused, although today's code has a commented "personal space" allow. | Only callers "entitled to the space a file belongs to" may receive it, and a request that names no space is entitled to none. The published upstream fix removes the same branch. |

In these three tasks the test and the reader take different readings of the same instruction text, and we believe
ours is the stronger one.

**Confidence labels.** To make cases like these easier to judge, every breaker now carries a confidence label
instead of a plain breaker / not-breaker verdict:
- high;
- medium;
- low;
- thin margin: the models fail at a single location.

Six delivered breakers carry the thin-margin label today:
- cline-hub-dashboard-cross-site-access (section 3.2);
- katex-trust-setting-pollution;
- kuma-tls-peer-verification-bypass;
- fastify-false-schema-validation-bypass;
- hubuum-error-log-secret-exposure;
- dolibarr-idor.

> **Thin-margin note on katex and kuma.** In katex-trust-setting-pollution, the failures rest on the
> `contrib/auto-render` route. In kuma-tls-peer-verification-bypass, they rest on `tools/xds-client`. Both
> locations are in scope by the instruction's wording.

### 3.5 Unfair tests that decided no run

Since 26 October our rule has been to repair, re-gate and regrade whenever an unfair test decided a run. On
28 October we extended it to every unfair test we find, including tests that decide nothing.

The tasks below were delivered before that extension. Each has a test that is unfair or tied to one implementation,
but in every run of both models the task also fails on other, fair tests. Their verdicts therefore stand.

**Included in this update.** The tests are fixed, the tasks re-gated, and every graded run regraded. Every run of
both models still fails each of these tasks.

| Task | Test change |
|---|---|
| ip-address-private-range-ssrf | The NAT64 local-use block (`64:ff9b:1::/48`) accepts either private or public as its answer, because the task leaves it open. |
| payara-rest-credential-forwarding | A staged file may sit at any depth under the staging directory, for example in a per-request subdirectory. Paths are compared in canonical form. |
| serialize-javascript-code-injection | The two T6 cases, a getter whose second read differs from its first, are removed. |
| tomcat-cluster-encryption-bypass | The bypass test builds and starts a real channel, so a refusal placed in the channel or in any interceptor is exercised. |
| uri-js-host-spoofing | For an empty scheme followed by an authority, the test accepts either today's parse or a parse that finds no scheme and no host. |

Only these test files changed in the five packages. In uri-js-host-spoofing, two comments in the agent image's
Dockerfile were also tidied.

We also checked the trailer tests of h2-request-destination-smuggling against the instruction. They are fair, and
that task is unchanged.

### 3.6 Fixes that follow in the next update

- **electron-builder-credential-exposure, seaweedfs-table-storage-authz, theia-workspace-trust-bypass,
  svgo-script-removal-xss:** these four are in the same position as the tasks in section 3.5. Each has an unfair
  test, but every run of both models also fails other, fair tests.
  - For the first three, the test-only fixes are applied on top of the hardened graders in this update, then every
    run is regraded.
  - On theia: two of its counted MiMo failures were 2-hour agent timeouts.
  - svgo-script-removal-xss will follow separately.
- **siyuan-unpublished-resource-exposure:** two defects in the test setup will be repaired, then the affected
  DeepSeek run regraded. One test fixture lacks an enabled flag, and a missing box configuration can crash one test
  binary.

## 4. What this update changes

| Change | Tasks |
|---|---|
| Withdrawn: package, trajectories where delivered, and README row removed | 15 (listed in `RESULTS.md`) |
| Grader hardening (PO-2) | electron-builder, hubuum, jackson-databind-jsonview, katex, mockoon, nocobase, seaweedfs, siyuan, theia |
| Test-only fixes (PO-3) | ip-address, payara, serialize-javascript, tomcat-cluster, uri-js |
| New results page | `RESULTS.md`: delivered breakers with confidence labels, and withdrawn breakers with reasons |

Task names are unchanged.

## 5. What we have changed in how we review tasks

Items 1–4 are in place in our pipeline as of 29 October 2026. Item 5 is recorded per breaker and shown in `RESULTS.md`.

1. **No delivery with an open question.** The delivery step refuses any task whose fairness review still has an
   open question without a recorded ruling, so the practice in place since 25 October is now a hard check.
2. **Cross-checking keep-working tests against the security rules.** Most of the issues above sit in functional
   ("keeps working") tests that contradict a security rule in the same instruction.
   - Our fairness review and our per-run audit now check every functional test against the security rules, not
     only the security tests against the instruction.
   - Both list every sentence of the instruction that a deciding test could conflict with. A test that conflicts
     with the instruction counts as unfair.
3. **Upstream's own fix as a check.** The gate runs the published upstream fix against the tests and flags any test
   it fails. A test that even upstream's fix cannot pass needs a reason.
4. **Scope check for added variants.** Variants we add beyond the advisory must sit within the scope the instruction
   describes, and must be reachable in the pinned code.
5. **A confidence label on every breaker:** high, medium, low or thin margin.
6. **Graders that know their tests (PO-1, PO-2).**
   - Each task will carry an expected-test manifest, and a missing test counts as a failure.
   - Runner exit codes will be recorded and test keys made unique.
   - Transfer or scorer faults will be reported as errors rather than scores. For the collect-style and overlay
     tasks, this is in this update (section 2).

## 6. An observation from our own review: file times in agent images

**What we found.** In injected tasks, the agent image built the repository first and applied the planted variants in
a later step. The planted files therefore carried a slightly newer modification time than the rest of the tree, and an
agent that sorted files by time could see which files had been changed. 31 of the delivered tasks were built this way.

**How agents used it.** We searched every trial transcript.
- Eight runs acted on the clue: seven DeepSeek and one MiMo.
- In the delivered breakers this happened only in siyuan-unpublished-resource-exposure, in three DeepSeek runs.
- Those runs still failed. The clue points only at the planted variants. The original flaw from the advisory sits in
  unmodified upstream files with the normal time, so the runs that followed the clue narrowed their fix to the planted
  files and missed the original flaw.
- No delivered verdict depends on the clue. We checked every failing run of the affected breakers, and none would
  plausibly have passed without it.

**What we changed.**
- New agent images give every file in the tree one uniform time.
- Trials reset file times when the agent container starts.
- The gate reports any remaining time difference.
- Our delivery step refuses a task whose agent image still shows the planted files.

**The delivered tasks.** We have not rebuilt the delivered packages for this, because no verdict changes. If you
re-run them, a model could still see the time difference in those images. Our post-run audits check every failing run
for this kind of hint, and we suggest your reviews do the same.

## 7. What follows

- **The remaining PO-3 test fixes:** electron-builder, seaweedfs, theia, siyuan and svgo (section 3.6).
- **The PO-1 grader fix:** an expected-test manifest per task, recorded runner exit codes and unique test keys, and
  a manifest rescore of the saved results.
