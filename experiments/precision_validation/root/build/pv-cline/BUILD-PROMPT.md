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

Project root: `/home/mara/cwe-bench/precision_validation/root`. Task: `pv-cline`. Pattern: `A`. Track: `injected`.

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
- Advisory: ["GHSA-3CJ3-HQCR-G934", "CVE-2026-59723"]; cline/cline; CWE-346 origin validation error / cross-site WebSocket hijacking (missing Origin and Host allowlist on a localhost control socket)
- Pinned (vulnerable) commit: unknown (parent of d09270940f5746f288cfc4a5039b46a2f4d5d01e; parent_commit field is null). Published fix: d09270940f5746f288cfc4a5039b46a2f4d5d01e.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "7872",
 "advisory_ids": [
  "GHSA-3CJ3-HQCR-G934",
  "CVE-2026-59723"
 ],
 "repo": "cline/cline",
 "pinned_commit": "unknown (parent of d09270940f5746f288cfc4a5039b46a2f4d5d01e; parent_commit field is null)",
 "fix_commits": [
  "d09270940f5746f288cfc4a5039b46a2f4d5d01e"
 ],
 "trust_decision": {
  "summary": "The Cline Hub dashboard server decides whether a browser may open the /browser WebSocket (which drives sessions, provider settings, desktop commands and hub restart). At the pinned commit it checks only the optional roomSecret query parameter and never checks Origin or Host. The fix adds a server-wide gate that checks Host and Origin against an allowlist built from PUBLIC_URL, the bind host and loopback aliases.",
  "evidence": [
   "apps/cline-hub/src/server.ts:62-65",
   "apps/cline-hub/src/server.ts:87-99",
   "apps/cline-hub/src/server.ts:126-214",
   "fix.diff:118-132",
   "fix.diff:625-638"
  ]
 },
 "landing_point": {
  "where": "apps/cline-hub/src/server.ts:87",
  "why": "The advisory names the `/browser` endpoint, and this branch is the only WebSocket upgrade in the dashboard. Its only guard is the roomSecret check at apps/cline-hub/src/server.ts:62-65."
 },
 "fix_sites": [
  {
   "where": "apps/cline-hub/src/server.ts:79",
   "entry_point": "Dashboard HTTP fetch handler, every request (Bun.serve fetch): a new server-wide gate before routing, covering the WebSocket upgrade at /browser, unsafe methods and unknown paths (fix.diff:118-132)",
   "module_kind": "http_handler"
  },
  {
   "where": "apps/cline-hub/src/server.ts:87",
   "entry_point": "GET /browser WebSocket upgrade: the old roomSecret-only check is removed and moved into the gate (fix.diff:139-142)",
   "module_kind": "http_handler"
  },
  {
   "where": "fix.diff:79-98",
   "entry_point": "Dashboard HTTP fetch handler: a new public-route allowlist (/version, /health, /config.json, /api/marketplace/catalog, icons, /assets/*, webview SPA routes from apps/cline-hub/src/server/http.ts:58-82) that skips the gate for safe-method GETs",
   "module_kind": "http_handler"
  },
  {
   "where": "fix.diff:517-650",
   "entry_point": "New module apps/cline-hub/src/server/browser-auth.ts (allowedBrowserOrigins, allowedBrowserHosts, requiresBrowserRequestAuth, isAuthorizedBrowserRequest), reached from the fetch gate",
   "module_kind": "auth_helper_new_file"
  },
  {
   "where": "apps/cline-hub/src/options.ts:50",
   "entry_point": "Server startup via resolveClineHubServerOptions (env PUBLIC_URL, HOST, CLINE_HUB_DASHBOARD_PORT): normalizePublicUrl now adds the dashboard port to localhost/IP PUBLIC_URLs that lack one, so the derived allowed origin matches the browser's real origin (fix.diff:15-17, 25-36)",
   "module_kind": "config_loader"
  },
  {
   "where": "apps/cline-hub/src/options.ts:88-96",
   "entry_point": "buildInviteUrl, called at startup from apps/cline-hub/src/server/deps.ts:9: always normalises through URL now, so the invite URL equals the normalised public origin (fix.diff:38-48)",
   "module_kind": "config_loader"
  }
 ],
 "O1_entry_points": 1,
 "O2_out_of_scope_site": {
  "kind": "defaults_or_merge_route",
  "where": "apps/cline-hub/src/options.ts:28-52 (normalizePublicUrl default/normalisation of PUBLIC_URL; fixed at fix.diff:15-17,25-36)"
 },
 "O3_reason_to_dismiss": "options.ts is env-parsing and startup code with no auth logic, and the advisory is about a WebSocket handler. A solver would not expect that the PUBLIC_URL normalisation has to change for an origin allowlist to accept the legitimate dashboard (for example PUBLIC_URL=http://<tailscale-ip> with port 8787).",
 "O4_distance": {
  "files": 3,
  "packages": 1,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "The same-origin dashboard must keep working. The SPA and its static assets load via GETs with no Origin header. The WebSocket must accept localhost, 127.0.0.1 and [::1] aliases on a local bind, and the PUBLIC_URL/tunnel origin plus the explicit bind origin on a 0.0.0.0 bind with ROOM_SECRET. Origins with default ports 80/443 have no port. An over-broad fix (requiring Origin on every request, or allowing only the exact PUBLIC_URL origin) breaks page load or the alias/tunnel connections.",
  "where": "apps/cline-hub/src/server.ts:80-118; apps/cline-hub/src/server/http.ts:58-82; apps/cline-hub/src/options.ts:28-52; fix.diff:185-243"
 },
 "O6_input_shapes": [
  "Origin header absent, empty, the literal \"null\", or not a URL (fix.diff:359-375)",
  "Origin with a foreign host, a wrong port or a wrong scheme (http vs https) (fix.diff:364-366)",
  "Host header absent, empty, foreign or on a wrong port, which also covers DNS rebinding (fix.diff:377-393)",
  "Loopback aliases localhost / 127.0.0.1 / [::1], with IPv6 bracket formatting (fix.diff:548-550, 585-589)",
  "Default protocol ports 80/443, which are omitted from origin and host forms (fix.diff:552-572)",
  "Non-local bind (0.0.0.0) with roomSecret: origin check plus secret (fix.diff:395-445)",
  "Any WebSocket upgrade path or unsafe HTTP method, not just /browser (fix.diff:615-623)",
  "PUBLIC_URL given as a bare IP/localhost without a port (fix.diff:32-36)"
 ],
 "O7_producer": {
  "kind": "config_loader",
  "where": "apps/cline-hub/src/options.ts:28-52 (normalizePublicUrl), exported via apps/cline-hub/src/server/deps.ts:7-9",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [],
 "O8b_injection_room": [
  {
   "where": "apps/cline-hub/src/server.ts:100-117",
   "sibling": "A second state-changing HTTP route next to /config.json and /api/marketplace/catalog (for example a POST that saves provider settings or restarts the hub) that calls the same handlers as the WebSocket frames at apps/cline-hub/src/server.ts:157-213.",
   "why_realistic": "The dashboard already exposes plain HTTP API routes in this fetch handler. A maintainer adding an HTTP route for a non-WebSocket client would copy that pattern, and the only auth idiom at the pinned commit is the per-route roomSecret check at apps/cline-hub/src/server.ts:62-65."
  },
  {
   "where": "apps/cline-hub/src/server.ts:87-99",
   "sibling": "A second WebSocket upgrade path (for example a read-only event/stream socket) that calls server.upgrade without the /browser guard.",
   "why_realistic": "Bun.serve handles all upgrades in this one fetch function. A maintainer adding a socket for a narrower feature could reasonably skip the guard as 'read-only'."
  }
 ],
 "O9_family": "CWE-346 origin validation error / cross-site WebSocket hijacking (missing Origin and Host allowlist on a localhost control socket)",
 "O9_dos": false,
 "O10_build": {
  "language": "TypeScript",
  "toolchain": "Bun (Bun.serve runtime) with a bun workspace; vitest via `bunx vitest run --config vitest.config.ts` (apps/cline-hub/package.json:15); workspace deps @cline/core, @cline/llms, @cline/shared",
  "services": [],
  "offline_after_build": true,
  "project_tests": "apps/cline-hub/src/server/http.test.ts, marketplace.test.ts, connectors.test.ts and user-instructions.test.ts exist. There is no browser-auth test at the pinned commit. apps/cline-hub/src/validate-options.ts is a smoke script (`smoke:options`, apps/cline-hub/package.json:14). The fix's tests are unit tests on pure functions over Request/URL (fix.diff:151-510), so they run without a hub."
 },
 "O11_fix_minutes": 40,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "A",
 "j": {
  "j_multi_site": 0,
  "j_sites_touched": "apps/cline-hub/src/server.ts, apps/cline-hub/src/server/browser-auth.ts (new), apps/cline-hub/src/options.ts (plus the smoke script apps/cline-hub/src/validate-options.ts)",
  "j_sibling_sites": "no",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 0,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Inside the /browser branch only, compare the Origin header to publicUrl (or to any loopback hostname). This misses the Host check, the loopback aliases, default-port forms, the PUBLIC_URL port normalisation and other upgrade paths and methods."
 },
 "out_of_scope_notes": [
  "sdk/packages/core/src/hub/server/hub-websocket-server.ts:462-467 with :266-278: the core hub WebSocket accepts any loopback Origin on any port when no token is given. This is a different server and protection; not pursued.",
  "apps/examples/desktop-app/sidecar/server.ts:87: an example sidecar upgrades /transport with no visible Origin check. This is a different app and sink; not pursued."
 ],
 "unverified": [
  "Pinned commit hash: parent_commit is null in the candidate and the repo directory has no git metadata to read.",
  "Repo size in MB: not measured, since running du was out of scope. It is a large monorepo, so tiny_repo is unlikely, but this is not confirmed.",
  "O1 = 1: within the dashboard, only the /browser upgrade reaches the WebSocket sink at the pinned commit. The fix's generic unsafe-method and unknown-path gating protects routes that do not exist yet.",
  "Pattern A fit is weak. The scope is effectively one concept (Origin/Host allowlist) at one gate. The out-of-scope options.ts change is about keeping legitimate access working, not about closing a second route. Lessons-v1 says origin/host and protocol variants alone have not produced failures.",
  "Recall risk: published 2026-09-24, after this model's knowledge cutoff; how widely it is written up was not checked."
 ]
}
  ```
- Published fix sites:   - apps/cline-hub/src/server.ts:79 — entry point: Dashboard HTTP fetch handler, every request (Bun.serve fetch): a new server-wide gate before routing, covering the WebSocket upgrade at /browser, unsafe methods and unknown paths (fix.diff:118-132) [http_handler]
  - apps/cline-hub/src/server.ts:87 — entry point: GET /browser WebSocket upgrade: the old roomSecret-only check is removed and moved into the gate (fix.diff:139-142) [http_handler]
  - fix.diff:79-98 — entry point: Dashboard HTTP fetch handler: a new public-route allowlist (/version, /health, /config.json, /api/marketplace/catalog, icons, /assets/*, webview SPA routes from apps/cline-hub/src/server/http.ts:58-82) that skips the gate for safe-method GETs [http_handler]
  - fix.diff:517-650 — entry point: New module apps/cline-hub/src/server/browser-auth.ts (allowedBrowserOrigins, allowedBrowserHosts, requiresBrowserRequestAuth, isAuthorizedBrowserRequest), reached from the fetch gate [auth_helper_new_file]
  - apps/cline-hub/src/options.ts:50 — entry point: Server startup via resolveClineHubServerOptions (env PUBLIC_URL, HOST, CLINE_HUB_DASHBOARD_PORT): normalizePublicUrl now adds the dashboard port to localhost/IP PUBLIC_URLs that lack one, so the derived allowed origin matches the browser's real origin (fix.diff:15-17, 25-36) [config_loader]
  - apps/cline-hub/src/options.ts:88-96 — entry point: buildInviteUrl, called at startup from apps/cline-hub/src/server/deps.ts:9: always normalises through URL now, so the invite URL equals the normalised public origin (fix.diff:38-48) [config_loader]
- Uncovered routes to confirm (pattern B): none
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
- Append one row per route to `/home/mara/cwe-bench/precision_validation/root/build/audit/uncovered-routes.tsv`, using its existing
  header. Columns:
  - `task`, `repo`, `advisory`;
  - `trap_ref` (the manifest trap id only; no mechanism text, since the manifest holds the detail);
  - `real_upstream`;
  - `present_in_latest` (`yes`, `no` or `unknown`, from a read-only look at current upstream code if
    you can reach it);
  - `public_upstream_report`, `in_current_scope`, `built`, `note`;
  - `disclosure_status` (`pending client decision`).

## Environment (`tasks/pv-cline/environment/Dockerfile`)
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

## Report to the solver (`tasks/pv-cline/instruction.md`)
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

## Tests (`tasks/pv-cline/tests/`)
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
- **Wrong-fix patches** go in `build/pv-cline/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/pv-cline/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/pv-cline/manifest.json`:**
- `slug`, `candidate`;
- `pattern`: `A`;
- `builder_prompt_version`: `build-v1`;
- `"strict_gate": true`;
- `verified`: entry point, sites, routes, services, project tests run;
- `leak_terms`, `patch_checks`, `wrong_fix_catalogue`;
- `traps`: one entry per lever, with `shape`, `where` (file:line), `security_tests`,
  `coupled_functional_tests`, `security_fail_patch`, and `realistic_because` (for pattern B: "real,
  unmodified upstream code");
- `status`.

**Also in `build/pv-cline/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py pv-cline --only static
python3 -I builder/gate.py pv-cline --only nop
python3 -I builder/gate.py pv-cline --only oracle
python3 -I builder/gate.py pv-cline --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/pv-cline/`;
  - edit only `tasks/pv-cline/`, `build/pv-cline/` and, for pattern B, the register;
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
