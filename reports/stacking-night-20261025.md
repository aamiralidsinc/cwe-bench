# Stacking night report, 2026-10-24 19:25 to 2026-10-25 04:40 UTC

## In short

- **8 both-model breaker candidates.** Each failed DeepSeek V4.1 Flash 3/3 and MiMo-V2.6-Pro 3/3. Every
  counted failing run had its own Opus 5.5 audit, and every fairness review is READY. That is 4 times the
  number we had when the night started, which was 2 (dagu, filebrowser).
- **The instruction upgrade was the main gain.** 12 task/model pairs that solved v1 failed 3/3 after the
  rewrite. The reverse happened 6 times, and every one of those v1 failures was a test fault we fixed.
- **Stacking adds difficulty on its own.** The stacked task failed while its one-bug control was solved in
  5 tasks (DeepSeek) and 6 tasks (MiMo). The reverse never happened.
- **No breaker is committed or shipped.** Each one has a `build/<slug>/NEEDS_HUMAN_REVIEW.md` on the VM.

## 1. Breaker candidates

| Task | Version | DeepSeek | MiMo | What decided it | Class | Status |
|---|---|---|---|---|---|---|
| dagu | v1 | 0.8, 0.8, 0.8 | 0.8, 0.8, 0.8 | git-sync pull decodes `%2E%2E%2Fevil.yaml` and writes it outside the DAGs folder | unreported, unfixed upstream (T6) | test fixed in place to accept both refusal forms; gate sound; no verdict changed |
| filebrowser | v1 | 0.86, 0.71, 0.86 | 0.86 ×3 | recursive copy onto an escaping child link; 5 of 6 runs blocked the write but returned 500 | unreported, unfixed upstream (T4) | **kept** (user: status code plus sloppy error handling = fair) |
| gitpython | v2 | 0.875 ×3 | 0.375, 0.625, 0.375 | DeepSeek missed git's `--exec` alias on ls-remote; MiMo missed the shared option builder | DeepSeek: unreported, unfixed upstream (T5) | **kept** (fairness: expert knowledge) |
| mistral-rs | v2 | 0, 0, 0 | 0, 0, 0 | both made the public loaders refuse local files; security 13/13 wherever it was measured | keep-working break | **kept; confirm with Klavis** |
| senaite | v2 | 0.82 ×3 | 0.82 ×3 | the read route runs any method the caller names (`include_methods`) | unreported, unfixed upstream (T9) | **kept** (fixture stays) |
| lemur | v3 | 0, 0, 0 | 0, 0, 0 | both re-validated addresses already stored, so legacy authorities broke; security 11/11 in every run | keep-working break | suggest the same as mistral-rs (ask Klavis) |
| vikunja | v2 | 0.83, 0.83, 0 | 0.83, 0, 0.83 | 4 of 6 runs linked a verified sign-in to an unconfirmed local account; 2 broke the string `email_verified` claim | injection room plus keep-working | needs your call: is "protections the product already applies" a fair cover? |
| tensorflow | v1 | 0, 0, 0 | 0, 0, 0.8 (3 h) | reshape setup dereferences an absent shape input; DeepSeek also over-refused at setup | unreported, unfixed upstream (T3) | needs your call (fairness question on setup-time refusal); v1 instruction still FAILS the listing check; its control also fails DeepSeek 3/3 |

**Not a clean breaker: mlflow (v3).**
- DeepSeek 0/3 is fair. MiMo has 2 fair fails and 1 run audited UNTRUSTED for instruction ambiguity.
- One test decides nearly every run: the shipped Ollama default must still work.
- The instruction does not say whether choosing `provider: ollama` counts as a "user-supplied value".
- An instruction-only repair is proposed in its NEEDS_HUMAN_REVIEW.md. It is not applied; it needs a new
  version and a re-trial.

**A new class, recorded at the user's request:** a real bug that is outside the advisory and outside the
upstream fix (`build/audit/UNCOVERED-UPSTREAM-CLASS.md`).
- It decides 4 of the 8 breakers, plus both MiMo-only leads.
- The models fix the reported route and the published siblings, then stop.

## 2. Leads that fail one model only (3/3, audited, fairness READY)

| Task | Fails | Other model |
|---|---|---|
| langflow | DeepSeek 0/3 (missed the second storage copy) | MiMo solved |
| elfinder (v3) | DeepSeek 0/3 (`..` identifier, backslash names) | MiMo solved (awaits audit) |
| fabio (v4, reworded tonight) | DeepSeek 0.64 ×3 (designated client-IP header, gRPC metadata) | MiMo solved (awaits audit) |
| avideo-wc3f | MiMo 0.875 ×3 (unquoted restream log path) | DeepSeek solved |
| uri-js | MiMo 0.8, 0.57, 0.9 (leading C0 characters) | DeepSeek solved |
| kyverno (v3) | MiMo 0/2 so far | DeepSeek solved |

## 3. Results per model (current version of each task; raw trial states, solves still await audit)

| | Solved | Failed 3/3 | In progress | Not run |
|---|---|---|---|---|
| DeepSeek, 30 stacked | 18 | 12 | 0 | 0 |
| MiMo, 30 stacked | 17 | 11 | 2 | 0 |
| DeepSeek, controls | 22 | 1 (tensorflow) | 0 | 7 |
| MiMo, controls | 22 | 0 | 1 | 7 |

A solve cannot make a breaker, so the solve audits were left for last. About 35 solves still await audit;
a solve that fails its audit would only reopen a pair.

## 4. v1 vs the upgraded instruction

There are 38 task/model pairs with runs on both v1 (archived) and the current version:

