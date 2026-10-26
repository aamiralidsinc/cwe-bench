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

Project root: `/home/mara/cwe-bench`. Task: `stk-mailpit-ghsa8r62`. Pattern: `A+B`. Track: `stacked`.

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
- Advisory: GHSA-524m-q5m7-79mm; GHSA-8r62-w5wh-fc5m
- Pinned (vulnerable) commit: 877a9159ceeaf380d5bb0e1d84017b24d2e7b361. Published fix: 6f1f4f34c989, fbe5e006c3f1.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "candidate_id": "h3-ghsa-8r62-w5wh-fc5m",
 "pattern": "H3b",
 "repo": "axllent/mailpit",
 "pinned_commit": "877a9159ceeaf380d5bb0e1d84017b24d2e7b361",
 "protections": [
  "WebSocket handshake admission: an upgrade request to the web UI event socket must be authorisation- and origin-checked before upgrader.Upgrade, admitting same-origin browsers, excluding foreign Origins, and still admitting Origin-less non-browser clients (server/websockets/client.go:114-141, server/server.go:199,333-336).",
  "Origin/path policy consistency: any decision keyed on the request path (the CORS Access-Control-Allow-Origin grant and the HTML-preview rule) must use the path the router actually matched (decoded r.URL.Path, without the query string), not the raw percent-encoded r.RequestURI (server/server.go:286-295).",
  "Basic-auth enforcement must be decided per request from state the request cannot clear process-wide; handlers must not switch UI credentials off for other in-flight requests (server/server.go:216-253,297-312; internal/auth/auth.go:11-20).",
  "Origin validation for state-changing HTTP endpoints: CORS response headers do not stop cross-origin simple POSTs, so send/release must reject foreign Origins themselves (server/server.go:162-176,267-325; server/apiv1/send.go:45-59; server/apiv1/release.go:58-101).",
  "CORS preflight exemption: only genuine, credential-less preflight OPTIONS requests may skip basic auth; the exemption must stay narrow enough to preserve that documented behaviour (server/server.go:299, CHANGELOG.md:215)."
 ],
 "traps": [
  {
   "id": "T1",
   "mechanism": "M4",
   "origin": "advisory_route",
   "locations": [
    "server/websockets/client.go:37",
    "server/websockets/client.go:129",
    "server/websockets/hub.go:58"
   ],
   "reason_to_dismiss": "The line carries an explicit comment ('allow multi-domain') and overrides gorilla's default same-origin check deliberately; Mailpit is a local development mail catcher, the handshake carries no stored data, and the socket only pushes notifications.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "easy",
   "tier_mimo": "easy",
   "type": "neither",
   "evidence": [
    "server/websockets/client.go:34-39",
    "server/websockets/client.go:114-141",
    "server/server.go:199",
    "server/websockets/hub.go:58-66",
    "server/ui-src/components/AppNotifications.vue:35"
   ]
  },
  {
   "id": "T2",
   "mechanism": "M1",
   "origin": "advisory_route",
   "locations": [
    "server/server.go:199",
    "server/server.go:333"
   ],
   "reason_to_dismiss": "ServeWs performs its own BasicAuth check (client.go:115-127), so the route deliberately does not use middleWareFunc; every other UI/API route is wrapped in it, and the handler is treated as self-contained.",
   "distance": {
    "files": 1,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "server/server.go:162-202",
    "server/server.go:199",
    "server/server.go:333-336",
    "server/websockets/client.go:114-127"
   ]
  },
  {
   "id": "T3",
   "mechanism": "M8",
   "origin": "published_fix_far_site",
   "locations": [
    "server/server.go:291",
    "server/server.go:287"
   ],
   "reason_to_dismiss": "The condition only *adds* an Access-Control-Allow-Origin response header, so a raw/decoded mismatch fails closed: an encoded path still routes, but it simply does not receive the CORS grant. The regex ends in \\.html$ and is applied to a string that still carries the query string, which likewise only narrows the grant.",
   "distance": {
    "files": 1,
    "packages": 1
   },
   "protection_state": "weak",
   "tier_deepseek": "hard",
   "tier_mimo": "xhard",
   "type": "mimo",
   "evidence": [
    "server/server.go:286-295",
    "server/server.go:202",
    "server/server.go:65",
    "config/config.go:542-548"
   ]
  },
  {
   "id": "T4",
   "mechanism": "M11",
   "origin": "uncovered_upstream",
   "locations": [
    "server/server.go:299"
   ],
   "reason_to_dismiss": "Browsers never attach credentials to a CORS preflight, so skipping auth for OPTIONS is required for --api-cors to work at all (the changelog records it as an intentional fix), and the only OPTIONS handler reachable through the middleware returns a blank 200 with no body or side effect (apiv1/api.go:76-80); the exemption has no exploitable consequence.",
   "distance": {
    "files": 1,
    "packages": 1
   },
   "protection_state": "weak",
   "tier_deepseek": "xhard",
   "tier_mimo": "hard",
   "type": "both",
   "evidence": [
    "server/server.go:297-312",
    "server/server.go:202",
    "server/apiv1/api.go:76-80",
    "CHANGELOG.md:215"
   ]
  },
  {
   "id": "T5",
   "mechanism": "M10",
   "origin": "uncovered_upstream",
   "locations": [
    "server/server.go:219",
    "server/server.go:243",
    "server/server.go:300",
    "server/websockets/client.go:115"
   ],
   "reason_to_dismiss": "The mutation is scoped to the send endpoint, the deferred restore runs immediately after the handler returns, and server_test.go:455-492 asserts that regular API endpoints are not affected by send API auth settings; the code reads as deliberate request-scoped plumbing.",
   "distance": {
    "files": 1,
    "packages": 2
   },
   "protection_state": "weak",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "server/server.go:216-253",
    "server/server.go:297-312",
    "server/websockets/client.go:115-127",
    "internal/auth/auth.go:11-20",
    "server/server_test.go:455-492"
   ]
  },
  {
   "id": "T6",
   "mechanism": "M4",
   "origin": "uncovered_upstream",
   "locations": [
    "server/server.go:167",
    "server/server.go:176",
    "server/apiv1/release.go:58",
    "server/apiv1/send.go:45"
   ],
   "reason_to_dismiss": "Mailpit's API is unauthenticated by default and exists to be driven by local scripts and CI; the CORS policy (and the browser's preflight) is assumed to cover cross-origin abuse, the handlers ignore Content-Type so any client shape works, and release additionally requires SMTP relaying to be configured.",
   "distance": {
    "files": 2,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "xhard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "server/server.go:162-176",
    "server/server.go:267-325",
    "server/apiv1/release.go:58-101",
    "server/apiv1/release.go:170",
    "server/apiv1/send.go:45-59",
    "server/apiv1/send.go:186"
   ]
  }
 ],
 "independent_groups": [
  [
   "T1",
   "T2"
  ],
  [
   "T3"
  ],
  [
   "T4"
  ],
  [
   "T5"
  ],
  [
   "T6"
  ]
 ],
 "history": {
  "a_fix_leaves_b_open": true,
  "b_in_code_a_wrote": null,
  "masking": [
   "T5 is invisible unless UI auth is configured: with auth.UICredentials == nil the gates at server/server.go:300 and server/websockets/client.go:115 are no-ops, so the race only matters on an authenticated deployment.",
   "T3 is reachable only when --api-cors is set, because the whole CORS block at server/server.go:290 is skipped otherwise.",
   "T4 has an effect only for OPTIONS requests matched by the api/v1 OPTIONS route (server/server.go:202); any other method/path is answered by the mux 405 handler before middleWareFunc runs, so the exemption exposes no handler.",
   "T6's release vector requires SMTP relay configuration (server/apiv1/release.go:170); the send vector is always available and stores a message."
  ],
  "dependency_bump_fix": false,
  "in_repo_fix_possible": true
 },
 "conflicts": [
  {
   "a": "T1",
   "b": "T3",
   "what": "The natural same-origin rule (compare the Origin host with r.Host) rejects the cross-origin UI deployment that the Access-Control-Allow-Origin policy at server/server.go:290-295 exists to support; an origin check must also admit the configured AccessControlAllowOrigin value and reverse-proxied public hosts, so a strict host equality fix breaks a must-keep-working configuration."
  },
  {
   "a": "T6",
   "b": "T4",
   "what": "Requiring an Origin header, or credentials, on unsafe HTTP methods also catches CORS preflight, which browsers send without credentials; the OPTIONS exemption at server/server.go:299 has to survive any global origin/auth middleware or --api-cors breaks."
  },
  {
   "a": "T5",
   "b": "T1",
   "what": "Replacing the global auth.UICredentials toggle with per-request credentials must keep both Send API auth modes working (server_test.go:336-414) while the websocket gate at server/websockets/client.go:115 still sees the real UI credentials; a naive fix that stops clearing the global changes send-API behaviour, and a fix that keeps clearing it leaves the websocket gate blind during the window."
  }
 ],
 "fairness_risks": [
  "Origin-less clients are legitimate: gorilla only consults CheckOrigin when an Origin header is present, and scripts/proxies/CLI websocket clients normally send none. A rule that rejects missing Origin would refuse a legitimate input shape and break non-browser use.",
  "The web UI itself must keep connecting: AppNotifications.vue:35 builds the socket URL from document.location.host and AppNotifications.vue:50 opens it with no headers; with --webroot the endpoint is Webroot+'api/events' (server/server.go:199), so a check hardcoding /api/events breaks webroot deployments.",
  "Reverse-proxy deployments (Vite/nginx in front of Mailpit) have Origin = the public host and r.Host = the backend address; exact Origin == scheme://r.Host comparison refuses a legitimate deployment.",
  "--api-cors is an existing supported flag, including a literal '*'; a security rule that refuses wildcard or configured cross-origin values contradicts a documented feature.",
  "CORS preflight must stay credential-less (server/server.go:299, CHANGELOG.md:215); requiring auth or an Origin on OPTIONS breaks cross-origin API use.",
  "The API is intentionally unauthenticated by default and is called by local scripts and CI without an Origin header or a JSON Content-Type; a blanket 'reject cross-origin/no-Origin POST' rule refuses legitimate use, and send.go:45-52 deliberately ignores Content-Type.",
  "Browser clients cannot set an Authorization header on a WebSocket handshake (AppNotifications.vue:50; client.go:116 relies on r.BasicAuth()), so the websocket authenticates only via cached Basic credentials; a fix that requires a token header on the handshake breaks the UI."
 ],
 "effort_minutes": 120,
 "usable": true,
 "design": {
  "traps": [
   "T1",
   "T2",
   "T3",
   "T6"
  ],
  "why": "The strongest available stack is four independent judgement points. T1+T2 form one guard (the websocket admission path) but hide two decisions: the CheckOrigin override at client.go:37 must be replaced with a real check, and the /api/events route is registered outside middleWareFunc (server.go:199), so a fix placed only in the shared middleware leaves the reported socket open; their dismiss reasons differ (the deliberate multi-domain comment versus 'ServeWs does its own auth'). T3 is a separate site and a separate decision: the raw RequestURI path policy at server.go:287-291 must be evaluated on the decoded, query-free path, otherwise any path-gated origin check copied from it inherits the percent-encoded-path bypass the advisory names. T6 is a separate sink family: state-changing POSTs (send, release) have no origin validation at all, so a websocket-only fix still lets a foreign page trigger them; its dismiss reason ('CORS/preflight handles it, the API is open by design') is unlike the other two. That mix covers a deepseek-type (T2, T6), a mimo-type/hows-type (T3), and coupled values (the --api-cors origin, webroot and Origin-less clients that the T1 fix must keep working). T5 is a real fifth group but a concurrency race makes hidden tests flaky; T4 is kept as a fairness/conflict constraint rather than a scored trap because the only reachable OPTIONS handler returns a blank 200. If the harness only accepts advisory-named surfaces, the stack narrows to T1/T2 plus T3, which is still two independent edits in two packages."
 },
 "unverified": [
  "The advisory texts and the diffs of a_fix 6f1f4f34c989 and b_fix fbe5e006c3f1 are not in the readable worktree (git metadata lives outside the pinned path), so the exact 'percent-encoded path' mechanism of B and whether B is a revert of A or a coverage gap could not be confirmed. The tree contains no websocket Origin check at all (grep for Origin/CheckOrigin finds only client.go:37 and the CORS config), so whatever A added is not identifiable at this pin.",
  "history.a_fix_leaves_b_open is answered true on this reading: the only refusal logic in the tree lives in middleWareFunc (server.go:267-325) and the /api/events route is registered without it (server.go:199), so an earlier path/origin policy of that shape cannot cover the socket. If A's fix was instead a CheckOrigin implementation that a later commit reverted, the answer would be 'A's code is not present' rather than 'A leaves B open'; the pinned content cannot distinguish the two.",
  "history.b_in_code_a_wrote is left null: client.go is the original Gorilla-derived handler (client.go:1-5) with a long-standing unconditional CheckOrigin, which suggests B is not in code A wrote, but A's patch was not readable.",
  "T3's security direction is uncertain: in the current code the raw-vs-decoded mismatch at server.go:291 fails closed (the request is routed but receives no Access-Control-Allow-Origin header), so on its own it leaks nothing. It is recorded because the advisory names percent-encoded paths and because this line is the obvious template a solver would copy for a path-gated Origin check, where the same shape would fail open. A hidden test that only exercises the CORS header would not prove a vulnerability.",
  "Whether the hidden tests exercise T5 (credential race) or T6 (HTTP CSRF on send/release) is unknown: both are repo-level gaps not named by the candidate summary; they are recorded as uncovered_upstream rather than advisory_route.",
  "gorilla/mux route matching and path cleaning are assumed from its documented default because the dependency source is not vendored in the worktree; no UseEncodedPath or SkipClean call exists in this repository, so r.URL.Path is decoded before matching and the percent-encoded forms reach the same handlers.",
  "The candidate is labelled H3b2 in the run inputs; the output schema enumerates only H3a/H3b/H3c, so pattern is reported as H3b.",
  "Mailpit's default deployment is unauthenticated and localhost-bound; every trap's real-world exploitability therefore depends on the deployment exposing the UI/API beyond localhost, which the code itself does not enforce."
 ]
}
  ```
- Published fix sites:   - server/websockets/client.go:37 — T1 M4 (reason to dismiss: The line carries an explicit comment ('allow multi-domain') and overrides gorilla's default same-origin check deliberately; Mailpit is a local development mail catcher, the handshake carries no stored data, and the socket only pushes notifications.)
  - server/websockets/client.go:129 — T1 M4 (reason to dismiss: The line carries an explicit comment ('allow multi-domain') and overrides gorilla's default same-origin check deliberately; Mailpit is a local development mail catcher, the handshake carries no stored data, and the socket only pushes notifications.)
  - server/websockets/hub.go:58 — T1 M4 (reason to dismiss: The line carries an explicit comment ('allow multi-domain') and overrides gorilla's default same-origin check deliberately; Mailpit is a local development mail catcher, the handshake carries no stored data, and the socket only pushes notifications.)
  - server/server.go:199 — T2 M1 (reason to dismiss: ServeWs performs its own BasicAuth check (client.go:115-127), so the route deliberately does not use middleWareFunc; every other UI/API route is wrapped in it, and the handler is treated as self-contained.)
  - server/server.go:333 — T2 M1 (reason to dismiss: ServeWs performs its own BasicAuth check (client.go:115-127), so the route deliberately does not use middleWareFunc; every other UI/API route is wrapped in it, and the handler is treated as self-contained.)
  - server/server.go:291 — T3 M8 (reason to dismiss: The condition only *adds* an Access-Control-Allow-Origin response header, so a raw/decoded mismatch fails closed: an encoded path still routes, but it simply does not receive the CORS grant. The regex ends in \.html$ and is applied to a string that still carries the query string, which likewise only narrows the grant.)
  - server/server.go:287 — T3 M8 (reason to dismiss: The condition only *adds* an Access-Control-Allow-Origin response header, so a raw/decoded mismatch fails closed: an encoded path still routes, but it simply does not receive the CORS grant. The regex ends in \.html$ and is applied to a string that still carries the query string, which likewise only narrows the grant.)
- Uncovered routes to confirm (pattern B):   - server/server.go:299 — T4 M11 (reason to dismiss: Browsers never attach credentials to a CORS preflight, so skipping auth for OPTIONS is required for --api-cors to work at all (the changelog records it as an intentional fix), and the only OPTIONS handler reachable through the middleware returns a blank 200 with no body or side effect (apiv1/api.go:76-80); the exemption has no exploitable consequence.)
  - server/server.go:219 — T5 M10 (reason to dismiss: The mutation is scoped to the send endpoint, the deferred restore runs immediately after the handler returns, and server_test.go:455-492 asserts that regular API endpoints are not affected by send API auth settings; the code reads as deliberate request-scoped plumbing.)
  - server/server.go:243 — T5 M10 (reason to dismiss: The mutation is scoped to the send endpoint, the deferred restore runs immediately after the handler returns, and server_test.go:455-492 asserts that regular API endpoints are not affected by send API auth settings; the code reads as deliberate request-scoped plumbing.)
  - server/server.go:300 — T5 M10 (reason to dismiss: The mutation is scoped to the send endpoint, the deferred restore runs immediately after the handler returns, and server_test.go:455-492 asserts that regular API endpoints are not affected by send API auth settings; the code reads as deliberate request-scoped plumbing.)
  - server/websockets/client.go:115 — T5 M10 (reason to dismiss: The mutation is scoped to the send endpoint, the deferred restore runs immediately after the handler returns, and server_test.go:455-492 asserts that regular API endpoints are not affected by send API auth settings; the code reads as deliberate request-scoped plumbing.)
  - server/server.go:167 — T6 M4 (reason to dismiss: Mailpit's API is unauthenticated by default and exists to be driven by local scripts and CI; the CORS policy (and the browser's preflight) is assumed to cover cross-origin abuse, the handlers ignore Content-Type so any client shape works, and release additionally requires SMTP relaying to be configured.)
  - server/server.go:176 — T6 M4 (reason to dismiss: Mailpit's API is unauthenticated by default and exists to be driven by local scripts and CI; the CORS policy (and the browser's preflight) is assumed to cover cross-origin abuse, the handlers ignore Content-Type so any client shape works, and release additionally requires SMTP relaying to be configured.)
  - server/apiv1/release.go:58 — T6 M4 (reason to dismiss: Mailpit's API is unauthenticated by default and exists to be driven by local scripts and CI; the CORS policy (and the browser's preflight) is assumed to cover cross-origin abuse, the handlers ignore Content-Type so any client shape works, and release additionally requires SMTP relaying to be configured.)
  - server/apiv1/send.go:45 — T6 M4 (reason to dismiss: Mailpit's API is unauthenticated by default and exists to be driven by local scripts and CI; the CORS policy (and the browser's preflight) is assumed to cover cross-origin abuse, the handlers ignore Content-Type so any client shape works, and release additionally requires SMTP relaying to be configured.)
- Design plan from the lead: TRACK = STACKED (H3b). Build the stacked design the reader chose: traps T1, T2, T3, T6. Why: The strongest available stack is four independent judgement points. T1+T2 form one guard (the websocket admission path) but hide two decisions: the CheckOrigin override at client.go:37 must be replaced with a real check, and the /api/events route is registered outside middleWareFunc (server.go:199), so a fix placed only in the shared middleware leaves the reported socket open; their dismiss reasons differ (the deliberate multi-domain comment versus 'ServeWs does its own auth'). T3 is a separate site and a separate decision: the raw RequestURI path policy at server.go:287-291 must be evaluated on the decoded, query-free path, otherwise any path-gated origin check copied from it inherits the percent-encoded-path bypass the advisory names. T6 is a separate sink family: state-changing POSTs (send, release) have no origin validation at all, so a websocket-only fix still lets a foreign page trigger them; its dismiss reason ('CORS/preflight handles it, the API is open by design') is unlike the other two. That mix covers a deepseek-type (T2, T6), a mimo-type/hows-type (T3), and coupled values (the --api-cors origin, webroot and Origin-less clients that the T1 fix must keep working). T5 is a real fifth group but a concurrency race makes hidden tests flaky; T4 is kept as a fairness/conflict constraint rather than a scored trap because the only reachable OPTIONS handler returns a blank 200. If the harness only accepts advisory-named surfaces, the stack narrows to T1/T2 plus T3, which is still two independent edits in two packages. Follow the stacked-task rules appended at the end of this prompt; they add to the rules above.
- Host notes: Reader fairness risks (resolve each in the report's contracts or the tests): Origin-less clients are legitimate: gorilla only consults CheckOrigin when an Origin header is present, and scripts/proxies/CLI websocket clients normally send none. A rule that rejects missing Origin would refuse a legitimate input shape and break non-browser use. | The web UI itself must keep connecting: AppNotifications.vue:35 builds the socket URL from document.location.host and AppNotifications.vue:50 opens it with no headers; with --webroot the endpoint is Webroot+'api/events' (server/server.go:199), so a check hardcoding /api/events breaks webroot deployments. | Reverse-proxy deployments (Vite/nginx in front of Mailpit) have Origin = the public host and r.Host = the backend address; exact Origin == scheme://r.Host comparison refuses a legitimate deployment. | --api-cors is an existing supported flag, including a literal '*'; a security rule that refuses wildcard or configured cross-origin values contradicts a documented feature. | CORS preflight must stay credential-less (server/server.go:299, CHANGELOG.md:215); requiring auth or an Origin on OPTIONS breaks cross-origin API use. | The API is intentionally unauthenticated by default and is called by local scripts and CI without an Origin header or a JSON Content-Type; a blanket 'reject cross-origin/no-Origin POST' rule refuses legitimate use, and send.go:45-52 deliberately ignores Content-Type. | Browser clients cannot set an Authorization header on a WebSocket handshake (AppNotifications.vue:50; client.go:116 relies on r.BasicAuth()), so the websocket authenticates only via cached Basic credentials; a fix that requires a token header on the handshake breaks the UI.. Conflicts the reader found: The natural same-origin rule (compare the Origin host with r.Host) rejects the cross-origin UI deployment that the Access-Control-Allow-Origin policy at server/server.go:290-295 exists to support; an origin check must also admit the configured AccessControlAllowOrigin value and reverse-proxied public hosts, so a strict host equality fix breaks a must-keep-working configuration. | Requiring an Origin header, or credentials, on unsafe HTTP methods also catches CORS preflight, which browsers send without credentials; the OPTIONS exemption at server/server.go:299 has to survive any global origin/auth middleware or --api-cors breaks. | Replacing the global auth.UICredentials toggle with per-request credentials must keep both Send API auth modes working (server_test.go:336-414) while the websocket gate at server/websockets/client.go:115 still sees the real UI credentials; a naive fix that stops clearing the global changes send-API behaviour, and a fix that keeps clearing it leaves the websocket gate blind during the window.

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

## Environment (`tasks/stk-mailpit-ghsa8r62/environment/Dockerfile`)
- **Base and code.** A small official base image. The repo goes into `/app` at the pinned commit,
  and `/app/.git` is then deleted.
- **Offline.** Install every dependency, tool and service the project and tests need; nothing may
  be downloaded at test time. Services start from `test.sh`.
- **Packages:** `patch`, `curl`, `ca-certificates`, `bash`, `git`.
- **Agent layer.** Append `common/trial/claude-code.Dockerfile.snippet` unchanged at the end.
- **No test code in the image.** The agent shares the container. Pre-build against stubs; `test.sh`
  copies the real tests in at grading time.
- **Project tests.** The project's own tests for the affected area must pass in the image at the
  pinned commit.
- **No leaked regression tests.** The pinned commit must not already contain the advisory's
  regression tests (check `git log` between the pinned and fix commits).

## Report to the solver (`tasks/stk-mailpit-ghsa8r62/instruction.md`)
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

## Tests (`tasks/stk-mailpit-ghsa8r62/tests/`)
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
- **Wrong-fix patches** go in `build/stk-mailpit-ghsa8r62/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/stk-mailpit-ghsa8r62/`:**
- `instruction.md`;
- `task.toml`, from `common/builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/stk-mailpit-ghsa8r62/manifest.json`:**
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

**Also in `build/stk-mailpit-ghsa8r62/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `common/builder/templates/` and `common/trial/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I common/gate/gate.py stk-mailpit-ghsa8r62 --only static
python3 -I common/gate/gate.py stk-mailpit-ghsa8r62 --only nop
python3 -I common/gate/gate.py stk-mailpit-ghsa8r62 --only oracle
python3 -I common/gate/gate.py stk-mailpit-ghsa8r62 --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/stk-mailpit-ghsa8r62/`;
  - edit only `tasks/stk-mailpit-ghsa8r62/`, `build/stk-mailpit-ghsa8r62/` and, for pattern B, the register;
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


