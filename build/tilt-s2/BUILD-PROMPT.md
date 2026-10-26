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

Project root: `/home/mara/cwe-bench`. Task: `tilt-s2`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: ["GHSA-6M68-R693-78QX", "CVE-2026-55883", "GO-2026-5181"]; tilt-dev/tilt; missing authentication/authorization on a local HTTP + WebSocket API (cross-site WebSocket hijacking / CSRF; CWE-345, CWE-306)
- Pinned (vulnerable) commit: 65ddaecbdbe3bc733ddaed6ea471afb1ebd4307d. Published fix: 47393fba7f6ef5e305d5e814551feef8e4acbc0a.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v2",
 "model": "deepseek-flash[1m]",
 "entry_id": "16199",
 "advisory_ids": [
  "GHSA-6M68-R693-78QX",
  "CVE-2026-55883",
  "GO-2026-5181"
 ],
 "repo": "tilt-dev/tilt",
 "pinned_commit": "65ddaecbdbe3bc733ddaed6ea471afb1ebd4307d",
 "fix_commits": [
  "47393fba7f6ef5e305d5e814551feef8e4acbc0a"
 ],
 "trust_decision": {
  "summary": "Whether a request may read or mutate the Tilt HUD is decided by whether it carries the per-user session token (Tilt-Token cookie or X-Tilt-Token header) equal to EngineState.Token, plus an Origin check; at the pinned commit no HTTP HUD route decides anything and only the websocket's CheckOrigin guards /ws/view, accepting any request with no Origin header.",
  "evidence": [
   "internal/hud/server/server.go:84-94",
   "internal/hud/server/server.go:112",
   "internal/hud/server/websocket.go:49-56",
   "internal/hud/server/gorilla/origin.go:16-20",
   "internal/token/token.go:19-34",
   "internal/store/engine_state.go:89"
  ]
 },
 "landing_point": {
  "where": "internal/hud/server/websocket.go:49-56",
  "why": "The summary names the HUD websocket stream; CheckOrigin on the /ws/view upgrader is the only guard on that route, and it falls back to CheckSameOrigin, which returns true when the Origin header is absent."
 },
 "fix_sites": [
  {
   "where": "internal/hud/server/server.go:84",
   "entry_point": "GET /api/view",
   "module_kind": "HUD HTTP handler route"
  },
  {
   "where": "internal/hud/server/server.go:85",
   "entry_point": "GET /api/dump/engine",
   "module_kind": "HUD HTTP handler route"
  },
  {
   "where": "internal/hud/server/server.go:86",
   "entry_point": "POST /api/analytics",
   "module_kind": "HUD HTTP handler route"
  },
  {
   "where": "internal/hud/server/server.go:87",
   "entry_point": "POST /api/analytics_opt",
   "module_kind": "HUD HTTP handler route"
  },
  {
   "where": "internal/hud/server/server.go:88",
   "entry_point": "POST /api/trigger",
   "module_kind": "HUD HTTP handler route"
  },
  {
   "where": "internal/hud/server/server.go:89",
   "entry_point": "POST /api/override/trigger_mode",
   "module_kind": "HUD HTTP handler route"
  },
  {
   "where": "internal/hud/server/server.go:91",
   "entry_point": "GET /api/snapshot/{snapshot_id}",
   "module_kind": "HUD HTTP handler route"
  },
  {
   "where": "internal/hud/server/server.go:92",
   "entry_point": "GET /api/websocket_token",
   "module_kind": "HUD HTTP handler route (CSRF token hand-out)"
  },
  {
   "where": "internal/hud/server/server.go:94",
   "entry_point": "POST /api/set_tiltfile_args",
   "module_kind": "HUD HTTP handler route"
  },
  {
   "where": "internal/hud/server/websocket.go:49-56",
   "entry_point": "GET /ws/view",
   "module_kind": "websocket upgrader CheckOrigin"
  },
  {
   "where": "internal/hud/server/controller.go:163",
   "entry_point": "ANY /proxy/*",
   "module_kind": "web-router prefix handler around the kubectl apiserver proxy"
  },
  {
   "where": "internal/hud/server/controller.go:160",
   "entry_point": "ANY /debug/* on the web listener",
   "module_kind": "pprof mux mount"
  },
  {
   "where": "internal/hud/server/controller.go:144",
   "entry_point": "ANY /debug/* on the apiserver listener",
   "module_kind": "pprof mux mount"
  },
  {
   "where": "internal/hud/server/server.go:109-116",
   "entry_point": "GET / (every SPA asset path)",
   "module_kind": "cookie-setting wrapper around the asset server"
  },
  {
   "where": "internal/cli/utils.go:21-42",
   "entry_point": "tilt dump view|engine, tilt tree, tilt trigger, tilt snapshot create",
   "module_kind": "CLI HTTP client wrapper (apiGet / apiPostJson)"
  },
  {
   "where": "fix.diff:44-54",
   "entry_point": "same CLI commands (loadToken helper)",
   "module_kind": "new CLI credential loader in internal/cli"
  },
  {
   "where": "internal/hud/server/gorilla/origin.go:16-26",
   "entry_point": "GET /ws/view",
   "module_kind": "vendored origin-check helper (deleted by the fix)"
  },
  {
   "where": "fix.diff:271-295",
   "entry_point": "all HUD routes",
   "module_kind": "new originCheck middleware, installed at internal/hud/server/server.go:74"
  },
  {
   "where": "fix.diff:317-341",
   "entry_point": "all HUD routes and /proxy",
   "module_kind": "new requireToken middleware on HeadsUpServer"
  },
  {
   "where": "internal/cli/flags.go:66",
   "entry_point": "tilt up --host help text",
   "module_kind": "CLI flag definition"
  },
  {
   "where": "internal/cli/flags.go:72",
   "entry_point": "tilt snapshot view --host help text",
   "module_kind": "CLI flag definition"
  }
 ],
 "O1_entry_points": 13,
 "O2_out_of_scope_site": {
  "kind": "second_implementation",
  "where": "internal/snapshots/server.go:61-78"
 },
 "O3_reason_to_dismiss": "It is a different opt-in command (tilt snapshot view) serving a static file the developer chose to publish, with no live engine state and no session token in that process, so a solver can argue it was never part of the HUD server the advisory protects.",
 "O4_distance": {
  "files": 15,
  "packages": 7,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "tilt logs dials /ws/view with no csrf query parameter and no Origin header, relying on the CheckSameOrigin fallback; removing that fallback without teaching this client a token breaks 'tilt logs -f' (the published fix does not update it).",
  "where": "internal/hud/client/log_streamer.go:36-45"
 },
 "O6_input_shapes": [
  "session token in the X-Tilt-Token request header",
  "session token in the Tilt-Token cookie",
  "websocket csrf token in the ?csrf= query parameter (the only shape /ws/view accepts)",
  "Origin header absent (allowed), present and equal to Host (allowed), present and different (rejected)",
  "GET requests (apiGet) and JSON POST requests (apiPostJson) from the CLI",
  "TILT_DISABLE_HUD_AUTH=1 environment bypass"
 ],
 "O7_producer": {
  "kind": "config_loader",
  "where": "internal/token/token.go:19-34",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "GET / on the HUD catch-all handler sets Tilt-Token to the live session token for any unauthenticated caller, so requireToken can be satisfied by anyone who can reach the port",
   "where": "internal/hud/server/server.go:109-116",
   "reason_to_dismiss": "The browser SPA needs the cookie on first page load and a cross-site page cannot read the response because of the same-origin policy, so it is not a token disclosure under the advisory's browser threat model",
   "distance": "same package and same file as the route registration the fix touches",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "The apiserver listener's non-/debug prefixes (/apis, /metrics, /healthz, /livez, /readyz, /openapi, /swagger, /version) carry no HUD token; only /debug was wrapped",
   "where": "internal/hud/server/controller.go:134-144",
   "reason_to_dismiss": "That listener binds to 127.0.0.1 in the tilt-apiserver builder and /apis already requires the apiserver bearer token, so it is not remotely reachable",
   "distance": "same function as the landing point's controller hunk",
   "present_in_latest": "unknown",
   "latest_where": ""
  }
 ],
 "O8b_injection_room": [
  {
   "where": "internal/snapshots/server.go:61-78",
   "sibling": "A token-gated route on the snapshot viewer's own ServeMux (e.g. /api/snapshot/local or an /api/view alias)",
   "why_realistic": "It reuses the same embedded asset server, serves the same serialized webview payload, and listens on the same --host flag (internal/cli/snapshot.go:127-128), so a maintainer treating it as 'the HUD in snapshot mode' would plausibly add the gate there."
  },
  {
   "where": "internal/hud/client/log_streamer.go:36-45",
   "sibling": "Sending the session token or fetched csrf token on the websocket Dial",
   "why_realistic": "It is the only other consumer of /ws/view in the tree; whoever tightens CheckOrigin must touch it, and the published fix shows exactly the omission a maintainer would make."
  },
  {
   "where": "internal/hud/server/controller.go:134-144",
   "sibling": "Another sensitive PathPrefix mounted on the apiRouter (or on the webRouter) without the loopback/requireToken wrapper",
   "why_realistic": "The router is a flat list of mounts; the fix added loopbackOnly to /debug only, so adding e.g. /metrics or /config the same way is an easy, natural sibling."
  },
  {
   "where": "internal/cli/openapi.go:108-110",
   "sibling": "A second ProvideHeadsUpServerController construction wired to an empty &server.HeadsUpServer{} with a nil store",
   "why_realistic": "This already exists (the headless server for 'tilt openapi'); a new middleware that reads s.store would nil-panic here, exactly as requireToken would on /proxy."
  }
 ],
 "O9_family": "missing authentication/authorization on a local HTTP + WebSocket API (cross-site WebSocket hijacking / CSRF; CWE-345, CWE-306)",
 "O9_dos": false,
 "O10_build": {
  "language": "Go",
  "toolchain": "Go 1.25.5 (go.mod:3) with vendored modules; go test -mod vendor -timeout 100s ./... (Makefile:26)",
  "services": [],
  "offline_after_build": true,
  "project_tests": "Unit tests only for this area: internal/hud/server/{server_test.go,websocket_test.go,apiserver_test.go} (httptest and memconn, no cluster), internal/cli/{trigger_test.go,get_test.go}, internal/hud/client/log_streamer_test.go; the ./integration package needs Docker/kind but does not cover these handlers."
 },
 "O11_fix_minutes": 60,
 "O12_red_flags": [],
 "O13_recall_risk": "low",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "internal/cli/flags.go, internal/cli/utils.go, internal/hud/server/controller.go, internal/hud/server/gorilla/origin.go (deleted), internal/hud/server/server.go, internal/hud/server/websocket.go",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Make CheckOrigin require the csrf token (or reject a missing Origin) and stop, leaving the nine /api routes, /proxy, /debug, the snapshot viewer and the tilt logs client untouched."
 },
 "out_of_scope_notes": [
  "The fix diff also removes unrelated vendor/modules.txt entries (backoff/v4, easyjson, josharian/intern); that is vendor drift unrelated to the HUD auth change and was not pursued."
 ],
 "unverified": [
  "repo size in MB could not be measured (no shell); assumed between 5 MB and 1.5 GB so neither tiny_repo nor giant_repo is flagged",
  "whether the snapshot-view server is considered inside the advisory's property is a judgement call; recorded as the O2 site with a dismissal argument",
  "no network access, so O13 recall could not be checked against advisory write-ups",
  "no build or test was run (reading and searching only)"
 ]
}
  ```
- Published fix sites:   - internal/hud/server/server.go:84 — entry point: GET /api/view [HUD HTTP handler route]
  - internal/hud/server/server.go:85 — entry point: GET /api/dump/engine [HUD HTTP handler route]
  - internal/hud/server/server.go:86 — entry point: POST /api/analytics [HUD HTTP handler route]
  - internal/hud/server/server.go:87 — entry point: POST /api/analytics_opt [HUD HTTP handler route]
  - internal/hud/server/server.go:88 — entry point: POST /api/trigger [HUD HTTP handler route]
  - internal/hud/server/server.go:89 — entry point: POST /api/override/trigger_mode [HUD HTTP handler route]
  - internal/hud/server/server.go:91 — entry point: GET /api/snapshot/{snapshot_id} [HUD HTTP handler route]
  - internal/hud/server/server.go:92 — entry point: GET /api/websocket_token [HUD HTTP handler route (CSRF token hand-out)]
  - internal/hud/server/server.go:94 — entry point: POST /api/set_tiltfile_args [HUD HTTP handler route]
  - internal/hud/server/websocket.go:49-56 — entry point: GET /ws/view [websocket upgrader CheckOrigin]
  - internal/hud/server/controller.go:163 — entry point: ANY /proxy/* [web-router prefix handler around the kubectl apiserver proxy]
  - internal/hud/server/controller.go:160 — entry point: ANY /debug/* on the web listener [pprof mux mount]
  - internal/hud/server/controller.go:144 — entry point: ANY /debug/* on the apiserver listener [pprof mux mount]
  - internal/hud/server/server.go:109-116 — entry point: GET / (every SPA asset path) [cookie-setting wrapper around the asset server]
  - internal/cli/utils.go:21-42 — entry point: tilt dump view|engine, tilt tree, tilt trigger, tilt snapshot create [CLI HTTP client wrapper (apiGet / apiPostJson)]
  - fix.diff:44-54 — entry point: same CLI commands (loadToken helper) [new CLI credential loader in internal/cli]
  - internal/hud/server/gorilla/origin.go:16-26 — entry point: GET /ws/view [vendored origin-check helper (deleted by the fix)]
  - fix.diff:271-295 — entry point: all HUD routes [new originCheck middleware, installed at internal/hud/server/server.go:74]
  - fix.diff:317-341 — entry point: all HUD routes and /proxy [new requireToken middleware on HeadsUpServer]
  - internal/cli/flags.go:66 — entry point: tilt up --host help text [CLI flag definition]
  - internal/cli/flags.go:72 — entry point: tilt snapshot view --host help text [CLI flag definition]
- Uncovered routes to confirm (pattern B):   - internal/hud/server/server.go:109-116 — GET / on the HUD catch-all handler sets Tilt-Token to the live session token for any unauthenticated caller, so requireToken can be satisfied by anyone who can reach the port (reason to dismiss: The browser SPA needs the cookie on first page load and a cross-site page cannot read the response because of the same-origin policy, so it is not a token disclosure under the advisory's browser threat model; still in latest: unknown)
  - internal/hud/server/controller.go:134-144 — The apiserver listener's non-/debug prefixes (/apis, /metrics, /healthz, /livez, /readyz, /openapi, /swagger, /version) carry no HUD token; only /debug was wrapped (reason to dismiss: That listener binds to 127.0.0.1 in the tilt-apiserver builder and /apis already requires the apiserver bearer token, so it is not remotely reachable; still in latest: unknown)
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

## Environment (`tasks/tilt-s2/environment/Dockerfile`)
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

## Report to the solver (`tasks/tilt-s2/instruction.md`)
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

## Tests (`tasks/tilt-s2/tests/`)
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
- **Wrong-fix patches** go in `build/tilt-s2/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/tilt-s2/`:**
- `instruction.md`;
- `task.toml`, from `common/builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/tilt-s2/manifest.json`:**
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

**Also in `build/tilt-s2/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `common/builder/templates/` and `common/trial/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I common/gate/gate.py tilt-s2 --only static
python3 -I common/gate/gate.py tilt-s2 --only nop
python3 -I common/gate/gate.py tilt-s2 --only oracle
python3 -I common/gate/gate.py tilt-s2 --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/tilt-s2/`;
  - edit only `tasks/tilt-s2/`, `build/tilt-s2/` and, for pattern B, the register;
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
