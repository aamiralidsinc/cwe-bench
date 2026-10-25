# CWE-bench single-model breakers (audited register)

Tasks where exactly ONE target model fails 3/3 under a fair grader while the OTHER model solves it 1.0.
Verdicts authoritative from `build/audit_results.py`; each failing-side run independently audited (Opus-5.5-high).
The other model's clean 1.0 solve proves the hidden tests are passable, so these are genuine model misses, not test-faults.
Source: overnight hardening→trial run 2026-10-21→22 (hardening dropped from production; these are kept on their own merit). NOT committed/shipped; NEEDS_HUMAN_REVIEW.

## DeepSeek-only breakers (DeepSeek failed 0/3, MiMo solved 1.0) — 6

| # | task | DeepSeek rewards | audit | what DeepSeek missed |
|---|------|------------------|-------|----------------------|
| 1 | typo3-ds | 0.7273, 0.7273, 0.7273 | trusted model-failed high (3/3) | closed the generic record-API but missed the two raw-`ConnectionPool` write surfaces — admin JSON import (`ImportFormDefinitionsCommand`/`FormTransferService`) and the preset-rewrite tool (`FormDefinitionPresetService`); fails `AdministrativeImportTest` + `PresetRewriteTest` (the task's documented hard spot) |
| 2 | django-cms-ds | 0.95, 0.9, 0.95 | trusted model-failed high (3/3) | missed small page-permission sub-vectors: set-home demoting the old home without rights (r1); empty-POST `parent_page` → root add + move-to-root without site-wide add right (r2); empty-parent → root (r3). Reference guards each; functional 211/211 |
| 3 | backstage-ds | 0, 0.6604, 0 | trusted model-failed (r1/r3 high, r2 medium) | r1/r3 over-blocked a must-keep-working Bitbucket Server fetch (wrongly included `bitbucketServer` in the user-credential set) → functional fail → 0; r2 under-covered 18 GitHub/GitLab action siblings. (r2 evidence caveat: harvest truncated to dist-types; confirmed via transcript) |
| 4 | keras-ds | 0.9048, 0.8095, 0.8095 | trusted model-failed high (3/3) | drew the link/indirection scope too narrowly — refused soft-links only when they chain to an external file, but followed within-file soft-links; also missed a group-level external link reached via a non-open shard. Instruction explicitly covers "a link to another location … at any level" |
| 5 | airflow-ds | 0, 0, 0.825 | trusted model-failed high (3/3) | per-key secrets-backend kwargs: r1/r2 over-redacted the deployment-wide `backend_kwarg__role_id` that must stay visible (functional fail → 0); r3 under-concealed team-scoped per-key kwargs on 5 CLI + 2 startup-log paths (sec 33/40). Reference distinguishes via `is_sensitive_option()` |
| 6 | flyto-core-ds | 0.9231, 0, 0.9487 | trusted model-failed high (3/3) | confined the caller's output path but left paths the module *derives* (atomic temp siblings, pagination item/progress files) + in-sandbox symlinks unconfined; r2 additionally shipped a `NameError` (missing import) breaking a legitimate conversion → 0 |

## MiMo-only breakers (MiMo failed 0/3, DeepSeek solved 1.0) — 3

| # | task | MiMo rewards | audit | what MiMo missed |
|---|------|--------------|-------|------------------|
| 7 | airflow-info-exposure-inj | 0.1304, 0.8261, 0 | trusted model-failed high (3/3) | under-covered the many team-scoped secrets-backend spellings/surfaces each run (r1 only the landing route); r3 over-redacted a non-sensitive team option → functional fail → 0. Grader verified fair-by-construction (root-locked `/tests`) |
| 8 | prompty-ds | 0.7857, 0.6071, 0.7857 | trusted model-failed high (3/3) | r1/r3 never guarded the OpenAI provider adapters (`providers/openai/executor.py`, `openai/src/wire.ts`) so a path-escaping `kind=prompty` tool is still loaded; r2 shipped ineffective absolute-path/symlink containment across provider + tool-dispatch + Jinja routes (the lexical-vs-canonical weakness the task targets) |
| 9 | pimcore-ds | 0, 0, 0.9583 | trusted model-failed high (3/3) | PHP regex anchor bug — used `$` (matches before a trailing `\n`) instead of `\A…\z`, so a trailing-newline name slips through (r1/r3); r1 also left an objectbrick drop-index DDL path unquoted + over-restricted legit names (functional fail → 0); r2 shipped a non-parsing PHP file (fatal) → generation tests error → 0 |

## Pending (not yet a clean 3/3) — 1

| task | side | status |
|------|------|--------|
| hazelcast-ds | MiMo | r1 (0.8095) + r3 (0.9048) trusted model-failed high — real misses (JDK platform class with null `CodeSource` escapes detection; nested ineligible class thrown as an error instead of delivered as a generic record). **r2 = harness-or-infra (untrusted): MiMo provider content-moderation refusal, agent wrote 0 code.** Needs an r2 MiMo RE-RUN to complete 3/3. |

## Notes
- Audit mechanics: `build/postmortem.py prepare` on each failing-side run → one Opus-5.5-high auditor per task → `record-ready`; verdicts read from `build/audit_results.py`.
- MiMo provider content-moderation refusals recur on security tasks (also seen on hermes-agent-ds) — treat an aborted (0-code) MiMo run as infra, not a model failure, and re-run it.
- Pipeline bugs observed during this batch (verdicts unaffected): harvest truncation dropped real `src` edits in favour of cache/dist-types on a few runs (confirmed via transcripts); concurrent audit subagents must use unique scratchpad paths or write verdicts directly on the VM (a shared-path collision briefly cross-wrote intermediate verdict files — all final VM verdicts re-verified task-correct).

## Added 2026-10-25 (withdrawn both-model breakers and precision_validation)

| task | who failed | evidence | note |
|------|-----------|----------|------|
| knowns-ds | DeepSeek (0/3 on the VM, 0/3 in the at-risk re-trial) | MiMo solved the delivered package 1.0 (at-risk ta04, `ext-actions-atrisk-knowns-ds-mimo-a2`) | withdrawn from BREAKERS.md |
| pv-spring-ws | DeepSeek (0/3 [0.8,0.8,0.6], trusted medium) | MiMo a4 = 1.0 after the unfair XmppForeignDomain test was removed and the runs rescored | fairness READY otherwise; ledger agrees (rejected, MiMo solved) |

