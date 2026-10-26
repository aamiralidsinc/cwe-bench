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

Project root: `/home/mara/cwe-bench`. Task: `chrome-devtools-mcp-ds`. Pattern: `B`. Track: `injected`.

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
- Advisory: ["GHSA-8QF9-62X2-82PP", "CVE-2026-53766"]; chromedevtools/chrome-devtools-mcp; CWE-22/CWE-59 path traversal via symlink (link following) on an allow-list root check
- Pinned (vulnerable) commit: 2eab50938093e848ca9786f2ce0c5bf371e63619. Published fix: 176eb695137d9c46a61e2d4d5571880c5145cf46.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v2",
 "model": "claude-opus-5-5",
 "entry_id": "10013",
 "advisory_ids": [
  "GHSA-8QF9-62X2-82PP",
  "CVE-2026-53766"
 ],
 "repo": "chromedevtools/chrome-devtools-mcp",
 "pinned_commit": "2eab50938093e848ca9786f2ce0c5bf371e63619",
 "fix_commits": [
  "176eb695137d9c46a61e2d4d5571880c5145cf46"
 ],
 "trust_decision": {
  "summary": "McpContext.validatePath decides whether a client-supplied file path lies inside the MCP client roots (plus os.tmpdir) using a lexical path.resolve prefix test, so a symlink inside a root that points outside passes; tools then read/write/upload through it.",
  "evidence": [
   "src/McpContext.ts:178-199",
   "src/McpContext.ts:161-172",
   "src/index.ts:61-70"
  ]
 },
 "landing_point": {
  "where": "src/McpContext.ts:186",
  "why": "Advisory names validatePath() and roots canonicalization; the lexical path.resolve + startsWith is the obvious spot."
 },
 "fix_sites": [
  {
   "where": "src/McpContext.ts:178-199",
   "entry_point": "core check used by every file-path MCP tool",
   "module_kind": "core check (logic change)"
  },
  {
   "where": "fix.diff:355-401",
   "entry_point": "new helper resolveCanonicalPath in src/utils/files.ts, called only from validatePath",
   "module_kind": "utility (new)"
  },
  {
   "where": "src/McpContext.ts:854-858",
   "entry_point": "Context.getHeapSnapshotRetainers (lower-level context API) -> MCP tool get_heapsnapshot_retainers; fix adds a missing check here",
   "module_kind": "lower-level API"
  },
  {
   "where": "src/McpContext.ts:711",
   "entry_point": "saveTemporaryFile (screenshot/lighthouse/slim screenshot without path)",
   "module_kind": "core helper (await only)"
  },
  {
   "where": "src/McpContext.ts:725",
   "entry_point": "saveFile (snapshot/screenshot/script/network/trace/lighthouse output)",
   "module_kind": "core helper (await only)"
  },
  {
   "where": "src/McpContext.ts:797",
   "entry_point": "MCP tool install_extension / reload_extension",
   "module_kind": "core helper (await only)"
  },
  {
   "where": "src/McpContext.ts:828",
   "entry_point": "MCP tool get_heapsnapshot_details",
   "module_kind": "lower-level API (await only)"
  },
  {
   "where": "src/McpContext.ts:835",
   "entry_point": "MCP tool get_heapsnapshot_summary",
   "module_kind": "lower-level API (await only)"
  },
  {
   "where": "src/McpContext.ts:842",
   "entry_point": "MCP tool get_heapsnapshot_summary",
   "module_kind": "lower-level API (await only)"
  },
  {
   "where": "src/McpContext.ts:850",
   "entry_point": "MCP tool get_heapsnapshot_class_nodes",
   "module_kind": "lower-level API (await only)"
  },
  {
   "where": "src/tools/ToolDefinition.ts:176",
   "entry_point": "Context type signature (sync -> async)",
   "module_kind": "type"
  },
  {
   "where": "src/tools/input.ts:466",
   "entry_point": "MCP tool upload_file (read)",
   "module_kind": "tool handler (await only)"
  },
  {
   "where": "src/tools/lighthouse.ts:62",
   "entry_point": "MCP tool lighthouse_audit outputDirPath",
   "module_kind": "tool handler (await only)"
  },
  {
   "where": "src/tools/memory.ts:28",
   "entry_point": "MCP tool take_heapsnapshot (write)",
   "module_kind": "tool handler (await only)"
  },
  {
   "where": "src/tools/memory.ts:54",
   "entry_point": "MCP tool get_heapsnapshot_summary (read)",
   "module_kind": "tool handler (await only)"
  },
  {
   "where": "src/tools/memory.ts:86",
   "entry_point": "MCP tool get_heapsnapshot_details (read)",
   "module_kind": "tool handler (await only)"
  },
  {
   "where": "src/tools/memory.ts:115",
   "entry_point": "MCP tool get_heapsnapshot_class_nodes (read)",
   "module_kind": "tool handler (await only)"
  },
  {
   "where": "src/tools/memory.ts:145",
   "entry_point": "MCP tool get_heapsnapshot_retainers (read)",
   "module_kind": "tool handler (await only)"
  },
  {
   "where": "src/tools/network.ts:119-120",
   "entry_point": "MCP tool get_network_request requestFilePath/responseFilePath (write)",
   "module_kind": "tool handler (await only)"
  },
  {
   "where": "src/tools/performance.ts:52",
   "entry_point": "MCP tool performance_start_trace (write)",
   "module_kind": "tool handler (await only)"
  },
  {
   "where": "src/tools/performance.ts:131",
   "entry_point": "MCP tool performance_stop_trace (write)",
   "module_kind": "tool handler (await only)"
  },
  {
   "where": "src/tools/screencast.ts:43",
   "entry_point": "MCP tool screencast_start (write, experimental)",
   "module_kind": "tool handler (await only)"
  },
  {
   "where": "src/tools/screenshot.ts:55",
   "entry_point": "MCP tool take_screenshot (write)",
   "module_kind": "tool handler (await only)"
  },
  {
   "where": "src/tools/script.ts:84",
   "entry_point": "MCP tool evaluate_script filePath (write)",
   "module_kind": "tool handler (await only)"
  },
  {
   "where": "src/tools/snapshot.ts:38",
   "entry_point": "MCP tool take_snapshot filePath (write)",
   "module_kind": "tool handler (await only)"
  }
 ],
 "O1_entry_points": 14,
 "O2_out_of_scope_site": {
  "kind": "lower_level_api",
  "where": "src/McpContext.ts:854-858 (getHeapSnapshotRetainers had no validatePath; tool-level check at src/tools/memory.ts:145 masked it)"
 },
 "O3_reason_to_dismiss": "The real logic change is one function; the per-tool sites are only await plumbing, and the ensureExtension rename after the check (writing x.heapsnapshot/x.json/x.txt after validating x) looks like a naming convenience, not a path-trust decision, so a solver canonicalizing validatePath alone will call the job done.",
 "O4_distance": {
  "files": 12,
  "packages": 1,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "os.tmpdir() is always an allowed root (on macOS /tmp and /var/folders are symlinks), roots themselves may be symlinked, and saveFile creates missing nested directories; rejecting all symlinks or requiring realpath of the target to exist breaks temp-file saves and nested output paths.",
  "where": "src/McpContext.ts:161-172, src/McpContext.ts:731, src/utils/files.ts:11-16"
 },
 "O6_input_shapes": [
  "existing file reached through a symlinked directory inside a root",
  "non-existent file whose parent exists",
  "non-existent file under several missing directories (walk up to nearest existing ancestor)",
  "root URI that is itself a symlink (root is realpath'd too)",
  "root that cannot be resolved (skipped, not fatal)",
  "undefined path / roots undefined (legacy allow-all) unchanged"
 ],
 "O7_producer": {
  "kind": "none",
  "where": "Roots come straight from the client roots/list response (src/index.ts:66-70) into setRoots; no schema/serializer/cache produces the checked path.",
  "check_calls_producer": null
 },
 "O8_uncovered_routes": [
  {
   "route": "take_heapsnapshot validates filePath but writes ensureExtension(filePath,'.heapsnapshot'), a different name that may be a symlink out of the root",
   "where": "src/tools/memory.ts:28-31",
   "reason_to_dismiss": "extension forcing looks cosmetic; validated path and written path share a directory",
   "distance": "different file (tools/memory.ts) from landing point; same package",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "saveFile validates clientProvidedFilePath then writes ensureExtension(path.resolve(...), ext) after mkdir -p; the written name is never canonicalized",
   "where": "src/McpContext.ts:725-732",
   "reason_to_dismiss": "saveFile already calls validatePath; the published fix leaves it as-is",
   "distance": "same file as landing point, different method; reached from snapshot/script/network/trace/lighthouse/screenshot tools",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "screencast_start validates request filePath then records to ensureExtension(path.resolve(filePath), .mp4/.webm)",
   "where": "src/tools/screencast.ts:43-73",
   "reason_to_dismiss": "experimental tool behind experimentalScreencast flag; ffmpeg path",
   "distance": "tools/screencast.ts, same package",
   "present_in_latest": "unknown",
   "latest_where": ""
  }
 ],
 "O8b_injection_room": [
  {
   "where": "src/HeapSnapshotManager.ts:34-43",
   "sibling": "a public load/open method on the manager that reads a snapshot by path without going through McpContext checks",
   "why_realistic": "the manager already resolves and caches by path.resolve(filePath) independently of validatePath"
  },
  {
   "where": "src/tools/extensions.ts:76-82",
   "sibling": "reload_extension re-installing from a stored path rather than via installExtension",
   "why_realistic": "the path comes from the browser, so a maintainer could skip the roots check as already trusted"
  },
  {
   "where": "src/daemon/client.ts:177-178",
   "sibling": "a CLI/daemon image export writing to a caller-chosen directory with its own path join",
   "why_realistic": "the daemon already writes files with writeFileSync outside McpContext"
  }
 ],
 "O9_family": "CWE-22/CWE-59 path traversal via symlink (link following) on an allow-list root check",
 "O9_dos": false,
 "O10_build": {
  "language": "TypeScript",
  "toolchain": "Node ^20.19 || ^22.12 || >=23, npm, tsc (npm run build; npm test = build + scripts/test.mjs)",
  "services": [
   "headless Chrome via puppeteer for tool-level tests; validatePath unit tests need no browser"
  ],
  "offline_after_build": true,
  "project_tests": "tests/McpContext.test.ts:236-270, tests/roots.test.ts, tests/utils/files.test.ts"
 },
 "O11_fix_minutes": 40,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "src/McpContext.ts, src/utils/files.ts, src/tools/ToolDefinition.ts, src/tools/input.ts, src/tools/lighthouse.ts, src/tools/memory.ts, src/tools/network.ts, src/tools/performance.ts, src/tools/screencast.ts, src/tools/screenshot.ts, src/tools/script.ts, src/tools/snapshot.ts",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 0,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Replace path.resolve with fs.realpathSync(filePath) in validatePath, which throws for not-yet-existing output files and leaves the root side and the ensureExtension-renamed write target uncanonicalized."
 },
 "out_of_scope_notes": [
  "Check-then-write TOCTOU between validatePath and fs.writeFile/mkdir (symlink swapped after check) is not addressed by any version of the fix.",
  "Roots undefined (client without roots capability) allows every path by design (src/McpContext.ts:182-185)."
 ],
 "unverified": [
  "Repo size in MB not measured.",
  "Latest release not provided; present_in_latest unknown for all O8 routes.",
  "The fix's ENOENT fallback (fix.diff:361-392) appends the basename of a dangling final-component symlink without following it; whether a hidden test could require handling that shape is not checked.",
  "O1 counts distinct MCP tools reaching validatePath (14); CLI wrappers in src/bin/chrome-devtools-cli-options.ts expose the same tools and were not counted separately."
 ]
}
  ```
- Published fix sites:   - src/McpContext.ts:178-199 — entry point: core check used by every file-path MCP tool [core check (logic change)]
  - fix.diff:355-401 — entry point: new helper resolveCanonicalPath in src/utils/files.ts, called only from validatePath [utility (new)]
  - src/McpContext.ts:854-858 — entry point: Context.getHeapSnapshotRetainers (lower-level context API) -> MCP tool get_heapsnapshot_retainers; fix adds a missing check here [lower-level API]
  - src/McpContext.ts:711 — entry point: saveTemporaryFile (screenshot/lighthouse/slim screenshot without path) [core helper (await only)]
  - src/McpContext.ts:725 — entry point: saveFile (snapshot/screenshot/script/network/trace/lighthouse output) [core helper (await only)]
  - src/McpContext.ts:797 — entry point: MCP tool install_extension / reload_extension [core helper (await only)]
  - src/McpContext.ts:828 — entry point: MCP tool get_heapsnapshot_details [lower-level API (await only)]
  - src/McpContext.ts:835 — entry point: MCP tool get_heapsnapshot_summary [lower-level API (await only)]
  - src/McpContext.ts:842 — entry point: MCP tool get_heapsnapshot_summary [lower-level API (await only)]
  - src/McpContext.ts:850 — entry point: MCP tool get_heapsnapshot_class_nodes [lower-level API (await only)]
  - src/tools/ToolDefinition.ts:176 — entry point: Context type signature (sync -> async) [type]
  - src/tools/input.ts:466 — entry point: MCP tool upload_file (read) [tool handler (await only)]
  - src/tools/lighthouse.ts:62 — entry point: MCP tool lighthouse_audit outputDirPath [tool handler (await only)]
  - src/tools/memory.ts:28 — entry point: MCP tool take_heapsnapshot (write) [tool handler (await only)]
  - src/tools/memory.ts:54 — entry point: MCP tool get_heapsnapshot_summary (read) [tool handler (await only)]
  - src/tools/memory.ts:86 — entry point: MCP tool get_heapsnapshot_details (read) [tool handler (await only)]
  - src/tools/memory.ts:115 — entry point: MCP tool get_heapsnapshot_class_nodes (read) [tool handler (await only)]
  - src/tools/memory.ts:145 — entry point: MCP tool get_heapsnapshot_retainers (read) [tool handler (await only)]
  - src/tools/network.ts:119-120 — entry point: MCP tool get_network_request requestFilePath/responseFilePath (write) [tool handler (await only)]
  - src/tools/performance.ts:52 — entry point: MCP tool performance_start_trace (write) [tool handler (await only)]
  - src/tools/performance.ts:131 — entry point: MCP tool performance_stop_trace (write) [tool handler (await only)]
  - src/tools/screencast.ts:43 — entry point: MCP tool screencast_start (write, experimental) [tool handler (await only)]
  - src/tools/screenshot.ts:55 — entry point: MCP tool take_screenshot (write) [tool handler (await only)]
  - src/tools/script.ts:84 — entry point: MCP tool evaluate_script filePath (write) [tool handler (await only)]
  - src/tools/snapshot.ts:38 — entry point: MCP tool take_snapshot filePath (write) [tool handler (await only)]
- Uncovered routes to confirm (pattern B):   - src/tools/memory.ts:28-31 — take_heapsnapshot validates filePath but writes ensureExtension(filePath,'.heapsnapshot'), a different name that may be a symlink out of the root (reason to dismiss: extension forcing looks cosmetic; validated path and written path share a directory; still in latest: unknown)
  - src/McpContext.ts:725-732 — saveFile validates clientProvidedFilePath then writes ensureExtension(path.resolve(...), ext) after mkdir -p; the written name is never canonicalized (reason to dismiss: saveFile already calls validatePath; the published fix leaves it as-is; still in latest: unknown)
  - src/tools/screencast.ts:43-73 — screencast_start validates request filePath then records to ensureExtension(path.resolve(filePath), .mp4/.webm) (reason to dismiss: experimental tool behind experimentalScreencast flag; ffmpeg path; still in latest: unknown)
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

## Environment (`tasks/chrome-devtools-mcp-ds/environment/Dockerfile`)
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

## Report to the solver (`tasks/chrome-devtools-mcp-ds/instruction.md`)
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

## Tests (`tasks/chrome-devtools-mcp-ds/tests/`)
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
- **Wrong-fix patches** go in `build/chrome-devtools-mcp-ds/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/chrome-devtools-mcp-ds/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/chrome-devtools-mcp-ds/manifest.json`:**
- `slug`, `candidate`;
- `pattern`: `B`;
- `builder_prompt_version`: `build-v1`;
- `"strict_gate": true`;
- `verified`: entry point, sites, routes, services, project tests run;
- `leak_terms`, `patch_checks`, `wrong_fix_catalogue`;
- `traps`: one entry per lever, with `shape`, `where` (file:line), `security_tests`,
  `coupled_functional_tests`, `security_fail_patch`, and `realistic_because` (for pattern B: "real,
  unmodified upstream code");
- `status`.

**Also in `build/chrome-devtools-mcp-ds/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py chrome-devtools-mcp-ds --only static
python3 -I builder/gate.py chrome-devtools-mcp-ds --only nop
python3 -I builder/gate.py chrome-devtools-mcp-ds --only oracle
python3 -I builder/gate.py chrome-devtools-mcp-ds --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/chrome-devtools-mcp-ds/`;
  - edit only `tasks/chrome-devtools-mcp-ds/`, `build/chrome-devtools-mcp-ds/` and, for pattern B, the register;
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
