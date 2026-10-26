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

Project root: `/home/mara/cwe-bench`. Task: `litellm-ds`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: ["GHSA-3CV6-JPF6-8222", "CVE-2026-84377", "PYSEC-2026-4066"]; berriai/litellm; SSRF / credential exfiltration via caller-controlled outbound destination (CWE-918); missing authorization on destination-routing parameters
- Pinned (vulnerable) commit: unknown (parent of 473f72e63a9777d793fbbf57194d8ec4fb97bc1b; parent_commit is null in the candidate record). Published fix: 473f72e63a9777d793fbbf57194d8ec4fb97bc1b, 820f247a6abba55cd87d130bef7bba7be3b29d37, c898d341c02299cf2506d0d8e84cc67953043593.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "426",
 "advisory_ids": [
  "GHSA-3CV6-JPF6-8222",
  "CVE-2026-84377",
  "PYSEC-2026-4066"
 ],
 "repo": "berriai/litellm",
 "pinned_commit": "unknown (parent of 473f72e63a9777d793fbbf57194d8ec4fb97bc1b; parent_commit is null in the candidate record)",
 "fix_commits": [
  "473f72e63a9777d793fbbf57194d8ec4fb97bc1b",
  "820f247a6abba55cd87d130bef7bba7be3b29d37",
  "c898d341c02299cf2506d0d8e84cc67953043593"
 ],
 "trust_decision": {
  "summary": "The proxy decides whether a caller may choose the outbound destination (URL-valued model/file_id, api_base and observability hosts in body or metadata) and whether admin-configured credentials may follow a caller-chosen destination. It decides this at auth time in is_request_body_safe, in add_litellm_data_to_request via _reject_url_valued_destinations, and in the router's credential-clearing step.",
  "evidence": [
   "litellm/proxy/auth/auth_utils.py:406-461",
   "litellm/proxy/auth/auth_utils.py:507-512",
   "litellm/proxy/litellm_pre_call_utils.py:247-287",
   "litellm/proxy/litellm_pre_call_utils.py:1437",
   "litellm/router_utils/clientside_credential_handler.py:99-103"
  ]
 },
 "landing_point": {
  "where": "litellm/proxy/litellm_pre_call_utils.py:254",
  "why": "The summary says 'unvalidated request-body routing parameters' and 'SSRF', which points to the central URL-valued model/file_id guard and its caller add_litellm_data_to_request; is_request_body_safe (litellm/proxy/auth/auth_utils.py:406) is the second obvious place to look."
 },
 "fix_sites": [
  {
   "where": "litellm/proxy/auth/auth_utils.py:439-442",
   "entry_point": "any authenticated multipart route sending bracket-notation metadata, e.g. POST /v1/files (form parsed into litellm_metadata at litellm/proxy/openai_files_endpoints/files_endpoints.py:378-388), checked via user_api_key_auth -> litellm/proxy/auth/auth_utils.py:507",
   "module_kind": "auth check (request-body blocklist)"
  },
  {
   "where": "litellm/proxy/common_request_processing.py:1289-1294",
   "entry_point": "POST /openai/deployments/{model:path}/chat/completions, /openai/deployments/{model:path}/completions, /engines/{model:path}/completions, /openai/deployments/{model:path}/embeddings, /engines/{model:path}/embeddings (path model overrides the body model after the guard has run)",
   "module_kind": "shared request processor"
  },
  {
   "where": "litellm/proxy/image_endpoints/endpoints.py:99-104",
   "entry_point": "POST /openai/deployments/{model:path}/images/generations",
   "module_kind": "endpoint handler (separate implementation of the model-selection step)"
  },
  {
   "where": "litellm/proxy/health_endpoints/_health_endpoints.py:1856-1858",
   "entry_point": "POST /health/test_connection (litellm/proxy/health_endpoints/_health_endpoints.py:1704-1708)",
   "module_kind": "health/management endpoint; second implementation of the router's config/request credential merge"
  },
  {
   "where": "litellm/proxy/litellm_pre_call_utils.py:254-287",
   "entry_point": "refactor only: exposes reject_url_valued_destination(field, value) so the two path-model sites can call it (fix.diff:190-244)",
   "module_kind": "shared guard helper"
  }
 ],
 "O1_entry_points": 6,
 "O2_out_of_scope_site": {
  "kind": "second_implementation",
  "where": "litellm/proxy/health_endpoints/_health_endpoints.py:1858 merges config credentials under request params (including a request-supplied api_base) without the clearing the router does at litellm/router_utils/clientside_credential_handler.py:99-103; fixed at fix.diff:153-160"
 },
 "O3_reason_to_dismiss": "/health/test_connection is an admin/model-management 'test connection' tool that is documented to load credentials from config and let you override params (litellm/proxy/health_endpoints/_health_endpoints.py:1775-1779), so a solver can argue it is a deliberate feature and not a request-body routing route. For the O8 queue route: it is marked experimental and hidden from the schema (litellm/proxy/proxy_server.py:13644-13649).",
 "O4_distance": {
  "files": 5,
  "packages": 4,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Test Connection on a configured model (name plus stored credential, no own connection fields) must still inherit the config credentials, and an add-model request carrying its own api_base plus api_key must test as sent. The allow_client_side_credentials opt-in must restore inheritance. Benign bracket metadata (litellm_metadata[tags], [spend_logs_metadata][owner]) must pass. Ordinary Azure deployment path names (dall-e-3) must route. Allowlisted hosts in provider_url_destination_allowed_hosts must pass. An over-broad fix (dropping config credentials always, rejecting any bracket key, rejecting any '/' in the path model) breaks these.",
  "where": "litellm/proxy/health_endpoints/_health_endpoints.py:1856-1858; litellm/proxy/common_utils/http_parsing_utils.py:349-382; litellm/proxy/litellm_pre_call_utils.py:254-274; fix.diff:365-433; fix.diff:295-308; fix.diff:457-466"
 },
 "O6_input_shapes": [
  "metadata as a dict (already covered, litellm/proxy/auth/auth_utils.py:439-442)",
  "metadata as a JSON-encoded string (already covered, litellm/proxy/auth/auth_utils.py:464-479)",
  "metadata as flat bracket-notation form keys metadata[...] / litellm_metadata[...] (new, fix.diff:17-23)",
  "model in the JSON body (already covered, litellm/proxy/litellm_pre_call_utils.py:1437)",
  "model in the URL path for Azure/engines routes, which overrides the body (new, fix.diff:47-48, fix.diff:180-181)",
  "non-string model/file_id values are ignored (fix.diff:197-199, fix.diff:477-487)",
  "health test: any banned destination field (api_base, aws_bedrock_runtime_endpoint, ...) in request params, plus litellm_credential_name by reference (fix.diff:91-127)"
 ],
 "O7_producer": {
  "kind": "mapper",
  "where": "litellm/proxy/common_utils/http_parsing_utils.py:349 (extract_nested_form_metadata), called by the files handler at litellm/proxy/openai_files_endpoints/files_endpoints.py:380-388 to build data['litellm_metadata'] from bracket keys",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "POST /queue/chat/completions takes model from the query param or the body and calls llm_router.schedule_acompletion without add_litellm_data_to_request, so the URL-valued model guard never runs",
   "where": "litellm/proxy/proxy_server.py:13644-13683",
   "reason_to_dismiss": "Tagged experimental, include_in_schema=False, and the fix only discusses Azure path-model routes and the shared processor",
   "distance": "same file as the chat/completions handlers (litellm/proxy/proxy_server.py), about 4,500 lines further down; another package from the landing point (litellm/proxy/litellm_pre_call_utils.py)",
   "present_in_latest": "yes",
   "latest_where": "latest/litellm/proxy/proxy_server.py:17489-17528"
  }
 ],
 "O8b_injection_room": [
  {
   "where": "litellm/proxy/auth/auth_utils.py:435-438",
   "sibling": "bracket-notation form keys for _NESTED_CONFIG_KEYS (extra_body[api_base], litellm_embedding_config[api_base]) are not reconstructed or checked, while the fix covers only metadata keys",
   "why_realistic": "A maintainer extending form parsing to extra_body for multipart SDK calls would reuse extract_nested_form_metadata with a new prefix and forget the auth bouncer, which is exactly the original bug shape."
  },
  {
   "where": "litellm/proxy/image_endpoints/endpoints.py:299-304",
   "sibling": "image_edit sets the path model before processing (covered today); a sibling multipart route that assigns the path model after add_litellm_data_to_request, like image_generation did, would reintroduce the bypass",
   "why_realistic": "The Azure-compatible handlers copy-paste the 'model or general_settings... or data.get(model)' block, and its position relative to the guard varies between handlers."
  },
  {
   "where": "litellm/proxy/health_endpoints/_health_endpoints.py:1856-1858",
   "sibling": "another admin 'test'/'validate' endpoint that merges stored deployment litellm_params under request params",
   "why_realistic": "The router's clearing list lives in router_utils, so a proxy-side merge written for UI convenience would not pick it up."
  }
 ],
 "O9_family": "SSRF / credential exfiltration via caller-controlled outbound destination (CWE-918); missing authorization on destination-routing parameters",
 "O9_dos": false,
 "O10_build": {
  "language": "Python",
  "toolchain": "Python 3 with poetry/pip from pyproject.toml; pytest",
  "services": [],
  "offline_after_build": true,
  "project_tests": "tests/test_litellm/proxy/auth/test_auth_utils.py, tests/test_litellm/proxy/health_endpoints/test_health_endpoints.py, tests/test_litellm/proxy/image_endpoints/test_azure_routes.py, tests/test_litellm/proxy/test_provider_url_destination_guard.py (unit tests with mocked provider calls; fix.diff:248-487)"
 },
 "O11_fix_minutes": 60,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "litellm/proxy/auth/auth_utils.py, litellm/proxy/common_request_processing.py, litellm/proxy/health_endpoints/_health_endpoints.py, litellm/proxy/image_endpoints/endpoints.py, litellm/proxy/litellm_pre_call_utils.py",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Add another banned key or tighten _reject_url_valued_destinations on the body, missing that the path model overrides the body after the guard, that bracket form keys bypass the dict check, and that /health/test_connection merges config credentials under a caller api_base."
 },
 "out_of_scope_notes": [
  "pre_db_read_auth_checks passes only the body model to is_request_body_safe, with a TODO for the URL model (litellm/proxy/auth/auth_utils.py:511); not pursued.",
  "Pass-through endpoint model assignment (litellm/proxy/pass_through_endpoints/pass_through_endpoints.py:184-188) not examined."
 ],
 "unverified": [
  "pinned_commit hash not given in the inputs and not derivable without git.",
  "Whether llm_router.schedule_acompletion accepts a URL-valued model on /queue/chat/completions depends on the configured model_list (for example a provider wildcard); not traced through the router.",
  "repo_mb not measured (no shell); giant_repo/tiny_repo not assessed and assumed not to apply.",
  "O1 counts handler groups (multipart files, chat, completions/engines, embeddings/engines, image generation, health test); the exact path count is higher.",
  "j_defence_ineffective = 1 because the guard existed but ran before the path model overwrote data['model'] (litellm/proxy/common_request_processing.py:1253-1294); read from code order, not executed.",
  "Whether the advisory text itself names all three mechanisms; only the summary was available."
 ]
}
  ```
- Published fix sites:   - litellm/proxy/auth/auth_utils.py:439-442 — entry point: any authenticated multipart route sending bracket-notation metadata, e.g. POST /v1/files (form parsed into litellm_metadata at litellm/proxy/openai_files_endpoints/files_endpoints.py:378-388), checked via user_api_key_auth -> litellm/proxy/auth/auth_utils.py:507 [auth check (request-body blocklist)]
  - litellm/proxy/common_request_processing.py:1289-1294 — entry point: POST /openai/deployments/{model:path}/chat/completions, /openai/deployments/{model:path}/completions, /engines/{model:path}/completions, /openai/deployments/{model:path}/embeddings, /engines/{model:path}/embeddings (path model overrides the body model after the guard has run) [shared request processor]
  - litellm/proxy/image_endpoints/endpoints.py:99-104 — entry point: POST /openai/deployments/{model:path}/images/generations [endpoint handler (separate implementation of the model-selection step)]
  - litellm/proxy/health_endpoints/_health_endpoints.py:1856-1858 — entry point: POST /health/test_connection (litellm/proxy/health_endpoints/_health_endpoints.py:1704-1708) [health/management endpoint; second implementation of the router's config/request credential merge]
  - litellm/proxy/litellm_pre_call_utils.py:254-287 — entry point: refactor only: exposes reject_url_valued_destination(field, value) so the two path-model sites can call it (fix.diff:190-244) [shared guard helper]
- Uncovered routes to confirm (pattern B):   - litellm/proxy/proxy_server.py:13644-13683 — POST /queue/chat/completions takes model from the query param or the body and calls llm_router.schedule_acompletion without add_litellm_data_to_request, so the URL-valued model guard never runs (reason to dismiss: Tagged experimental, include_in_schema=False, and the fix only discusses Azure path-model routes and the shared processor; still in latest: yes)
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

## Environment (`tasks/litellm-ds/environment/Dockerfile`)
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

## Report to the solver (`tasks/litellm-ds/instruction.md`)
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

## Tests (`tasks/litellm-ds/tests/`)
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
- **Wrong-fix patches** go in `build/litellm-ds/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/litellm-ds/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/litellm-ds/manifest.json`:**
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

**Also in `build/litellm-ds/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py litellm-ds --only static
python3 -I builder/gate.py litellm-ds --only nop
python3 -I builder/gate.py litellm-ds --only oracle
python3 -I builder/gate.py litellm-ds --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/litellm-ds/`;
  - edit only `tasks/litellm-ds/`, `build/litellm-ds/` and, for pattern B, the register;
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
