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

Project root: `/home/mara/cwe-bench`. Task: `openlist-s2`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: ["GHSA-P6PH-3JX2-3337", "CVE-2026-102663", "GO-2026-6113"]; openlistteam/openlist; path-based authorization / information disclosure (CWE-200, CWE-639)
- Pinned (vulnerable) commit: 757f9d383db8e61d06a35c0b79701d6f85f75804. Published fix: 59bd3431408578f420895457554700cc9a52375a, 84ecda35aae2bd0020474086e6ddfd3aa2340679.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v2",
 "model": "deepseek-flash[1m]",
 "entry_id": "18575",
 "advisory_ids": [
  "GHSA-P6PH-3JX2-3337",
  "CVE-2026-102663",
  "GO-2026-6113"
 ],
 "repo": "openlistteam/openlist",
 "pinned_commit": "757f9d383db8e61d06a35c0b79701d6f85f75804",
 "fix_commits": [
  "59bd3431408578f420895457554700cc9a52375a",
  "84ecda35aae2bd0020474086e6ddfd3aa2340679"
 ],
 "trust_decision": {
  "summary": "A search hit is trusted because strings.HasPrefix(node.Parent, user.BasePath) says so, and the handler returns the backend's unfiltered hit count; the same raw string-prefix trust is repeated on share create/update, and the shared-path unwrap helper does no read-time revalidation of the creator's (reloaded) BasePath.",
  "evidence": [
   "server/handles/search.go:54",
   "server/handles/search.go:68",
   "server/handles/sharing.go:464",
   "server/handles/sharing.go:548",
   "internal/op/sharing.go:90-113",
   "pkg/utils/path.go:41-44"
  ]
 },
 "landing_point": {
  "where": "server/handles/search.go:47-68",
  "why": "The advisory title names the Bleve search path check, so an engineer first reads the handler loop that drops hits with strings.HasPrefix(node.Parent, user.BasePath) and then returns the backend's raw page and raw Total."
 },
 "fix_sites": [
  {
   "where": "server/handles/search.go:52-65",
   "entry_point": "GET/POST /api/fs/search (server/router.go:200)",
   "module_kind": "http_handler"
  },
  {
   "where": "server/handles/search.go:47-68",
   "entry_point": "GET/POST /api/fs/search (server/router.go:200)",
   "module_kind": "http_handler"
  },
  {
   "where": "internal/search/search.go:50-52",
   "entry_point": "internal dispatch used only by /api/fs/search",
   "module_kind": "search_dispatch"
  },
  {
   "where": "internal/search/bleve/search.go:28-58",
   "entry_point": "searcher backend reached through /api/fs/search",
   "module_kind": "search_backend"
  },
  {
   "where": "internal/search/searcher/searcher.go:14-31",
   "entry_point": "none (interface definition; reached only via /api/fs/search)",
   "module_kind": "search_api_interface"
  },
  {
   "where": "server/handles/sharing.go:461-468",
   "entry_point": "POST /api/share/update (server/router.go:238)",
   "module_kind": "http_handler"
  },
  {
   "where": "server/handles/sharing.go:545-552",
   "entry_point": "POST /api/share/create (server/router.go:237)",
   "module_kind": "http_handler"
  },
  {
   "where": "internal/op/sharing.go:90-113",
   "entry_point": "op layer called by /api/fs/get, /api/fs/list, /api/fs/archive/meta, /api/fs/archive/list, /sd/:sid/*, /sad/:sid/*",
   "module_kind": "op_layer"
  }
 ],
 "O1_entry_points": 9,
 "O2_out_of_scope_site": {
  "kind": "lower_level_api",
  "where": "internal/op/sharing.go:90-113"
 },
 "O3_reason_to_dismiss": "A solver can argue that re-validating a creator's current BasePath inside the sharing unwrap helper is a different feature from the Bleve search prefix bug, and that the raw file list a multi-file share shows at its root was chosen by the creator, so a later admin base-path change is configuration, not this advisory.",
 "O4_distance": {
  "files": 5,
  "packages": 4,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "A user must still reach and share their own base path exactly: hits whose Parent equals user.BasePath (files sitting directly in the base folder) and a share whose file equals the base path must stay visible. A naive fix that requires a separator, e.g. HasPrefix(s, user.BasePath+\"/\"), hides the base folder itself and makes search return nothing at the base root; the equality arm of utils.IsSubPath (pkg/utils/path.go:43) is what keeps both working (same shape at server/handles/search.go:54).",
  "where": "pkg/utils/path.go:41-44"
 },
 "O6_input_shapes": [
  "string-prefix sibling without a separator: base /data vs hit parent /database (the bug)",
  "exact equality: base /data vs hit parent /data, which must still pass",
  "multi-element files array in one create/update request (every element must be checked, not just the first)",
  "un-normalised paths (backslashes, //, '.', '..', trailing slash) on both sides of the comparison",
  "hit directly in the requested parent vs hit in a deep subfolder of it (subtree, not equality)",
  "pagination shapes: page>1, per_page smaller or larger than the visible result set, and per_page above the 1000-document batch with duplicate sort names on the batch boundary"
 ],
 "O7_producer": {
  "kind": "serializer",
  "where": "internal/op/sharing.go:62",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "Multi-file sharing root listing: POST/GET /api/fs/list with path /@s{sid} enumerates sharing.Files element by element and never calls GetSharingUnwrapPath, so the creator-BasePath revalidation added by the fix does not apply to it",
   "where": "internal/sharing/list.go:52-79",
   "reason_to_dismiss": "it only lists the paths the creator declared when the share was made, and the base-path change was an admin action on a different feature",
   "distance": "2 packages from server/handles (server/handles -> internal/sharing/list.go:70), a file and package the fix never touched",
   "present_in_latest": "unknown",
   "latest_where": ""
  }
 ],
 "O8b_injection_room": [
  {
   "where": "internal/op/sharing.go:115-122",
   "sibling": "a new caller of op.CreateSharing / op.UpdateSharing (share import, bulk create, bootstrap) that skips the handler-level BasePath check",
   "why_realistic": "the check lives only in the HTTP handlers (server/handles/sharing.go:464,548); the op-layer create/update accepts any Files slice, so a maintainer adding an import or bulk route would naturally call op directly"
  },
  {
   "where": "internal/sharing/list.go:52-79",
   "sibling": "a second walk over sharing.Files (download-all, share summary/manifest, torrent export) that maps each path without GetSharingUnwrapPath",
   "why_realistic": "the multi-file root listing already copies this pattern, so a new sharing feature would copy it again"
  },
  {
   "where": "internal/search/meilisearch/search.go:43-79",
   "sibling": "a backend-native SearchFiltered in the meilisearch searcher that reuses the existing page/hits-per-page query and TotalHits and forgets the requested-parent / base-path filter",
   "why_realistic": "the fix makes SearchFiltered an optional capability that each backend is expected to implement, and this backend already returns an unfiltered TotalHits"
  },
  {
   "where": "server/handles/sharing.go:545-552",
   "sibling": "an admin-on-behalf share creation path (req.CreatorName) that the loop skips because reqUser.IsAdmin()",
   "why_realistic": "that exempt branch already exists, and the fix only catches the result at read time"
  }
 ],
 "O9_family": "path-based authorization / information disclosure (CWE-200, CWE-639)",
 "O9_dos": false,
 "O10_build": {
  "language": "Go",
  "toolchain": "module go 1.25.0 with toolchain go1.26.4 (go.mod:3-5); CI builds with Go 1.26.4 and CGO (.github/workflows/build.yml:36,45)",
  "services": [],
  "offline_after_build": true,
  "project_tests": "No tests exist under internal/search or internal/sharing at the pinned commit (the fix's internal/search/search_test.go and internal/search/bleve/search_test.go are new files); pkg/utils/path_test.go covers FixAndCleanPath/GetPathHierarchy but not IsSubPath, and server/common/check_test.go:9 TestCoversPath exercises MetaCoversPath, which does call utils.IsSubPath."
 },
 "O11_fix_minutes": 45,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "server/handles/search.go, server/handles/sharing.go, internal/op/sharing.go, internal/search/search.go, internal/search/bleve/search.go, internal/search/searcher/searcher.go",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Swap strings.HasPrefix for utils.IsSubPath in server/handles/search.go and the two sharing handlers, and re-filter the returned page in the handler while still handing back the backend's raw Total."
 },
 "out_of_scope_notes": [
  "No out-of-scope findings; the strings.TrimPrefix(reqPath, user.BasePath) at server/webdav/webdav.go:778 only builds an href and is not a boundary check."
 ],
 "unverified": [
  "Repository size in MB (no shell in this session) - repo_mb left null and the tiny_repo/giant_repo flags are unset on that basis.",
  "Whether the internal/sharing/list.go root-listing route is still missing the revalidation in the latest release (no latest tree was supplied) - present_in_latest is unknown.",
  "Whether the meilisearch and db backends behave the same under the hidden tests (no running of the project permitted)."
 ]
}
  ```
- Published fix sites:   - server/handles/search.go:52-65 — entry point: GET/POST /api/fs/search (server/router.go:200) [http_handler]
  - server/handles/search.go:47-68 — entry point: GET/POST /api/fs/search (server/router.go:200) [http_handler]
  - internal/search/search.go:50-52 — entry point: internal dispatch used only by /api/fs/search [search_dispatch]
  - internal/search/bleve/search.go:28-58 — entry point: searcher backend reached through /api/fs/search [search_backend]
  - internal/search/searcher/searcher.go:14-31 — entry point: none (interface definition; reached only via /api/fs/search) [search_api_interface]
  - server/handles/sharing.go:461-468 — entry point: POST /api/share/update (server/router.go:238) [http_handler]
  - server/handles/sharing.go:545-552 — entry point: POST /api/share/create (server/router.go:237) [http_handler]
  - internal/op/sharing.go:90-113 — entry point: op layer called by /api/fs/get, /api/fs/list, /api/fs/archive/meta, /api/fs/archive/list, /sd/:sid/*, /sad/:sid/* [op_layer]
- Uncovered routes to confirm (pattern B):   - internal/sharing/list.go:52-79 — Multi-file sharing root listing: POST/GET /api/fs/list with path /@s{sid} enumerates sharing.Files element by element and never calls GetSharingUnwrapPath, so the creator-BasePath revalidation added by the fix does not apply to it (reason to dismiss: it only lists the paths the creator declared when the share was made, and the base-path change was an admin action on a different feature; still in latest: unknown)
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

## Environment (`tasks/openlist-s2/environment/Dockerfile`)
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

## Report to the solver (`tasks/openlist-s2/instruction.md`)
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

## Tests (`tasks/openlist-s2/tests/`)
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
- **Wrong-fix patches** go in `build/openlist-s2/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/openlist-s2/`:**
- `instruction.md`;
- `task.toml`, from `common/builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/openlist-s2/manifest.json`:**
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

**Also in `build/openlist-s2/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `common/builder/templates/` and `common/trial/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I common/gate/gate.py openlist-s2 --only static
python3 -I common/gate/gate.py openlist-s2 --only nop
python3 -I common/gate/gate.py openlist-s2 --only oracle
python3 -I common/gate/gate.py openlist-s2 --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/openlist-s2/`;
  - edit only `tasks/openlist-s2/`, `build/openlist-s2/` and, for pattern B, the register;
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
