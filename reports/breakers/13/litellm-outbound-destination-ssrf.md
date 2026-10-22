# litellm-outbound-destination-ssrf — a task that DeepSeek V4.1 Flash and MiMo-V2.6-Pro both fail 3/3

**Status of 2026-10-21.** Sources: the delivered task, the task build and validation records, the fairness review, every counted attempt's transcript, final code and per-test results, and the independent audit of every counted attempt.

## Summary

- **Result: both target models failed all 3 counted attempts.**
  - DeepSeek V4.1 Flash: 0.0, 0.0, 0.0.
  - MiMo-V2.6-Pro: 0.0, 0.0, 0.0.
- DeepSeek finished every attempt on its own, in 31, 67 and 43 minutes of a 2-hour limit. MiMo never stopped on its own: each counted attempt reached its time limit (2 h, 2 h, and 3 h on the third) and was graded on the code it had at that moment. A time-limit stop counts as a failure.
- Every counted attempt was audited independently and judged a trustworthy, genuine model failure with high confidence.
- The task is a real library at the commit before a published fix: berriai/litellm, a Python LLM gateway, with a server-side request forgery that also carries the operator's credentials. The advisory's own routes are combined with one real route the published fix left open and two added routes of the same kind.
- Why both fail: both models close the attack routes, then lock down the connectivity-test route so tightly that a legitimate behaviour beside it breaks. The task requires that behaviour to keep working: when the operator opts in, a caller-supplied endpoint still inherits the configured credentials. Five of the six attempts failed on this one functional test alone. MiMo's first attempt also left three routes open when its time ran out.

## 1. The task

**Vulnerability (CWE-918, server-side request forgery, with credential exposure).** LiteLLM is a self-hosted gateway in front of LLM providers. An operator configures deployments: a name clients call, the upstream provider and endpoint, and the credentials for it. A client holding an ordinary proxy key can make the gateway send a provider request to a host the client chooses, carrying the deployment's configured credential. In the reported example, the client puts a URL where the model identifier belongs in a deployment-scoped route. The body names a legitimate model, and the URL path decides the destination.

**Base advisory:** GHSA-3CV6-JPF6-8222. Vulnerable commit `76ffefcc1c36f4e78178ca0278d38385cafa6ec6`, the direct parent of the upstream fix `473f72e63a9777d793fbbf57194d8ec4fb97bc1b`. The upstream fix closes the advisory's routes. It does not close the queue route or the two added routes.

**What the task contains.** Seven routes to one rule. The report names none of them.

| Route | What leaks | What must keep working next to it | Origin |
|---|---|---|---|
| 1. Deployment-scoped path model in the shared request processor (chat/completions and embeddings, including the `/engines` alias): the path value replaces the body model after the body check has run | a URL in the path becomes the outbound destination | ordinary deployment names, including ones with a provider prefix and a slash, still route; allowlisted destination hosts still route | advisory's own route |
| 2. The same path-model replacement in the separate image-generation handler | same, on image generation | ordinary image deployment names still route | advisory's own route (second implementation) |
| 3. Bracket-notation form fields on the file-upload route (`litellm_metadata[...]`, `metadata[...]`): at check time these are flat keys, so the body check does not see a destination | a destination or observability host reaches the provider call | form fields that do not choose a destination are still delivered; the operator's opt-in still lets callers pass these fields | advisory's own route |
| 4. The management connectivity test (`/health/test_connection`) merges the deployment's stored credentials under a caller-supplied destination field, and keeps a stored-credential reference | the configured key, or a reference that resolves to it, goes with a caller-chosen endpoint | a configured model named alone inherits its endpoint and credentials; a complete caller connection is tested as sent; under the operator's opt-in, a caller endpoint still inherits the configured credentials | advisory's own route |
| 5. The priority-queue chat route (`/queue/chat/completions`) never calls the request check | a URL-valued model in the body or query string reaches the provider | ordinary queue models and allowlisted hosts still route | real upstream code the fix left open |
| 6. The same bracket form handling extended to the `extra_body[...]` container, while the check still handles only the metadata prefixes | a destination in `extra_body` form fields reaches the provider | form fields in `extra_body` that do not choose a destination are still delivered, and still pass under the opt-in | code added for the task |
| 7. An Azure-compatible path-model route added to the moderations handler, copied from the other handlers | a URL in the path becomes the destination | ordinary moderation deployment names still route | code added for the task |

