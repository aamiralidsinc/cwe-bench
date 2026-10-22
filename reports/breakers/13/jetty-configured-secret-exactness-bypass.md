# jetty-configured-secret-exactness-bypass — a task that DeepSeek V4.1 Flash and MiMo-V2.6-Pro both fail 3/3

**Status of 2026-10-22: both-model breaker, audit-confirmed; not yet delivered.** The counted attempts were run on 2026-10-22 (05:34–11:00 UTC). This task was produced by a post-trial **hardening** pass on a previously-solved task (see "Provenance" below). Sources: the task as trialled, the hardening/gate records, the fairness review, and the independent audit of every counted attempt (per-attempt transcript, final code and per-test results).

## Summary

- **Result: both target models failed all 3 counted attempts.**
  - DeepSeek V4.1 Flash: 0.8889, 0.8889, 0.8889.
  - MiMo-V2.6-Pro: 0.8889, 0.8889, 0.8889.
- Every counted attempt was audited independently (Opus-5.5, high reasoning): all 6 were judged **trustworthy** and a **genuine model failure**, high confidence. No contamination, no timeout, no harness/infra fault.
- The task is **Eclipse Jetty**, a real Java web server, hardened around a credential-exactness flaw (CWE-287-class authentication weakness): a value that is *not* the exact configured secret can authenticate.
- Why both models fail: every attempt fixes the credential-**representation** layer (charset collapse) and clears 8 of 9 security tests plus all functional tests, but misses the credential-**configuration** layer. One security test (`SecurityConfiguredSecretExactnessTest::valueThatDropsAConfiguredCharacterIsRejected`) fails in all 6 attempts → 8/9 security = **0.8889**, identical across every run.

## 1. The task

**Vulnerability.** A configured account secret must be matched **exactly**: no value other than the exact secret may authenticate, however the value is presented, and however the account's secret is held. There are two distinct reach-paths to a near-miss authentication:

1. **Representation layer** — a credential that is not faithfully representable in the stored charset (ISO-8859-1 → UTF-8 collapse) can be silently normalised so that a different input matches. Fixed in `Credential` / `DigestAuthenticator` / `BasicAuthenticator` by `canEncode()`-style faithfulness guards.
2. **Configuration layer** — `PropertyUserStore` applies `.trim()` to the configured credential when it loads it, so a configured secret `"pa? "` (with a deliberate trailing space) is stored as `"pa?"`. The near-miss value `"pa?"` — which **drops a configured character** — then authenticates.

- **Project and language:** Eclipse Jetty (Java).
- **Rule given to the agent (goal-only instruction):** no value other than the exact configured secret may authenticate, however presented and however the account's secret is held; **fix the flaw and its close variants**, keep legitimate authentication working.

**Hidden tests.** 9 security tests and 14 functional tests. The security tests assert only **externally-observable HTTP behaviour** — a near-miss credential yields a client error (`isClientError()`) and is **not** authenticated (`!authenticatedAs(...)`); the exact credential still authenticates. The functional tests assert legitimate authentication keeps working. **Reward** = 1.0 only if every test passes; otherwise the share of security tests passed (with functional all passing → 8/9 = 0.8889).

The single failing security test, in all 6 attempts, is **`SecurityConfiguredSecretExactnessTest::valueThatDropsAConfiguredCharacterIsRejected`**: it configures the secret `"pa? "` (trailing space written as an explicit properties escape, so the space is part of the value, not layout) and asserts that the non-exact value `"pa?"` is **rejected**.

## 2. How we know the task is fair

- **Scripted gate — all four stages pass** before the counted attempts: the hardened code fails the security tests and passes the functional tests; the **reference fix scores 1.0**; wrong-fix patches fail the matching security tests; static/conformance checks pass.
- **Reference fix.** Removing the `.trim()` on the loaded credential in `PropertyUserStore.java` (so the configured trailing space is preserved) makes the near-miss value fail the exactness check. The reference passes all 9 security and 14 functional tests. This is a **product-code** change squarely within the stated exactness property — not a reliance on any internal signature.
- **Fairness review** (separate model): **GATE_A READY**. Every security test traces to the stated exactness property and the close-variants clause; every functional test traces to a keep-working clause. (Flagged `NEEDS_HUMAN_REVIEW: YES` for a routine author confirmation; the audit below resolved it.)
- **Independent audit of every counted attempt** (Opus-5.5, high): all 6 **trustworthy / model-failed / high**. The audit specifically confirmed the failing test is a **purpose-built CWE security test that asserts only external HTTP behaviour** (`isClientError` + `!authenticatedAs`) and **pins no internal method/constructor signature** — i.e. it is **not** a restored pristine project unit test that over-constrains the fix's internal design.

## 3. Results, attempt by attempt

