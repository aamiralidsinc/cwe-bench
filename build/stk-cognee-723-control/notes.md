# stk-cognee-723-control — build notes

- Same pinned tree (topoteretes/cognee @ 4067f0b8a255f3a511a71cc0806b9f20dd73c31b) and the
  byte-identical `instruction.md` as the stacked task.
- Only the advisory's own route is covered: `POST /api/v1/settings`. Four security tests (llm block,
  vector block, both blocks, a second ordinary account) and the same nine functional tests as the
  stacked task.
- Reference fix: the final upstream superuser guard (the published fix's net effect after the
  revert), applied at the write handler.
- Check patches: `control_malformed_identity` (a guard that mistypes the identity, so the write stays
  open; security_fail) and `control_overbroad` (all writes refused; functional_fail).
- Local: pinned — 4/4 security tests fail, 9/9 functional pass; guard fix — 4/4 security and
  9/9 functional pass. Every check patch applies cleanly to the pinned tree.
- Gate result: see `gate_report.json` / `gate_verdict.json` in this directory.
