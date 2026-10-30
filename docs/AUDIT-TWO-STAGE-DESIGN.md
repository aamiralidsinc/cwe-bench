# Two-stage audit: DeepSeek first pass, Opus at the breaker gate

Status: design, 2026-10-30. Not built. Owner direction: Claude credits are short, so move low-risk or
token-heavy audit work to DeepSeek and keep only high-risk judgements on Opus 5.5.

## Why

Today every failing run gets a full Opus 5.5-high audit as soon as it is graded. One audit reads about
500 KB of evidence per run (tests ~280 KB, transcript ~90 KB, reference fix, final code), roughly
30-40k Opus tokens per run.

Most of that work never decides anything. From 2026-10-28 to 2026-10-30, 506 Opus audits ran:

| Task outcome | Audits | Tasks |
|---|---|---|
| Solved later by a model (the audit could not make it a breaker) | 261 (52%) | 82 |
| Became a breaker candidate | 145 | 24 |
| Still open | 100 | 30 |

A fail only matters once a task reaches the breaker gate (both models fail 3/3). Before that, an audit
is only needed to catch two things early: infra trouble (rerun) and an unfair test that decided a run
(repair). Both can be caught more cheaply.

## The split

| Work | Who | Risk if wrong | Why this owner |
|---|---|---|---|
| Infra facts: timeouts, 429s, provider stops, truncated harvests, empty stdout, crashes vs assertion failures, tool calls inside the grading window | Script (no LLM) | Low: facts, checkable | Deterministic; already partly in `run.json` and verifier XML |
| Contamination signals: reads of `/tests`, WebFetch/WebSearch, upstream lookups, `find -newer`, netguard hits | Script, then DeepSeek reads the hits | Low: hits are quoted and checkable | grep finds candidates; DeepSeek says whether each hit is real |
| Which tests failed, which decided the reward (any functional fail = 0) | Script | Low | Arithmetic over verifier results |
| Dossier per failing test: test input and assertion (file:line), what the model changed for it (patch hunk), every candidate instruction sentence verbatim (all "keeps working" sentences + topic sentences), whether the failure goes through a stand-in or helper | DeepSeek (audit 1) | Medium: can miss or invent; contained by the quote check below | The token-heavy reading: transcript, tests, patch |
| Provisional label per failing test (fair / possibly unfair + kind / infra) and a thin flag | DeepSeek (audit 1) | Medium: never final, only routes work | Over-flagging is cheap; under-flagging is caught at the gate |
| Confirm a DeepSeek "possibly unfair and decided the run" item before the queue repairs tests | Opus (small, one item) | High: a wrong repair weakens a fair test | Narrow: dossier item + that test + the quoted sentences only |
| Final verdict for every failing run of a breaker candidate: fairness, keeps-working conflicts, one-implementation, scope, attribution, confidence, thin | Opus (audit 2) | High: this is what reaches the client | Same as today, but once per task, at the gate, from dossiers |
| Fairness review of a breaker candidate | DeepSeek (unchanged) | Judgement questions go to Opus or the owner | Already on DeepSeek |
| KEEP / park / drop, owner questions, anything sent to the client | Opus (main session) + owner | High | Unchanged |

## Pipeline steps

```
trial graded (fail)
  -> audit_prep            (exists)  evidence folder
  -> audit_facts   NEW     script    FACTS.json: infra, contamination hits, failing tests, deciding tests
  -> audit1        NEW     DeepSeek  DOSSIER.json + DOSSIER.md, provisional verdict
  -> quote_check   NEW     script    every quote in the dossier must exist verbatim at its file:line;
                                     a dossier that fails is re-run once, then goes to Opus as "unverified"
  -> route         NEW     queue     see routing table
  -> audit2        NEW     Opus      per TASK at the breaker gate; writes verdict.json (today's schema)
  -> audit_record          (exists)  records verdict.json as today
```

Routing after audit 1 (deterministic, in the queue):

