# Results audit — 2026-10-15

Reference for whoever reads trial results next (mostly me). Read this before
quoting any trial number.

## 1. The only source of truth

**Run `python3 build/audit_results.py`.** It reads the raw trial folders and nothing else,
then writes `build/audit/trials.tsv` (one row per trial) and `build/audit/ledger.md` (the
tables). RESULTS.md is built from its output.

Raw evidence per trial, under `~/.tb-graders/cwe/jobs/<job>/<task>__<id>/`:

| File | What it gives |
|---|---|
| `result.json` | `verifier_result.rewards.reward`, `exception_info`, UTC timestamps for every phase, `task_checksum`, token counts |
| `verifier/reward.json` | the same reward (fallback when there is no result.json) |
| `verifier/results.json` | pass/fail for every security and functional test |
| `config.json` | model name and agent env (shows which config era the run used) |
| `agent/claude-code.txt` | agent stream; a `{"type":"result"}` event means the agent stopped by itself |

**Do not use these to judge results.** The buggy reader wrote them, and they are wrong
for many runs:
`build/queue.json` (result/status text), `build/<task>/runs_<model>.log`,
`build/<task>/trial_detail_<model>.json`, `build/trial-matrix.md`. The fleet still uses
`trial_detail_*.json` to decide which (task, model) pairs are done; that is their only valid use.

## 2. Why earlier readings were wrong (three bugs, all proven)

1. **A file was read as the trial folder.** `trial.py` did `sorted(job.glob("*/"))[0]`.
   On this Mac's Python 3.9, `glob("*/")` also returns files (folder-only matching came in
   3.11). The sorted list for `filament-…` is
   `['config.json', 'filament__b5CEz3F', 'job.log', …]`, so the reader opened
   `config.json/result.json`, found nothing, and logged
   `reward=None, hit-agent-timeout (agent never emitted a result)`. It hit every task whose
   name sorts after `config.json` (filament, stigmem, trigger-dev, russh-sib, …). Tasks that
   sort before it (actualbudget, argo-workflows, asyncssh, cloudreve) read correctly. The
   recorded `trial_dir` values ending in `/config.json` prove this.
   **Fixed:** the reader now keeps only folders (`p.is_dir()`).
2. **Graded timeouts were thrown away.** When `exception_info` was set (an
   `AgentTimeoutError`), `trial.py` recorded the exception and never read the reward, even
   though the verifier had graded the run. This hid, for example, cloudreve/MiMo run 2
   (1.0) and async-http-client/MiMo (1.0). **Fixed:** the reward is always read, and the
   cause is marked `(graded)` or `(not graded)`.
3. **Only one trial was read per job.** Early jobs (`*-1013-*`, `*-1014-0514*`) ran 3 trials
   inside one job folder. Reading only the first one produced
   "jackson-databind DeepSeek failed 0/1" (the first trial alphabetically was its single
   0.0; the other two scored 1.0) and "async-http-client MiMo failed 0/1".
   `audit_results.py` reads every trial in every job.

The earlier theory that the problem was "reading stale runs from older eras" was wrong.
Every run is valid evidence (see the checks below). The problem was reading them badly.

## 3. Checks that the raw record is trustworthy

- **Grades are from run time, not added later:** for all 107 `reward.json` files, the file
  mtime is within 2 minutes of the verifier's own `finished_at`.
- **Each task stayed the same across runs:** every task has a single `task_checksum` over
  all its trials, so no run was against an older version of the task.
- **Coverage:** 125 trials (smoke tests excluded): 104 graded, including 18 graded at the
  timeout, and 21 ungraded.
- **Ungraded causes:** CancelledError 9 (runs I killed during the 10-14/15 churn),
  NonZeroAgentExitCodeError 7 (agent crashed; DeepSeek before the config fixes),
  ApiRateLimitError 2, AgentTimeoutError without a grade 2 (one each on trigger-dev
  DeepSeek and MiMo), killed with no result.json 1. None of them is a model failure.

## 4. Config eras (UTC, from each trial's config.json)

| Model | Env first seen | Since |
|---|---|---|
| DeepSeek | AUTO_COMPACT only | 2026-10-13 23:57 |
| DeepSeek | + MAX_OUTPUT_TOKENS | 2026-10-14 23:29 |
| DeepSeek | + API_TIMEOUT_MS | 2026-10-14 23:57 |
| DeepSeek | + DISABLE_ADAPTIVE_THINKING (current) | 2026-10-15 00:06 |
| MiMo | none | 2026-10-13 23:57 |
| MiMo | API_TIMEOUT_MS (current) | 2026-10-15 00:06 |

A solve in any era counts as a solve. A failure in an early era is weaker evidence, and
should be confirmed in the current config before it's built on.

## 5. The five one-model failures in detail

