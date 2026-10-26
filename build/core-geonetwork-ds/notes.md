# core-geonetwork-ds — build notes

Start (UTC): 2026-10-24T05:19:44Z (pipeline start). Verification work started 05:2x.

Advisory: GHSA-PJP7-Q6WP-97QX / CVE-2026-53573 — GeoNetwork post-login redirect
(CWE-601). Pinned: 6c756c63cd1fa942f3832d99c64380c69c5e8be9 (verified = parent of
cde9b6481a29e2473b7b74479b4e3fd6843bac4e; 0d74f67 is the identical 4.2.x backport).
Published fix source: logout success handler, new saved-request success handler, new
shared redirect helper, Keycloak + OIDC login filters, core security XML.

## Security property (stated once, applies to every route)

No value that arrives with a request may cause the application to send the browser to an
address that is not on the configured site. A destination is on-site when it is a path on
the site, or an absolute address with the site's protocol/host/port (default port may be
omitted). Off-site destinations must never be used: refuse (client error) or fall back to
a safe configured destination.

## Levers (each with a different reason to dismiss)

1. **SSO login filters (reported site; how-type: parser differential).**
   `KeycloakAuthenticationProcessingFilter` (core/.../keycloak/, `successfulAuthentication`
   no-request-cache branch) and `GeonetworkOAuth2LoginAuthenticationFilter`
   (core/.../openidconnect/) gate on `java.net.URI.isAbsolute()`. A protocol-relative
   `//host` is not absolute, so it is forwarded. Dismissal: "the filter already checks
   isAbsolute()".
2. **Core sign-out success handler (Pattern A far site; shape trap).**
   `jeeves/config/springutil/JeevesNodeAwareLogoutSuccessHandler#determineTargetUrl` uses
   `startsWith("/")` as the whole same-site test; `//host` and `/\host` pass. Dismissal:
   "the reported issue is the SSO filters; sign-out is not login; a relative check exists".
3. **Form-login success handler wired only in XML (Pattern A far site).**
   `config-security-core.xml` wires stock Spring
   `SavedRequestAwareAuthenticationSuccessHandler` with `targetUrlParameter=redirectUrl`
   and no validation. Dismissal: "a framework class, not GeoNetwork code".
4. **CAS sign-out handler (real upstream uncovered route; how-type: protection never
   existed).** `org/fao/geonet/web/RedirectLogoutSuccessHandler` returns the raw
   `redirect` request parameter with no validation. Dismissal: "CAS is an optional
   profile with a different parameter name, and its default target is already an external
   CAS URL, so external redirects are intended". Real, unmodified upstream code; the
   published fix never touches it.
5. **Coupled must-keep-working value (how-type).** The UI posts/links
   `redirectUrl=window.location.href` (absolute same-site) for both sign-in
   (`web-ui/.../menu-signin.html`) and sign-out (`CatController.js`). A relative-only
   check breaks return-to-page. Tests keep absolute same-site destinations working on
   sign-out and form login.
6. **Injected: Shibboleth pre-auth filter.** Added a `redirectUrl` branch mirroring the
   Keycloak no-cache branch (the filter already has the same saved-request structure).
   Dismissal: "optional legacy header-based profile, unrelated to the reported SSO flow".
7. **Injected: Keycloak logout success handler.** Added `redirectUrl` support as the
   post-logout destination substituted into the IDP logout placeholder (parity with the
   core sign-out handler). Dismissal: "the IDP logout URL is external by design, so the
   destination inside it looks like the IDP's business".
8. **Injected: ECAS profile config.** CAS filter success handler switched to
   `targetUrlParameter=redirectUrl` with the stock Spring class (copy of the core
   login wiring). Dismissal: "separate CAS/ECAS deployment profile in another config
   file; the default-target-only wiring looks deliberate".

Injected siblings are placed only where the upstream fix never touches (Shibboleth
filter, Keycloak logout handler, ECAS XML).

## Full candidate list (screener O8/O8b + own search)

Real sinks accepting a request-supplied destination:
1. JeevesNodeAwareLogoutSuccessHandler (core sign-out) — chosen, lever 2.
2. KeycloakAuthenticationProcessingFilter (no-cache login branch) — chosen, lever 1.
3. GeonetworkOAuth2LoginAuthenticationFilter — chosen, lever 1.
4. stock SavedRequestAwareAuthenticationSuccessHandler for form login — chosen, lever 3.
5. RedirectLogoutSuccessHandler (CAS sign-out, `redirect`) — chosen, lever 4.
6. KeycloakLogoutSuccessHandler (no parameter today) — inject, lever 7.
7. ShibbolethPreAuthFilter (saved request only today) — inject, lever 6.
8. ECAS stock success handler (`alwaysUseDefaultTargetUrl`) — inject, lever 8.
Dismissed candidates:
9. JeevesNodeAwareRedirectStrategy — receives server-chosen URLs, not a request destination.
10. LocaleRedirects — target built from configuration/locale; `referer` only becomes a query value.
11. GeoNetworkPortalFilter — always `contextPath + rewrittenPath`, same-origin.
12. Keycloak/OIDC pre-auth-action login filters — build `redirectUrl` from the request URI
    (path only), not an accepted destination.
13. Keycloak/Shibboleth saved-request branches — `DefaultSavedRequest` is built from the
    request host/port; the URL is same-origin and server-cached.
14. LogosApi / AtomGetData / datahub-integration — server-derived URLs (screener already
    noted out of scope).

Why the injected picks beat the rest: 6 and 7 require understanding how the destination is
consumed (mirrored branch / embedded, URL-encoded IDP parameter), and 8 is a config-only
site in a different security profile; all three are far from the reported SSO login code
and from each other, and each has a distinct dismissal. The dismissed candidates do not
take a request-supplied destination at all, so the property does not cover them.

