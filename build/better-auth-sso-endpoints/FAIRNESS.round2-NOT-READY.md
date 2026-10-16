# FAIRNESS review (round 2): better-auth-sso-endpoints

Reviewer: independent pre-trial agent, 2026-10-16. I did not write the tests. Inputs read:
instruction.md (404 words), tests/ (security, functional, support/harness.ts,
support/vitest.verifier.config.mjs, test.sh, score.py), solution/fix.patch, manifest.json,
notes.md (incl. "Fairness round"), checks/*.patch, gate_report.partial.json (patches stage only),
and the round-1 review FAIRNESS.round1-NOT-READY.md. No Docker, trials, gates or upstream lookup.
The nop and oracle stages are reported in notes.md only; gate_report.partial.json holds just the
patches stage, so I could not confirm them from a gate file.

## 0. Round-1 required changes: were they applied?

| # | Round-1 requirement | Status |
|---|---|---|
| 1 | Instruction rewrites (remove edited-provider sentence, "Nothing rejected it", field and fetch-site lists, save-and-reload sentence, "refused cleanly / not stored", "carried over", "instead of relying on automatic metadata discovery"; "HTTPS" -> HTTP(S); "reachable on the public internet" -> "publicly routable"; keep trustedOrigins, the rule, host classes, preservation clause) | Done. All listed phrases are gone; "over HTTP or HTTPS" and "publicly routable" are in. The builder also dropped "now or earlier" from my proposed property sentence: correct, because pre-fix stored providers are not tested and the reference (write-time only) would not meet it. One residual hint remains in the preservation clause (see 3). |
| 2 | Public-host functional test must not need DNS | Done: https://8.8.8.8 (publicly routable, not TEST-NET). |
| 3 | Security cases for 10.x, 169.254.169.254 and an alternate loopback spelling, recorded without network, asserting only "no request" | Done: 10.0.0.5 and 169.254.169.254 and `localhost` via `FetchRecorder` (global fetch wrapper, synthetic 200); `127.1` against the real InternalHost listener. All assert `hits === 0` only. Issuer pinned to 127.0.0.1 so the `localhost` recorder cannot see legitimate IdP traffic; getAuthHeaders uses customFetchImpl, not global fetch, so it is not recorded either. |
| 4 | `skip_branch_only.patch` and a loopback-only patch | Done. Gate: skip_branch_only fails exactly the override test (0.8889); loopback_only fails exactly private + metadata (0.7778). alt_correct_fix (fetch-time layer) and hardening still 1.0, so the new tests accept both valid layers. |

## 1. Test-by-test fairness

| Test (file::name) | Asserts | Instruction sentence / expert knowledge making it fair | Could a correct fix fail it? | Risk |
|---|---|---|---|---|
| security::skip-discovery registration cannot point the token exchange at an internal host | InternalHost (127.0.0.1, other port, not trusted) gets 0 requests after register + sign-in | "No provider configuration ... may cause the server to send a request to a host the deployment does not permit ... permitted only if publicly routable, or if its origin is listed in trustedOrigins ... loopback" | No (origin, not hostname, is stated) | low |
| security::...user-info fetch at an internal host | same, userInfoEndpoint | same | No | low |
| security::...key (jwks) fetch at an internal host | same, jwksEndpoint, no userinfo | same | No | low |
| security::updating an existing provider cannot redirect a fetch to an internal host | update tokenEndpoint to InternalHost, 0 hits | "No provider configuration that a caller entitled to manage SSO can supply through the public API" (covers update) | No | low |
| security::endpoints cannot target a private-network address | no global-fetch call to 10.0.0.5 | "private-network ... address" | Maybe: a fix that refuses only at socket-connect time (custom undici dispatcher / agent that checks the IP before connecting) still calls `fetch()`, which the recorder counts as a hit. Valid per the instruction ("never be contacted"), but unusual for a library and must still honour trustedOrigins by origin | low-medium |
| security::endpoints cannot target the cloud instance-metadata address | no fetch to 169.254.169.254 | "link-local or cloud instance-metadata address" | Maybe: same connect-time case | low-medium |
| security::endpoints cannot target loopback written in short form | `http://127.1:<port>`, real InternalHost, 0 hits | "however the address is written" | No (WHATWG URL normalises 127.1 to 127.0.0.1; a connect-time fix also passes since the listener is real) | low |
| security::endpoints cannot target loopback by name | no fetch to `localhost:9` | "loopback ... however the address is written" | Maybe: same connect-time case; a DNS-resolving check works offline for `localhost` | low-medium |
| security::an explicit endpoint override cannot smuggle an internal host past discovery | discovery on trusted IdP + tokenEndpoint on InternalHost, 0 hits | same property sentence ("No provider configuration ...") | No | low |
| functional::registers a skip-discovery provider on an allow-listed IdP and signs in | ok + redirect to /dashboard | "Registering ... and signing in through a provider whose addresses are on origins listed in trustedOrigins ... over HTTP or HTTPS" | No | low |
| functional::registers a discovery-based provider on an allow-listed IdP and signs in | same, discovery mode | same | No | low |
| functional::updates a provider endpoint to another allow-listed value and still signs in | update ok + sign-in ok | "Legitimate SSO must keep working exactly as today" (update is an existing feature); currently also "updating" (see 3) | No | low |
| functional::accepts a provider whose endpoints are on a publicly routable host | register https://8.8.8.8 ok | "A provider whose addresses are on a publicly routable host is accepted" | No (IP literal, no DNS) | low |
| functional::accepts an internal IdP whose origin the operator added to the allow-list | register trusted loopback IdP ok | "(including an internal identity provider the operator put there)" | No | low |

Scoring: 1.0 only with all 14 passing; any functional failure gives 0. Fine.

The low-medium items share one cause: `FetchRecorder` intercepts at the `fetch()` call, above
any network-layer guard. Recommended (not required): record at the socket layer instead (wrap
`net.connect` / `tls.connect` or use a `net.Socket.prototype.connect` hook, record attempts to
the target host and fail them), so a guard that refuses before connecting passes while vulnerable
code is still recorded. Unverified that Node's bundled undici picks up such a patch; verify on
nop and oracle before switching.

## 2. Leniency

| Property / trap | Most plausible wrong fix | Caught? |
|---|---|---|
| BASE (stored skip-discovery endpoints bypass the discovery validator) | harden validateDiscoveryUrl / runtime-discovery path only | yes, 9/9 security (callback_discovery_path_only.patch) |
| BASE, wrong field | validate discoveryEndpoint only | yes, 9/9 (validate_discovery_field_only.patch) |
| T1 update route | registration only | yes, update test (miss_update.patch) |
| T2 override while discovery runs | validate only when skipDiscovery | yes, override test (skip_branch_only.patch) |
| host classes | loopback-only rule | yes, private + metadata tests (loopback_only.patch) |
| raw-string match | `href.includes("127.0.0.1")` | yes, 127.1 and localhost tests |
| allow-list by hostname | trustedOrigins matched on hostname | yes, every InternalHost test (shares 127.0.0.1 with the IdP) |
| over-restriction | refuse all / ignore trustedOrigins | yes, functional (disable_feature, block_trusted_loopback) |

Wrong fixes no test catches:
1. A hand-written deny-list on the parsed hostname that covers 127.0.0.1, localhost, 10/8 and
   169.254/16 but misses other forms: `0.0.0.0` (reaches local listeners on Linux), other
   127/8 addresses (127.0.0.2), `[::1]`, `[::ffff:127.0.0.1]`, 192.168/16, 172.16/12,
   `metadata.google.internal`. The repo already ships `isPublicRoutableHost`, so most fixes
   will use it, but this is the remaining gap. Recommended: add `http://0.0.0.0:<InternalHost
   port>` (real listener; verify it connects in the container) and one 192.168.x recorder case.
2. Prefix-style trusted-origin matching (`url.startsWith(origin)`, defeated by
   `http://127.0.0.1:P@10.0.0.5/`). Untested; low likelihood since `ctx.context.isTrustedOrigin`
   exists.
3. Redirect from an allowed endpoint to an internal host: not tested, not required by the
   reference. Acceptable.
4. Providers stored before the fix: not tested and no longer claimed by the instruction.
   Acceptable.

## 3. Hints in instruction.md

Impact is now told through sign-in only: the title, "What we observed" ("During a sign-in
through a provider ... our server sent requests to a service bound to loopback ... and used the
responses in the sign-in") and the property ("No provider configuration that a caller entitled
to manage SSO can supply through the public API ...") never mention saving, storing, reloading,
field names, fetch steps or the discovery branch. That meets DeepSeek shape 2.

Remaining items:
- "Registering, updating and signing in through a provider whose addresses are on origins
  listed in `trustedOrigins` ... keeps working" - names both producer routes, and "updating"
  paraphrases trap T1 (the route round 1 removed from the observation section). Neutral:
  "Legitimate SSO must keep working exactly as today: a provider whose addresses are on
  origins listed in `trustedOrigins` (including an internal identity provider the operator put
  there) keeps working end to end, over HTTP or HTTPS. A provider whose addresses are on a
  publicly routable host is accepted." The functional update test stays fair through "keep
  working exactly as today".
- "A member with SSO-management rights can register such a provider and configure the
  addresses the server uses to talk to it." Names registration, but it is the attacker model
  every SSRF report needs and says nothing about saving or reload. Acceptable. Optional
  softer form: "... can set up such a provider, including the addresses the server uses to
  talk to it."
- "however the address is written" and the host-class list are property statements that make
  the 127.1 / localhost / 10.x / metadata tests fair; keep.
- `trustedOrigins` is a documented option the functional tests need; keep.
- No leak_terms (isPublicRoutableHost, validateSkipDiscoveryEndpoints, 169.254.169.254, ssrf,
  ...) appear in the instruction. No flaw count, file or function names.

## 4. Realism

Unchanged from round 1: BASE, T1 and T2 are unmodified upstream code at 23094a62, reachable
through registerSSOProvider / updateSSOProvider and the real /sso/callback flow, driven via
`auth.api.*` and `auth.handler` with an ordinary signed-in user (the plugin's default
authorisation). The new cases use real attacker inputs (private IP, metadata IP, short loopback,
`localhost`) through the same entry points. Nothing planted or contrived. Stale text only:
manifest BASE note says "all 5 attacks" (now 9), and the security test header says every test
uses an InternalHost; both are hidden and harmless, fix at leisure.

## 5. Verdict: NOT READY (one instruction edit)

Required:
1. instruction.md: replace the second "Required behaviour" bullet with the neutral wording in
   section 3 (drop "Registering, updating and"). Tests unchanged; re-run `gate.py --only static`.

Recommended (not blocking):
- Move FetchRecorder to the socket layer (section 1) so a connect-time guard cannot be failed.
- Add a `0.0.0.0` InternalHost case and a 192.168.x recorder case (section 2, item 1), with a
  check patch for a narrow deny-list; re-run patches.
- Refresh the stale "5 attacks" text in manifest.json and the security test header comment.