| Task / failing model | Graded runs (UTC start, reward) | What was missed | Kind |
|---|---|---|---|
| actualbudget / MiMo | 10-14 19:11 0.9; 19:45 0.9; 20:13 0.9 | the same test every run: `sync upload rejects path traversal in the file id` | **Blind spot**: stopped by itself after 21–33 min, every run. Old MiMo config, but no run was near the timeout, so the config doesn't explain it. Strongest signal. |
| jackson-databind-sib / DeepSeek | 10-14 14:22 0.625; 14:37 0.625; 14:55 0.0 | the same 3 injected siblings every run: `methodExtrasHidden`, `mapExtrasHidden`, `nodeExtrasHidden` (run 3 also broke `visibleTypeIdCreatorPropStillBound`) | **Blind spot**: stopped by itself after ~15 min. Early DeepSeek config; never re-run in the current one. |
| asyncssh / MiMo | 10-15 08:07 0.0 (0/5 security); 09:08 0.0 (4/5 security, 4/5 functional) | run 2 missed only `test_authorized_keys_username_traversal` and broke `test_per_user_pubkey_login` | **Out of time**: both runs hit 60 min |
| stigmem / MiMo | 10-15 03:33 0.0; 04:40 0.444 | different holes each run (self-registration, peer tokens, unsigned plugins, non-loopback insecure modes) | **Out of time**: both runs hit 60 min |
| trigger-dev / DeepSeek | 10-15 05:36 0.0 (0/8 security, 0/5 functional) + 1 timeout without a grade | everything, functional tests included: the repo was left broken mid-edit | **Out of time, thin**: 1 graded run. MiMo solved it at 58 min. |

Takeaway for task design: the "blind spot" kind (stops early and misses the same site every
time) is a capability failure that more time won't fix. The "out of time" kind depends on
the 60-minute limit and on how slowly the model works.

## 6. Evidence gaps (not needed for any verdict)

- MiMo was never run on hickory-dns or rclone. Both are already rejected because DeepSeek solved them.
- Several cells have fewer than 3 graded runs. That doesn't matter for "rejected" (one solve
  is enough), but a real pass@3 = 0 claim needs 3 graded failures on each model.
- jackson-databind-sib/DeepSeek failed only in the early config.

## 7. Time limit change and where timed-out runs spent their time (2026-10-15)

**Limit:** the agent limit went from 3600 s to 7200 s in the template and all 19 tasks. I had
set 3600 s on 2026-10-13 to match CWE-bench's one-hour rollout. The user's "2 hours" came from
the TB3 project, not this one, but they chose 2 hours for CWE-bench too. `run_trial.sh` now
passes `CWE_AGENT_LIMIT_SEC` so each trial's config.json records its limit (runs without it
ran at 3600 s). The ledger treats a non-solving run cut by a shorter limit as "cut", not failed.

**Claim checked: "timeouts came from long Java/Rust builds."** It doesn't hold in general.
Measured with `build/time_breakdown.py` from timestamped tool calls in each trial's
Claude Code session transcript (122 trials; output in `build/audit/time_breakdown.tsv`):

| Group | Runs | Build | Test | Other commands | Model (thinking + API wait) |
|---|---|---|---|---|---|
| Timed out, Java/Rust | 8 | 7% | 8% | 16% | 70% |
| Timed out, other languages | 12 | 7% | 7% | 5% | 81% |
| Finished, Java/Rust | 37 | 6% | 4% | 19% | 70% |
| Finished, other languages | 65 | 1% | 12% | 12% | 75% |

- 12 of the 20 timeouts were Python, Go, PHP or TypeScript, not Java/Rust.
- Java builds were not the issue: async-http-client spent 0.4 min building; jackson-databind 6.5 of 60 min.
- **Rust (russh) is the real exception:** cargo check/test took 13–23 of 66 min. The russh/DeepSeek
  run also lost 28 min to a sub-agent searching Claude Code's own install files.
- **The largest build cost was TypeScript:** trigger-dev's `pnpm run typecheck` took 15–17 min per
  run (25–29% of the hour). That affects the trigger-dev/DeepSeek failure.
- asyncssh/MiMo and stigmem/MiMo spent 56–59 of 60 min on the model side: they're slow, not
  blocked by builds.
- "Model" time includes API latency and can't be split into thinking vs network from these logs.

## 8. Procedure from now on

1. After any trial batch, run `python3 build/audit_results.py` and read `build/audit/ledger.md`.
2. To look at one run, open its raw `result.json` and `verifier/results.json`. Don't
   reconstruct results from logs or memory.
3. Never kill live runs (that caused 9 of the 21 ungraded trials).
4. Quote numbers only from the ledger, and say "graded" vs "ungraded" explicitly.

## 9. trigger-dev grader hardened (2026-10-15)

Three trigger-dev runs lost their grade because grading hung for the full verifier limit
(25 min, against a normal 2–4 min). The agent leaves its own dev server, Postgres or
restart-loop scripts running, and the old `test.sh` had no cleanup and no step timeouts.
In a fourth run (DeepSeek, 2-hour run 1), the grader's build failed and it tested the
image's old prebuilt, vulnerable server. That run was reviewed as a grader fault and is
excluded (`build/audit/reviews.tsv`).

Fix: `test.sh` first kills leftover agent processes (sparing its own process chain), and
every setup step and test group has a timeout. The verifier limit is now 2400 s.
Validated twice: the full gate passed, and a test copy whose solution applies the real fix
and then leaves a fake server on port 3030 inside a restart loop scored 1.0 (8/8, 5/5).
The cleanup killed both, so the real fixed app was tested.

Since then, any non-solve whose grading setup broke is "needs review" (build/review_flags.py),
not a model failure. Every run's final code is saved to `<trial>/final-code/`, and containers
of non-solves are kept for review (`build/audit/kept_containers.tsv`).
