# stk-link-preview-js-ghsacpjf-control — notes

Control for `stk-link-preview-js-ghsacpjf` (build rule 13). Same pinned checkout
(2f3dc49e7f08d9862f1e3b157f09617d820248b8), same `instruction.md` (byte-identical), same
`environment/` and `tests/test.sh` shape.

Differences from the stacked task, by design:

- The security suite carries the advisory's own route only: the caller's address-resolution answer
  is checked, but the request is made to the name, which is resolved again when the connection is
  opened (four forms: a plain link, a link found inside text, a secure link, and the manual redirect
  target of the same guard).
- `solution/fix.patch` closes that route only: the request is sent to the validated address at both
  request sites. It does not classify the answer beyond the dotted-quad check the pinned code
  already had, does not check a link's own literal host, and does not take over followed redirect
  hops.
- The functional suite, the project's own offline cases and the hidden-test harness are identical to
  the stacked task's.

Local results: pinned 0/4 security fail-as-expected, 9/9 functional pass; control reference 4/4 +
9/9. Check patches: `miss_T4` leaves all four security cases failing with functional green;
`refuse_all` and `adjacent_api` each break functional cases; `hardening` scores full marks.