| Model | Attempt | Score | Security | Functional | The one miss |
|---|---|---|---|---|---|
| DeepSeek | 1 | 0.8889 | 8/9 | 14/14 | configuration-layer `.trim()` exactness variant |
| DeepSeek | 2 | 0.8889 | 8/9 | 14/14 | same |
| DeepSeek | 3 | 0.8889 | 8/9 | 14/14 | same |
| MiMo | 1 | 0.8889 | 8/9 | 14/14 | same |
| MiMo | 2 | 0.8889 | 8/9 | 14/14 | same |
| MiMo | 3 | 0.8889 | 8/9 | 14/14 | same |

Every attempt fixed the representation-layer flaw (clearing the other 8 security tests and all 14 functional tests) and missed exactly the configuration-layer variant. Notably, DeepSeek attempt 1 **read `PropertyUserStore.java`** during the run and still did not edit the `.trim()`.

## 4. Why both models failed

Both models correctly identified and fixed the credential-**representation** flaw (the charset-collapse layer, with `canEncode()`-style faithfulness guards in `Credential`, `DigestAuthenticator`, `BasicAuthenticator`). That is a real, non-trivial fix — and it passes 8 of 9 security tests and every functional test. What all 6 attempts missed is the **second reach-path**: `PropertyUserStore` trims the configured credential at load time, so a configured trailing space is silently dropped and a value that omits it authenticates. The instruction's exactness property ("no value other than the exact configured secret … however the account's secret is held") and the "fix the close variants" constraint put the configuration layer in scope; the reference removes the `.trim()`. The identical 0.8889 across all 6 runs reflects one shared blind spot — the credential-**configuration** layer — not a brittle or over-constrained test.

*(Minor, non-decisive nuance, recorded in each verdict: the instruction's "Magnitudes" clause frames the headline attack as a charset-unrepresentable character; but the broad Security-property wording, the close-variants constraint, and the deliberate trailing-space properties escape keep the configuration-layer variant clearly in scope — hence high confidence, not medium.)*

## 5. Evaluation setup

- Harness: Harbor with the Claude Code agent.
- Models: DeepSeek V4.1 Flash and MiMo-V2.6-Pro. 3 counted attempts each, 2-hour agent budget (`CWE_AGENT_TIMEOUT_MULT=1.5`).
- Offline agent phase: no web tools; hidden tests staged only after the agent stops.
- Every counted attempt was audited before it counted (Opus-5.5, high): no access to hidden tests, no lookups, grading after the agent stopped, the score reflects real defects in the model's code.
- A run that uses its full budget without solving counts as a failure; a run cut off by a provider/network outage is not counted. No attempt here timed out or was cut off.

## 6. Questions you may ask

**Is the failure the model's fault and not the task's?** The reference fix scores 1.0; the gate passed all four stages; the fairness review traced every test to the instruction; and an independent per-attempt audit found all 6 trustworthy model-failures (high). The failing test asserts only external HTTP behaviour and pins no internal signature, so it is not an over-constrained project test.

**Does it hinge on one test?** Yes, one test fails in every run (`valueThatDropsAConfiguredCharacterIsRejected`) — but the audit confirmed that test is fair, in-scope, and fixed by a product-code change the reference makes; and both model families independently missed the same real second layer. The 0.8889 is a correct-but-incomplete fix, not a brittle grader.

**Could the model have seen the answer?** The agent had no network and no access to the hidden tests; the audit checked every transcript. DeepSeek attempt 1 even read the relevant file and still did not make the fix.

## Provenance (hardening)

This task was produced by a **post-trial hardening pass** on 2026-10-21→22: a previously-solved Jetty task was hardened (the second, configuration-layer reach-path was added and the task re-gated) and then re-trialled, at which point both models failed 3/3. Note for the file: the hardening approach yielded ~6% both-model breakers across the batch and is **not** being adopted as the production path; this task is kept because it is an audit-confirmed, fair both-model breaker on its own merits.

## Appendix

- **Internal slug:** `jetty.project-ds`.
- **Counted runs (job folders):** `jetty.project-ds-deepseek-r1-20261022-053400-n001`, `jetty.project-ds-deepseek-r2-20261022-055933-n002`, `jetty.project-ds-deepseek-r3-20261022-062431-n003`, `jetty.project-ds-mimo-r1-20261022-065442-n004`, `jetty.project-ds-mimo-r2-20261022-090643-n005`, `jetty.project-ds-mimo-r3-20261022-104102-n006`.
- **Build record** (commit pins, environment/injection patch, reference `fix.patch`, full gate check-patch table, fairness review, per-attempt evidence and audit verdicts): `build/jetty.project-ds/` on the build host. Those specifics are not duplicated here; this report is written from the audit evidence and the trialled task.
- **Audit verdict:** 6/6 trustworthy, attribution model-failed, confidence high.
