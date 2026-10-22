# CWE-bench confirmed both-model breakers (VM running register)
Verdicts authoritative from build/audit_results.py only. "Shipped" = already in client repo.

| # | task | DeepSeek | MiMo | audit | status |
|---|------|----------|------|-------|--------|
| 1 | protobuf.js-ds | failed 0/3 | failed 0/3 | trusted | SHIPPED |
| 2 | seaweedfs-ds | failed 0/3 | failed 0/3 | trusted | SHIPPED |
| 3 | electron-builder-ds | failed 0/3 | failed 0/3 | trusted | SHIPPED |
| 4 | litellm-ds | failed 0/3 | failed 0/3 (timeouts) | trusted | SHIPPED |
| 5 | jackson-databind-sib2 | failed 0/3 | failed 0/3 | trusted | SHIPPED |
| 6 | mockoon-ds | failed 0/3 [0.9259,0.963,0.9259] | failed 0/3 [0.9259,0.9259,0.963] | trusted model-failed high (6/6) | CONFIRMED 2026-10-21 — NOT yet in client repo; user to add+commit |
| 7 | hubuum-client-rust-ds | failed 0/3 [0,0,0] | failed 0/3 [0,0,0] | trusted model-failed high (6/6) | CONFIRMED 2026-10-21 — NOT yet in client repo; user to add+commit |
| 8 | siyuan-ds | failed 0/3 [0,0,0] | failed 0/3 [0,0,0] (incl genuine 2h timeout) | trusted model-failed high (6/6) | CONFIRMED 2026-10-21 — NOT yet in client repo; user to add+commit |
| 9 | theia-ds | failed 0/3 [0,0,0] | failed 0/3 [0,0,0] (2 genuine 2h-cap timeouts) | trusted model-failed high (6/6) | CONFIRMED 2026-10-21 — NOT yet in client repo; user to add+commit |
| 10 | openbao-ds | failed 0/3 [0,0,0] | failed 0/3 [0,0,0] | trusted model-failed high (6/6) | CONFIRMED 2026-10-21 — NOT yet in client repo; user to add+commit |
| 11 | tinacms-ds | failed 0/3 [0,0,0] | failed 0/3 [0.9726,0,0] | trusted model-failed high (6/6) | CONFIRMED 2026-10-21 — NOT yet in client repo; user to add+commit |
| 12 | knowns-ds | failed 0/3 [0.8929,0.8571,0.8571] | failed 0/3 [0.8571,0.8571,0.9643] | trusted model-failed (6/6; 5 high, 1 medium) | CONFIRMED 2026-10-21 — NOT yet in client repo; user to add+commit |
| 13 | yamcs-ds | failed 0/3 [0,0,0] | failed 0/3 [0,0,0] (incl genuine 2h timeout) | trusted model-failed high (6/6) | CONFIRMED 2026-10-21 — NOT yet in client repo; user to add+commit |
| 14 | grav-ds | failed 0/3 [0,0.8696,0] | failed 0/3 [0.6087,0,0.6957] | trusted model-failed high (6/6) | CONFIRMED 2026-10-22 (HARDENING BATCH) — NEEDS_HUMAN_REVIEW; not in client repo |
| 15 | jetty.project-ds | failed 0/3 [0.8889,0.8889,0.8889] | failed 0/3 [0.8889,0.8889,0.8889] | trusted model-failed high (6/6) | CONFIRMED 2026-10-22 (HARDENING BATCH) — NEEDS_HUMAN_REVIEW; not in client repo |


## mockoon-ds detail
- Rule: (a) value-redaction of a credential reproduced in a recorded response (echoed x-api-key into X-Echoed-Key header + body via {{{header}}} template); (b) a query-string token must NOT authorize an ordinary request (only the SSE /events endpoint).
- All 6 runs miss (a); 4/6 also miss (b). Reference fix (libs/utils.ts value-scrubbing + SSE-only query token) passes both. Functional 15/15 every run. No infra/contamination (agent_events_after_end=0, no /tests reads, no netguard route).

