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

Project root: `/home/mara/cwe-bench`. Task: `langflow-s3`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: ["GHSA-4HMC-CFM3-W43C", "CVE-2026-105699"]; langflow-ai/langflow; CWE-639 authorization bypass through user-controlled key (IDOR) combined with CWE-22 path traversal
- Pinned (vulnerable) commit: cae2bdfef625fcc5998c9a88ffa8f0cc562ab32b. Published fix: b8fe970493fd5fb2e1fc71dfccc79f90b76058fa, f0fd436fe9829192ee550e6cb46961a01dd37032.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v2",
 "model": "deepseek-flash[1m]",
 "entry_id": "794",
 "advisory_ids": [
  "GHSA-4HMC-CFM3-W43C",
  "CVE-2026-105699"
 ],
 "repo": "langflow-ai/langflow",
 "pinned_commit": "cae2bdfef625fcc5998c9a88ffa8f0cc562ab32b",
 "fix_commits": [
  "b8fe970493fd5fb2e1fc71dfccc79f90b76058fa",
  "f0fd436fe9829192ee550e6cb46961a01dd37032"
 ],
 "trust_decision": {
  "summary": "An authenticated MCP client controls the last two path segments of a read_resource URI and the server performs no ownership check at all: the namespace segment (flow id or user id) is passed straight into the storage service, so any user can list every user's flows/files and read any flow's stored file. Decided by the absence of a user/project filter in handle_read_resource and handle_list_resources, plus storage services that compose data_dir/flow_id/file_name without any containment check on the read path.",
  "evidence": [
   "src/backend/base/langflow/api/v1/mcp_utils.py:161-183",
   "src/backend/base/langflow/api/v1/mcp_utils.py:103-107",
   "src/backend/base/langflow/api/v1/mcp_utils.py:336-349",
   "src/backend/base/langflow/services/storage/local.py:193",
   "src/lfx/src/lfx/services/storage/local.py:143"
  ]
 },
 "landing_point": {
  "where": "src/backend/base/langflow/api/v1/mcp_utils.py:161",
  "why": "The advisory title names unscoped MCP resource handlers; the read handler is the sink where a client-supplied namespace and filename go straight to storage, so an engineer looks here first."
 },
 "fix_sites": [
  {
   "where": "src/backend/base/langflow/api/v1/mcp_utils.py:161-195",
   "entry_point": "MCP read_resource on the global server (GET /api/v1/mcp/sse, /api/v1/mcp/streamable)",
   "module_kind": "api handler (MCP protocol handler)"
  },
  {
   "where": "src/backend/base/langflow/api/v1/mcp_utils.py:81-158",
   "entry_point": "MCP list_resources on the global server (GET /api/v1/mcp/sse, /api/v1/mcp/streamable)",
   "module_kind": "api handler (MCP protocol handler)"
  },
  {
   "where": "src/backend/base/langflow/api/v1/mcp_utils.py:329-399",
   "entry_point": "MCP list_tools on the global server (GET /api/v1/mcp/sse, /api/v1/mcp/streamable)",
   "module_kind": "api handler (MCP protocol handler)"
  },
  {
   "where": "src/backend/base/langflow/api/v1/mcp_projects.py:1249-1252",
   "entry_point": "MCP project server (GET /api/v1/mcp/project/{project_id}/sse, /api/v1/mcp/project/{project_id}/streamable)",
   "module_kind": "wrapper (per-project MCP server adapter)"
  },
  {
   "where": "src/backend/base/langflow/services/storage/local.py:100-288",
   "entry_point": "StorageService.save_file/get_file/get_file_stream/delete_file/get_file_size, reached from MCP read_resource and from /api/v1/files/* and /api/v2/files/*",
   "module_kind": "service (first storage implementation)"
  },
  {
   "where": "src/lfx/src/lfx/services/storage/local.py:102-223",
   "entry_point": "lfx StorageService public API used by components via lfx.services.deps.get_storage_service (src/lfx/src/lfx/services/deps.py:84)",
   "module_kind": "service (second implementation, separate package, no defence at pinned commit)"
  }
 ],
 "O1_entry_points": 4,
 "O2_out_of_scope_site": {
  "kind": "second_implementation",
  "where": "src/lfx/src/lfx/services/storage/local.py:130-153"
 },
 "O3_reason_to_dismiss": "lfx is a separate library package, and what the Langflow backend actually wires is langflow.services.storage.local via StorageServiceFactory (src/backend/base/langflow/services/storage/factory.py:18-22), so the reported MCP route is already fixed once that class is hardened.",
 "O4_distance": {
  "files": 4,
  "packages": 2,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "User-level files uploaded through /api/v2/files are stored under the owner's user id, not a flow id, and the global MCP server must keep listing and reading them (namespace segment may be a user id); a fix that requires the namespace to be a flow the caller owns breaks File Manager uploads. Project-scoped resource listing must also keep returning the project's own flow files.",
  "where": "src/backend/base/langflow/api/v1/mcp_utils.py:136-153"
 },
 "O6_input_shapes": [
  "percent-encoded traversal in filename after urlparse split, e.g. ..%2F..%2F..%2Fetc%2Fpasswd",
  "literal ../ segments",
  "backslash ..\\\\..\\\\ segments",
  "nested subpath such as sub/dir.txt",
  "empty filename",
  "namespace segment is a flow UUID",
  "namespace segment is the caller's own user UUID (user bucket)",
  "project_id absent (global server) vs UUID/str (project server)",
  "current_user context present vs absent"
 ],
 "O7_producer": {
  "kind": "handler",
  "where": "src/backend/base/langflow/api/v1/mcp_utils.py:109-153",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "Storage path-builder primitives still compose data_dir/flow_id/file_name with no containment check after the fix; flow-saved file_path values and tool-mode file_path_str reach them via resolve_component_path/get_full_path and then a real file open (src/lfx/src/lfx/graph/vertex/param_handler.py:155-171, src/lfx/src/lfx/components/files_and_knowledge/file.py:603-619, src/lfx/src/lfx/custom/custom_component/custom_component.py:184-188)",
   "where": "src/lfx/src/lfx/services/storage/local.py:40-63",
   "reason_to_dismiss": "build_full_path/resolve_component_path are just path-string helpers, not reads; the values come from flow authors and component code rather than from an MCP client, so the storage containment check is argued not to belong there.",
   "distance": "same lfx package, 2 files from the storage module; also present in the backend implementation (src/backend/base/langflow/services/storage/local.py:41-60), i.e. 2 packages from the landing point",
   "present_in_latest": "unknown",
   "latest_where": ""
  }
 ],
 "O8b_injection_room": [
  {
   "where": "src/backend/base/langflow/api/v2/files.py:556",
   "sibling": "A project/flow-scoped file-download route that passes a namespace taken from the stored File row (instead of str(current_user.id)) into get_file.",
   "why_realistic": "The file manager already stores paths with a namespace prefix and re-derives file_name from them, so a sibling that forwards the stored parent directory is a natural refactor and would reopen cross-namespace reads."
  },
  {
   "where": "src/backend/base/langflow/api/v1/mcp_projects.py:214-292",
   "sibling": "A project file-listing endpoint that queries Flow by folder_id without the owner filter, mirroring the list_resources bug the fix closes.",
   "why_realistic": "This builder already issues project-scoped Flow queries and returns them to an MCP client; copying its query shape for a files endpoint is a one-line mistake."
  },
  {
   "where": "src/lfx/src/lfx/schema/image.py:144",
   "sibling": "Image/attachment loading that splits a stored path into (flow_id, file_name) and passes both straight to get_file.",
   "why_realistic": "It already calls parse_file_path on persisted state, so a crafted stored path (rename after the check) would select another namespace's directory."
  }
 ],
 "O9_family": "CWE-639 authorization bypass through user-controlled key (IDOR) combined with CWE-22 path traversal",
 "O9_dos": false,
 "O10_build": {
  "language": "Python (monorepo: langflow backend + lfx library + React frontend)",
  "toolchain": "uv / pytest / ruff; packages under src/backend/base and src/lfx",
  "services": [],
  "offline_after_build": true,
  "project_tests": "src/backend/tests/unit/api/v1/test_mcp_utils.py (FakeSession/FakeStorageService, monkeypatched deps), src/backend/tests/unit/services/storage/test_local_storage_service.py (tmp_path fixtures), src/lfx/tests/unit/services/test_minimal_services.py"
 },
 "O11_fix_minutes": 50,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "src/backend/base/langflow/api/v1/mcp_utils.py, src/backend/base/langflow/api/v1/mcp_projects.py, src/backend/base/langflow/services/storage/local.py, src/lfx/src/lfx/services/storage/local.py",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Add a '..' check on the filename inside handle_read_resource (or only guard get_file in the langflow LocalStorageService) and call it fixed."
 },
 "out_of_scope_notes": [
  "S3StorageService (src/backend/base/langflow/services/storage/s3.py:187-217) composes keys with the same string pattern the fix hardened, but S3 keys are opaque and never normalised to a filesystem path, so it has no traversal defect and was not pursued."
 ],
 "unverified": [
  "repo_mb: no shell available to measure the tree; source is clearly well under the 1.5 GB giant threshold but the exact size was not measured",
  "Which storage class is registered at runtime in each deployment mode was read only through the factories/decorators, not executed",
  "present_in_latest for O8: no latest checkout was supplied, so it is unknown whether the path-builder route is still unvalidated today"
 ]
}
  ```
- Published fix sites:   - src/backend/base/langflow/api/v1/mcp_utils.py:161-195 — entry point: MCP read_resource on the global server (GET /api/v1/mcp/sse, /api/v1/mcp/streamable) [api handler (MCP protocol handler)]
  - src/backend/base/langflow/api/v1/mcp_utils.py:81-158 — entry point: MCP list_resources on the global server (GET /api/v1/mcp/sse, /api/v1/mcp/streamable) [api handler (MCP protocol handler)]
  - src/backend/base/langflow/api/v1/mcp_utils.py:329-399 — entry point: MCP list_tools on the global server (GET /api/v1/mcp/sse, /api/v1/mcp/streamable) [api handler (MCP protocol handler)]
  - src/backend/base/langflow/api/v1/mcp_projects.py:1249-1252 — entry point: MCP project server (GET /api/v1/mcp/project/{project_id}/sse, /api/v1/mcp/project/{project_id}/streamable) [wrapper (per-project MCP server adapter)]
  - src/backend/base/langflow/services/storage/local.py:100-288 — entry point: StorageService.save_file/get_file/get_file_stream/delete_file/get_file_size, reached from MCP read_resource and from /api/v1/files/* and /api/v2/files/* [service (first storage implementation)]
  - src/lfx/src/lfx/services/storage/local.py:102-223 — entry point: lfx StorageService public API used by components via lfx.services.deps.get_storage_service (src/lfx/src/lfx/services/deps.py:84) [service (second implementation, separate package, no defence at pinned commit)]
- Uncovered routes to confirm (pattern B):   - src/lfx/src/lfx/services/storage/local.py:40-63 — Storage path-builder primitives still compose data_dir/flow_id/file_name with no containment check after the fix; flow-saved file_path values and tool-mode file_path_str reach them via resolve_component_path/get_full_path and then a real file open (src/lfx/src/lfx/graph/vertex/param_handler.py:155-171, src/lfx/src/lfx/components/files_and_knowledge/file.py:603-619, src/lfx/src/lfx/custom/custom_component/custom_component.py:184-188) (reason to dismiss: build_full_path/resolve_component_path are just path-string helpers, not reads; the values come from flow authors and component code rather than from an MCP client, so the storage containment check is argued not to belong there.; still in latest: unknown)
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

## Environment (`tasks/langflow-s3/environment/Dockerfile`)
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

## Report to the solver (`tasks/langflow-s3/instruction.md`)
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

## Tests (`tasks/langflow-s3/tests/`)
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
- **Wrong-fix patches** go in `build/langflow-s3/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/langflow-s3/`:**
- `instruction.md`;
- `task.toml`, from `common/builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/langflow-s3/manifest.json`:**
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

**Also in `build/langflow-s3/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `common/builder/templates/` and `common/trial/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I common/gate/gate.py langflow-s3 --only static
python3 -I common/gate/gate.py langflow-s3 --only nop
python3 -I common/gate/gate.py langflow-s3 --only oracle
python3 -I common/gate/gate.py langflow-s3 --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/langflow-s3/`;
  - edit only `tasks/langflow-s3/`, `build/langflow-s3/` and, for pattern B, the register;
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
