# Test-repair brief (2026-10-16)

You repair the hidden tests of ONE task (`SLUG`, given with this brief) in
`/Users/dev/terminal-bench/cwe-bench`. Post-run audits (Opus 5.5 high) flagged tests that are too
lenient (a wrong fix could pass) or too strict / unfair (a correct fix could fail). Your job: close
each flagged gap that is fair to close, prove the tests still accept correct fixes, then re-grade
the saved final code of earlier runs with the repaired tests.

## Inputs
- Flagged items: `build/audit/lenient_items_2026-10-16.txt` (sections `== SLUG | ...` and
  `-- REC SLUG | ...`) and the `## SLUG` section of `research/own-runs/TEST-REPAIRS.md`. Each item
  names the audit's verdict.json for the full reasoning.
- The task: `tasks/SLUG/` (instruction.md, tests/, solution/), `build/SLUG/` (manifest.json,
  checks/*.patch, notes.md).
- Rules for tests: `builder/BUILDER.md` §3c, §3f and especially §3g (lessons from our own runs).

## Steps
1. **Triage every flagged item.** Several were already fixed earlier today. For each: check the
   current tests; mark it `already fixed`, `fix`, or `skip` (with the reason).
2. **Fairness rule (decides fix vs skip).** A new or tightened assertion is allowed only when the
   property follows from `instruction.md` (what it states, or what a competent security engineer
   would infer from it) — never from the upstream fix's particular design. If a test needs an
   interface contract the instruction does not state, either add ONE plain sentence to the
   instruction (no fix, file, function names or leak terms; the gate checks) or skip the item.
   Follow §3g: any 4xx plus no side effect, never one exact status; no product helpers in tests;
   no constants the instruction does not state; per-resource/per-verb stubs; set every candidate
   knob; drive the entry point the instruction names.
   - **A "too lenient" fix** adds the missing case: e.g. a security case another reasonable wrong
     fix would miss, or a functional case that a refuse-all / delete-the-feature fix would break.
   - **A "too strict" fix** relaxes the assertion to what the instruction promises.
3. **Edit only `tasks/SLUG/tests/`** (and, if unavoidable, one sentence of `instruction.md`). Never
   put test code under `environment/`. Do not change `solution/`.
4. **Prove each new case bites.** For each closed leniency, add a patch to `build/SLUG/checks/`
   that exploits the old gap (e.g. login-only check, refuse-all route, reads-only verification) and
   list it in `manifest.json` `patch_checks` with `security_fail` or `functional_fail`. Keep all
   existing patch checks. The reference fix and every `pass` patch (incl. `hardening` and `blind`
   kinds, where present) must still score 1.0. If a `pass` patch or a blind fix now fails your new
   test, your test is probably unfair: rethink it before anything else.
5. **Run the gate through the shared Docker slots** (the VM is shared with other repairs):
   `cd /Users/dev/terminal-bench/cwe-bench && python3 build/slot.py 3 -- python3 -I builder/gate.py SLUG`
   (use `--only static` first while iterating). The task is repaired only when it prints PASSED.
6. **Regrade saved runs.** Find every trial folder of this task under
   `~/.tb-graders/cwe/jobs/SLUG-*/*/` that has `final-code/changes.patch` and a `result.json`.
   Regrade each run whose current reward (the newest `regrade-*/REGRADE.json`, else the verifier
   reward) is 1.0. If you RELAXED any test, also regrade the runs below 1.0. Use:
   `python3 build/slot.py 3 -- python3 build/regrade_from_code.py <trial_dir> "test repair 2026-10-16: <one line>"`
   For every run whose reward DROPS from 1.0, name the failing test and explain, from the saved
   `final-code/changes.patch`, whether the fix really has that defect.
7. **Write it down.** Append a `## 2026-10-16 test repair` section to `build/SLUG/notes.md`: each
   item and its decision, the new patch checks, the gate result, the regrade table.

## Do not
- Touch other tasks, `RESULTS.md`, the ledger, `build/queue_offline.py`, `build/audit/*.tsv` or
  `repair_hold.txt`, or anything outside `tasks/SLUG/`, `build/SLUG/`, and the trial folders'
  new `regrade-*` dirs.
- Start agent trials, or stop/remove containers you did not start. Delete no images.
- Use web lookups of this project's upstream fix or tests.

## Report back (concise)
PASSED or not; per item: already fixed / fixed (how) / skipped (why); new patch checks; any
instruction change (quote it); regrade table `trial | old | new | failing tests`; for each drop,
whether the fix really has the defect.
