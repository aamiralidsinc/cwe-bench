# Pre-trial fairness and leniency review brief (gate requirement, BUILDER.md 3h)

You review ONE task before any model trial. You did not write its tests. Project root:
the repo root (the folder holding .cwe-bench-root). Read tasks/SLUG/instruction.md, every file in tasks/SLUG/tests/,
tasks/SLUG/solution/fix.patch, build/SLUG/manifest.json (patch_checks, traps, wrong_fix_catalogue),
build/SLUG/notes.for-review.md (the build notes without earlier audit, fairness, decision and run
conclusions), build/SLUG/checks/*.patch, build/SLUG/gate_report.json (what each check patch, upstream's
own fix included, failed) and build/SLUG/trial_summary.md (the failing tests of each run; it may be
missing). Judge on your own: never open build/SLUG/notes.md, build/SLUG/history/, FAIRNESS.md.prev-*,
HUMAN-DECISION.md, or any audit or postmortem file. Do not run Docker, trials or gates. Do not look
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
   form the instruction allows. "The reference fix passes" never answers this column: the reference
   is one implementation.
1a. Conflict check (gate a; owner rule 2026-10-28: if a test and the instruction disagree, the
   failure is unfair). For EVERY test, security and functional, add three columns to the step-1 table:
   (i) every instruction sentence the test could conflict with, quoted. Look first at the pairs that
       broke delivered tasks: a "keeps working" / "behaves exactly as today" / "existing deployments"
       sentence against a security rule (a functional test that demands accepting an input a security
       rule, read literally, refuses; or a security test that demands refusing something today's
       behaviour or a keep-working sentence allows), and a stated mechanism against an unstated
       detail. Write "none" only after checking every security rule and every keep-working sentence;
   (ii) would a fix that follows the OTHER sentence, or a different correct implementation the
       instruction allows (another character class, layer, data structure, refusal form, a stricter
       but still correct rule), fail this test? no / yes: name that fix and the assertion it fails;
   (iii) label: `ok`, `conflict` (two sentences, the test sides with one), `one-implementation` (the
       test pins a detail the instruction does not state), or a scope label from step 4a. A "yes" in
       (ii) is never `ok`, whatever the reference does.
   Then a "Conflicts" table with one row per test not labelled `ok`: test | label | the sentences |
   the fix that fails | deciding: yes / no / unknown. A test is deciding when some run in
   trial_summary.md fails it and fails no `ok`-labelled test ("unknown" when trial_summary.md is
   missing). Every row is a gate-a failure: GATE_A is NOT_READY. Give the remedy as a test change
   (keep the instruction, change the test and the reference). For a `conflict` row, name the other
   sentence and the fix that follows it: the repair step turns it into an other_reading check that the
   gate runs (common/fairness/OTHER-READING-CHECK.md).
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
4a. Scope and reachability (gate a). For every trap or variant beyond the advisory's own route
   (manifest.traps whose origin is not the advisory route, and every test not mapped to a trap), give:
   the instruction sentence whose scope covers it, quoted (the scope the instruction DESCRIBES: the
   protected data, outcome or component it names; "outside the advisory" is not a scope question),
   and the entry point that reaches it at the pinned commit (file:function or route, and the product
   code that creates the state the test sets up). The general property counts: a hidden route needs no
   sentence that names, describes or points at it, so quoting the general property that, read
   literally, applies to the route is enough. Label the test `out-of-scope` only when no instruction
   sentence, read literally, covers the change it needs, and `unreachable` when no code at the pinned
   commit creates the state it needs (a dead path) or no real entry point reaches it. Both are unfair:
   list them in the Conflicts table. In gate_report.json, a security test that upstream's own fix
   (checks/upstream_fix.patch) fails is expected only for uncovered or injected traps; for any other
   test, explain it or label it.
5. Verdict — TWO SEPARATE GATES; keep them distinct:
   a. UNFAIRNESS gate (the ONLY thing that sets NOT READY): mark NOT READY *only* if a CORRECT fix a
      competent engineer would write from instruction.md would FAIL the grader — i.e. a "yes" (or an
      unresolved "maybe") in the step-1 "could a correct fix fail?" column. Qualifying mechanisms:
      a contradiction between instruction and tests; an assertion not derivable from visible material
      or standard expert knowledge; an unfaithful/synthetic harness a correct fix never satisfies; an
      impossible or ambiguous spec; any test labelled in step 1a or 4a (conflict, one-implementation,
      out-of-scope, unreachable). For an uncovered or never-protected route, gate a fires ONLY
      when (1) the general property, read literally, does not cover the route (for example a word
      that names one stage while the route runs at another), or (2) its test also fails a correct
      fix (a harness that bypasses a valid layer, or a demand for one error class or status). It
      never fires because the route lies outside the published fix. If every correct fix passes, the task is READY — EVEN WHEN wrong
      fixes could also pass. Give the exact instruction/test changes required to remove the unfairness.
      PRIMARY-MECHANISM rule: judge gate a against the correct fix that follows the instruction's
      PRIMARY stated mechanism. If that fix passes every test, the task is READY even when the
      instruction also offers a secondary allowance (e.g. "...or it is left out") that only some
      alternative implementation might fail — that is leniency (gate b), not unfairness. Gate a fires
      only when the natural correct fix following the stated mechanism cannot pass. This rule covers
      an explicitly optional allowance only. It never excuses a conflict (step 1a): a keep-working
      sentence, a security rule and the stated refusal form are not secondary allowances, and a test
      that only the reference's own detail passes is `one-implementation`, not leniency.
   b. QUALITY findings (recorded, NOT a reason for NOT READY): the leniency (2), hint (3) and realism
      (4) items. Fix these proactively to raise delivery quality — tighten/extend tests to catch the
      named wrong fixes, neutralize hint wording, replace contrived traps — but a task is NOT unfair
      merely because a wrong/cheating fix could also pass, a hint is present, or coverage is thin. List
      them under "Quality to tighten" with the specific change.

Do NOT let leniency, hints or realism ALONE drive NOT READY — that over-flags fair tasks. Only a
concrete correct-fix-fails mechanism (gate a) sets NOT READY.

End the file with EXACTLY these three machine-readable lines, in this order, nothing after them:
GATE_A: READY            (or `GATE_A: NOT_READY`) — the fairness verdict from gate a ONLY. Leniency,
                         hints, realism and quality NEVER change this line. Any row in the Conflicts
                         table makes it NOT_READY.
CONFLICTS: 0; DECIDING: 0  — rows in the Conflicts table (steps 1a and 4a), then how many of them
                         are deciding (`DECIDING: unknown` when trial_summary.md is missing). The
                         pipeline reads this line: a deciding conflict blocks an automatic KEEP and
                         the delivery until the owner records a CONFLICTS-RULED line.
NEEDS_HUMAN_REVIEW: NO   (or `NEEDS_HUMAN_REVIEW: YES`) — set YES when the gate-a call rested on a
                         JUDGMENT (a genuine/defensible ambiguity, a borderline reading, or notable
                         disclaimers a human should confirm), so a person can look, and always when
                         a conflict is deciding or "unknown". This is SEPARATE
                         and does NOT change GATE_A: a task can be `READY` + `NEEDS_HUMAN_REVIEW: YES`
                         or `NOT_READY` + `NEEDS_HUMAN_REVIEW: YES`. Only set NO when the verdict is
                         clear-cut.

Above those three lines, return: the READY / NOT READY reasoning (with its unfairness reason if NOT
READY), the Conflicts table (write "none" if empty), the "Required: generalize" list (step 3a;
write "none" if empty), the "Quality to tighten" list, and — if NEEDS_HUMAN_REVIEW is YES — a
one-line "Human review:" note naming exactly what to confirm. Keep the prose under 300 words (the
tables do not count).
