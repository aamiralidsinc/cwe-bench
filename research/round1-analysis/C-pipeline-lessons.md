# C. What round 1 taught us about the pipeline itself (2026-10-16)

Question: what did round 1 teach us about the process, its cost and its reliability, and what
should change before round 2? Scope: the pipeline (screen → build → gate → trial → audit →
repair), not what makes a task hard.

Sources: `sourcer/index/candidates.sqlite` (read-only), `sourcer/*shortlist*`, `build/queue.json`,
`build/*/manifest.json` and `notes.md` (the 16 "2026-10-16 test repair" sections),
`build/audit/*.tsv`, `build/audit/lenient_items_2026-10-16.txt`, `RESULTS.md`, `build/RESULTS-AUDIT.md`,
`research/own-runs/{FINDINGS,TEST-REPAIRS}.md`, `builder/{BUILDER.md,gate.py,templates/}`,
`build/{TRIAL-PROCEDURE.md,queue_offline.py,slot.py,harvest_code.py,postmortem.py}`. I also
scanned every `result.json`, `regrade-*/REGRADE.json` and `postmortem-*/verdict.json` under
`~/.tb-graders/cwe/jobs` (186 trials), plus `~/.tb-graders/cwe/gate-jobs` (480 gate stage runs).
The ledger is the one from 08:34 UTC today. trigger-dev's repair is still running.

Caveats:
- n is small (19 tasks, 38 pairs).
- Builder and auditor wall-clock and token costs were **never recorded**, so those costs are
  marked "not measured".
- My hour split by run category (§3) re-implements `audit_results.py`'s exclusion order in a
  scratch script. It agrees with the ledger's category counts to within a few runs, not exactly.
  For example, it puts 28 solves in "used the internet" where the ledger has 20. The difference
  is that the ledger files some of them under "awaiting audit" first.

---

## 0. The short version

1. **The tests were the weakest stage, and they were wrong in both directions.**
   - 15 of the 56 regrades changed a reward: 8 went up (the test rejected a correct fix) and 7
     went down (the test accepted a wrong fix).
   - Of the 5 one-model failures reported on 10-15 (RESULTS-AUDIT §5), 3 were test faults:
     actualbudget/MiMo, stigmem/MiMo and trigger-dev/DeepSeek. One more was the 60-min limit
     (asyncssh/MiMo). Only jackson-databind-sib/DeepSeek was genuine.
   - The 16 repairs added about 55 new wrong-fix patch checks. The first-pass gate had about 3-5
     per task. So roughly half of today's ~120 patch checks are wrong fixes that round-1 tests
     would have scored 1.0, or that would have failed a correct fix.
2. **About half the agent time produced no usable evidence.**
   - Total: 109 agent-hours over 186 trials.
   - Usable: about 41 h ended in counted, audited runs.
   - Redundant: about 13 h were extra solves of pairs that were already settled.
   - Invalidated, about 55 h, by our own faults or by setting changes made mid-round:
     - internet lookups: ~20 h
     - leaked answers or unstated contracts: ~13 h
     - runs cut at 60 min: ~9 h
     - ungraded or infrastructure: ~7 h
     - test faults: ~4 h
     - leaked hidden tests: ~1.5 h
3. **Most of the gate time was rework.**
   - There were 51 gate sessions and 32 of them were re-gates.
   - 10-16, the repair day, used 12.8 of the 19.9 gate container-hours (241 of 480 stage runs).
   - That day's gates took a median of ~30 min against ~7 min in the first pass, slowed by a full
     Docker disk, a lost build cache and contended slots.
4. **Most of the fixes already exist, but as per-task patches or opt-in flags, not as defaults.**
   - `strict_gate` is set by **no** manifest.
   - The templates have neither the offline allowlist nor the agent-kill step.
   - No pre-trial fairness review exists.
   - The flakiness check is still 2 oracle runs.
   - Nothing checks disk space.
   - The trial queue and the gate/regrade slots have separate caps.

---

## 1. Funnel per track

