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

Project root: `/home/mara/cwe-bench`. Task: `rsdoctor-access-control-inj`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: GHSA-JMG2-RCXH-W8Q3 / CVE-2026-61782 - web-infra-dev/rsdoctor - missing access control / exposure of a local dev server (CWE-200; DNS-rebinding and cross-origin reads via wildcard CORS, all-interfaces bind, unauthenticated WebSocket). Who may reach the Rsdoctor report server (HTTP API, static client, open-in-editor, WebSocket API): at the pinned commit nobody decides. It listens on 
- Pinned (vulnerable) commit: 2c413f7030229b0edd2e26fecbc1ec285e2c7116. Published fix: 602eb306a49b6d19c4c1ea9d8ee0f8caab9e208f.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "12254",
 "advisory_ids": [
  "GHSA-JMG2-RCXH-W8Q3",
  "CVE-2026-61782"
 ],
 "repo": "web-infra-dev/rsdoctor",
 "pinned_commit": "parent of 602eb306a49b6d19c4c1ea9d8ee0f8caab9e208f (parent_commit not given; tree at /home/mara/screen4/hosts/12254/repo)",
 "fix_commits": [
  "602eb306a49b6d19c4c1ea9d8ee0f8caab9e208f",
  "e9aaef21f85becfe43a46f716509f41ea5edeb40"
 ],
 "trust_decision": {
  "summary": "Who may reach the Rsdoctor report server (HTTP API, static client, open-in-editor, WebSocket API): at the pinned commit nobody decides. It listens on all interfaces, sends wildcard CORS and accepts any WS handshake. The fix restricts it to loopback bind + local Host header + local Origin + per-server WS token, all decided in RsdoctorServer.bootstrap and Socket.bootstrap.",
  "evidence": [
   "packages/sdk/src/sdk/server/index.ts:87-90",
   "packages/sdk/src/sdk/server/index.ts:106",
   "packages/sdk/src/sdk/server/index.ts:203-204",
   "packages/sdk/src/sdk/server/socket/index.ts:44",
   "packages/utils/src/build/server.ts:107",
   "fix.diff:661-688",
   "fix.diff:854-863"
  ]
 },
 "landing_point": {
  "where": "packages/sdk/src/sdk/server/index.ts:106",
  "why": "The advisory names an unauthenticated HTTP API. The obvious place is the wildcard cors() middleware and the Access-Control-Allow-Origin:* headers in wrapNextHandleFunction (index.ts:203-204) in RsdoctorServer.bootstrap."
 },
 "fix_sites": [
  {
   "where": "packages/sdk/src/sdk/server/index.ts:106",
   "entry_point": "every HTTP route of the report server (/api/*, static client, /__open-in-editor), started by RsdoctorRspackPlugin / rsdoctor CLI",
   "module_kind": "http server middleware (core)"
  },
  {
   "where": "packages/sdk/src/sdk/server/index.ts:203-204",
   "entry_point": "all Router GET/POST APIs and server.proxy() routes (e.g. Manifest)",
   "module_kind": "response wrapper"
  },
  {
   "where": "packages/sdk/src/sdk/server/index.ts:62-75",
   "entry_point": "server.host/origin/socketUrl used by openClientPage and the manifest's __SOCKET__URL__",
   "module_kind": "server config getter"
  },
  {
   "where": "packages/sdk/src/sdk/server/socket/index.ts:44",
   "entry_point": "WebSocket upgrade on the report server port (request/subscribe for any SDK.ServerAPI.API)",
   "module_kind": "second protocol on the same server"
  },
  {
   "where": "packages/utils/src/build/server.ts:76-110",
   "entry_point": "Server.createServer / getPortSync (public util in @rsdoctor/utils/build) used by RsdoctorServer.bootstrap",
   "module_kind": "lower-level API, other package"
  },
  {
   "where": "packages/sdk/src/sdk/server/fakeServer.ts:5-15",
   "entry_point": "new RsdoctorSDK({config:{noServer:true}}): inherited bootstrap still listened",
   "module_kind": "subclass/wrapper"
  },
  {
   "where": "packages/sdk/src/sdk/sdk/index.ts:63-68",
   "entry_point": "RsdoctorSDK constructor (public @rsdoctor/sdk API)",
   "module_kind": "config plumbing"
  },
  {
   "where": "packages/sdk/src/sdk/multiple/primary.ts:45-54",
   "entry_point": "RsdoctorRspackMultiplePlugin -> RsdoctorSDKController.createSlave",
   "module_kind": "second construction path (multi-compiler)"
  },
  {
   "where": "packages/sdk/src/sdk/multiple/server.ts:8-9",
   "entry_point": "RsdoctorSlaveServer for multi-compiler builds",
   "module_kind": "subclass"
  },
  {
   "where": "packages/core/src/inner-plugins/utils/config.ts:94-119",
   "entry_point": "plugin options normalisation (new server.cors/server.port option)",
   "module_kind": "defaults/merge config"
  },
  {
   "where": "packages/rspack-plugin/src/plugin.ts:70-90",
   "entry_point": "new RsdoctorRspackPlugin(options)",
   "module_kind": "plugin wiring"
  },
  {
   "where": "packages/cli/src/commands/analyze.ts:73",
   "entry_point": "rsdoctor analyze --profile",
   "module_kind": "CLI"
  },
  {
   "where": "packages/cli/src/commands/stats-analyze.ts:45-49",
   "entry_point": "rsdoctor stats-analyze",
   "module_kind": "CLI"
  },
  {
   "where": "packages/components/src/utils/socket.ts:66-74",
   "entry_point": "browser client WS connection (must carry token)",
   "module_kind": "client (frontend)"
  },
  {
   "where": "packages/components/src/utils/data/local.ts:72",
   "entry_point": "browser client LocalServerDataLoader",
   "module_kind": "client (frontend)"
  }
 ],
 "O1_entry_points": 6,
 "O2_out_of_scope_site": {
  "kind": "lower_level_api",
  "where": "packages/utils/src/build/server.ts:107 (server.listen(port) on all interfaces, in @rsdoctor/utils, a different package from the sdk server); also the WS server packages/sdk/src/sdk/server/socket/index.ts:44 and the noServer FakeServer packages/sdk/src/sdk/server/fakeServer.ts:5-15"
 },
 "O3_reason_to_dismiss": "The report is about the HTTP API and CORS. The WebSocket handshake ('a separate realtime channel the browser can't read cross-origin anyway'), the generic createServer util in another package, and a server created with noServer:true or disableClientServer:true ('no server is supposed to run') all look outside it.",
 "O4_distance": {
  "files": 4,
  "packages": 2,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Several legitimate local clients must keep working. The MCP helper in @rsdoctor/ai POSTs to http://localhost:<port> from Node with no Origin and no token. bundle-diff runs two servers on different ports and the client loads across ports (the fix's tests allow 127.0.0.1:port+1). *.localhost origins must also keep working, as must the user-configurable server.cors. Requiring a token on all HTTP, or rejecting every Origin, breaks these.",
  "where": "packages/ai/src/server/request.ts:24-35; packages/cli/src/commands/bundle-diff.ts:164-200; fix.diff:1002-1006"
 },
 "O6_input_shapes": [
  "Host header string, absent, or array (rejected unless string)",
  "Host with IPv6 bracket form [::1]:port",
  ":authority pseudo-header when Host absent (HTTP/2)",
  "*.localhost hostnames (Origin must match Host)",
  "Origin absent (allowed) vs non-local vs array",
  "WebSocket upgrade with missing/invalid token query param",
  "server.cors true / false / object without origin (keeps default local origins)"
 ],
 "O7_producer": {
  "kind": "config_loader",
  "where": "packages/core/src/inner-plugins/utils/config.ts:94-119 (normalizeUserConfig; fix adds server/server.port merge at fix.diff:243-251) feeding packages/sdk/src/sdk/sdk/index.ts:63-68",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "GET /__open-in-editor still has no per-server token after the published fix. Only the Host/Origin middleware guards it, and a no-cors cross-site GET carries no Origin and a localhost Host, so isAllowedCorsRequest(undefined) passes.",
   "where": "packages/sdk/src/sdk/server/index.ts:118-169",
   "reason_to_dismiss": "Opening a file in the local editor is a UI convenience, not data exposure (CWE-200), and the response is opaque cross-origin.",
   "distance": "same file as landing point; consumer in packages/components/src/components/Opener/ide.tsx:30",
   "present_in_latest": "no",
   "latest_where": "latest/packages/core/src/sdk/server/index.ts:302"
  },
  {
   "route": "GET Env API returns the machine's LAN IP (getLocalIpAddress) to any caller allowed by the server",
   "where": "packages/sdk/src/sdk/server/apis/project.ts:13-15",
   "reason_to_dismiss": "Reachable only from local clients once the Host/Origin gate is in; the IP is low-value metadata.",
   "distance": "other file in same package (apis/)",
   "present_in_latest": "yes",
   "latest_where": "latest/packages/core/src/sdk/server/apis/project.ts:14"
  }
 ],
 "O8b_injection_room": [
  {
   "where": "packages/cli/src/commands/bundle-diff.ts:164-165",
   "sibling": "a CLI command that spins up its own connect/http server for the diff manifests instead of reusing RsdoctorServer",
   "why_realistic": "bundle-diff already runs two servers and serves custom manifest buffers via proxy(); a maintainer could plausibly have used a lightweight standalone server here."
  },
  {
   "where": "packages/ai/src/server/request.ts:24-35",
   "sibling": "an MCP-side HTTP/SSE bridge that re-exposes report APIs on its own port",
   "why_realistic": "The ai package already proxies report-server APIs for agents; an HTTP transport for MCP is a common addition."
  },
  {
   "where": "packages/sdk/src/sdk/server/index.ts:233-248",
   "sibling": "a proxy()/addRoute API that registers handlers ahead of the Host/Origin middleware via stack.splice",
   "why_realistic": "proxy() already splices into app.stack at a computed index rather than appending."
  }
 ],
 "O9_family": "missing access control / exposure of a local dev server (CWE-200; DNS-rebinding and cross-origin reads via wildcard CORS, all-interfaces bind, unauthenticated WebSocket)",
 "O9_dos": false,
 "O10_build": {
  "language": "TypeScript (Node.js)",
  "toolchain": "pnpm monorepo, rslib/rsbuild, rstest",
  "services": [],
  "offline_after_build": true,
  "project_tests": "packages/sdk/tests/server/apis/project.test.ts (spins up real server via setupSDK), packages/utils/tests/server.test.ts, packages/core/tests/build/utils/config.test.ts"
 },
 "O11_fix_minutes": 75,
 "O12_red_flags": [],
 "O13_recall_risk": "low",
 "pattern_fit": "A",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "packages/sdk/src/sdk/server/{index.ts,security.ts,socket/index.ts,fakeServer.ts}, packages/sdk/src/sdk/sdk/index.ts, packages/sdk/src/sdk/multiple/{primary.ts,server.ts}, packages/utils/src/build/server.ts, packages/core/src/inner-plugins/utils/config.ts, packages/rspack-plugin/src/{plugin.ts,multiple.ts}, packages/cli/src/commands/{analyze.ts,stats-analyze.ts}, packages/components/src/utils/{socket.ts,data/local.ts}, packages/types/src/{plugin/plugin.ts,sdk/instance.ts,sdk/server/index.ts}",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 0,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Replace cors() with a localhost-only origin allowlist and drop the '*' headers, leaving the all-interfaces bind, the Host check (DNS rebinding) and the unauthenticated WebSocket untouched."
 },
 "out_of_scope_notes": [
  "POST ApplyErrorFix (packages/sdk/src/sdk/server/apis/fs.ts:7-17) writes source files on request; integrity rather than disclosure, gated by the same server middleware.",
  "launch-editor 'editor' parameter is unvalidated at pinned (index.ts:131); latest adds an editor allowlist."
 ],
 "unverified": [
  "pinned_commit hash: parent_commit is null in the candidate; the tree was taken as given.",
  "repo_mb not measured (no shell size check).",
  "Whether the tests build and run offline was not checked (no execution allowed); offline_after_build assumed true because the tests use local http only.",
  "O1 count of 6 = RsdoctorRspackPlugin, RsdoctorRspackMultiplePlugin, rsdoctor analyze, rsdoctor stats-analyze, rsdoctor bundle-diff, RsdoctorSDK public constructor (incl. noServer). Webpack plugin not present in this repo.",
  "disableClientServer:true (CI default) still bootstraps the server (packages/rspack-plugin/src/plugin.ts:111 vs :249). Inferred from code and from the fix's added test fix.diff:384-395; not executed.",
  "O8 open-in-editor no-cors bypass reasoning is from reading security.ts (fix.diff:794-796); not exercised."
 ]
}
  ```
- Published fix sites:   - packages/sdk/src/sdk/server/index.ts:106 — entry point: every HTTP route of the report server (/api/*, static client, /__open-in-editor), started by RsdoctorRspackPlugin / rsdoctor CLI [http server middleware (core)]
  - packages/sdk/src/sdk/server/index.ts:203-204 — entry point: all Router GET/POST APIs and server.proxy() routes (e.g. Manifest) [response wrapper]
  - packages/sdk/src/sdk/server/index.ts:62-75 — entry point: server.host/origin/socketUrl used by openClientPage and the manifest's __SOCKET__URL__ [server config getter]
  - packages/sdk/src/sdk/server/socket/index.ts:44 — entry point: WebSocket upgrade on the report server port (request/subscribe for any SDK.ServerAPI.API) [second protocol on the same server]
  - packages/utils/src/build/server.ts:76-110 — entry point: Server.createServer / getPortSync (public util in @rsdoctor/utils/build) used by RsdoctorServer.bootstrap [lower-level API, other package]
  - packages/sdk/src/sdk/server/fakeServer.ts:5-15 — entry point: new RsdoctorSDK({config:{noServer:true}}): inherited bootstrap still listened [subclass/wrapper]
  - packages/sdk/src/sdk/sdk/index.ts:63-68 — entry point: RsdoctorSDK constructor (public @rsdoctor/sdk API) [config plumbing]
  - packages/sdk/src/sdk/multiple/primary.ts:45-54 — entry point: RsdoctorRspackMultiplePlugin -> RsdoctorSDKController.createSlave [second construction path (multi-compiler)]
  - packages/sdk/src/sdk/multiple/server.ts:8-9 — entry point: RsdoctorSlaveServer for multi-compiler builds [subclass]
  - packages/core/src/inner-plugins/utils/config.ts:94-119 — entry point: plugin options normalisation (new server.cors/server.port option) [defaults/merge config]
  - packages/rspack-plugin/src/plugin.ts:70-90 — entry point: new RsdoctorRspackPlugin(options) [plugin wiring]
  - packages/cli/src/commands/analyze.ts:73 — entry point: rsdoctor analyze --profile [CLI]
  - packages/cli/src/commands/stats-analyze.ts:45-49 — entry point: rsdoctor stats-analyze [CLI]
  - packages/components/src/utils/socket.ts:66-74 — entry point: browser client WS connection (must carry token) [client (frontend)]
  - packages/components/src/utils/data/local.ts:72 — entry point: browser client LocalServerDataLoader [client (frontend)]
- Uncovered routes to confirm (pattern B):   - packages/sdk/src/sdk/server/index.ts:118-169 — GET /__open-in-editor still has no per-server token after the published fix. Only the Host/Origin middleware guards it, and a no-cors cross-site GET carries no Origin and a localhost Host, so isAllowedCorsRequest(undefined) passes. (reason to dismiss: Opening a file in the local editor is a UI convenience, not data exposure (CWE-200), and the response is opaque cross-origin.; still in latest: no)
  - packages/sdk/src/sdk/server/apis/project.ts:13-15 — GET Env API returns the machine's LAN IP (getLocalIpAddress) to any caller allowed by the server (reason to dismiss: Reachable only from local clients once the Host/Origin gate is in; the IP is low-value metadata.; still in latest: yes)
- Design plan from the lead: TRACK = INJECTED (breaker recipe: only injected-sibling tasks at a recurring trust decision have beaten both models).

RECURRING DECISION / PROTECTED SINK: Who may reach the Rsdoctor report server (HTTP API, static client, open-in-editor, WebSocket API): at the pinned commit nobody decides. It listens on all interfaces, sends wildcard CORS and accepts any WS handshake. The fix restricts it to loopback bind + loca

STEP 1 - confirm the published fix's sites and these uncovered-route leads with tests on the pinned copy: packages/sdk/src/sdk/server/index.ts:118-169 (GET /__open-in-editor still has no per-server token aft; dismiss: Opening a file in the local editor is a UI co); packages/sdk/src/sdk/server/apis/project.ts:13-15 (GET Env API returns the machine's LAN IP (getLocalIpAdd; dismiss: Reachable only from local clients once the Ho).
STEP 2 - INJECT 2 to 4 sibling vulnerabilities of the SAME mechanism into our pinned copy at these recurring sites (verify each by reading the code): packages/cli/src/commands/bundle-diff.ts:164-165 -> a CLI command that spins up its own connect/http server for the diff m (realistic: bundle-diff already runs two servers and serves custom manif); packages/ai/src/server/request.ts:24-35 -> an MCP-side HTTP/SSE bridge that re-exposes report APIs on its own por (realistic: The ai package already proxies report-server APIs for agents); packages/sdk/src/sdk/server/index.ts:233-248 -> a proxy()/addRoute API that registers handlers ahead of the Host/Origi (realistic: proxy() already splices into app.stack at a computed index r). Each sibling MUST be code a maintainer could plausibly have written (no tell-tale names/comments/shortcuts; match surrounding style), reachable through the real public entry point, covered by a stated invariant, placed where the published upstream fix never touches, and carry a DIFFERENT plausible reason-to-dismiss from the others (legacy/compat path, internal/trusted caller, unsupported combination, neighbouring feature). Distinct reasons-to-dismiss are the lever.
STEP 3 - hidden security tests require closing the base flaw, every uncovered route AND every injected sibling through the real entry point. The oracle closes all; a fix that closes only the obvious sites must score < 1.0 (add a security_fail check patch for exactly that partial fix).
STEP 4 - COUPLED MUST-KEEP-WORKING (one functional test per trap): Several legitimate local clients must keep working. The MCP helper in @rsdoctor/ai POSTs to http://localhost:<port> from Node with no Origin and no token. bundle-diff runs two servers on different por (near packages/ai/src/server/request.ts:24-35; packages/); keep every legitimate use of the mechanism working.

Aim for >=3 levers with DIFFERENT reasons to dismiss. Every sibling must be findable by a blind engineer from instruction.md + code; if not, drop it. instruction.md stays product-level: system, one impact with one user trigger, invariants covering EVERY route/sibling (a natural list, no count); never name files/functions/fields/CVEs (all in manifest.leak_terms). Register each sibling and route in build/audit/uncovered-routes.tsv.
- Host notes: Language: TypeScript (Node.js). Offline after build, no external services. INJECTED: siblings go in OUR copy only, register them. Recurring trust decision (6 entry points) + screener injection room. Build+test via real entry points; project's own area tests pass at the pinned commit. Pin at the vulnerable commit; keep unrelated earlier fixes.

## Design: where difficulty comes from
Models find the code the report leads to and diagnose it correctly. They fail on scope. Build these
in, in order of evidence:
1. **Pattern A: the published fix's far sites.**
   - The report leads to one site. The tests cover every entry point the published fix protects,
     including one in a module that looks out of scope: a second implementation, a lower-level
     public API, a wrapper, a save/reload path, or a defaults or merge route.
   - Give it a plausible **reason to dismiss**, and **distance**: another file or package from the
     landing point.
2. **Pattern B: uncovered routes.**
   - Routes into the same protected sink where the advisory's own protection is missing at the
     pinned commit, and which the published fix did not touch.
   - They are unmodified upstream code, so a solver can argue they were never covered.
   - The strongest lever found so far: DeepSeek 6 of 6 on one; both models 0 of 3 on three combined.
3. **Input-shape variants** that the general rule covers but a one-case fix misses (a plain string
   and an array).
4. **A coupled must-keep-working behaviour** next to the sink, tested functionally, so an
   over-broad fix fails. MiMo tends to over-harden.
5. **Producer off the check's path.** The check depends on data produced elsewhere (a schema,
   serializer, cache, mapper or config loader) and does not call it. It counts only if the producer
   is infrastructure, not a request handler.
6. **Injected siblings**, only where the plan asks for them. Each must be:
   - code a maintainer could have written, with no deceptive names or comments;
   - reachable through the real entry point;
   - covered by a stated invariant;
   - placed where the upstream fix never touches.

Aim for at least two levers with **different** reasons to dismiss.

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

## Environment (`tasks/rsdoctor-access-control-inj/environment/Dockerfile`)
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

## Report to the solver (`tasks/rsdoctor-access-control-inj/instruction.md`)
**Write:**
- what the system is, at product level;
- one observed impact, with ONE concrete trigger at user level (HTTP request, CLI call or public API
  use);
- the security properties as **invariants**: who may do what to which data, or what attacker input
  must never achieve. Word each so it covers every tested route and shape ("no value of X may …").
  If there are several, give one natural list, never a count;
- every **contract** the tests need:
  - the refusal form ("a client error with no side effect");
  - any interface or field name a test uses;
  - preservation clauses ("works exactly as today");
  - a legitimate magnitude next to any attack magnitude;
- that examples are examples, not the full set;
- the standard constraints block: fix the problem and its close variants; keep legitimate use
  working; do not modify or add tests; do not look up the upstream fix; do not special-case the
  example.

**Never write:**
- file, package, function, class, field or parameter names a user would not see;
- line numbers, the root cause, the fix approach, or a CVE or GHSA id;
- a list of routes, spellings or roles;
- restricting adverbs ("directly", "only via");
- anything that names or paraphrases a far site, an uncovered route or an injected sibling.

Put every identifier that must not appear in `manifest.leak_terms`.

## Tests (`tasks/rsdoctor-access-control-inj/tests/`)
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
- **Wrong-fix patches** go in `build/rsdoctor-access-control-inj/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/rsdoctor-access-control-inj/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/rsdoctor-access-control-inj/manifest.json`:**
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

**Also in `build/rsdoctor-access-control-inj/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py rsdoctor-access-control-inj --only static
python3 -I builder/gate.py rsdoctor-access-control-inj --only nop
python3 -I builder/gate.py rsdoctor-access-control-inj --only oracle
python3 -I builder/gate.py rsdoctor-access-control-inj --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/rsdoctor-access-control-inj/`;
  - edit only `tasks/rsdoctor-access-control-inj/`, `build/rsdoctor-access-control-inj/` and, for pattern B, the register;
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