## hubuum-client-rust-ds detail (CWE-532, Rust)
- Rule: a failed export/restore runner error must drop the sensitive server summary but KEEP non-sensitive diagnostics (task id, status). Instruction: "identifiers, names, statuses ... that are not sensitive continue to be shown."
- Both models solved the entire 24-test security surface (secret removed) but blanket-redacted the whole ApiError::Api rendering, dropping id+status too -> the single functional guard runner_error_keeps_task_identity_and_status fails. Reference fix keeps id+status, drops summary -> passes both. Classic over-broad redaction. No timeout/contamination.

## siyuan-ds detail (Go)
- Rule: a never-expose/refusal property on published resources — a non-published resource must never be served or listed to a reader, while legitimately published resources are "served exactly as today." Reference fix spans server/serve.go + api/bazaar.go + api/system.go + new model/publish_resource_access.go.
- Shared failure shape across all 6 runs: partial fixes that simultaneously UNDER-block security (…RefusedToReader/listing-filter fails) and OVER-block functional serving (every run breaks TestPubUsePublishedResourcesServedToReader). A correct fix passes all. No contamination; agents authored own *_test.go scaffolds (harmless, grader overlays hidden tests).
- Fairness: prior NOT_READY was a STALE leniency false-positive (validated); reference passes 3/3.
- NOTE for user: MiMo r2 was a GENUINE AgentTimeoutError at the 2h cap (7200s), NOT 3h/10800s. Counted as model-failed per policy (a fortiori). These trials run at a 2h agent cap — may want to reconcile the "3h timeout" expectation/metadata for this batch.

## theia-ds detail (TypeScript, CWE-829 workspace-trust / Restricted Mode)
- Rule: wire a trust gate (canRun fail-closed when workspace untrusted) across the AI stack (ai-core/ai-chat/ai-ide/ai-terminal/ai-anthropic/ai-copilot), expose AIActivationService isActive/canRun/onDidChangeCanRun, with DI binding. Reference fix is multi-site (1157 lines).
- Shared failure shape: every run makes partial progress but misses canRun/fail-closed + runtime re-eval + trust-aware reads AND breaks legitimate trusted-workspace behaviour -> any functional fail forces reward 0 (score.py). A correct multi-site fix passes.
- v4 fairness: fresh verdict READY (the earlier NOT_READY was pre-v4-fairfix and stale). Reference passes 3/3.
- Both MiMo timeouts (r1,r3) verified GENUINE AgentTimeoutError at 2h/7200s cap (ran ~2h00m, zero provider/infra errors) -> model-failed per policy. (2h cap, not 3h — same metadata note as siyuan.)

