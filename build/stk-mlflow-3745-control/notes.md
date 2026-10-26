# stk-mlflow-3745-control — build notes

Control for `stk-mlflow-3745`: the same pinned checkout and the same report, but only the
advisory's own route (the write-time destination check on gateway secret configuration) is in the
security tests and the reference fix.

- Reference (`solution/fix.patch`): adds the outbound-address helper with the URL check and calls it
  from the store's create/update writers. No merged-config, connect-time, shipped-default or
  derived-host handling (those are the stacked task's extra concepts).
- Security tests (4): loopback, private, link-local and unspecified upstreams are refused on
  create.
- Functional tests (5): public configuration round trip, model/endpoint lifecycle, shipped local
  default still called, public third-party configuration accepted, legitimate region/location
  names accepted.

Local runs: pinned 4/4 security fail + 5/5 functional pass; reference 4/4 + 5/5; check patches
behave as declared (`sf-no-write-api-base`, `sf-crash`, `sf-wrong-object` security_fail;
`ff-refuse-all` functional_fail; `pass-alternative`, `pass-hardening` all pass).

Static: fails only on the intentionally missing blind-fix pass patch the fairness team writes.