**Report given to the agent.** It is written as a real bug report:
- the system;
- the one example (route 1, as a `curl` request);
- the properties. No caller-supplied model or file identifier may become a URL-valued destination "however the request delivers it: request body, query parameter, URL path, or form field". The same holds for every caller-supplied parameter that names a destination or observability endpoint. The configured credentials rule reads: "Credentials configured for a deployment must never be sent to a destination the request chose." Finally, "Every route that accepts a model identifier obeys these rules, including management routes that test a deployment's connectivity";
- the contracts:
  - the refusal form (a client error, and no outbound request);
  - the field and container names the tests use;
  - preservation: ordinary names, allowlisted destinations and benign nested fields keep working, and "The explicit admin opt-in that lets callers supply their own connection parameters still works";
  - connectivity tests: a configured model named without any connection field inherits the configured endpoint and credentials, and a complete caller connection is tested as sent.

No route, file, function or count is named.

**Hidden tests.**
- **21 security test cases:**
  - route 1: 6;
  - route 2: 2;
  - route 3: 3;
  - route 4: 4;
  - route 5: 2 (body and query);
  - route 6: 2;
  - route 7: 2.
- **298 functional tests:**
  - 18 written for the task (9 routing, 4 form, 5 connectivity-test);
  - 280 of the project's own tests for the affected area: request checks (224), health endpoints (36), the Azure image routes (2), and the destination guard (18). The grader restores these from pristine copies.
- **How the tests drive the code.** They call the real FastAPI application in-process, with the provider call replaced by a recorder. They assert that an attack gets a client error and never reaches the provider. On the connectivity-test route they assert that the configured secret is not among the parameters handed downstream.
- **Reward:** the security pass fraction, or 0 if any functional test fails. Only 1.0 is a solve.

## 2. How we know the task is fair

| Check | Result |
|---|---|
| Vulnerable code (offline container) | security 0/21, functional 298/298. The scripted gate's vulnerable-state stage passed with the same counts |
| Reference fix (offline container) | 21/21 and 298/298, reward 1.0, in three consecutive identical runs. The scripted gate's reference stage passed |
| Blind fix (a fresh model sees only the report and the code) | not run |
| An alternative correct fix and a hardened fix, written differently from the reference (`pass-alt`, `pass-hardening`) | declared to pass; verified with the build checks below |
| The upstream advisory fix alone (`sf-published-only`) | fails security: the queue route, the `extra_body` form route and the moderations route stay open |
| A fix for each route left out in turn (`sf-no-image-path`, `sf-no-form-metadata`, `sf-no-extra-body-form`, `sf-no-health`, `sf-no-queue`, `sf-no-moderation`, `sf-landing-only`) | each fails the matching security tests |
| Other wrong fixes (`sf-body-only`, `sf-wrong-field`, `sf-crash-as-refusal`, `sf-form-check-in-handler`) | each fails security |
| Over-broad fixes (`ff-reject-all-destinations`, `ff-overbroad-health`) | each fails functional tests: the first breaks the operator allowlist, the second breaks credential inheritance on the connectivity test |
| Independent fairness review of every test against the report | verdict READY. Every "could a correct fix fail this test?" row is "no". The medium-risk rows are about discoverability: the report says "the explicit admin opt-in" without naming the setting. |

The build notes record 16 check patches, each verified as declared. Three were added later (`sf-example-host-only`, `sf-https-only`, `sf-health-crash-as-refusal`); they were written for a revised suite and were not run against the delivered tests. The scripted gate's stages passed in separate runs. A single complete gate report is not recorded.

