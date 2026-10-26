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

Project root: `/home/mara/cwe-bench`. Task: `cognee-s2`. Pattern: `A`. Track: `injected`.

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
- Advisory: ["GHSA-49F7-WHX5-4256", "CVE-2026-58473", "PYSEC-2026-3816"]; topoteretes/cognee; missing authorization for a critical function (CWE-306 / CWE-862): writing the deployment-global LLM and vector-DB configuration; the same fix also masks a configuration disclosure (CWE-200) on the read route.
- Pinned (vulnerable) commit: 4067f0b8a255f3a511a71cc0806b9f20dd73c31b. Published fix: 10971db1b0bd97e88f96bd2a9ffb3edb7b22bcd0, d10b1b77e2157c6238fd4d1acb1923a048991699, ebcf82412d0954f5c5018444f7eee8d96fee5113.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v2",
 "model": "deepseek-flash",
 "entry_id": "723",
 "advisory_ids": [
  "GHSA-49F7-WHX5-4256",
  "CVE-2026-58473",
  "PYSEC-2026-3816"
 ],
 "repo": "topoteretes/cognee",
 "pinned_commit": "4067f0b8a255f3a511a71cc0806b9f20dd73c31b",
 "fix_commits": [
  "10971db1b0bd97e88f96bd2a9ffb3edb7b22bcd0",
  "d10b1b77e2157c6238fd4d1acb1923a048991699",
  "ebcf82412d0954f5c5018444f7eee8d96fee5113"
 ],
 "trust_decision": {
  "summary": "Whether the caller may modify the process-global LLM / vector-DB configuration (and see its API keys), decided per request by `user.is_superuser` in the settings handler, by an env-var gate in the registration router factory, and by masking in the settings serializer; at the pinned commit the write handler, the register route and the key serialization are all unguarded.",
  "evidence": [
   "cognee/api/v1/settings/routers/get_settings_router.py:73-101",
   "cognee/api/v1/users/routers/get_register_router.py:5-6",
   "cognee/modules/settings/get_settings.py:94-96",
   "fix.diff:215-219",
   "fix.diff:152-159"
  ]
 },
 "landing_point": {
  "where": "cognee/api/v1/settings/routers/get_settings_router.py:73-101",
  "why": "The summary says non-superusers can overwrite global LLM configuration; that is literally this unguarded POST handler, which validates an arbitrary provider/model/URL and calls save_llm_config / save_vector_db_config on the shared lru_cached config objects."
 },
 "fix_sites": [
  {
   "where": "cognee/api/v1/settings/routers/get_settings_router.py:93-95",
   "entry_point": "POST /api/v1/settings",
   "module_kind": "http_router"
  },
  {
   "where": "cognee/api/v1/users/routers/get_register_router.py:5-6",
   "entry_point": "POST /api/v1/auth/register",
   "module_kind": "http_router (router factory, env-gated)"
  },
  {
   "where": "cognee/modules/settings/get_settings.py:94-96",
   "entry_point": "GET /api/v1/settings",
   "module_kind": "module_service (settings serializer, llm branch)"
  },
  {
   "where": "cognee/modules/settings/get_settings.py:184-187",
   "entry_point": "GET /api/v1/settings",
   "module_kind": "module_service (settings serializer, vector_db branch)"
  }
 ],
 "O1_entry_points": 3,
 "O2_out_of_scope_site": {
  "kind": "save_reload_or_serialization",
  "where": "cognee/modules/settings/get_settings.py:87-191 \u2014 the module-level function that serializes the live lru_cached config into the API response (masking at :94-96 and :184-187), which the report never points at and the new handler check never calls"
 },
 "O3_reason_to_dismiss": "The report is about non-superusers *overwriting* the global config, so a solver can argue that get_settings() only assembles a read response and that masking the key (and handling an unset key) is a display concern for a different ticket; likewise that the cognee.config setters and the CLI are library/operator code with no unprivileged caller to authorise.",
 "O4_distance": {
  "files": 4,
  "packages": 3,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "The GET response's masked key is round-tripped by clients into POST /settings, and save_llm_config/save_vector_db_config deliberately skip any key containing '*****' so the stored key is not overwritten with stars; a fix that instead drops api_key from the response or rejects non-plain keys breaks that save flow. Second, single-user deployments document running with auth off (ENABLE_BACKEND_ACCESS_CONTROL=false, .env.template:277-301), where get_authenticated_user (cognee/modules/users/methods/get_authenticated_user.py:93-96) resolves an unauthenticated caller to the default user, which is created with is_superuser=True (cognee/modules/users/methods/create_default_user.py:10-17) \u2014 the guard must key on the resolved user, not on the presence of a token, or that mode stops being able to save settings.",
  "where": "cognee/modules/settings/save_llm_config.py:17-18"
 },
 "O6_input_shapes": [
  "settings payload with only the llm branch set",
  "settings payload with only the vector_db branch set",
  "settings payload with both branches set (the single guard sits in front of both save calls)",
  "llm api_key present vs absent (None) in the GET response",
  "vector_db key present vs empty/unset in the GET response",
  "registration env var spellings 'true'/'1' (case-insensitive) vs any other value"
 ],
 "O7_producer": {
  "kind": "config_loader",
  "where": "cognee/infrastructure/llm/config.py:263-278 (and the vector twin at cognee/infrastructure/databases/vector/config.py:111-126) \u2014 lru_cached module singletons built from env/.env (cognee/infrastructure/llm/config.py:88); the superuser check never calls them",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "cognee.config.set_llm_api_key / set_llm_model / set_llm_provider / set_vector_db_key / set_llm_config(dict) / set_vector_db_config(dict) mutate the same lru_cached global config objects with no authorisation at all, and the dict forms bypass the '*****' guard that save_llm_config applies",
   "where": "cognee/api/v1/config/config.py:311-320",
   "reason_to_dismiss": "It is a library API executed by the embedding application's own trusted code: no HTTP caller and no user identity, so there is no unprivileged actor to check.",
   "distance": "separate top-level package (cognee/api/v1/config) reached through the public cognee.config namespace (cognee/__init__.py:27), one package away from the landing point",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "`cognee config set llm_api_key <value>` and `cognee config unset llm_api_key` reach the same sink through config.set(key, value), which dispatches by key name",
   "where": "cognee/cli/commands/config_command.py:129-146",
   "reason_to_dismiss": "Local CLI run by the operator on the host with the same OS credentials as the service; no privilege boundary is crossed.",
   "distance": "cognee/cli/commands plus the generic dispatcher at cognee/api/v1/config/config.py:659-716, two packages from the landing point",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "the identity the check trusts is minted by a public Python API: create_user(..., is_superuser=True) sets the is_superuser field the handler reads, with no authorisation on the call",
   "where": "cognee/api/v1/users/create_user.py:4-12",
   "reason_to_dismiss": "In-process admin/library helper reachable only from trusted code (tests, create_default_user); no HTTP route exposes the is_superuser argument.",
   "distance": "cognee/api/v1/users vs cognee/api/v1/settings \u2014 neighbouring package, one file",
   "present_in_latest": "unknown",
   "latest_where": ""
  }
 ],
 "O8b_injection_room": [
  {
   "where": "cognee/api/v1/settings/routers/get_settings_router.py:73-101",
   "sibling": "a POST /api/v1/settings/reset or PATCH /api/v1/settings route that restores defaults over the same DTOs",
   "why_realistic": "The module already has exactly one write route over SettingsPayloadDTO and no reset/defaults route; a defaults route is the natural next PR and is easy to add without repeating the superuser guard."
  },
  {
   "where": "cognee/api/v1/config/config.py:659-716",
   "sibling": "an HTTP POST /api/v1/config/set (or /api/v1/admin/config) exposing config.set(key, value)",
   "why_realistic": "The generic key-based setter already exists for the CLI and accepts any config key, so exposing it to the web UI is a small, plausible change that would silently reopen the flaw while looking like plumbing."
  },
  {
   "where": "cognee/api/v1/users/routers/get_configuration_router.py:47-69",
   "sibling": "a global-scope variant of store_user_configuration (name='global') that merges a caller-supplied dict into the global settings",
   "why_realistic": "The per-user configuration store already takes an arbitrary JSON dict documented as holding 'LLM settings'; extending it to a global scope is a natural merge route and would not pass through the save_settings guard."
  }
 ],
 "O9_family": "missing authorization for a critical function (CWE-306 / CWE-862): writing the deployment-global LLM and vector-DB configuration; the same fix also masks a configuration disclosure (CWE-200) on the read route.",
 "O9_dos": false,
 "O10_build": {
  "language": "Python >=3.10,<3.15",
  "toolchain": "hatchling build backend with uv.lock and poetry.lock; pytest; test client via fastapi.testclient",
  "services": [
   "sqlite (file-backed relational DB, migrated at app startup; no external service needed for the settings endpoints)"
  ],
  "offline_after_build": true,
  "project_tests": "cognee/tests/api/test_conditional_authentication_endpoints.py mocks get_llm_config/get_vectordb_config and calls GET /api/v1/settings with the default user under the auth postures; no test at the pinned commit exercises the settings *write* path, and the fix's cognee/tests/api/test_settings_authorization.py does not exist in the pinned tree"
 },
 "O11_fix_minutes": 30,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "A",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "cognee/api/v1/settings/routers/get_settings_router.py, cognee/api/v1/users/routers/get_register_router.py, cognee/modules/settings/get_settings.py",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 0,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Add `if not user.is_superuser: raise HTTPException(403)` at the top of the POST handler (what the first fix commit did), verify with a request through that same route, and stop \u2014 leaving the serializer site and the cognee.config/CLI setters alone."
 },
 "out_of_scope_notes": [
  "GET /api/v1/settings returns provider/model/endpoint plus the first 10 characters of both stored API keys to any authenticated user (cognee/modules/settings/get_settings.py:94-96,184-187) \u2014 a confidentiality issue, not this advisory's missing-authorization flaw; noted only.",
  "The default user is created as a superuser with a well-known password (cognee/modules/users/methods/create_default_user.py:10-17); outside this advisory, not pursued.",
  "cognee/api/v1/serve/credentials.py:49-54 writes cloud tokens to ~/.cognee with mode 0600 \u2014 unrelated surface, not pursued."
 ],
 "unverified": [
  "repo size in MB (no shell to measure; certainly well above 5 MB and far below 1.5 GB, so neither tiny_repo nor giant_repo could be confirmed)",
  "whether the fixed tree applies d10b1 after the 10971 revert: the diff contains a revert and a re-apply of the same get_settings.py masking, so the net change from the pinned commit depends on the final tip, which could not be inspected without a shell; the two masking fix_sites are recorded because they are in the diff",
  "whether .git history at the pinned commit still contains the earlier reverted guard commit (a possible recall shortcut for solvers), and whether solvers receive the git history at all",
  "fastapi-users is not present in the tree, so the field set of schemas.BaseUserCreate/BaseUserUpdate could not be checked; no claim is made that POST /api/v1/auth/register or PATCH /api/v1/users/me can set is_superuser",
  "no latest release was provided, so present_in_latest for every O8 route is unknown"
 ]
}
  ```
- Published fix sites:   - cognee/api/v1/settings/routers/get_settings_router.py:93-95 — entry point: POST /api/v1/settings [http_router]
  - cognee/api/v1/users/routers/get_register_router.py:5-6 — entry point: POST /api/v1/auth/register [http_router (router factory, env-gated)]
  - cognee/modules/settings/get_settings.py:94-96 — entry point: GET /api/v1/settings [module_service (settings serializer, llm branch)]
  - cognee/modules/settings/get_settings.py:184-187 — entry point: GET /api/v1/settings [module_service (settings serializer, vector_db branch)]
- Uncovered routes to confirm (pattern B): none
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

## Environment (`tasks/cognee-s2/environment/Dockerfile`)
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

## Report to the solver (`tasks/cognee-s2/instruction.md`)
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

## Tests (`tasks/cognee-s2/tests/`)
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
- **Wrong-fix patches** go in `build/cognee-s2/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/cognee-s2/`:**
- `instruction.md`;
- `task.toml`, from `common/builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/cognee-s2/manifest.json`:**
- `slug`, `candidate`;
- `pattern`: `A`;
- `builder_prompt_version`: `build-v1`;
- `"strict_gate": true`;
- `verified`: entry point, sites, routes, services, project tests run;
- `leak_terms`, `patch_checks`, `wrong_fix_catalogue`;
- `traps`: one entry per lever, with `shape`, `where` (file:line), `security_tests`,
  `coupled_functional_tests`, `security_fail_patch`, and `realistic_because` (for pattern B: "real,
  unmodified upstream code");
- `status`.

**Also in `build/cognee-s2/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `common/builder/templates/` and `common/trial/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I common/gate/gate.py cognee-s2 --only static
python3 -I common/gate/gate.py cognee-s2 --only nop
python3 -I common/gate/gate.py cognee-s2 --only oracle
python3 -I common/gate/gate.py cognee-s2 --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/cognee-s2/`;
  - edit only `tasks/cognee-s2/`, `build/cognee-s2/` and, for pattern B, the register;
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
