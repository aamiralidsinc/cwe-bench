# stk-virtualenv-2350-control build notes

Control task for `stk-virtualenv-2350`: the same pinned commit, the same `instruction.md` (byte
identical), and only the advisory's own download-integrity route in the security tests and in the
reference.

- **Pinned commit:** `d721ff140ce4afdc2a9b76751e4584e25d9fbea6`
- **Reference:** the published fix `a01ed3e2f239d6ab1fce62c5c7664ccf268fff6d` (source changes only,
  `solution/fix.patch`).
- **Lever:** T1 only — a downloaded seed wheel is returned whatever pip left behind, and all three
  pip report shapes are accepted (`src/virtualenv/seed/wheels/acquire.py:140-142`, `:145-154`).
- **Coupled value:** a wheel from an operator-configured index and a wheel with no public release
  record keep working (functional tests).
- **Local runs:** pinned 3 security fail / 79 functional pass; published fix 82/82; every check
  patch matches its declared expectation. Container gate results are in `gate_report.json`.
- The instruction is copied from the stacked task and is kept identical for the task's whole life
  (checked by `pipelines/stacking/3-build-gate/check_stack.py`).
