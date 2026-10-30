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
