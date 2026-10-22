# grav-config-secret-theme-alias-exfiltration — a task that DeepSeek V4.1 Flash and MiMo-V2.6-Pro both fail 3/3

**Status of 2026-10-22: both-model breaker, audit-confirmed; not yet delivered.** The counted attempts were run on 2026-10-22 (05:12–09:30 UTC). This task was produced by a post-trial **hardening** pass on a previously-solved task (see "Provenance" below). Sources: the task as trialled, the hardening/gate records, the fairness review, and the independent audit of every counted attempt (per-attempt transcript, final code and per-test results).

## Summary

- **Result: both target models failed all 3 counted attempts.**
  - DeepSeek V4.1 Flash: 0.0, 0.8696, 0.0.
  - MiMo-V2.6-Pro: 0.6087, 0.0, 0.6957.
- Every counted attempt was audited independently (Opus-5.5, high reasoning): all 6 were judged **trustworthy** and a **genuine model failure**, high confidence. No contamination, no timeout, no harness/infra fault.
- The task is **Grav**, a real PHP flat-file CMS, hardened around a configuration/secret-exfiltration flaw (CWE-200-class information exposure through template rendering).
- Why both models fail: every attempt redacts denied configuration values on the **literal** denied path, but misses one **close-variant reach-path** — the legacy `theme` alias that mirrors `themes.<name>`. One security test (`ThemeSettingsAliasTest`) fails in all 6 attempts; some attempts additionally break a legitimate-use functional test with an over-broad redactor.

## 1. The task

**Vulnerability.** Grav renders configuration into templates. A value an administrator has marked hidden (for example a key under `themes.<theme>.integrations`) must not leak into page output through any variable that exposes configuration. The flaw: redaction applied to a configuration key on its canonical path does not follow the value when the engine copies a subtree onto a **legacy alias**. When `themes->load()` runs, it copies `themes.<active-theme>` onto the top-level `theme` key; a value denied on `themes.<theme>.integrations` is then reachable, un-redacted, through `theme`, `theme_var()`, `header_var()` and `theme_config()`.

- **Project and language:** Grav (PHP).
- **Rule given to the agent (goal-only instruction):** redact any configuration value that is hidden from content, **however the value is reached or rendered**, and **fix the flaw and its close variants** — while keeping legitimate template, header and configuration access working.

**Hidden tests.** 46 security tests and 40 functional tests. The security tests seed their own marker secrets and assert only on **rendered output** (the secret must not appear through any exposed variable; any refusal shape is accepted). The functional tests assert that legitimate template/header/config access keeps working. **Reward** = 1.0 only if every test passes; otherwise the share of security tests passed, **forced to 0 if any functional test fails**.

The consistent failing security test is **`ThemeSettingsAliasTest`**: it denies the canonical `themes.<theme>.integrations`, calls `themes->load()` (which creates the `theme` copy), and asserts the secret does not leak through the `theme` variable / `theme_var()` / `header_var()` / `theme_config()`. The contrast test that every attempt **passes** is `StandardVariableExfiltrationTest`, which denies the **literal** `theme.integrations` key — so the models redact literal denied paths correctly, but miss the alias copy.

## 2. How we know the task is fair

- **Scripted gate — all four stages pass** before the counted attempts: the hardened (vulnerable-for-the-task) code fails the security tests and passes the functional tests; the **reference fix scores 1.0**; wrong-fix patches fail the matching security tests; static/conformance checks pass.
- **Reference fix.** `Grav\Common\Security::expandThemeAliasDeniedPaths` expands denied paths across the legacy alias, so a denied value is redacted whether it is reached through `themes.<name>` or through `theme`. The reference passes all 46 security and 40 functional tests.
- **Fairness review** (separate model, every hidden test checked against the instruction): **GATE_A READY**. Every security test traces to the stated Security property ("any configuration value hidden from content … however the value is reached or rendered") and the close-variants clause; every functional test traces to a keep-working clause. (Flagged `NEEDS_HUMAN_REVIEW: YES` for a routine author confirmation; the audit below resolved it.)
- **Independent audit of every counted attempt** (Opus-5.5, high): all 6 **trustworthy / model-failed / high**. The audit specifically confirmed this is **not a test-fault** — the failing tests are purpose-built CWE security tests that seed their own marker secrets and assert on externally-observable rendered output; they do not restore pristine project unit tests that pin the reference fix's internal architecture.

