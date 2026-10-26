# stk-uri-js-ghsagcv8-control — build notes

Control for `stk-uri-js-ghsagcv8`: the same pinned checkout, the same report (`instruction.md` is
byte-identical to the stacked task's), but only the advisory's own route in the security tests and
the reference.

- Security suite: 17 cases (T1's 12 delimiter forms and T2's 5 case variants), driven through both
  public entry points.
- Functional suite: identical to the stacked task (186 tests: 166 project QUnit cases + 20 API
  cases).
- Reference (`solution/fix.patch`): the two published fixes together (A + B: a case-insensitive
  web-scheme delimiter normalisation). It leaves the scheme-relative and whitespace routes open,
  which the control does not test.
- Check patches: `control_miss_case_variant.patch` (A without `/i`, security_fail, 5 failing) and
  `control_overbroad.patch` (normalises every scheme, functional_fail, 36 failing).
- `strict_gate` is false for the control, matching the pre-reset build.

Gate (2026-10-23): static PASSED; nop PASSED (17 security failing, 186 functional passing);
oracle PASSED (2 identical runs at 1.0); patches PASSED 2/2.
