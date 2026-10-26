# stk-dottie-js-ghsar5mx — build notes

Start: 2026-10-23T01:24:06Z (original build; build/start_utc.txt was reset by the re-run)
End: 2026-10-23T02:32Z (original build). Restored and re-gated from 2026-10-23T08:38Z.

The original build completed and passed every gate stage at 02:32Z. A later pipeline restart
removed `tasks/` and `build/<slug>/manifest.json`; the deliverable was restored from the gate's
own snapshot (`/tmp/gate-04_diq53`, the alt-fix variant, whose `solution/fix.patch` had been
replaced by tests/check machinery) and the reference patch was regenerated from the gated oracle
workspace. The regenerated `solution/fix.patch` reproduces that file byte-for-byte
(md5 8c8017da9e84a6d6be72aa6de04eaa14) and the manifest was rewritten to the same design. All
test files were confirmed final by matching the oracle run's JUnit test names (21 security + 65
functional) exactly. The control task was rebuilt the same way: its reference and both check
patches were regenerated from the control gate jobs' recovered workspaces (nop workspace equals
the pinned file byte-for-byte, md5 67a67beb0e930b0be69c5302d96b907d).

Stacked H3a task on mickhansen/dottie.js. Pinned b48e22714aae4489ea6276452f22cc61980ba5a4
(2.0.3), which `git log` confirms is the first parent of A's fix 7d3aee1c9c3c (2.0.4,
"rudimentary __proto__ guarding"). B's fix 7e8fa1345a4b (2.0.7) is the later complete guard.

## Levers (one line each)

- **T1 (A, advisory route)** — the nested-write traversal splits a dotted path and writes every
  segment unfiltered; a prototype-bearing segment at any position replaces an intermediate
  object's prototype, and the default-value call delegates to it. dottie.js:74,81,86,89,94,107 and
  111-113. Reason to dismiss: the report shows one dotted name, so a first-segment check (what
  upstream shipped in A) looks complete.
- **T3 (A, advisory route)** — the flat-object conversion runs its own split-and-walk over the
  caller's chosen separator; A guarded only its first part, B had to add every part.
  dottie.js:141,142,147,148,149,153,156. Reason to dismiss: the report's example is a write call,
  so the conversion reads as a different feature.
- **T4 (B, uncovered upstream, deepseek-type)** — a key with no separator goes to the plain-copy
  branch; an own `__proto__` key (as JSON.parse produces) goes through the setter and replaces the
  returned object's prototype. dottie.js:134,141,161,162. Reason to dismiss: "a key with no
  separator is just copied, not a path". Both published fixes leave it open.
- **T5 (B, uncovered upstream, mimo-type)** — an array path is used raw; a non-string part is
  converted to a property name on access, so a strict comparison of the raw part misses it, while
  a join/re-split fix breaks array parts that contain the separator. dottie.js:74,81,86,89. Reason
  to dismiss: "array paths are arrays of strings". Both published fixes compare raw parts.

Concepts (manifest.stacking.concepts): [T1,T5] (one guard site: the nested-write traversal,
including the property-name conversion), [T3], [T4]. T2 (the default-value call) is folded into
T1: a guard inside the nested write covers it, so it is not an independent concept; the reader's
design left it out and its security cases are still run under T1.

## Verified