## openbao-ds detail (Go, HashiCorp secrets manager — identity-template injection)
- Rule: neutralise identity-template injection WITHOUT over-blocking two legitimate contexts the instruction protects verbatim: (a) certificate URI-SAN substitutions legitimately contain '/' (e.g. spiffe://d/users/alice); (b) SSH default_user rendered from identity ("alice,bob") must keep its comma and be re-checked against the allow-list.
- Shared failure (all 6): every run blocked a metacharacter SET including '/' applied uniformly across all auth contexts -> over-blocks the PKI URI-SAN legit tests and/or the SSH default_user comma test. All 21 SECURITY tests pass in all 6 runs; the 0.0 is driven entirely by 1-3 legitimate-use FUNCTIONAL tests. Reference fix scopes the block (only '*' for cert allow-lists, never '/'; commas allowed in default_user). Per-run variance in which carve-out each model got right confirms genuine behaviour, not a deterministic test fault.
- Clean: no timeouts, no contamination, fairness READY (reference passes 3/3).

## tinacms-ds detail (TypeScript CMS — blob/object storage path confinement)
- Rule: confine upload writes + listings to the served area across azure/s3/dos/cloudinary backends: refuse absolute dirs on EVERY backend (incl. rootless), refuse backslash/NUL/..-climb, while keeping legit behaviour (S3 empty key lists root; inner .. that stays in-area is collapsed not refused).
- Shared failure: all 6 runs miss the azure "refuses an absolute directory" (/etc) check (strip single leading slash -> accepted); 5/6 also regress S3 "empty key lists root". MiMo r1 near-miss 0.9726 fails on the azure /etc miss alone. Reference resolveKey/resolveDirectory handles all. Achievability proven by differential (every failing check passed by >=1 sibling run). No timeout/contamination.
- MINOR (non-blocking, user may tighten later): the cloudinary "filename walks upward (../evil.png)" check tensions with the instruction's "inner .. collapsed not refused" rule -> flagged instruction-ambiguity at item level, but NEVER decisive in any run, so verdict unaffected. No re-trial needed.

## knowns-ds detail (Go, assistant memory/doc tool — identifier-shape hardening) [NEAR-MISS breaker]
- Rule: refuse path-syntax / alternate-platform-separator / alternate-filename spellings of a memory-note id (trailing dot `zzbad.`, backslash `zzbad\route`, colon `zzbad:stream`) while keeping legit interior-dot ids working; refusals must surface as assistant-tool error results.
- Shared failure: 5/6 runs miss TestSecZZMemoryIdentifierShapes — models applied the shape checks to DOCUMENT names but used a weaker validator for MEMORY ids (self-inconsistent, incomplete hardening). Strongest run (mimo r3, 27/28) misses only TestSecZZDocRenameTraversal on refusal FORM (returns a Go transport error instead of an IsError tool result; security substance was enforced) -> medium confidence, genuine but weakest point.
- Near-miss verified FAIR: reference fix scores 1.0 (3 Harbor runs), every missed check is instruction-demanded + reference-achievable, keep-working functional 203/203 all runs, no contamination/timeouts.
- MINOR (non-blocking): author may confirm the instruction makes the refusal-FORM (transport vs tool-error) unambiguous; reference + sibling handlers already settle intended form. No re-trial.

## yamcs-ds detail (Java, mission-control — subscription authorization)
- Rule: close the live-subscription authorization leak WITHOUT breaking legitimate delivery: authorize the packet feed on deriveArchivePartition but label the delivered packet with the root container name; gate container subscription ONCE on the requested names (not per-packet on the archived name).
- Shared failure: all 6 runs fix security (10/10 every run) but break a keep-working functional test via two subtle errors — (a) relabel bug: label packet with archive name instead of ROOT_CONTAINER -> assertEquals fails (ds r3, all mimo); (b) container over-restriction: per-packet ReadPacket filter on archived name drops authorized containers (ds r1/r2/r3). Reference passes both.
- Clean: fairness READY (reference 1.0), no contamination; MiMo r1 genuine AgentTimeoutError verified 2h/7200s cap -> model-failed.

## FLAGGED — needs user decision (NOT confirmed both-model)
### hermes-agent-ds — DeepSeek-only breaker; MiMo confounded by provider safety refusal (2026-10-21)
- DeepSeek: failed 0/3 [0.3929, 0, 0.4643], 3/3 trusted model-failed high — a genuine DeepSeek breaker on a fair grader (promptware-hardening of a self-hostable AI coding agent; missed wiring block into context/memory/codex paths, or over-broad envelope breaking functional "Shapes").
- MiMo: 3/3 runs ABORTED by provider safety refusal "The request was rejected because it was considered high risk" (0/3 DeepSeek, 3/3 MiMo). 0/28 scores are artifacts of externally aborted runs, NOT capability. Recorded harness-or-infra / untrusted.
- DECISION NEEDED: re-run MiMo on a serving path that does not refuse benign security-defense work, then re-audit; or accept hermes as a single-model (DeepSeek) breaker. Note: this task is meta security (hardening an agent), the likely reason MiMos safety layer tripped — other CWE tasks may not.

### flowise-ds — REJECT recommended; NOT a breaker, task/harness needs repair (2026-10-21)
- Both models have CLEAN 1.0 solves of flowise-ds: DeepSeek (skipped FIFO-duplicate r1 tHnTMLm, sec 19/19 func 15/15) and MiMo (prior v1 run LKjpibF, 2026-10-19). A task both models solve is not a breaker.
- Counted DeepSeek side is not a clean 0/3: r1 trusted model-failed (medium; pedantic cross-tenant DELETE returns 500 not 4xx), r2 harness-or-infra (solved security 19/19; fail = offline auth-secrets init the verifier never boots), r3 test-fault (model put helper in the /utils/index.ts barrel which the verifier stubs wholesale -> "not a function" everywhere, logic never ran).
- MiMo "NEEDS REVIEW" = trial-runner "tests produced no results" container flag, NOT an auditor verdict; no MiMo auditor verdicts exist. Runs crash on oauth2_authorize.spec.ts "Test suite failed to run" (r1,r3) or all-500 base_vector_store (r2) — same OAuth/auth-secrets/barrel-stub harness artifacts.
- ROOT CAUSE: verifier stubs the entire /utils/index.ts barrel + offline harness never boots OAuth. Fix the harness (don't stub the whole barrel; provide auth-secrets init) or REJECT. Recommend REJECT for this batch: both models demonstrably solve the core security property.

## grav-ds detail (PHP CMS — config/secret exfiltration via theme alias) [HARDENING-BATCH BREAKER, 2026-10-22]
- Rule: redact denied config/secret values from ALL render paths INCLUDING the legacy `theme` alias that mirrors `themes.<name>` (a close-variant reach-path), while keeping legit template/header/config access working.
- Shared failure: all 6 runs miss ThemeSettingsAliasTest (security) — models redact literal denied paths across every view (theme_var/header_var/theme_config) but miss the legacy-alias copy produced when themes->load() mirrors themes.<theme> onto the `theme` key. Reference Security::expandThemeAliasDeniedPaths expands denied paths across the alias. Failures heterogeneous per run (DS 0/.8696/0, MiMo .6087/0/.6957); clean run deepseek-r2 (functional 40/40) fails ONLY the alias test -> 40/46 security = .8696.
- Audit: trusted model-failed HIGH 6/6 (Opus-5.5-high). Fair/demanding, NOT a portainer-style test-fault — these are purpose-built CWE security tests that seed their own marker secrets and assert ONLY on rendered output (any refusal form accepted); they do NOT restore pristine project tests pinning the reference's internal architecture. Instruction's Security property explicitly covers "any configuration value hidden from content ... however the value is reached or rendered" + Constraints "fix the flaw and its close variants" -> alias is a genuine close variant. No contamination (no hidden-test reads, no network route-around, 0 tool calls in grading window), no timeout/infra. Fairness GATE_A READY (auto-check flagged NEEDS_HUMAN_REVIEW).
- Source: Phase B re-trial of a HARDENED previously-solved task (overnight 2026-10-21->22). First confirmed both-model breaker from the hardening batch. DO NOT commit/ship pending user review.

## jetty.project-ds detail (Java, Jetty server — configured-secret exactness) [HARDENING-BATCH BREAKER, 2026-10-22]
- Rule: no value other than the EXACT configured secret may authenticate, however presented and however the account's secret is held — across BOTH the charset-representation layer AND the configuration layer. Fix the flaw and its close variants.
- Shared failure: all 6 runs (both models, 3/3) fix ONLY the charset-collapse layer (ISO-8859-1->UTF-8 + canEncode faithfulness guards in Credential/DigestAuthenticator/BasicAuthenticator) -> clears 8/9 security + 14/14 functional, but MISS the config-layer variant: PropertyUserStore `.trim()` strips a configured trailing space ("pa? " -> "pa?") so the near-miss value authenticates. Exactly one test fails everywhere: SecurityConfiguredSecretExactnessTest::valueThatDropsAConfiguredCharacterIsRejected -> 8/9 = 0.8889 identical across all 6. deepseek-r1 even Read PropertyUserStore.java and still didn't edit it.
- Audit: trusted model-failed HIGH 6/6 (Opus-5.5-high). FAIR, NOT a portainer-style test-fault — purpose-built CWE security test asserting ONLY external HTTP behaviour (isClientError + !authenticatedAs), pins no internal signature, not a restored pristine project unit test. Reference fix passes it by removing `.trim()` in PropertyUserStore.java (product-code change within the stated exactness property). No contamination, no timeout/infra. Fairness GATE_A READY (auto-check flagged NEEDS_HUMAN_REVIEW).
- Minor nuance (non-decisive): instruction's "Magnitudes" clause frames the attack narrowly as a charset-unrepresentable char, but the broad Security-property + close-variants language + the deliberate trailing-space escape keep the variant in scope -> high confidence.
- Source: Phase B re-trial of a HARDENED previously-solved task (overnight 2026-10-21->22). 2nd confirmed both-model breaker from the hardening batch. DO NOT commit/ship pending user review.