| Audit 1 says | Queue does | Opus? |
|---|---|---|
| Infra or provider stop (from FACTS) | Rerun under today's rules | No |
| Fair model fail | Record as provisional fail; trials continue (MiMo starts after DeepSeek 3/3 as today) | Not yet |
| Possibly unfair, did not decide the run | Note for the fairness review | Not yet |
| Possibly unfair, decided the run | Hold the run; Opus confirms that one item; confirmed -> repair (today's path); rejected -> provisional fail | Yes, one item |
| Contamination hit judged real | Hold the run | Yes |
| Quote check failed twice | Mark unverified | At the gate |

At the gate (both models 0/3 on provisional verdicts), the queue writes `audit2_ready.txt` with one line
per TASK. The main session launches one Opus 5.5-high agent per task. It reads the instruction and tests
once, then each run's dossier, and checks the cited slices itself instead of the whole transcript. It writes
the final `verdict.json` for every failing run of that task. Only those verdicts count toward a breaker.
Solves stay unaudited.

## Expected saving

- About half of today's Opus audits disappear: the runs of tasks a model later solves.
- Audit 2 reads dossiers and slices instead of full evidence: an estimated 10-15k tokens per run
  instead of 30-40k, and the instruction and tests are read once per task instead of once per run.
- Rough total: 70-80% fewer Opus tokens on audits. The measured figure comes from calibration.

## Risks and controls

- **DeepSeek misses an unfair test that decided a run.** The task reaches the gate with a wrong
  provisional fail, and Opus catches it there. Cost: a few wasted MiMo trials and a later repair. No
  wrong breaker reaches the client, because only Opus verdicts count.
- **DeepSeek over-flags unfair tests.** Each flag costs one small Opus check, not a repair.
- **DeepSeek invents quotes or line numbers.** Known weakness: it over-claims uncovered routes, and its
  fairness reviews are lenient. The quote check rejects any dossier whose quotes are not found verbatim.
- **Later repairs.** An unfair test found at the gate rather than at run 1 means more regrades. Accepted.

## Calibration before switching (required)

Run audit 1 on about 60 runs that Opus already audited tonight (batches CM-CU), without showing it the Opus
verdicts. Measure:

1. Recall on "unfair test decided the run": at least 9 of the 10 Opus findings tonight. Must be high,
   because a miss delays a repair.
2. Recall on infra and contamination: 100% on the cases in the sample.
3. Quote check pass rate: at least 90% of dossiers on the first try.
4. Agreement on "fair model fail": reported, not gated (Opus decides at the gate anyway).

Switch only if 1-3 pass. If 1 fails, keep Opus on every run DeepSeek labels fair with medium or low
confidence, and re-measure.

## Not changed

- Opus decides every verdict that counts toward a breaker.
- Owner rules: keeps-working conflicts are unfair; thin breakers are parked; the 3 h timeout is a fail;
  provider content-filter stops are not fails.
- Builds, fairness and repairs stay on DeepSeek.

## Also: the night check itself

Each night check runs in the main Opus session. Its health, resource, event and audit-list steps are
mechanical. A `nightcheck.py` that prints a 15-line summary, with exceptions only, would let the main
session act on exceptions instead of collecting numbers.

## Built (branch audit-two-stage, 2026-10-30): audit 1

All in `common/audit/audit1/`; nothing is wired into the queue.

| File | What it does |
|---|---|
| `facts.py <postmortem>` | No LLM. Writes `FACTS.json` + `facts-input/` (verifier JUnit XML and logs, trial.log error lines) into the folder. Failing tests with category, crash/assertion/setup-error, message, test source file:line, frames mapped to `evidence/tests` (helper frames flagged); reward arithmetic (functional zeroing, sole failure); infra signals (timeout, provider stop / content filter, 429 retries, API cut, missing result event, tool calls inside the grading window, artifact-transfer errors, verifier setup flags, one identical crash everywhere); evidence gaps (empty / missing / truncated patch); contamination candidates (hidden-test paths, WebFetch/WebSearch, code-host fetches, other external URLs, mtime and history probes, netguard lines), each with file:line. Reuses `review_flags.py` and `internet_use.py`. |
| `AUDIT1-PROMPT.md`, `run_audit1.sh` | The DeepSeek dossier agent, launched like the fairness review: `common/launch/drive.sh deepseek bash .../run_audit1.sh` with the run folder as working directory; tools Read, Grep, Glob, Write; `--restricted` keeps it inside the folder, so it cannot open `verdict.json`, `POSTMORTEM.*`, other runs or reviews. The prompt goes in on stdin, so no task name is on any command line. Writes `DOSSIER.json`, `DOSSIER.md`, `AUDIT1.json` (status, attempts, tokens, quote check). |
| `quote_check.py` | No LLM. Every `{file, line, quote}` in the dossier must occur verbatim (whitespace-normalised) in the cited file, starting within 3 lines of the cited line. Choices: quotes may span lines; diff markers may be left out in a patch; the digest's ` \| ` newline stand-in matches either way; no ellipses, no case folding. A failing dossier gets one retry that sees only the failure list and its first dossier. |
| `route.py` | No LLM. The routing table below, from FACTS + DOSSIER + quote check. `decided_by_unfair` is recomputed from the labels (every failing test possibly-unfair or infra), never taken from the agent. |
| `calibrate.py`, `calibration/` | Calibration: build the set (copies evidence only), run the agents (6 at a time, 30 s apart, progress file), compare with the Opus verdicts. |

## Calibration results (2026-10-30, klavis-vm)

Set: 67 runs = 57 with an Opus verdict written after 2026-10-29T21:50Z + 10 older (8 harness-or-infra, 2
instruction-ambiguity; for one of them, stk-bifrost-19592__DheeLZt, the newest Opus verdict is model-failed, so the
sample holds 6 infra runs). No Opus verdict in the whole archive (1,490) is "contaminated", so contamination recall
cannot be measured; 0/67 false contamination holds. Opus classes: 11 unfair-decided (test-fault), 2 ambiguity, 6
infra, 48 model-failed. Only evidence/ was copied; audit 1 never saw a verdict (`--restricted` kept it in its folder;
the smoke run's log shows only Read/Grep/Glob/Write offered and its Bash/Edit attempts refused).

| Gate | Round 1 as run | Round 1 + facts fixes (no re-run) | Round 2 (36 re-run) | Final: round-2 prompt, no demotion (67) |
|---|---|---|---|---|
| 1 unfair test decided the run (>= 90%) | 11/11 PASS | 11/11 PASS | 4/5 with demotion; 5/5 without | **11/11 PASS** |
| 1b ambiguity held (report) | 2/2 | 2/2 | - | 2/2 |
| 2 infra (100%) | 2/6 FAIL | 6/6 PASS | 1/1 | **6/6 PASS** |
| 2 contamination (100%) | 0/0 | 0/0 | 0/0 | 0/0 (not measurable) |
| 3 quote check, first try (>= 90%) | 55/67 = 82% (5 were raw tabs in JSON); 60/67 = 89.6% JSON-lenient | same | 30/36 = 83% | **60/67 = 89.6%: just FAILS**; 100% verified after the one retry |
| 4 fair model fail agreement (report) | 28/48 | 28/48 | 16/30 | 34/48 |
| 5 false "unfair, deciding" holds (count) | 19/48 | 19/48 | 14/30 (11 with demotion) | 14/48 |

- Round-1 infra misses were all FACTS gaps, fixed deterministically: `repetition_truncation` stop (git-js-s3, an owner
  rule), permission-denied tool results (logging-operator-s2: the repository's own .claude deny rule), and the same
  environment-type crash in every failing test (generator-jhipster-ds `document is not defined`, summarize-ds
  `Cannot find package`). These rules were found on this sample, so they were checked on 1,102 held-out audited runs
  (facts + route only, no LLM): facts flag 35/39 of Opus's harness-or-infra runs and 8/1,063 others (each costs a
  rerun, not a wrong breaker). The 4 held-out misses (deeptutor-ds, flowise-ds, librenms-ds WqDe2yZ, stk-october)
  have no hard signal and depend on the DeepSeek labels.
- The one prompt iteration (round 2) added the "complete fix" rule, a `fair_version_passes` field, and stricter
  quoting instructions. The complete-fix rule cut false holds 19 -> 14 with no recall loss. Using
  `fair_version_passes=false` to demote an item (route `demote`) cut them to 11 but lost zeppelin Xqzp3m7 (a
  keeps-working conflict the agent relabelled one-implementation with fair_version_passes=false). Recommended: keep
  the field for audit 2 to read, but do not demote on it (`route(..., demote=False)`).
- Quote check: 13 of 2,421 first-try quotes failed in round 1, 6 of them text not in the file. In round 2 the 7
  dossiers picked for quote failures failed again 4 times (one task, mobile-security-framework, cites near-identical
  sentences in a long transcript three times); the other 29 passed 27. The retry fixed every one (final 67/67).
- Remaining false holds come mostly from three tasks (mail x4, coraza x2, capsule) where the agent names a design the
  instruction arguably allows; each costs one small Opus check.

**Tokens and cost.** DeepSeek per run: mean 1.5M tokens, almost all cache reads (uncached input ~65k, output ~42k),
4-5 minutes wall time, $1.39-1.43 per run as Claude Code reports it (its own price table, not DeepSeek's invoice).
Opus audit 2, estimated from the dossiers (dossier + +-8 lines around each cited place + 6k fixed + 2.5k output):
mean 15k tokens per run (max 25k), against 25-40k for today's full audit. With holds (27/67 runs, each a smaller check,
bounded here by 14.5k) and audit 2 only for tasks that reach the gate: if every task reached the gate, ~1.4M Opus
tokens for these 67 runs instead of ~2.2M today (-36%); with the measured share of audits whose task is later
solved (52%), ~0.9M (-60%). The 40% hold rate of this sample (tonight's batch had many unfair tests) is the main
cost driver; holds on fair runs would fall with a lower unfair share in live traffic.

**Recommendation: switch with conditions.** (1) Turn on in shadow mode first (`enabled = true, shadow = true`):
DeepSeek cost only, Opus unchanged, live agreement measured with calibrate.py. (2) Go to `shadow = false` when the
live set confirms gate 1 (>= 90%) and gate 3 (>= 90% first try; it is at 89.6% here, and the retry already makes
every dossier verified). (3) Route without the fair_version_passes demotion. (4) Keep the design's fallback: if
gate 1 slips, Opus also audits every run audit 1 calls fair with medium or low confidence.

## Queue integration plan (not built; build after the owner has seen the calibration)

**Config** (`common/queue/queue.toml`, new table, default off):

```toml
[audit1]
enabled = false        # audit_facts + audit1 jobs for every prepared folder
shadow = true          # true: audit_ready.txt still lists every folder (Opus audits as today); audit 1 only records
                       #       ROUTE.json, so live agreement can be measured. false: the routing table below applies.
timeout_sec = 2700     # per agent attempt (run_audit1.sh AUDIT1_TIMEOUT)
```
plus `limits.max_running.audit_facts = 4`, `limits.max_running.audit1 = 6` (shared DeepSeek key with trials),
`priority.audit_facts = 56`, `priority.audit1 = 54` (between audit_prep 55 and fairness), `max_attempts.audit1 = 2`.

**Job kinds** (`common/queue/kinds/audit_facts.py`, `kinds/audit1.py`, commands in `phase4.command`):

| Kind | Command | Check (done when) | Light |
|---|---|---|---|
| `audit_facts` | `python3 -I common/audit/audit1/facts.py <pm>` | `<pm>/FACTS.json` exists, newer than PREPARED.json | yes |
| `audit1` | `bash -c 'cd "$1" && common/launch/drive.sh deepseek bash "$2"' _ <pm> <ROOT>/common/audit/audit1/run_audit1.sh` | `<pm>/AUDIT1.json` with status `ok` or `unverified` | no |

Both run in queue workers (CWEQ_JOB set), so their command lines may name the folder.

**Hook** (`phase4.audit_plan`, after A1 audit_prep): for each folder in state `ready` (prepared for the grading now
in use, no verdict.json): no FACTS.json -> queue `audit_facts`; FACTS.json but no AUDIT1.json -> queue `audit1`;
AUDIT1.json present -> run `route.route(pm)` and write `<pm>/ROUTE.json` (route, why, verified, the test ids). Same
skips as audit_prep (held for a repair, busy, a model that already solved, solves). With `shadow = true` nothing
else changes. With `shadow = false`:

Routing uses `route.route(pm, demote=False)` (see the calibration).

| ROUTE.json route | Queue does | Opus |
|---|---|---|
| `infra-rerun` | `postmortem.py record-provisional <pm>` (attribution harness-or-infra, trustworthy false): the run is untrusted, so the existing untrusted/rerun path re-runs it | no |
| `provisional-fail`, `note-unfair` | `record-provisional` (attribution model-failed, `provisional: true`); trials continue (MiMo after DeepSeek 3/3 as today); note-unfair items listed for the fairness review | at the gate |
| `hold-unfair-deciding`, `hold-contamination` | folder listed in `audit2_confirm.txt`; the run counts for nothing until Opus answers; confirmed -> Opus writes verdict.json (test-fault) and today's repair path runs; rejected -> Opus writes verdict.json (model-failed) | yes, one item |
| `unverified` | `record-provisional` with `unverified: true`; audit 2 reads the full evidence for it | at the gate |

**`audit2_confirm.txt`** (`pipelines/router/out/queue/`, rewritten each pass): one line per held folder,
`<postmortem folder>\t<hold-unfair-deciding|hold-contamination>\t<test ids or hit ids, comma-separated>`.
The main session launches one small Opus check per line (dossier item + that test + the quoted sentences only).

**`audit2_ready.txt`** (same folder, rewritten each pass): one line per TASK whose both models are 0/3 on
provisional verdicts and whose failing runs lack an Opus verdict.json:
`<slug>\t<model>:<fails>/<runs>[,<model>:<fails>/<runs>]\t<pm folder>[,<pm folder>...]\t<flags>` with flags such as
`unverified=1,note-unfair=2,thin=1` (`-` if none). The main session launches one Opus 5.5-high agent per line; it
writes verdict.json (today's schema) into every listed folder; `audit_record` records them as today.

**`postmortem.py` changes:**
- new `record-provisional <pm>`: writes POSTMORTEM.json from DOSSIER.json + ROUTE.json with `"provisional": true`,
  `"auditor": "audit1: facts.py + DeepSeek V4.1 Flash"`, `"brief_version": "audit1-v1"`, the mapped attribution and
  items (labels -> unfair_kind), and `unverified` when the quote check failed;
- `record` (Opus verdict.json): when POSTMORTEM.json is provisional, keep it as POSTMORTEM.provisional.json and
  write the Opus one; `record-ready` records a folder whose POSTMORTEM.json is provisional and that now has a
  verdict.json;
- `current_postmortem` / `phase4.postmortem_state`: a provisional POSTMORTEM.json without verdict.json is state
  `provisional` (not prepared again, not listed in audit_ready.txt when shadow is off).
- `audit_results.py`: a provisional model-failed counts as a graded fail for scheduling (launch counts, MiMo after
  DeepSeek), but a task whose fails are not all Opus-recorded is "awaiting audit 2", never BREAKER candidate.

**Roll-out:** (1) `enabled = true, shadow = true` for a few days: every failing run still gets today's Opus audit,
and ROUTE.json is compared with it (calibrate.py works on live folders); (2) `shadow = false` once the live
agreement matches the calibration; Opus audits then happen only for `audit2_confirm.txt` and `audit2_ready.txt`.
