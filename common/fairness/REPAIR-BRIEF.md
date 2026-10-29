# Test-repair brief (the queue's `repair` job, owner 2026-10-28)

The audit-driven brief of the repair step: the fairfix step restored as a work-queue job
(`common/queue/kinds/repair.py`, `common/queue/repairjob.py`; history in `docs/WORK-QUEUE.md`).

- **Used by:** both fairfix scripts in repair mode (`REPAIR_INPUTS` set):
  `pipelines/sibling/10-fairfix/run_fairfix.sh` and `pipelines/stacking/8-fairfix/run_fairfix_stack.sh`.
  They append `common/fairness/OTHER-READING-CHECK.md` (when present) and, for a stacked task, the
  stacking addendum.
- **What is sent:** only the text below the marker, with `{{SLUG}}`, `{{ROOT}}`, `{{INPUTS}}`, `{{DATE}}`,
  `{{SCRATCH}}` filled in.
- **Who holds the task:** the job, never the agent. It sets `.hold-repair` before the agent starts, checks the
  result in code, restores the originals when a check fails, queues the re-gate, and the queue lifts the hold
  after the regrades (reconcile R6).

---8<---

You repair the hidden tests of ONE security-fix benchmark task after its model runs. Project root:
{{ROOT}}. Task slug: {{SLUG}}. Today: {{DATE}}.

Post-run audits, a fairness review or the owner flagged tests that a correct fix can fail. Your job:
make every flagged test fair, prove the task still works, and leave a record. The queue has already
put the task on hold. It re-gates and regrades every run after you, and it lifts the hold itself.

## Read first, in this order

1. {{INPUTS}}/FINDING.md: what was flagged. Each audit item names the exact test, its verdict,
   `unfair_kind`, the instruction sentences it conflicts with, and what the model did. FINDING.json
   holds the same data.
2. {{INPUTS}}/INPUTS.md: the index of everything else.
3. {{INPUTS}}/runs/<run>/ for EVERY graded run, audited or not. Each run folder has:
   - RUN.md: reward, grading, audit;
   - failures.md: every failing test with the verifier output that names it;
   - results.json;
   - changes.patch: the run's final diff. When it is cut or truncated, RUN.md names the run's
     workspace; read the code there;
   - transcript-excerpts.md: the agent's steps around the failing area.
   Find out exactly why each flagged test failed for each run's code.
4. build/{{SLUG}}/trial_summary.md, tasks/{{SLUG}}/instruction.md, tasks/{{SLUG}}/tests/ (all files),
   tasks/{{SLUG}}/solution/fix.patch, build/{{SLUG}}/manifest.json, build/{{SLUG}}/checks/*.patch and
   build/{{SLUG}}/gate_report.json.
5. The FULL build/{{SLUG}}/notes.md, build/{{SLUG}}/history/, earlier repaired-tests-*/README.md,
   FAIRNESS.md and its .prev-* versions, and HUMAN-DECISION.md. You need the history.
6. A prior repair analysis or proposal in history/ (`*-repair-analysis.md`, `*-repair-proposal/`) is a
   starting point to VERIFY, never to apply blindly. Check each claim against the tests, the code and the
   runs. Validate everything again yourself.

## The rules

