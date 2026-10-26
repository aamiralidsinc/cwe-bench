# stk-fabio-ghsafq95-control

Control task for the stacked build: the same pinned fabiolb/fabio checkout and the same
`instruction.md`, but only the advisory's own route (the hop-by-hop declaration that removes a
forwarding header the proxy set) is exercised.

- Security tests (5): `tests/security/connection_test.go` (raw HTTP/1.1 through the real binary).
- Functional tests (10): the same keep-working suite as the stacked task.
- Reference: `fdaf1e966162` alone (the first published fix), reduced to `proxy/http_headers.go`.
- Checks: `cf-sf-no-sanitiser.patch` (security_fail), `cf-ff-refuse-connection.patch`
  (functional_fail), `cf-pass-hardening.patch` (pass), plus the declared blind slot.
- Prior verification: pinned tree 5/5 security fail + 10/10 functional pass; A alone 5/5 + 10/10
  (reward 1.0); the miss patch 5 security fail; the over-broad patch 9 functional fail.

## Gate (2026-10-23)

- static: PASSED.
- nop: PASSED — the 5 connection tests fail, 10/10 functional pass (trial
  `stk-fabio-ghsafq95-control-nop-1792737371`).
- oracle: PASSED — 3/3 runs at reward 1.0 (15/15 each; identical result maps).
- patches: PASSED — cf-sf-no-sanitiser (5 security failing, functional all passing),
  cf-ff-refuse-connection (9 functional failing), cf-pass-hardening (reward 1.0).

End: 2026-10-23T07:04Z.
