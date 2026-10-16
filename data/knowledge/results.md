# CWE-Bench task factory: results

*Status as of 2026-10-15 12:55 (America/New_York). Pilot phase. Every number below comes from the recorded run artifacts listed under "Provenance".*

## Summary

- **5 tasks evaluated against the target models so far: 4 solved by at least one model, 1 still in play.**
  - **pyload, CWE-613: DeepSeek solved it and MiMo failed.** The task is rejected as too easy and recorded as a "breaks only MiMo" pattern.
  - **Batch 2 (devalue, ip-address, pypdf): DeepSeek solved all 3 on its first attempt.** MiMo also solved ip-address. MiMo's attempts on devalue and pypdf were stopped early, because DeepSeek's solve had already decided the verdict.
  - **MCP TypeScript SDK, CWE-345/522: both models failed all 3 attempts (pass@3 = 0) in the first run.** It is not accepted yet. 5 of the 6 attempts hit the 30-minute time limit. A 60-minute re-run was lost to a network outage on our side. In the **2-hour** re-run, DeepSeek has failed attempt 1 again (0.92), finishing on its own well inside the limit. MiMo's attempt 1 is still running. The final verdict will be in the next-day update.
- **1 task accepted: the MCP TypeScript SDK (GHSA-6qxp-vccf-f47h).** In the 2-hour run both models failed all 3 attempts (pass@3 = 0). Packaged in `data/05_accepted_harbor/ghsa-6qxp-vccf-f47h/`, and the final oracle check on the packaged copy passed.
  - **DeepSeek:** 0.92 on all 3 attempts, finishing on its own each time (79–127 steps). It left one security variant open every time.
  - **MiMo:** 0.50 on all 3 attempts. All 3 hit the 2-hour limit (47–57 steps) with no security hole closed. Under the agreed rule a scored timeout counts as a failure, as CWE-bench grades it. Even so, MiMo's result partly reflects its speed (about 2 minutes per step).
- **Observation (small sample):** the one task DeepSeek has failed spans 8 files and 174 changed lines. The 4 tasks it solved were smaller fixes (2–5 files, 25–111 lines).

**Ledger:** per-task, per-model graded counts in the shared format are in `ledger.md`. It is rebuilt from the raw trials after every model run (`python -m src.common.ledger`).

## Setup