- **Test-only.** Never edit instruction.md, task.toml or environment/: the job checks this and reverts the
  whole repair. You may change tests/, the reference (solution/fix.patch, solution/solve.sh), checks/*.patch
  and manifest.json (patch_checks, traps, test lists).
- **Owner rule: if a test and the instruction disagree, the failure is unfair.** Fix the test.
- **Pick the harder resolution.** When the instruction and a test conflict, keep the instruction. Change
  the tests, and the reference and check patches where needed, so they follow it. Never resolve a
  conflict by weakening what the instruction asks for.
- **What a fair test does.**
  - It drives the real entry point.
  - It asserts the protected outcome: no write, no leak, no access.
  - It accepts every outcome the instruction allows: any refusal form or 4xx it allows, a refusal at store
    time or at use time, and any valid layer.
  - It computes expected values in the test. It needs no network.
- **Keep the bite.**
  - Keep every assertion that is fair.
  - Drop a case only when it cannot be made fair; a removal goes to `removed-tests-{{DATE}}/`.
  - Never remove or weaken the test of a real unfixed upstream route, or of a route where the protection
    never existed, just because it is hard. Such a route is fair when the instruction's general property
    covers it.
  - Never add a sentence anywhere that points at a route.
- **The audit may be wrong.** If a flagged test is in fact fair, show why with code evidence from the
  runs and the instruction, and leave it as it is.
- **Do not decide verdicts.** Never touch `.hold-repair` or `.sound`, never start trials, re-gates or
  regrades of real run folders, and never edit `build/audit/`, the ledger or another task.

## Validate on a scratch copy before you change the live task

1. Copy the task into a scratch data root:
   `mkdir -p {{SCRATCH}}/data/tasks {{SCRATCH}}/data/build`
   `cp -a tasks/{{SLUG}} {{SCRATCH}}/data/tasks/`
   `cp -a build/{{SLUG}} {{SCRATCH}}/data/build/` (the manifest, checks/ and notes are enough if it is large)
2. Edit the copy.
3. Run the real gate on the copy, one stage at a time; gate.py honours CWE_DATA_ROOT:
   `CWE_DATA_ROOT={{SCRATCH}}/data python3 -I common/gate/gate.py {{SLUG}} --only static`, then
   `--only nop`, `--only oracle`, `--only patches`. The report lands in the scratch copy's build folder.
   If a release does not honour CWE_DATA_ROOT yet, run the verifier image by hand on the copy instead.
4. Check the results:
   - nop must still FAIL every security test it failed before and PASS every functional test;
   - the oracle passes every test;
   - every check patch keeps its declared `expect`. A check patch that now passes a repaired test is
     re-declared `pass` only if it is now a correct fix by the instruction; otherwise your test lost its
     bite, so rethink it.
5. Grade each flagged run's saved code against the new tests on a COPY of its run folder (never the real
   one):
   - copy result.json, config.json, verifier/, final-code/ and artifacts/ into {{SCRATCH}}/runs/<trial>/;
   - run `CWE_DATA_ROOT={{SCRATCH}}/data python3 -I common/audit/regrade_from_code.py {{SCRATCH}}/runs/<trial> "repair validation"`.
   Each run's new result must follow from the finding: a run that failed only on unfair tests should now
   pass them. A run that still fails must fail a fair test, and you must name it.

## Swap, and record

1. Keep everything in build/{{SLUG}}/repaired-tests-{{DATE}}-repair/:
   - original/: the files before the repair;
   - new/: the repaired files;
   - tests.diff;
   - validation-results.txt;
   - README.md. Per finding item: the test, what was unfair, what you changed and why. Then the validation
     table: nop, oracle, every check patch, every run's old and new result.
   Use removed-tests-{{DATE}}-repair/ with the same README for whole files you remove.
2. Swap atomically, each file at once: stage the new file next to its target in the same folder, then
   `mv -f` it over the target. Touch every changed test file afterwards.
3. Write build/{{SLUG}}/history/{{DATE}}-repair.md: the finding, the decision per item, the changes and the
   validation. Do not edit notes.md: it holds build facts only, and the job reverts any edit to it.
4. Write {{INPUTS}}/OUTCOME.json:
   `{"outcome": "repaired" | "no_repair_needed" | "could_not_repair", "reason": "...", "folder": "repaired-tests-...",
   "items": [{"test": "...", "action": "repaired | removed | kept-fair | not-repaired", "why": "..."}],
   "validation": {"nop": "...", "oracle": "...", "patches": "...", "runs": {"<trial>": [old, new]}}}`.
   For no_repair_needed or could_not_repair, change no task file.

## Pitfalls from the hand repairs

- **Waiting.** A waiting loop's command line must not contain the slug or the words regate, regrade,
  repair, fairfix, upgrade or fairness: the queue reads command lines and would treat the task as busy.
  A waiter must never `pgrep` a pattern that is in its own command line (it finds itself and waits
  forever). Wait on a pid you started (`wait <pid>`, or poll `kill -0 <pid>`).
- **Processes.** Never send SIGSTOP. Kill only pids you started yourself: other jobs share the machine.
- **Root-owned scratch.** Files that containers wrote into scratch can be root-owned. Remove them through a
  container: `docker run --rm -v <dir>:/x alpine:3 rm -rf /x/<name>`. Never use sudo.
- **Images.** Remove only images you built under a temporary tag. Never prune images or the build cache.
- **No upstream lookups.** Never look up the upstream fix or its tests.

## Report (under 300 words)

- Each finding item and what you did with it.
- The scratch gate result per stage and the regrade table of the runs.
- The repair folder.
- Anything you could not make fair, and why.
