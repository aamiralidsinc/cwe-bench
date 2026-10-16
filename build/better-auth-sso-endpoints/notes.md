# better-auth-sso-endpoints build notes

- Start: 2026-10-16T15:32:12Z
- End (build authored): 2026-10-16T16:05Z (gate stages run after)

## Candidate
GHSA-5rr4-8452-hf4v, @better-auth/sso. Vulnerable parent
23094a628f007f801be6d26e5b15dc5fc6fc4eb8, fix 37f60cb176cb53147da7dfd5ec15afa5b486e81e.
CWE-918 SSRF via unvalidated OIDC provider endpoint URLs saved at registration/update
and fetched server-side at the OIDC callback.

## Step 1 — shape confirmed (Hadi "data producer off the check's path")
- CHECK the report points at: the callback's server-side fetches of the stored endpoints
  (packages/sso/src/routes/sso.ts callback: validateAuthorizationCode -> tokenEndpoint,
  betterFetch -> userInfoEndpoint, validateToken -> jwksEndpoint).
- DATA PRODUCER off that path: the registration handler (sso.ts registerSSOProvider ->
  buildOIDCConfig, JSON.stringify) and the update handler (providers.ts updateSSOProvider ->
  mergeOIDCConfig) persist the endpoints; they reach the fetch via save-and-reload
  (safeJsonParse at callback). The check does not call the producer.
- The only pre-existing endpoint validation (discovery.ts validateDiscoveryUrl /
  normalizeDiscoveryUrls) sits on the runtime-discovery path. Stored skip-discovery providers
  skip it: needsRuntimeDiscovery() returns false once token+jwks+auth are present, so
  ensureRuntimeDiscovery() returns early and the raw endpoints flow straight to the fetches.
  A fix placed on the discovery/fetch path therefore leaves the stored-data path open —
  demonstrated by callback_discovery_path_only.patch (0/5 security).

## Traps (all REAL pre-existing gaps; source = mined, nothing planted)
- BASE: data producer off the check's path (DeepSeek). Covered by token/userinfo/jwks tests.
- T1 (MiMo): the update-provider route merges endpoints into the stored config in a different
  file (providers.ts) and reaches the same sink; miss_update.patch leaves it open.
- T2 (MiMo): with discovery enabled, a user-supplied endpoint overrides the discovered value
  and is stored unvalidated; the discovery URL (visible binding) is checked but the override
  beside it is not. Covered by the "explicit endpoint override" security test.

## Tests
- Behavioural, loopback-only. A legitimate OIDC IdP (oauth2-mock-server) runs on loopback and
  its origin is placed in trustedOrigins. An InternalHost loopback listener (NOT in
  trustedOrigins) stands in for internal infrastructure and records every request it receives.
- Security (5): register/update a provider so one endpoint points at the InternalHost, drive a
  full sign-in, assert internal.hits === 0 (no outbound contact). On vulnerable code the server
  contacts it (attack succeeds -> test fails); on any correct fix it never does.
- Functional (5): legitimate skip-discovery sign-in, discovery-based sign-in, update + sign-in,
  acceptance of a public-host provider, and the trustedOrigins escape hatch for an internal IdP.

## Verified locally (node 24, pnpm 10.30.2, vitest 4.1.5, offline after install)
- Repo's own sso suite on the vulnerable commit: 22/22 pass (src/oidc.test.ts).
- vulnerable: security 0/5, functional 5/5.
- reference fix (solution/fix.patch): security 5/5, functional 5/5.
- Check patches (each run against the suite):
  - callback_discovery_path_only.patch  -> 5 security fail, functional pass (security_fail) [BASE]
  - validate_discovery_field_only.patch -> 5 security fail, functional pass (security_fail) [wrong_resource]
  - miss_update.patch                    -> 1 security fail (update), functional pass (security_fail) [unlisted_route]
  - disable_feature.patch                -> 5 functional fail (functional_fail) [refuse_all]
  - block_trusted_loopback.patch         -> 1 functional fail (discovery) + 4 security fail (functional_fail) [adjacent_api]
  - alt_correct_fix.patch (callback layer)-> 10/10 pass (pass)
  - hardening.patch                       -> 10/10 pass (pass, hardening)

## Not done here (left to independent agents, per BRIEF rule 6)
- The blind pass patch and build/<slug>/FAIRNESS.md. `gate.py --only static` will report both
  as problems; that is expected. No DeepSeek/MiMo trials were run.

## Fairness notes I can see myself
- The trustedOrigins escape hatch is a documented, user-facing option and is stated in the
  instruction, so the functional tests that rely on it are fair. The security property
  ("publicly routable or operator-allow-listed, else refuse") is standard SSRF expert
  knowledge and is stated as an invariant without naming the producer or the reload path.
- The behavioural assertion is "no outbound contact", not an exact status, so any correct
  fix at either the write or the fetch layer passes (alt_correct_fix proves it).

## Fairness round (2026-10-16, after FAIRNESS.md: NOT READY)
- Instruction rewritten per FAIRNESS.md section 3: impact told only through sign-in; removed
  the saving/reload sentences, field and fetch-step lists, the edited-provider sentence,
  "sequence of registration or update", "carried over", "instead of discovery", and the
  untested "refused cleanly / not stored" bullet. "publicly routable"; "HTTP or HTTPS".
  Also dropped the reviewer's "now or earlier": providers stored before the fix are not
  tested and the reference would not meet that clause. 404 words (wc, with markdown).
- Public-host functional test now uses https://8.8.8.8 (no DNS needed).
- Security cases added: 10.0.0.5, 169.254.169.254, http://127.1:<port>, http://localhost:9.
  Hosts that cannot be served are captured by a global-fetch recorder (tests/support
  FetchRecorder) that answers with a synthetic 200; assertions are only "no request".
- Harness fix: oauth2-mock-server names a loopback issuer "localhost"; the issuer is pinned to
  http://127.0.0.1:<port> so it cannot collide with the localhost case.
- New checks: skip_branch_only.patch (isolates T2), loopback_only.patch (private + metadata).
- Gate: static (only the blind patch missing), nop, oracle x3, patches (9/9) all PASS.

## Second fairness round (2026-10-16)
- Preservation bullet replaced with the reviewer's wording (instruction 401 words by wc).
- FetchRecorder replaced by ConnectRecorder: hooks net.Socket.prototype.connect (used by
  Node's fetch/undici, plain and TLS), records the attempt and reroutes it to the loopback
  InternalHost. A fix that refuses before connecting therefore passes.
- Added 192.168.1.20 (recorder) and http://0.0.0.0:<port> (real listener) cases. In the
  container, 0.0.0.0 connects on the vulnerable code and every recorder case records the
  attempt: vulnerable 0/11 security (all 11 fail on the assertion), reference 11/11, 5/5.
- localhost case moved from port 9 to 8080: port 9 is on the Fetch spec's blocked-port list,
  so fetch refuses it before any connection (it passed vulnerable code under the socket hook).
- Stale counts in manifest.json and the security test header comment refreshed.
- 17:05Z (lead): trials started in parallel with the full strict gate; they count only if that gate prints PASSED.
