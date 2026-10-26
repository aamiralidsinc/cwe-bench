# Fairness review — stk-fabio-ghsafq95 (pre-trial, gate requirement)

Read: `tasks/stk-fabio-ghsafq95/instruction.md`, every file under `tasks/stk-fabio-ghsafq95/tests/`,
`solution/fix.patch`, `build/stk-fabio-ghsafq95/manifest.json`, `notes.md`, and all 15
`build/stk-fabio-ghsafq95/checks/*.patch`. Nothing was run. No upstream fix was consulted.

Covering sentences used below (verbatim from `instruction.md`):

- **SET** — "Where the proxy sets a value on a forwarded request, or the operator designates a header
  to carry a trust value, the backend must receive the proxy's value unchanged: the client must not
  be able to remove it, alter it, or substitute a value of its own."
- **DESIG** — "For every header the operator designates to carry a trust value, the backend receives
  the proxy's own value on every path the proxy serves."
- **KEEP** — "Everything that works today keeps working." (also "Keep legitimate use working.")
- **INVARIANTS** — "These are invariants, not a list of cases."

## 1. Per-test fairness

| test | asserts | covering sentence | could a correct fix fail it? | risk |
|---|---|---|---|---|
| `security/clientip_test.go::TestSec_DesignatedClientIPHeaderIsFabios` | with `-proxy.header.clientip X-Real-Ip`, a client `X-Real-Ip: 9.9.9.9` must not replace the derived address | SET (designated) + DESIG; "substitute a value of its own" | **no** — dropping the `!= "X-Real-Ip"` skip writes the derived value; `IsLoopbackValue` accepts host or host:port | low |
| `security/connection_test.go::TestSec_ConnectionTokenDoesNotRemoveRealIP` | `Connection: close, X-Real-Ip` must not drop the proxy-set `X-Real-Ip` | SET ("the client must not be able to remove it") | **no** — removing only the protected token leaves the later derived value intact | low |
| `…::TestSec_ConnectionTokenDoesNotRemoveForwardedHost` | same for `X-Forwarded-Host` (backend sees `example.com`) | SET | **no** — same token filter | low |
| `…::TestSec_ConnectionTokenDoesNotRemoveForwardedProto` | same for `X-Forwarded-Proto` (`http`) | SET | **no** — same | low |
| `…::TestSec_ConnectionTokenDoesNotRemoveForwarded` | same for the `Forwarded` value (`for=127.0.0.1`) | SET | **no** — `Forwarded` is in every correct protected set | low |
| `…::TestSec_ConnectionDeclarationAcrossLines` | tokens split over two `Connection` lines cannot drop `X-Forwarded-Port` (`80`) | INVARIANTS + standard expert knowledge: repeated header fields combine (RFC 7230 §3.2.2); the proxy derives the port from the request | **no** — the correct parser reads `Header.Values("Connection")`; a first-value parser is a wrong fix, not a correct one | low |
| `…::TestSec_ConfiguredClientIPHeaderIsFabios` | declaration naming the configured `X-Client-IP` cannot remove it | SET (proxy-set + designated) | **no** — the protected set includes `cfg.ClientIPHeader` | low |
| `…::TestSec_RequestIDIsFabios` | `Connection: …, X-Request-ID` + client marker cannot suppress or replace the proxy-generated id | SET ("alter it, or substitute a value") + DESIG | **no** — filtering the token before the reverse proxy preserves the handler's value | low |
| `security/grpc_test.go::TestSec_GRPCClientIPIsFabios` | gRPC metadata for the configured address header is the peer address, one value, not `9.9.9.9` | DESIG ("on every path the proxy serves") | **no** — `peer.FromContext` host or host:port passes | low |
| `…::TestSec_GRPCRequestIDIsFabios` | gRPC request id is non-empty and not the client's `attacker-id` | DESIG | **no** — any proxy-generated value (e.g. the repo UUID) passes | low |
| `…::TestSec_GRPCTLSHeaderIsNotClientSupplied` | plaintext gRPC: client `x-secure: attacker-tls` must be absent | SET ("substitute a value of its own") + standard expert knowledge / the repo's documented contract: the transport-assertion header is set only on a secured connection, so the proxy's value on plaintext is none | **no for the natural fix** — delete the client's entry and set only when `peer.AuthInfo` is TLS; an implementation that writes an empty or invented "false" value would fail, but that is not the product's contract, so it is not a correct fix | medium |
| `functional/http_test.go::TestFunc_PreservesClientRealIPWhenNotDesignated` | no designation: client `X-Real-Ip: 6.6.6.6` reaches the backend | KEEP; the opening sentence is framing, and SET does not apply (no designation, and the proxy does not set the header when present) | **no** — a blanket overwrite is over-broad and breaks KEEP; the repo's own unit test pins this behaviour | medium |
| `…::TestFunc_PreservesClientForwardedHost` | client `X-Forwarded-Host: 9.10.11.12` is preserved | KEEP; SET does not apply (the proxy sets it only when absent) | **no** — same | medium |
| `…::TestFunc_AppendsForwardedForChain` | `X-Forwarded-For: 3.3.3.3` becomes `3.3.3.3, 127.0.0.1` | KEEP + standard expert knowledge: the appended chain is the proxy's own value; the client contributes a prior hop, it does not alter the proxy's value | **no** — a fix that strips client contributions breaks KEEP | medium |
| `…::TestFunc_OrdinaryHopByHopHeaderStillStripped` | a declared ordinary header (`X-Legit`) is still stripped | KEEP + standard expert knowledge: hop-by-hop semantics | **no** — the fix removes only protected tokens; deleting all of `Connection` is a wrong fix | low |
| `…::TestFunc_ConfiguredClientIPHeaderIsSet` | designated custom address header is set on an ordinary request | KEEP | **no** — unchanged branch | low |
| `…::TestFunc_RequestIDHeaderIsSet` | designated request id is set on an ordinary request | KEEP | **no** — unchanged write | low |
| `…::TestFunc_WebsocketUpgrade` | `Connection: Upgrade, X-Forwarded-Host` still negotiates 101 | KEEP; the rule protects a value, not the `Upgrade` token | **no** — the upgrade token is not protected and is kept | low |
| `…::TestFunc_WebsocketDeclarationAcrossLines` | upgrade tokens split over two `Connection` lines still negotiate 101 | KEEP + standard expert knowledge: repeated fields combine | **no** — `Values()` keeps `Upgrade`; a first-value parser is a wrong fix (`ff-single-line-parser`) | low |
| `…::TestFunc_AppendsForwardedForChainWhenConfigured` | with `clientip=X-Forwarded-For`, the chain still appends | KEEP + DESIG: the appended chain is the proxy's own value | **no** — the existing `X-Forwarded-For` exception must be kept; removing the whole condition is a wrong fix, not a correct one | medium |
| `functional/grpc_test.go::TestFunc_GRPCCallAndOpaqueMetadata` | an ordinary gRPC call succeeds and non-designated metadata (`x-trace-tag`) survives | KEEP; DESIG covers only designated names | **no** — a fix that deletes all metadata breaks KEEP | low |