| Item | Value |
|---|---|
| Target models | DeepSeek V4.1 Flash (`deepseek-flash`, reasoning effort `max`); Xiaomi MiMo-V2.6-Pro (`mimo-v2.6-pro`) |
| Agent harness | Harbor `terminus-2` for both models. Model calls are made from the host; the agent gets a shell inside the task container. |
| Isolation | Task container has no network (`network_mode: none`) and no web tools. Hidden tests are uploaded only after the agent finishes. |
| Attempts | 3 per model. Attempt 1 runs on both models first. If either model solves it, the task is rejected and attempts 2–3 are skipped, because pass@3 = 0 is no longer possible. |
| Grading | Deterministic partial score: mean of (security tests passed, functional tests passed, the repo's existing tests that passed before and after the fix). **1.0 = solved.** |
| Time budget | 30 minutes per attempt in the completed evaluations below. Re-runs use 2 hours, so timeouts no longer decide results. |
| Task sources | OSV.dev, GitHub Advisory Database, huntr disclosures (PyPI + npm). Batch 1: fixes committed after 2026-09-23, which is after both models were released. Batch 2: fixes committed after 2026-09-11, which is after DeepSeek V4.1 Flash's release (2026-09-10) and before MiMo-V2.6's (2026-09-21/22). The cutoff was relaxed because the stricter pool ran out. |

## Evaluation results

### 1. pyload — GHSA-jq7h-wrvp-3rgx (CWE-613, Python)
*Password change and privilege revocation through the REST API do not invalidate the user's existing sessions.*

| Model | Attempt | Score | Security | Functional | Existing tests (29) | Notes |
|---|---|---|---|---|---|---|
| DeepSeek | 1 | **1.00 (solved)** | 1.00 | 1.00 | 1.00 | finished in 58 steps |
| MiMo | 1 | 0.67 | 0.00 | 1.00 | 1.00 | none of the stale-session probes were blocked; hit the time limit (26 steps) |

**Verdict:** rejected as too easy. Attempts 2–3 were not run because DeepSeek had already solved it.
**Pattern:** breaks only MiMo.

### 2. MCP TypeScript SDK — GHSA-6qxp-vccf-f47h (CWE-345, CWE-522, TypeScript)
*The OAuth client could send credentials to an authorization server chosen by the resource being accessed.*

| Model | Attempt | Score | Security | Functional | Notes |
|---|---|---|---|---|---|
| DeepSeek | 1 | 0.83 | 0.67 | 1.00 | hit the time limit (105 steps) |
| DeepSeek | 2 | 0.92 | 0.83 | 1.00 | **finished on its own** (97 steps) and left one attack variant open |
| DeepSeek | 3 | 0.92 | 0.83 | 1.00 | hit the time limit (96 steps) |
| MiMo | 1 | 0.50 | 0.00 | 1.00 | hit the time limit (32 steps) |
| MiMo | 2 | 0.50 | 0.00 | 1.00 | hit the time limit (37 steps) |
| MiMo | 3 | 0.50 | 0.00 | 1.00 | hit the time limit (28 steps) |

**Verdict:** pass@3 = 0 on both models, but it is **not accepted yet**.
- **DeepSeek:** the failure is a clear capability failure. It declared the fix finished while one attack variant was still open (incomplete remediation).
- **MiMo:** we can't tell capability from time pressure. It took about 1 minute per step and hit the limit on all 3 attempts.

**Evaluation history for this task**

| Run | Agent time limit | Date | Outcome |
|---|---|---|---|
| 1 | 30 min | 2026-10-14 | All 6 attempts failed (table above). 5 of 6 hit the time limit, so the result is inconclusive for acceptance. |
| 2 | 60 min | 2026-10-14 evening | **No valid result.** The network on our machine dropped about 50 minutes in, so both models' attempts ended with connection errors before they could finish. Excluded (see below). |
| 3 | **2 hours** | 2026-10-15 | **ACCEPTED.** DeepSeek failed 3/3 (0.92 each; security 0.83, functional 1.0) and stopped on its own each time. MiMo failed 3/3 (0.50 each; security 0.00, functional 1.00), each attempt reaching the 2-hour limit. |

### 3–5. Batch 2 (2026-10-15)

| Task | Bug | DeepSeek attempt 1 | MiMo attempt 1 | Verdict |
|---|---|---|---|---|
| devalue — GHSA-j22f-vq7h-c4qm (npm; CWE-200, CWE-226) | Serializer exposes shared memory contents | **1.00 solved** (68 steps) | stopped early (24 steps) | rejected: too easy |
| ip-address — GHSA-j6r3-76f7-8jcv (npm; CWE-697, CWE-843) | Subnet checks compare addresses of different families | **1.00 solved** (31 steps) | **1.00 solved** (38 steps) | rejected: too easy (both solve) |
| pypdf — GHSA-v247-6f48-mgcj (Python; CWE-400, CWE-407) | Very long runtimes with many embedded files | **1.00 solved** (33 steps; all 231 existing tests kept passing) | stopped early (19 steps) | rejected: too easy |

These fixes were small (2–4 files, 25–93 changed lines), and DeepSeek solved each one on its first attempt in 31–68 steps.

## Pipeline funnel (cumulative)

| Step | Count | Notes |
|---|---|---|
| Advisories mined | 437 | OSV, GHSA, huntr (PyPI + npm) |
| Passed screening | 42 | Real source-code fix, fix committed after the cutoff (see Setup), repo ≤ 150 MB, repo has tests |
| Selected for task building | 15 | Highest screening scores, at most one task per repository per batch |
| Could not be built | 1 | pydantic-ai: install failed |
| Generation blocked by the safety filter | 3 | handlebars (code injection), source-map-js, smol-toml. Also one pyload rewrite. |
| Oracle patch too large | 1 | msgpack5: the fix commit included a rebuilt minified bundle. Fixed: build artifacts are now removed from oracle patches, and the task is queued for generation. |
| Tasks generated | 10 | |
| Rejected by quality review, waiting for a rewrite | 3 | 2 pyload advisories, adm-zip |
| Filtered by the recall probe | 1 | shell-quote: both models named the fix location from the report alone |
| Test harness never ran correctly (4 rounds) | 1 | simple-git: a TypeScript monorepo whose internal packages only its own test runner can load |
| Passed quality review and oracle validation | 5 | pyload, MCP SDK, devalue, ip-address, pypdf |
| Evaluated against the models | 5 | Results above |
| Solved by at least one model | 4 | pyload, devalue, ip-address, pypdf |
| Still in play | 0 | |
| Accepted | 1 | MCP SDK (GHSA-6qxp-vccf-f47h) |

## Quality gates: what they caught

- **Quality review before any model run.** In batch 1, 4 of the 5 first drafts were rejected. In batch 2, after the review's rules were given to the generator up front, 1 of 5 first drafts was rejected. In each rejected draft, the hidden tests accepted only the original developers' exact fix design, so a different but correct fix would have failed. The rejection reasons are sent back to the generator. Every rewrite that was re-checked passed the review (pyload and simple-git on their second draft; the MCP SDK on its first draft).
- **Oracle validation (running the real fix against the tests).** It caught one broken test harness: the pyload tests re-created the web app for every test, which the project does not allow. That task was rewritten using the real test output, and the rewrite validated.
- **No AI judge decides acceptance.** Pass or fail comes only from the automatic tests. A task is accepted only if every attempt failed cleanly.

## Excluded from this report (problems on our side, all fixed)

These runs failed because of our pipeline or our machine, not because of the tasks or the models, so their records were removed from the results above. The raw records are kept for audit (see Provenance).

| Date | Issue | Fix |
|---|---|---|
| 2026-10-14 | Harbor's network restriction modes are not supported by Docker Desktop on macOS, so validation runs could not start | The task container is now isolated with Docker's own `network_mode: none` |
| 2026-10-14 | The task image did not support pnpm workspaces | The package manager is detected from the lockfile |
| 2026-10-14 | TypeScript packages were not compiled in the task image, so the tests could not load the library | The image builds the project, and grading rebuilds it first so the agent's edits are what get tested |
| 2026-10-14/15 | The Node 20 image was too old for a repository's pnpm 11 build | Switched to Node 22 |
| 2026-10-15 | One fix commit included a rebuilt minified JavaScript bundle (a 453,000-character diff) | Generated build artifacts are now removed from oracle patches |
| 2026-10-14/15 | Network outage on our machine interrupted the 60-minute MCP SDK re-run. No attempt finished, so no result was recorded. | Re-run with a 2-hour limit started 2026-10-15 |

## Next steps

1. **In progress:** the MCP SDK 2-hour re-run, waiting on MiMo's attempts. It is accepted if pass@3 = 0 holds.
2. **Task difficulty:** DeepSeek solves small, local fixes on its first attempt. Screening will rank candidates higher when the real fix spans more files and directories, which is the shape of the only task it failed.
3. **Candidate pool:** 42 screened candidates are available under the current cutoff. The next batch includes msgpack5 and the 3 tasks waiting for a rewrite.

## Provenance

- **Per-attempt artifacts:** `data/04_eval_runs/<ID>/<model>/<job>/<trial>/`. Each trial folder holds:
  - `agent/trajectory.json`: every step the model took
  - `verifier/score_breakdown.json`: the score parts
  - `verifier/test-stdout.txt`: the full test output
- **Validation runs:** `data/03_environments/<ID>/validation/`
- **Outcome log (machine-readable):** `data/knowledge/task_outcomes.jsonl`
- **Raw run log and the excluded records:** `data/knowledge/archive/`

---

## Run log (appended automatically by the pipeline)
## 2026-10-15T12:47:14Z - Stage 4 - rubric + oracle validation

counts: {"ok": 1, "failed_oracle": 1, "rejected": 0, "regenerate": 0, "failed": 0}

| task | verdict | detail |
|---|---|---|
| GHSA-6qxp-vccf-f47h | ok | oracle 1.0, pre-patch fails as required; existing pass->pass tests: 0 (from 0 candidate files) |
| GHSA-x6jw-m9v5-85vh | REJECTED | oracle does not pass its own tests (reward [0.0, 0.0], failing: ['::test_functional_interpret_trailers_with_inline_key', '::test_functional_interpret_trailers_w |

## 2026-10-15T13:33:18Z - Stage 4 - rubric + oracle validation

counts: {"ok": 3, "failed_oracle": 2, "rejected": 0, "regenerate": 1, "failed": 0}

| task | verdict | detail |
|---|---|---|
| GHSA-j22f-vq7h-c4qm | ok | oracle 1.0, pre-patch fails as required; existing pass->pass tests: 0 (from 0 candidate files) |
| GHSA-j6r3-76f7-8jcv | ok | oracle 1.0, pre-patch fails as required; existing pass->pass tests: 0 (from 0 candidate files) |
| GHSA-p634-w6r4-rjp2 | REJECTED | rubric: The oracle fails test_functional_object_property_like_names. The `in` check on the plain-object entryTable matches inherited properties ('constructor',  |
| GHSA-pqg4-j6r4-53mv | REJECTED | recall probe: both models name the fix location from the report alone |
| GHSA-v247-6f48-mgcj | ok | oracle 1.0, pre-patch fails as required; existing pass->pass tests: 231 (from 4 candidate files) |
| GHSA-x6jw-m9v5-85vh | REJECTED | oracle does not pass its own tests (reward [0.0, 0.0], failing: ['::test_functional_interpret_trailers_with_inline_key', '::test_functional_interpret_trailers_w |

## 2026-10-15T15:57:06Z - Stage 4 - rubric + oracle validation

counts: {"ok": 1, "failed_oracle": 1, "rejected": 0, "regenerate": 2, "failed": 0}

| task | verdict | detail |
|---|---|---|
| GHSA-mcm9-63f2-9j32 | REJECTED | functional tests failing on vulnerable code (not pass->pass): ['test_functional_output_is_script_safe'] |
| GHSA-p634-w6r4-rjp2 | ok | oracle 1.0, pre-patch fails as required; existing pass->pass tests: 0 (from 0 candidate files) |
| GHSA-x33g-cr3x-6449 | REJECTED | recall probe: both models name the fix location from the report alone |
| GHSA-x937-hj6v-793p | REJECTED | rubric: The functional tests cannot tell a working cache from a disabled one: removing caching entirely passes every hidden test, even though the report require |

## 2026-10-15T16:49:09Z - Stage 5 - DeepSeek / MiMo evaluation

counts: {"done": 0, "accepted": 1}

| task | status | rewards per model | detail |
|---|---|---|---|
| GHSA-6qxp-vccf-f47h | accepted | deepseek: [0.9167, 0.9167, 0.9167] ; mimo: [0.5, 0.5, 0.5] | all attempts failed cleanly on every model {'hole_still_open': 6} |

## 2026-10-15T17:58:43Z - Stage 5 - DeepSeek / MiMo evaluation

counts: {"rejected_too_easy": 1}

| task | status | rewards per model | detail |
|---|---|---|---|
| GHSA-p634-w6r4-rjp2 | rejected_too_easy | deepseek: [1.0] ; mimo: [1.0] | solved by deepseek, mimo |

## 2026-10-16T01:09:43Z - Stage 4 - rubric + oracle validation

counts: {"ok": 0, "failed_oracle": 0, "rejected": 0, "regenerate": 1, "failed": 0}

| task | verdict | detail |
|---|---|---|
| GHSA-vp8m-p9jh-q5pm | REJECTED | rubric: test_functional_origins_allow_list fails on the vulnerable code: an allow-list on a Client with no per-request origin never cached before, yet the repor |

## 2026-10-16T01:11:06Z - Stage 4 - rubric + oracle validation

counts: {"ok": 0, "failed_oracle": 0, "rejected": 0, "regenerate": 1, "failed": 0}

| task | verdict | detail |
|---|---|---|
| GHSA-68fv-2mgg-jv7q | REJECTED | rubric: The hidden test needs a line-offset cap somewhere between 1,000,000 (must work) and 50,000,000 (must be refused, with output capped at 1,000,000 bytes). |

## 2026-10-16T01:30:41Z - Stage 4 - rubric + oracle validation

counts: {"ok": 0, "failed_oracle": 1, "rejected": 0, "regenerate": 0, "failed": 0}

| task | verdict | detail |
|---|---|---|
| GHSA-68fv-2mgg-jv7q | REJECTED | oracle does not pass its own tests (reward [0.6667, 0.6667], failing: ['::test_functional_copy_small_indexed_into_generator', '::test_functional_copy_small_inde |

## 2026-10-16T01:35:39Z - Stage 4 - rubric + oracle validation

counts: {"ok": 1, "failed_oracle": 0, "rejected": 0, "regenerate": 0, "failed": 0}

| task | verdict | detail |
|---|---|---|
| GHSA-vp8m-p9jh-q5pm | ok | oracle 1.0, pre-patch fails as required; existing pass->pass tests: 0 (from 15 candidate files); fix checks: shallow leaves 5/7 security tests open, removal bre |

## 2026-10-16T02:04:09Z - Stage 4 - rubric + oracle validation

counts: {"ok": 1, "failed_oracle": 0, "rejected": 0, "regenerate": 0, "failed": 0}

| task | verdict | detail |
|---|---|---|
| GHSA-hqr4-qq8f-hg3x | ok | oracle 1.0, pre-patch fails as required; existing pass->pass tests: 0 (from 15 candidate files); fix checks: shallow leaves 3/7 security tests open, removal bre |

## 2026-10-16T02:05:48Z - Stage 4 - rubric + oracle validation

counts: {"ok": 4, "failed_oracle": 0, "rejected": 0, "regenerate": 9, "failed": 3}

| task | verdict | detail |
|---|---|---|
| GHSA-24ch-f2g6-9hhh | ok | oracle 1.0, pre-patch fails as required; existing pass->pass tests: 0 (from 15 candidate files); fix checks: shallow leaves 6/7 security tests open, removal bre |
| GHSA-2q42-4q24-7rgv | REJECTED | rubric: The security tests require at least one emitted file (`confined()` returns False on an empty file list), so fixes that reject hostile specs with a diagn |
| GHSA-3wxw-xv34-2frg | ok | oracle 1.0, pre-patch fails as required; existing pass->pass tests: 42 (from 13 candidate files); fix checks: shallow leaves 3/5 security tests open, removal br |
| GHSA-5jq2-8x83-x246 | REJECTED | rubric: Hidden tests require an undisclosed, arbitrary length cutoff (accept 60-character IDs, reject 200-character ones) that matches the oracle's internal _MA |
| GHSA-68fv-2mgg-jv7q | REJECTED | oracle does not pass its own tests (reward [0.6667, 0.6667], failing: ['::test_functional_copy_small_indexed_into_generator', '::test_functional_copy_small_inde |
| GHSA-68w4-83fh-f2w8 | ok | oracle 1.0, pre-patch fails as required; existing pass->pass tests: 8 (from 2 candidate files); fix checks: shallow leaves 3/4 security tests open, removal brea |
| GHSA-77xj-x4rm-935c | REJECTED | oracle does not pass its own tests (reward [0.0, 0.0], failing: unknown) |
| GHSA-8r5x-fm3f-whwj | REJECTED | rubric: Every hidden-test AST leaves out `loc`. On the vulnerable code, helper/ambiguous invocation likely emits `"loc":` with no value (JSON.stringify(undefine |
| GHSA-9q47-3cm2-2rp8 | ok | oracle 1.0, pre-patch fails as required; existing pass->pass tests: 28 (from 1 candidate files); fix checks: shallow leaves 3/7 security tests open, removal bre |
| GHSA-hmq2-7hp6-7crh | REJECTED | oracle does not pass its own tests (reward [0.7857, 0.7857], failing: ['::test_functional_nested_model_call_with_function_filter', '::test_functional_nested_mod |
| GHSA-hqr4-qq8f-hg3x | ok | oracle 1.0, pre-patch fails as required; existing pass->pass tests: 0 (from 15 candidate files); fix checks: shallow leaves 3/7 security tests open, removal bre |
| GHSA-hxh3-vqpv-xpqv | REJECTED | oracle run had no verdict: RuntimeError: Docker compose command failed for environment ghsa-hxh3-vqpv-xpqv. Command: docker compose --project-name harbor_task__ |
| GHSA-jggr-w7fw-pc2j | REJECTED | oracle run had no verdict: RuntimeError: Docker compose command failed for environment ghsa-jggr-w7fw-pc2j. Command: docker compose --project-name harbor_task__ |
| GHSA-p4rw-rvv2-7xwr | REJECTED | oracle run had no verdict: RuntimeError: Docker compose command failed for environment ghsa-p4rw-rvv2-7xwr. Command: docker compose --project-name harbor_task__ |
| GHSA-qf28-8hc6-vwrp | REJECTED | rubric: Security tests call the patched internal utilities getSelect/setNestedValue directly instead of going through the export/preview HTTP entry point; Tests |
| GHSA-r4xh-jqrq-34v2 | REJECTED | rubric: Security tests depend on a 30s wall-clock limit that includes vitest startup, and the vulnerable code's runtime (~9e11 bytes of memchr scanning) may com |

## 2026-10-16T02:10:48Z - Stage 4 - rubric + oracle validation

counts: {"ok": 0, "failed_oracle": 0, "rejected": 0, "regenerate": 0, "failed": 1}

| task | verdict | detail |
|---|---|---|
| GHSA-hmq2-7hp6-7crh | REJECTED | check patch 'shallow' produced no per-test verdict: RuntimeError: Docker compose command failed for environment ghsa-hmq2-7hp6-7crh. Command: docker compose --p |

## 2026-10-16T02:14:20Z - Stage 4 - rubric + oracle validation

counts: {"ok": 0, "failed_oracle": 0, "rejected": 0, "regenerate": 1, "failed": 0}

| task | verdict | detail |
|---|---|---|
| GHSA-qf28-8hc6-vwrp | REJECTED | rubric: The functional tests never check the content of the preview docs, so a fix that ignores or drops all `fields` (removing field selection) still passes. T |

## 2026-10-16T02:21:58Z - Stage 4 - rubric + oracle validation

counts: {"ok": 0, "failed_oracle": 0, "rejected": 0, "regenerate": 0, "failed": 1}

| task | verdict | detail |
|---|---|---|
| GHSA-77xj-x4rm-935c | REJECTED | oracle fails once the existing-test set is enforced: oracle run had no verdict: RuntimeError: Docker compose command failed for environment ghsa-77xj-x4rm-935c. |

## 2026-10-16T02:23:32Z - Stage 4 - rubric + oracle validation

counts: {"ok": 0, "failed_oracle": 0, "rejected": 0, "regenerate": 0, "failed": 1}

| task | verdict | detail |
|---|---|---|
| GHSA-r4xh-jqrq-34v2 | REJECTED | oracle run produced 0/2 trials |

## 2026-10-16T02:31:01Z - Stage 4 - rubric + oracle validation

counts: {"ok": 0, "failed_oracle": 0, "rejected": 0, "regenerate": 0, "failed": 1}

| task | verdict | detail |
|---|---|---|
| GHSA-2q42-4q24-7rgv | REJECTED | oracle run had no verdict: RuntimeError: Docker compose command failed for environment ghsa-2q42-4q24-7rgv. Command: docker compose --project-name harbor_task__ |

## 2026-10-16T02:31:27Z - Stage 4 - rubric + oracle validation

counts: {"ok": 0, "failed_oracle": 0, "rejected": 0, "regenerate": 1, "failed": 0}

| task | verdict | detail |
|---|---|---|
| GHSA-jggr-w7fw-pc2j | REJECTED | oracle does not pass its own tests (reward [0.5, 0.5], failing: ['::test_security_custom_prototypes_and_symbol_keys', '::test_security_custom_prototypes_and_sym |

## 2026-10-16T02:44:06Z - Stage 4 - rubric + oracle validation

counts: {"ok": 0, "failed_oracle": 0, "rejected": 0, "regenerate": 1, "failed": 0}

| task | verdict | detail |
|---|---|---|
| GHSA-5jq2-8x83-x246 | REJECTED | fix checks: ALTERNATIVE correct fix scores 0 |

## 2026-10-16T03:09:48Z - Stage 4 - rubric + oracle validation

counts: {"ok": 2, "failed_oracle": 0, "rejected": 0, "regenerate": 0, "failed": 0}

| task | verdict | detail |
|---|---|---|
| GHSA-hxh3-vqpv-xpqv | ok | oracle 1.0, pre-patch fails as required; existing pass->pass tests: 494 (from 15 candidate files); fix checks: shallow leaves 5/6 security tests open, removal b |
| GHSA-p4rw-rvv2-7xwr | ok | oracle 1.0, pre-patch fails as required; existing pass->pass tests: 118 (from 13 candidate files); fix checks: shallow leaves 4/5 security tests open, removal b |

## 2026-10-16T03:36:58Z - Stage 4 - rubric + oracle validation

counts: {"ok": 0, "failed_oracle": 0, "rejected": 0, "regenerate": 0, "failed": 1}

| task | verdict | detail |
|---|---|---|
| GHSA-qf28-8hc6-vwrp | REJECTED | pre-patch run had no verdict: RuntimeError: Docker compose command failed for environment ghsa-qf28-8hc6-vwrp. Command: docker compose --project-name harbor_tas |

## 2026-10-16T03:38:14Z - Stage 4 - rubric + oracle validation

counts: {"ok": 1, "failed_oracle": 0, "rejected": 0, "regenerate": 0, "failed": 0}

| task | verdict | detail |
|---|---|---|
| GHSA-5jq2-8x83-x246 | ok | oracle 1.0, pre-patch fails as required; existing pass->pass tests: 319 (from 7 candidate files); fix checks: shallow leaves 2/5 security tests open, removal br |

## 2026-10-16T04:50:56Z - Stage 4 - rubric + oracle validation

counts: {"ok": 2, "failed_oracle": 0, "rejected": 0, "regenerate": 2, "failed": 1}

| task | verdict | detail |
|---|---|---|
| GHSA-2q42-4q24-7rgv | REJECTED | oracle does not pass its own tests (reward [0.375, 0.375], failing: ['::test_functional_json_schema_basic_and_dotted_names', '::test_functional_json_schema_basi |
| GHSA-77xj-x4rm-935c | ok | oracle 1.0, pre-patch fails as required; existing pass->pass tests: 238 (from 11 candidate files); fix checks: shallow leaves 3/6 security tests open, removal b |
| GHSA-hmq2-7hp6-7crh | ok | oracle 1.0, pre-patch fails as required; existing pass->pass tests: 74 (from 15 candidate files); fix checks: shallow leaves 6/7 security tests open, removal br |
| GHSA-jggr-w7fw-pc2j | REJECTED | oracle does not pass its own tests (reward [0.5, 0.5], failing: ['::test_security_custom_prototypes_and_symbol_keys', '::test_security_custom_prototypes_and_sym |
| GHSA-r4xh-jqrq-34v2 | REJECTED | oracle run produced 0/2 trials |

## 2026-10-16T04:58:57Z - Stage 4 - rubric + oracle validation

counts: {"ok": 0, "failed_oracle": 0, "rejected": 0, "regenerate": 1, "failed": 0}

| task | verdict | detail |
|---|---|---|
| GHSA-r4xh-jqrq-34v2 | REJECTED | oracle does not pass its own tests (reward [0.875, 0.875], failing: ['::test_security_many_single_quoted_key_entries', '::test_security_many_table_headers', 'te |

## 2026-10-16T05:02:02Z - Stage 4 - rubric + oracle validation

counts: {"ok": 0, "failed_oracle": 1, "rejected": 0, "regenerate": 0, "failed": 0}

| task | verdict | detail |
|---|---|---|
| GHSA-jggr-w7fw-pc2j | REJECTED | oracle does not pass its own tests (reward [0.5, 0.5], failing: ['::test_security_custom_prototypes_and_symbol_keys', '::test_security_custom_prototypes_and_sym |

## 2026-10-16T05:18:53Z - Stage 4 - rubric + oracle validation

counts: {"ok": 0, "failed_oracle": 1, "rejected": 0, "regenerate": 0, "failed": 0}

| task | verdict | detail |
|---|---|---|
| GHSA-r4xh-jqrq-34v2 | REJECTED | security tests that already pass on vulnerable code: ['test_security_many_table_headers'] |

## 2026-10-16T06:08:08Z - Stage 4 - rubric + oracle validation

counts: {"ok": 1, "failed_oracle": 1, "rejected": 0, "regenerate": 0, "failed": 0}

| task | verdict | detail |
|---|---|---|
| GHSA-2q42-4q24-7rgv | ok | oracle 1.0, pre-patch fails as required; existing pass->pass tests: 28 (from 3 candidate files); fix checks: shallow leaves 5/7 security tests open, removal bre |
| GHSA-qf28-8hc6-vwrp | REJECTED | oracle fails once the existing-test set is enforced: oracle does not pass its own tests (reward [0.9867], failing: ['test/access-control/getConfig.ts::(no resul |

## 2026-10-16T06:38:16Z - Stage 4 - rubric + oracle validation

counts: {"ok": 1, "failed_oracle": 0, "rejected": 0, "regenerate": 0, "failed": 0}

| task | verdict | detail |
|---|---|---|
| GHSA-qf28-8hc6-vwrp | ok | oracle 1.0, pre-patch fails as required; existing pass->pass tests: 24 (from 7 candidate files); fix checks: shallow leaves 3/5 security tests open, removal bre |

## 2026-10-16T08:16:19Z - Stage 4 - rubric + oracle validation

counts: {"ok": 1, "failed_oracle": 1, "rejected": 0, "regenerate": 5, "failed": 0}

| task | verdict | detail |
|---|---|---|
| GHSA-2q76-m6w6-qgc6 | REJECTED | rubric: Tests require owner binding to be done with field-level `access` on the `user` field; valid hook-based fixes, or rules that allow only assigning yoursel |
| GHSA-376h-93r7-7g6f | REJECTED | oracle does not pass its own tests (reward [0.0, 0.0], failing: ['::test_functional_admin_under_base_served', '::test_functional_admin_under_base_served', '::te |
| GHSA-8fvv-fgr5-f8ch | ok | oracle 1.0, pre-patch fails as required; existing pass->pass tests: 72 (from 13 candidate files); fix checks: shallow leaves 4/6 security tests open, removal br |
| GHSA-8xx6-hgc6-gc2m | REJECTED | isolation audit: fix code is readable inside the image: /usr/local/lib/python3.11/site-packages/httpx2/_content.py contains 3 of the fix's added lines; fix code |
| GHSA-mcm9-63f2-9j32 | REJECTED | functional tests failing on vulnerable code (not pass->pass): ['test_functional_output_is_script_safe'] |
| GHSA-w3v8-gmh9-3wv7 | REJECTED | rubric: Hidden tests require the pathological call to end within 25s (including subprocess spawn/import), but the report only demands 'bounded time'; a fix usin |
| GHSA-x78j-v8h9-3j2q | REJECTED | rubric: test_security_prompt_line_break requires collapsing Unicode line separators (U+2028/U+0085/U+2029). cmd.exe does not treat these as line breaks and the  |

## 2026-10-16T08:21:51Z - Stage 4 - rubric + oracle validation

counts: {"ok": 1, "failed_oracle": 0, "rejected": 0, "regenerate": 0, "failed": 0}

| task | verdict | detail |
|---|---|---|
| GHSA-8xx6-hgc6-gc2m | ok | oracle 1.0, pre-patch fails as required; existing pass->pass tests: 53 (from 2 candidate files); fix checks: shallow leaves 6/8 security tests open, removal bre |

## 2026-10-16T08:43:55Z - Stage 4 - rubric + oracle validation

counts: {"ok": 0, "failed_oracle": 1, "rejected": 0, "regenerate": 1, "failed": 0}

| task | verdict | detail |
|---|---|---|
| GHSA-q238-5cxm-5c9h | REJECTED | rubric: The security tests don't tell vulnerable code from fixed code. Nesting a Multi* inside a Multi* of the same kind breaks GEOS's child-type check, so on t |
| GHSA-q2xc-rrxj-58x9 | REJECTED | isolation audit: fix code is readable inside the image: /usr/local/lib/python3.11/site-packages/starlette/middleware/cors.py contains 2 of the fix's added lines |

## 2026-10-16T09:10:37Z - Stage 4 - rubric + oracle validation

counts: {"ok": 1, "failed_oracle": 0, "rejected": 0, "regenerate": 0, "failed": 0}

| task | verdict | detail |
|---|---|---|
| GHSA-q2xc-rrxj-58x9 | ok | oracle 1.0, pre-patch fails as required; existing pass->pass tests: 0 (from 15 candidate files); fix checks: shallow leaves 7/8 security tests open, removal bre |

## 2026-10-16T10:18:33Z - Stage 4 - rubric + oracle validation

counts: {"ok": 0, "failed_oracle": 0, "rejected": 0, "regenerate": 0, "failed": 1}

| task | verdict | detail |
|---|---|---|
| GHSA-q2xc-rrxj-58x9 | REJECTED | check patch 'removal' produced no per-test verdict: no trial |

## 2026-10-16T10:27:45Z - Stage 4 - rubric + oracle validation

counts: {"ok": 0, "failed_oracle": 0, "rejected": 0, "regenerate": 1, "failed": 0}

| task | verdict | detail |
|---|---|---|
| GHSA-376h-93r7-7g6f | REJECTED | oracle does not pass its own tests (reward [0.0, 0.0], failing: ['::test_functional_adapter_path_serves_real_admin', '::test_functional_adapter_path_serves_real |

## 2026-10-16T11:09:16Z - Stage 4 - rubric + oracle validation

counts: {"ok": 1, "failed_oracle": 0, "rejected": 0, "regenerate": 3, "failed": 1}

| task | verdict | detail |
|---|---|---|
| GHSA-2q76-m6w6-qgc6 | REJECTED | oracle does not pass its own tests (reward [0.0, 0.0], failing: ['::test_functional_owner_can_create_own', '::test_functional_owner_can_create_own', '::test_fun |
| GHSA-376h-93r7-7g6f | REJECTED | oracle does not pass its own tests (reward [0.0, 0.0], failing: ['::test_functional_adapter_path_serves_real_admin', '::test_functional_adapter_path_serves_real |
| GHSA-mcm9-63f2-9j32 | ok | oracle 1.0, pre-patch fails as required; existing pass->pass tests: 0 (from 6 candidate files); fix checks: shallow leaves 2/6 security tests open, removal brea |
| GHSA-w3v8-gmh9-3wv7 | REJECTED | check patch 'shallow' produced no per-test verdict: EnvironmentStartTimeoutError: Environment start timed out after 1200.0 seconds |
| GHSA-x78j-v8h9-3j2q | REJECTED | rubric: The tests treat raising an exception from generate() as a failure, although erroring out on an unsafe value is a reasonable way to block and the report  |

## 2026-10-16T11:23:51Z - Stage 4 - rubric + oracle validation

counts: {"ok": 1, "failed_oracle": 0, "rejected": 0, "regenerate": 0, "failed": 0}

| task | verdict | detail |
|---|---|---|
| GHSA-q2xc-rrxj-58x9 | ok | oracle 1.0, pre-patch fails as required; existing pass->pass tests: 406 (from 15 candidate files); fix checks: shallow leaves 7/8 security tests open, removal b |

## 2026-10-16T11:43:16Z - Stage 4 - rubric + oracle validation

counts: {"ok": 1, "failed_oracle": 0, "rejected": 0, "regenerate": 0, "failed": 0}

| task | verdict | detail |
|---|---|---|
| GHSA-w3v8-gmh9-3wv7 | ok | oracle 1.0, pre-patch fails as required; existing pass->pass tests: 38 (from 4 candidate files); fix checks: shallow leaves 3/6 security tests open, removal bre |

## 2026-10-16T12:49:46Z - Stage 5 - DeepSeek / MiMo evaluation

counts: {"rejected_too_easy": 2}

| task | status | rewards per model | detail |
|---|---|---|---|
| GHSA-q2xc-rrxj-58x9 | rejected_too_easy | deepseek: [1.0] ; mimo: [] | solved by deepseek |
| GHSA-w3v8-gmh9-3wv7 | rejected_too_easy | deepseek: [1.0] ; mimo: [] | solved by deepseek |