## Stacked task: additional rules

You are building a **stacked** task: one checkout with several independent places where a protection
is missing. The reader's record lists them, with evidence: `/home/mara/cwe-bench/pipelines/stacking/out/reader/h3-ghsa-8r62-w5wh-fc5m.json`. Verify each trap on the
pinned code before you rely on it. The record is a lead.

**The stack**
1. **At least 3 independent concepts.** If one guard or one fix site would close two traps, they are
   ONE concept. Count your reference fix's independent edit sites, not advisories or routes.
2. **Each concept is hard on its own** for at least one target model (tier hard or xhard in the
   record).
3. **Both models covered.** At least one DeepSeek-type trap (a route where the protection never
   existed, with a plausible reason to dismiss it) and at least one MiMo-type trap (a coupled
   must-keep-working value next to a hidden one, or a how-type mechanism).
4. **No single trap carries the task.** A fix that closes every concept except the hardest must still
   fail. Add one `security_fail` check patch per concept (a fix that misses only that concept).
5. **A coupled must-keep-working value next to every hidden route**, tested functionally. The
   report covers it ONLY through the general keep-working sentence ("everything that works today
   keeps working"); it never names or describes the value. If a security rule, read literally, would
   forbid that value, reword the security rule over its protected outcome instead of adding an
   exception that names the value.
6. **Effort budget.** A careful engineer who knows where to look fixes everything in about 45-60
   minutes. If the stack needs more, drop the weakest concept.

**The report**
7. **One general property per distinct protection, and nothing per trap.** Never one per route, and
   never a count. Describe no surface, as the build template already requires. If the stack spans two
   protections, state two properties, each over its protected data or outcome.
   - **The one-bug test:** for every sentence of the report, ask "would this sentence be here if the
     task had only the advisory's own route?" If not, delete it. That covers forms ("in every form it
     can be named"), timing ("and again when the call connects"), sources ("whichever response
     supplies it"), encodings, aliases, example values in keep-working lines, and lists of resources.
   - Only the advisory's own route may be shown, in the impact example.
   - General contracts that hold for every route stay: the refusal form (for example "a client
     error, with no effect"), an operator opt-in, "keep every legitimate use working".
   - Keep the report short: the goal in a few lines, the property, the general contracts.
   - After the build, `pipelines/stacking/4-listing/run_listing_check.sh` classifies every hidden trap against the
     report. One NAMED hidden trap, or more than one DESCRIBED hidden trap, is a FAIL. Once the
     reviewer is calibrated (`pipelines/stacking/4-listing/LISTING_ENFORCE`), a FAIL means the task is not marked sound.

**History rules** (by the record's `pattern`)
8. **H3a / H3b (fix of a fix):**
   - pin the parent of the earlier fix A's first commit;
   - the reference fix is the complete fix (A plus the later fix B, or an equivalent);
   - add `checks/upstream_first_fix.patch`, which is A's fix applied alone, with `expect: fail`, so
     upstream's first fix is proven to be a wrong fix.
9. **H3c (masking):** the masked bug's security test must fail on the pinned code through its own
   route, without relying on the masking bug, so the gate's nop stage holds.
10. **Conflicting fixes (F8):** when the record names a pair where the natural fix for one trap breaks
    a value another needs, test that value functionally. The report covers it only through the
    general keep-working sentence, as in rule 5; never by naming the value.
11. **Dependency-bump fixes (F5):** when upstream fixed a bug by upgrading a dependency, the task must
    be fixable inside the repository. The reference proves it. The report never asks for an upgrade,
    and the solver works offline.
12. **Recall check (every pattern):** add `checks/upstream_fix.patch` (every published fix commit for
    the stacked advisories, applied together) with `expect: fail`. If it passes, the stack adds
    nothing beyond what upstream shipped. Rework the design.

**The control task**
13. Also build `<slug>-control`: the same pinned code, the same report, but only the advisory's own
    route (the trap the report leads to) in the security tests and the reference. It isolates the
    effect of stacking from the effect of the host. The two `instruction.md` files stay byte-identical
    for the task's whole life: any later change to the stacked report (fairfix, upgrade) is copied to
    the control. `check_stack.py` checks it.

**Manifest:** add a `stacking` block containing:
- `pattern`;
- `reader_record`;
- `concepts` (groups of trap ids);
- `history`: advisories A and B with their fix commits, `pinned_commit` and its rule;
- `score_at_build`: copy the `score` of your job's row in `pipelines/stacking/out/stack_scores_ds.tsv` (do NOT run
  `score_stack.py`: it rewrites the shared selection file);
- `control_slug`.

**Exact manifest fields the static conformance check reads (step 5, `pipelines/stacking/3-build-gate/check_stack.py`). Emit these literally — the field NAMES and VALUES below must match, or the build is rejected before the container gate:**

`manifest.traps[]` — one object per trap:
- `id` (string) — referenced by `stacking.concepts`.
- `type` — exactly one of `"deepseek"`, `"mimo"`, or `"both"`. At least one trap must be `"deepseek"` or `"both"`, and at least one must be `"mimo"` or `"both"`.
- `origin` — for a hidden route, one of `"uncovered_upstream"`, `"published_fix_far_site"`, `"injection_room"`. Any trap with such an `origin` must also carry `coupled_functional_tests`: a non-empty list of the functional-test ids that keep its must-keep-working value honest.

`manifest.stacking` — an object with exactly these keys (all required):
- `pattern` — e.g. `"H3a"`, `"H3b1"`, `"H3b2"`, `"H4"`.
- `concepts` — a list of **at least 3** groups; each group is a list of trap `id`s forming one independent concept. Every id must exist in `manifest.traps`.
- `history`, `control_slug`, `score_at_build`, `reader_record` — as described above.

`manifest.patch_checks[]` — in addition to the task's normal patch checks, add:
- **One per concept** (a fix that closes every concept EXCEPT this one, so its security tests still fail):
  `{ "patch": "checks/miss_<concept>.patch", "kind": "security_fail", "expect": "security_fail", "misses": [<exactly this concept's trap ids>] }`.
  `misses` must be non-empty and be a subset of that concept's trap id group; one such check is required for every group in `stacking.concepts`.
- **Recall (always):** `{ "patch": "checks/upstream_fix.patch", "expect": "security_fail" }` — all published fix commits for the stacked advisories applied together.
- **Recall (H3a and every H3b variant):** also `{ "patch": "checks/upstream_first_fix.patch", "expect": "security_fail" }` — the earlier fix A applied alone.

Every `checks/*.patch` named above must be a real file in the task's `checks/` directory (the container gate then runs each with its `expect`ed outcome). A concept with no `security_fail` miss-check, a trap with no `type`, or a missing recall check/file each fails the conformance check.

**Report back:** also give the concept count, the DeepSeek-type and MiMo-type trap ids, the result of
each history check patch, and the control task's gate result.

Stacked task slug: `stk-mailpit-ghsa8r62`. Control task slug: `stk-mailpit-ghsa8r62-control`. Manifest `stacking.reader_record`: `pipelines/stacking/out/reader/h3-ghsa-8r62-w5wh-fc5m.json`.