## 2. Leniency (QUALITY, non-blocking)

| property / trap | most plausible WRONG fix | caught? (test; `checks/` patch) |
|---|---|---|
| P1: proxy-set values survive a hop-by-hop declaration (T1 base) | no filtering at all | yes — 7 security tests; `sf-no-connection-protection.patch` |
| P1 | refuse the request / crash on a protected token | yes — 9 functional fails `ff-refuse-connection.patch`; 7 security fails `sf-crash-on-attack.patch` |
| P1 | delete the whole `Connection` header | yes — `TestFunc_OrdinaryHopByHopHeaderStillStripped`, `TestFunc_WebsocketUpgrade`, `TestFunc_WebsocketDeclarationAcrossLines`; no check patch |
| P1 | parse only the first `Connection` line | yes — only `TestFunc_WebsocketDeclarationAcrossLines` (the security line-split test still passes, because the whole second line is dropped); `ff-single-line-parser.patch` |
| P1 | match tokens case-sensitively | **no test** — every declaration uses canonical case |
| T2: configured names removable | hard-coded well-known list only | yes — `TestSec_ConfiguredClientIPHeaderIsFabios`, `TestSec_RequestIDIsFabios`; `miss_concept_connection.patch`, `sf-hardcoded-list.patch`, `upstream_first_fix.patch` |
| T2 | protect the configured address name but not the configured TLS name on HTTP | **no test** — the TLS header is exercised only on gRPC |
| T3: request id removable/substitutable | protect only headers written in the header builder, miss the handler-written id | yes — `TestSec_RequestIDIsFabios`; `miss_concept_connection.patch` |
| T3 | append the proxy id instead of replacing | **not fully caught** — the HTTP test reads `Header.Get` and never counts values; the gRPC test does count |
| T4: designated address | keep the `X-Real-Ip` skip | yes — `TestSec_DesignatedClientIPHeaderIsFabios`; `miss_concept_clientip.patch`, `sf-no-clientip-overwrite.patch` |
| T4 | overwrite only the well-known `X-Real-Ip`, not a custom designated name | **no test** — no request supplies a value for a custom designated name without a declaration |
| T4 | overwrite unconditionally | yes — `TestFunc_PreservesClientRealIPWhenNotDesignated`; `ff-overwrite-xrealip.patch` |
| T4 | constant / listener-derived address instead of the client's | **no test** — the whole topology is loopback, so any local value passes |
| T6: gRPC path | fix HTTP only | yes — three gRPC security tests; `miss_concept_grpc.patch`, `sf-no-grpc-protection.patch` |
| T6 | delete client metadata but derive nothing | yes — `TestSec_GRPCClientIPIsFabios`, `TestSec_GRPCRequestIDIsFabios`; no patch |
| T6 | set the TLS assertion unconditionally | yes — `TestSec_GRPCTLSHeaderIsNotClientSupplied`; no patch |
| T6 | strip all metadata | yes — `TestFunc_GRPCCallAndOpaqueMetadata`; no patch |
| P3: designated value on the HTTP plaintext path | leave a client-supplied transport assertion on plaintext HTTP (the reference's HTTP side only filters declarations and never deletes this value) | **no test** — no HTTP test configures `-proxy.header.tls` |

**Wrong fixes no test catches:** (i) case-sensitive token matching; (ii) an `X-Real-Ip`-only
special case for T4; (iii) a constant or listener-derived client address (loopback-only harness);
(iv) append-instead-of-replace on HTTP (no value-count assertion); (v) a client-supplied TLS
assertion on the HTTP plaintext path. The `wrong_fix_catalogue` n/a entries (direction, read/write
split, check-after-adjustment, missing authority, adjacent API) have no analogue: one direction,
write-only, a filter before the reverse proxy, locally derived values, and no exported sibling the
tests touch.

## 3. Hints (QUALITY, non-blocking)

- "A client sent a request whose hop-by-hop declaration named a forwarding header the proxy had just
  set. The backend received the request with no such header at all." — paraphrases the mechanism
  (hop-by-hop declaration) and thereby the fix. Neutral: *"A client was able to make a value the
  proxy had set on a forwarded request disappear before the backend saw it."*
- The two contract clauses (SET's "operator designates a header to carry a trust value"; DESIG's "on
  every path the proxy serves") are the protected outcome, not a place to look. No file, function,
  header, flag, route, variant list or count is named. The v3 listing check labels them DESCRIBED
  (T2/T3/T4 and T6); that FAIL is user-waived in `LISTING_WAIVER.md`, and no narrower wording states
  the required contract.

## 3a. Surface descriptions — Required: generalize

**none.** The instruction names no sibling, far site or uncovered route, no product term that
identifies a stage, channel or format, and no general word that is also a stage or entry-point name.
The quantifier "on every path the proxy serves" states the property once over the protected outcome;
the "operator designates a header" clause defines the protected data class and names no source. The
impact example names no header, file or route. (Do not add a route- or value-pointing sentence to
make either path test fair; the property already covers both.)

## 4. Realism (QUALITY, non-blocking)

| trap | code a maintainer could write? | reachable via the real entry point? |
|---|---|---|
| T2 | yes — it is the published first fix's hard-coded list, with the configured names read from flags | yes — HTTP listener, `-proxy.header.*`, a raw request |
| T3 | yes — the request-id write in the request handler predates both advisories | yes — HTTP listener, `-proxy.header.requestid` |
| T4 | yes — the `X-Real-Ip` skip and conditional write are real, unmodified upstream code | yes — HTTP listener with `-proxy.header.clientip` and a client value |
| T6 | yes — the verbatim metadata copy is still upstream code, wired from `main.go` | yes — the real gRPC listener and transparent handler |

Nothing is planted. `sf-crash-on-attack.patch` is a synthetic wrong-fix check (a panic a solver might
write as "refusal"), not task code. T4 and T6 are routes the published fix left open; they are in
scope of the stated property by definition.

## Stacking checks

Concepts: **C1 = [T2, T3]** (declaration filter over operator-configured names), **C2 = [T4]**
(designated address value written instead of skipped), **C3 = [T6]** (the gRPC forwarding path).

| check | C1 (T2, T3) | C2 (T4) | C3 (T6) | outcome |
|---|---|---|---|---|
| S1 coupled traps | KEEP covers the configured-address/request-id values; SET does not forbid them (the proxy sets them) | KEEP covers undesignated preservation and the appended chain; SET applies only to proxy-set/designated values | KEEP covers opaque metadata; DESIG covers only designated names | pass |
| S2 shape traps | a declaration naming a proxy-set/designated header is the attack; legitimate split/upgrade shapes still succeed (token ignored, request served) | a client value for a designated header is outside the legitimate set; the only protected pass-through is for values neither set nor designated | designated metadata values and a client assertion on an unsecured connection are outside the legitimate set; non-designated metadata is legitimate | pass |
| S3 fixtures/harness | real binary, static route, operator flags; backend-read values only | same | real gRPC listener/transparent handler | pass |
| S4 independence | C1 tests pass with C2/C3 unfixed (`miss_concept_clientip`, `miss_concept_grpc` flip only their own tests) | C2 test passes with C1/C3 unfixed (`miss_concept_connection`) | C3 tests pass with C1/C2 unfixed | pass |
| S5 history | `upstream_first_fix.patch` violates the property read literally: operator-designated names stay removable/substitutable (6 security fails) | same (T4 open) | same (T6 open) | pass |
| S6 contracts | product-visible flags and wire values only; no guessed field/function name | protected class named in product terms ("headers the proxy sets", "headers the operator designates to carry a trust value") | same; no authority/fallback interface | pass |
| S7 decisive tests | — | — | — | not fired |

**S1 detail — coupled values.** `TestFunc_PreservesClientRealIPWhenNotDesignated` (client
`X-Real-Ip`), `TestFunc_PreservesClientForwardedHost` (client host), `TestFunc_AppendsForwardedForChain`
(chain), `TestFunc_ConfiguredClientIPHeaderIsSet`, `TestFunc_RequestIDHeaderIsSet`,
`TestFunc_AppendsForwardedForChainWhenConfigured`, `TestFunc_GRPCCallAndOpaqueMetadata`. Each is
covered by KEEP; none is forbidden by SET read with its stated scope, and DESIG requires the
proxy's value rather than the removal of these values. No contradiction, so no gate-a failure.

**S2 detail — refused shapes.** Refused: a `Connection` token naming a proxy-set/designated header
(security tests); a client value for a designated header; a declared header on a second
`Connection` line; gRPC client values for designated metadata; a client transport assertion on an
unsecured connection. Each lies outside the legitimate set the keep-working clauses, examples and
fixtures describe; the legitimate split/upgrade and opaque-metadata shapes are accepted by the
functional tests.

**S3–S6.** Every state is legitimate (enabled static routes, operator designations, ordinary
clients). The harness drives the real binary's HTTP and gRPC listeners and reads what the backend
received, so any valid layer passes — `pass-alt.patch` places the guard in the dispatcher
(`http_proxy.go`) before `addHeaders`, and `pass-hardening.patch` in the header builder, both at
1.0. A guard placed after the reverse proxy has already stripped the value cannot restore it and is
not a valid layer. Refusal forms (error status, connection close, panic) cannot satisfy "the backend
must receive the proxy's value" and are caught by the functional/security tests. Each concept's
security tests fail on the pinned tree through its own route (nop: 11/11 security fail). H3b, so
H3c masking does not apply. `upstream_first_fix.patch` (A alone) violates DESIG read literally (the
operator-designated names are not protected), and `upstream_fix.patch` (A+B) still fails 4 security
tests. No dependency bump is involved. No test needs a field or function name the solver must guess.

**S7.** `build/stk-fabio-ghsafq95/trial_summary.md` does not exist, so S7 is not fired. The
build-level `trial_detail_deepseek.json` records three 2026-10-25 runs at reward 0.6364 (4 of 11
security tests failing in each); no single test decided a run, and the per-test names are outside
the restricted root.

## 5. Verdict

**Gate a — fairness: READY.** Every test is passed by the reference (oracle 21/21) and by guards at
other valid layers (`pass-alt`, `pass-hardening`); each security test is covered by a general clause
read literally — SET for the proxy-set values (T1), DESIG for operator-designated headers "on every
path" (T2/T3/T4/T6). No test demands an error class, a refusal form, or a guessed name. The only
reading risk is the opening sentence ("Whatever a backend may take as the proxy's own word…"): read
alone it would forbid the preserved client values, but SET is scoped, KEEP requires preservation,
and the repo pins it in a project test. No correct fix following the primary mechanism fails.

**Required: generalize** — none. The contract clauses state the property once over the protected
outcome; the impact example names no header, file or route.

**Quality to tighten** (non-blocking): add a lowercase-token declaration test (case-sensitive
matching); add a custom designated-name HTTP substitution test (`X-Real-Ip`-only special case); bind
the client to a second loopback address (constant/listener-derived address); assert exactly one
value on the HTTP derived headers (append-instead-of-replace); add a plaintext HTTP
`-proxy.header.tls` test and delete the client's assertion on the HTTP side (the reference's HTTP
fix filters only the declaration); keep `ff-single-line-parser` coverage where it is (only the
functional split-line websocket test catches it); neutralize the mechanism sentence in §3.

**Human review:** confirm that the opening Requirement sentence is framing for the scoped rule (so a
correct fix preserves undesignated client-supplied forwarding values) and that absence, not an empty
value, is the required proxy value for the plaintext transport assertion.

GATE_A: READY
NEEDS_HUMAN_REVIEW: YES
