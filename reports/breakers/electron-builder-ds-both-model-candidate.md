# electron-builder-ds — a DeepSeek-only result (DeepSeek fails, MiMo solved) — with a flip to watch

**Status of 2026-10-20. PROVISIONAL — not a confirmed both-models breaker, and the current task version needs reconciling (see the box below).** On the task version that carried the given classification (the 2026-10-19 fairness-revised build, 16 security tests), this is a *DeepSeek-only* result: **DeepSeek V4.1 Flash failed every counted attempt** (best ≈0.94, never 1.0) while **MiMo-V2.6-Pro solved it** (reached 1.0). This is the mirror image of prompty-path-read-inj (there MiMo fails and DeepSeek solves). No per-attempt transcript audit has been run, so the why-DeepSeek-fails analysis below is **inferred, not confirmed**.

> **Discrepancy you asked me to verify — flagged, not resolved.** The brief said that after the 2026-10-20 §2 upgrade the task "stayed DeepSeek-only (unchanged)." The VM does **not** show that. The post-upgrade re-trial (18 security tests) has **both** models failing all 3: DeepSeek 0.7222/0.6111/0.7222 and MiMo 0.6111/0.6111/0.6111 — and `auto_trial.out` records `ACCEPTED: deepseek: failed (0p/3f/0e); mimo: failed (0p/3f/0e)`. MiMo, which solved the 16-test version, no longer solves the 18-test version. So on the **current** task version this looks like a **both-models candidate**, not DeepSeek-only. Nothing is officially graded either way: `build/audit_results.py` lists both models as "no graded run (+3 awaiting audit)". This needs the caller's decision and a post-run audit before it is classified.

Sources (VM, read-only): `build/electron-builder-ds/manifest.json`, `tasks/electron-builder-ds/instruction.md`, `build/electron-builder-ds/FAIRNESS.md`, `notes.md`, `runs_deepseek.log`, `runs_mimo.log`, `auto_trial.out`, the `[trial-done …]` line in `build/pipeline/auto_trial.log`, and `build/audit_results.py`. The per-test breakdown and transcript audit that the jackson report relies on have **not** been produced for this task.

## Summary

- **Result on the 2026-10-19 version (16 security / 165 functional), the one the given classification describes — DeepSeek-only:**
  - DeepSeek V4.1 Flash: never reached 1.0. Its logged rewards across runs n001–n003 were 0.875, 0.6875, 0.875, 0.875, 0.75, 0.9375 — best **0.9375 = 15/16 security** (one route left open), all functional passing. (`runs_deepseek.log` logs two reward lines per run slot here, so I cannot cleanly carve out exactly three counted scores — I report the honest range and the best.)
  - MiMo-V2.6-Pro: 0.625 (10/16) on run 1, then **1.0 on run 2 — solved**, early-exit.
  - So on that version it is **not** a breaker (a breaker needs both models to fail all 3). It is a lead that separates the two models.
- **Result on the 2026-10-20 §2 upgrade version (18 security / 165 functional), the current task — both fail (see the box above):**
  - DeepSeek: 0.7222 (13/18), 0.6111 (11/18), 0.7222 (13/18) — 3 fails, best 0.7222.
  - MiMo: 0.6111 (11/18), 0.6111 (11/18), 0.6111 (11/18) — 3 fails, no solve.
  - `auto_trial.out` accepted this as both-failed; `audit_results.py` still shows it as awaiting audit (ungraded).
- Every counted attempt on both versions finished on its own (`cause=None`, `finish=success`, no timeout); DeepSeek ran ~20 min/attempt, MiMo ~40–112 min/attempt.
- **No attempt scored 0.0** on either version, so no model broke a legitimate behaviour (any functional failure forces reward 0); the scores differ only in how many of the security routes each model closed.
- **The upgrade is the lever that changed the classification.** The §2 upgrade added two security tests over real, unmodified upstream code — the embedded block-map trailing-range route (T8) and the full update download through the Electron executor (a second caller of the same redirect decision as T1). MiMo's 16-test solve did not cover these; on the 18-test version MiMo drops to 11/18 and fails. This flip is exactly why the "stayed DeepSeek-only" premise does not hold on the VM.

