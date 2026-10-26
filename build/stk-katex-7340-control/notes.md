# stk-katex-7340-control — build notes

Control for stk-katex-7340: the same pinned checkout, the same report (instruction.md is
byte-identical), but only the advisory's own route in the security tests and the reference.

- Reference: the published fix 0adf7e77 source hunks (src/Settings.ts, src/Namespace.ts).
- Security tests (5): the caller's options entry read as an own property — polluted trust on
  \href, a trust value on the options object's prototype, \url and \includegraphics, and a macro
  table on the options prototype (the same read for another key).
- Functional tests: the same 25 hidden functional tests as the stacked task plus the project's own
  test/katex-spec.ts (623 tests, pristine copy from /tests).
- Local matrix: reference 5/5 + 648/648; pf-miss 0/5 + 648/648; pf-trust-key-only 4/5 + 648/648;
  ff-refuse-trusted 5/5 + 620/648; ff-overcoerce 5/5 + 545/648; pass-hardening and pass-alt
  5/5 + 648/648.
- The control has no hidden route, so its selection isolates the effect of stacking from the host.
