# Pre-trial fairness and leniency review brief (gate requirement, BUILDER.md 3h)

You review ONE task before any model trial. You did not write its tests. Project root:
/Users/dev/terminal-bench/cwe-bench. Read tasks/SLUG/instruction.md, every file in tasks/SLUG/tests/,
tasks/SLUG/solution/fix.patch, build/SLUG/manifest.json (patch_checks, traps, wrong_fix_catalogue),
build/SLUG/notes.md and build/SLUG/checks/*.patch. Do not run Docker, trials or gates. Do not look
up the upstream fix online.

The solver sees ONLY instruction.md and the repository. It never sees tests, notes or task.toml.

Write build/SLUG/FAIRNESS.md:
1. Table, one row per test (file::name): what it asserts | the instruction sentence (or "standard
   expert knowledge: ...") that makes it fair | could a CORRECT fix that a competent engineer would
   write from the instruction fail it? (no / maybe / yes, with the fix) | risk low/medium/high.
   The covering sentence may be the task's one general property: a test is covered when that
   property, read literally, applies to the route it drives. Do not require a sentence that names
   or points at the route. In the "could a correct fix fail" column, also consider a correct guard
   placed at a different valid layer (dispatcher vs handler, before vs after setup) and any refusal
   form the instruction allows.
2. Leniency (QUALITY, non-blocking): for each security property and each trap in manifest.traps, name
   the most plausible WRONG fix and whether some test catches it (cite the test and the checks/ patch,
   if any). List wrong fixes no test catches.
3. Hints (QUALITY, non-blocking): any sentence in instruction.md that names or paraphrases a file,
   function, mechanism, the fix approach, a trap, a variant list or the flaw count. Quote it and
   propose neutral wording.
3a. Surface descriptions (REQUIRED to fix, but NOT a gate-a reason): any sentence that describes
   where a sibling, far site or uncovered route lives, even in product terms (a route, operation,
   command, channel, object kind, stage or format), or that exists only to cover one trap; and any
   general word that is also the name of one stage or entry point. Such a report turns the task
   into a checklist. Quote each one and give the general rewording (the property stated once over
   the protected data or outcome). List them under "Required: generalize". Never recommend ADDING a
   sentence that points at a route to make a test fair: widen the general property instead.
4. Realism (QUALITY, non-blocking): is each trap code a real maintainer could have written, reachable
   via the real entry point? Flag anything that looks planted or contrived. Real, unmodified
   upstream routes that the published fix left open, and routes where the protection never existed,
   are realistic by definition: never flag them as "beyond the advisory", "out of scope" or "not what
   upstream fixed". A solver's reason to skip one ("upstream doesn't support it", "not a security
   boundary") is the solver's judgement, and leaving it open is a model failure.
5. Verdict — TWO SEPARATE GATES; keep them distinct:
   a. UNFAIRNESS gate (the ONLY thing that sets NOT READY): mark NOT READY *only* if a CORRECT fix a
      competent engineer would write from instruction.md would FAIL the grader — i.e. a "yes" (or an
      unresolved "maybe") in the step-1 "could a correct fix fail?" column. Qualifying mechanisms:
      a contradiction between instruction and tests; an assertion not derivable from visible material
      or standard expert knowledge; an unfaithful/synthetic harness a correct fix never satisfies; an
      impossible or ambiguous spec. For an uncovered or never-protected route, gate a fires ONLY
      when (1) the general property, read literally, does not cover the route (for example a word
      that names one stage while the route runs at another), or (2) its test also fails a correct
      fix (a harness that bypasses a valid layer, or a demand for one error class or status). It
      never fires because the route lies outside the published fix. If every correct fix passes, the task is READY — EVEN WHEN wrong
      fixes could also pass. Give the exact instruction/test changes required to remove the unfairness.
      PRIMARY-MECHANISM rule: judge gate a against the correct fix that follows the instruction's
      PRIMARY stated mechanism. If that fix passes every test, the task is READY even when the
      instruction also offers a secondary allowance (e.g. "...or it is left out") that only some
      alternative implementation might fail — that is leniency (gate b), not unfairness. Gate a fires
      only when the natural correct fix following the stated mechanism cannot pass.
   b. QUALITY findings (recorded, NOT a reason for NOT READY): the leniency (2), hint (3) and realism
      (4) items. Fix these proactively to raise delivery quality — tighten/extend tests to catch the
      named wrong fixes, neutralize hint wording, replace contrived traps — but a task is NOT unfair
      merely because a wrong/cheating fix could also pass, a hint is present, or coverage is thin. List
      them under "Quality to tighten" with the specific change.

Do NOT let leniency, hints or realism ALONE drive NOT READY — that over-flags fair tasks. Only a
concrete correct-fix-fails mechanism (gate a) sets NOT READY.

End the file with EXACTLY these two machine-readable lines, in this order, nothing after them:
GATE_A: READY            (or `GATE_A: NOT_READY`) — the fairness verdict from gate a ONLY. Leniency,
                         hints, realism and quality NEVER change this line.
NEEDS_HUMAN_REVIEW: NO   (or `NEEDS_HUMAN_REVIEW: YES`) — set YES when the gate-a call rested on a
                         JUDGMENT (a genuine/defensible ambiguity, a borderline reading, or notable
                         disclaimers a human should confirm), so a person can look. This is SEPARATE
                         and does NOT change GATE_A: a task can be `READY` + `NEEDS_HUMAN_REVIEW: YES`
                         or `NOT_READY` + `NEEDS_HUMAN_REVIEW: YES`. Only set NO when the verdict is
                         clear-cut.

Above those two lines, return: the READY / NOT READY reasoning (with its unfairness reason if NOT
READY), the "Required: generalize" list (step 3a; write "none" if empty), the "Quality to tighten"
list, and — if NEEDS_HUMAN_REVIEW is YES — a one-line "Human review:"
note naming exactly what to confirm. Keep the prose under 300 words.
