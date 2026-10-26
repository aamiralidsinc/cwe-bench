# Build one security-fix benchmark task (build-v1)

## What this is
We build a security-fix benchmark from published, already-fixed advisories in open-source projects.
You build ONE task, from the advisory below.

The task pins the project at the commit just before the published fix and gives a solver agent that
code plus a short problem report (`instruction.md`). Hidden behavioural tests then score the
solver's fix. The tests check that the flaw is closed, using harmless inputs and markers, and that
legitimate use still works.

Everything stays on this machine. Describe each mechanism in one line in notes and reports; the
tests hold the detail, so never write exploitation steps out in prose. Stay inside this advisory's
own protection, in this repository, at the pinned commit. Note anything outside that scope in one
line in your report, and do not build on it.

Project root: `/home/mara/cwe-bench`. Task: `core-geonetwork-ds`. Pattern: `A+B`. Track: `injected`.

## Goal and acceptance
- **The bar.** Two target models (DeepSeek V4.1 Flash, MiMo-V2.6-Pro) must each fail all 3
  finished attempts because of their own judgement.
- **Fairness.** Everything the tests require must be findable from `instruction.md` plus the code,
  or be standard expert knowledge. A careful engineer who knows where to look fixes it in about
  45 minutes.
- **What never counts as a failure:** timeouts, and runs cut by API or network errors.
- **Proof.** A task is built only when the gate passes. A task that misses the bar is reported as
  such, never shipped weaker.

