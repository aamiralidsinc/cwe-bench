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
2. Leniency: for each security property and each trap in manifest.traps, name the most plausible
   WRONG fix and whether some test catches it (cite the test and the checks/ patch, if any). List
   wrong fixes no test catches.
3. Hints: any sentence in instruction.md that names or paraphrases a file, function, mechanism, the
   fix approach, a trap, a variant list or the flaw count. Quote it and propose neutral wording.
4. Realism: is each trap code a real maintainer could have written, reachable via the real entry
   point? Flag anything that looks planted or contrived.
5. Verdict: READY, or NOT READY with the exact changes required (instruction sentences to add or
   remove, tests to loosen or tighten). Be strict: the client audits fairness and rejects cheats.

Return the verdict and the medium/high items (under 300 words).
