# xray-core-ds — build notes

- Start (UTC): 2026-10-24T04:49:28Z (resumed 07:50:20Z after the host Docker repair)
- Pattern: A (published fix's far sites + uncovered routes), track: injected
- Advisory: GHSA-5WF9-H793-W73C (CWE-297); vulnerable 0bafca94…, fix 64fada32…

## Levers (one line each)

- T1 (how-type, coupled must-keep-working): the verifier accepts a pinned-CA chain with an empty
  DNSName, and each client route must supply the dialed host — tls/config.go:333 plus
  grpc/dial.go:139 (name copied only for domain destinations) and hysteria/dialer.go:348 (QUIC
  fills the name on its own copy). Dismissal: "the transports already set SNI".
- T2 (how-type, route where the protection never existed): realm HTTP rendezvous client builds its
  TLS config with no destination — finalmask/realm/http.go:88. Dismissal: it is a NAT-punch helper,
  not a proxy transport.
- T3 (how-type, route where the protection never existed): RAW/TCP fromMitm override can be empty —
  tcp/dialer.go:41. Dismissal: MITM forwarding is a special mode.
- T4 (how-type, wrong object, injected): TLS config cached per settings object, not per destination —
  tls/cache.go:16 used by tcp/dialer.go:43. Dismissal: "the same settings always dial the same
  server".
- T5 (how-type, second implementation, injected): the DoH resolver's own uTLS stack verifies the
  pinned chain but not the host — app/dns/nameserver_doh.go:112. Dismissal: the resolver is not a
  proxy transport and does not use the shared verifier.

## Injected-sibling candidates considered

1. `tls/grpc.go` grpcUtls credentials reading the pre-clone config (O8b): rejected — with the
   fail-closed guard it can only break legitimate use, never fail open; not independently testable.
2. `tls/tls.go` copyConfig check/use differential (O8b): same problem — the verifier reads the
   original config, so the guard closes it.
3. DoQ nameserver accepting user TLS settings (O8b): viable but a QUIC DNS server is hard to drive
   offline; picked the DoH sibling instead, which is the same second-implementation idea over TCP.
4. Config-loader host default: rejected — a default from the camouflage Host header is ambiguous
   (the operator may intend that name), so it is not a clean violation.
5. Per-settings TLS config cache (T4): picked — production-plausible optimization, independently
   testable through the real transport dialer, and it makes the verifier decide on a different
   destination's name (a how-type wrong-object failure rather than a search cost).
6. DoH chain-only pin check (T5): picked — the resolver is a genuinely separate TLS implementation
   and the defect survives the published fix.

## Verified

- Every lever reproduces on the injected vulnerable tree and is closed by the reference fix; each
  hidden suite was run on the injected tree (all 6 security tests fail as exploits, all 9 functional
  tests pass), on the reference fix (all pass), and on all ten check patches.
- The published fix alone (guard + gRPC + Hysteria) leaves T2/T4/T5 open and breaks the realm
  functional case; a guard-only repair breaks gRPC-over-IP and Hysteria legitimate use.
- gRPC, Hysteria/QUIC, TLS, realm and DoH paths are all loopback/offline; no service, GPU or kernel
  feature is needed.
- Project tests for the affected area that do not need the internet pass on the injected tree and on
  the reference fix.

## Could not verify

- `present_in_latest` for the two real uncovered routes (realm, fromMitm): not checked against
  current upstream.
- Whether the project documents pinnedPeerCertSha256 as always enforcing the hostname: docs are not
  in the tree.
- The project's DoH/QUIC nameserver tests need the public internet and are therefore not run by the
  verifier; the pristine copies are restored so the package still compiles.

## Gate results (2026-10-24)

- static: PASS
- nop: PASS — 6 security results, all failing as exploits; 35 functional results, all passing
- oracle: PASS — 3 runs, reward 1.0 each, identical results
- patches: PASS — 9 checks: miss_grpc_hysteria / miss_realm / miss_frommitm / miss_cache /
  miss_doh each fail exactly their intended security test with no functional failure; overbroad
  fails only the pinned-leaf-without-a-name functional test; refuse_all fails 13; alt_pass and
  hardening score 1.0. The `blind` patch is declared for downstream generation.
- End (UTC): 2026-10-24T09:00:00Z (the session was paused by the operator from about 05:50 to 07:50
  while the host Docker daemon was repaired; all stages above were then re-run on the fixed daemon).