## 1. The task

**Vulnerability (CWE-200 / credential exposure across a trust boundary).** electron-userland/electron-builder, GHSA-P2F4-R6V6-J797 / CVE-2026-54673, Node/TypeScript, at the pinned vulnerable commit `8a035f83` (direct parent of the upstream fix `22a7532b`). The product is a suite of desktop-app build/publish/update tools whose network requests carry operator-supplied credentials, and which are handed secrets for the services they use. Two real exposures: a credential supplied for one origin reached a **different** origin after a server redirect, and a configured secret was written in clear text into diagnostic output.

**The rule (as given to the agent).** A credential is bound to the origin (scheme, host, port) it was supplied for and must never travel to another origin on any hop or by any path — however the credential is expressed (standard or application-specific header in any spelling/case, or connection-level `options.auth`). After a cross-origin redirect the request may continue only **without** the credential, and must still complete by its normal path or an equivalent fallback (no crash, no breaking a later legitimate request). Separately, no secret may appear in clear text in any diagnostic output (error message or `DEBUG=electron-builder`), whatever the field/option/variable is named. Same-origin redirects and http→https upgrades on the same host keep their credentials; ordinary non-credential headers still travel cross-origin; everything else works as today. The instruction names no file, function, route or flaw count, and forbids special-casing examples, modifying tests, and looking up the upstream fix.

**The routes to the same rule (none named in the instruction).** This is an INJECTED-track task (`pattern: A+B`): real upstream sinks plus injected sibling code of the same class. From the manifest's trap catalogue:

| Trap | Kind | Where / shape | Why a solver might skip it |
|---|---|---|---|
| T1 — core redirect, credential shapes | real (advisory landing) | `httpExecutor.ts:323` `prepareRedirectUrlOptions`; capitalised/app-specific headers, cookies, proxy creds, Basic auth via `options.auth`, port-only origin change | the report's example is a GitLab token; adding that one header + a case-insensitive check looks sufficient |
| T2 — block-based (differential) download redirects | real upstream, uncovered | `DifferentialDownloader.ts:260-264`, `multipleRangeDownloader.ts:73,96`; single-range and default multi-range | "a blockmap optimisation in another package; comments say Electron handles redirects" |
| T8 — embedded block-map trailing range | real upstream, uncovered (**added by the upgrade**) | `DifferentialDownloader.ts:274-308` `readRemoteBytes/request()`; trailing byte-range read redirected to another origin | the two obvious range paths look like the whole differential download; this helper is reached before them |
| T3 — runtime redaction | real (fix site) | `httpExecutor.ts:90,209,586`; JSON request-body debug + JSON error text with `private_token`/`apiKey`/`clientSecret`/`passphrase` | "a logging concern; the existing redactor already hides token/password names" |
| T4 — build/config redaction | real (fix site) | `util.ts:51,186,192`, `gitHubPublisher.ts:61`, `gitlabPublisher.ts:49`; failed-command stdout/stderr, echoed invalid publish token | "build-time command output / config validation looks unrelated to an HTTP redirect" |
| T5–T7 — injected Gitea publisher siblings | injected | `giteaPublisher.ts:39,46,78`; upload 307-to-storage redirect, echoed malformed token, debug of resolved config | "uploads/config look like a publisher concern, not the reported redirect"; the published fix never enters this file |