## Inputs
- Advisory: ["GHSA-PJP7-Q6WP-97QX", "CVE-2026-53573"]; geonetwork/core-geonetwork; CWE-601 open redirect (redirect target validation: protocol-relative / backslash parser differential between server check and browser)
- Pinned (vulnerable) commit: 6c756c63cd1fa942f3832d99c64380c69c5e8be9. Published fix: 0d74f673dfc926bde935819ed34636d789b2fecd, cde9b6481a29e2473b7b74479b4e3fd6843bac4e.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v2",
 "model": "claude-opus-5-5",
 "entry_id": "27365",
 "advisory_ids": [
  "GHSA-PJP7-Q6WP-97QX",
  "CVE-2026-53573"
 ],
 "repo": "geonetwork/core-geonetwork",
 "pinned_commit": "6c756c63cd1fa942f3832d99c64380c69c5e8be9",
 "fix_commits": [
  "0d74f673dfc926bde935819ed34636d789b2fecd",
  "cde9b6481a29e2473b7b74479b4e3fd6843bac4e"
 ],
 "trust_decision": {
  "summary": "Whether a request-supplied post-login/post-logout redirect target (redirectUrl parameter) is server-local or same-site before the response redirects to it; decided separately in the logout handler, the Keycloak and OIDC login filters, and (not at all) in the Spring form-login success handler.",
  "evidence": [
   "core/src/main/java/jeeves/config/springutil/JeevesNodeAwareLogoutSuccessHandler.java:75-107",
   "core/src/main/java/org/fao/geonet/kernel/security/keycloak/KeycloakAuthenticationProcessingFilter.java:149-163",
   "core/src/main/java/org/fao/geonet/kernel/security/openidconnect/GeonetworkOAuth2LoginAuthenticationFilter.java:122-138",
   "web/src/main/webapp/WEB-INF/config-security/config-security-core.xml:172-178"
  ]
 },
 "landing_point": {
  "where": "core/src/main/java/jeeves/config/springutil/JeevesNodeAwareLogoutSuccessHandler.java:79",
  "why": "The only existing same-site check for redirectUrl; its startsWith(\"/\") shortcut lets protocol-relative //host values through, which is the obvious 'bypass' the summary names."
 },
 "fix_sites": [
  {
   "where": "core/src/main/java/jeeves/config/springutil/JeevesNodeAwareLogoutSuccessHandler.java:75-107",
   "entry_point": "HTTP /signout?redirectUrl= (core LogoutFilter, config-security-core.xml:197-221)",
   "module_kind": "logout success handler (core security, jeeves package)"
  },
  {
   "where": "web/src/main/webapp/WEB-INF/config-security/config-security-core.xml:174",
   "entry_point": "HTTP POST /signin with redirectUrl (formLoginFilter, config-security-core.xml:152-184); fix adds new class GeonetworkSavedRequestAwareAuthenticationSuccessHandler (fix.diff:81-153)",
   "module_kind": "Spring XML bean wiring of a framework success handler (no project Java code at pinned commit)"
  },
  {
   "where": "core/src/main/java/org/fao/geonet/kernel/security/keycloak/KeycloakAuthenticationProcessingFilter.java:149-163",
   "entry_point": "Keycloak interactive login callback with redirectUrl query param (config-security-keycloak.xml:84)",
   "module_kind": "optional SSO provider filter (keycloak package)"
  },
  {
   "where": "core/src/main/java/org/fao/geonet/kernel/security/openidconnect/GeonetworkOAuth2LoginAuthenticationFilter.java:122-138",
   "entry_point": "OIDC login callback with redirectUrl query param (config-security-openidconnect.xml:75, config-security-openidconnectbearer.xml:82)",
   "module_kind": "optional SSO provider filter (openidconnect package)"
  },
  {
   "where": "fix.diff:154-310",
   "entry_point": "new shared helper RedirectUtil.isRelativeRedirect / isSafeRedirect / sendSafeRedirect used by all sites",
   "module_kind": "new utility (kernel.security)"
  }
 ],
 "O1_entry_points": 4,
 "O2_out_of_scope_site": {
  "kind": "wrapper_or_composition",
  "where": "web/src/main/webapp/WEB-INF/config-security/config-security-core.xml:172-178 (form login uses stock Spring SavedRequestAwareAuthenticationSuccessHandler with targetUrlParameter=redirectUrl and no check; fix wraps it in a subclass and rewires the bean)"
 },
 "O3_reason_to_dismiss": "The form-login redirect is handled entirely by an unmodified Spring Security class configured in XML, so a solver can argue it is framework behaviour, not GeoNetwork code; the CAS logout handler is a separate optional auth profile with a different parameter name ('redirect') whose default target is already an external CAS URL.",
 "O4_distance": {
  "files": 5,
  "packages": 4,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Absolute same-site URLs must still be honoured: the UI posts redirectUrl=window.location.href on sign-in and an absolute same-site prefix on sign-out; the logout default target and CAS default target (${cas.logout.url}) are absolute URLs that must not be filtered. A fix that only allows '/path' breaks login/logout return-to-page.",
  "where": "web-ui/src/main/resources/catalog/js/CatController.js:1753-1769"
 },
 "O6_input_shapes": [
  "protocol-relative //host",
  "backslash variants /\\host, \\\\host, \\/host",
  "absolute cross-site http(s)://host",
  "scheme-only absolute such as javascript:",
  "same host different protocol or port",
  "unanchored relative such as host.example or catalog.search",
  "null/empty parameter (falls back to default/context home)",
  "case-insensitive host match for same-site absolute URLs"
 ],
 "O7_producer": {
  "kind": "config_loader",
  "where": "web/src/main/webapp/WEB-INF/config-security/config-security-core.xml:172-178 (bean wiring decides which success handler produces the target URL); site host/protocol/port from core/src/main/java/org/fao/geonet/kernel/setting/SettingManager.java:507-522",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "CAS logout: RedirectLogoutSuccessHandler returns the raw 'redirect' request parameter as the redirect target with no validation",
   "where": "core/src/main/java/org/fao/geonet/web/RedirectLogoutSuccessHandler.java:20-27",
   "reason_to_dismiss": "Only active under the CAS security profile (config-security-cas.xml:126-129), uses parameter 'redirect' not 'redirectUrl', lives in org.fao.geonet.web, and its default target is an external CAS URL so external redirects look intended.",
   "distance": "different package (org.fao.geonet.web) and different XML profile from the landing point; not touched by fix",
   "present_in_latest": "unknown",
   "latest_where": ""
  }
 ],
 "O8b_injection_room": [
  {
   "where": "core/src/main/java/org/fao/geonet/kernel/security/shibboleth/ShibbolethPreAuthFilter.java:143-168",
   "sibling": "a Shibboleth branch that honours a redirectUrl query parameter after pre-auth, mirroring the Keycloak/OIDC 'cf GN keycloak' blocks",
   "why_realistic": "Keycloak and OIDC filters already copy this exact pattern for the no-request-cache case; Shibboleth has the same saved-request structure and a maintainer adding parity would copy the old isAbsolute() check."
  },
  {
   "where": "core/src/main/java/org/fao/geonet/kernel/security/keycloak/KeycloakLogoutSuccessHandler.java:52-61",
   "sibling": "honour a redirectUrl parameter as the post-logout URL passed to the IDP logout placeholder",
   "why_realistic": "The core logout handler supports redirectUrl, and the UI always sends it on signout (CatController.js:1763-1769), so a parity request for Keycloak is plausible."
  },
  {
   "where": "web/src/main/webapp/WEB-INF/config-security/config-security-ecas.xml:103-107",
   "sibling": "ECAS success handler switched from alwaysUseDefaultTargetUrl to targetUrlParameter=redirectUrl with the stock Spring class",
   "why_realistic": "Copy of the core formLoginFilter wiring; pure config change a maintainer could make to support return-to-page."
  }
 ],
 "O9_family": "CWE-601 open redirect (redirect target validation: protocol-relative / backslash parser differential between server check and browser)",
 "O9_dos": false,
 "O10_build": {
  "language": "Java",
  "toolchain": "Maven, Java 11 (Spring Security 5, javax.servlet)",
  "services": [],
  "offline_after_build": true,
  "project_tests": "Fix adds Mockito unit tests in core module (RedirectUtilTest, JeevesNodeAwareLogoutSuccessHandlerTest, GeonetworkSavedRequestAwareAuthenticationSuccessHandlerTest); none exist at pinned commit. Handlers can be unit-tested with mocked SettingManager/request without DB."
 },
 "O11_fix_minutes": 45,
 "O12_red_flags": [],
 "O13_recall_risk": "low",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "core/src/main/java/jeeves/config/springutil/JeevesNodeAwareLogoutSuccessHandler.java, core/src/main/java/org/fao/geonet/kernel/security/GeonetworkSavedRequestAwareAuthenticationSuccessHandler.java (new), core/src/main/java/org/fao/geonet/kernel/security/RedirectUtil.java (new), core/src/main/java/org/fao/geonet/kernel/security/keycloak/KeycloakAuthenticationProcessingFilter.java, core/src/main/java/org/fao/geonet/kernel/security/openidconnect/GeonetworkOAuth2LoginAuthenticationFilter.java, web/src/main/webapp/WEB-INF/config-security/config-security-core.xml",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Change startsWith(\"/\") to reject \"//\" in JeevesNodeAwareLogoutSuccessHandler only, missing backslash forms, the Keycloak/OIDC isAbsolute() checks, and the unchecked Spring form-login success handler."
 },
 "out_of_scope_notes": [
  "Client-side redirects in web-ui (EditorController.js:663-664 window.location.replace of redirectUrl; LoginController.js:288-291) are a separate client layer, not pursued.",
  "InspireAtom AtomGetData.java:152 and LogosApi.java:224 redirect to server-derived URLs; unrelated to the login redirect parameter."
 ],
 "unverified": [
  "repo_mb not measured (no shell used); GeoNetwork is a large multi-module repo, likely well above 5 MB and below 1.5 GB.",
  "Saved-request redirects in KeycloakAuthenticationProcessingFilter.java:136-147 and ShibbolethPreAuthFilter.java:156-167 come from the server-side request cache; whether those caches are the restricted GeoNetworkHttpSessionRequestCache (config-security-core.xml:142-150) under every profile was not checked.",
  "present_in_latest unknown for the CAS RedirectLogoutSuccessHandler route (no latest release supplied).",
  "Whether CAS profile is buildable/testable offline in a unit test was assumed from the handler having no dependencies beyond Spring Security."
 ]
}
  ```
- Published fix sites:   - core/src/main/java/jeeves/config/springutil/JeevesNodeAwareLogoutSuccessHandler.java:75-107 — entry point: HTTP /signout?redirectUrl= (core LogoutFilter, config-security-core.xml:197-221) [logout success handler (core security, jeeves package)]
  - web/src/main/webapp/WEB-INF/config-security/config-security-core.xml:174 — entry point: HTTP POST /signin with redirectUrl (formLoginFilter, config-security-core.xml:152-184); fix adds new class GeonetworkSavedRequestAwareAuthenticationSuccessHandler (fix.diff:81-153) [Spring XML bean wiring of a framework success handler (no project Java code at pinned commit)]
  - core/src/main/java/org/fao/geonet/kernel/security/keycloak/KeycloakAuthenticationProcessingFilter.java:149-163 — entry point: Keycloak interactive login callback with redirectUrl query param (config-security-keycloak.xml:84) [optional SSO provider filter (keycloak package)]
  - core/src/main/java/org/fao/geonet/kernel/security/openidconnect/GeonetworkOAuth2LoginAuthenticationFilter.java:122-138 — entry point: OIDC login callback with redirectUrl query param (config-security-openidconnect.xml:75, config-security-openidconnectbearer.xml:82) [optional SSO provider filter (openidconnect package)]
  - fix.diff:154-310 — entry point: new shared helper RedirectUtil.isRelativeRedirect / isSafeRedirect / sendSafeRedirect used by all sites [new utility (kernel.security)]
- Uncovered routes to confirm (pattern B):   - core/src/main/java/org/fao/geonet/web/RedirectLogoutSuccessHandler.java:20-27 — CAS logout: RedirectLogoutSuccessHandler returns the raw 'redirect' request parameter as the redirect target with no validation (reason to dismiss: Only active under the CAS security profile (config-security-cas.xml:126-129), uses parameter 'redirect' not 'redirectUrl', lives in org.fao.geonet.web, and its default target is an external CAS URL so external redirects look intended.; still in latest: unknown)
- Design plan from the lead: No lead plan is provided for this task — you are the lead as well as the builder. Using the Design section above and the screener record, design the task yourself and WRITE YOUR PLAN in `notes.md` BEFORE you build:
  - choose the main lever and at least one more, each with a DIFFERENT reason a solver would dismiss or skip it. The main lever must be HOW-type (its fix needs the mechanism understood: a producer the check never calls, a coupled must-keep-working value, a shape a plausible check mishandles, a route where the protection never existed); another entry point or a planted copy is only an extra;
  - decide the sites, routes and input shapes the security tests will cover;
  - identify the coupled must-keep-working behaviour next to each lever, for the functional tests;
  - for the injected track: decide the realistic sibling gap(s) to add — each must be code a maintainer could plausibly have left, reachable through the real entry point, covered by the task's one general property (never by a sentence of its own), and placed where the published fix never touches. First list EVERY possible sibling site and route you can find (the screener's O8/O8b leads plus your own search of the code). Then pick 2–4 of them: the most complex and hardest to find of all the candidates (how-type over where-type, far from where the report leads, with a plausible reason to dismiss), each with a different reason a solver would skip it. Record the full candidate list, and why each pick beat the others, in notes.md;
  - write the security property ONCE, in general terms over the protected data or outcome, before choosing routes. Every route and sibling must fall under it as written; the report must not describe where any of them lives;
  - if this candidate cannot support a fair task that meets the bar (flaw does not reproduce at the pinned commit through a real entry point, needs network/GPU/GUI at run time, or no design meets the bar), STOP and report why. Do not ship a weak task.
Follow every rule in the Design, Report, Tests and Proof sections exactly. You choose the design; the rules are fixed.
- Host notes: none

## Design: where difficulty comes from
Models find the code the report leads to and diagnose it correctly. They fail on scope. Build these
in, in order of evidence:
1. **Pattern A: the published fix's far sites.**
   - The report leads to one site. The tests cover every entry point the published fix protects,
     including one in a module that looks out of scope: a second implementation, a lower-level
     public API, a wrapper, a save/reload path, or a defaults or merge route.
   - Give it a plausible **reason to dismiss**, and **distance**: another file or package from the
     landing point.
   - **A second implementation is the strongest form of this**: separate code doing the same
     guarded operation (a fallback backend, another package, another transport, a legacy version),
     so fixing the reported copy changes nothing in the other. Models fix the copy the example hits,
     re-run the example and stop. Prefer a real one (Pattern A or B) over a planted one. Find
     candidates by searching for the low-level primitive across packages (redirect following,
     header copying, file writes, message construction). It only counts if the report never
     describes it.
2. **Pattern B: uncovered routes.**
   - Routes into the same protected sink where the advisory's own protection is missing at the
     pinned commit, and which the published fix did not touch.
   - They are unmodified upstream code. A solver may argue they were never covered, but the task's
     general property covers them, so leaving one open is a model failure, not out of scope. The
     same holds for a route where the protection never existed: the property requires it.
   - Make sure the property, read literally, really covers each route (no word that excludes it),
     and that its test fails only when the protection is really missing (it must pass a correct
     fix placed at any valid layer).
   - The strongest lever found so far: DeepSeek 6 of 6 on one; both models 0 of 3 on three combined.
3. **Shape traps: an input form that a plausible check mishandles.** Examples: a value given as an
   array where the check only handles a string; a name split on the first separator when it can
   contain the separator; a resolved path against a lexical check; a rename or rewrite that happens
   after the check; a nested expression the check never inspects. Two conditions: the general
   property must cover the form literally, and the form must not fall inside anything a
   must-keep-working clause or a test fixture calls legitimate. A pure spelling, encoding, verb,
   protocol or role variant of a stated input is NOT a shape trap: both models always catch those
   (see "Never add").
4. **A coupled must-keep-working behaviour** next to the sink, tested functionally, so an
   over-broad fix fails. MiMo tends to over-harden.
5. **Producer off the check's path.** The check depends on data produced elsewhere (a schema,
   serializer, cache, mapper, table builder or config loader) and does not call it; the data
   reaches the check on a separate path (saved and reloaded, rebuilt from config). The fix needs
   both the check and the producer. Models trace into what the check calls, never back to where
   its data comes from. Rules:
   - it counts only if the producer is infrastructure, not a request handler;
   - verify that the check does **not** call the producer; if it does, the model follows the call
     and fixes it;
   - the report describes impact only through the check's path and states the property abstractly
     ("including data saved earlier"); it never points at the producer or the reload path;
   - avoid fixes where the check cannot compile without the producer change (that forces the find);
   - hidden tests must not need a field or function name the solver would have to guess;
   - prefer a producer deep in internal machinery (a table or schema builder). One behind a path
     that is easy to follow falls as soon as anything points at it.
6. **Injected siblings**, only where the plan asks for them. Each must be:
   - code a maintainer could have written, with no deceptive names or comments;
   - reachable through the real entry point;
   - covered by the task's general property, never by a sentence of its own;
   - placed where the upstream fix never touches.
7. **Wrong object.** The authorization check exists but decides on a different object than the one
   the request actually touches: a neighbouring or proxy resource (a parent or container instead of
   the item written), or an identity field the caller supplies (an account inside a caller-provided
   resource name; a parent read from one part of the request while the write uses another). Models
   copy the nearby precedent. Rules:
   - the instruction names the protected object class in product terms ("the objects that hold the
     limits"), never the check or its location;
   - the security test denies exactly the object touched while the proxy object stays allowed;
   - a functional test keeps a legitimate request on that same object working.
8. **Ordering.** The check is right but runs at the wrong moment: after an adjustment turns the
   attacker's value into a different bad value (an offset, a clamp, a unit conversion, a
   normalisation), or after a side effect has already happened (a directory created, a file cleared,
   copied or re-permissioned, a request sent) before the refusal. Rules:
   - the instruction states the property over the attacker's input or the outcome ("nothing outside
     the folder is created or changed, even when the request is refused"), never the order of steps;
   - the security test checks the side effect itself, not only the response;
   - any fix that keeps the property passes, wherever it places the check.
9. **Route where the protection never existed.** Real code reaches the protected sink but never had
   the check at all, so its absence reads as design (DeepSeek missed one 6 of 6 times). Rules:
   - it needs a plausible reason to dismiss: an unsupported combination, a legacy path, a
     neighbouring feature. If the project documents the protection as applying everywhere with no
     exceptions, there is no reason to dismiss and the route adds nothing;
   - the general property must cover it literally; never describe it in the instruction;
   - confirm it with a behavioural test on the pinned copy, like any Pattern B route.
10. **Merged or defaults route.** The restricted value reaches the sink through defaults, a merge,
    inheritance, a patch, or stored configuration rather than the request field the report shows.
    Models treat the report's example fields as the whole set. Rules:
    - state the property over the sink ("anything a submitter supplies that ends up in X, however
      it gets there"), not over the entry or field;
    - the security test drives the merged or stored route through the real entry point;
    - a functional test keeps legitimate defaults and merges working.

Aim for at least two levers with **different** reasons to dismiss.

**At least one lever must be how-type**: its fix needs the mechanism understood, not only found.
How-type levers are a producer off the check's path (5), a coupled must-keep-working value (4), a
shape that a plausible check mishandles (3: a separator split, a rename after the check), and a
route where the protection never existed. Where-type levers (another entry point into the same code,
a second copy, injected siblings) only cost a search. They held only when the report stayed general,
so count them as extras, never as the task's main difficulty.

Never add:
- encoding, verb, protocol or role/direction variants;
- more routes of one concept;
- resource-exhaustion traps.

Every lever must be findable by a blind engineer from the report and the code. A lever that a blind
fix cannot find is unfair: remove it.

**Pattern B rules:**
- Confirm each route with a behavioural test on the pinned copy before relying on it. The
  screener's claim is only a lead.
- Append one row per route to `/home/mara/cwe-bench/build/audit/uncovered-routes.tsv`, using its existing
  header. Columns:
  - `task`, `repo`, `advisory`;
  - `trap_ref` (the manifest trap id only; no mechanism text, since the manifest holds the detail);
  - `real_upstream`;
  - `present_in_latest` (`yes`, `no` or `unknown`, from a read-only look at current upstream code if
    you can reach it);
  - `public_upstream_report`, `in_current_scope`, `built`, `note`;
  - `disclosure_status` (`pending client decision`).

## Environment (`tasks/core-geonetwork-ds/environment/Dockerfile`)
- **Base and code.** A small official base image. The repo goes into `/app` at the pinned commit,
  and `/app/.git` is then deleted.
- **Offline.** Install every dependency, tool and service the project and tests need; nothing may
  be downloaded at test time. Services start from `test.sh`.
- **Packages:** `patch`, `curl`, `ca-certificates`, `bash`, `git`.
- **Agent layer.** Append `harness/claude-code.Dockerfile.snippet` unchanged at the end.
- **No test code in the image.** The agent shares the container. Pre-build against stubs; `test.sh`
  copies the real tests in at grading time.
- **Project tests.** The project's own tests for the affected area must pass in the image at the
  pinned commit.
- **No leaked regression tests.** The pinned commit must not already contain the advisory's
  regression tests (check `git log` between the pinned and fix commits).

## Report to the solver (`tasks/core-geonetwork-ds/instruction.md`)
**Write:**
- what the system is, at product level;
- one observed impact, with ONE concrete trigger at user level (HTTP request, CLI call or public API
  use);
- the security property as an **invariant**, stated once in general terms: who may do what to which
  data, or what attacker input must never achieve ("no value of X may …, however it arrives"). It is
  fair when, read literally, it covers every tested route and shape; it must not point at any of
  them. Write a second property only for a genuinely different protection, never one per route,
  and never a count;
- every **contract** the tests need, each stated once for the whole product, never per route:
  - the refusal form ("a client error with no side effect");
  - any interface or field name a test uses, stated so it applies everywhere. If a sibling's test
    would need a contract that only that sibling uses, change the test so it does not, or drop the
    sibling;
  - preservation clauses ("everything that works today keeps working exactly as today"). Name a
    coupled legitimate value in property terms ("visible values keep binding even next to a hidden
    one"), not by the feature or route it sits on;
  - a legitimate magnitude next to any attack magnitude;
- that examples are examples, not the full set;
- the standard constraints block: fix the problem and its close variants; keep legitimate use
  working; do not look up the upstream fix; do not special-case the
  example.

**Never write:**
- file, package, function, class, field or parameter names a user would not see;
- line numbers, the root cause, the fix approach, or a CVE or GHSA id;
- a list of routes, spellings or roles;
- restricting adverbs ("directly", "only via");
- anything that names or paraphrases a far site, an uncovered route or an injected sibling;
- any clause that describes where a far site, uncovered route or injected sibling lives, even in
  product terms: no route, operation, command, channel, object kind, stage or format that points
  at one of them. State each property once, over the protected data or outcome, so it covers every
  route without pointing at any;
- a word that is general but is also the name of one stage or entry point ("loading" when the
  product has a load call). Pick wording that cannot be read as one surface.

Check before you finish: for each sentence of the report, ask whether it exists to cover one
specific route or trap. If it does, delete it or widen it into the general property.

Put every identifier that must not appear in `manifest.leak_terms`.

## Tests (`tasks/core-geonetwork-ds/tests/`)
- **`security/`:** one test per site, route, input shape and form. Each one:
  - goes through the real entry point;
  - fails on the pinned code and passes on a correct fix;
  - asserts the attack is blocked: any client error plus no side effect, never one exact status.
- **`functional/`:**
  - legitimate use, including the coupled behaviour of every lever;
  - where they exist, the project's own tests for the area.
- **No product code in a test's bookkeeping.** Compute expected values and clean-ups in the test
  itself, because a hardened helper must not crash a test.
- **Stubs** of permission or authority answer per resource and verb, like the real thing.
- **Scope.** A test may vary only what the instruction names, and drive only the entry point it
  names.
- **No network**, and nothing that depends on the fix commit being present.
- **Templates.** JUnit XML into the two directories the template names. Copy `score.py` unchanged.
  Edit only the marked command lines of `test.sh`, and keep its agent-kill block.

## Proof
- **The oracle.** `solution/fix.patch` is the published fix reduced to source changes, plus fixes
  for every uncovered route and injected sibling in the task. `solution/solve.sh` applies it to
  `/app`.
- **Wrong-fix patches** go in `build/core-geonetwork-ds/checks/`, listed in `manifest.patch_checks`:
  - one `security_fail` per lever (the fix that misses only that lever);
  - a `functional_fail` (an over-broad or feature-removing fix);
  - a `pass` of kind `hardening` (the oracle plus defensive hardening of the product code the
    security tests import);
  - a `pass` alternative fix where a second valid design is plausible.
- **`manifest.wrong_fix_catalogue`:** for each class, a `checks/` patch, or `n/a: <why>`:
  `refuse_all`, `crash_as_refusal`, `wrong_resource`, `one_role_or_direction`, `reads_only`,
  `check_after_adjustment`, `unlisted_route`, `malformed_identity`, `missing_authority`,
  `adjacent_api`.

## Deliverables
**`tasks/core-geonetwork-ds/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/core-geonetwork-ds/manifest.json`:**
- `slug`, `candidate`;
- `pattern`: `A+B`;
- `builder_prompt_version`: `build-v1`;
- `"strict_gate": true`;
- `verified`: entry point, sites, routes, services, project tests run;
- `leak_terms`, `patch_checks`, `wrong_fix_catalogue`;
- `traps`: one entry per lever, with `shape`, `where` (file:line), `security_tests`,
  `coupled_functional_tests`, `security_fail_patch`, and `realistic_because` (for pattern B: "real,
  unmodified upstream code");
- `status`.

**Also in `build/core-geonetwork-ds/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py core-geonetwork-ds --only static
python3 -I builder/gate.py core-geonetwork-ds --only nop
python3 -I builder/gate.py core-geonetwork-ds --only oracle
python3 -I builder/gate.py core-geonetwork-ds --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/core-geonetwork-ds/`;
  - edit only `tasks/core-geonetwork-ds/`, `build/core-geonetwork-ds/` and, for pattern B, the register;
  - do not commit.

## Stop and report instead of shipping when
- the flaw does not reproduce through a real entry point at the pinned commit;
- a planned route or site is not reachable, or the check calls the producer directly (substitute
  another lever the code supports if you can, and say so);
- the task needs network at run time, or a GPU, kernel or GUI;
- the tests are flaky;
- no design meets the bar.

## Report back (under 400 words)
- The gate result for each stage.
- Each lever in one line: pattern, shape, file:line, reason to dismiss.
- Pattern B: each register row.
- The instruction's word count.
- Every guess you could not verify.
- Any fairness concern you see yourself.
- Anything noticed outside the scope, in one line.
- If abandoned, exactly why.
