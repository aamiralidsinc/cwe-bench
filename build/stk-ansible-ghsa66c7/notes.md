# Build notes: stk-ansible-ghsa66c7

Started: 2026-10-26T02:16:34Z
Ended: 2026-10-26T04:10:13Z

Source: ansible/ansible at 157b783521b52d9c3f357e811f6be0ec7600a89e, the direct parent of
998793fd0ab5 ("Fixes to safe_eval", CVE-2014-4657). The later, incomplete follow-up
5429b85b9f6c ("Change safe_eval to a strict white list", CVE-2014-4678) shipped on the 1.6
branch; the two fixes are not linear descendants in git (verified with the GitHub compare API
and `git rev-parse 998793fd0ab5^`).

## Levers (one line each)

- T1 (mimo, advisory route): the controller's value conversion guards spellings (`\w\.\w+\(`,
  `import \w+`) instead of parsing the expression, and fails open; lib/ansible/utils/__init__.py:948-992.
- T2 (deepseek, published-fix far site): a separately maintained copy of the same conversion in
  the support code inlined into every shipped module, reached when a mapping-valued argument
  arrives as non-JSON text; lib/ansible/module_utils/basic.py:640-671, called at 697-704.
- T3 (deepseek, uncovered upstream): a stored value is re-expanded by the ordinary, unsandboxed
  Jinja2 environment when it is looked up; lib/ansible/utils/template.py:388-403 with the
  environment at 530.

## Wrong-fix behaviour (fresh copy of the pinned tree + patch, same three suites)

| patch | security | functional | expected |
|---|---|---|---|
| sf-miss-controller (fixes T2+T3) | 5 of 6 fail | pass | security_fail |
| sf-miss-module (fixes T1+T3) | 1 of 6 fail (the module copy) | pass | security_fail |
| sf-miss-host-value (fixes T1+T2) | 1 of 6 fail (the value expansion) | pass | security_fail |
| sf-regex (spelling tightening) | 1 of 6 fail (call nested in an allowed call's argument) | pass | security_fail |
| sf-check-after-render | 1 of 6 fail (side effect before the check) | pass | security_fail |
| ff-refuse-all | 2 of 6 pass | 3 of 8 pass | functional_fail |
| ff-stop-retemplating | 0 of 6 pass | 6 of 8 pass | functional_fail |
| crash-as-refusal | 3 of 6 pass | 2 of 8 pass | functional_fail |
| pass-alt (literal parser) | pass | pass | pass |
| pass-hardening | pass | pass | pass |
| upstream_first_fix (A alone) | 2 of 6 fail | pass | security_fail |
| upstream_fix (A+B together) | 2 of 6 fail | pass | security_fail |

The real verifier flow (`tests/Dockerfile` image, the task's own `test.sh`) was run end-to-end on a
reference copy of the tree: status `scored`, reward 1.0, 20 of 20 tests.

## What was verified

- Gate stage `static`: PASSED for the stacked task and its control.
- Gate stage `nop` (real Harbor trial, separate verifier image): PASSED - security 0/6 pass,
  functional 14/14 pass, reward 0.0.
- The verifier flow was also run end to end outside Harbor with the task's own
  `tests/Dockerfile` image and `test.sh` on a reference-patched tree: status `scored`,
  reward 1.0, 20 of 20 tests.
- Pinned code, through `ansible-playbook` with a local connection: all six security tests fail
  with their side effect present; all eight functional tests and the six project tests pass.
- Reference fix (`solution/fix.patch` = T1 + T2 + T3): all twenty tests pass.
- Each wrong-fix patch was applied to a fresh copy of the pinned tree and run through the same
  three suites (table above). The control task's reference (T1 only) passes its four security
  tests and all functional/project tests; the pinned control fails all four security tests.
- The T3 route was confirmed by a behavioural test on the pinned copy (marker file created).
- The project test (`test/units/TestUtils.py`, six tests, restored from a pristine copy) passes
  on the pinned tree, the reference, and every pass patch.
- The upstream fixes were applied together to the pinned tree and run: the stack is not closed
  by upstream's shipped fixes (recall check). `upstream_first_fix.patch` is A alone.

## Gate stages not completed in this session

`oracle`: PASSED - three strict trials through Harbor, all reward 1.0 and identical (security 6/6,
functional 14/14 each).

`patches`: could not be run through Harbor. The shared 8-CPU VM was running 187-240 concurrent
Harbor jobs from other build sessions and its Docker daemon repeatedly stopped starting containers
(`docker run --rm alpine true` timed out; verifier containers came up `Dead`). The remaining
wall-clock budget was spent getting the three oracle trials through one at a time. This is an
infrastructure condition, not a task verdict. Re-run when the VM is quiet:

    python3 -I common/gate/gate.py stk-ansible-ghsa66c7 --only patches

Every check in `patches` was validated locally against the same three suites (table above), and the
reference was also run end to end with the real verifier image. The control task passed its
`static` stage; its Harbor stages were not run for the same reason, and its reference and pinned
behaviour were validated locally.