**Scoring.** Reward = security pass fraction, **0 if any functional test fails**, 1.0 = solve. The 2026-10-19 version had 16 security + 165 functional; the 2026-10-20 upgrade added 2 security tests (T8 embedded block-map, and the Electron full-download redirect — a second caller of T1's shared decision), for 18 security + 165 functional. So on the 18-test version 0.6111 = 11/18 security closed, 0.7222 = 13/18, with all functional passing.

## 2. Fairness status — READY (round-2 review), but it predates the upgrade

`FAIRNESS.md` is a round-2 review and its verdict is **"READY for trial. No high items."** Round 1's six required changes are all present and correct, the instruction names no file/function/trap/variant-list/flaw-count, and the nop/oracle/pass/fail patch declarations match the code read. The residual items are non-blocking: fixed-name-list leniency (a header or field list covering exactly the tested names still scores 1.0 — tighten by adding untested names if the client wants zero tolerance for shortcut fixes), a shared-headers in-place-mutation leniency, one medium-low fairness note on the differential no-redirect `Range` test (a full-download fallback is safe but fails that test; defended by S7), and a couple of low hint/realism flags.

**Important caveat:** this review was done against the **16-security** suite ("Suite counts: 16 security, 165 functional"). The two tests the 2026-10-20 upgrade added (T8 embedded block-map; the Electron full-download redirect) are **not** covered by this fairness review — they were pre-verified only by targeted in-container patch runs (`notes.md`), and the manifest records the "full launcher re-gate" as **pending**. So the fairness sign-off does not yet extend to the version on which both models now fail.

## 3. Why DeepSeek fails and MiMo solved — INFERRED, not audited

No transcript or per-test audit has been run, so the following is inference from the reward fractions and the trap catalogue, not confirmed findings:

- **DeepSeek (16-test version):** best 0.9375 = 15/16 — it closed nearly everything and left exactly **one** route open, every run, while breaking nothing (no 0.0). This matches DeepSeek's profile elsewhere (jackson, prompty): it audits widely, then leaves one route it judges out of scope — plausibly one of the far redaction sites (T3/T4) or an injected Gitea sibling (T5–T7). *Which* route is unconfirmed without the per-test breakdown.
- **MiMo (16-test version):** 0.625 then **1.0** — found the remaining routes on a second pass and solved. This confirms the 16-test version was solvable and the DeepSeek miss there was a real capability gap, not a broken test.
- **The upgrade flip (18-test version):** both models sit at 11–13/18. The two added tests (T8 trailing-range embedded block map; the Electron full-download caller of the shared redirect decision) are precisely the kind of "uncovered real upstream route reached by a non-obvious caller" that the earlier MiMo solve did not have to cover. The inference is that MiMo's 16-test fix closed the visible routes but not these two, dropping it to 11/18. Unconfirmed until an audit reads the attempts.

## 4. What is needed before this can be trusted or reported

1. **Reconcile the classification first.** The brief's premise (DeepSeek-only after the upgrade) is contradicted by the VM: the current (18-test) counted re-trial has both models failing 3/3. Decide which task version the report is about — the 16-test version (DeepSeek-only lead) or the current 18-test version (both-models candidate). They give different verdicts.
2. **Run the post-run audit** (Opus 5.5-high, per the standing rule) on all counted attempts for both models; `audit_results.py` currently shows both as "no graded run (+3 awaiting audit)", so nothing is officially graded yet.
3. **Extract per-test results** to confirm which route DeepSeek leaves open on the 16-test version, and which routes both models miss on the 18-test version (the inference in §3).
4. **Complete the full launcher re-gate for the upgraded (18-test) build** and extend the fairness review to the two added tests (T8 and the Electron full-download redirect); the round-2 fairness sign-off only covers the 16-test suite.
5. Only then classify: a DeepSeek-only lead (16-test), a both-models breaker (18-test), or a solved task. It is none of these with confidence yet.

## 5. Evaluation setup

- Harness: Harbor with the Claude Code agent.
- Models: DeepSeek V4.1 Flash and MiMo-V2.6-Pro; up to 3 counted attempts each, early-exit on a solve (MiMo early-exited after its run-2 solve on the 16-test version).
- Offline: model APIs only, web tools disabled, no git history; the hidden tests are copied in only after the agent stops. Reward = security pass fraction, 0 if any functional test fails, 1.0 = solve.
- A timeout would count as a failure; an attempt cut off by a provider or network outage is not counted. Every counted attempt here finished on its own (`cause=None`).
- Track: INJECTED (`pattern: A+B`) — real upstream sinks (T1–T4, T8) plus injected Gitea-publisher siblings (T5–T7) of the same credential-exposure class.
