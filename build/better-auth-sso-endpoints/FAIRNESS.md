# FAIRNESS review (round 3): better-auth-sso-endpoints

Reviewer: independent pre-trial agent, 2026-10-16. I did not write the tests. Inputs read:
instruction.md (401 words by wc), every file in tests/ (security/endpoint_contact.test.ts,
functional/provider_signin.test.ts, support/harness.ts, support/vitest.verifier.config.mjs,
test.sh, score.py), solution/fix.patch, manifest.json (patch_checks, traps, wrong_fix_catalogue),
notes.md (incl. "Second fairness round"), all nine checks/*.patch, task.toml,
environment/Dockerfile, the round-1 and round-2 reviews, and the gate logs in
gate_runs_2026-10-16_r2/. No Docker, trials, gates or upstream lookup. The only thing I ran was
`node -e` against the local Node 24 to print `net.connect` and `tls.connect`, to confirm the
socket-layer recorder sits on the path Node's fetch uses.

## 0. Round-2 requests: were they applied?

| # | Round-2 request | Status | Evidence |
|---|---|---|---|
| 1 | Replace the second "Required behaviour" bullet with the neutral wording (drop "Registering, updating and") | Done, word for word | instruction.md lines 33-37 |
| 2 | Move the outbound recorder to the socket layer so a guard that refuses before connecting cannot fail | Done. `ConnectRecorder` replaces `net.Socket.prototype.connect`. It handles both the internal `[options, cb]` array from `net.connect` and direct `(options)` / `(port, host)` calls, records the attempt, and reroutes it to the loopback InternalHost. In Node 24, `net.connect` ends in `socket.connect(normalized)` and `tls.connect` in `tlssock.connect(options, ...)`, so undici's plain and TLS connections both pass through the hook. Inside the container the hook does see vulnerable traffic: callback_discovery_path_only.patch fails all four recorder cases. | harness.ts:80-143; patches.report.json |
| 3 | Add a `0.0.0.0` case and a 192.168.x case | Done. `http://0.0.0.0:<InternalHost port>` uses the real listener. `192.168.1.20` goes through the recorder. loopback_only.patch now fails 4 tests (10.x, 192.168.x, metadata, 0.0.0.0), and callback_discovery_path_only fails 11 of 11, so both new cases are reached on near-vulnerable code in the container. The localhost case moved from port 9 to 8080 because port 9 is on the Fetch blocked-port list, which would have made that case pass on vulnerable code. | security tests at lines 230-246; patches.report.json |
| 4 | Fix the stale text ("5 attacks", test header) | Done. The manifest BASE note now reads "all 11 security tests". The security header (lines 1-14) describes InternalHost plus ConnectRecorder. The early "Tests" and "Verified locally" sections of notes.md still say 5. They are history, superseded by later sections, and hidden. | manifest.json, endpoint_contact.test.ts |

Gate logs for round 2: nop PASS, oracle x3 PASS, patches 9/9 PASS (each reward matches its
expectation). Static FAILS only on "no expect=pass patch with kind='blind'". That patch is owed
by an independent agent under rule 6. It is not a fairness defect, but the full gate cannot pass
until someone adds it.

## 1. Test-by-test fairness

Property sentence (P): "No provider configuration that a caller entitled to manage SSO can
supply through the public API may cause the server to send a request to a host the deployment
does not permit. A host is permitted only if it is publicly routable, or if its origin is listed
in `trustedOrigins`. Any other host must never be contacted on a provider's behalf: for example
a loopback, private-network, link-local or cloud instance-metadata address, however the address
is written."
Preservation sentence (K): "Legitimate SSO must keep working exactly as today: a provider whose
addresses are on origins listed in `trustedOrigins` (including an internal identity provider the
operator put there) keeps working end to end, over HTTP or HTTPS. A provider whose addresses are
on a publicly routable host is accepted."

All security tests assert only `hits === 0`, meaning no request or connection attempt to the
disallowed host. Rejection at registration, rejection at fetch time, a silent drop and a
pre-connect refusal all pass. In every security test the allow-listed IdP is
`http://127.0.0.1:<idp port>`, which shares its hostname with InternalHost. A hostname-based
allow-list therefore fails, which is fair because P says "origin".

| Test (file::name) | Asserts | Fair because | Could a correct fix fail it? | Risk |
|---|---|---|---|---|
| security::skip-discovery registration cannot point the token exchange at an internal host | InternalHost (127.0.0.1, other port, not trusted) gets 0 requests after register and full sign-in | P: loopback, origin not in trustedOrigins | No | low |
| security::...user-info fetch at an internal host | same, userInfoEndpoint | P | No | low |
| security::...key (jwks) fetch at an internal host | same, jwksEndpoint, no userInfoEndpoint | P | No | low |
| security::updating an existing provider cannot redirect a fetch to an internal host | legit provider, then tokenEndpoint updated to InternalHost, 0 hits | P ("No provider configuration ... through the public API" covers every management call) | No. A fix that refuses the update leaves the legit provider in place, and sign-in reaches only the trusted IdP | low |
| security::endpoints cannot target a private-network address | ConnectRecorder("10.0.0.5") sees 0 connect attempts | P: "private-network" | No. Socket-layer counting accepts guards placed before connecting | low |
| security::endpoints cannot target the cloud instance-metadata address | ConnectRecorder("169.254.169.254"), 0 | P: "link-local or cloud instance-metadata" | No | low |
| security::endpoints cannot target loopback written in short form | `http://127.1:<port>`, real InternalHost, 0 hits | P: "however the address is written". WHATWG URL normalises it to 127.0.0.1 | No | low |
| security::endpoints cannot target loopback by name | ConnectRecorder("localhost") on :8080, 0 | P: loopback, "however the address is written" | Only an exotic fix. One that never classifies the name and relies only on a custom `lookup` passed to the socket would make a `connect()` call that the hook counts before resolution. That design alone also misses every IP literal, because Node skips lookup for literals, so it would fail the 10.x, 192.168.x and metadata tests anyway. | low |
| security::endpoints cannot target another private-network range | ConnectRecorder("192.168.1.20"), 0 | P: "private-network" | No | low |
| security::endpoints cannot target the unspecified address | `http://0.0.0.0:<port>`, real InternalHost, 0 hits | P is an allow-list ("permitted only if publicly routable"). 0.0.0.0/8 is not routable (RFC 6890), and 0.0.0.0 is a standard SSRF bypass (expert knowledge) | No. isPublicRoutableHost, which the repo ships, rejects it (the oracle passes), and any allow-list fix rejects it | low |
| security::an explicit endpoint override cannot smuggle an internal host past discovery | discovery against the trusted IdP plus an explicit tokenEndpoint on InternalHost, 0 hits | P ("No provider configuration ...") | No. Refusing, ignoring the override or checking at fetch time all pass | low |
| functional::registers a skip-discovery provider on an allow-listed IdP and signs in | register ok, callback redirect contains /dashboard | K (trustedOrigins, over HTTP) | No | low |
| functional::registers a discovery-based provider on an allow-listed IdP and signs in | same, discovery mode | K | No | low |
| functional::updates a provider endpoint to another allow-listed value and still signs in | update ok, sign-in ok | K ("keep working exactly as today") | No | low |
| functional::accepts a provider whose endpoints are on a publicly routable host | register `https://8.8.8.8` skip-discovery, ok | K ("publicly routable host is accepted"). No DNS or network needed | Only a fix that probes reachability at registration, which nothing in the instruction asks for | low |
| functional::accepts an internal IdP whose origin the operator added to the allow-list | loopback IdP in trustedOrigins, register ok | K ("including an internal identity provider the operator put there") | No | low |

Scoring (score.py): 1.0 only if all 16 tests pass. Any functional failure gives 0. A skipped
test counts as a fail. An empty group counts as failed. test.sh copies the tests fresh from
/tests and kills the agent first. No issues.

## 2. Leniency

| Property / trap | Most plausible wrong fix | Caught? |
|---|---|---|
| BASE (stored skip-discovery endpoints bypass the runtime-discovery validator) | harden validateDiscoveryUrl / the discovery path only | Yes, 11 of 11 security tests fail (callback_discovery_path_only.patch, reward 0) |
| BASE, wrong field | validate discoveryEndpoint only | Yes, 11 of 11 (validate_discovery_field_only.patch) |
| T1 update route | fix registration only | Yes, the update test (miss_update.patch, 0.9091) |
| T2 override while discovery runs | validate only when skipDiscovery is set | Yes, the override test (skip_branch_only.patch, 0.9091) |
| host classes | loopback-only rule | Yes, the 10.x, 192.168.x, metadata and 0.0.0.0 tests (loopback_only.patch, 0.6364) |
| raw-string match | `href.includes("127.0.0.1")` / `hostname === "127.0.0.1"` | Yes, the 127.1, localhost and 0.0.0.0 tests |
| allow-list by hostname | match trustedOrigins on hostname, not origin | Yes, every InternalHost test (it shares 127.0.0.1 with the trusted IdP) |
| over-restriction | refuse all / ignore trustedOrigins | Yes, functional (disable_feature.patch; block_trusted_loopback.patch) |
| valid alternative layers | checks at fetch time; reference plus fetch-time | Pass 1.0 (alt_correct_fix.patch, hardening.patch), so both layers are accepted |

Wrong fixes no test catches (all low likelihood, because the repo already exports
`isPublicRoutableHost` and the reference uses it):
1. A hand-written deny-list that covers 127.0.0.1, localhost, 0.0.0.0, 10/8, 192.168/16 and
   169.254/16 but misses 172.16/12, 100.64/10, other 127/8 addresses, IPv6 (`[::1]`,
   `[fd00::]`, `[::ffff:127.0.0.1]`) or `metadata.google.internal`. Optional hardening: add a
   ConnectRecorder("::1") case with `http://[::1]:8080` (the hook already strips brackets), plus
   one 172.16.x case. Not blocking: round 2's main concern (0.0.0.0, 192.168) is now covered.
2. Prefix-style trusted-origin matching (`url.startsWith(origin)`, defeated by
   `http://127.0.0.1:P@10.0.0.5/`). Untested. Unlikely, since `ctx.context.isTrustedOrigin`
   exists.
3. An allowed endpoint that redirects (3xx) to an internal host. Untested, and the reference
   does not handle it either. This is IdP behaviour, not "provider configuration", so it is
   acceptable.
4. Hostnames that resolve via DNS to internal addresses. "However the address is written" could
   be read to cover them, but the reference does not resolve names and no test needs it.
   Solvers who go further still pass. Acceptable.
5. Providers stored before the fix. Untested and not claimed by the instruction. Acceptable.

## 3. Hints in instruction.md

Checked for leaks of the saved-provider path (storage, reload, skip-discovery, discovery bypass)
and of the update route. None found. A case-insensitive grep for
skip/discover/updat/stor/sav/reload/persist/token/jwks/userinfo/callback/endpoint/edit/exist/regist
matches only line 7 ("register") and the word "changes" in the Notes line ("source changes take
effect"). No manifest.leak_terms appear (isPublicRoutableHost, validateSkipDiscoveryEndpoints,
validateDiscoveryUrl, classifyHost, discovery_private_host, ssrf, server-side request forgery,
vaadata, 169.254.169.254). The instruction names no file or function, no flaw count and no fix
approach. task.toml does name the register and update routes, but the solver never sees it.

Remaining sentences, all acceptable:
- "A member with SSO-management rights can register such a provider and configure the addresses
  the server uses to talk to it." This is the attacker model every SSRF report needs. It names
  the obvious entry point, and says nothing about update, storage or the discovery branch. Keep.
  (Optional, cosmetic: "can set up such a provider, including the addresses ...".)
- "however the address is written" and the host-class list. These are property statements that
  make the 127.1, localhost, 10.x, 192.168.x and metadata tests fair. They read as "for example"
  under an allow-list rule, not as a list of spellings. Keep.
- "Fix the flaw in the library itself, for every way it can be reached, not only the example
  above." This is a slightly stronger nudge than BUILDER.md's standard block ("the attack and
  close variants"): it implies more than one route. Two other tasks use the same sentence, it
  names no route, and it makes the task easier rather than unfair. Optional: use the standard
  "Fix the library so that the reported behaviour and close variants of it no longer occur,
  while legitimate use keeps working." Low.
- `trustedOrigins` is a documented, user-facing option the functional tests depend on. Keep.

## 4. Realism

BASE, T1 and T2 are unmodified upstream code at 23094a62. The Dockerfile fetches that single
commit with depth 1, deletes .git, and makes one fresh "Initial commit", so no upstream history
or fix is in the image. Every case is reached through the real entry points
(`auth.api.registerSSOProvider` / `updateSSOProvider`, then `POST /sign-in/sso` and the real
`/sso/callback` via `auth.handler`) by an ordinary signed-in user, which is the plugin's default
authorisation. The new inputs (0.0.0.0, 192.168.1.20) are standard attacker payloads. The test
harness is instrumentation only: the recorder reroutes connections so nothing leaves the
machine, and it never changes the product code. Nothing looks planted or contrived.

## 5. Verdict: READY

Every round-2 request is applied and backed by gate evidence: nop, oracle x3 and patches 9/9
pass. The new tests fit the instruction. Correct fixes at configuration time, fetch time or
before connecting all pass, while each trap is isolated by its own check patch. No new text leaks
the saved-provider path or the update route.

Not blocking:
- Gate: the blind pass patch (kind='blind', expect=pass) is still owed, so `gate.py --only
  static` fails until an independent agent supplies it.
- Optional hardening: a `[::1]` ConnectRecorder case and a 172.16.x case (section 2, item 1).
- Optional wording: the standard constraint sentence in place of "for every way it can be
  reached" (section 3).
