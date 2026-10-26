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

Project root: `/home/mara/cwe-bench`. Task: `perses-ds`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: ["GHSA-4227-9989-JRHX", "CVE-2026-63199", "GO-2026-6514"]; perses/perses; CWE-862 missing authorization (A01 broken access control): secret use by reference without checking the referrer's read permission on the secret
- Pinned (vulnerable) commit: 51b7c0bba66fd2a725de9dc885808c68fbd79091. Published fix: 2368c9ef4eb0a70fbca5df69aa20e595821ab625.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v2",
 "model": "claude-opus-5-5",
 "entry_id": "15545",
 "advisory_ids": [
  "GHSA-4227-9989-JRHX",
  "CVE-2026-63199",
  "GO-2026-6514"
 ],
 "repo": "perses/perses",
 "pinned_commit": "51b7c0bba66fd2a725de9dc885808c68fbd79091",
 "fix_commits": [
  "2368c9ef4eb0a70fbca5df69aa20e595821ab625"
 ],
 "trust_decision": {
  "summary": "Whether a caller may make the server attach a stored (project or global) secret to an outbound datasource request: the proxy resolves the secret named in a datasource spec with no secret-read check, and the spec can be authored by anyone holding datasource create/update (saved) or datasource create (unsaved) rights; the fix gates secret references with Secret/GlobalSecret read at save time (datasource services) and at proxy time for unsaved specs.",
  "evidence": [
   "internal/api/impl/proxy/proxy.go:214-228",
   "internal/api/impl/proxy/projectdatasource.go:47-58",
   "internal/api/impl/proxy/projectdatasource.go:89-100",
   "internal/api/impl/proxy/globaldatasource.go:47-58",
   "internal/api/impl/v1/datasource/service.go:44-50",
   "internal/api/toolbox/toolbox.go:147-160",
   "fix.diff:235-271"
  ]
 },
 "landing_point": {
  "where": "internal/api/impl/proxy/proxy.go:217",
  "why": "Summary says 'datasource proxy ... secret disclosure'; newProxy is where retrieveSecret is called for the secret named in the spec, and the three unsaved proxy handlers that feed it sit next to it."
 },
 "fix_sites": [
  {
   "where": "internal/api/impl/proxy/projectdatasource.go:40-59",
   "entry_point": "POST <apiPrefix>/proxy/unsaved/projects/:project/datasources/* (internal/api/impl/proxy/proxy.go:163, group internal/api/core/server.go:176)",
   "module_kind": "HTTP proxy handler (landing package)"
  },
  {
   "where": "internal/api/impl/proxy/globaldatasource.go:41-59",
   "entry_point": "POST <apiPrefix>/proxy/unsaved/globaldatasources/* (internal/api/impl/proxy/proxy.go:156)",
   "module_kind": "HTTP proxy handler (landing package)"
  },
  {
   "where": "internal/api/impl/proxy/localdatasource.go:41-60",
   "entry_point": "POST <apiPrefix>/proxy/unsaved/projects/:project/dashboards/:dashboard/datasources/* (internal/api/impl/proxy/proxy.go:170)",
   "module_kind": "HTTP proxy handler (landing package)"
  },
  {
   "where": "internal/api/impl/proxy/projectdatasource.go:29-38",
   "entry_point": "refactor only: retrieveSecret now passed in; saved route ANY <apiPrefix>/proxy/projects/:project/datasources/:name (internal/api/impl/proxy/proxy.go:159-161) keeps unchecked lookup (fix.diff:148-150)",
   "module_kind": "HTTP proxy helper"
  },
  {
   "where": "internal/api/impl/proxy/globaldatasource.go:29-39",
   "entry_point": "refactor only; saved global route (internal/api/impl/proxy/proxy.go:152-154) keeps unchecked lookup (fix.diff:61-63)",
   "module_kind": "HTTP proxy helper"
  },
  {
   "where": "internal/api/impl/proxy/localdatasource.go:29-39",
   "entry_point": "refactor only; saved dashboard route (internal/api/impl/proxy/proxy.go:166-168) keeps unchecked lookup (fix.diff:105-107)",
   "module_kind": "HTTP proxy helper"
  },
  {
   "where": "internal/api/impl/v1/datasource/service.go:44",
   "entry_point": "POST project datasources via generic toolbox Create (internal/api/toolbox/toolbox.go:147-160)",
   "module_kind": "CRUD service, save path (different package from proxy)"
  },
  {
   "where": "internal/api/impl/v1/datasource/service.go:64",
   "entry_point": "PUT project datasource via toolbox Update (internal/api/toolbox/toolbox.go:162-175)",
   "module_kind": "CRUD service, save path"
  },
  {
   "where": "internal/api/impl/v1/globaldatasource/service.go:44",
   "entry_point": "POST global datasources via toolbox Create",
   "module_kind": "CRUD service, save path"
  },
  {
   "where": "internal/api/impl/v1/globaldatasource/service.go:64",
   "entry_point": "PUT global datasource via toolbox Update",
   "module_kind": "CRUD service, save path"
  },
  {
   "where": "internal/api/dependency/service_manager.go:127",
   "entry_point": "server wiring (authz injected into datasource service)",
   "module_kind": "dependency wiring"
  },
  {
   "where": "internal/api/dependency/service_manager.go:131",
   "entry_point": "server wiring (authz injected into globaldatasource service)",
   "module_kind": "dependency wiring"
  }
 ],
 "O1_entry_points": 7,
 "O2_out_of_scope_site": {
  "kind": "save_reload_or_serialization",
  "where": "internal/api/impl/v1/datasource/service.go:44-70 and internal/api/impl/v1/globaldatasource/service.go:44-70 (fix.diff:200-226, fix.diff:330-356): the secret reference is persisted by the CRUD save path and later used by the saved-proxy routes, which the fix deliberately leaves without a secret check (fix.diff:61-63, fix.diff:148-150)"
 },
 "O3_reason_to_dismiss": "The report is about the datasource *proxy*; the CRUD services in impl/v1 already pass the toolbox Datasource create/update RBAC check (internal/api/toolbox/toolbox.go:152,167), so a solver can argue saving a datasource is authorised and only proxy requests matter, or that dashboards are a different resource with their own RBAC.",
 "O4_distance": {
  "files": 7,
  "packages": 5,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Viewers with only Datasource read (no Secret read) must still query saved datasources whose spec references a secret through the saved proxy routes; also internal provisioning (nil ctx) must still create datasources with secrets, and datasources without a secret must save for users lacking Secret read. Gating retrieveSecret on Secret read for saved routes breaks dashboards for every viewer.",
  "where": "internal/api/impl/proxy/projectdatasource.go:61-74; internal/api/impl/proxy/globaldatasource.go:61-73; internal/api/impl/proxy/localdatasource.go:62-77; internal/api/provisioning/provisioning.go:144-167; internal/api/authorization/native/native.go:198-200; internal/api/authorization/k8s/k8s.go:235-237"
 },
 "O6_input_shapes": [
  "HTTPProxy config with spec.secret (fix.diff:251-255)",
  "SQLProxy config with spec.secret (fix.diff:256-260)",
  "proxy config located anywhere in plugin.spec by reflection, struct or map, kind matched case-insensitively (pkg/model/api/v1/datasource/proxy.go:48-105, pkg/model/api/v1/datasource/proxy.go:132-160); fix reuses ValidateAndExtract so it covers these",
  "project scope (Secret read in metadata.project) vs global scope (GlobalSecret read on wildcard project)",
  "create vs update",
  "unsaved project / global / dashboard proxy bodies"
 ],
 "O7_producer": {
  "kind": "handler",
  "where": "internal/api/impl/v1/datasource/service.go:52-62 and internal/api/impl/v1/globaldatasource/service.go:52-62 persist the spec that the saved-proxy route later reads via DAO (internal/api/impl/proxy/projectdatasource.go:76-87); for the O8 route the producer is internal/api/impl/v1/dashboard/service.go:65-77",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "Dashboard create with spec.datasources entries that reference a project secret, then the saved dashboard-datasource proxy route; dashboard save never checks Secret read and the saved route only checks Datasource read.",
   "where": "internal/api/impl/v1/dashboard/service.go:57-63",
   "reason_to_dismiss": "Dashboards are a separate resource with their own RBAC (DashboardScope via internal/api/toolbox/toolbox.go:152,167); the advisory and fix talk about datasources, and the fix's own checkSecretPermission lives only in the datasource services.",
   "distance": "internal/api/impl/v1/dashboard (separate package from both proxy landing point and fixed datasource services); sink reached via internal/api/impl/proxy/localdatasource.go:62-95 and route internal/api/impl/proxy/proxy.go:166-168",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "Same via dashboard update (PUT) path, which validates but never inspects local datasource secrets.",
   "where": "internal/api/impl/v1/dashboard/service.go:79-115",
   "reason_to_dismiss": "Update of an existing dashboard by a user already allowed to edit it looks like ordinary editing; Validate (internal/api/impl/v1/dashboard/service.go:141-169) only checks the DisableLocal flag.",
   "distance": "same package as previous route",
   "present_in_latest": "unknown",
   "latest_where": ""
  }
 ],
 "O8b_injection_room": [
  {
   "where": "internal/api/impl/v1/ephemeraldashboard/service.go:50",
   "sibling": "A saved-proxy route for ephemeral dashboard local datasources (EphemeralDashboardSpec embeds dashboard.Spec, pkg/model/api/v1/ephemeraldashboard.go:50-53) with no secret check on ephemeral create/update.",
   "why_realistic": "Ephemeral dashboards already carry spec.datasources; a maintainer adding preview support would mirror proxySavedDashboardDatasource with an ephemeral DAO lookup."
  },
  {
   "where": "internal/api/impl/proxy/proxy.go:197-260",
   "sibling": "A third proxy kind (or a secondary secret field) resolved via retrieveSecret but not listed in checkSecretPermission's switch.",
   "why_realistic": "The save-time check duplicates the proxy's kind switch (fix.diff:250-261) rather than sharing it, so a new kind added in newProxy would naturally be forgotten in the services."
  }
 ],
 "O9_family": "CWE-862 missing authorization (A01 broken access control): secret use by reference without checking the referrer's read permission on the secret",
 "O9_dos": false,
 "O10_build": {
  "language": "Go",
  "toolchain": "go 1.26.2 (go.mod:3)",
  "services": [],
  "offline_after_build": true,
  "project_tests": "internal/api/impl/proxy/proxy_test.go (unit); internal/api/e2e/api/proxy_test.go and rbac_test.go behind //go:build integration, using a file-backed DB (internal/api/e2e/framework/server.go:181)"
 },
 "O11_fix_minutes": 60,
 "O12_red_flags": [],
 "O13_recall_risk": "low",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "internal/api/dependency/service_manager.go, internal/api/impl/proxy/globaldatasource.go, internal/api/impl/proxy/localdatasource.go, internal/api/impl/proxy/projectdatasource.go, internal/api/impl/v1/datasource/service.go, internal/api/impl/v1/globaldatasource/service.go",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 0,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Add a Secret-read check inside newProxy/retrieveSecret for every proxy request (breaks all viewers on saved routes) or only on the unsaved handlers (leaves saved datasources and dashboards open)."
 },
 "out_of_scope_notes": [
  "Reflection finder iterates map keys in unspecified order (pkg/model/api/v1/datasource/proxy.go:98-103); a plugin spec with two proxy blocks could make the save-time check and the proxy pick different configs - not pursued.",
  "Service discovery creates global datasources with server context (internal/api/discovery/discovery.go:27) - trusted config, not pursued."
 ],
 "unverified": [
  "Advisory text itself was not available beyond the summary; landing point inferred from the summary.",
  "Whether the latest release still lacks a secret check on dashboard create/update: no latest tree provided.",
  "Repository size in MB not measured.",
  "fix.diff:273-283 adds manageQuery to internal/api/impl/v1/datasource/service.go, which does not appear at the pinned commit; treated as unrelated churn.",
  "Exact CRUD route paths for datasources/globaldatasources not opened; entry points named via the generic toolbox handlers.",
  "Integration tests not run; offline_after_build assumes the Go module cache is populated at build time."
 ]
}
  ```
- Published fix sites:   - internal/api/impl/proxy/projectdatasource.go:40-59 — entry point: POST <apiPrefix>/proxy/unsaved/projects/:project/datasources/* (internal/api/impl/proxy/proxy.go:163, group internal/api/core/server.go:176) [HTTP proxy handler (landing package)]
  - internal/api/impl/proxy/globaldatasource.go:41-59 — entry point: POST <apiPrefix>/proxy/unsaved/globaldatasources/* (internal/api/impl/proxy/proxy.go:156) [HTTP proxy handler (landing package)]
  - internal/api/impl/proxy/localdatasource.go:41-60 — entry point: POST <apiPrefix>/proxy/unsaved/projects/:project/dashboards/:dashboard/datasources/* (internal/api/impl/proxy/proxy.go:170) [HTTP proxy handler (landing package)]
  - internal/api/impl/proxy/projectdatasource.go:29-38 — entry point: refactor only: retrieveSecret now passed in; saved route ANY <apiPrefix>/proxy/projects/:project/datasources/:name (internal/api/impl/proxy/proxy.go:159-161) keeps unchecked lookup (fix.diff:148-150) [HTTP proxy helper]
  - internal/api/impl/proxy/globaldatasource.go:29-39 — entry point: refactor only; saved global route (internal/api/impl/proxy/proxy.go:152-154) keeps unchecked lookup (fix.diff:61-63) [HTTP proxy helper]
  - internal/api/impl/proxy/localdatasource.go:29-39 — entry point: refactor only; saved dashboard route (internal/api/impl/proxy/proxy.go:166-168) keeps unchecked lookup (fix.diff:105-107) [HTTP proxy helper]
  - internal/api/impl/v1/datasource/service.go:44 — entry point: POST project datasources via generic toolbox Create (internal/api/toolbox/toolbox.go:147-160) [CRUD service, save path (different package from proxy)]
  - internal/api/impl/v1/datasource/service.go:64 — entry point: PUT project datasource via toolbox Update (internal/api/toolbox/toolbox.go:162-175) [CRUD service, save path]
  - internal/api/impl/v1/globaldatasource/service.go:44 — entry point: POST global datasources via toolbox Create [CRUD service, save path]
  - internal/api/impl/v1/globaldatasource/service.go:64 — entry point: PUT global datasource via toolbox Update [CRUD service, save path]
  - internal/api/dependency/service_manager.go:127 — entry point: server wiring (authz injected into datasource service) [dependency wiring]
  - internal/api/dependency/service_manager.go:131 — entry point: server wiring (authz injected into globaldatasource service) [dependency wiring]
- Uncovered routes to confirm (pattern B):   - internal/api/impl/v1/dashboard/service.go:57-63 — Dashboard create with spec.datasources entries that reference a project secret, then the saved dashboard-datasource proxy route; dashboard save never checks Secret read and the saved route only checks Datasource read. (reason to dismiss: Dashboards are a separate resource with their own RBAC (DashboardScope via internal/api/toolbox/toolbox.go:152,167); the advisory and fix talk about datasources, and the fix's own checkSecretPermission lives only in the datasource services.; still in latest: unknown)
  - internal/api/impl/v1/dashboard/service.go:79-115 — Same via dashboard update (PUT) path, which validates but never inspects local datasource secrets. (reason to dismiss: Update of an existing dashboard by a user already allowed to edit it looks like ordinary editing; Validate (internal/api/impl/v1/dashboard/service.go:141-169) only checks the DisableLocal flag.; still in latest: unknown)
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

## Environment (`tasks/perses-ds/environment/Dockerfile`)
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

## Report to the solver (`tasks/perses-ds/instruction.md`)
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

## Tests (`tasks/perses-ds/tests/`)
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
- **Wrong-fix patches** go in `build/perses-ds/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/perses-ds/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/perses-ds/manifest.json`:**
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

**Also in `build/perses-ds/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py perses-ds --only static
python3 -I builder/gate.py perses-ds --only nop
python3 -I builder/gate.py perses-ds --only oracle
python3 -I builder/gate.py perses-ds --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/perses-ds/`;
  - edit only `tasks/perses-ds/`, `build/perses-ds/` and, for pattern B, the register;
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
