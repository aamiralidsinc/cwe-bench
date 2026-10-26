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

Project root: `/home/mara/cwe-bench`. Task: `mcp-context-forge-mm`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: ["GHSA-VWF3-4XXJ-QG6H"]; ibm/mcp-context-forge; server-side template injection (CWE-1336 / CWE-94), unsandboxed template engine on stored user content
- Pinned (vulnerable) commit: parent of 4d31004661858a2e99055b3c0c9f14218b8f7120 (parent_commit not given in candidate). Published fix: 4d31004661858a2e99055b3c0c9f14218b8f7120.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "5900",
 "advisory_ids": [
  "GHSA-VWF3-4XXJ-QG6H"
 ],
 "repo": "ibm/mcp-context-forge",
 "pinned_commit": "parent of 4d31004661858a2e99055b3c0c9f14218b8f7120 (parent_commit not given in candidate)",
 "fix_commits": [
  "4d31004661858a2e99055b3c0c9f14218b8f7120"
 ],
 "trust_decision": {
  "summary": "Whether a stored prompt template (written by any prompt author or a federated upstream) may reach Python internals when rendered; decided only at render time in PromptService._render_template via the module-level Jinja environment, which at the pinned commit is a plain unsandboxed Environment.",
  "evidence": [
   "mcpgateway/services/prompt_service.py:80-93",
   "mcpgateway/services/prompt_service.py:96-106",
   "mcpgateway/services/prompt_service.py:2887-2894",
   "fix.diff:1876",
   "fix.diff:2046-2051"
  ]
 },
 "landing_point": {
  "where": "mcpgateway/services/prompt_service.py:2865",
  "why": "The advisory summary names PromptService._render_template and the 'unsandboxed Jinja2 Environment'; the env it uses is 20 lines away in the same file (prompt_service.py:88)."
 },
 "fix_sites": [
  {
   "where": "mcpgateway/services/prompt_service.py:88",
   "entry_point": "POST /prompts/{prompt_id} (main.py:6370), JSON-RPC prompts/get (main.py:10484 via /rpc main.py:7250), /_internal/mcp/prompts/get (main.py:8647), streamable HTTP prompts/get (transports/streamablehttp_transport.py:2307)",
   "module_kind": "core service: Jinja env singleton (the actual SSTI fix: Environment -> SandboxedEnvironment, fix.diff:1876)"
  },
  {
   "where": "mcpgateway/services/prompt_service.py:2890-2892",
   "entry_point": "same render routes as above",
   "module_kind": "core service: str.format fallback in the same function; fix adds a SecurityError branch so sandbox rejections do not fall through to str.format (fix.diff:2046-2051)"
  },
  {
   "where": "mcpgateway/services/prompt_service.py:768",
   "entry_point": "POST /prompts (main.py:6270), admin add prompt (admin.py:13035), import (services/import_service.py:877)",
   "module_kind": "core service: create-time validation, _validate_template replaced by validate_prompt_template regex blocklist (fix.diff:1896-1901)"
  },
  {
   "where": "mcpgateway/services/prompt_service.py:1102",
   "entry_point": "bulk import via register_prompts_bulk (services/import_service.py:1121)",
   "module_kind": "core service: bulk create-time validation (fix.diff:1951-1956)"
  },
  {
   "where": "mcpgateway/services/prompt_service.py:2278",
   "entry_point": "PUT /prompts/{prompt_id} (main.py:6497), admin edit prompt (admin.py:13156), import update (services/import_service.py:887)",
   "module_kind": "core service: update-time validation (fix.diff:2000-2005)"
  },
  {
   "where": "mcpgateway/services/content_security.py:242",
   "entry_point": "called from the prompt create/update paths above",
   "module_kind": "lower-level validator module: new detect_malicious_patterns / validate_prompt_template (fix.diff:1483-1786); advisory pre-flight only"
  },
  {
   "where": "mcpgateway/main.py:6329",
   "entry_point": "POST /prompts, PUT /prompts/{id}",
   "module_kind": "HTTP error mapping only (fix.diff:1054-1131)"
  },
  {
   "where": "mcpgateway/admin.py:13035",
   "entry_point": "admin add/edit prompt",
   "module_kind": "HTTP error mapping only (fix.diff:887-923)"
  },
  {
   "where": "mcpgateway/services/resource_service.py:527",
   "entry_point": "POST/PUT /resources, bulk resources",
   "module_kind": "unrelated to the SSTI sink: regex content scan on resources plus MIME-priority churn (fix.diff:2095-2361)"
  },
  {
   "where": "mcpgateway/services/tool_service.py:1873",
   "entry_point": "POST/PUT /tools, bulk tools",
   "module_kind": "unrelated to the SSTI sink: regex scan of tool name/description/inputSchema (fix.diff:2402-2513)"
  }
 ],
 "O1_entry_points": 4,
 "O2_out_of_scope_site": {
  "kind": "none",
  "where": "The SSTI protection itself sits in one function (prompt_service.py:88, plus the fallback at prompt_service.py:2890-2892). Sites in tool_service.py and resource_service.py belong to a separate regex content-scanning feature bundled into the same PR (fix.diff:473) and never reach the Jinja sink."
 },
 "O3_reason_to_dismiss": "The federation sync stores upstream-supplied templates with no create-time validation (gateway_service.py:1258, 1279, 4818, 4833), and a solver can argue that federated prompts are 'fetched upstream, not rendered locally' (prompt_service.py:340-354). That holds only when the template is empty. The str.format fallback can be dismissed as 'legacy {name}-style support, not Jinja'.",
 "O4_distance": {
  "files": 2,
  "packages": 1,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Ordinary Jinja templates with variables, loops and filters, and the str.format fallback for templates that Jinja cannot render, must keep rendering. An over-broad blocklist (the fix's own SQL-keyword and '&&|\\|\\|' patterns) rejects ordinary prose such as 'select an option'.",
  "where": "mcpgateway/services/prompt_service.py:2887-2894"
 },
 "O6_input_shapes": [
  "direct dunder attribute access in {{ }} (sandbox, fix.diff:1876)",
  "attr()/getattr chains and hex-escaped names, caught only at render by the sandbox (fix.diff:484-488)",
  "sandbox SecurityError no longer falls through to str.format attribute access (fix.diff:2046-2051)",
  "literal dunder/eval/exec/open patterns caught at create/update/bulk time (fix.diff:954-972)"
 ],
 "O7_producer": {
  "kind": "mapper",
  "where": "mcpgateway/services/gateway_service.py:4765-4839 (_update_or_create_prompts) and mcpgateway/services/gateway_service.py:1258-1279 (register_gateway): upstream prompt objects are mapped into DbPrompt.template, then rendered later through prompt_service.py:2021",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "Federation sync writes upstream-supplied prompt templates to the DB without the create-time template validation the fix added (render is still sandboxed after the fix)",
   "where": "mcpgateway/services/gateway_service.py:4818",
   "reason_to_dismiss": "Federated prompts look like upstream-fetched metadata (prompt_service.py:340-354), not local templates",
   "distance": "different service file (gateway_service.py vs prompt_service.py), same package",
   "present_in_latest": "yes",
   "latest_where": "latest/mcpgateway/services/gateway_service.py:6755"
  },
  {
   "route": "register_gateway orphan-reassign and create paths copy the upstream template with no validation",
   "where": "mcpgateway/services/gateway_service.py:1258",
   "reason_to_dismiss": "Same as above: treated as a federation concern",
   "distance": "different service file, same package",
   "present_in_latest": "yes",
   "latest_where": "latest/mcpgateway/services/gateway_service.py:2285"
  },
  {
   "route": "str.format fallback still runs for non-SecurityError Jinja failures (e.g. undefined-attribute errors), so format-string attribute access can still reach argument internals",
   "where": "mcpgateway/services/prompt_service.py:2890-2892",
   "reason_to_dismiss": "Legacy {name}-style compatibility; str values give only reprs, no call",
   "distance": "same function as the landing point",
   "present_in_latest": "yes",
   "latest_where": "latest/mcpgateway/services/prompt_service.py:3115"
  }
 ],
 "O8b_injection_room": [
  {
   "where": "plugins/webhook_notification/webhook_notification.py:146-166",
   "sibling": "Replace the hand-rolled {{key}} substitution with a plain jinja2 Environment().from_string render of an operator/plugin-configured payload template",
   "why_realistic": "The code comment at plugins/webhook_notification/webhook_notification.py:156 already says 'could be enhanced with Jinja2'; it lives in a separate plugin package far from prompt_service."
  },
  {
   "where": "mcpgateway/services/resource_service.py:3698-3704",
   "sibling": "Render text resource templates through a separate plain Jinja Environment (or a reused copy of _get_jinja_env) instead of uri_template.format(**params)",
   "why_realistic": "Resource templates are the MCP sibling of prompt templates, and a maintainer adding richer resource templating would copy the prompt renderer."
  },
  {
   "where": "mcpgateway/services/prompt_service.py:2817",
   "sibling": "A second render helper (e.g. an admin 'preview/test prompt' path) that builds its own Environment rather than calling _get_jinja_env",
   "why_realistic": "Admin UI routes in admin.py duplicate service logic elsewhere; a preview route would plausibly construct its own env."
  }
 ],
 "O9_family": "server-side template injection (CWE-1336 / CWE-94), unsandboxed template engine on stored user content",
 "O9_dos": false,
 "O10_build": {
  "language": "Python (plus unrelated Rust crates)",
  "toolchain": "pyproject.toml / pip or uv, jinja2>=3.1.6 (pyproject.toml:82)",
  "services": [],
  "offline_after_build": null,
  "project_tests": "tests/unit/mcpgateway/services/test_prompt_service.py (exists at pinned commit, no sandbox/SSTI tests); the fix adds tests/unit/mcpgateway/services/test_content_pattern_detection.py and tests/integration/test_content_pattern_detection.py (new files, fix.diff:2636, fix.diff:3177)"
 },
 "O11_fix_minutes": 20,
 "O12_red_flags": [],
 "O13_recall_risk": "high",
 "pattern_fit": "injection_only",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "mcpgateway/services/prompt_service.py, mcpgateway/services/content_security.py, mcpgateway/main.py, mcpgateway/admin.py, mcpgateway/config.py, mcpgateway/services/resource_service.py, mcpgateway/services/tool_service.py, mcpgateway/services/metrics.py",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 0,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Swap Environment for SandboxedEnvironment at prompt_service.py:88 and stop, leaving the except-Exception fallback to template.format(**arguments) at prompt_service.py:2892 to re-open attribute access; or add only a create-time regex blocklist, which misses federated/stored templates."
 },
 "out_of_scope_notes": [
  "resource_service.py:3703 renders resource uri_template via str.format(**params) with URI-derived params (separate feature, not this advisory's sink).",
  "The fix diff also reverts unrelated behaviour (MIME priority in resource_service, metrics labels, OAuth metric text), so it looks like a branch merge, not a focused patch."
 ],
 "unverified": [
  "pinned_commit hash not given (parent_commit null); assumed to be the parent of the fix commit.",
  "repo_mb not measured; the repo is clearly not tiny (main.py >11k lines, admin.py >13k lines), so tiny_repo/giant_repo were not evaluated.",
  "offline_after_build not confirmed; default SQLite is expected but not checked in config.",
  "Whether mcp.types.Prompt keeps an extra 'template' field through model_dump (gateway_service.py:5503-5515), which decides whether a federated upstream can actually plant a non-empty template that renders locally.",
  "Whether the remaining str.format fallback (prompt_service.py:2892) leaks anything useful with Dict[str,str] arguments; likely repr-only, no call.",
  "O1 counts render routes only; websocket /ws (main.py:10866) and /message (main.py:11052) may forward to the same RPC dispatcher and were not traced.",
  "Single_site not flagged because the published diff touches many functions, but the SSTI protection itself is a one-line env swap plus one except branch."
 ]
}
  ```
- Published fix sites:   - mcpgateway/services/prompt_service.py:88 — entry point: POST /prompts/{prompt_id} (main.py:6370), JSON-RPC prompts/get (main.py:10484 via /rpc main.py:7250), /_internal/mcp/prompts/get (main.py:8647), streamable HTTP prompts/get (transports/streamablehttp_transport.py:2307) [core service: Jinja env singleton (the actual SSTI fix: Environment -> SandboxedEnvironment, fix.diff:1876)]
  - mcpgateway/services/prompt_service.py:2890-2892 — entry point: same render routes as above [core service: str.format fallback in the same function; fix adds a SecurityError branch so sandbox rejections do not fall through to str.format (fix.diff:2046-2051)]
  - mcpgateway/services/prompt_service.py:768 — entry point: POST /prompts (main.py:6270), admin add prompt (admin.py:13035), import (services/import_service.py:877) [core service: create-time validation, _validate_template replaced by validate_prompt_template regex blocklist (fix.diff:1896-1901)]
  - mcpgateway/services/prompt_service.py:1102 — entry point: bulk import via register_prompts_bulk (services/import_service.py:1121) [core service: bulk create-time validation (fix.diff:1951-1956)]
  - mcpgateway/services/prompt_service.py:2278 — entry point: PUT /prompts/{prompt_id} (main.py:6497), admin edit prompt (admin.py:13156), import update (services/import_service.py:887) [core service: update-time validation (fix.diff:2000-2005)]
  - mcpgateway/services/content_security.py:242 — entry point: called from the prompt create/update paths above [lower-level validator module: new detect_malicious_patterns / validate_prompt_template (fix.diff:1483-1786); advisory pre-flight only]
  - mcpgateway/main.py:6329 — entry point: POST /prompts, PUT /prompts/{id} [HTTP error mapping only (fix.diff:1054-1131)]
  - mcpgateway/admin.py:13035 — entry point: admin add/edit prompt [HTTP error mapping only (fix.diff:887-923)]
  - mcpgateway/services/resource_service.py:527 — entry point: POST/PUT /resources, bulk resources [unrelated to the SSTI sink: regex content scan on resources plus MIME-priority churn (fix.diff:2095-2361)]
  - mcpgateway/services/tool_service.py:1873 — entry point: POST/PUT /tools, bulk tools [unrelated to the SSTI sink: regex scan of tool name/description/inputSchema (fix.diff:2402-2513)]
- Uncovered routes to confirm (pattern B):   - mcpgateway/services/gateway_service.py:4818 — Federation sync writes upstream-supplied prompt templates to the DB without the create-time template validation the fix added (render is still sandboxed after the fix) (reason to dismiss: Federated prompts look like upstream-fetched metadata (prompt_service.py:340-354), not local templates; still in latest: yes)
  - mcpgateway/services/gateway_service.py:1258 — register_gateway orphan-reassign and create paths copy the upstream template with no validation (reason to dismiss: Same as above: treated as a federation concern; still in latest: yes)
  - mcpgateway/services/prompt_service.py:2890-2892 — str.format fallback still runs for non-SecurityError Jinja failures (e.g. undefined-attribute errors), so format-string attribute access can still reach argument internals (reason to dismiss: Legacy {name}-style compatibility; str values give only reprs, no call; still in latest: yes)
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

## Environment (`tasks/mcp-context-forge-mm/environment/Dockerfile`)
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

## Report to the solver (`tasks/mcp-context-forge-mm/instruction.md`)
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

## Tests (`tasks/mcp-context-forge-mm/tests/`)
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
- **Wrong-fix patches** go in `build/mcp-context-forge-mm/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/mcp-context-forge-mm/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/mcp-context-forge-mm/manifest.json`:**
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

**Also in `build/mcp-context-forge-mm/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py mcp-context-forge-mm --only static
python3 -I builder/gate.py mcp-context-forge-mm --only nop
python3 -I builder/gate.py mcp-context-forge-mm --only oracle
python3 -I builder/gate.py mcp-context-forge-mm --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/mcp-context-forge-mm/`;
  - edit only `tasks/mcp-context-forge-mm/`, `build/mcp-context-forge-mm/` and, for pattern B, the register;
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