| Stage | Mined | Stacking | Injection (siblings) |
|---|---|---|---|
| Screened | 37,416 OSV advisories in the index. 1,462 passed the diff-stage classifier (1,442 `candidate` + 20 `shortlisted`); 19,594 rejected, mostly no fix commit (9,791), no GitHub repo (3,254) or no CWE (3,089); 15,217 deferred (outside the recency window) | 1,179 repos passed the co-presence filter (4-10 co-present advisories, ≤ 60 total, not a giant) | Bases come from mined tasks |
| Read by hand | 62 rows in `review/annotations.tsv` (16 keep-main, 4 keep-control, 38 skip, 2 drop) | Top 20 by score (`stacking-shortlist.md`) | 6 bases considered |
| Shortlisted | 20 (16 main + 4 controls) | 20 | 6 |
| Build attempted | 6 from the shortlist (ranks 1, 2, 5, 7, 8, 13), plus py-shiny from Task13 outside the screener = **7** | **8** (ranks 1, 4, 5, 6, 7, 9, 11, 20). Ranks 2, 3, 8, 10 and 12 (praisonai, studiocms, sentry, sglang, formie) were skipped, and no reason is recorded | **6** attempted. async-sib and tomcat-sib were abandoned (single sink, no second site), so **4** were built |
| Gate passed (first pass) | 7/7 | 8/8 | 4/4 |
| Trialled | 7 tasks, 14 pairs | 8 tasks, 16 pairs | 4 tasks, 8 pairs |
| Final audited pairs | 14 solved, 0 failed | 15 solved, 1 open (asyncssh/DeepSeek) | 7 solved, **1 failed** (jackson-databind-sib/DeepSeek) |
| Breakers | 0 | 0 | 0 |

Process observations:
- **Every built task passed the gate on the first pass, and the gate still let through 3 false
  failures and at least 8 false or lenient solves** (§2).
  - The first-pass gate was a necessary check, not a sufficient one.
  - Its yield (19/19) tells us it was too easy to pass, not that the builds were good.
- **The 4 mined controls and 10 mined main candidates were never built.**
  - Once the pilot showed that mined tasks are solved, building was stopped.
  - The controls were meant to calibrate the screener, so the screener's ranking was never
    tested against a control.
- **The reasons for skipping stacking candidates are not recorded** (no file mentions
  praisonai, studiocms, sentry, sglang or formie outside the shortlist).
  - Round 2 should log every skip with a reason, as `annotations.tsv` does for mined.
- **Per-pair run counts were uneven before the queue learned to stop at the first solve:**
  py-shiny/DeepSeek had 24 runs, jackson-sib7/DeepSeek 15, filament/DeepSeek 9 and
  trigger-dev/DeepSeek 9. 34 extra solves (~13 agent-h) were never audited, because one trusted
  solve settles a pair.

---

## 2. Every fault class we hit

Numbers are runs or tasks as stated. "Caught by" is the first mechanism that surfaced the fault.
"Effect" is what the fault did to verdicts.

### 2a. Test faults that failed correct fixes (tests too strict)

| Fault | Tasks hit | Caught by | Effect |
|---|---|---|---|
| **One exact refusal status** (405, 403, `codes.PermissionDenied`) | trigger-dev (realtime write 405), argo (403/PermissionDenied), cloudreve (403), filament (403) | own-runs transcript analysis (trigger-dev); audits | trigger-dev/DeepSeek reported "failed"; r2 and r4 regraded 0 → 1.0. Gate check added 10-16 (`exact_status_asserts`) |
| **Test calls a product helper the agent can change** | actualbudget (`getPathForUserFile`) | own-runs analysis (verifier stdout) | actualbudget/MiMo reported "failed 0/3". The 3 runs had no saved code and were excluded, and 3 re-runs were needed. Gate now lists `security_test_product_imports`; a `hardening` patch is required only under `strict_gate` |
| **Constant or contract the instruction never states** | argo (2 MB cap from upstream); ruby-saml (`ValidationError` + `/exceed/i`); rclone and rclone-sib (`_secret_access_key` field); filament ("refuse as a client error"); hickory (error type); stigmem (acknowledgement setting, left ungradable) | audits; repair agents | argo/MiMo VSELT69 excluded. rclone and rclone-sib: every run before 10-16 01:57 voided (`task_defects.tsv`). 4 instruction sentences were added (cloudreve, filament, hickory, russh-sib) |
| **Wrong knob** (varies `node_url`; the instruction says bind host) | stigmem v2/v3 | own-runs analysis | stigmem/MiMo reported "failed 0/3"; 2 runs regraded 0 / 0.44 → 1.0; 2 runs excluded (no code) |
| **Wrong layer** (internal function instead of the named entry point) | stigmem v4 | own-runs analysis | as above |
| **Fixture outside the instruction's scope** (a batch that does not exist where the instruction says "their own batches") | trigger-dev check-completion | own-runs analysis | part of the trigger-dev/DeepSeek false failure |
| **Test outside the instruction** (bare protocol-relative URL) | webob | audit (CeNzGqe) | 2 runs regraded 0.9 → 1.0 |
| **Refusal raised outside the test's try block** | stigmem (Settings / `create_app`, `sys.exit` as `CancelledError`) | repair agent | none observed; fixed in the repair |
| **Instruction wording induces a wrong design** ("tens of millions of pixels" read as the bomb, so a 16.7 MP cap) | cloudreve | audit + repair | both 1.0 runs would fail the new 24 MP test. They were kept at 1.0 because the requirement is new |
| **Runner setting distorted partial scores** (nextest fail-fast cut security tests from the JUnit) | russh | repair agent | partial rewards only; 1.0 was unaffected |