## 3. Results, attempt by attempt

| Model | Attempt | Score | Security | Functional | Finish | Left open | Broke |
|---|---|---|---|---|---|---|---|
| DeepSeek | 1 | 0.0 | 21/21 | 297/298 | stopped on its own, 31 min | nothing | opt-in credential inheritance on the connectivity test |
| DeepSeek | 2 | 0.0 | 21/21 | 297/298 | stopped on its own, 67 min | nothing | the same |
| DeepSeek | 3 | 0.0 | 21/21 | 297/298 | stopped on its own, 43 min | nothing | the same |
| MiMo | 1 | 0.0 | 15/21 | 297/298 | time limit (2 h) | image route (2), moderations route (2), queue route body and query (2) | the same |
| MiMo | 2 | 0.0 | 21/21 | 297/298 | time limit (2 h) | nothing | the same |
| MiMo | 3 | 0.0 | 21/21 | 297/298 | time limit (3 h) | nothing | the same |

- All 6 broke the same legitimate behaviour: `test_operator_opt_in_restores_inheritance_for_a_caller_endpoint`.
- 5 of 6 closed all 21 security cases and failed on that one functional test alone.
- 1 of 6 (MiMo, attempt 1) also left three routes open: the image handler, the added moderations route and the queue route.
- None of the 297 other functional tests failed in any attempt.
- Two further MiMo attempts ended without a grade (one was cancelled after about 52 minutes, one was stopped before grading). They are not counted.

## 4. Why both models failed

### 4.1 The connectivity test's opt-in inheritance (all 6 attempts broke it)

The functional test turns on the operator setting `allow_client_side_credentials` and sends a configured model with a caller-supplied endpoint. It expects the configured key to be inherited. Every model reasoned from the credential rule and withheld the configured credentials whenever the request chose its own endpoint, whatever the opt-in said:
- DeepSeek, attempt 1. The audit: "when the request supplies api_base it uses request params only and drops all configured credentials, with NO allow_client_side_credentials check". Its own final summary reports this as verified: "With a local upstream and `allow_client_side_credentials: true`: caller `api_base` without a caller key produced no outbound request and no deployment secret."
- DeepSeek, attempt 2, added an opt-in check, but only around rejecting a stored-credential reference. The audit found that "the credential-inheritance clearing … runs unconditionally, ignoring the opt-in". Its summary: "a caller endpoint causes config credentials and stored-credential references to be withheld".
- DeepSeek, attempt 3, in its summary: "caller-chosen endpoints never receive configured credentials."
- MiMo, attempt 2, replaced the merge with `if request_selects_connection(...): litellm_params = dict(request_litellm_params)`, which has no opt-in branch.
- MiMo, attempt 3, wrote a merge helper whose docstring states the rule it applied: "A request that brings its own destination is tested against that destination without anything the deployment configured."
- MiMo, attempt 1, was cut off with the same behaviour in place.

The reference fix returns the full configured parameters when the opt-in is set and strips them otherwise. Each audit rated the failure "stated in the instruction", found that a correct fix passes, and judged it a genuine failure. The test reached a normal assertion (`None == 'sk-configured-secret'`) rather than crashing.

### 4.2 What MiMo left open (attempt 1)

At its 2-hour limit, MiMo had hardened the chat and embeddings path-model check. It had not yet extended it to the image-generation handler, the moderations route or the queue route. The audit: "an incomplete-but-progressing correct-direction fix", with 265 tool calls and no idle stall or provider outage. In attempts 2 and 3 MiMo closed these routes.

### 4.3 What they got right

Five of six attempts closed every security case. That covers all seven routes, including the queue route the upstream fix never touched and both added routes. Several attempts also hardened neighbouring paths: the router's credential merge, cached provider clients, and stored-credential resolution. The failures do not come from missing the attack. They come from the coupled legitimate behaviour on the connectivity-test route, and on MiMo's side, from not finishing within the limit.

### 4.4 Model profiles on this task

