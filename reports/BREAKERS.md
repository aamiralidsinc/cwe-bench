# CWE-bench breakers register

As of 2026-10-19. Source: raw trial logs (`build/<slug>/runs_{deepseek,mimo}.log`), reconciled with
the round-2 re-trials and the DeepSeek-driven pilot lane (`build/*-ds`). **Authoritative per-run verdicts come from `build/audit_results.py`; this file
is the working register.** "Breaker" = the client goal: BOTH target models (DeepSeek V4.1 Flash and
MiMo-V2.6-Pro) fail all 3 counted attempts. Single-model breakers are leads, not the deliverable.

Reward key: a model "solves" at reward 1.0. A model "fails" a run at reward < 1.0. 3 fails with no
solve = that model broken on the task.

## Both-models breakers (the deliverable) — CONFIRMED

| Task | DeepSeek | MiMo | Audited | Fairness | Notes |
|---|---|---|---|---|---|
| `jackson-databind-sib2` | 0.0, 0.0, 0.0 | 0.0, 0.0, 0.0 | yes (high conf) | READY | The one confirmed, audited breaker. CWE-863 authz, 4 routes incl. an absent-protection catch-all + coupled legitimate values. Report: `reports/jackson-databind-sib2-breaker.md`. |
| `litellm-ds` | 0.0, 0.0, 0.0 (clean graded fail) | timeout ×all | yes — DeepSeek trustworthy ×3 (2026-10-20) | READY (validated by fixed two-gate agent + Opus) | DS-lane pilot. DeepSeek solves the SSRF security half every run (21/21 security) but breaks the required **opt-in credential-inheritance preservation** (instruction §59–63) every time — a coupled must-keep-working contract (M11), not a security miss; the reference fix preserves it, so a correct fix passes. MiMo never solves — it exhausts the window every attempt (3× at 2 h, then r4 cut at 3 h, r5 killed), counted as a timeout (user, 2026-10-20). |

Count: **2 both-models breakers** — `jackson-databind-sib2` (audited, high conf) and `litellm-ds` (DeepSeek clean-fail 3/3, postmortem trustworthy; MiMo timeout). litellm's DeepSeek failure is a coupled-contract preservation miss, not a security miss.

## DeepSeek-only breakers (DeepSeek fails 3/3, MiMo solves)

| Task | DeepSeek | MiMo | Fairness | Notes |
|---|---|---|---|---|
| `electron-builder-ds` | 0.6875, 0.875, 0.75 | 1.0 (solves) | **READY + audited (high)** | **CONFIRMED (fair + audited).** DS pilot lane. CWE credential leak: DeepSeek strips only standard `Authorization` — leaks `X-Api-Key` on differential/multi-range requests and never redacts secrets in failed-command output / debug logs / JSON errors (2–5 security fails per run, functional 165/165). MiMo solves. Postmortem: model-failed, trust=true ×3 (`~/.tb-graders/cwe/jobs/electron-builder-ds-deepseek-r{1,2,3}-*/…/postmortem-*`). |
| `vitest-api-fs-authz-inj` | 0.625, 0.625, 0.625 | 1.0, 1.0 | fairfixed; not re-reviewed | Post-fairfix re-trial. DeepSeek stuck at 5/8 security every run; MiMo solves. Near-miss on a both-breaker. |

## MiMo-only breakers (MiMo fails 3/3, DeepSeek solves)

| Task | DeepSeek | MiMo | Fairness | Notes |
|---|---|---|---|---|
| `backstage-ds` | 1.0 (solves) | 0.0, 0.0, 0.9149 | **READY + audited (high)** | **CONFIRMED (fair + audited).** DS pilot lane. MiMo never guards `fetch:template`/`fetch:file` credentials for GitHub (4 security fails) — r3 fixed the Bitbucket over-block (functional 85/85) but still missed the template-fetch guard, capping at 0.9149. DeepSeek solves at 1.0. Caveat: MiMo's best (0.9149) is a near-miss, not a wide gap. Postmortem: model-failed, trust=true ×3 (`~/.tb-graders/cwe/jobs/backstage-ds-mimo-r{1,2,3}-*/…/postmortem-*`). |
| `prompty-path-read-inj` | 0.8333, 1.0 | 0.8333, 0.8333, 0.8333 | NOT READY (fix not applied) | CWE-22 path traversal, 4 routes. MiMo leaves exactly one route open each run. Report: `reports/prompty-path-read-inj-mimo-only.md`. |
| `flowise-cross-tenant-inj` | 0.0, 1.0 | 0.0, 0.0, 0.0 | not reviewed | DeepSeek solves run 2; MiMo 0/3. |
| `electron-builder-credential-leakage` | 1.0 | 0.8, 0.9, 0.8 | not reviewed | DeepSeek solves; MiMo plateaus below 1.0. |
| `stigmem` | 1.0, 1.0 | 0.0, 0.4444, 0.0 | not reviewed | DeepSeek solves; MiMo 0/3. |

### MiMo-only — tentative (needs a 3rd MiMo run to confirm 3/3)

| Task | DeepSeek | MiMo | Notes |
|---|---|---|---|
| `airflow-info-exposure-inj` | 0.95, 0.0, 1.0 | 0.0, 0.0 | DeepSeek solves run 3; MiMo failed 2/2 but the 3rd run was not recorded. Confirm with one more MiMo run. |

## Reconciliation — formerly listed as breakers, now downgraded (2026-10-18 re-trials)

The pre-fairfix host-ledger counted these as both-models breakers; fairness review found the failures
were test artifacts, and after fairfix + re-trial both models solve. They are **not** breakers:

| Task | Was | Now | DeepSeek | MiMo |
|---|---|---|---|---|
| `grav-info-exposure-inj` | "breaker" | solved | 1.0 ×3 | 1.0 ×3 |
| `jenkins-ec2fleet-authz-inj` | "breaker" | solved | 1.0 ×3 | 1.0, 1.0 |
| `vitest-api-fs-authz-inj` | "breaker" | **DeepSeek-only** (see above) | 0.625 ×3 | 1.0, 1.0 |

## Caveats
- Audited AND fairness-READY so far: `jackson-databind-sib2` (both-models), `electron-builder-ds`
  (DeepSeek-only), `backstage-ds` (MiMo-only). These three are validated. Every OTHER single-model
  entry is still a **lead**: not fairness-reviewed, or explicitly NOT READY (e.g. `prompty`, where a
  test-construction issue may inflate MiMo's failures). Validate (fairfix + re-trial + audit) before
  reporting the leads.
- `electron-builder-ds` / `backstage-ds` are confirmed **single-model** breakers (one model still
  solves), so they are strong leads toward a both-model breaker, not the deliverable itself.
- Single-model breakers do not meet the client's both-fail goal; they are kept to track which model
  each task separates and to mine for a both-breaker recipe.
- The fully model-driven DeepSeek/MiMo pilot (50 candidates per lane) is running; its breakers will be
  appended here as its ledgers (`build/pipeline/ledger_{deepseek,mimo}.tsv`) report.
