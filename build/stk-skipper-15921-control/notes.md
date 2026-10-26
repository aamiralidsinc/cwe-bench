# stk-skipper-15921-control — build notes

Control task for `stk-skipper-15921`. Same pinned tree, same injected third route, same
`instruction.md` (byte-identical), but only the advisory's own route appears in the security suite
and in the reference fix.

- Reference (`solution/fix.patch`): the status-returning extraction, the ext_authz adapter that
  writes the completeness value, and the first body-evaluating request filter. The second real
  filter and the injected prefix route are left as they are at the pinned commit.
- Security suite: `zz_sec_advisory_test.go` only (three tests on the reported route).
- Functional suite: the same nine tests as the stacked task.
- Check patches: advisory-route miss, content-length wrong fix, over-broad functional failure,
  hardening pass, alternative pass (upstream fix, which closes the advisory route), blind declared
  but written later.