## Verified on the pinned commit (real entry points, mocked servlet objects)

* keycloak `successfulAuthentication`, query `redirectUrl=//attacker.invalid/x` ->
  sendRedirect("//attacker.invalid/x")
* oidc `successfulAuthentication`, same -> sendRedirect("//attacker.invalid/x")
* logout `onLogoutSuccess`, param `//attacker.invalid/x`, root context ->
  sendRedirect("//attacker.invalid/x")
* form-login configured success handler (parsed from config-security-core.xml)
  `onAuthenticationSuccess`, `//attacker.invalid/x` -> sendRedirect same
* CAS configured handler (config-security-cas.xml) `onLogoutSuccess`,
  `redirect=https://attacker.invalid/phish` -> sendRedirect same
* injected Shibboleth `doFilter`, `//attacker.invalid/x` -> sendRedirect same
* injected Keycloak logout `onLogoutSuccess`, `redirectUrl=https://attacker.invalid/phish`
  -> Location `https://idp.example.com/logout?redirect=https%3A%2F%2Fattacker.invalid%2Fphish`
* injected ECAS configured handler `onAuthenticationSuccess`, `//attacker.invalid/x` ->
  sendRedirect same

Note: Java `java.net.URI` rejects backslashes, so the SSO/Shibboleth filters are only
bypassed by protocol-relative `//`; the sign-out and form/CAS/ECAS handlers accept `/\`
as a shape (browsers normalise it) and are tested for it. Root context is used for the
sign-out/form/CAS cases because `DefaultRedirectStrategy` prefixes a non-empty context
path; a root deployment is a supported configuration.

## Build facts verified

* `mvn -pl core -am -DskipTests install` on JDK 17 (Maven 3.9) builds 13 modules in ~4 min
  online; .m2 ~300 MB.
* Offline reuse needs `_remote.repositories`/`*.lastUpdated` stripped after warming, and a
  real test run to fetch the surefire JUnit4 provider.
* Hidden tests are compiled and run with `mvn -o -pl core test -Dtest=...`; Mockito-inline,
  spring-test and JUnit 4 are core test dependencies.

## Local suite verification (JDK 17, Maven offline, `-Dsystem.numCores=1`)

* Oracle tree: security 16/16, functional 19/19, 35 tests pass.
* Injected vulnerable tree (nop): all 16 security tests fail, all 19 functional
  tests pass.
* Wrong-fix variants (fresh injected tree per variant):
  - alt_correct_fix: 35/35 pass (independent helper implementation).
  - hardening: 35/35 pass (stricter control-character/userinfo rejection).
  - fix_sso_parser: 2 security failures (Keycloak + OIDC).
  - fix_logout_only: 2 security failures (sign-out).
  - fix_form_wiring: 3 security failures (form sign-in).
  - fix_cas_route: 3 security failures (CAS).
  - fix_shibboleth_missing: 1 security failure.
  - fix_keycloak_logout_missing: 3 security failures.
  - fix_ecas_missing: 2 security failures.
  - fix_published_only: 9 security failures (CAS + all injected siblings).
  - fix_uri_parser_only: 8 security failures (URI-only parser mismatch).
  - overbroad_relative_only: 4 functional failures (absolute same-site broken).
  - overbroad_refuse_all: 11 functional failures (relative return-to-page broken).
  - crash_as_refusal: refused destinations throw an unchecked exception instead of
    a clean refusal (security tests error; functional tests keep working) — validated
    by the same file-level reasoning and re-checked by the gate.

## Not verified / open

* Root-context deployment assumption for lever 2/3/CAS tests (product supports it; the
  SSO sites, the advisory's subject, are exploitable under any context path).
* Whether a solver could fix at a wholly different layer (a global servlet filter); tests
  drive the product's real handlers, which is where the upstream fix lives.
* `present_in_latest` for the CAS route: not checked against a newer release.

## Docker / gate log

- Environment image (`maven:3.9-eclipse-temurin-17`, injected tree, Maven warm into
  /home/agent/.m2): built successfully; /workspace has the fresh one-commit baseline and
  no target dirs.
- Verifier image (same base, pinned tree warmed into /home/agent/.m2): built successfully.
- Full verifier simulation in the environment image (nop state): 16 security results (all
  fail), 19 functional results (all pass), score.py reward 0.0.
- Gate stages: static PASSED; nop PASSED; oracle PASSED (3/3 reward 1.0, identical);
  patches PASSED: all 14 declared checks behaved as required (9 security_fail, 2
  functional_fail, 2 pass, plus the not-yet-generated blind pass).
- The host Docker daemon was deadlocked under load and the build was paused ~1h; the
  operator restarted the daemon and the remaining stages ran on the system Docker only.

## Gate results (each stage run separately, in order)

- static: PASSED (no warnings).
- nop: PASSED (16 security tests all fail, 19 functional all pass).
- oracle: PASSED (3/3 runs, reward 1.0, identical results).
- patches: PASSED. fix_published_only 9 security failures; fix_sso_parser 2;
  fix_logout_only 2; fix_form_wiring 3; fix_cas_route 3; fix_shibboleth_missing 1;
  fix_keycloak_logout_missing 3; fix_ecas_missing 2; crash_as_refusal 13 (5 security
  classes error instead of refusing cleanly); fix_uri_parser_only 8;
  overbroad_relative_only 4 functional failures; overbroad_refuse_all 11 functional
  failures; hardening and alt_correct_fix reward 1.0. All functional tests pass on
  every security_fail variant.

End (UTC): 2026-10-24T09:59:01Z. (The build was paused by the operator for about an
hour while the host Docker daemon was restarted; it resumed at 2026-10-24T07:49:10Z.)