| v1 → current | Pairs | Tasks |
|---|---|---|
| solved → failed 3/3 | **12** | gitpython ×2, lemur ×2, mistral-rs ×2, vikunja ×2, mlflow ×2, elfinder (DeepSeek), uri-js (MiMo) |
| failed → solved | 6 | avideo-ghsaghcv ×2, mjml ×2, siyuan ×2. All three had v1 test faults, which were fixed tonight |
| solved both | 18 | |
| failed both | 2 | avideo-wc3f (MiMo), fabio (DeepSeek) |

So the upgrade (removing hints about hidden traps from the instruction) produced 4 of the 8 breakers:
gitpython, mistral-rs, lemur and vikunja.

It also damaged 11 of the 22 instructions it rewrote: it deleted carve-outs instead of rewording the rules.
Every damaged instruction was repaired before its counted runs, and upgrade prompt v2 adds rule 3.

**Lesson:** after an upgrade, run a contradiction check before trials. Five of the 30 tasks were never
upgraded:
- dagu and filebrowser were already breakers;
- tensorflow was left to finish its decision;
- lobe-chat already passed the listing check;
- mjml went down the test-fault path.

## 5. Stacked vs one-bug control (both trialled, current versions)

| Model | Stacked fails, control solved | Both solved | Both fail | Stacked solved, control fails |
|---|---|---|---|---|
| DeepSeek | 5 | 17 | 1 (tensorflow) | 0 |
| MiMo | 6 | 16 | 1 | 0 |

Correction to an overnight message: MiMo did solve the langflow control once (a run before its three
failures), so there is no stacked-vs-control inversion.

**A build-step gap in senaite-control:** its instruction equals the stacked one (rule 13) and asks for two
fixes, but the control tests and reference cover only the first. When a report names two problems, the
control needs both.

## 6. Wall time and usage per stage (whole stacking batch, cumulative)

| Stage | Runs | Agent hours | Output tokens | CLI-estimated cost |
|---|---|---|---|---|
| Build (DeepSeek builder) | 28 | 19.1 | 1.0 M | $314 |
| Gate (container: nop, oracle, patches) | 48 full gates on record; 342 failed stage attempts (194 task, 148 infra) | median 31 min per full gate, p90 86 min | n/a | n/a |
| Listing check | 34 | 0.7 | 0.5 M | $11 |
| Upgrade (instruction only) | 31 | 0.5 | 0.3 M | $8 |
| Fairness review | 17 | 1.8 | 1.0 M | $30 |
| Fairfix / repair | 17 | 1.0 | 0.2 M | $56 |
| Trials, stacked, DeepSeek | 128 runs (109 graded, 34 solves) | 52.6 (median 23 min/run) | 14.0 M | n/a |
| Trials, stacked, MiMo | 118 runs (95 graded, 33 solves) | 118.7 (median 61 min/run) | 1.0 M | n/a |
| Trials, controls, DeepSeek | 60 runs (49 graded) | 22.7 | 6.6 M | n/a |
| Trials, controls, MiMo | 59 runs (50 graded) | 56.1 | 0.8 M | n/a |
| Post-run audits (Opus 5.5 high, sub-agents) | ~110 runs audited in total, ~60 tonight | ~2-4 min each | n/a | n/a |

About the cost column: the CLI-estimated cost is Claude Code's own estimate for the routed DeepSeek
sessions, not a bill. MiMo trials are about 2.6 times slower per run than DeepSeek and dominate trial wall
time.

## 7. Fixed overnight

- **Harbor refused 27 trial starts under load.** The 30 s nftables probe timed out, and those starts were
  wrongly refused as "allowlist not supported". The timeout is now 300 s, with a backup in
  `docker.py.bak-probe30-20261025`. There were 0 refusals after the patch.
- **Harness and test faults repaired:**
  - jenkins: the fixture's realm could not be serialised.
  - siyuan and siyuan-control: the icon test contradicted the instruction.
  - senaite and senaite-control: the stub API module hid helpers a fix adds.
  - pyload-4744: the startup test read the saved value instead of the effective one.
  - senaite record test.
  - dagu sync refusal form.
  - Earlier: mjml and avideo.
- **Process errors fixed:**
  - A stale hold blocked the kyverno-control trials.
  - A stale queue run was still testing siyuan-control on old tests.
  - The finished queue was not restarted blindly, because it would duplicate the running pairs.
- **Audit integrity:** a shared-scratchpad collision was spot-checked across 56 verdicts and nothing was
  corrupted. Auditors now use unique local folders.
- **The three held tasks went to trial on your decision:**
  - comfyui and pyload-7gvf: their wording was accepted, with a `LISTING_WAIVER.md` each.
  - fabio: reworded to drop `X-Real-Ip`, then accepted.

## 8. Decisions (updated 2026-10-25 ~05:50 UTC)

All 8 breaker candidates are now **kept**:
- vikunja: fair. The product already refuses unconfirmed accounts at password login and at password reset.
- tensorflow: stays at v1, with no upgrade.
- mistral-rs and lemur: confirm with Klavis (the keep-working class).
- mlflow: the instruction-only repair is in progress (scope the destination sentence, then gate and
  re-trial).

The original list follows for the record.

1. **lemur:** keep it and ask Klavis, like mistral-rs?
2. **vikunja:** is "protections the product already applies" a fair general cover for the unconfirmed
   local account?
3. **tensorflow:**
   - Is a setup-time refusal of a not-yet-filled input an over-broad fix?
   - Should we upgrade its v1 instruction? That means a re-trial from zero.
4. **mlflow:** apply the instruction-only repair and re-trial?
5. Still running: MiMo on comfyui (0.9 so far), kyverno and tensorflow-control, plus the controls. None of
   these can become a both-model breaker. The other model has already solved each one:
   - DeepSeek solved comfyui, pyload-7gvf and kyverno.
   - MiMo solved fabio and elfinder.
