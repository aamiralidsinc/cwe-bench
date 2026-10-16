# Trial operating procedure (to stop the None-guessing loop)

## The one rule
NEVER `docker stop` / `pkill` / restart the fleet while trials are running.
Orchestration changes happen ONLY when nothing is live. Killing a live run
records it as reward=None — which is what caused every past "mysterious" None.

## When a run is None, DO NOT GUESS — read `cause` (now recorded per run)
`build/<task>/trial_detail_<model>.json` runs[].cause is one of:
- `exception:<type> (graded)`                -> e.g. AgentTimeoutError graded at timeout: a REAL
                                                result; the reward counts.
- `exception:<type> (not graded)`            -> harness error; retry once.
- `result-event-but-no-result.json`          -> verifier/grader didn't run; task/gate bug.
- `session-ended-early-no-result at <t>s`    -> run was CUT mid-work (external kill,
                                                dropped stream, or agent gave up). If WE
                                                killed nothing, re-run undisturbed once.
- `hit-agent-timeout (~1800s)`               -> genuine timeout; the model truly didn't finish.

A None is a *non-result*, never counted as a model "fail". Only a completed run
scoring <1.0 is a real fail. BREAKER = both models have REAL failing runs.

## Baseline anchor
cloudreve completed clean (341 turns, result event, DeepSeek solved). The harness
WORKS. Measure every None against that, not as a new universal mystery.

## Evidence and review (2026-10-15)
- Every run keeps its container (`--ek keep_containers=true` in run_trial.sh). After the
  run, trial.py saves the agent's final code to `<trial>/final-code/` (diff of /app vs
  the task image, plus the grader's /tmp logs when available). It then deletes the
  container of a clean solve and keeps every other one, listed in
  `build/audit/kept_containers.tsv`.
- A non-solve whose grading setup broke (build/server/DB step failed, tests did not
  report, every functional test failed: see build/review_flags.py) is **needs review**,
  not a model failure. Decide from the saved code and logs, then record `model` or
  `harness` in `build/audit/reviews.tsv`. `harness` = our fault: fix the grader and
  re-grade in the kept container, or give the pair a replacement run.
- When a kept container is no longer needed: `python3 build/release_container.py
  <trial_dir> "<why>"` (code is saved first; `... list` shows what is kept).
- Test runs must write jobs under /Users/dev (Colima shares only that), never /tmp.

## Memory budget for parallel runs (2026-10-15)
Concurrency is limited by MEMORY, not by slot count. The Colima VM has 12 GB. Keep the
sum of the running tasks' `[environment] memory_mb` at or below ~11 GB (trigger-dev 6 GB,
jackson 4 GB, stigmem 4 GB...). On 2026-10-15, 6 parallel runs (2× trigger-dev + 3×
jackson + stigmem) exhausted the VM: the kernel killed an agent's process mid-run, and that
run had to be excluded. Check `colima ssh -- sudo dmesg -T | grep -i oom` after any
unexplained failure.

## Trial setting: offline, like CWE-bench (2026-10-16)

**Network:** CWE-bench runs agents with only the model provider's API reachable (arXiv 2610.17020).
- Every task's `task.toml` sets `[agent] network_mode = "allowlist"` with only `api.deepseek.com`
  and `api.xiaomimimo.com`. Harbor's egress sidecar enforces it.
- Proof: `harness/offline-check`. Model APIs answer; GitHub, PyPI, plain sites, `git`, SSH and
  SMTP are blocked.
- Tasks without that setting must not be trialled. `build/audit/offline_since.tsv` records when
  each task switched.