- **DeepSeek V4.1 Flash:** fast (31–67 minutes), wide in scope. It found every route in all three attempts, then applied the credential rule on the connectivity test without an exception for the opt-in.
- **MiMo-V2.6-Pro:** worked until the deadline every time (265, 542 and 394 tool calls in the three counted attempts, last activity within a minute of the limit). It used much of its time on full-suite test runs and live checks. Even with 3 hours it did not change the connectivity-test behaviour.

## 5. Evaluation setup

- Harness: Harbor with the Claude Code agent.
- Models: DeepSeek V4.1 Flash (reasoning effort max) and MiMo-V2.6-Pro, with 3 counted attempts each. The time limit is 2 hours per attempt; MiMo's third counted attempt ran with a 3-hour limit.
- Offline: the agent could reach only the model APIs, and web tools were disabled. The repository has no git history, so no later fix commit is present. The hidden tests are not in the agent's environment, and grading starts after the agent stops.
- Every counted attempt was audited before it counted, by a separate Claude Opus 5.5 auditor that read the transcript, final code and grader output. It checked:
  - no access to the hidden tests and no lookups;
  - no tool calls inside the grading window;
  - the score reflects real defects in the model's code.

  All six were rated trustworthy, model-failed, high confidence.
- What counts: a run that reaches its time limit is graded on its code at that moment and counts as a failure. A run cut off by a provider or infrastructure fault is not counted.

## 6. Questions you may ask

**Is the failure the model's fault and not the task's?** The reference fix scores 1.0, and so do the alternative and hardened fixes. The fairness review rated every test fair (READY). Each of the six audits judged the deciding failure "stated in the instruction" and found that a correct fix passes.

**Does it hinge on one test?** For five of the six attempts, yes. They passed every security case and every other functional test and failed only `test_operator_opt_in_restores_inheritance_for_a_caller_endpoint`. All three DeepSeek attempts and MiMo's second and third would score 1.0 without that test. Only MiMo's first attempt also failed security.

**Could the model have seen the answer?** The queue route and the two added routes are not covered by the published fix. The agent could not reach the internet or the hidden tests, and each audit checked the transcript for lookups and route-arounds.

**What does a 0.0 mean here?** A legitimate behaviour was broken, since any functional failure scores 0. In this task the score does not show how much of the security side was fixed: five of the six 0.0 attempts had all 21 attack cases closed.

## Appendix: what is in the task package

| What | Contents |
|---|---|
| Task | report (`instruction.md`), `task.toml`, environment (Dockerfile at the pinned commit plus `injection.patch` for routes 6 and 7), reference fix (`solution/fix.patch`), hidden tests (21 security cases, 298 functional), `score.py` |
| Validation | build notes and manifest, 19 check patches (wrong-fix, over-broad and passing variants), fairness review |
| Attempts | per attempt: score, per-test results, final code, transcript and the audit's findings |

**Internal slug:** `litellm-ds`. Counted attempts:
- DeepSeek:
  - `litellm-ds-deepseek-r1-20261019-100033-n001`
  - `litellm-ds-deepseek-r2-20261019-103318-n002`
  - `litellm-ds-deepseek-r3-20261019-114118-n003`
- MiMo:
  - `litellm-ds-mimo-r1-20261019-124919-n001`
  - `litellm-ds-mimo-r2-20261019-145142-n002`
  - `litellm-ds-mimo-r4-20261020-005629-n001`

Uncounted: `litellm-ds-mimo-r3-…` (cancelled, no grade) and `litellm-ds-mimo-r5-…` (no grade).

**Sources used:**
- the delivered task `tasks/litellm-outbound-destination-ssrf/` and its `RESULTS.md` section;
- the build record `build/litellm-ds/` (`notes.md`, `manifest.json`, `FAIRNESS.md`, `checks/`, gate and run logs);
- per attempt: `result.json`, `verifier/results.json`, `final-code/changes.patch`, the transcript, and the recorded `POSTMORTEM.json`.
