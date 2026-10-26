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

Project root: `/home/mara/cwe-bench`. Task: `cline-s2`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: ["GHSA-3CJ3-HQCR-G934", "CVE-2026-59723"]; cline/cline; origin/host validation error on a browser-reachable local privileged endpoint (CWE-346; also CWE-1385 missing origin validation on WebSocket, with DNS rebinding/WS hijacking impact)
- Pinned (vulnerable) commit: 23c9bf1c05bfb116e843d18e1268304b00131e69. Published fix: d09270940f5746f288cfc4a5039b46a2f4d5d01e.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v2",
 "model": "deepseek-flash[1m]",
 "entry_id": "7872",
 "advisory_ids": [
  "GHSA-3CJ3-HQCR-G934",
  "CVE-2026-59723"
 ],
 "repo": "cline/cline",
 "pinned_commit": "23c9bf1c05bfb116e843d18e1268304b00131e69",
 "fix_commits": [
  "d09270940f5746f288cfc4a5039b46a2f4d5d01e"
 ],
 "trust_decision": {
  "summary": "At the pinned commit the dashboard listener trusts a request purely on the roomSecret query parameter, and trusts every request when no secret is set (the default local mode), so any web page can open ws://127.0.0.1:8787/browser and drive the privileged desktop-command socket; the published fix instead decides trust from the request's Host and Origin headers against an allowlist built from bindHost/port/publicUrl, evaluated for every request in the Bun.serve fetch entry, with public GET webview/static routes exempted.",
  "evidence": [
   "apps/cline-hub/src/server.ts:62-65",
   "apps/cline-hub/src/server.ts:78-79",
   "apps/cline-hub/src/server.ts:87-99",
   "apps/cline-hub/src/server.ts:118",
   "apps/cline-hub/src/server.ts:130-152",
   "apps/cline-hub/src/options.ts:33-51",
   "apps/cline-hub/src/server/deps.ts:7-9"
  ]
 },
 "landing_point": {
  "where": "apps/cline-hub/src/server.ts:87",
  "why": "The advisory names the /browser endpoint, which is the one route that calls server.upgrade (server.ts:97) and whose only gate is the roomSecret query check at server.ts:88-90."
 },
 "fix_sites": [
  {
   "where": "fix.diff:515-654",
   "entry_point": "every HTTP request and WebSocket upgrade on the dashboard listener (imported and called from server.ts fetch)",
   "module_kind": "new shared auth/origin-check module (apps/cline-hub/src/server/browser-auth.ts)"
  },
  {
   "where": "fix.diff:122-136",
   "entry_point": "Bun.serve fetch handler, before any route dispatch, so it covers the GET /browser upgrade and all HTTP routes",
   "module_kind": "HTTP/WS request handler"
  },
  {
   "where": "fix.diff:143-146",
   "entry_point": "GET /browser (WebSocket upgrade): the old roomSecret-only check is removed here",
   "module_kind": "HTTP/WS route handler"
  },
  {
   "where": "fix.diff:83-102",
   "entry_point": "all GET routes: PUBLIC_BROWSER_PATHS + /assets/ + isWebviewRoute exemption predicate consumed by the gate",
   "module_kind": "route classification helper inside the server module"
  },
  {
   "where": "fix.diff:19-21",
   "entry_point": "environment/CLI configuration: resolveClineHubServerOptions via apps/cline-hub/src/server/deps.ts:7 (`bun run src/server.ts`, `cline dashboard`)",
   "module_kind": "config loader / options parser (normalizePublicUrl)"
  },
  {
   "where": "fix.diff:29-40",
   "entry_point": "same config loader: isDefaultProtocolPort + shouldAddDashboardPortToPublicUrl used by normalizePublicUrl",
   "module_kind": "config loader / options parser"
  },
  {
   "where": "fix.diff:42-53",
   "entry_point": "buildInviteUrl, whose result becomes deps.ts:9 inviteUrl and the URL `cline dashboard` opens (apps/cli/src/commands/dashboard.ts:191-202)",
   "module_kind": "URL builder in the config module"
  },
  {
   "where": "fix.diff:659-678",
   "entry_point": "bun run smoke:options (apps/cline-hub/package.json:14) executing apps/cline-hub/src/validate-options.ts",
   "module_kind": "option-validation / smoke script"
  }
 ],
 "O1_entry_points": 1,
 "O2_out_of_scope_site": {
  "kind": "second_implementation",
  "where": "apps/examples/desktop-app/sidecar/server.ts:87 (fetch handler 69-110, websocket handler 112-148; command sink apps/examples/desktop-app/sidecar/commands.ts:713) - a second Bun.serve browser-to-desktop bridge that upgrades /transport with no Origin, Host or secret check and dispatches provider settings, MCP settings, git checkout and session-delete commands"
 },
 "O3_reason_to_dismiss": "It sits under apps/examples in a different workspace package (@cline/code), binds 127.0.0.1 with no room-secret concept, and the README calls the dashboard itself an example rather than a production admin tool, so a solver can reasonably call the sidecar out of the advisory's /browser scope; likewise the sdk hub server already has an origin check and only serves token-authenticated CLI/VS Code clients.",
 "O4_distance": {
  "files": 6,
  "packages": 3,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "PUBLIC_URL may legitimately omit the dashboard port: a tunnel hostname such as https://YOUR-TUNNEL.example must keep working unchanged (no port appended, origin matched as-is), while a bare localhost/IP PUBLIC_URL such as http://100.82.5.118 must gain the dashboard port so the browser's Origin http://100.82.5.118:8787 matches; an over-broad 'always append the port' rule breaks tunnel invites and an over-narrow origin allowlist 403s the legitimate Tailscale/IP dashboard.",
  "where": "apps/cline-hub/src/options.ts:33-51, apps/cline-hub/README.md:91-97"
 },
 "O6_input_shapes": [
  "Origin header absent, empty, unparseable ('null', 'not a url') or missing entirely",
  "Origin with a foreign host (http://evil.attacker.example.com)",
  "Origin with the right local host but another port (http://127.0.0.1:9999) or another scheme (https vs http)",
  "Host header absent, empty, foreign (evil.attacker.example.com), or right host with the wrong port",
  "Request kind: every WebSocket upgrade (any path) vs safe GET/HEAD/OPTIONS vs unsafe POST",
  "Route kind: public webview routes, /assets/*, /version, /health, /config.json, marketplace catalog vs privileged routes such as /browser",
  "roomSecret query parameter: absent, wrong, or present",
  "PUBLIC_URL shapes: bare localhost/IP with no port (port appended), tunnel hostname with no port (port not appended), and default protocol ports 80/443 (origins formatted without a port)"
 ],
 "O7_producer": {
  "kind": "config_loader",
  "where": "apps/cline-hub/src/options.ts:28-52 (normalizePublicUrl) -> apps/cline-hub/src/server/deps.ts:7-9 -> publicUrl consumed by the fix's allowlist (fix.diff:578-617 builds allowedBrowserOrigins/allowedBrowserHosts from bindHost/port/publicUrl); the same loader value is serialized to clients as browserConfig (apps/cline-hub/src/server/deps.ts:23-26) and into the invite URL (apps/cline-hub/src/server/deps.ts:9)",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "WebSocket upgrade on ws://127.0.0.1:3126/transport of the desktop-app sidecar, with no Origin/Host validation, reaching the same privileged command dispatcher",
   "where": "apps/examples/desktop-app/sidecar/server.ts:87-89",
   "reason_to_dismiss": "example app, localhost-only bind, no room-secret feature; the advisory names the dashboard",
   "distance": "different app and workspace package (apps/examples/desktop-app vs apps/cline-hub), 2 directory levels apart",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "Cross-origin POST /shutdown on the sidecar (no Origin check, no preflight-requiring content type) which triggers onShutdown and process.exit",
   "where": "apps/examples/desktop-app/sidecar/server.ts:91-106",
   "reason_to_dismiss": "same example-app argument, and it is a lifecycle endpoint rather than the command socket",
   "distance": "same file as the sidecar bridge, another app/package from the landing point",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "SDK hub websocket server accepts any localhost origin (any port, either scheme) when bound locally, so a page served by another local server can open the hub socket without the auth token",
   "where": "sdk/packages/core/src/hub/server/hub-websocket-server.ts:456-471 (isLocalHubOrigin at 266-278)",
   "reason_to_dismiss": "the hub endpoint already validates origins and its real clients (CLI, VS Code) authenticate with a bearer/subprotocol token; it is a different package and not the dashboard",
   "distance": "different package (sdk/packages/core) and a different transport (node:http + ws server.on('upgrade'))",
   "present_in_latest": "unknown",
   "latest_where": ""
  }
 ],
 "O8b_injection_room": [
  {
   "where": "apps/cline-hub/src/server.ts:78-119",
   "sibling": "an HTTP command route such as POST /api/desktop-command or POST /api/hub/restart next to the socket frames",
   "why_realistic": "the webview already exposes desktop commands and a Restart Hub button over the socket (server.ts:130-152, 212-214); a REST fallback for non-WS clients is a natural maintainer addition, and a fix that only guards the /browser branch leaves it open while the published gate (any unsafe method) closes it"
  },
  {
   "where": "apps/cline-hub/src/server.ts:75-119",
   "sibling": "a second WebSocket endpoint such as /events or /terminal that streams session data or accepts commands",
   "why_realistic": "the single Bun.serve listener already multiplexes HTTP and upgrade requests and the peer registry broadcasts state (server.ts:120-125); a second upgrade path would be added in the same handler, catching any fix that path-matches '/browser' instead of gating every upgrade"
  },
  {
   "where": "apps/cline-hub/src/server/deps.ts:7-9",
   "sibling": "a second consumer of publicUrl/roomSecret, e.g. GET /api/invite or a QR-code endpoint that re-serializes the invite URL",
   "why_realistic": "inviteUrl is already derived once from publicUrl and roomSecret and printed/opened by the CLI (apps/cli/src/commands/dashboard.ts:191-202); any such consumer re-exposes the same publicUrl whose port normalization the published fix adds in options.ts"
  }
 ],
 "O9_family": "origin/host validation error on a browser-reachable local privileged endpoint (CWE-346; also CWE-1385 missing origin validation on WebSocket, with DNS rebinding/WS hijacking impact)",
 "O9_dos": false,
 "O10_build": {
  "language": "TypeScript",
  "toolchain": "Bun (Bun.serve, bun workspaces, bun tsc) plus vitest; apps/cline-hub depends on workspace packages @cline/core, @cline/shared, @cline/llms with vitest aliases to sdk sources (apps/cline-hub/vitest.config.ts:9-27)",
  "services": [
   "local detached hub daemon spawned on 127.0.0.1 by ensureDetachedHubServer (apps/cline-hub/src/server/hub.ts:92-119); no external service",
   "network only for the /api/marketplace/catalog route (apps/cline-hub/src/server.ts:103-117), unrelated to the auth checks"
  ],
  "offline_after_build": true,
  "project_tests": "apps/cline-hub runs vitest in a node environment over src/**/*.test.ts (apps/cline-hub/package.json:15, apps/cline-hub/vitest.config.ts:29-32): http.test.ts, connectors.test.ts, marketplace.test.ts, user-instructions.test.ts at the pinned commit; there is no route/auth test until the fix adds browser-auth.test.ts, and those tests build plain Request/URL objects so they need no port or network."
 },
 "O11_fix_minutes": 60,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "apps/cline-hub/src/server.ts, apps/cline-hub/src/server/browser-auth.ts, apps/cline-hub/src/options.ts, apps/cline-hub/src/validate-options.ts",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Add an Origin (or localhost-name) check inside the /browser branch only, copying the SDK hub's isLocalHubOrigin, and never touch normalizePublicUrl, the public-route exemption, or the sidecar/hub sibling endpoints."
 },
 "out_of_scope_notes": [
  "Only read (never exercised) the sidecar example and the sdk hub websocket server, to compare the origin-check idiom; nothing outside the dashboard listener was run or probed.",
  "apps/cline-hub/src/webview/vite.config.ts:36-40 sets Access-Control-Allow-Origin: * and cors: true on the Vite dev server only; not pursued.",
  "No other HTTP/WS listener exists inside apps/cline-hub (apps/cline-hub/src/server/connectors.ts has no server); only the apps/examples and sdk packages add listeners."
 ],
 "unverified": [
  "Repository size in MB, so whether it crosses the giant_repo (1.5 GB) or tiny_repo (5 MB) threshold: no shell was available; the tree is a large multi-app monorepo but apps/cline-hub itself is one small app.",
  "present_in_latest / latest_where for every O8 route: no latest release was supplied for this screener run.",
  "Whether the advisory text is read as covering apps/examples/desktop-app and the sdk hub server; they are recorded as O2/O8 on the basis of the same mechanism (privileged browser-to-local websocket), not on advisory wording.",
  "Runtime offline check: the dashboard start path calls ensureDetachedHubServer (apps/cline-hub/src/server/hub.ts:92-119); not executed, so first-run network behaviour of the hub daemon is unconfirmed.",
  "Residual observation on the published fix, not a pinned-commit route: public GET paths stay exempt from the Host check (PUBLIC_BROWSER_PATHS includes /health and /config.json, fix.diff:83-94), so DNS rebinding could still read those responses; they are not routes into the privileged socket.",
  "O4 file and package counts are estimates of the import/launch chain, not a measured shortest path."
 ]
}
  ```
- Published fix sites:   - fix.diff:515-654 — entry point: every HTTP request and WebSocket upgrade on the dashboard listener (imported and called from server.ts fetch) [new shared auth/origin-check module (apps/cline-hub/src/server/browser-auth.ts)]
  - fix.diff:122-136 — entry point: Bun.serve fetch handler, before any route dispatch, so it covers the GET /browser upgrade and all HTTP routes [HTTP/WS request handler]
  - fix.diff:143-146 — entry point: GET /browser (WebSocket upgrade): the old roomSecret-only check is removed here [HTTP/WS route handler]
  - fix.diff:83-102 — entry point: all GET routes: PUBLIC_BROWSER_PATHS + /assets/ + isWebviewRoute exemption predicate consumed by the gate [route classification helper inside the server module]
  - fix.diff:19-21 — entry point: environment/CLI configuration: resolveClineHubServerOptions via apps/cline-hub/src/server/deps.ts:7 (`bun run src/server.ts`, `cline dashboard`) [config loader / options parser (normalizePublicUrl)]
  - fix.diff:29-40 — entry point: same config loader: isDefaultProtocolPort + shouldAddDashboardPortToPublicUrl used by normalizePublicUrl [config loader / options parser]
  - fix.diff:42-53 — entry point: buildInviteUrl, whose result becomes deps.ts:9 inviteUrl and the URL `cline dashboard` opens (apps/cli/src/commands/dashboard.ts:191-202) [URL builder in the config module]
  - fix.diff:659-678 — entry point: bun run smoke:options (apps/cline-hub/package.json:14) executing apps/cline-hub/src/validate-options.ts [option-validation / smoke script]
- Uncovered routes to confirm (pattern B):   - apps/examples/desktop-app/sidecar/server.ts:87-89 — WebSocket upgrade on ws://127.0.0.1:3126/transport of the desktop-app sidecar, with no Origin/Host validation, reaching the same privileged command dispatcher (reason to dismiss: example app, localhost-only bind, no room-secret feature; the advisory names the dashboard; still in latest: unknown)
  - apps/examples/desktop-app/sidecar/server.ts:91-106 — Cross-origin POST /shutdown on the sidecar (no Origin check, no preflight-requiring content type) which triggers onShutdown and process.exit (reason to dismiss: same example-app argument, and it is a lifecycle endpoint rather than the command socket; still in latest: unknown)
  - sdk/packages/core/src/hub/server/hub-websocket-server.ts:456-471 (isLocalHubOrigin at 266-278) — SDK hub websocket server accepts any localhost origin (any port, either scheme) when bound locally, so a page served by another local server can open the hub socket without the auth token (reason to dismiss: the hub endpoint already validates origins and its real clients (CLI, VS Code) authenticate with a bearer/subprotocol token; it is a different package and not the dashboard; still in latest: unknown)
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

## Environment (`tasks/cline-s2/environment/Dockerfile`)
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

## Report to the solver (`tasks/cline-s2/instruction.md`)
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

## Tests (`tasks/cline-s2/tests/`)
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
- **Wrong-fix patches** go in `build/cline-s2/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/cline-s2/`:**
- `instruction.md`;
- `task.toml`, from `common/builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/cline-s2/manifest.json`:**
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

**Also in `build/cline-s2/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `common/builder/templates/` and `common/trial/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I common/gate/gate.py cline-s2 --only static
python3 -I common/gate/gate.py cline-s2 --only nop
python3 -I common/gate/gate.py cline-s2 --only oracle
python3 -I common/gate/gate.py cline-s2 --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/cline-s2/`;
  - edit only `tasks/cline-s2/`, `build/cline-s2/` and, for pattern B, the register;
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
