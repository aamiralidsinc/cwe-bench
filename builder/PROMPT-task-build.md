# Task-build prompt template (one task per sub-agent)

> **FORMAT (2026-10-21): Frontier-SWE delivery format.** Fill the skeletons in `builder/templates/` and follow `builder/FRONTIER-CONFORMANCE-SPEC.md`. The gate enforces it via `builder/conformance_check.py`, so a non-conforming task fails. Where any guidance below predates this and says `/app`, "delete `.git`", a model-host **allowlist**, or "do not modify/add tests", it is SUPERSEDED: use `/workspace`; keep the fresh one-commit git baseline (do not delete it); `[agent]` and `[verifier]` are `network_mode = "no-network"` with NO allowlist (the model host is allowed at run time via `--allow-agent-host`); and `instruction.md` must not mention tests or grading.


Use for a host the screener marked `build` (or `maybe`, if the user approves). Fill the `{{...}}`
slots and send everything between the two `---8<---` lines. The rules live in `BUILDER.md` and
`BRIEF-trap-stack.md`. This template only adds the per-task inputs, so keep those files current
rather than copying lessons in here.

| Slot | Fill with |
|---|---|
| `{{SLUG}}` | the task directory name, e.g. `<repo>-<feature>-sib` |
| `{{CANDIDATE_ROW}}` | the candidate's row (index or shortlist), as JSON |
| `{{SCREEN_JSON_PATH}}` | `sourcer/review/hosts-v4/<entry_id>.json` |
| `{{TRAP_PLAN}}` | the lead's chosen base shape and 2–3 traps, taken from the screener's list and edited |
| `{{EXTRA_NOTES}}` | anything host-specific (known build gotchas, a trap to avoid, a credit line); "none" if empty |

After this builder reports, the lead runs the rest of the process in NEXT-STEPS.md:
- blind fix (`BLIND-FIX-BRIEF.md`, a fresh agent);
- fairness review (`FAIRNESS-REVIEW-BRIEF.md`, another fresh agent);
- the full strict gate;
- trials;
- an audit of every graded run.

If a safety check stops a brief, narrow it. Do not route it through another model.

---8<---

You build ONE Harbor-format security-fix benchmark task from a published, already-fixed advisory in
an open-source project. The task gives a solver agent the vulnerable code and a vulnerability
report, and hidden behavioural tests check its fix. Nothing you build leaves this machine.

Project root: `/Users/dev/terminal-bench/cwe-bench`. SLUG: `{{SLUG}}`.

## Read, in full, before starting
1. `builder/BUILDER.md`: the build rules (environment, exploit, tests, oracle, wrong-fix patches,
   §3g test rules, §3h defaults, §3i instruction style, §3j trap stacking, manifest, gate).
2. `builder/BRIEF-trap-stack.md`: the round-2 goal, the hard rules, and the lessons from
   marshmallow, jackson-databind-readonly and better-auth. Follow its rules 1–9 exactly.
3. `{{SCREEN_JSON_PATH}}`: the screener's reading of this host. Treat it as a lead, not a fact.
   Verify every file:line before relying on it.

## Inputs
Candidate:
```json
{{CANDIDATE_ROW}}
```
Trap plan, chosen by the lead:
{{TRAP_PLAN}}

Host notes: {{EXTRA_NOTES}}

## What this task must achieve
DeepSeek V4.1 Flash and MiMo-V2.6-Pro must both fail all 3 finished attempts because of their own
judgement, never because of a task defect. So:
- **Base shape** (beats DeepSeek): a feature-absent route with a *reason to dismiss* and *distance*
  from the report's landing point, or a data producer off the check's path, where the producer is
  infrastructure the attacker never calls and the check does not call it.
- **At least 2 more traps with DIFFERENT dismissal reasons** (beat MiMo, which probes the obvious
  path). Use the B-failure-modes §3a ranks. Never add encoding, verb, protocol or role variants, or
  more routes of one concept.
- **Fair.** Every trap is realistic code, reachable through the real entry point, covered by an
  invariant in `instruction.md` or by standard expert knowledge, and never named or paraphrased.
  Prefer real, unmodified gaps to injected ones. If you must inject, write what a maintainer could
  have written, with no deceptive names or comments.
- **Small enough.** A careful engineer who knows where to look fixes everything in about 45 minutes.

If the plan does not hold up in the code (a trap is not reachable, the producer is called by the
check, a route is next to the landing point, the build needs network at run time), first try to
substitute a trap of another listed shape that the code does support, and record why. If no plan
meets the bar, stop and report `abandoned` with the reason. Do not ship a weaker task.

## Deliverables
- `tasks/{{SLUG}}/`: `instruction.md` (§3i style, no names, no count, no fix), `task.toml`
  (template, offline allowlist), `environment/Dockerfile` (vulnerable commit, `/app/.git` removed,
  no test code, agent layer appended), `solution/solve.sh` and `fix.patch` (closes the base and
  every trap), `tests/test.sh` (template, agent-kill block kept), `tests/score.py` (unchanged), and
  `tests/security/` and `tests/functional/` (one security test per trap form, plus a coupled
  functional test per trap).
- `build/{{SLUG}}/manifest.json` must have:
  - `"strict_gate": true`;
  - `leak_terms`;
  - `traps` (shape, file:line, covering tests, `security_fail` patch, why it is realistic);
  - `wrong_fix_catalogue` (every class in `gate.py: WRONG_FIX_CLASSES`, a patch or `n/a: why`);
  - `patch_checks`.
- `build/{{SLUG}}/checks/`:
  - one `security_fail` patch per trap (the fix that misses only that trap);
  - the catalogue patches;
  - a `functional_fail` patch for over-broad fixes;
  - a `pass` patch of kind `hardening`;
  - an alternative-correct `pass` patch where a second valid fix is plausible.
- `build/{{SLUG}}/notes.md`: start and end UTC, each trap, what you verified, what you could not.

Do NOT write the `blind` patch or `FAIRNESS.md`, and do NOT run any model, `build/trial.py` or
`harness/run_trial.sh`. Run the gate stages yourself, in order, one at a time:
`python3 -I builder/gate.py {{SLUG}} --only static`, then `--only nop`, `--only oracle`,
`--only patches`. In static, only the missing blind patch and FAIRNESS.md may remain as problems.

Machine: one shared 8-CPU / 12 GB Docker VM that is running trials.
- Never prune Docker images or the build cache.
- Never stop containers you did not start.
- Run at most one Docker build or gate stage of your own at a time.
- Scratch work goes in `~/.tb-graders/cwe/work/{{SLUG}}/`. Edit only `tasks/{{SLUG}}/` and
  `build/{{SLUG}}/`. Do not commit.

## Report back (under 400 words)
- Each gate stage's result.
- The base shape and each trap in one line: shape, file:line, real or injected, reason to dismiss.
- The instruction's word count.
- Every guess you could not verify.
- Any fairness concern you see yourself.
- If abandoned, exactly why.

---8<---