Totals:
- 8 runs went up on regrade.
- 6 runs were excluded as `test-fault`, not regradable.
- 3 of the 5 one-model failures reported on 10-15 were test faults (actualbudget/MiMo,
  stigmem/MiMo, trigger-dev/DeepSeek). asyncssh/MiMo was the 60-min limit, and
  jackson-databind-sib/DeepSeek is the only genuine one.
- **Every false failure we found came from a test rule that §3g now states.**

### 2b. Lenient tests that passed wrong fixes (false or inflated solves)

| Fault | Tasks | Caught by | Effect |
|---|---|---|---|
| **Refuse-all / deny-all passes** (no positive control for the protected path) | rclone-sib (MiMo ypUhTQw **counted SOLVED, false**); rclone (deny-all scored 1.0); hickory (fail every validating lookup); stigmem (refuse every public bind); trigger-dev (delete the write route) | audits | rclone-sib/MiMo moved SOLVED → open, then re-solved on repaired tests |
| **Stubs that answer the same for every resource or verb** (fake RBAC) | argo sync + template | own-runs + audits | argo r11 DeepSeek QprUNQg and MiMo b5WYen5 regraded 1.0 → 0.75 → 0.7059 |
| **Crash, panic or HTTP 500 counted as a refusal** | stigmem, filament, russh, russh-sib, hickory (any error) | audits; repair agents | filament/MiMo r11 1.0 → 0.75 (set aside: the rule is newer than the run). New `crash_not_refuse`, `panic_refusal`, `upload_crash_refusal` checks |
| **One-role / one-direction fix passes** (both peers run the patched library) | russh, russh-sib | audit (t2scdx3, r1-n002) | raw-peer and vulnerable-peer tests added |
| **Missing variant of a stated property** | asyncssh (dropbear −1 packet size), async-http-client (strict cookie decode), rclone (no-secret fallback), argo (`templateDefaults`), webob (`relative_url('//host')`), actualbudget (overwrite/reset/download), trigger-dev (other-org member, SSRF spellings), ruby-saml (scan-then-reject), jackson-databind (value-before-discriminator), cloudreve (banned status, absolute target) | audits (27 item-level `lenient-test` verdicts; 34 flagged items over 13 tasks; 87 recommendations) | 7 solves dropped on regrade: asyncssh DeepSeek r11 (0.9167), async-http-client DeepSeek uGhFbba and MiMo tfkenPc (0.8333, reconstructed code), rclone DeepSeek r11 (0.9), webob MiMo r12 (0.0), argo r11 ×2. asyncssh/DeepSeek is open again |

Two lessons for the process:
- Leniency hides in **solves** and strictness hides in **failures**. Both distort verdicts:
  - a lenient test rejects a task that might have been a breaker (asyncssh/DeepSeek);
  - a strict test invents a breaker that is not one (actualbudget/MiMo).
- Neither is visible from the reward alone. Only reading the code against the instruction
  catches them, which the audits did.

### 2c. Leaked tests or answers in the image or the instruction