- Pinned behaviour reproduced for every lever through the public entry points (nested-write,
  default-value, flat-object conversion and its one-argument form). All 21 security cases fail on
  the pinned tree; all 65 functional cases pass (18 coupled cases + the project's 46 Mocha cases).
- Reference fix (`solution/fix.patch`): 21/21 security, 65/65 functional.
- Check patches, each run locally against the pinned tree before the container gate:
  - `miss_concept_set.patch` 10/21 security, functional all pass;
  - `miss_concept_transform_delimited.patch` 15/21, functional all pass;
  - `miss_concept_transform_plain.patch` 17/21, functional all pass;
  - `guard_before_coercion.patch` 16/21 (only T5 fails), functional all pass;
  - `reads_only.patch` 0/21, functional all pass;
  - `upstream_first_fix.patch` (A alone) 2/21, functional all pass;
  - `upstream_fix.patch` (A+B) 12/21, functional all pass (T4 and T5 stay open);
  - `functional_overbroad.patch` 21/21 security but 63/65 functional (substring blocklist);
  - `refuse_all.patch` 21/21 security but 33/65 functional;
  - `alt_correct_fix.patch` 21/21 + 65/65; `hardening.patch` 21/21 + 65/65.
- The project's pinned Mocha suite (6 files, 46 cases) passes on the pinned tree, the reference and
  every check patch that is expected to keep functional behaviour; it fails 14 cases under
  `refuse_all.patch`.
- Four repeated local runs of every patch produced identical JUnit output (same hashes), so the
  suites are deterministic.
- Control task, local: pinned 0/6 security + 65/65 functional; control reference 6/6 + 65/65;
  `control_miss_first_position.patch` 1/6 + 65/65; `control_overbroad.patch` 6/6 + 63/65.
- No advisory regression test is present at the pinned commit: A adds 8 + 12 lines to
  set.test.js/transform.test.js and B adds two new *.proto-bypass.test.js files, all after b48e227.
- Current upstream (2.0.7, master 24ca5e8) still has T4 and T5 open (the plain-copy branch is
  unguarded and the guard compares raw path parts with `includes`); register rows updated.

## Could not verify / guesses

- Tier estimates come from the screener record; trials were not run here (the build prompt forbids
  running target models), so the bar is unknown until the trial batch.
- `stacking/score_stack.py` scores this design 0.053 (P(fail all 3 attempts) 0.23 for each model)
  and flags `single-trap-carries`: dropping each model's hardest concept leaves 0.002. That is
  inherent to the reader's three concepts, two of which (T1, T3) the record tiers easy for both
  models. It was built as the host specified.
- Whether a correct fix must also refuse `constructor`/`prototype` is not set by the pinned code:
  at the pinned commit such paths create own shadow objects and do not write onto a prototype.
  The reference blocks them (published B behaviour), but no security test requires or forbids it,
  and no functional test uses them as legitimate names.
- The refusal mode is deliberately unjudged: tests accept a skipped write or a thrown error.
- No injected sibling: the reader's design names none and the project has one implementation file.

## Container gate

- static: fails only on the missing `blind` pass patch (permitted; the blind patch is written
  after the build).
- nop: PASSED — 21/21 security tests fail on the pinned tree, 65/65 functional pass (reward 0.0).
- oracle: PASSED — 3/3 identical runs, reward 1.0 (21/21 security, 65/65 functional).
- patches: PASSED 11/11 on the retry. The first attempt produced the known Harbor egress-probe
  flake on the second check (ValueError: network_mode='no-network' is not supported because the
  30 s sidecar readiness probe timed out under the shared VM's load); the stage was retried
  unchanged. Container results (all match the local matrix): `miss_concept_set` 10/21 sec,
  functional 65/65; `miss_concept_transform_delimited` 15/21; `miss_concept_transform_plain`
  17/21; `guard_before_coercion` 16/21; `reads_only` 0/21; `upstream_first_fix` 2/21;
  `upstream_fix` 12/21 (only T4's four and T5's five security cases fail); `functional_overbroad`
  functional 63/65; `refuse_all` functional 33/65; `alt_correct_fix` and `hardening` reward 1.0.

## Control task gate

- static: PASSED.
- nop: PASSED — 6/6 security tests fail, 65/65 functional pass.
- oracle: PASSED 2/2 identical runs at reward 1.0 (6/6 security, 65/65 functional) after one retry
  of the same egress-probe flake.
- patches: PASSED 2/2 — `control_miss_first_position.patch` security_fail (1/6, functional
  65/65), `control_overbroad.patch` functional_fail (security 6/6, functional 63/65).

## Rebuild verification (2026-10-23, from 08:38Z)

The reference fix is one shared predicate plus an in-place guard at each of the three write sites:
every part of the nested-write path (after `String()` conversion), every part of the conversion
loop after the caller's delimiter split, and the separator-free copy branch.

Local matrix re-measured against the restored files, identical to the original build:

- pinned: security 21/21 fail, functional 65/65 pass.
- reference: 21/21 security pass, 65/65 functional pass.
- `alt_correct_fix` 21/21+65/65; `hardening` 21/21+65/65.
- `miss_concept_set` 11 security fail; `miss_concept_transform_delimited` 6; `miss_concept_transform_plain` 4;
  `guard_before_coercion` 5; `reads_only` 21.
- `upstream_first_fix` 19 security fail; `upstream_fix` 9 security fail (T4 + T5 open).
- `functional_overbroad` 2 functional fail; `refuse_all` 32 functional fail.
- Control: pinned 6/6 security fail; reference 6/6 pass + 65/65 functional; `control_miss_first_position`
  5 security fail + 65/65 functional; `control_overbroad` 6/6 security + 2 functional fail.

## Fairness

- The instruction states one outcome-based invariant over "path, key or path part, however written
  or supplied", so it covers transform keys and array parts without naming either site.
- It names the coupled legitimate values in property terms: ordinary nested names, list paths
  (each part treated as given), the force option, reads and defaulting, and names that merely
  resemble a prototype name.
- The attack example is one dotted name at one write; no route is described.

## Container gate, re-run (2026-10-23)

All stages run one at a time on the restored files:

- static: PASS (main and control).
- nop: PASS — main 21/21 security fail, 65/65 functional pass; control 6/6 security fail,
  65/65 functional pass.
- oracle: PASS — main 3/3 identical, reward 1.0, 86 tests; control 3/3 identical, reward 1.0,
  71 tests.
- patches: PASS 11/11 on main, 3/3 on control (the blind file is written later by run_blindfix and
  is skipped here). Container outcomes match the local matrix above exactly:
  `miss_concept_set` 11/21 security fail; `miss_concept_transform_delimited` 6; 
  `miss_concept_transform_plain` 4; `guard_before_coercion` 5; `reads_only` 21; `upstream_first_fix`
  19; `upstream_fix` 9 (only T4's four and T5's five fail); `functional_overbroad` 2 functional
  fail; `refuse_all` 32 functional fail; `alt_correct_fix` and `hardening` reward 1.0.
  Control: `control_miss_first_position` 5 security fail with all functional passing;
  `control_overbroad` 2 functional fail; `hardening` reward 1.0.
- `stacking/check_stack.py`: conforming (3 concepts, H3a).

End: 2026-10-23T09:18Z.
