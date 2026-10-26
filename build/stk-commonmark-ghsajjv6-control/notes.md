# stk-commonmark-ghsajjv6-control notes

Started 2026-10-26T02:27:36Z. Finished 2026-10-26T__END__Z.

This is the control task for stk-commonmark-ghsajjv6. It uses the same pinned commit
(6cfa16c7f37e2748114c56d9375a09af656b995c) and a byte-identical instruction.md; only the
advisory's own route (unpaired smart quotes re-copying the growing text node) is in its security
tests and in its reference fix (04a5d11ef6bf, reduced to source).

- Security tests: quotes_double, quotes_single, quotes_mixed, quotes_in_heading. All four fail on
  the pinned code (timeouts or the 20 s in-test bound) and pass on the reference fix.
- Functional tests: the same nine as the stacked task (the project's Attributes and SmartPunct
  fixtures plus a large legitimate document and a plain document). All pass on the pinned code and
  on the reference fix.
- Check patches: no_change (security_fail), cap_merge (security_fail), bad_join (functional_fail),
  hardening (pass), alt_fix (pass, listener-level merge once per container with the shared merger
  untouched). All verified locally against a clean pinned checkout.
- Static checks: common/gate static and common/builder/conformance_check.py pass.

The control exists only to isolate the effect of stacking from the effect of the host; it is not
intended to be hard.