| Fault | Count | Caught by | Fix |
|---|---|---|---|
| Hidden tests baked into `/opt/harness` (shared container) | 5 tasks (hickory-dns, rclone, rclone-sib, russh, russh-sib); 7 runs read or ran them | transcript scan, 10-15 | `test.sh` copies the tests in at grading time; the gate's `hidden_test_leaks` check and a §3c rule (done) |
| Vulnerable commit = upstream's "Add regression tests" commit (expected outputs + fix comment in `/app/tests`) | webob; 6 runs voided | audits (yZH7hQv, ksABBkj) | rebased to the parent commit `b240857`. **No gate check exists for this class** |
| Instruction names the sibling mechanism | jackson-sib7 (DeepSeek found the siblings in 10/11 sib7 runs vs 0/6 sib runs) | own-runs comparison | §3f "blind agent names mechanisms" rule. **Manual, not automated** |
| Grader trusts agent-writable files (`/opt/target` build output; `/app/tests` bootstrap; `/app/vendor`) | hickory (fixed: fresh target/cargo home); filament (skipped); generic in shared-mode grading | audits | not exploited in any run; generic fix not done |

### 2d. Internet lookup of the upstream fix

- Runs that fetched the advisory or fix solved 43/44 (98%). Runs that did not solved 40/62
  (65%) (`research/own-runs/FINDINGS.md`).
- **Offline switch:** 10-15 23:35 UTC for 17 tasks, 10-16 01:57 for rclone and rclone-sib.
  Enforced by Harbor's allowlist, which lets only the model APIs through.
- **The allowlist had a hole until 10-16 00:33:** Claude Code's WebSearch runs on the provider's
  side, so it got through. Filament DeepSeek r11 got live results, and its audit marks it
  `contaminated`. The fix was `--ak disallowed_tools=WebSearch,WebFetch`.
- **Cost:** 20 solves discounted in the ledger, plus a full offline re-run of every pair:
  31 runs, ~25 agent-h.
- **Status:**
  - Done in all 19 `task.toml` files and in `run_trial.sh`.
  - **Not in `builder/templates/task.toml`.**
  - The gate does not check for it.

### 2e. Flaky tests

| Flake | Found when | Why the first-pass gate missed it |
|---|---|---|
| trigger-dev oracle 0.0 / 1.0. A clock step under load gave a deployment an earlier `createdAt`, so the next version number collided (HTTP 500) | repair gate try 3, 10-16 | the gate runs the oracle only 2×, on a quiet VM. The flake needs a clock step, which load causes |
| cloudreve `PUT /file/viewerSession` returned no data once right after an upload | repair gate, 10-16 | the same reasons |
| Harbor egress probe "allowlist not supported by EnvironmentType.DOCKER" under VM load | asyncssh gate 1, trigger-dev try 1 | it is infrastructure, not a test, but it shows as a gate failure |

### 2f. Missing final-code harvests

- **137 of 186 trial folders have no `final-code/`.** These are all runs started before about
  10-15 afternoon. `harvest_code.py` was wired into `trial.py` on 10-15.
- What it cost:
  - 6 test-fault runs could not be regraded, so they were excluded, and actualbudget/MiMo had to
    be re-run 3 times.
  - Most 10-13/14 solves cannot be checked against repaired tests.
  - The workaround was to rebuild the final code from transcripts. 4 official regrades used it
    (async-http-client) and about 10 informal checks (jackson-databind 6, russh-sib 4).
- **Harvest truncation:**
  - Filament DeepSeek r11's harvest hit the 500-file cap and kept 343 vendor/cache files and zero
    product source.
  - Grading it would have written a false 0.0, which `audit_results.py` would have preferred.
- **Postmortem bundles:**
  - They lacked `final-code/` until recently. Most of the 93 verdicts recommend adding it.
  - They still copy the **current** `tasks/<task>/tests`, not the version that was graded
    (trigger-dev xG36wVE audit).

### 2g. Infrastructure

