# FAIRNESS review: better-auth-sso-endpoints

Reviewer: independent pre-trial agent, 2026-10-16. I did not write the tests. Inputs read:
instruction.md (584 words), tests/ (security, functional, support, test.sh, score.py),
solution/fix.patch, manifest.json, notes.md, checks/*.patch. I also read the vulnerable tree at
23094a62 (sparse checkout of packages/sso, packages/core/src/utils, docs sso.mdx) to confirm the
existing behaviour. I did not look at the upstream fix online. I ran no Docker, trials or gates.

Facts used below (vulnerable tree):
- `@better-auth/core/utils/host` already exports `isPublicRoutableHost`/`classifyHost`
  (static classification, no DNS: an FQDN is "public" unless localhost/*.localhost/metadata names).
- The discovery path (`validateDiscoveryUrl`, `normalizeDiscoveryUrls`) already requires the
  discovery URL and every discovered URL to be in `trustedOrigins` (strict, no public exception).
  docs/plugins/sso.mdx documents this. `discoverOIDCConfig` lets a caller-supplied
  `existingConfig.*Endpoint` win over the discovered value without any check (trap T2 is real).

## 1. Test-by-test fairness

| Test (file::name) | Asserts | Instruction sentence / expert knowledge making it fair | Could a correct fix fail it? | Risk |
|---|---|---|---|---|
| security/endpoint_contact::skip-discovery registration cannot point the token exchange at an internal host | after register + full sign-in, the loopback `InternalHost` (127.0.0.1, not in trustedOrigins, different port from the trusted IdP) got 0 requests | "A supplied endpoint URL is permitted only if its host is reachable on the public internet, or its origin is one the operator has allow-listed; any other host ... loopback ... must be refused. This holds for every endpoint the server later contacts" | No. A fix matching trustedOrigins by hostname instead of origin would fail (same 127.0.0.1), but the instruction says "origin" | low |
| security/endpoint_contact::...user-info fetch at an internal host | same, userInfoEndpoint internal | same sentence ("every endpoint the server later contacts") | No | low |
| security/endpoint_contact::...key (jwks) fetch at an internal host | same, jwksEndpoint internal, no userinfo | same | No | low |
| security/endpoint_contact::updating an existing provider cannot redirect a fetch to an internal host | register legit, update tokenEndpoint to internal, sign in, 0 hits | "No sequence of provider registration or update ..."; "The same happened when an existing provider was edited" | No (fair; over-hinted, see 3) | low |
| security/endpoint_contact::an explicit endpoint override cannot smuggle an internal host past discovery | discovery on trusted IdP + supplied tokenEndpoint internal, 0 hits | "every way an endpoint value can be supplied or carried over" | No | low |
| functional/provider_signin::registers a skip-discovery provider on an allow-listed IdP and signs in | register ok, sign-in redirects to /dashboard | "Registration, update and full sign-in against a provider whose endpoints are on allow-listed origins ... continue to succeed" | Maybe: a fix that also enforces https (the instruction says the server makes "outbound HTTPS requests") rejects the http://127.0.0.1 trusted IdP | medium |
| functional/provider_signin::registers a discovery-based provider on an allow-listed IdP and signs in | same, discovery mode | same sentence | Maybe: same https point | low-medium |
| functional/provider_signin::updates a provider endpoint to another allow-listed value and still signs in | update ok, sign-in ok | same sentence | Maybe: same https point | low-medium |
| functional/provider_signin::accepts a provider whose endpoints are on a publicly routable host | register with https://idp.example.com/* (not in trustedOrigins), skipDiscovery, ok | "a provider on an ordinary public host is accepted"; "its host is reachable on the public internet" | Maybe: a DNS-resolving check (standard SSRF practice: resolve, then reject private answers) fails closed because the verifier has no network ("There is no network access"), so idp.example.com does not resolve. "reachable on the public internet" invites exactly that check | medium |
| functional/provider_signin::accepts an internal IdP whose origin the operator added to the allow-list | register loopback trusted IdP, ok | "or its origin is one the operator has allow-listed"; "(including an internal identity provider the operator put on the allow-list)" | No | low |

Scoring (score.py): 1.0 only if all 10 pass; any functional failure gives 0. Fine.
Contract check: the security tests assert only "no outbound contact", so a write-time refusal and
a fetch-time refusal both pass (alt_correct_fix.patch proves the latter). Good.

## 2. Leniency

| Property / trap | Most plausible wrong fix | Caught? |
|---|---|---|
| BASE (stored skip-discovery endpoints bypass the discovery validator) | harden `validateDiscoveryUrl` only | yes, all 5 security tests (callback_discovery_path_only.patch) |
| BASE, wrong field | validate `discoveryEndpoint` only | yes, 5 security tests (validate_discovery_field_only.patch) |
| T1 update route | fix registration only | yes, `updating an existing provider` (miss_update.patch) |
| T2 override when discovery runs | validate the endpoints only when skipDiscovery is true | yes, `explicit endpoint override`; but no check patch isolates it (the two patches above fail all 5). Add `skip_branch_only.patch` (expect security_fail, 1 test) |
| over-restriction | refuse all OIDC / ignore trustedOrigins | yes, functional (disable_feature.patch, block_trusted_loopback.patch) |
| allow-list by host not origin | match trustedOrigins on hostname | yes, every security test (InternalHost shares 127.0.0.1) |

Wrong fixes NO test catches:
1. **Loopback-only check** (reject 127/8, ::1, localhost; allow 10/8, 172.16/12, 192.168/16,
   169.254/16 incl. 169.254.169.254, metadata.google.internal). Every security test uses only
   127.0.0.1, yet the instruction's own example includes the cloud metadata address. This is the
   largest leniency gap.
2. **Raw-string checks** (e.g. `url.includes("127.0.0.1")`) on the unparsed value: untested
   spellings (`http://localhost:P`, `http://127.1:P`, `http://2130706433:P`, `[::ffff:127.0.0.1]`).
   The instruction requires "independent of how the URL is spelled"; nothing tests it.
3. Redirect-following from an allowed endpoint to an internal one: not tested and not required by
   the reference either; acceptable to leave out.

## 3. Hints in instruction.md

DeepSeek shape 2 check (BRIEF-trap-stack.md: describe impact through the check's path only, state
the property abstractly, never name the producer or the reload path). **The instruction fails it.**
It names both the producer (registration/update) and the save-and-reload path:

- "supply the provider's own endpoint URLs directly — the authorization endpoint, the token
  endpoint, the user-info endpoint and the key (JWKS) endpoint. These are saved with the provider.
  Later, when someone signs in through that provider, the server itself makes outbound HTTPS
  requests to some of those saved endpoints to complete the exchange (swap the authorization code
  for tokens, verify the token, read the user profile)" - names the reload path, lists the four
  fields and the three fetch sites (= the three tested variants), and says "HTTPS" (see 1).
  Neutral: "An SSO manager can register an external OIDC provider and configure the addresses the
  server uses to talk to it. When someone signs in through that provider, the server contacts the
  provider and uses what it returns in the sign-in."
- "registered a provider and set one of its endpoint URLs to an address on our internal network
  ... Nothing rejected it." - points at registration as the missing check (the producer).
  Neutral: "During a sign-in through a provider configured by a member with SSO-management rights,
  our server sent requests to a service bound to loopback (in another case, to the cloud
  instance-metadata address) and used the responses in the sign-in."
- "The same happened when an existing provider was edited to move an endpoint onto such an
  address." - names trap T1 outright. Remove.
- "No sequence of provider registration or update, performed through the public management API"
  - names the routes. Neutral: "No provider configuration that a caller entitled to manage SSO can
  supply through the public API, now or earlier, may cause the server to send a request to a host
  the deployment does not permit."
- "for every way an endpoint value can be supplied or carried over" - "carried over" paraphrases
  the merge/override routes (T1, T2). Neutral: "for every request the server makes on a
  provider's behalf".
- "A rejected value is refused cleanly: the request fails with a client error and no provider
  capable of causing the forbidden request is left stored." - points at the write path (storage)
  and is untested (alt_correct_fix keeps the provider stored and scores 1.0). Remove.
- "instead of relying on automatic metadata discovery" - points at the skip-discovery branch.
  Remove (the neutral system sentence above covers the feature).
- "(the same allow-list the library already uses elsewhere)" - mild pointer to the existing
  discovery-path check. Optional removal; keep `trustedOrigins` itself (documented user-facing
  option; the functional tests need it, so naming it is required and fair).
- "reachable on the public internet" - replace with "publicly routable" (see 1).

Note on the shape: alt_correct_fix shows a fix placed at the fetch sites (the "check") is correct,
so even with a clean instruction the BASE trap only catches a model that hardens the existing
discovery validator, not every model that stays on the check's path. That is a design limit, not
a fairness problem.

Word count: 584. With the cuts above it should land near 350-400, in line with BUILDER.md 3i.

## 4. Realism

All three traps are unmodified upstream code at 23094a62 (source = mined, nothing planted),
reachable through the real `registerSSOProvider` / `updateSSOProvider` endpoints and the real
`/sso/callback` flow. The tests call `auth.api.*` (same handlers as HTTP) with a session of an
ordinary signed-in user, which matches the plugin's default authorisation. Nothing looks
contrived. The new public-or-allow-listed rule is a deliberate departure from the documented
discovery rule (strictly trustedOrigins); the instruction states it explicitly, so it is fair.

## 5. Verdict: NOT READY

Required changes:
1. Instruction: apply the rewrites in section 3 (remove the update sentence, the "Nothing
   rejected it" framing, the field and fetch-site lists, the save-and-reload sentence, the
   "refused cleanly / not stored" bullet, "carried over", "instead of relying on automatic
   metadata discovery"); keep `trustedOrigins`, the public-or-allow-listed rule, the example host
   classes, and the preservation clause. Replace "HTTPS" with nothing or "HTTP(S)" and
   "reachable on the public internet" with "publicly routable".
2. Tests: in `accepts a provider whose endpoints are on a publicly routable host`, use a public
   IP literal (e.g. 8.8.8.8 or 1.1.1.1; not a TEST-NET range, which is reserved) instead of
   idp.example.com, so a DNS-resolving fix is not failed by the offline verifier; or add one
   instruction sentence saying the deployment may have no outbound DNS.
3. Tests (tighten): add security cases for a private (10.x), link-local/metadata
   (169.254.169.254) and an alternate loopback spelling (`localhost` or `127.1`). The first two
   cannot be served, so record outbound requests in the harness (wrap global `fetch` / an undici
   dispatcher) and assert none targets the host. Assert only "no request", so write-time and
   fetch-time fixes both still pass.
4. Add `checks/skip_branch_only.patch` (expect security_fail on the override test only) and a
   loopback-only patch (expect security_fail once 3 is in).
Then re-run the gate.
