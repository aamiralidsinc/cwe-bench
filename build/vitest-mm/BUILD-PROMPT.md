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

Project root: `/home/mara/cwe-bench`. Task: `vitest-mm`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: ["GHSA-5XRQ-8626-4RWP", "CVE-2026-47429"]; vitest-dev/vitest; missing authorization on network-reachable write/exec API plus path confinement (CWE-862 / CWE-22)
- Pinned (vulnerable) commit: parent of 20e00ef7808de6d330c5e2fda530f686e08f1c8d (parent_commit not given in candidate). Published fix: 20e00ef7808de6d330c5e2fda530f686e08f1c8d, af88b1f5d82844a4761ea9a977156c98e2b14ca8.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "8887",
 "advisory_ids": [
  "GHSA-5XRQ-8626-4RWP",
  "CVE-2026-47429"
 ],
 "repo": "vitest-dev/vitest",
 "pinned_commit": "parent of 20e00ef7808de6d330c5e2fda530f686e08f1c8d (parent_commit not given in candidate)",
 "fix_commits": [
  "20e00ef7808de6d330c5e2fda530f686e08f1c8d",
  "af88b1f5d82844a4761ea9a977156c98e2b14ca8"
 ],
 "trust_decision": {
  "summary": "Whether a client holding the API token (token is handed to anyone who loads the UI HTML) may write files, delete files, run tests, or touch files outside Vite server.fs.allow is decided per WebSocket handler in packages/vitest/src/api/setup.ts (UI API) and packages/browser/src/node/rpc.ts + commands/fs.ts (browser API); at the pinned commit there is no write/exec gate at all, and the file check is the deprecated isFileServingAllowed that returns true when server.fs.strict is false.",
  "evidence": [
   "packages/vitest/src/api/check.ts:5-22",
   "packages/ui/node/index.ts:100-113",
   "packages/vitest/src/api/setup.ts:77-90",
   "packages/vitest/src/api/setup.ts:152-159",
   "packages/browser/src/node/rpc.ts:115-121",
   "packages/browser/src/node/rpc.ts:194-205",
   "packages/browser/src/node/commands/fs.ts:8-17",
   "packages/vitest/src/node/vite.ts:49-53"
  ]
 },
 "landing_point": {
  "where": "packages/vitest/src/api/setup.ts:77-90",
  "why": "The summary names the Vitest UI server and file read/execute; the UI WebSocket handlers saveTestFile/rerun/rerunTask are the obvious write+exec sinks reachable from the UI."
 },
 "fix_sites": [
  {
   "where": "packages/vitest/src/api/setup.ts:62-64",
   "entry_point": "UI API WebSocket (API_PATH) handler onTaskUpdate, removed by fix (fix.diff:1286-1288)",
   "module_kind": "handler (core vitest package)"
  },
  {
   "where": "packages/vitest/src/api/setup.ts:77-84",
   "entry_point": "UI API WebSocket handler saveTestFile (UI code editor save)",
   "module_kind": "handler (core vitest package)"
  },
  {
   "where": "packages/vitest/src/api/setup.ts:85-90",
   "entry_point": "UI API WebSocket handlers rerun / rerunTask (UI run buttons)",
   "module_kind": "handler (core vitest package)"
  },
  {
   "where": "packages/vitest/src/api/setup.ts:152-159",
   "entry_point": "UI API WebSocket handler updateSnapshot (UI fix-snapshot button)",
   "module_kind": "handler (core vitest package)"
  },
  {
   "where": "packages/browser/src/node/rpc.ts:115-121",
   "entry_point": "browser API WebSocket /__vitest_browser_api__ checkFileAccess used by read/save/removeSnapshotFile",
   "module_kind": "second implementation (separate browser-mode API server, @vitest/browser package)"
  },
  {
   "where": "packages/browser/src/node/rpc.ts:154-156",
   "entry_point": "browser API WebSocket handler onTaskArtifactRecord (annotation/artifact attachments copied to disk)",
   "module_kind": "second implementation (@vitest/browser rpc)"
  },
  {
   "where": "packages/browser/src/node/rpc.ts:194-205",
   "entry_point": "browser API WebSocket handlers saveSnapshotFile / removeSnapshotFile",
   "module_kind": "second implementation (@vitest/browser rpc)"
  },
  {
   "where": "packages/browser/src/node/commands/fs.ts:8-60",
   "entry_point": "browser API WebSocket triggerCommand (packages/browser/src/node/rpc.ts:254-282) -> built-in commands readFile/writeFile/removeFile/__vitest_fileInfo (packages/browser/src/node/commands/index.ts:11-15)",
   "module_kind": "wrapper / lower-level command API (@vitest/browser)"
  },
  {
   "where": "packages/vitest/src/node/config/resolveConfig.ts:58-101",
   "entry_point": "config/CLI: test.api / test.browser.api (--api.host etc.) resolved via resolveApiServerConfig, called at packages/vitest/src/node/config/resolveConfig.ts:588 and :801-805",
   "module_kind": "config loader / defaults-merge route (browser.api inherits api)"
  },
  {
   "where": "packages/vitest/src/node/config/serializeConfig.ts:34",
   "entry_point": "UI API getConfig (packages/vitest/src/api/setup.ts:91-93) returns serialized config; fix adds api.allowExec/allowWrite (fix.diff:1448-1453)",
   "module_kind": "serializer"
  },
  {
   "where": "fix.diff:1345-1368",
   "entry_point": "CLI --api.allowExec / --api.allowWrite and number-vs-object transform in packages/vitest/src/node/cli/cli-config.ts",
   "module_kind": "CLI option schema"
  },
  {
   "where": "fix.diff:1022-1144",
   "entry_point": "UI client Vue components (Navigation.vue, ExplorerItem.vue, ViewEditor.vue) disable run/save buttons; UX only, not a server-side gate",
   "module_kind": "client UI"
  }
 ],
 "O1_entry_points": 12,
 "O2_out_of_scope_site": {
  "kind": "second_implementation",
  "where": "packages/browser/src/node/rpc.ts:154-156, packages/browser/src/node/rpc.ts:194-205 and packages/browser/src/node/commands/fs.ts:31-49 (separate browser-mode API server in @vitest/browser; also defaults/merge route packages/vitest/src/node/config/resolveConfig.ts:801-805 where browser.api must inherit api flags)"
 },
 "O3_reason_to_dismiss": "The advisory names the UI server; the browser-mode API is a separate server on another port whose snapshot/file writes are made by the user's own test code, so gating it looks like breaking browser tests rather than closing the UI hole.",
 "O4_distance": {
  "files": 8,
  "packages": 3,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "On a localhost (default) host, UI save/run and browser-mode snapshot writes, attachments and commands.writeFile must keep working (defaults true); with writes disabled, commands.readFile and readSnapshotFile must still work (fix gates only writes, fix.diff:842-850), and middlewareMode is exempt (fix.diff:1402). An over-broad fix that gates reads, or flips defaults for localhost, breaks browser tests and the UI editor.",
  "where": "packages/browser/src/node/commands/fs.ts:19-29, packages/browser/src/node/rpc.ts:187-193, packages/vitest/src/node/config/resolveConfig.ts:91-98"
 },
 "O6_input_shapes": [
  "host value: localhost / 127.0.0.1 keep write+exec, any other host disables by default, explicit override wins (fix.diff:1402-1419)",
  "api given as number vs object on the CLI (fix.diff:1362-1367)",
  "browser.api inheriting from root api vs its own override (fix.diff:1404-1414)",
  "Windows backslash paths normalised with slash() before the fs check (fix.diff:847, 858, 869, 876)",
  "server.fs.strict=false bypass and cleanUrl query/hash stripping of the old check removed by switching to isFileLoadingAllowed (packages/vitest/src/node/vite.ts:49-53, packages/vitest/src/node/vite.ts:66-68)",
  "annotation single attachment vs artifact.attachments array (fix.diff:922-935)",
  "updateSnapshot with and without a file argument (packages/vitest/src/api/setup.ts:152-159)"
 ],
 "O7_producer": {
  "kind": "config_loader",
  "where": "packages/vitest/src/node/config/resolveConfig.ts:58-101 (resolveApiServerConfig computes allowWrite/allowExec defaults; serializer packages/vitest/src/node/config/serializeConfig.ts:34 carries them to the UI client)",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "UI HTTP /__vitest_attachment__ streams any path that passes the deprecated isFileServingAllowed (true when server.fs.strict is false); fix converted rpc/commands checks but not this one",
   "where": "packages/ui/node/index.ts:77",
   "reason_to_dismiss": "read-only HTTP endpoint behind the API token, and the fix is about write/exec flags",
   "distance": "packages/ui/node (third package, not touched server-side by the fix)",
   "present_in_latest": "yes",
   "latest_where": "latest/packages/ui/node/index.ts:121"
  },
  {
   "route": "browser-server HTTP /__vitest_attachment__ copy of the same middleware, same deprecated check",
   "where": "packages/browser/src/node/plugin.ts:194",
   "reason_to_dismiss": "described in code as a copy of the UI handler; a read path in a plugin, not an RPC handler",
   "distance": "packages/browser/src/node/plugin.ts, a file the fix did not touch",
   "present_in_latest": "yes",
   "latest_where": "latest/packages/browser/src/node/index.ts:298"
  },
  {
   "route": "UI API getExternalResult / getTransformResult read module source using the deprecated isFileServingAllowed",
   "where": "packages/vitest/src/api/setup.ts:103",
   "reason_to_dismiss": "source viewer for modules of a known test file; reads only",
   "distance": "same file as landing point",
   "present_in_latest": "yes",
   "latest_where": "latest/packages/vitest/src/api/setup.ts:120"
  },
  {
   "route": "browser API onTaskArtifactRecord with writes allowed copies a client-supplied attachment path from anywhere into attachmentsDir (no server.fs check)",
   "where": "packages/vitest/src/node/test-run.ts:262-273",
   "reason_to_dismiss": "writes are allowed on localhost by design, and the copy happens in the core test-run module, not the RPC handler",
   "distance": "packages/vitest/src/node/test-run.ts, reached from packages/browser/src/node/rpc.ts:154-156",
   "present_in_latest": "no",
   "latest_where": "latest/packages/browser/src/node/rpc.ts:296-310"
  },
  {
   "route": "browser API registerMock redirect joins a client URL pathname onto root, and the mocker later reads that file, with no server.fs check",
   "where": "packages/browser/src/node/rpc.ts:310-313",
   "reason_to_dismiss": "mocking is a neighbouring feature (module redirection), not file access",
   "distance": "same file as browser fix site; sink in packages/mocker/src/node/interceptorPlugin.ts:34-35",
   "present_in_latest": "no",
   "latest_where": "latest/packages/browser/src/node/rpc.ts:494-498"
  },
  {
   "route": "browser API sendCdpEvent / trackCdpEvent forward arbitrary CDP commands with no allowExec/allowWrite gate",
   "where": "packages/browser/src/node/rpc.ts:350-357",
   "reason_to_dismiss": "CDP is a provider-specific (playwright/chromium) feature, not a file or test-run operation",
   "distance": "same file as browser fix site",
   "present_in_latest": "no",
   "latest_where": "latest/packages/browser/src/node/rpc.ts:534"
  }
 ],
 "O8b_injection_room": [
  {
   "where": "packages/browser/src/node/rpc.ts:194-205",
   "sibling": "another write handler next to saveSnapshotFile (e.g. benchmark/result writer) with checkFileAccess but no canWrite",
   "why_realistic": "upstream later added readBenchmarkResult/writeBenchmarkResult handlers at exactly this spot (latest/packages/browser/src/node/rpc.ts:318-331)"
  },
  {
   "where": "packages/browser/src/node/commands/fs.ts:43-49",
   "sibling": "an extra built-in command (copyFile/appendFile) that calls assertFileAccess but not assertWrite",
   "why_realistic": "commands are added as small functions registered in packages/browser/src/node/commands/index.ts:11-15; a maintainer copies the read pattern"
  },
  {
   "where": "packages/vitest/src/api/setup.ts:152-159",
   "sibling": "a UI handler that saves an inline snapshot or opens a file, gated only by filesMap membership",
   "why_realistic": "saveTestFile already uses filesMap as its only gate (packages/vitest/src/api/setup.ts:78-83)"
  }
 ],
 "O9_family": "missing authorization on network-reachable write/exec API plus path confinement (CWE-862 / CWE-22)",
 "O9_dos": false,
 "O10_build": {
  "language": "TypeScript",
  "toolchain": "Node.js + pnpm monorepo (vite build per package)",
  "services": [
   "Playwright Chromium for test/browser and test/ui e2e specs"
  ],
  "offline_after_build": true,
  "project_tests": "test/config/test/override.test.ts (api flag resolution, offline), test/browser/specs/errors.test.ts (browser fs commands/snapshots, needs Chromium), test/ui/test/*.spec.ts (Playwright UI), test/cli/test/config/browser-configs.test.ts"
 },
 "O11_fix_minutes": 75,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "packages/vitest/src/api/setup.ts, packages/vitest/src/api/types.ts, packages/vitest/src/node/config/resolveConfig.ts, packages/vitest/src/node/config/serializeConfig.ts, packages/vitest/src/node/cli/cli-config.ts, packages/vitest/src/node/types/config.ts, packages/vitest/src/runtime/config.ts, packages/browser/src/node/rpc.ts, packages/browser/src/node/commands/fs.ts, packages/ui/client/** (UX), packages/utils/src/source-map.ts (unrelated)",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Gate saveTestFile/rerun in packages/vitest/src/api/setup.ts behind a host check, leaving the browser API rpc/commands, the browser.api default inheritance and the strict=false check bypass untouched."
 },
 "out_of_scope_notes": [
  "packages/mocker/src/node/interceptorPlugin.ts:68-71 accepts redirect paths over the Vite HMR socket without confinement (later confined at latest/packages/mocker/src/node/interceptorPlugin.ts:84); different transport, not this advisory's API.",
  "packages/browser/src/node/rpc.ts:206-226 getBrowserFileSourceMap reads a sourceMappingURL-resolved path without checkFileAccess; limited to modules already in the graph.",
  "Fix diff also carries unrelated noise: docs/config/browser.md deletion, UI null-guards on config, packages/utils/src/source-map.ts stack pattern."
 ],
 "unverified": [
  "pinned_commit hash not given (parent_commit null); assumed to be the parent of the first fix commit.",
  "Whether af88b1f5 is fully contained in fix.diff was not checked separately.",
  "repo_mb not measured (no shell used); vitest monorepo is well above 5 MB and far below 1.5 GB by inspection.",
  "Fairness risk: the published fix introduces new public options api.allowWrite/api.allowExec and browser.api.* with host-based defaults; hidden tests would need the report to name these options and the default rule, otherwise the task is unfair.",
  "O1 counts handlers/commands individually (5 UI API handlers, 3 browser rpc handlers, 4 browser commands)."
 ]
}
  ```
- Published fix sites:   - packages/vitest/src/api/setup.ts:62-64 — entry point: UI API WebSocket (API_PATH) handler onTaskUpdate, removed by fix (fix.diff:1286-1288) [handler (core vitest package)]
  - packages/vitest/src/api/setup.ts:77-84 — entry point: UI API WebSocket handler saveTestFile (UI code editor save) [handler (core vitest package)]
  - packages/vitest/src/api/setup.ts:85-90 — entry point: UI API WebSocket handlers rerun / rerunTask (UI run buttons) [handler (core vitest package)]
  - packages/vitest/src/api/setup.ts:152-159 — entry point: UI API WebSocket handler updateSnapshot (UI fix-snapshot button) [handler (core vitest package)]
  - packages/browser/src/node/rpc.ts:115-121 — entry point: browser API WebSocket /__vitest_browser_api__ checkFileAccess used by read/save/removeSnapshotFile [second implementation (separate browser-mode API server, @vitest/browser package)]
  - packages/browser/src/node/rpc.ts:154-156 — entry point: browser API WebSocket handler onTaskArtifactRecord (annotation/artifact attachments copied to disk) [second implementation (@vitest/browser rpc)]
  - packages/browser/src/node/rpc.ts:194-205 — entry point: browser API WebSocket handlers saveSnapshotFile / removeSnapshotFile [second implementation (@vitest/browser rpc)]
  - packages/browser/src/node/commands/fs.ts:8-60 — entry point: browser API WebSocket triggerCommand (packages/browser/src/node/rpc.ts:254-282) -> built-in commands readFile/writeFile/removeFile/__vitest_fileInfo (packages/browser/src/node/commands/index.ts:11-15) [wrapper / lower-level command API (@vitest/browser)]
  - packages/vitest/src/node/config/resolveConfig.ts:58-101 — entry point: config/CLI: test.api / test.browser.api (--api.host etc.) resolved via resolveApiServerConfig, called at packages/vitest/src/node/config/resolveConfig.ts:588 and :801-805 [config loader / defaults-merge route (browser.api inherits api)]
  - packages/vitest/src/node/config/serializeConfig.ts:34 — entry point: UI API getConfig (packages/vitest/src/api/setup.ts:91-93) returns serialized config; fix adds api.allowExec/allowWrite (fix.diff:1448-1453) [serializer]
  - fix.diff:1345-1368 — entry point: CLI --api.allowExec / --api.allowWrite and number-vs-object transform in packages/vitest/src/node/cli/cli-config.ts [CLI option schema]
  - fix.diff:1022-1144 — entry point: UI client Vue components (Navigation.vue, ExplorerItem.vue, ViewEditor.vue) disable run/save buttons; UX only, not a server-side gate [client UI]
- Uncovered routes to confirm (pattern B):   - packages/ui/node/index.ts:77 — UI HTTP /__vitest_attachment__ streams any path that passes the deprecated isFileServingAllowed (true when server.fs.strict is false); fix converted rpc/commands checks but not this one (reason to dismiss: read-only HTTP endpoint behind the API token, and the fix is about write/exec flags; still in latest: yes)
  - packages/browser/src/node/plugin.ts:194 — browser-server HTTP /__vitest_attachment__ copy of the same middleware, same deprecated check (reason to dismiss: described in code as a copy of the UI handler; a read path in a plugin, not an RPC handler; still in latest: yes)
  - packages/vitest/src/api/setup.ts:103 — UI API getExternalResult / getTransformResult read module source using the deprecated isFileServingAllowed (reason to dismiss: source viewer for modules of a known test file; reads only; still in latest: yes)
  - packages/vitest/src/node/test-run.ts:262-273 — browser API onTaskArtifactRecord with writes allowed copies a client-supplied attachment path from anywhere into attachmentsDir (no server.fs check) (reason to dismiss: writes are allowed on localhost by design, and the copy happens in the core test-run module, not the RPC handler; still in latest: no)
  - packages/browser/src/node/rpc.ts:310-313 — browser API registerMock redirect joins a client URL pathname onto root, and the mocker later reads that file, with no server.fs check (reason to dismiss: mocking is a neighbouring feature (module redirection), not file access; still in latest: no)
  - packages/browser/src/node/rpc.ts:350-357 — browser API sendCdpEvent / trackCdpEvent forward arbitrary CDP commands with no allowExec/allowWrite gate (reason to dismiss: CDP is a provider-specific (playwright/chromium) feature, not a file or test-run operation; still in latest: no)
- Design plan from the lead: No lead plan is provided for this task — you are the lead as well as the builder. Using the Design section above and the screener record, design the task yourself and WRITE YOUR PLAN in `notes.md` BEFORE you build:
  - choose the main lever and at least one more, each with a DIFFERENT reason a solver would dismiss or skip it;
  - decide the sites, routes and input shapes the security tests will cover;
  - identify the coupled must-keep-working behaviour next to each lever, for the functional tests;
  - for the injected track: decide the realistic sibling gap(s) to add — each must be code a maintainer could plausibly have left, reachable through the real entry point, covered by a stated invariant, and placed where the published fix never touches. Add 2–4 siblings at a recurring trust decision, each with its own reason a solver would skip it;
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

## Environment (`tasks/vitest-mm/environment/Dockerfile`)
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

## Report to the solver (`tasks/vitest-mm/instruction.md`)
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

## Tests (`tasks/vitest-mm/tests/`)
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
- **Wrong-fix patches** go in `build/vitest-mm/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/vitest-mm/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/vitest-mm/manifest.json`:**
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

**Also in `build/vitest-mm/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py vitest-mm --only static
python3 -I builder/gate.py vitest-mm --only nop
python3 -I builder/gate.py vitest-mm --only oracle
python3 -I builder/gate.py vitest-mm --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/vitest-mm/`;
  - edit only `tasks/vitest-mm/`, `build/vitest-mm/` and, for pattern B, the register;
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
