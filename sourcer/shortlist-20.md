# Sourcer 1 (OSV) shortlist: 16 candidates + 4 controls

Generated 2026-10-13T22:17:19Z by `osv_sourcer.py finalise` from the index and `review/annotations.tsv`.

- Nothing here has been built, run or exploited.
- **main** rows were chosen by the difficulty rules. **control** rows are ones the rules predict are too easy (single sink or one-site guard, compact, Python or JS/TS); they are there to test the rules, not as tasks we expect to survive.
- Columns named `c_*` are computed from the fix diff and the advisory text. Columns marked JUDGEMENT are one reader's verdict after reading the advisory and the diff. Columns marked GUESS (entry point, services) are a reading of the advisory, not a test result.
- Line counts are non-blank added/removed lines in non-test source files of the one fix commit linked.

| # | Role | Advisory / CVE | Repo | Lang | CWE (class) | Published | Files, +/-, hunks | Tests | S1 multi-site | S2 other layer | S3 defence failed | Score (computed / read) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | main | GHSA-mhm7-754m-9p8w  | [fasterxml/jackson-databind](https://github.com/fasterxml/jackson-databind) | Java | CWE-863 Incorrect Authorization (authz) | 2026-07-21 | 1, +75/-36, 4 | yes | yes | yes | yes | 19.0 / 26.0 |
| 2 | main | GHSA-2jwh-9rmr-j4xf CVE-2026-107228 | [asynchttpclient/async-http-client](https://github.com/asynchttpclient/async-http-client) | Java | CWE-287 Improper Authentication (auth_session) | 2026-10-08 | 3, +101/-6, 10 | yes | yes | yes | yes | 15.0 / 24.0 |
| 3 | main | GHSA-6qvr-wjmv-v8mm CVE-2026-54491 | [koel/koel](https://github.com/koel/koel) | PHP | CWE-918 Server-Side Request Forgery (other) | 2026-07-15 | 17, +263/-217, 32 | yes | yes | yes | yes | 16.0 / 21.0 |
| 4 | main | GHSA-fq2p-5p22-8g6j CVE-2026-58429 | [go-gitea/gitea](https://github.com/go-gitea/gitea) | Go | CWE-1259 Improper Restriction of Security Token Assignment (authz) | 2026-07-21 | 14, +148/-81, 37 | yes | yes | yes | yes | 13.0 / 21.0 |
| 5 | main | GHSA-5j98-2g5x-46v6 CVE-2026-93657 | [hickory-dns/hickory-dns](https://github.com/hickory-dns/hickory-dns) | Rust | CWE-347 Improper Verification of Cryptographic Signature (integrity) | 2026-10-05 | 5, +111/-6, 11 | yes | yes | yes | yes | 7.0 / 20.0 |
| 6 | main | GHSA-889w-m37p-88m5  | [pyload/pyload](https://github.com/pyload/pyload) | Python | CWE-613 Insufficient Session Expiration (auth_session) | 2026-10-09 | 5, +65/-33, 11 | yes | yes | yes | yes | 13.0 / 20.0 |
| 7 | main | GHSA-p8qx-h547-fjw9 CVE-2026-102822 | [eugeny/russh](https://github.com/eugeny/russh) | Rust | CWE-129 Improper Validation of Array Index (other) | 2026-09-30 | 2, +73/-22, 3 | no | yes | yes | yes | 12.0 / 20.0 |
| 8 | main | GHSA-6hx8-3wjj-gr8g CVE-2026-54770 | [pylons/webob](https://github.com/pylons/webob) | Python | CWE-601 Open Redirect (other) | 2026-08-27 | 4, +167/-10, 10 | yes | yes | yes | yes | 11.0 / 19.0 |
| 9 | main | GHSA-8c6h-7g6x-m5x4 CVE-2026-49205 | [thorsten/phpmyfaq](https://github.com/thorsten/phpmyfaq) | PHP | CWE-862 Missing Authorization (authz) | 2026-06-23 | 3, +7/-0, 7 | no | yes | no | yes | 15.0 / 19.0 |
| 10 | main | GHSA-3wxw-xv34-2frg CVE-2026-78679 | [gitpython-developers/gitpython](https://github.com/gitpython-developers/gitpython) | Python | CWE-88 Argument Injection (other) | 2026-09-08 | 5, +36/-15, 14 | yes | yes | no | yes | 13.0 / 17.0 |
| 11 | main | GHSA-7gfh-x38p-prh3 CVE-2026-73649 | [shepherdwind/velocity.js](https://github.com/shepherdwind/velocity.js) | TypeScript | CWE-94 Code Injection (other) | 2026-07-24 | 3, +54/-33, 10 | yes | yes | no | yes | 14.0 / 17.0 |
| 12 | main | GHSA-qxvw-fvwx-5cp7 CVE-2026-55857 | [mariadb-corporation/mariadb-connector-j](https://github.com/mariadb-corporation/mariadb-connector-j) | Java | CWE-319 Cleartext Transmission (auth_session) | 2026-08-28 | 4, +15/-6, 4 | yes | yes | no | yes | 16.0 / 17.0 |
| 13 | main | GHSA-xwwr-4h3p-r22c CVE-2026-88018 | [rclone/rclone](https://github.com/rclone/rclone) | Go | CWE-287 Improper Authentication (auth_session) | 2026-09-10 | 5, +266/-63, 20 | yes | no | yes | yes | 13.0 / 17.0 |
| 14 | main | GHSA-9gm5-9rfh-m6vx CVE-2026-86003 | [coredns/coredns](https://github.com/coredns/coredns) | Go | CWE-441 Confused Deputy (authz) | 2026-09-17 | 4, +31/-7, 8 | yes | yes | no | yes | 11.0 / 15.0 |
| 15 | main | GHSA-h3x4-894j-xpx5 CVE-2026-68525 | [apache/tomcat](https://github.com/apache/tomcat) | Java | CWE-863 Incorrect Authorization (authz) | 2026-08-26 | 2, +133/-59, 18 | yes | no | yes | no | 14.0 / 12.0 |
| 16 | main | GHSA-5qhf-9phg-95m2 CVE-2026-73492 | [flavorjones/loofah](https://github.com/flavorjones/loofah) | Ruby | CWE-184 Incomplete List of Disallowed Inputs (other) | 2026-07-21 | 1, +34/-9, 3 | yes | no | no | yes | 7.0 / 10.0 |
| 17 | control | GHSA-g84c-rxfj-3j2c CVE-2026-76844 | [webpack/webpack-dev-middleware](https://github.com/webpack/webpack-dev-middleware) | JavaScript | CWE-22 Path Traversal (other) | 2026-09-29 | 1, +15/-0, 1 | yes | no | no | no | -6.0 / -6.0 |
| 18 | control | GHSA-vj5c-m527-mpff CVE-2026-54639 | [style-dictionary/style-dictionary](https://github.com/style-dictionary/style-dictionary) | JavaScript | CWE-1321 Prototype Pollution (other) | 2026-07-28 | 1, +4/-0, 1 | yes | no | no | no | -6.0 / -6.0 |
| 19 | control | GHSA-7mx3-vvmw-hjmv CVE-2026-104852 | [ardatan/graphql-tools](https://github.com/ardatan/graphql-tools) | TypeScript | CWE-1321 Prototype Pollution (other) | 2026-10-05 | 1, +5/-1, 1 | yes | no | no | no | -5.0 / -5.0 |
| 20 | control | GHSA-j36p-7w88-g82j CVE-2026-49119 | [gradio-app/gradio](https://github.com/gradio-app/gradio) | Python | CWE-22 Path Traversal (other) | 2026-07-01 | 1, +2/-2, 1 | yes | no | no | no | -5.0 / -5.0 |

S1, S2, S3 in the table are JUDGEMENT.

## Per candidate

### 1. GHSA-mhm7-754m-9p8w (no CVE)

- Role: **main**
- Repo: https://github.com/fasterxml/jackson-databind (Java, tier weakest; stars: 3754)
- CWE: CWE-863 Incorrect Authorization (all listed: CWE-863); class: authz
- Fix commit: https://github.com/fasterxml/jackson-databind/commit/c628b357ed143d8492756d5c1458cfb9fbeb29ed (dated 2026-07-05)
- Vulnerable (parent) commit: `d627a8a86fcb062429282f79f3f256f181ed2c7b`
- Published: 2026-07-21; severity: MODERATE; fix commits referenced by the advisory: 2
- Fix size: 1 source files, +75/-36 lines, 4 hunks; tests in fix: yes
- Computed signals: fix sites 4; same new check at 4 sites (`visibleInView`); multi-site 1; cause-layer wording 0; defence-failed 1; bypass/incomplete 1; sibling advisories 3; favoured class 1; single compact hunk 0; far apart 1; restructured 1; single sink 0; one-site guard 0
- JUDGEMENT: S1 multi-site yes (sites touched: 2 methods in ExternalTypeHandler (handlePropertyValue, complete), 4 hunks; sibling sites exist: yes: sibling advisories GHSA-5hh8 and GHSA-rcqc fixed the same missing view check on other deserialisation paths); S2 cause in another layer yes; S3 existing defence ineffective yes; S7 over-broad repair breaks legitimate use yes
- Score: computed 19.0, with reading 26.0
- Entry point (GUESS): Library API: ObjectMapper.readerWithView(View).readValue(json) for a class with a creator parameter carrying @JsonView and @JsonTypeInfo(include=EXTERNAL_PROPERTY)
- Services probably needed (GUESS): none
- Flaw: The active @JsonView filter is applied to ordinary bean properties but not to creator properties handled through the external-type-id path, so a view-restricted constructor parameter is populated from attacker JSON.
- Tempting wrong fix (JUDGEMENT): Add creatorProp.visibleInView(activeView) in the BeanDeserializer branch the advisory names; values are buffered by ExternalTypeHandler and assigned later in complete(), so the restricted property is still populated. The over-broad variant (skip every external-type-id property when a view is active) breaks view-visible properties.
- Why hard (JUDGEMENT): S1: the same view check must hold on every path that can set a property (regular, creator, unwrapped, external type id; two earlier advisories were the same gap elsewhere). S2: the advisory points at BeanDeserializer, the fix lands in ExternalTypeHandler where values are buffered and completed. S3: the view filter existed and was simply not consulted on this path.
- Caveats: metrics describe the largest of 2 fetched fix commits; Two fix commits referenced (2.x and 3.x branches).

### 2. GHSA-2jwh-9rmr-j4xf (CVE-2026-107228)

- Role: **main**
- Repo: https://github.com/asynchttpclient/async-http-client (Java, tier weakest; stars: 6396)
- CWE: CWE-287 Improper Authentication (all listed: CWE-287); class: auth_session
- Fix commit: https://github.com/asynchttpclient/async-http-client/commit/fd9763620725126c1c8bb0af1ceb9a7523099a5f (dated 2026-09-06)
- Vulnerable (parent) commit: `7dc5bbc2d0a48aa2a9caf089a626dcfd333168e9`
- Published: 2026-10-08; severity: MODERATE; fix commits referenced by the advisory: 1
- Fix size: 3 source files, +101/-6 lines, 10 hunks; tests in fix: yes
- Computed signals: fix sites 7; same new check at 2 sites (`withHeaderCookies`); multi-site 1; cause-layer wording 0; defence-failed 1; bypass/incomplete 1; sibling advisories 1; favoured class 1; single compact hunk 0; far apart 1; restructured 0; single sink 0; one-site guard 0
- JUDGEMENT: S1 multi-site yes (sites touched: 3 files: NettyRequestFactory (first request), Redirect30xInterceptor (redirect hop), CallerCookies (redirect and auth-retry reconciliation); sibling sites exist: yes: redirect and 401/407 retry hops rebuild the request separately); S2 cause in another layer yes; S3 existing defence ineffective yes; S7 over-broad repair breaks legitimate use yes
- Score: computed 15.0, with reading 24.0
- Entry point (GUESS): Library API: request built with setHeader/addHeader("Cookie", ...) on a client whose CookieStore already holds a cookie for the origin; needs a local HTTP server
- Services probably needed (GUESS): none (a local test HTTP server)
- Flaw: With the default cookie store, a Cookie header the caller set directly is replaced by the store's cookies, so in a multi-user application one user's request can go out with another user's session cookie.
- Tempting wrong fix (JUDGEMENT): In NettyRequestFactory, skip writing store cookies when the caller already set a Cookie header. That drops the jar's cookies (breaks normal cookie-store behaviour that tests cover) and leaves the redirect and auth-retry hops, which rebuild the header from the cookie list.
- Why hard (JUDGEMENT): S3: CVE-2024-53990 was already fixed, but that fix works on the cookie list and a directly set header never reaches it. S1: first request, redirect hop and auth retry each need the same merge rule. S2: the header is lost where the request is serialised, not where cookies are chosen. S7: must merge, keep caller precedence and fold to one header rather than suppress either source.

### 3. GHSA-6qvr-wjmv-v8mm (CVE-2026-54491)

- Role: **main**
- Repo: https://github.com/koel/koel (PHP, tier weak; stars: 17278)
- CWE: CWE-918 Server-Side Request Forgery (all listed: CWE-918); class: other
- Fix commit: https://github.com/koel/koel/commit/5f6ce2cefd08f437a269236b677ad971517ccbb6 (dated 2026-06-04)
- Vulnerable (parent) commit: `8ee1de0f5589ef34d3e3bbb9c9555a5de69eaf06`
- Published: 2026-07-15; severity: HIGH; fix commits referenced by the advisory: 2
- Fix size: 17 source files, +263/-217 lines, 32 hunks; tests in fix: yes
- Computed signals: fix sites 24; same new check at 2 sites (`getAsStream`); multi-site 1; cause-layer wording 1; defence-failed 1; bypass/incomplete 1; sibling advisories 6; favoured class 0; single compact hunk 0; far apart 1; restructured 1; single sink 0; one-site guard 0
- JUDGEMENT: S1 multi-site yes (sites touched: 17 source files: podcast sync, episode playable, radio station create/update (API and Subsonic), stream proxy, download service, shared Network/SafeHttp services; sibling sites exist: yes: every server-side fetcher); S2 cause in another layer yes; S3 existing defence ineffective yes; S7 over-broad repair breaks legitimate use no
- Score: computed 16.0, with reading 21.0
- Entry point (GUESS): HTTP API as an authenticated non-admin user: add a podcast or radio station whose URL redirects to an internal address
- Services probably needed (GUESS): database (SQLite or MySQL/PostgreSQL) and a local HTTP server that issues redirects (GUESS)
- Flaw: The fix for CVE-2026-47260 validated only the initial URL in most fetchers and the redirect target in one, so a 302 to an internal address (or DNS rebinding) still reaches internal services from several endpoints.
- Tempting wrong fix (JUDGEMENT): Add the per-redirect check to the one fetcher shown in the proof of concept. The other podcast and radio paths keep following redirects unchecked.
- Why hard (JUDGEMENT): S1: the same 'is this destination allowed' decision is needed in about half a dozen fetch paths. S3 and S4: isSafeUrl() exists and the earlier fix shipped, but only the first hop was checked. S2: the durable fix is in the shared HTTP client layer (IP pinning, redirect callback), not at each caller. PHP; large restructuring (+263/-217).
- Caveats: metrics describe the largest of 2 fetched fix commits; Two fix commits referenced; the linked one moves helper classes, so part of the line count is file moves. SSRF is not one of the favoured classes.

### 4. GHSA-fq2p-5p22-8g6j (CVE-2026-58429)

- Role: **main**
- Repo: https://github.com/go-gitea/gitea (Go, tier weak; stars: 58475)
- CWE: CWE-1259 Improper Restriction of Security Token Assignment (all listed: CWE-1259 CWE-284); class: authz
- Fix commit: https://github.com/go-gitea/gitea/commit/f2a1271f164569264c378fad720b0c000fff3336 (dated 2026-05-18)
- Vulnerable (parent) commit: `81b544c27954fcf37c95b8f7638a78bfda01e9cc`
- Published: 2026-07-21; severity: MODERATE; fix commits referenced by the advisory: 2
- Fix size: 14 source files, +148/-81 lines, 37 hunks; tests in fix: yes
- Computed signals: fix sites 34; same new check at 18 sites (`ApplyPublicOnly`); multi-site 1; cause-layer wording 0; defence-failed 0; bypass/incomplete 0; sibling advisories 15; favoured class 1; single compact hunk 0; far apart 1; restructured 1; single sink 0; one-site guard 0
- JUDGEMENT: S1 multi-site yes (sites touched: 14 source files: ApplyPublicOnly added to six query-option types in models/, applied in org, repo, issue, star, watch and user API handlers, plus the repo assignment and API context; sibling sites exist: yes: every API listing that can return private organisations, repositories, stars, watches, feeds or users); S2 cause in another layer yes; S3 existing defence ineffective yes; S7 over-broad repair breaks legitimate use no
- Score: computed 13.0, with reading 21.0
- Entry point (GUESS): HTTP API: GET /api/v1/user/orgs and /api/v1/users/{username}/orgs/{org}/permissions (and other listings) with a personal access token restricted to public-only
- Services probably needed (GUESS): database (built-in SQLite should do; GUESS) and git
- Flaw: A personal access token limited to public-only can still read private organisation membership and permissions, because the public-only restriction is enforced by route middleware that is missing on some routes and checks the wrong object on others.
- Tempting wrong fix (JUDGEMENT): Add the existing checkTokenPublicOnly() middleware to the two routes named in the advisory. It evaluates the user in the path rather than the organisations returned, and the starred, watched, feed and search listings stay unfiltered.
- Why hard (JUDGEMENT): S1: one restriction must hold in every query that can return private data (the fix touches 14 files). S3: a middleware for exactly this restriction exists and is attached to most routes, so the code looks protected. S2: the fix moves the decision from the route layer to the query options in the model layer. Go, authorisation class.
- Caveats: 1 referenced fix commits not fetched (cap); Two fix commits referenced; the linked one is dated 2026-05-18, before the June window (the advisory was published 2026-07-21). Large application; build time not measured.

### 5. GHSA-5j98-2g5x-46v6 (CVE-2026-93657)

- Role: **main**
- Repo: https://github.com/hickory-dns/hickory-dns (Rust, tier weakest; stars: 5440)
- CWE: CWE-347 Improper Verification of Cryptographic Signature (all listed: CWE-347); class: integrity
- Fix commit: https://github.com/hickory-dns/hickory-dns/commit/92f93c0b889f6a292bc943304d88c4c6561fe1b9 (dated 2026-07-21)
- Vulnerable (parent) commit: `5213becf46316a6c16f2ddf4d904f52c5502efdc`
- Published: 2026-10-05; severity: HIGH; fix commits referenced by the advisory: 1
- Fix size: 5 source files, +111/-6 lines, 11 hunks; tests in fix: yes
- Computed signals: fix sites 6; same new check at 1 sites; multi-site 1; cause-layer wording 0; defence-failed 0; bypass/incomplete 0; sibling advisories 0; favoured class 1; single compact hunk 0; far apart 1; restructured 0; single sink 0; one-site guard 0
- JUDGEMENT: S1 multi-site yes (sites touched: 5 files: DNS error type, retry handle, resolver caching client, resolver, server forwarder (catalog.rs); sibling sites exist: yes: lookup(), lookup_ip() and the server's forwarded-response builder all consume the same validated response); S2 cause in another layer yes; S3 existing defence ineffective yes; S7 over-broad repair breaks legitimate use yes
- Score: computed 7.0, with reading 20.0
- Entry point (GUESS): Library API: Resolver::lookup() / lookup_ip() with DNSSEC validation enabled, against an upstream that returns records with invalid signatures
- Services probably needed (GUESS): none (a mock or scripted upstream DNS server; GUESS)
- Flaw: With DNSSEC validation enabled, the high-level lookup APIs return Ok with the records even when validation marks them bogus, so callers cannot tell forged answers from valid ones.
- Tempting wrong fix (JUDGEMENT): In Resolver::lookup(), scan the returned records and fail when any is not proven secure. That also fails unsigned (insecure) zones, which must keep resolving, and leaves lookup_ip(), the negative-answer path and the server's forwarder returning bogus data; the retry layer must also treat the new error as final.
- Why hard (JUDGEMENT): S3: validation is implemented and runs, but its verdict is dropped before the API returns. S2: the decision belongs where the response becomes a lookup (caching client), and the new error has to be carried through the retry handle and the forwarder. S7: 'reject anything not Secure' breaks ordinary unsigned lookups. Rust, integrity class.
- Caveats: Advisory text is short. Workspace build time not measured.

### 6. GHSA-889w-m37p-88m5 (no CVE)

- Role: **main**
- Repo: https://github.com/pyload/pyload (Python, tier python; stars: 3885)
- CWE: CWE-613 Insufficient Session Expiration (all listed: CWE-613); class: auth_session
- Fix commit: https://github.com/pyload/pyload/commit/3e726ba271a6b1015e3a0ea6dc7e46a8f71a62ad (dated 2026-10-05)
- Vulnerable (parent) commit: `8abfe4f434c28a49c7954ff7aa1124d001cdbf6b`
- Published: 2026-10-09; severity: HIGH; fix commits referenced by the advisory: 1
- Fix size: 5 source files, +65/-33 lines, 11 hunks; tests in fix: yes
- Computed signals: fix sites 9; same new check at 2 sites (`_invalidate_user_sessions`); multi-site 1; cause-layer wording 0; defence-failed 1; bypass/incomplete 0; sibling advisories 1; favoured class 1; single compact hunk 0; far apart 1; restructured 1; single sink 0; one-site guard 0
- JUDGEMENT: S1 multi-site yes (sites touched: 5 files: core API (set_user_permission, remove_user, change_password and a session-invalidator hook), user database, web UI app setup, JSON blueprint, helpers; sibling sites exist: yes: the documented /api/<func> route, its legacy camelCase alias and the web UI JSON routes all reach the same user changes); S2 cause in another layer yes; S3 existing defence ineffective yes; S7 over-broad repair breaks legitimate use no
- Score: computed 13.0, with reading 20.0
- Entry point (GUESS): HTTP: POST /api/set_user_permission (or legacy /api/setUserPermission) as admin, then continued use of the demoted user's cookie session
- Services probably needed (GUESS): none (built-in SQLite)
- Flaw: Changing or revoking a user's permissions through the API updates the database but does not invalidate that user's existing session, which keeps its old role and permission bits for up to the session lifetime.
- Tempting wrong fix (JUDGEMENT): Call the existing session-invalidation helper in the one web route named in the report. The legacy alias and other API methods that change users (remove_user, password or role changes) still leave sessions alive.
- Why hard (JUDGEMENT): S2: invalidation lived in the web UI JSON blueprint; the change that needs it happens in the core API layer, and the fix moves it there behind a hook. S1: several user-mutating API methods and two routes to each. S3: session invalidation already existed on one path, so the code looks covered. Python but in the session-handling class.

### 7. GHSA-p8qx-h547-fjw9 (CVE-2026-102822)

- Role: **main**
- Repo: https://github.com/eugeny/russh (Rust, tier weakest; stars: 1901)
- CWE: CWE-129 Improper Validation of Array Index (all listed: CWE-129); class: other
- Fix commit: https://github.com/eugeny/russh/commit/2885385abfee279092a41d80c6cb6ac367353159 (dated 2026-08-23)
- Vulnerable (parent) commit: `3430fd26ecafc0dc3705210f5f39a9119fa22774`
- Published: 2026-09-30; severity: LOW; fix commits referenced by the advisory: 1
- Fix size: 2 source files, +73/-22 lines, 3 hunks; tests in fix: no
- Computed signals: fix sites 3; same new check at 1 sites; multi-site 0; cause-layer wording 1; defence-failed 1; bypass/incomplete 1; sibling advisories 1; favoured class 0; single compact hunk 0; far apart 1; restructured 1; single sink 0; one-site guard 0
- JUDGEMENT: S1 multi-site yes (sites touched: 2 files: negotiation.rs (client-to-server and server-to-client MAC selection) and cipher/mod.rs (length check); sibling sites exist: yes: both directions of MAC selection); S2 cause in another layer yes; S3 existing defence ineffective yes; S7 over-broad repair breaks legitimate use no
- Score: computed 12.0, with reading 20.0
- Entry point (GUESS): Network: SSH key exchange in which both peers offer MAC 'none' together with a CTR/CBC cipher, then one crafted packet
- Services probably needed (GUESS): none
- Flaw: Algorithm negotiation checks that a MAC-requiring block cipher has a MAC only in the fallback branch, so 'none' can be negotiated with AES-CTR/CBC; a short packet then panics the reader (and the session has no integrity protection).
- Tempting wrong fix (JUDGEMENT): Add a bounds check in cipher::read where the slice index panics. The crash goes away, but an unauthenticated CTR/CBC session can still be negotiated.
- Why hard (JUDGEMENT): S2: the report and the panic point at cipher::read; the cause is in negotiation.rs. S3: the needs_mac() check existed but ran only when no common MAC was found. A fix judged only on 'no panic' passes while leaving the negotiation flaw. Rust.
- Caveats: No tests changed in the fix commit apart from an inline unit test; CWE listed is CWE-129 (index validation), which hides the integrity aspect. Hidden tests would need an SSH peer that offers mac=none.

### 8. GHSA-6hx8-3wjj-gr8g (CVE-2026-54770)

- Role: **main**
- Repo: https://github.com/pylons/webob (Python, tier python; stars: 443)
- CWE: CWE-601 Open Redirect (all listed: CWE-601); class: other
- Fix commit: https://github.com/pylons/webob/commit/ff89560643fb252751b4db8806a283b5377f1f07 (dated 2026-06-09)
- Vulnerable (parent) commit: `54c1133c79e48940776a272f4500530e1cc3232a`
- Published: 2026-08-27; severity: MODERATE; fix commits referenced by the advisory: 1
- Fix size: 4 source files, +167/-10 lines, 10 hunks; tests in fix: yes
- Computed signals: fix sites 4; same new check at 1 sites; multi-site 1; cause-layer wording 1; defence-failed 0; bypass/incomplete 1; sibling advisories 1; favoured class 0; single compact hunk 0; far apart 1; restructured 0; single sink 0; one-site guard 0
- JUDGEMENT: S1 multi-site yes (sites touched: 3 call sites (Response Location handling, exc.py redirect __call__, Request.relative_url) plus a new urljoin in util.py; sibling sites exist: yes); S2 cause in another layer yes; S3 existing defence ineffective yes; S7 over-broad repair breaks legitimate use no
- Score: computed 11.0, with reading 19.0
- Entry point (GUESS): Library API / WSGI: a redirect response whose Location value starts with a space or C0 control character followed by //host
- Services probably needed (GUESS): none
- Flaw: WebOb checks a redirect target for a scheme or leading // before joining it to the request URL, but urllib's urljoin strips leading control characters and spaces afterwards, so ' //evil.example' passes the check and becomes an off-site redirect.
- Tempting wrong fix (JUDGEMENT): Strip the extra characters before the check in _make_location_absolute. The exc.py path and relative_url call urljoin directly and stay exposed, and the check still depends on mirroring whatever urlsplit strips in each Python version.
- Why hard (JUDGEMENT): S2: the check and the parser disagree, and the lasting fix replaces the parser (own RFC 3986 urljoin) instead of adding another strip. S3 and S4: this is the third advisory for the same check. S1: three call sites.
- Caveats: Behaviour depends on the Python version (urlsplit stripping, 3.10+). Python and not a favoured class (open redirect); kept for signals 1-4.

### 9. GHSA-8c6h-7g6x-m5x4 (CVE-2026-49205)

- Role: **main**
- Repo: https://github.com/thorsten/phpmyfaq (PHP, tier weak; stars: 620)
- CWE: CWE-862 Missing Authorization (all listed: CWE-862); class: authz
- Fix commit: https://github.com/thorsten/phpmyfaq/commit/d5c195b1ecf5dc30fb825d7eb50d22481c24cb07 (dated 2026-05-24)
- Vulnerable (parent) commit: `df54d00cefec73dc9da35fc9fcf60f5fa7cc310c`
- Published: 2026-06-23; severity: MODERATE; fix commits referenced by the advisory: 1
- Fix size: 3 source files, +7/-0 lines, 7 hunks; tests in fix: no
- Computed signals: fix sites 4; same new check at 4 sites (`userHasPermission`); multi-site 1; cause-layer wording 0; defence-failed 0; bypass/incomplete 1; sibling advisories 3; favoured class 1; single compact hunk 0; far apart 1; restructured 0; single sink 0; one-site guard 0
- JUDGEMENT: S1 multi-site yes (sites touched: 4 endpoints in 3 controllers (Category, Faq x2, Question); sibling sites exist: yes: the advisory lists four endpoints left out when BackupController was fixed; not checked whether more exist); S2 cause in another layer no; S3 existing defence ineffective yes; S7 over-broad repair breaks legitimate use no
- Score: computed 15.0, with reading 19.0
- Entry point (GUESS): HTTP REST API: write endpoints called with a valid shared API token by a user without the matching permission
- Services probably needed (GUESS): database (MySQL/MariaDB, PostgreSQL or SQLite)
- Flaw: Four public-API write endpoints check only the shared API token and never the calling user's permission, so any token holder can create categories, FAQs and questions.
- Tempting wrong fix (JUDGEMENT): Add userHasPermission() to the single endpoint named in the report title, as the previous CVE fix did for BackupController; the other endpoints stay open.
- Why hard (JUDGEMENT): S1 in its plainest form: one line per endpoint, and a fix is only complete if every write endpoint has it. S4: this advisory exists because CVE-2026-24421 was fixed at one site only. S3: hasValidToken() looks like an access check but is not per-user. Tiny fix (+7 lines) that is easy to leave partial. PHP, authorisation class.
- Caveats: No tests in the fix commit. Fix is added-only single lines, so the computed shape signals rate it low.

### 10. GHSA-3wxw-xv34-2frg (CVE-2026-78679)

- Role: **main**
- Repo: https://github.com/gitpython-developers/gitpython (Python, tier python; stars: 5185)
- CWE: CWE-88 Argument Injection (all listed: CWE-200 CWE-88); class: other
- Fix commit: https://github.com/gitpython-developers/gitpython/commit/1b0d2d9b91575f7db44ef4ff58ac37fc9335e5f6 (dated 2026-08-05)
- Vulnerable (parent) commit: `4ba9ce61b709f52ac92fa0c711efe2dcbe2bd89e`
- Published: 2026-09-08; severity: MODERATE; fix commits referenced by the advisory: 1
- Fix size: 5 source files, +36/-15 lines, 14 hunks; tests in fix: yes
- Computed signals: fix sites 13; same new check at 1 sites; multi-site 1; cause-layer wording 0; defence-failed 1; bypass/incomplete 1; sibling advisories 16; favoured class 0; single compact hunk 0; far apart 1; restructured 1; single sink 0; one-site guard 0
- JUDGEMENT: S1 multi-site yes (sites touched: 5 files, about 13 hunks: tag creation, diff (two classes), blame options, ls-remote, and the shared option checker; sibling sites exist: yes: every wrapper that forwards user values to a git subcommand); S2 cause in another layer no; S3 existing defence ineffective yes; S7 over-broad repair breaks legitimate use no
- Score: computed 13.0, with reading 17.0
- Entry point (GUESS): Library API: TagReference.create(repo, path, reference=...) and the diff/blame wrappers with attacker-influenced arguments
- Services probably needed (GUESS): none (git binary)
- Flaw: The unsafe-option guard for `git tag` inspects keyword arguments only, so a positional reference such as --file=<path> reaches git and the file's content is returned as the tag message; diff and blame have the same kind of gap.
- Tempting wrong fix (JUDGEMENT): Reject a reference that starts with --file or -F in TagReference.create. Option abbreviations, clustered short options and the equivalent gaps in diff, blame and ls-remote remain.
- Why hard (JUDGEMENT): S3: the guard and its deny-list were added by the previous fix and are called, but with an empty positional list. S1: the same guard must be applied to positionals and kwargs in several wrappers, each with its own set of dangerous options. S4: stated incomplete fix; GitPython has several advisories of this family in the window.
- Caveats: Python and not a favoured class; kept for signals 1, 3 and 4.

### 11. GHSA-7gfh-x38p-prh3 (CVE-2026-73649)

- Role: **main**
- Repo: https://github.com/shepherdwind/velocity.js (TypeScript, tier strong; stars: 615)
- CWE: CWE-94 Code Injection (all listed: CWE-94); class: other
- Fix commit: https://github.com/shepherdwind/velocity.js/commit/f8e47a6c4607249b9c967d3a1ced959b4dd64dba (dated 2026-07-14)
- Vulnerable (parent) commit: `4cbc7f102c1c7c3e938883a11789231c2d9e6eac`
- Published: 2026-07-24; severity: CRITICAL; fix commits referenced by the advisory: 1
- Fix size: 3 source files, +54/-33 lines, 10 hunks; tests in fix: yes
- Computed signals: fix sites 9; same new check at 5 sites (`isBlockedPathKey`); multi-site 1; cause-layer wording 0; defence-failed 1; bypass/incomplete 1; sibling advisories 0; favoured class 0; single compact hunk 0; far apart 1; restructured 1; single sink 0; one-site guard 0
- JUDGEMENT: S1 multi-site yes (sites touched: 3 files: guard moved out of set.ts into a shared module and applied at 4 reference sites in references.ts (root context lookup, property read, index access, method call); two `in` tests replaced by own-property tests; sibling sites exist: yes: every way a template can walk from a value to its prototype chain); S2 cause in another layer no; S3 existing defence ineffective yes; S7 over-broad repair breaks legitimate use yes
- Score: computed 14.0, with reading 17.0
- Entry point (GUESS): Library API: rendering an attacker-controlled Velocity template (property read reaching the Function constructor)
- Services probably needed (GUESS): none
- Flaw: The guard added for GHSA-j658-c2gf-x6pq blocks constructor / __proto__ / prototype only in #set assignment paths; property reads and method calls are unfiltered, so a template can reach the Function constructor and execute code.
- Tempting wrong fix (JUDGEMENT): Block the key 'constructor' in the one property-read path the proof of concept uses. Index access, method calls and the root context lookup stay open; and banning the key names outright also hides legitimate own properties called 'constructor', which the real fix keeps readable through an own-property test.
- Why hard (JUDGEMENT): S3 and S4: a guard for exactly these keys exists and the advisory is a stated bypass of it. S1: the same rule has to be applied at every reference-resolution path (4 sites plus the #set paths). S7: a keyword ban breaks data objects that have such keys as own properties.
- Caveats: TypeScript, the models' strongest language, and a code-injection class; kept because signals 1, 3, 4 and 7 all apply. Small project (615 stars).

### 12. GHSA-qxvw-fvwx-5cp7 (CVE-2026-55857)

- Role: **main**
- Repo: https://github.com/mariadb-corporation/mariadb-connector-j (Java, tier weakest; stars: 363)
- CWE: CWE-319 Cleartext Transmission (all listed: CWE-319 CWE-522); class: auth_session
- Fix commit: https://github.com/mariadb-corporation/mariadb-connector-j/commit/f4a727c764d1cf48fd0c3d5e301dfa92503e0a58 (dated 2026-06-08)
- Vulnerable (parent) commit: `a87c711315f501497509c693564aad3eda50d187`
- Published: 2026-08-28; severity: MODERATE; fix commits referenced by the advisory: 2
- Fix size: 4 source files, +15/-6 lines, 4 hunks; tests in fix: yes
- Computed signals: fix sites 4; same new check at 4 sites (`requireSecure`); multi-site 1; cause-layer wording 1; defence-failed 1; bypass/incomplete 0; sibling advisories 1; favoured class 1; single compact hunk 0; far apart 1; restructured 0; single sink 0; one-site guard 0
- JUDGEMENT: S1 multi-site yes (sites touched: 4 files: the gate in StandardClient plus the per-plugin flag on the factory interface, ClearPassword and PAM factories; sibling sites exist: yes: every authentication plugin that sends the password unhashed needs the flag; PAM (dialog) was the one missed); S2 cause in another layer no; S3 existing defence ineffective yes; S7 over-broad repair breaks legitimate use yes
- Score: computed 16.0, with reading 17.0
- Entry point (GUESS): Library API: JDBC connection to a server (hostile or man-in-the-middle) that answers with an Authentication Switch Request for the dialog plugin over plain TCP
- Services probably needed (GUESS): MariaDB server with PAM, or a scripted fake MySQL-protocol server (GUESS)
- Flaw: The driver refuses to send a cleartext password over plain TCP for mysql_clear_password, but the sibling PAM (dialog) plugin has no such gate, so a server can make the client send the password in clear.
- Tempting wrong fix (JUDGEMENT): Refuse the dialog plugin whenever TLS is off: this breaks PAM authentication over a local unix socket, which is legitimate and which the real fix explicitly exempts. Or hard-code a check inside the PAM plugin only, leaving the gate keyed to one plugin name again.
- Why hard (JUDGEMENT): S3: a working 'requires TLS' gate existed and covered only one of the plugins that transmit the password. S1: the property has to be declared per plugin and enforced at the one switch point. S7: the simple rule (no TLS, no PAM) rejects unix-socket connections. Java, authentication class; small fix (+15/-6) that is easy to get half right.
- Caveats: metrics describe the largest of 2 fetched fix commits; Two fix commits referenced. Reproducing needs a server that requests the dialog plugin; not verified how hard that is to script.

### 13. GHSA-xwwr-4h3p-r22c (CVE-2026-88018)

- Role: **main**
- Repo: https://github.com/rclone/rclone (Go, tier weak; stars: 60288)
- CWE: CWE-287 Improper Authentication (all listed: CWE-287 CWE-306); class: auth_session
- Fix commit: https://github.com/rclone/rclone/commit/90595f34f27f569be6b27c57fe5ab65057d323bd (dated 2026-08-24)
- Vulnerable (parent) commit: `b3cf0444a2a3345f81d53919f38b28ef8630e6e7`
- Published: 2026-09-10; severity: CRITICAL; fix commits referenced by the advisory: 1
- Fix size: 5 source files, +266/-63 lines, 20 hunks; tests in fix: yes
- Computed signals: fix sites 17; same new check at 2 sites (`CallAccessKey`); multi-site 1; cause-layer wording 0; defence-failed 1; bypass/incomplete 0; sibling advisories 1; favoured class 1; single compact hunk 0; far apart 1; restructured 1; single sink 0; one-site guard 0
- JUDGEMENT: S1 multi-site no (sites touched: 5 files: serve/s3/server.go, s3.go, serve/proxy/proxy.go and the proxy test helper; sibling sites exist: unknown); S2 cause in another layer yes; S3 existing defence ineffective yes; S7 over-broad repair breaks legitimate use yes
- Score: computed 13.0, with reading 17.0
- Entry point (GUESS): CLI + HTTP: `rclone serve s3 --auth-proxy <prog>` without --auth-key, then S3 requests signed with an empty secret
- Services probably needed (GUESS): none (the auth proxy is a local script)
- Flaw: With --auth-proxy, a middleware registers whatever access key id the client presents with the configured secret, which is empty unless --auth-key is set, so SigV4 verification succeeds for any request signed with an empty secret.
- Tempting wrong fix (JUDGEMENT): Refuse to start when --auth-proxy is used without --auth-key, or skip registering a key when the secret is empty. The first breaks the documented proxy-only mode; the second makes every proxy user fail signature verification. Neither gives per-user secrets.
- Why hard (JUDGEMENT): S2: the signature check that 'fails' is in gofakes3; the bad state is created earlier by the middleware that fills the credential store from client input. S3: full SigV4 verification is present and runs, it is just fed an attacker-chosen key. S7: the real fix extends the proxy protocol so the proxy returns the secret per access key (+266/-63). Go, authentication class.

### 14. GHSA-9gm5-9rfh-m6vx (CVE-2026-86003)

- Role: **main**
- Repo: https://github.com/coredns/coredns (Go, tier weak; stars: 14367)
- CWE: CWE-441 Confused Deputy (all listed: CWE-441); class: authz
- Fix commit: https://github.com/coredns/coredns/commit/530b0a5ff2ad68cc0421f10dd93568945cc671c9 (dated 2026-07-16)
- Vulnerable (parent) commit: `d5e54040ffab9a5c12c6de27b66f59f62b385195`
- Published: 2026-09-17; severity: HIGH; fix commits referenced by the advisory: 1
- Fix size: 4 source files, +31/-7 lines, 8 hunks; tests in fix: yes
- Computed signals: fix sites 5; same new check at 4 sites (`UnpackRequest`); multi-site 1; cause-layer wording 0; defence-failed 0; bypass/incomplete 0; sibling advisories 0; favoured class 1; single compact hunk 0; far apart 1; restructured 1; single sink 0; one-site guard 0
- JUDGEMENT: S1 multi-site yes (sites touched: 4 call sites in 3 files: gRPC Query, QUIC stream (DoQ), and the two DoH decoders in doh.go (POST body and GET base64), plus a new shared helper; sibling sites exist: yes: UDP/TCP/DoT already enforce the rule in a different code path); S2 cause in another layer no; S3 existing defence ineffective yes; S7 over-broad repair breaks legitimate use no
- Score: computed 11.0, with reading 15.0
- Entry point (GUESS): Network: RFC 2136 UPDATE message sent over DNS-over-HTTPS, DoH3, DoQ or DNS-over-gRPC to a CoreDNS that forwards upstream
- Services probably needed (GUESS): an upstream DNS server that accepts dynamic updates, or a stub upstream (GUESS)
- Flaw: UDP, TCP and DoT listeners reject UPDATE opcodes before plugin dispatch, but the DoH, DoH3, DoQ and gRPC listeners unpack messages themselves and forward UPDATEs unchanged to the upstream.
- Tempting wrong fix (JUDGEMENT): Reject UPDATE in the one path the report demonstrates (for example the DoH POST decoder), or add an opcode check in the forward plugin only; the DoH GET decoder, DoQ and gRPC, and other proxying plugins stay open.
- Why hard (JUDGEMENT): S1: one request policy has to hold at four separately written unpack sites (the fix routes all of them through one UnpackRequest helper). S3: the rejection existed for the classic transports, so the code looks protected. Small fix (+31/-7) spread over 4 files. Go.
- Caveats: Fix commit is a 'Merge commit from fork' (GitHub private-fork merge).

### 15. GHSA-h3x4-894j-xpx5 (CVE-2026-68525)

- Role: **main**
- Repo: https://github.com/apache/tomcat (Java, tier weakest; stars: 8260)
- CWE: CWE-863 Incorrect Authorization (all listed: CWE-863); class: authz
- Fix commit: https://github.com/apache/tomcat/commit/10d048e16034ddf12055e0cede0da05b15c823b8 (dated 2026-07-30)
- Vulnerable (parent) commit: `4fb4523d70258614a00e7501ae0fdf3cdcbc2470`
- Published: 2026-08-26; severity: CRITICAL; fix commits referenced by the advisory: 3
- Fix size: 2 source files, +133/-59 lines, 18 hunks; tests in fix: yes
- Computed signals: fix sites 17; same new check at 4 sites (`doAuthenticateExtended`); multi-site 1; cause-layer wording 0; defence-failed 1; bypass/incomplete 0; sibling advisories 0; favoured class 1; single compact hunk 0; far apart 1; restructured 1; single sink 0; one-site guard 0
- JUDGEMENT: S1 multi-site no (sites touched: 2 classes: AuthenticatorBase.invoke and FormAuthenticator (new result type threaded through doAuthenticate); sibling sites exist: unknown); S2 cause in another layer yes; S3 existing defence ineffective no; S7 over-broad repair breaks legitimate use yes
- Score: computed 14.0, with reading 12.0
- Entry point (GUESS): HTTP: FORM login, after which Tomcat restores the saved original request whose method differs from the login POST
- Services probably needed (GUESS): none
- Flaw: Security constraints are looked up for the request before FORM authentication; when the saved request is restored with a different HTTP method the stale constraints are used, so a method-specific constraint is bypassed.
- Tempting wrong fix (JUDGEMENT): Patch FormAuthenticator.restoreRequest (where the method changes) to refuse or downgrade restored requests whose method differs, or re-check only roles there; that either breaks the documented restore-POST-after-login behaviour that existing FORM tests cover, or leaves the user-data (transport) constraint and cache headers computed for the wrong method.
- Why hard (JUDGEMENT): S2: the wrong state (constraints for the pre-login method) is produced in AuthenticatorBase.invoke, but the symptom appears after FormAuthenticator swaps the request; the real fix changes the authenticator contract so the caller refreshes constraints. S7: the obvious repair removes saved-request restore. Java, authorisation class, fix restructures control flow (+133/-59).
- Caveats: metrics describe the largest of 3 fetched fix commits; Three fix commits referenced (one per Tomcat branch); metrics are for one of them. Not checked which branch the linked commit is on.

### 16. GHSA-5qhf-9phg-95m2 (CVE-2026-73492)

- Role: **main**
- Repo: https://github.com/flavorjones/loofah (Ruby, tier weak; stars: 1000)
- CWE: CWE-184 Incomplete List of Disallowed Inputs (all listed: CWE-184 CWE-79); class: other
- Fix commit: https://github.com/flavorjones/loofah/commit/f1be9d893b5a8dd79240441a912d8897e74c38c0 (dated 2026-07-13)
- Vulnerable (parent) commit: `5e91af861e3cdab47b91dd0b81f3afdfd13a5e19`
- Published: 2026-07-21; severity: LOW; fix commits referenced by the advisory: 1
- Fix size: 1 source files, +34/-9 lines, 3 hunks; tests in fix: yes
- Computed signals: fix sites 3; same new check at 1 sites; multi-site 0; cause-layer wording 0; defence-failed 1; bypass/incomplete 1; sibling advisories 3; favoured class 0; single compact hunk 0; far apart 1; restructured 0; single sink 1; one-site guard 0
- JUDGEMENT: S1 multi-site no (sites touched: 1 function (allowed_uri?) plus a new decoder, 3 hunks in one file; sibling sites exist: yes: sibling advisory GHSA-8whx-365g-h9vv is another bypass of the same check (named whitespace references)); S2 cause in another layer no; S3 existing defence ineffective yes; S7 over-broad repair breaks legitimate use yes
- Score: computed 7.0, with reading 10.0
- Entry point (GUESS): Library API: Loofah::HTML5::Scrub.allowed_uri?(string) called directly by an application
- Services probably needed (GUESS): none
- Flaw: allowed_uri? decodes HTML character references before testing the scheme, but only those ending in a semicolon; a browser also decodes semicolon-less numeric references, so java&#115cript: style URIs are reported safe.
- Tempting wrong fix (JUDGEMENT): Make the semicolon optional for the exact decimal form in the report, or strip '&#' sequences before the scheme test, or reject any URI containing '&#'. The first two miss hex and zero-padded forms or produce a different string than the browser sees; the last rejects legitimate encoded URLs.
- Why hard (JUDGEMENT): S3: the decoding step is there and looks sufficient; it disagrees with browser parsing in a corner the report shows only one instance of. S7: blanket rejection breaks valid input. Ruby. Single file, so signals 1 and 2 do not apply.
- Caveats: Advisory says Loofah's default sanitize() path is not affected; only direct callers of allowed_uri?. Not in a favoured class (filter bypass leading to XSS).

### 17. CONTROL: GHSA-g84c-rxfj-3j2c (CVE-2026-76844)

- Role: **control**
- Repo: https://github.com/webpack/webpack-dev-middleware (JavaScript, tier strong; stars: 2509)
- CWE: CWE-22 Path Traversal (all listed: CWE-22); class: other
- Fix commit: https://github.com/webpack/webpack-dev-middleware/commit/cefccbac330c29052fc6dffe85fd292ea2ac782b (dated 2026-09-03)
- Vulnerable (parent) commit: `ec97e06f377e593cb40e4a07e81ffd937ea82026`
- Published: 2026-09-29; severity: HIGH; fix commits referenced by the advisory: 2
- Fix size: 1 source files, +15/-0 lines, 1 hunks; tests in fix: yes
- Computed signals: fix sites 1; same new check at 1 sites; multi-site 0; cause-layer wording 0; defence-failed 0; bypass/incomplete 0; sibling advisories 0; favoured class 0; single compact hunk 1; far apart 0; restructured 0; single sink 0; one-site guard 1
- JUDGEMENT: S1 multi-site no (sites touched: 1 hunk, 15 added lines; sibling sites exist: no); S2 cause in another layer no; S3 existing defence ineffective no; S7 over-broad repair breaks legitimate use no
- Score: computed -6.0, with reading -6.0
- Entry point (GUESS): HTTP: request to a dev server using webpack-dev-middleware with a publicPath that does not end in a slash
- Services probably needed (GUESS): none
- Flaw: getFilenameFromUrl slices the URL by publicPath length, so with a non-slash-terminated publicPath a crafted URL resolves outside the output directory.
- Tempting wrong fix (JUDGEMENT): (control) none needed: a containment check after the path is built, at the reported function, is the fix.
- Why predicted easy (JUDGEMENT): Predicted easy: single function, added-only containment check, JavaScript.
- Caveats: metrics describe the largest of 2 fetched fix commits; Fix commit is a 'Merge commit from fork'; two commits referenced.

### 18. CONTROL: GHSA-vj5c-m527-mpff (CVE-2026-54639)

- Role: **control**
- Repo: https://github.com/style-dictionary/style-dictionary (JavaScript, tier strong; stars: 4858)
- CWE: CWE-1321 Prototype Pollution (all listed: CWE-1321); class: other
- Fix commit: https://github.com/style-dictionary/style-dictionary/commit/23b5e8dda143441f0d6b8e2b4222e2da98058bc5 (dated 2026-06-08)
- Vulnerable (parent) commit: `5345c8c29c8aa7538ea07fcd7dbbadbb5c8e4231`
- Published: 2026-07-28; severity: HIGH; fix commits referenced by the advisory: 2
- Fix size: 1 source files, +4/-0 lines, 1 hunks; tests in fix: yes
- Computed signals: fix sites 1; same new check at 1 sites; multi-site 0; cause-layer wording 0; defence-failed 0; bypass/incomplete 0; sibling advisories 0; favoured class 0; single compact hunk 1; far apart 0; restructured 0; single sink 0; one-site guard 1
- JUDGEMENT: S1 multi-site no (sites touched: 1 hunk, 4 added lines; sibling sites exist: no); S2 cause in another layer no; S3 existing defence ineffective no; S7 over-broad repair breaks legitimate use no
- Score: computed -6.0, with reading -6.0
- Entry point (GUESS): Library API: convertTokenData(tokens, {output: 'object'}) with a token key containing __proto__
- Services probably needed (GUESS): none
- Flaw: convertTokenData builds nested objects from token keys without filtering __proto__, giving prototype pollution.
- Tempting wrong fix (JUDGEMENT): (control) none needed: the obvious guard at the reported spot is the actual fix.
- Why predicted easy (JUDGEMENT): Predicted easy: one sink, one compact added-only hunk at the place the report names, JavaScript, no earlier fix to get round.
- Caveats: 1 referenced commit(s) over 120 days older than the newest were ignored as not the fix; metrics describe the largest of 2 fetched fix commits; Two commits referenced. The shipped fix is itself a keyword check ('__proto__'); constructor/prototype paths were not examined.

### 19. CONTROL: GHSA-7mx3-vvmw-hjmv (CVE-2026-104852)

- Role: **control**
- Repo: https://github.com/ardatan/graphql-tools (TypeScript, tier strong; stars: 5431)
- CWE: CWE-1321 Prototype Pollution (all listed: CWE-1321); class: other
- Fix commit: https://github.com/ardatan/graphql-tools/commit/0b9529f1988fd36186a7c106a6efe0356f1b7f2e (dated 2026-09-07)
- Vulnerable (parent) commit: `1eabf0a45ae173daf046a7e1e91cfea8d481720b`
- Published: 2026-10-05; severity: HIGH; fix commits referenced by the advisory: 1
- Fix size: 1 source files, +5/-1 lines, 1 hunks; tests in fix: yes
- Computed signals: fix sites 1; same new check at 1 sites; multi-site 0; cause-layer wording 0; defence-failed 0; bypass/incomplete 0; sibling advisories 0; favoured class 0; single compact hunk 1; far apart 0; restructured 0; single sink 0; one-site guard 1
- JUDGEMENT: S1 multi-site no (sites touched: 1 hunk, +5/-1; sibling sites exist: no); S2 cause in another layer no; S3 existing defence ineffective no; S7 over-broad repair breaks legitimate use no
- Score: computed -5.0, with reading -5.0
- Entry point (GUESS): Library API: mergeDeep() over objects with keys constructor / __proto__ / prototype (reached in practice through GraphQL field aliases during result merging)
- Services probably needed (GUESS): none
- Flaw: mergeDeep copies keys named __proto__, constructor or prototype, giving prototype pollution.
- Tempting wrong fix (JUDGEMENT): (control) none needed: skip the three keys in the merge loop.
- Why predicted easy (JUDGEMENT): Predicted easy: one utility function, textbook guard, TypeScript.
- Caveats: Monorepo (only packages/utils is touched).

### 20. CONTROL: GHSA-j36p-7w88-g82j (CVE-2026-49119)

- Role: **control**
- Repo: https://github.com/gradio-app/gradio (Python, tier python; stars: 43750)
- CWE: CWE-22 Path Traversal (all listed: CWE-22); class: other
- Fix commit: https://github.com/gradio-app/gradio/commit/97d541f3d5fd05b2587a69ecc94b68fe5d2d7004 (dated 2026-05-31)
- Vulnerable (parent) commit: `0d670adf41a0b510f7fd745495dce1664d38f0e5`
- Published: 2026-07-01; severity: HIGH; fix commits referenced by the advisory: 1
- Fix size: 1 source files, +2/-2 lines, 1 hunks; tests in fix: yes
- Computed signals: fix sites 1; same new check at 1 sites; multi-site 0; cause-layer wording 0; defence-failed 0; bypass/incomplete 0; sibling advisories 0; favoured class 0; single compact hunk 1; far apart 0; restructured 0; single sink 0; one-site guard 1
- JUDGEMENT: S1 multi-site no (sites touched: 1 hunk, +2/-2 (two adjacent path joins in one method); sibling sites exist: no); S2 cause in another layer no; S3 existing defence ineffective no; S7 over-broad repair breaks legitimate use no
- Score: computed -5.0, with reading -5.0
- Entry point (GUESS): HTTP / component API: a FileExplorer component payload whose path segments contain ../, reaching preprocess()
- Services probably needed (GUESS): none
- Flaw: FileExplorer.preprocess joins client-supplied path segments onto root_dir with os.path.join and normpath, so files outside root_dir reach the application callback.
- Tempting wrong fix (JUDGEMENT): (control) none needed: the class already has a _safe_join helper; using it at the two joins in this method is the fix.
- Why predicted easy (JUDGEMENT): Predicted easy: one method, an existing helper to reuse, +2/-2, Python, the report names the method.
- Caveats: Fix commit dated 2026-05-31, one day before the window (advisory published inside it).
