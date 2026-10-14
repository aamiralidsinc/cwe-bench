# Stacking builder brief (Branch C)

Build ONE Harbor task from a repo that already contains several REAL,
co-present security vulnerabilities — no injection. Read `BUILDER.md` first for
the general rules (environment, offline, real entry point, gate, check patches);
this file covers only what differs for stacking.

## Inputs
- A row from `sourcer/stacking-shortlist.tsv` (repo, ecosystem, co-present count,
  the sample advisory ids open at the peak-overlap version, the CWEs).
- SLUG given with this brief.

## Pick the commit (the heart of stacking)
1. Clone the repo (scratch dir under ~/.tb-graders/cwe/work/<slug>/).
2. For each candidate advisory, find its introduced and fixed commits/versions.
3. Choose a single commit **C** where as many target advisories as possible are
   simultaneously OPEN — i.e. for each included vuln, C is at or after it was
   introduced and strictly before it was fixed. Every included vuln must be
   genuinely present at C (verify by reproducing it on a checkout of C), not
   introduced by a later regression relative to C.
4. Aim for 4–6 co-present vulns for a first task (more = much more build cost).
   Prefer favoured-class ones (auth/session, access control, integrity, design)
   and drop any you cannot reach through a real entry point offline.
5. The environment is the repo at **C** (deps/services installed, offline,
   `/app/.git` removed, agent layer appended).

## Tests: one group per vuln
- `tests/security/` : for EACH included vuln, one or more tests that exploit it
  through a real entry point and assert it is blocked. On the vulnerable checkout
  (C) every security test FAILS; after the full fix every one PASSES.
- `tests/functional/` : legitimate-use tests for each affected feature, so a fix
  that disables a feature fails.
- `score.py` (unchanged) gives partial credit, but acceptance still requires the
  model to reach reward 1.0 — i.e. fix ALL of them. Partial fixes are recorded
  but count as a non-solve, which is exactly why stacking is hard.

## Oracle and check patches
- `solution/fix.patch` = the real upstream fixes for all included vulns, source
  only, applied together; must score 1.0 twice, identically.
- `build/<slug>/checks/`:
  - `subset_fix.patch` → expect `security_fail`: fixes some but not all vulns
    (e.g. all but one). Must leave >=1 security test failing, functional all pass.
    This proves the task isn't solved by fixing the easy ones.
  - `disable_feature.patch` → expect `functional_fail`.
  - `alt_correct_fix.patch` → expect `pass`: all vulns fixed, written differently
    from upstream where plausible.

## instruction.md (the report)
Describe the observed impacts and how each is triggered, through real entry
points, as a user/triager would file them — multiple symptoms are fine. NO fix,
NO file/function names, NO line numbers, NO CVE/GHSA ids, and do NOT state how
many issues there are. The gate's leak check enforces this (list the CVE ids and
fixing-function names in manifest `leak_terms`).

## Memorization note
These are public CVEs. Trials run offline so the model cannot look them up, but
pure recall is a risk: prefer recent advisories and favour stacks where the
combination (not each individual bug) is the hard part.

## Gate
`python3 -I builder/gate.py <slug>` must print PASSED. Report per BUILDER.md,
plus: which commit C you chose, which vulns are co-present there and your proof
each is really present at C, and which you dropped as unreachable offline.