- `harness/netguard` (block only the task's own repo) is kept but superseded.
- **No web tools either.** Claude Code's WebSearch runs on the model provider's side, inside the
  allowed API call, so the allowlist cannot stop it. It returned live results in the "offline"
  filament r11 run (2026-10-16).
  - `run_trial.sh` passes `--ak disallowed_tools=WebSearch,WebFetch`.
  - Proof: the agent's tool list in the transcript's init event has neither tool.
  - Ledger: solves between the offline switch and that change count only without a WebSearch call
    (`WEB_TOOLS_OFF_UTC` in `audit_results.py`).
- **Docker networks:** kept trials leave their networks behind, and Docker's ~31 address pools
  ran out. The queue runs `docker network prune -f` before each launch.

**Earlier runs:**
- A solve counts only without internet lookup (`build/internet_use.py`); a failure still counts.

**Timeouts:**
- A non-solve that hits a limit under 3 h is not a failure. It is re-run with
  `CWE_AGENT_TIMEOUT_MULT=1.5` (Harbor `--agent-timeout-multiplier`, i.e. 3 h); only a 3 h timeout
  counts. `build/audit/timeout_reruns.tsv` lists the owed re-runs.

**Queue:** `build/queue_offline.py` runs open pairs from r11 up.
- Limits: 4 slots, real memory under 7.5 GB.
- Stops a pair at 1 solve or 3 counted failures.
- `--status` shows progress.

**Task defects:** `build/audit/task_defects.tsv` lists tasks whose build leaked the answer.
- Their runs before the fix time do not count.
- Example: webob's vulnerable commit was upstream's own "Add regression tests" commit.

## Post-run audit before any result is final (2026-10-16)
Two of three reported per-model failures turned out to be faults in our own tests
(research/own-runs/FINDINGS.md). From now on **no graded run counts toward a verdict until an
independent auditor has judged it trustworthy**:
1. `trial.py` prepares the evidence automatically after each graded run
   (`python3 build/postmortem.py prepare <trial>` by hand for older runs or regrades). This
   writes `<trial>/postmortem-<UTC>/` with the evidence, `AUDITOR_BRIEF.md` and
   `verdict.schema.json`.
2. When a run finishes, the main session starts a sub-agent: general-purpose, model opus
   (Claude Opus 5.5), effort high, one per run. Its brief: read AUDITOR_BRIEF.md in that folder,
   judge from the evidence only, and write verdict.json. The main session may also audit a run
   itself. No CLI calls.
3. `python3 build/postmortem.py record <postmortem dir>` validates verdict.json and writes
   POSTMORTEM.json and POSTMORTEM.md.
4. `python3 build/audit_results.py` counts the run only if its newest postmortem audited the
   grading now in use and says `trustworthy: true`.
   - Otherwise the run shows as "awaiting audit" or "audit: untrusted".
   - A regrade makes the old audit stale, so audit after the regrade.
   - `build/audit/awaiting_audit.tsv` (and `postmortem.py pending`) lists the runs that still
     need an audit.
5. **Record every verdict straight away** (user, 2026-10-16):
   `python3 build/postmortem.py record-ready && python3 build/audit_results.py && python3 build/update_results.py`.
   - This refreshes RESULTS.md's task table and prints which verdict cells changed.
   - When a pair's verdict changes, also edit RESULTS.md's executive summary, open pairs and
     corrections by hand.
Report numbers only from the audited ledger.

## After every trial batch (2026-10-15)
1. `python3 build/audit_results.py` to rebuild the results table.
2. `~/.local/share/uv/tools/harbor/bin/python build/archive_runs.py` to lock the finished runs
   into `~/.tb-graders/cwe/archive/` (write-once, read-only, UTC-named; live runs skipped).
3. Delete images only after step 2 has archived every run of that task.

## Reading order (replaces the old rule, 2026-10-15)
1. Run `python3 build/audit_results.py`, then read `build/audit/ledger.md`. It reads every
   raw trial folder and is the ONLY source for verdicts.
2. To look at a single run, open its raw `result.json` + `verifier/results.json`.
3. Do NOT judge from trial-matrix.md, trial_detail_*.json, runs_*.log or queue.json
   result text. A reader bug wrote them, and they are wrong for many runs.

## #1 CAUSE of past confusion: a reader bug, not stale runs
The old explanation ("reading stale runs from older eras") was wrong: every job dir is
valid evidence. The real cause was `trial.py` itself: `glob("*/")` returns files on
Python 3.9, so `config.json` was read as the trial, and graded timeouts were discarded.
Both are fixed. Full write-up: `build/RESULTS-AUDIT.md`.
Timestamped job names (`<task>-<model>-r<run>-YYYYMMDD-HHMMSS-nNNN`) are still useful for
ordering runs.
