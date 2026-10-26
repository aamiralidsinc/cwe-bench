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

Project root: `/home/mara/cwe-bench`. Task: `grpc-node-ds`. Pattern: `B`. Track: `injected`.

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
- Advisory: ["GHSA-F596-WHHP-79R4", "CVE-2026-101915"]; grpc/grpc-node; information exposure through server error messages (CWE-550)
- Pinned (vulnerable) commit: 651cbeec6b4d6d11cbee91c042946d2fe5968ef6. Published fix: 350de32860428cc62473a00bee4035360690ffea, 7c5c5181159c6ddd292805881ef2cdec29bb475f, e8329b122ca99ba10877e990c2f6edd40224fd0d.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v2",
 "model": "claude-opus-5-5",
 "entry_id": "10926",
 "advisory_ids": [
  "GHSA-F596-WHHP-79R4",
  "CVE-2026-101915"
 ],
 "repo": "grpc/grpc-node",
 "pinned_commit": "651cbeec6b4d6d11cbee91c042946d2fe5968ef6",
 "fix_commits": [
  "350de32860428cc62473a00bee4035360690ffea",
  "7c5c5181159c6ddd292805881ef2cdec29bb475f",
  "e8329b122ca99ba10877e990c2f6edd40224fd0d"
 ],
 "trust_decision": {
  "summary": "The server decides what text from a server-side exception goes into the client-visible status details. At the pinned commit, every handler type's catch block copies the thrown Error.message straight into sendStatus.",
  "evidence": [
   "packages/grpc-js/src/server.ts:2038-2048",
   "packages/grpc-js/src/server.ts:2087-2097",
   "packages/grpc-js/src/server.ts:2155-2165",
   "packages/grpc-js/src/server.ts:2186-2196"
  ]
 },
 "landing_point": {
  "where": "packages/grpc-js/src/server.ts:2043",
  "why": "The literal string 'Server method handler threw error' in handleUnary matches the summary, and grepping for it finds all four sites."
 },
 "fix_sites": [
  {
   "where": "packages/grpc-js/src/server.ts:2040-2047",
   "entry_point": "Server.addService unary handler (handleUnary via _runHandlerForCall, server.ts:1469)",
   "module_kind": "core server handler dispatch"
  },
  {
   "where": "packages/grpc-js/src/server.ts:2089-2096",
   "entry_point": "Server.addService client-streaming handler (handleClientStreaming, server.ts:1471)",
   "module_kind": "core server handler dispatch"
  },
  {
   "where": "packages/grpc-js/src/server.ts:2157-2164",
   "entry_point": "Server.addService server-streaming handler (handleServerStreaming, server.ts:1473)",
   "module_kind": "core server handler dispatch"
  },
  {
   "where": "packages/grpc-js/src/server.ts:2188-2195",
   "entry_point": "Server.addService bidi-streaming handler (handleBidiStreaming, server.ts:1475)",
   "module_kind": "core server handler dispatch"
  },
  {
   "where": "fix.diff:274-275",
   "entry_point": "process env GRPC_NODE_DEBUG_SEND_ERROR_DETAILS (new opt-in flag in packages/grpc-js/src/environment.ts)",
   "module_kind": "config/environment"
  }
 ],
 "O1_entry_points": 4,
 "O2_out_of_scope_site": {
  "kind": "none",
  "where": "All four published sites are sibling catch blocks in one file (packages/grpc-js/src/server.ts:2038-2196). None of them looks out of scope."
 },
 "O3_reason_to_dismiss": "For the serializer/deserializer routes: 'the advisory is about errors thrown by method handlers; serialization errors are library/codec errors, not handler errors, and they help with debugging.'",
 "O4_distance": {
  "files": 2,
  "packages": 1,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "A handler can deliberately send an error to the client with callback(err) or stream.emit('error', err), including a plain Error whose message becomes the status details. The project's tests rely on this. A fix that also sanitises serverErrorToStatus would break it.",
  "where": "packages/grpc-js/src/server-call.ts:62-84; packages/grpc-js/src/server-call.ts:200-203; packages/grpc-js/test/test-server-errors.ts:464-473"
 },
 "O6_input_shapes": [
  "synchronous throw of an Error from the handler in each of the 4 call types (unary, clientStream, serverStream, bidi); no other shape is handled (async rejections and thrown non-Errors are not special-cased)"
 ],
 "O7_producer": {
  "kind": "serializer",
  "where": "packages/grpc-js/src/server-interceptors.ts:719 (handler.serialize = app-supplied responseSerialize, wired at packages/grpc-js/src/server-interceptors.ts:1056); its thrown message is sent at packages/grpc-js/src/server-interceptors.ts:893-899",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "If the app-supplied responseSerialize throws, its exception message is sent to the client in the status details (sendMessage catch).",
   "where": "packages/grpc-js/src/server-interceptors.ts:892-901",
   "reason_to_dismiss": "Serializer failure, not a 'method handler' throw; the message carries a fixed prefix and the existing tests exercise it (test-server-errors.ts:174-189).",
   "distance": "another file in the same package (server.ts -> server-interceptors.ts)",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "If the app-supplied requestDeserialize throws, its exception message is sent to the client in the status details.",
   "where": "packages/grpc-js/src/server-interceptors.ts:791-798",
   "reason_to_dismiss": "A request-parsing error caused by client input, so arguably the client is entitled to the diagnostic.",
   "distance": "another file in the same package",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "An HTTP/2 stream write error message is sent to the client in the status details.",
   "where": "packages/grpc-js/src/server-interceptors.ts:921-928",
   "reason_to_dismiss": "Transport-level error, not application code; the message is unlikely to hold app secrets.",
   "distance": "another file in the same package",
   "present_in_latest": "unknown",
   "latest_where": ""
  }
 ],
 "O8b_injection_room": [
  {
   "where": "packages/grpc-js/src/server-call.ts:200-203",
   "sibling": "A stream 'error' listener that formats a non-status thrown Error (for example from a piped source) as 'Server stream error ${err.message}'.",
   "why_realistic": "Errors from Node stream pipelines arrive through the same 'error' event that the deliberate status API uses, so a maintainer could plausibly add a helper there that formats the message."
  },
  {
   "where": "packages/grpc-js/src/server-interceptors.ts:861-868",
   "sibling": "A try/catch around listener.onReceiveMetadata / user server interceptors that sends `Interceptor threw error ${err.message}`.",
   "why_realistic": "Server interceptors are user code at a lower layer; mirroring the handler catch there is a natural feature addition."
  },
  {
   "where": "packages/grpc-js/src/server.ts:1979-2057",
   "sibling": "A .catch on a Promise returned by handler.func (async handlers) that formats the rejection message.",
   "why_realistic": "handleUnary is already async, and supporting async handlers is a commonly requested feature."
  }
 ],
 "O9_family": "information exposure through server error messages (CWE-550)",
 "O9_dos": false,
 "O10_build": {
  "language": "TypeScript",
  "toolchain": "Node.js + npm, tsc (typescript ^5.3.3), gulp + mocha tests",
  "services": [],
  "offline_after_build": true,
  "project_tests": "packages/grpc-js/test/test-server-errors.ts (thrown errors, serialization failure, emit('error') status propagation); localhost-only servers"
 },
 "O11_fix_minutes": 15,
 "O12_red_flags": [],
 "O13_recall_risk": "low",
 "pattern_fit": "B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "packages/grpc-js/src/server.ts, packages/grpc-js/src/environment.ts",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 0,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Replace the four catch-block details with a generic 'Unknown error' and stop, or over-fix by sanitising serverErrorToStatus, which breaks deliberate callback(err)/emit('error') details."
 },
 "out_of_scope_notes": [
  "Trace logging of status details at packages/grpc-js/src/server-interceptors.ts:939-946 is server-side only, so it is not part of this sink.",
  "The decoder error message at packages/grpc-js/src/server-interceptors.ts:835-836 is library-generated size text, not reviewed further."
 ],
 "unverified": [
  "Repo size in MB was not measured (no shell).",
  "Whether the O8 routes still exist in latest is unknown (no latest tree provided).",
  "Whether the advisory text names only the 'thrown by method handlers' path, and so whether O8 routes would be judged covered by the property, is inferred from the summary only.",
  "The weak point is that the published fix is 4 copies of one concept in one file (a WHERE-type pattern); how-type room is limited to the serializer route."
 ]
}
  ```
- Published fix sites:   - packages/grpc-js/src/server.ts:2040-2047 — entry point: Server.addService unary handler (handleUnary via _runHandlerForCall, server.ts:1469) [core server handler dispatch]
  - packages/grpc-js/src/server.ts:2089-2096 — entry point: Server.addService client-streaming handler (handleClientStreaming, server.ts:1471) [core server handler dispatch]
  - packages/grpc-js/src/server.ts:2157-2164 — entry point: Server.addService server-streaming handler (handleServerStreaming, server.ts:1473) [core server handler dispatch]
  - packages/grpc-js/src/server.ts:2188-2195 — entry point: Server.addService bidi-streaming handler (handleBidiStreaming, server.ts:1475) [core server handler dispatch]
  - fix.diff:274-275 — entry point: process env GRPC_NODE_DEBUG_SEND_ERROR_DETAILS (new opt-in flag in packages/grpc-js/src/environment.ts) [config/environment]
- Uncovered routes to confirm (pattern B):   - packages/grpc-js/src/server-interceptors.ts:892-901 — If the app-supplied responseSerialize throws, its exception message is sent to the client in the status details (sendMessage catch). (reason to dismiss: Serializer failure, not a 'method handler' throw; the message carries a fixed prefix and the existing tests exercise it (test-server-errors.ts:174-189).; still in latest: unknown)
  - packages/grpc-js/src/server-interceptors.ts:791-798 — If the app-supplied requestDeserialize throws, its exception message is sent to the client in the status details. (reason to dismiss: A request-parsing error caused by client input, so arguably the client is entitled to the diagnostic.; still in latest: unknown)
  - packages/grpc-js/src/server-interceptors.ts:921-928 — An HTTP/2 stream write error message is sent to the client in the status details. (reason to dismiss: Transport-level error, not application code; the message is unlikely to hold app secrets.; still in latest: unknown)
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

## Environment (`tasks/grpc-node-ds/environment/Dockerfile`)
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

## Report to the solver (`tasks/grpc-node-ds/instruction.md`)
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

## Tests (`tasks/grpc-node-ds/tests/`)
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
- **Wrong-fix patches** go in `build/grpc-node-ds/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/grpc-node-ds/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/grpc-node-ds/manifest.json`:**
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

**Also in `build/grpc-node-ds/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py grpc-node-ds --only static
python3 -I builder/gate.py grpc-node-ds --only nop
python3 -I builder/gate.py grpc-node-ds --only oracle
python3 -I builder/gate.py grpc-node-ds --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/grpc-node-ds/`;
  - edit only `tasks/grpc-node-ds/`, `build/grpc-node-ds/` and, for pattern B, the register;
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
