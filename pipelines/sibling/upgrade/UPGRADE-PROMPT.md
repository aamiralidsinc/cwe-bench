You are UPGRADING one already-built CWE-bench security-fix task to comply with the sibling-injection
rules (BETTER-PATTERNS §2–§8), reusing its existing build wherever possible, before a fresh trial.
Project root: /home/mara/cwe-bench. Task slug: {{SLUG}}.

Read, in order: tasks/{{SLUG}}/instruction.md, every file in tasks/{{SLUG}}/tests/,
tasks/{{SLUG}}/solution/fix.patch, build/{{SLUG}}/manifest.json, build/{{SLUG}}/notes.md,
build/{{SLUG}}/checks/*.patch, and the task's repo under tasks/{{SLUG}}/ (the pinned code the solver
sees). The solver sees ONLY instruction.md and the repository — never tests, notes or task.toml.

Apply, in order, making the SMALLEST change that satisfies each rule:

1. INSTRUCTION — one general property only (§2/§3/§4). Rewrite instruction.md so the security
   property is stated ONCE, in general terms over the protected data or outcome. Remove every
   sentence that NAMES or DESCRIBES where a route, sibling or far site lives — no route, operation,
   command, channel, object-kind, stage, format, file, function, or count/route list, even in
   product terms. Keep each coupled must-keep-working contract, but state it generally. A property is
   fair when, read literally, it covers the route; it must not point at it. A report that points at
   its routes is a checklist, and checklists get solved — this is the change that most makes models
   fail, so do it thoroughly.

2. LEVERS — at least one HOW-type (§5/§6/§7). The task must have >=1 how-type lever, whose fix needs
   the mechanism understood: a producer the check never calls (M6), a parser/shape differential (M8),
   a coupled must-keep-working value (M11), or a route where the protection never existed (M4). If it
   has none (every lever is just an extra entry point or a planted copy of one concept), ADD exactly
   one how-type lever as realistic in-repo code a maintainer could plausibly have left, reachable
   through the real entry point, covered by the general property, and never described in the
   instruction. Do NOT add where-type route lists.

3. COVERAGE (§8). The security tests must assert the property across every route it covers literally,
   INCLUDING routes the published upstream fix left open and routes where the protection never
   existed — leaving such a route open is a model failure, not a fairness gap. Add one behavioural
   security test (through the real entry point, expected values computed in the test, no network) and
   one security_fail check patch (checks/*.patch: a fix that misses only that lever) per
   newly-covered lever, wired into manifest.patch_checks with the stated expect.

4. ORACLE + MANIFEST. Extend solution/fix.patch so the oracle still PASSES 1.0 against the new tests
   (it must close every lever). Update manifest.json (patch_checks, traps, leak_terms) to match. Keep
   instruction.md free of every manifest.leak_terms token.

HARD RULES:
- Keep the task valid: the pinned code must still FAIL every security test (nop); the oracle must
  still PASS all tests (oracle 1.0). Never weaken a test merely to make something pass.
- REUSE the prebuilt image. An instruction / test / manifest / checks-only change needs NO image
  rebuild. Rebuild the image ONLY if you changed repo code in step 2, and then rebuild it the same
  way the task was originally built. State clearly in your report whether a rebuild was needed.
- Edit only under tasks/{{SLUG}}/ and build/{{SLUG}}/. Scratch in ~/.tb-graders/cwe/work/{{SLUG}}/.
- Do NOT look up the upstream fix online.
- If the task cannot support a fair §2 task without a from-scratch rebuild (bad lever, no how-type
  potential), STOP and report why — do not ship a weak task.

After your edits, run ONLY the static leak-scan to confirm instruction.md carries no leaked term:
  python3 -I common/gate/gate.py {{SLUG}} --only static
(A missing blind.patch in static is allowed — it is wired separately.) Do NOT run nop/oracle/patches
yourself: the launcher re-gates after you, and ONLY when a container gate is actually needed. But you
MUST keep the task valid by your own reasoning — the pinned code must still FAIL every security test,
and solution/fix.patch must still PASS all tests; if you changed any test or the fix, re-check that
logic carefully before finishing.

Report, under 300 words: the instruction's framing before and after (one line each); each lever and
its type; what coverage you added; whether you changed any file under tests/, solution/, environment/
(repo code), or checks/ — i.e. whether a full container gate is needed — or changed ONLY
instruction.md / manifest metadata (no container gate needed); whether the image was rebuilt; and
anything you could not satisfy and why.
