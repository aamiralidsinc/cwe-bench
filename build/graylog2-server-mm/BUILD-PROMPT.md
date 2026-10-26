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

Project root: `/home/mara/cwe-bench`. Task: `graylog2-server-mm`. Pattern: `B`. Track: `injected`.

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
- Advisory: ["GHSA-M9C2-85GV-8XR5", "CVE-2026-69190"]; graylog2/graylog2-server; missing authorization / IDOR on share (grant) modification: edit permission used where ownership required (CWE-862/CWE-639)
- Pinned (vulnerable) commit: parent of 9303f395dd29c03abd8885f1c7d1c90f8aae72d4 (parent_commit not given in candidate). Published fix: 9303f395dd29c03abd8885f1c7d1c90f8aae72d4, ac1c0b19e3f44c2eed8e95f4d398ba455e30a8f2, c87879642537d07760a572ba01b76cb657582608, e98c6670d05748a9749ab0646be7f40561734b42.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "26905",
 "advisory_ids": [
  "GHSA-M9C2-85GV-8XR5",
  "CVE-2026-69190"
 ],
 "repo": "graylog2/graylog2-server",
 "pinned_commit": "parent of 9303f395dd29c03abd8885f1c7d1c90f8aae72d4 (parent_commit not given in candidate)",
 "fix_commits": [
  "9303f395dd29c03abd8885f1c7d1c90f8aae72d4",
  "ac1c0b19e3f44c2eed8e95f4d398ba455e30a8f2",
  "c87879642537d07760a572ba01b76cb657582608",
  "e98c6670d05748a9749ab0646be7f40561734b42"
 ],
 "trust_decision": {
  "summary": "Whether the caller may change grants (share/unshare, incl. owner capability) on a view; decided in PUT /views/{id}, which at the pinned commit only checks VIEW_EDIT/DASHBOARDS_EDIT (canUpdateView) and then applies the embedded share_request, while the dedicated shares endpoint requires entity:own.",
  "evidence": [
   "graylog2-server/src/main/java/org/graylog/plugins/views/search/rest/ViewsResource.java:393-405",
   "graylog2-server/src/main/java/org/graylog/plugins/views/search/rest/ViewsResource.java:407-412",
   "graylog2-server/src/main/java/org/graylog/plugins/views/search/rest/ViewsResource.java:287-292",
   "graylog2-server/src/main/java/org/graylog/plugins/views/search/permissions/SearchUser.java:97-101",
   "graylog2-server/src/main/java/org/graylog/security/rest/EntitySharesResource.java:160-165",
   "graylog2-server/src/main/java/org/graylog/security/rest/RestResourceWithOwnerCheck.java:31-41"
  ]
 },
 "landing_point": {
  "where": "graylog2-server/src/main/java/org/graylog/plugins/views/search/rest/ViewsResource.java:393",
  "why": "Summary names saved searches and dashboards; ViewsResource.update is the view update endpoint that forwards share_request to updateViewSharing."
 },
 "fix_sites": [
  {
   "where": "graylog2-server/src/main/java/org/graylog/plugins/views/search/rest/ViewsResource.java:398",
   "entry_point": "PUT /api/views/{id} (body: {entity, share_request})",
   "module_kind": "REST resource handler (only security-relevant hunk: fix.diff:77-78 adds checkOwnership when share_request present)"
  },
  {
   "where": "graylog2-server/src/main/java/org/graylog/plugins/views/search/rest/ViewsResource.java:111",
   "entry_point": "all /api/views routes (class now extends RestResourceWithOwnerCheck, fix.diff:43)",
   "module_kind": "class hierarchy change, enables checkOwnership"
  },
  {
   "where": "graylog2-server/src/main/java/org/graylog/plugins/views/search/rest/ViewsResource.java:281",
   "entry_point": "POST /api/views and POST /api/views/{id} (refactor to toGRNType only, fix.diff:52)",
   "module_kind": "refactor, not security-relevant"
  },
  {
   "where": "graylog2-server/src/main/java/org/graylog/plugins/views/search/rest/ViewsResource.java:289",
   "entry_point": "updateViewSharing helper (refactor only, fix.diff:60-62)",
   "module_kind": "refactor, not security-relevant"
  },
  {
   "where": "graylog2-server/src/main/java/org/graylog/plugins/views/search/rest/ViewsResource.java:437",
   "entry_point": "DELETE /api/views/{id} (refactor only, fix.diff:90-91)",
   "module_kind": "refactor, not security-relevant"
  }
 ],
 "O1_entry_points": 1,
 "O2_out_of_scope_site": {
  "kind": "none",
  "where": "Published fix touches only ViewsResource.java; no second implementation, lower-level API or wrapper was changed (fix.diff:10-93)."
 },
 "O3_reason_to_dismiss": "Content-pack install shares are applied only to entities 'belonging to' the installation and the route already requires content_pack:install (admin-level), so a solver can argue it is a separate feature, not the views update path in the report.",
 "O4_distance": {
  "files": 2,
  "packages": 2,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "A Manager (VIEW_EDIT, not owner) must still be able to save view/dashboard content via PUT /views/{id} without share_request; owners must still share via the update body; create/duplicate with share_request must still share the newly created view (caller becomes owner). A fix that rejects any update by non-owners, or any share_request on create, breaks these.",
  "where": "graylog2-server/src/main/java/org/graylog/plugins/views/search/rest/ViewsResource.java:271-292"
 },
 "O6_input_shapes": [
  "share_request present with grantee capabilities (incl. own capability) vs absent (fix.diff:78 checks only when present)",
  "share_request present but empty map (fix test fix.diff:135 uses empty map and still expects 403)",
  "dashboard vs search view type -> GRN type (fix.diff:66-68)",
  "NOT handled by published fix: body entity.id different from path {id} - check uses body dto.id() (fix.diff:78) while sharing uses persisted path id result.id() (graylog2-server/src/main/java/org/graylog/plugins/views/search/rest/ViewsResource.java:397-402)"
 ],
 "O7_producer": {
  "kind": "none",
  "where": "Grants are written by EntitySharesService.updatePrimaryEntityShares (graylog2-server/src/main/java/org/graylog/security/shares/EntitySharesService.java:258-340), a service sink, not a producer of cached/serialized state.",
  "check_calls_producer": null
 },
 "O8_uncovered_routes": [
  {
   "route": "PUT /api/views/{id} with body entity.id set to a view the caller owns and path id set to the target view: published check inspects the body id, sharing is applied to the path id.",
   "where": "graylog2-server/src/main/java/org/graylog/plugins/views/search/rest/ViewsResource.java:396-402",
   "reason_to_dismiss": "Frontend always sends matching ids; a solver copying the published fix uses dto.id() and verifies with matching ids.",
   "distance": "same method as landing point",
   "present_in_latest": "no",
   "latest_where": "latest/graylog2-server/src/main/java/org/graylog/plugins/views/search/rest/ViewsResource.java:412"
  },
  {
   "route": "POST /api/system/content_packs/{id}/{rev}/installations with share_request: entities found already on the system (findExisting, e.g. streams) are included in the installation and then shared via updateEntityShares with no ownership check.",
   "where": "graylog2-server/src/main/java/org/graylog2/contentpacks/ContentPackService.java:198-213",
   "reason_to_dismiss": "Different feature and entity types (not views), requires content_pack:install permission, and 'found on system' reuse looks like a legacy content-pack behaviour.",
   "distance": "different package (org.graylog2.contentpacks vs org.graylog.plugins.views.search.rest), 2 files away",
   "present_in_latest": "yes",
   "latest_where": "latest/graylog2-server/src/main/java/org/graylog2/contentpacks/ContentPackService.java:422"
  },
  {
   "route": "Content pack upgrade path re-shares all installation entities (incl. reused/updated pre-existing ones) via the same shareEntities helper without ownership check.",
   "where": "graylog2-server/src/main/java/org/graylog2/contentpacks/ContentPackService.java:375",
   "reason_to_dismiss": "Upgrade is admin-driven and only touches entities of a previous installation.",
   "distance": "different package, same file as previous route",
   "present_in_latest": "unknown",
   "latest_where": ""
  }
 ],
 "O8b_injection_room": [
  {
   "where": "graylog2-server/src/main/java/org/graylog/events/rest/EventDefinitionsResource.java:343-371",
   "sibling": "PUT /events/definitions/{id} accepting CreateEntityRequest with share_request and applying it after EVENT_DEFINITIONS_EDIT only",
   "why_realistic": "create() at :315-330 already takes CreateEntityRequest and shares; a maintainer aligning update with create (as ViewsResource does) would plausibly copy the sharing block without an owner check."
  },
  {
   "where": "graylog2-server/src/main/java/org/graylog/events/rest/EventNotificationsResource.java:212-232",
   "sibling": "PUT /events/notifications/{id} taking CreateEntityRequest and calling updateEntityShares after EVENT_NOTIFICATIONS_EDIT",
   "why_realistic": "Same create/update asymmetry as event definitions (create shares at :201-203); the frontend share-on-save UX would motivate it."
  },
  {
   "where": "graylog2-server/src/main/java/org/graylog2/rest/resources/streams/StreamResource.java:249-250",
   "sibling": "stream update route accepting share_request alongside stream edits",
   "why_realistic": "Stream create already accepts share_request; extending update mirrors the views pattern in a distant package."
  }
 ],
 "O9_family": "missing authorization / IDOR on share (grant) modification: edit permission used where ownership required (CWE-862/CWE-639)",
 "O9_dos": false,
 "O10_build": {
  "language": "Java (backend) + TypeScript web UI",
  "toolchain": "Maven wrapper (mvnw, pom.xml at repo root); web interface via node/yarn not needed for backend unit tests",
  "services": [
   "MongoDB and OpenSearch for a full server run; ViewsResourceTest is a mock-based unit test needing none"
  ],
  "offline_after_build": true,
  "project_tests": "graylog2-server/src/test/java/org/graylog/plugins/views/search/rest/ViewsResourceTest.java (mock Subject/ViewService); ContentPackServiceTest for shareEntities"
 },
 "O11_fix_minutes": 20,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "graylog2-server/src/main/java/org/graylog/plugins/views/search/rest/ViewsResource.java",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 0,
  "j_defence_ineffective": 0,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Add checkOwnership(grnType.toGRN(dto.id())) in update when share_request is present, using the body id (exactly the published fix), leaving the path/body id mismatch and content-pack share routes open."
 },
 "out_of_scope_notes": [
  "EntitySharesService.resolveImplicitGrants propagates a share request to synced entities without a per-entity ownership check (graylog2-server/src/main/java/org/graylog/security/shares/EntitySharesService.java:350-361); no SyncedEntitiesResolver implementation found in this repo."
 ],
 "unverified": [
  "pinned_commit hash not given (parent_commit null); assumed repo/ is the parent of the fix commit.",
  "Only one diff provided for four fix commits; other three assumed to be backports of the same ViewsResource change.",
  "repo_mb unknown (no shell/du used); Graylog server+web is likely well over 5 MB and under 1.5 GB.",
  "Whether content-pack findExisting reuse is reachable for an entity the installer does not own in practice (StreamFacade.findExisting matching rules) not traced; O8 route 2 relevance to this advisory's scope is a judgement call.",
  "Upgrade path (ContentPackService.java:244-258) has no REST caller in this repo; may only be reached from enterprise plugins.",
  "Latest line for upgrade shareEntities call not located; marked unknown.",
  "Advisory full text not provided; trust decision derived from the summary, changelog (fix.diff:8) and code."
 ]
}
  ```
- Published fix sites:   - graylog2-server/src/main/java/org/graylog/plugins/views/search/rest/ViewsResource.java:398 — entry point: PUT /api/views/{id} (body: {entity, share_request}) [REST resource handler (only security-relevant hunk: fix.diff:77-78 adds checkOwnership when share_request present)]
  - graylog2-server/src/main/java/org/graylog/plugins/views/search/rest/ViewsResource.java:111 — entry point: all /api/views routes (class now extends RestResourceWithOwnerCheck, fix.diff:43) [class hierarchy change, enables checkOwnership]
  - graylog2-server/src/main/java/org/graylog/plugins/views/search/rest/ViewsResource.java:281 — entry point: POST /api/views and POST /api/views/{id} (refactor to toGRNType only, fix.diff:52) [refactor, not security-relevant]
  - graylog2-server/src/main/java/org/graylog/plugins/views/search/rest/ViewsResource.java:289 — entry point: updateViewSharing helper (refactor only, fix.diff:60-62) [refactor, not security-relevant]
  - graylog2-server/src/main/java/org/graylog/plugins/views/search/rest/ViewsResource.java:437 — entry point: DELETE /api/views/{id} (refactor only, fix.diff:90-91) [refactor, not security-relevant]
- Uncovered routes to confirm (pattern B):   - graylog2-server/src/main/java/org/graylog/plugins/views/search/rest/ViewsResource.java:396-402 — PUT /api/views/{id} with body entity.id set to a view the caller owns and path id set to the target view: published check inspects the body id, sharing is applied to the path id. (reason to dismiss: Frontend always sends matching ids; a solver copying the published fix uses dto.id() and verifies with matching ids.; still in latest: no)
  - graylog2-server/src/main/java/org/graylog2/contentpacks/ContentPackService.java:198-213 — POST /api/system/content_packs/{id}/{rev}/installations with share_request: entities found already on the system (findExisting, e.g. streams) are included in the installation and then shared via updateEntityShares with no ownership check. (reason to dismiss: Different feature and entity types (not views), requires content_pack:install permission, and 'found on system' reuse looks like a legacy content-pack behaviour.; still in latest: yes)
  - graylog2-server/src/main/java/org/graylog2/contentpacks/ContentPackService.java:375 — Content pack upgrade path re-shares all installation entities (incl. reused/updated pre-existing ones) via the same shareEntities helper without ownership check. (reason to dismiss: Upgrade is admin-driven and only touches entities of a previous installation.; still in latest: unknown)
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

## Environment (`tasks/graylog2-server-mm/environment/Dockerfile`)
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

## Report to the solver (`tasks/graylog2-server-mm/instruction.md`)
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

## Tests (`tasks/graylog2-server-mm/tests/`)
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
- **Wrong-fix patches** go in `build/graylog2-server-mm/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/graylog2-server-mm/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/graylog2-server-mm/manifest.json`:**
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

**Also in `build/graylog2-server-mm/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py graylog2-server-mm --only static
python3 -I builder/gate.py graylog2-server-mm --only nop
python3 -I builder/gate.py graylog2-server-mm --only oracle
python3 -I builder/gate.py graylog2-server-mm --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/graylog2-server-mm/`;
  - edit only `tasks/graylog2-server-mm/`, `build/graylog2-server-mm/` and, for pattern B, the register;
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