| Incident | Count / impact | Status |
|---|---|---|
| Docker disk full on the Colima VM | 2+ windows on 10-16 (~05:45-06:30 UTC). They broke at least 6 gate or regrade attempts: argo gate d, rclone-sib nop, russh gate 1, a russh-sib oracle, trigger-dev try 2 and an asyncssh regrade. A 10-13 russh run's overlay was also at 100% | **No disk check anywhere** |
| Build cache loss after freeing disk (inferred) | gate image builds went from a median of 0.1-0.7 min and a max of ≤ 3.5 min before 10-16 04:00 to maxima of 25.5 / 29.7 / 15.7 min at 05/06/07 UTC; `speed_check.py` was written to flag them | not addressed |
| Slot oversubscription | 6 parallel trials on the 12 GB VM caused an OOM kill, so trigger-dev r4 was degraded (graded `harness`, then regraded). Gate/regrade contention on 10-16 led to `slot.py` (cap 3, later 2), and a `slot.py` bug when lowering MAX stopped cloudreve and argo gates | Memory gate in the queue (8 slots, ≥ 3.5 GiB free) and `slot.py` (3) are **separate caps on one VM**: up to 11 Docker jobs at once |
| Grader OOM (trigger-dev esbuild at 6 GB; a 4.5 GB core dump in `/app`) | 2 runs reviewed as `harness` | fixed for trigger-dev (8 GB, cleanup, timeouts) |
| Docker address pools exhausted (kept containers' networks) | queue stalls | `docker network prune` before each launch (done) |
| Agent not killed at timeout (Harbor) | 15 runs kept editing during grading; async-http-client tfkenPc audited untrusted for it | kill in all 19 `test.sh` (done); **not in the template** |
| 60-min limit, later 120 min | 11 non-solving runs voided as "cut at 60 min" (~9 agent-h); a 3 h re-run rule for timeouts | done (`CWE_AGENT_TIMEOUT_MULT`) |
| Provider stops | 1 ("considered high risk", jackson-databind-sib MiMo) | recorded as excluded |
| Ungraded runs | 27: CancelledError 12 (killed by us during churn), NonZeroAgentExitCode 7 (early DeepSeek config), killed with no result.json 3, rate limit 2, AgentTimeout without a grade 2, VerifierTimeout 1 | none counted as fails |
| Model config changed mid-round | DeepSeek env changed 4 times on 10-13 to 10-15 | eras recorded in RESULTS-AUDIT §4 |
| Our own reader bugs | `trial.py` read `config.json` as a trial (Python 3.9 `glob("*/")`), dropped graded timeouts, and read 1 trial per job. Result: false "None" and false "failed" verdicts, and a wrong "7 tasks voided by starvation" report | fixed; `audit_results.py` is the only source |

---

## 3. Cost and time

### 3a. Wall clock per stage

| Stage | Measured | Source |
|---|---|---|
| Screening | not measured; the stages are incremental (NVD/OSV bulk dumps, cached patches) | `sourcer/README.md` |
| Build (builder agent) | **not measured**: no start/end time or token count is recorded | none |
| Gate, first pass | 19 sessions, median **~7 min** (3-107 min; rclone 107, async-http-client 72, russh 42, trigger-dev 36, argo 29) | gate-jobs, sessions split at 1 h gaps |
| Gate, re-gates | 32 sessions. On the repair day: median **~30 min**, max 211 (trigger-dev), 194 (argo), 151 (cloudreve), 92 (russh-sib) | same |
| Gate total | 480 stage runs, 19.9 container-h. 10-13..15: 239 runs / 7.1 h; 10-16: 241 runs / 12.8 h | same |
| Trial | 186 runs, **109 agent-h**. Agent phase median 33 min (max 112). Image setup median 0.1 min (max 8.4). Verifier usually < 1 min (trigger-dev median 3.2, max 25) | `result.json` |
| Inside a trial | of 61.8 agent-h measured (122 runs, 10-15): model/API ~74%, commands ~26% (tests 5.0 h, builds 2.8 h). Builds matter only for russh (13-23 of 66 min) and trigger-dev typecheck (15-17 min/run) | `time_breakdown.tsv` (stale since 10-15) |
| Audit | 124 bundles prepared, 93 verdicts (85 trustworthy, 8 not). Bundle-to-verdict median 2.3 min (IQR 1.7-4.4) from file times. Token cost not measured | postmortem dirs |
| Repair | 16 tasks, ~04:50-08:50 UTC on 10-16 with parallel agents; ~55 new patch checks; 48 regrades | notes.md, regrade dirs |
| Regrade | 56 regrades (8 on 10-15, 48 on 10-16). 15 changed the reward (8 up, 7 down) | REGRADE.json |

Per task, trial agent-hours ranged from 2.1 h (hickory-dns) to 11.6 h (trigger-dev). The total
for each task was driven by re-runs, not by task size: trigger-dev 11.6, rclone-sib 9.8,
async-http-client 9.8, stigmem 9.2, filament 8.7, jackson-sib7 8.5.

### 3b. First-pass work vs rework

Agent-hours by what became of the run:

| Category | Runs | Agent-h | Share |
|---|---|---|---|
| Counted (graded, audited trustworthy): solves | 38 | 31.0 | 28% |
| Counted: non-solves | 17 | 9.7 | 9% |
| Redundant: extra solves of an already-settled pair, never audited | 34 | 13.1 | 12% |
| Invalid, internet lookup (open-internet era) | 28 | 19.7 | 18% |
| Invalid, task leaked the answer or relied on an unstated contract (webob, rclone, rclone-sib) | 23 | 12.9 | 12% |
| Invalid, cut at the 60-min limit | 9 | 9.4 | 9% |
| Invalid, test fault (not regradable) | 6 | 4.1 | 4% |
| Invalid, ungraded / grader fault / provider stop | 26 | 7.4 | 7% |
| Invalid, read leaked hidden tests | 3 | 1.5 | 1% |
| Untrusted audit | 1 | 0.5 | <1% |

Only **~37%** of agent time went into evidence that counts. **~51%** was voided by our own
faults or by setting changes made mid-round: open internet, leaks, the time limit, test faults
and infrastructure.

The gate and regrade side shows the same picture:
- **≥ 64%** of gate container-time and **86%** of regrades (48/56) were rework on 10-16.
- That figure does not count the 10-15 re-gates for leaked tests and the trigger-dev hardening.

The rework clusters on settings that were not fixed before trials started:
- network policy;
- time limit;
- where tests live in the image;
- what a refusal must look like;
- whether final code is saved.

Each of these is a one-time decision. Round 1 paid for each of them again on every run done
before the decision.

---

## 4. Changes before round 2, ordered by impact

Status: **done** = in effect for new work today; **partial** = exists but opt-in or per-task
only; **not done**.

| # | Change | Prevents (round-1 evidence) | Status |
|---|---|---|---|
| 1 | **Turn `strict_gate` on by default** (gate.py fails unless a manifest opts out as legacy). Require a `hardening` pass patch and a `blind` pass patch for every new task | product-helper crashes (actualbudget); tests that hard-code upstream's shape, which 8 regrades showed failing correct fixes | **partial**: the checks exist as warnings; **0/19** manifests set `strict_gate`; only actualbudget has `hardening` and only russh-sib has `blind` (and that one is a trial's own code) |
| 2 | **An independent fairness and leniency review of the tests before any trial.** A fresh Opus reviewer reads instruction + tests and produces the item list today's audits produced: for each assertion, is it stated or inferable from the instruction? For each security property, which plausible wrong fix would pass? Its findings become patch checks, so the gate must pass again after any change | all of §2a and §2b. The audits found 34 flagged items and 27 lenient-test verdicts *after* ~109 agent-h had been spent | **not done** (the fairness rule exists only in the post-hoc `REPAIR-BRIEF`) |
| 3 | **A required wrong-fix catalogue in the gate.** For each property class, the builder must supply the applicable checks: refuse-all/deny-all (`functional_fail`); crash/panic/500 instead of a refusal; wrong resource or verb against per-resource stubs; one role / one direction; reads verified but writes refused; string blocklist vs. resolved address; guard placed after a normalising adjustment. Gate: every listed class is present or carries a written N/A | ~55 checks added post hoc by 16 repairs; the rclone-sib false solve; argo stub leniency; the asyncssh −1 | **not done** (BUILDER §3f asks for one shallow + one disable patch only) |
| 4 | **Offline by default, enforced by the gate.** Put `[agent] network_mode = "allowlist"` + `allowed_hosts` in `builder/templates/task.toml`; gate static fails without it; keep `disallowed_tools=WebSearch,WebFetch` in `run_trial.sh`; run `harness/offline-check` once per round | 20+ internet-assisted solves; a full offline re-run (~25 agent-h); the provider-side WebSearch hole | **partial**: done in all 19 tasks and `run_trial.sh`; **template and gate not done** |
| 5 | **Always harvest final code, source-first, and fail loudly.** Remove the 500-file truncation for source paths (cap only build output), harvest during grading as well as after, and mark a run "not regradable" at once if no product source was captured. Postmortem bundles should use the *graded* task version from the archive, not the current `tests/` | 137/186 runs not regradable; 6 excluded test-fault runs and 3 re-runs; transcript reconstructions; filament r11's truncated harvest; the trigger-dev audit read the wrong test version | **partial**: harvest is done in `trial.py` since 10-15 and `final-code` is in bundles; **truncation and graded-version snapshot not done** |
| 6 | **Flakiness check under load.** Oracle ×5 (not ×2) plus nop ×2. At least 2 runs with other gates running at the same time; a fail on any repetition fails the gate | trigger-dev clock-step 500; cloudreve viewer session (both missed by 2 quiet oracle runs) | **not done** (oracle ×2) |
| 7 | **Leak checks the gate does not have yet.** (a) Fail if the vulnerable commit or `/app` contains test files added between the vulnerable commit and the fix (webob); (b) automate the blind-agent mechanism-naming check (jackson-sib7); (c) a grader integrity pass that rebuilds from fresh dirs and ignores agent-writable config (the hickory pattern), applied by default | webob's shipped regression tests (6 runs); jackson-sib7 wording; the hickory/filament shared-grader risk | (a) **not done**; (b) **partial** (manual §3f); (c) **partial** (hickory only) |
| 8 | **Template `test.sh` kills the agent before grading** | 15 runs edited during grading; tfkenPc untrusted | **partial**: done in all 19 tasks; **not in the template** |
| 9 | **Trial procedure: freeze the task, smoke it, then fan out.** One pilot pair per task first (catches harness and grader breakage on 1 run, not 6); then the queue's stop-at-first-trusted-solve; no counting before the audit; any test change means regrade the saved code and re-audit | 34 redundant solves (~13 h); py-shiny/DeepSeek 24 runs; mid-round setting changes | **partial**: audit-before-count, stop-at-first-solve and regrade-on-repair are **done**; the pilot pair and the version freeze are **not done** |
| 10 | **One global concurrency cap plus a disk budget.** A single semaphore shared by `queue_offline.py` and `slot.py`; before each launch, require free memory and free Docker disk (e.g. `df /var/lib/docker` ≥ 20 GB) or wait; prune with `docker builder prune --keep-storage` instead of wiping the cache; release kept containers after review on a schedule | the disk-full windows and ≥ 6 broken attempts; the cache-loss slowdown (builds 25-30 min); the 10-15 OOM; the slot.py MAX bug | **partial**: memory gate and network prune are done; **disk check, shared cap and cache-preserving prune are not** |
| 11 | **Image reuse in the gate.** Build the task image once per gate and reuse it for nop, oracle and every patch check (patch at container start) | ~12 of 19.9 gate container-h were image setup; repair-day gates took 30-211 min | **not done** |
| 12 | **Fix the trial settings before round 2 and don't change them mid-round**: offline, 2 h with a 3 h re-run, current model env configs, web tools off | voided runs from the 60-min cuts (~9 h), the open-internet era (~20 h) and config eras | the settings are decided; keep them frozen |
| 13 | **Record cost per stage**: builder and auditor start/end and tokens in each `build/<task>/` and postmortem dir; a skip reason for each shortlist row | could not measure build or audit cost in this analysis; unrecorded stacking skips | **not done** |
| 14 | **Instruction hygiene in the brief**: no magnitude phrases that suggest a limit ("tens of millions of pixels"); state every interface a test needs (`_secret_access_key`) or don't test it; state how to refuse (client error vs. exception) | the cloudreve cap; the rclone contract; the filament 500 | **partial**: §3g covers contracts; magnitude phrases and refusal form are covered only by today's per-task instruction sentences |

Why this order:
- 1-3 attack the faults that changed verdicts. Every false failure and every lenient solve came
  from test design, and the cheapest place to catch them is before trials.
- 4-5 protect the evidence. Without them a round can be voided after the fact, as happened twice
  in round 1.
- 6-8 are cheap gate additions.
- 9-11 are about cost and throughput.
- 12-14 are about discipline.

What is **already done today** and needs no further work:
- the §3g test rules;
- the exact-status gate check;
- the hidden-tests-in-`environment/` gate check;
- per-task offline allowlist + web tools off;
- per-task agent kill;
- final-code harvest in `trial.py`;
- kept containers + `regrade.py` / `regrade_from_code.py`;
- the mandatory Opus post-run audit + `audit_results.py` as the only source;
- `task_defects` / `excluded_runs` / `contaminated` bookkeeping;
- memory-gated queue with stop-at-first-solve;
- the 3 h timeout re-run rule;
- the write-once run archive.

One open question for round 2: whether the pre-trial review (#2) should be a second Opus reviewer
or the same auditor brief run against the oracle plus the patch checks. Round 1's audits were
effective, but they found faults only in runs that already existed. Running the same brief before
trials needs some candidate fixes to read. The blind and hardening patches from #1 are the
natural input.
