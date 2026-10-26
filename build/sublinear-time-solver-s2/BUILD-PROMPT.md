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

Project root: `/home/mara/cwe-bench`. Task: `sublinear-time-solver-s2`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: ["GHSA-XC9G-J69Q-37XW", "CVE-2026-55609"]; ruvnet/sublinear-time-solver; CWE-73 external control of file name or path (arbitrary file write/read, including traversal), same family as CWE-22
- Pinned (vulnerable) commit: 1210646955f33abe5c91f894cc7b04d024f62408. Published fix: a701296e363192be863e79d788fa268095e3d229, ea9a212b69e4449ec443fe088a7aec7546f70b4a.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v2",
 "model": "deepseek-flash",
 "entry_id": "14848",
 "advisory_ids": [
  "GHSA-XC9G-J69Q-37XW",
  "CVE-2026-55609"
 ],
 "repo": "ruvnet/sublinear-time-solver",
 "pinned_commit": "1210646955f33abe5c91f894cc7b04d024f62408",
 "fix_commits": [
  "a701296e363192be863e79d788fa268095e3d229",
  "ea9a212b69e4449ec443fe088a7aec7546f70b4a"
 ],
 "trust_decision": {
  "summary": "A caller-supplied file path may only name a basename inside a fixed, per-feature directory that the process owns; the decision is made in the sink helper (resolveStatePath/resolveVectorPath + O_NOFOLLOW open), not in the MCP request handler or the JSON input schema.",
  "evidence": [
   "fix.diff:89-106",
   "fix.diff:472-500",
   "fix.diff:551-560",
   "src/mcp/server.ts:1275"
  ]
 },
 "landing_point": {
  "where": "src/consciousness-explorer/mcp/server.js:239",
  "why": "The advisory names the MCP export_state tool; the tool schema is the first hit when searching export_state, and its handler at server.js:528-529 forwards args.filepath unchanged to ConsciousnessExplorer.exportState, which lands in fs.writeFileSync at src/consciousness-explorer/index.js:288."
 },
 "fix_sites": [
  {
   "where": "src/consciousness-explorer/index.js:288",
   "entry_point": "MCP tool `export_state` (src/consciousness-explorer/mcp/server.js:528-529) and CLI `export <filepath>` / `evolve --export <path>` (src/consciousness-explorer/bin/cli.js:46,353-361)",
   "module_kind": "library class method (library layer, separate from the MCP handler)"
  },
  {
   "where": "src/consciousness-explorer/index.js:297",
   "entry_point": "MCP tool `import_state` (src/consciousness-explorer/mcp/server.js:545-546) and CLI `import <filepath>` (src/consciousness-explorer/bin/cli.js:373-380)",
   "module_kind": "library class method (read direction of the same sink family)"
  },
  {
   "where": "src/consciousness-explorer/mcp/server.js:239-264",
   "entry_point": "MCP tool schemas `export_state` / `import_state` filepath property",
   "module_kind": "MCP tool definition (stdio server, description/pattern only)"
  },
  {
   "where": "fix.diff:353-589",
   "entry_point": "shared helper reached by both export_state and import_state",
   "module_kind": "new helper module src/consciousness-explorer/lib/safe-path.js"
  },
  {
   "where": "src/mcp/server.ts:1275",
   "entry_point": "MCP tool `saveVectorToFile` -> handleSaveVectorToFile (src/mcp/server.ts:1121-1140)",
   "module_kind": "MCP tool handler in a second, separate server tree (src/mcp) of the same npm package"
  },
  {
   "where": "src/mcp/server.ts:1184",
   "entry_point": "MCP tool `solveTrueSublinear` with the `vector_file` argument (src/mcp/server.ts:936-938)",
   "module_kind": "MCP tool handler in the second server tree (read direction, lower-level helper)"
  },
  {
   "where": "src/mcp/server.ts:366-379",
   "entry_point": "MCP tool schema for `saveVectorToFile` file_path property",
   "module_kind": "MCP tool definition (stdio server, description/pattern only)"
  },
  {
   "where": "fix.diff:5-168",
   "entry_point": "shared helper reached by saveVectorToFile and vector_file",
   "module_kind": "new helper module src/mcp/safe-path.ts"
  }
 ],
 "O1_entry_points": 5,
 "O2_out_of_scope_site": {
  "kind": "second_implementation",
  "where": "src/mcp/server.ts:1275 (saveVectorToFile) and src/mcp/server.ts:1184 (loadVectorFromFile)"
 },
 "O3_reason_to_dismiss": "The main sublinear-time-solver MCP server is a different program from the consciousness-explorer MCP server named in the advisory; saveVectorToFile/vector_file are numerical-plumbing features for the solver, so the vector path reads as an unrelated feature that the export_state report never mentioned.",
 "O4_distance": {
  "files": 2,
  "packages": 2,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Callers legitimately pass absolute paths today: the CLI documents `export <filepath>`, `import <filepath>` and `evolve --export <path>` (arbitrary destination), and the in-repo integration example writes to /tmp/consciousness-state-test.json. A basename-only rule buried in the library makes all of those throw, so an over-broad fix breaks the documented CLI contract and the example.",
  "where": "src/consciousness-explorer/bin/cli.js:46"
 },
 "O6_input_shapes": [
  "non-string or empty filepath (typeof / length check)",
  "basename longer than 255 UTF-8 bytes",
  "forward-slash or backslash separators (relative subpath, absolute path, ../ traversal)",
  "\".\" and \"..\" as the whole name",
  "leading dot (hidden dotfile names)",
  "ASCII control characters including NUL (0x00-0x1f, 0x7f)",
  "Windows reserved device names with or without an extension (CON, COM1, LPT9, ...)",
  "symlink planted at the final path component (O_NOFOLLOW)",
  "final component that is not a regular file (fstat isFile -> ENOTFILE)",
  "read direction as well as write direction (import_state / vector_file vs export_state / saveVectorToFile)",
  "both argument names, filepath (state) and file_path / vector_file (vectors)"
 ],
 "O7_producer": {
  "kind": "handler",
  "where": "src/consciousness-explorer/mcp/server.js:529",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "CLI `verify --export <path>` writes the verification report to any caller-supplied path with no containment",
   "where": "src/consciousness-explorer/bin/cli.js:127-129",
   "reason_to_dismiss": "the path comes from a local CLI flag typed by the operator, not from a caller of the MCP server, so it is not attacker-controlled",
   "distance": "same package, different file (bin/ vs index.js) and a code path the published fix never touched",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "ProofLogger.exportProof(filepath) is a public library method that writes JSON to a caller-supplied path with no validation",
   "where": "src/consciousness-explorer/lib/proof-logger.js:647-656",
   "reason_to_dismiss": "no MCP tool or CLI command in the repo calls it, so it looks like an internal proof/debug helper rather than an exposed route",
   "distance": "same package, lib/ subdirectory, with no in-repo caller",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "main solver CLI writes solution/analysis/result/graph JSON to any `--output <path>` with no containment",
   "where": "src/cli/index.ts:182",
   "reason_to_dismiss": "operator-owned CLI flag on the local command line; the advisory's file arguments are MCP tool arguments, not CLI flags",
   "distance": "different tree (src/cli) from the landing point, same npm package",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "compiled copy of the same sink still resolves and writes an arbitrary path",
   "where": "dist/mcp/server.js:1121",
   "reason_to_dismiss": "dist/ is generated output; npm run build:ts regenerates it from src/mcp/server.ts, so it needs no fix of its own",
   "distance": "same function, generated tree checked into the repo",
   "present_in_latest": "unknown",
   "latest_where": ""
  }
 ],
 "O8b_injection_room": [
  {
   "where": "src/consciousness-explorer/mcp/server.js:239-264",
   "sibling": "a third persistence tool (e.g. `export_memory` / `snapshot_state`) taking a `filepath` and calling the same export helper",
   "why_realistic": "the persistence tool group already ships export_state/import_state as a named pair, so adding a third snapshot tool is the obvious incremental change a maintainer would make"
  },
  {
   "where": "src/mcp/server.ts:286-289",
   "sibling": "a third file-path argument beside `vector_file` (e.g. `matrix_file` or `save_result_to`) that reaches the same load/save helpers",
   "why_realistic": "the published follow-up commit extended exactly this file from vector_file to saveVectorToFile, so another file argument is the natural next feature and would land outside both helpers"
  },
  {
   "where": "src/mcp/server.ts:1279-1291",
   "sibling": "a format/extension mapper that rewrites the protected filename (e.g. appending a default extension or normalising case) after the check",
   "why_realistic": "getFileFormat already reads the raw filePath and is still called before safeWriteVector, so a maintainer adding a default-extension rewrite is a small natural edit that could reintroduce a separator"
  },
  {
   "where": "src/consciousness-explorer/index.js:288-297",
   "sibling": "a session-named snapshot writer that derives the filename from state (session id + '.json') instead of taking it from the caller",
   "why_realistic": "the class already generates session/timestamp state, so writing an auto-named snapshot next to exportState is a plausible convenience method that never passes through the MCP handler"
  }
 ],
 "O9_family": "CWE-73 external control of file name or path (arbitrary file write/read, including traversal), same family as CWE-22",
 "O9_dos": false,
 "O10_build": {
  "language": "TypeScript + JavaScript (ESM, type: module)",
  "toolchain": "node >=16, npm, tsc via typescript ^5.9.2; `npm run build` = clean (rm -rf dist) + tsc + scripts/copy-wasm.js, and the wasm binaries are already committed under dist/wasm and src/consciousness-explorer/wasm so wasm-pack is not needed for the copy step",
  "services": [],
  "offline_after_build": true,
  "project_tests": "none for this area: tests/consciousness/ contains only impossible_to_fake_tests.ts and no test mentions export_state, import_state, saveVectorToFile or safe-path; package.json test = `npm run build && node --test tests/`, and tests/mcp/mcp-tool-tests.js does not cover the file-path tools"
 },
 "O11_fix_minutes": 45,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "src/consciousness-explorer/index.js, src/consciousness-explorer/mcp/server.js, src/consciousness-explorer/lib/safe-path.js (new), src/mcp/server.ts, src/mcp/safe-path.ts (new)",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 0,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Add a `..`/separator regex to the export_state inputSchema (or a path.resolve containment check inside handleExportState) and stop, leaving the library sinks, the separate saveVectorToFile / vector_file pair in src/mcp, and the direct CLI writeFileSync routes untouched."
 },
 "out_of_scope_notes": [
  "src/neural-pattern-recognition/cli/index.js:358,550,553 writes reports to an operator-supplied `--output` path in another sub-package of the same repo; same class as the uncovered CLI routes but not the advisory's MCP surface, so not pursued."
 ],
 "unverified": [
  "repo size in MB not measured (shell unavailable in this session), so tiny_repo/giant_repo are left unflagged and repo_mb is null",
  "build and tests were not executed (read-only screen): whether `npm run build` (tsc) and `node --test tests/` succeed at the pinned commit is untested",
  "present_in_latest is unknown for every O8 route because the candidate supplied no latest release",
  "whether ProofLogger.exportProof has a caller outside this repository is unknown; no in-repo caller was found",
  "O7 producer kind is recorded as handler because the sink argument is produced directly by the MCP request handler; the check lives in the library sink and never sees other producers of the same argument"
 ]
}
  ```
- Published fix sites:   - src/consciousness-explorer/index.js:288 — entry point: MCP tool `export_state` (src/consciousness-explorer/mcp/server.js:528-529) and CLI `export <filepath>` / `evolve --export <path>` (src/consciousness-explorer/bin/cli.js:46,353-361) [library class method (library layer, separate from the MCP handler)]
  - src/consciousness-explorer/index.js:297 — entry point: MCP tool `import_state` (src/consciousness-explorer/mcp/server.js:545-546) and CLI `import <filepath>` (src/consciousness-explorer/bin/cli.js:373-380) [library class method (read direction of the same sink family)]
  - src/consciousness-explorer/mcp/server.js:239-264 — entry point: MCP tool schemas `export_state` / `import_state` filepath property [MCP tool definition (stdio server, description/pattern only)]
  - fix.diff:353-589 — entry point: shared helper reached by both export_state and import_state [new helper module src/consciousness-explorer/lib/safe-path.js]
  - src/mcp/server.ts:1275 — entry point: MCP tool `saveVectorToFile` -> handleSaveVectorToFile (src/mcp/server.ts:1121-1140) [MCP tool handler in a second, separate server tree (src/mcp) of the same npm package]
  - src/mcp/server.ts:1184 — entry point: MCP tool `solveTrueSublinear` with the `vector_file` argument (src/mcp/server.ts:936-938) [MCP tool handler in the second server tree (read direction, lower-level helper)]
  - src/mcp/server.ts:366-379 — entry point: MCP tool schema for `saveVectorToFile` file_path property [MCP tool definition (stdio server, description/pattern only)]
  - fix.diff:5-168 — entry point: shared helper reached by saveVectorToFile and vector_file [new helper module src/mcp/safe-path.ts]
- Uncovered routes to confirm (pattern B):   - src/consciousness-explorer/bin/cli.js:127-129 — CLI `verify --export <path>` writes the verification report to any caller-supplied path with no containment (reason to dismiss: the path comes from a local CLI flag typed by the operator, not from a caller of the MCP server, so it is not attacker-controlled; still in latest: unknown)
  - src/consciousness-explorer/lib/proof-logger.js:647-656 — ProofLogger.exportProof(filepath) is a public library method that writes JSON to a caller-supplied path with no validation (reason to dismiss: no MCP tool or CLI command in the repo calls it, so it looks like an internal proof/debug helper rather than an exposed route; still in latest: unknown)
  - src/cli/index.ts:182 — main solver CLI writes solution/analysis/result/graph JSON to any `--output <path>` with no containment (reason to dismiss: operator-owned CLI flag on the local command line; the advisory's file arguments are MCP tool arguments, not CLI flags; still in latest: unknown)
  - dist/mcp/server.js:1121 — compiled copy of the same sink still resolves and writes an arbitrary path (reason to dismiss: dist/ is generated output; npm run build:ts regenerates it from src/mcp/server.ts, so it needs no fix of its own; still in latest: unknown)
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

## Environment (`tasks/sublinear-time-solver-s2/environment/Dockerfile`)
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

## Report to the solver (`tasks/sublinear-time-solver-s2/instruction.md`)
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

## Tests (`tasks/sublinear-time-solver-s2/tests/`)
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
- **Wrong-fix patches** go in `build/sublinear-time-solver-s2/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/sublinear-time-solver-s2/`:**
- `instruction.md`;
- `task.toml`, from `common/builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/sublinear-time-solver-s2/manifest.json`:**
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

**Also in `build/sublinear-time-solver-s2/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `common/builder/templates/` and `common/trial/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I common/gate/gate.py sublinear-time-solver-s2 --only static
python3 -I common/gate/gate.py sublinear-time-solver-s2 --only nop
python3 -I common/gate/gate.py sublinear-time-solver-s2 --only oracle
python3 -I common/gate/gate.py sublinear-time-solver-s2 --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/sublinear-time-solver-s2/`;
  - edit only `tasks/sublinear-time-solver-s2/`, `build/sublinear-time-solver-s2/` and, for pattern B, the register;
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