## 3. Results, attempt by attempt

| Model | Attempt | Score | Note |
|---|---|---|---|
| DeepSeek | 1 | 0.0 | missed the alias test **and** broke a legitimate-use functional test (trusted-template config access) → functional fail forces 0 |
| DeepSeek | 2 | 0.8696 | **clean run — functional 40/40**; fails **only** `ThemeSettingsAliasTest` → 40/46 security = 0.8696 |
| DeepSeek | 3 | 0.0 | missed the alias test; a functional regression forces 0 |
| MiMo | 1 | 0.6087 | missed the alias test plus further security gaps; functional passed |
| MiMo | 2 | 0.0 | over-broad redactor broke ~5 legitimate page-header dumps → functional fail forces 0 |
| MiMo | 3 | 0.6957 | missed the alias test; functional passed |

- The **cleanest** evidence is DeepSeek attempt 2: a run with **all 40 functional tests passing** that still fails, because it misses exactly the alias close-variant. That isolates the breaker's core.
- Rewards are **heterogeneous** across the 6 runs (not a single deterministic partial), consistent with genuine, model-specific shortfalls rather than one brittle test.

## 4. Why both models failed

Every attempt built a redactor that handles **denied values on their literal path** across every exposed view — and every attempt missed the **legacy-alias copy**. When `themes->load()` mirrors `themes.<theme>` onto the `theme` key, a value denied only on the canonical path is reachable again through `theme` / `theme_var()` / `header_var()` / `theme_config()`. The instruction's Security property ("however the value is reached or rendered") and its "fix the close variants" constraint put this alias squarely in scope; the reference handles it with `expandThemeAliasDeniedPaths`. Two attempts additionally over-corrected and broke legitimate configuration/header access (functional regressions that force the reward to 0). The failures are not about finding the flaw — they are about following the denied value across one more reach-path.

## 5. Evaluation setup

- Harness: Harbor with the Claude Code agent.
- Models: DeepSeek V4.1 Flash and MiMo-V2.6-Pro. 3 counted attempts each, 2-hour agent budget (`CWE_AGENT_TIMEOUT_MULT=1.5`).
- Offline agent phase: no web tools; hidden tests staged only after the agent stops.
- Every counted attempt was audited before it counted (Opus-5.5, high): no access to hidden tests, no lookups, grading after the agent stopped, the score reflects real defects in the model's code.
- A run that uses its full budget without solving counts as a failure; a run cut off by a provider/network outage is not counted. No attempt here timed out or was cut off.

## 6. Questions you may ask

**Is the failure the model's fault and not the task's?** The reference fix scores 1.0; the gate passed all four stages; the fairness review traced every test to the instruction; and an independent per-attempt audit found all 6 trustworthy model-failures (high). One clean run (DeepSeek 2, functional 40/40) fails on the single alias test.

**Does it hinge on one test?** The consistent miss is `ThemeSettingsAliasTest`, but the rewards are heterogeneous and two runs fail on separate over-broad-fix functional regressions — so it is not one brittle test carrying every run.

**Could the model have seen the answer?** The agent had no network and no access to the hidden tests; the audit checked every transcript.

## Provenance (hardening)

This task was produced by a **post-trial hardening pass** on 2026-10-21→22: a previously-solved Grav task was hardened (a harder, in-scope close-variant — the theme alias — was added and the task re-gated) and then re-trialled, at which point both models failed 3/3. Note for the file: the hardening approach yielded ~6% both-model breakers across the batch and is **not** being adopted as the production path; this task is kept because it is an audit-confirmed, fair both-model breaker on its own merits.

## Appendix

- **Internal slug:** `grav-ds`.
- **Counted runs (job folders):** `grav-ds-deepseek-r1-20261022-051235-n001`, `grav-ds-deepseek-r2-20261022-053048-n002`, `grav-ds-deepseek-r3-20261022-055352-n003`, `grav-ds-mimo-r1-20261022-061850-n004`, `grav-ds-mimo-r2-20261022-081225-n005`, `grav-ds-mimo-r3-20261022-092621-n006`.
- **Build record** (commit pins, environment/injection patch, reference `fix.patch`, full gate check-patch table, fairness review, per-attempt evidence and audit verdicts): `build/grav-ds/` on the build host. Those specifics are not duplicated here; this report is written from the audit evidence and the trialled task.
- **Audit verdict:** 6/6 trustworthy, attribution model-failed, confidence high.
