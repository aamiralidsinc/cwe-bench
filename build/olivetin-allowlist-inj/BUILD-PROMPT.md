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

Project root: `/home/mara/cwe-bench`. Task: `olivetin-allowlist-inj`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: GHSA-PRJ9-97MP-MWH2 / CVE-2026-53541 - olivetin/olivetin - CWE-20 improper input validation: allowlist filter bypass via reserved-prefix exception, plus unvalidated identity-derived system values into shell template/env (command-injection sink). Which request-argument names may reach the shell template and process environment without a declared type check: stepParseArgs keeps any undeclared ot
- Pinned (vulnerable) commit: 41612c6bc6a8a6424e27e6a66fb0dae30524c768. Published fix: ebffd9f040f791208aee1db2e5a8aecd1e3e603d.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "18705",
 "advisory_ids": [
  "GHSA-PRJ9-97MP-MWH2",
  "CVE-2026-53541",
  "GO-2026-5552"
 ],
 "repo": "olivetin/olivetin",
 "pinned_commit": "unknown (parent of ebffd9f040f791208aee1db2e5a8aecd1e3e603d; parent_commit not given in the candidate)",
 "fix_commits": [
  "ebffd9f040f791208aee1db2e5a8aecd1e3e603d"
 ],
 "trust_decision": {
  "summary": "Which request-argument names may reach the shell template and process environment without a declared type check: stepParseArgs keeps any undeclared ot_-prefixed argument (keepArgument), injects system args before filtering, and inserts ot_username unvalidated into the main shell and the shellAfterCompleted shell.",
  "evidence": [
   "service/internal/executor/executor.go:667-683",
   "service/internal/executor/executor.go:736-739",
   "service/internal/executor/executor.go:750-753",
   "service/internal/executor/executor.go:952-972",
   "service/internal/executor/arguments.go:85-101",
   "service/internal/executor/executor.go:937"
  ]
 },
 "landing_point": {
  "where": "service/internal/executor/executor.go:736-739",
  "why": "The summary says ot_-prefixed arguments bypass input filtering; keepArgument is the one place with an explicit HasPrefix(name, \"ot_\") exception in the argument filter."
 },
 "fix_sites": [
  {
   "where": "service/internal/executor/executor.go:736-739",
   "entry_point": "StartAction / StartActionAndWait RPCs (service/internal/api/api.go:127-150, service/internal/api/api.go:258-270) with client-supplied argument maps",
   "module_kind": "core executor, argument filter"
  },
  {
   "where": "service/internal/executor/executor.go:667-676",
   "entry_point": "every ExecRequest caller (API start RPCs, triggers, cron, calendar, file-in-dir, webhooks); system-arg injection moved after filtering",
   "module_kind": "core executor, step ordering"
  },
  {
   "where": "service/internal/executor/executor.go:750-753",
   "entry_point": "all API start RPCs (api.go:127, :258, :279, :302); username comes from trusted header / JWT / OAuth2 identity",
   "module_kind": "core executor, system argument injection (now validated via validatedSystemArgs)"
  },
  {
   "where": "service/internal/executor/executor.go:941-972",
   "entry_point": "any action with shellAfterCompleted, started via the API start RPCs",
   "module_kind": "second implementation: separate system-args map and separate shell sink for post-completion command"
  },
  {
   "where": "service/internal/executor/arguments.go:17-25",
   "entry_point": "TypeSafetyCheck / ValidateArgument (also ValidateArgumentType RPC, service/internal/api/api.go:792-802)",
   "module_kind": "type registry; new shell_safe_identifier type so email-style usernames stay valid"
  },
  {
   "where": "service/internal/config/sanitize.go:15-29",
   "entry_point": "config load and reload (service/internal/config/config_reloader.go:68)",
   "module_kind": "config loader; rejects action arguments (top-level and dashboard inline actions) named with the reserved ot_ prefix"
  },
  {
   "where": "service/internal/config/config.go:1-10",
   "entry_point": "constant ReservedArgumentNamePrefix (fix.diff:34-35)",
   "module_kind": "config constant"
  },
  {
   "where": "frontend/resources/vue/views/ArgumentForm.vue:177",
   "entry_point": "web UI argument form (fix.diff:21-22)",
   "module_kind": "frontend; renders new type as text input"
  }
 ],
 "O1_entry_points": 4,
 "O2_out_of_scope_site": {
  "kind": "second_implementation",
  "where": "service/internal/executor/executor.go:952-957 (shellAfterCompleted builds its own system-args map, including unvalidated ot_username, and templates it into a second shell command at :959 and env at :972). Secondary: config-loader reservation check added at service/internal/config/sanitize.go:15-29 (fix.diff:49-76)."
 },
 "O3_reason_to_dismiss": "The docs say shellAfterCompleted 'cannot use argument values - they are not passed to the command' (docs/modules/ROOT/pages/action_execution/aftercompletion.adoc:16), so a solver fixing the ot_ filter bypass can argue that path takes no user input and is out of scope, even though ot_username there comes from an external identity provider.",
 "O4_distance": {
  "files": 4,
  "packages": 3,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "System args ot_username and ot_executionTrackingId must still reach templates and env (OT_USERNAME) for every action and for shellAfterCompleted, and email-style usernames (alice@example.com, plus-addressing) must stay valid; dropping all ot_ args, or validating the username as ascii_identifier, breaks this documented feature.",
  "where": "docs/modules/ROOT/pages/args/env.adoc:46-66; docs/modules/ROOT/pages/action_execution/aftercompletion.adoc:20-21; fix.diff:151; fix.diff:500-513"
 },
 "O6_input_shapes": [
  "undeclared client-supplied argument with ot_ prefix and an arbitrary suffix (e.g. ot_custom) via the StartAction argument list",
  "client-supplied ot_username / ot_executionTrackingId colliding with system names (must be overwritten by server values after filtering)",
  "action argument declared in config with the reserved ot_ prefix, top-level actions",
  "same, in dashboard inline actions merged into cfg.Actions (service/internal/config/sanitize.go:31-77)",
  "identity-provider username containing shell metacharacters (header/JWT/OAuth2), in the main shell/exec path",
  "same username in the shellAfterCompleted path",
  "invalid or empty tracking ID / username (RejectNull) failing the execution",
  "email-style username with @ and + that must still pass"
 ],
 "O7_producer": {
  "kind": "mapper",
  "where": "username mapped from external identity: service/internal/auth/trusted-headers.go:14, service/internal/auth/otjwt/jwt.go:229, service/internal/auth/otoauth2/restapi_auth_oauth2.go:348",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [],
 "O8b_injection_room": [
  {
   "where": "service/internal/webhooks/handler.go:165-177",
   "sibling": "a prefix exception in the webhook's own filterToDefinedArguments that passes webhook_* metadata/header args through undeclared, mirroring keepArgument's ot_ exception",
   "why_realistic": "matcher.go:173-185 already produces webhook_method/path/query/header_* args that the strict filter drops unless declared; a maintainer wanting them available by default would add exactly the same kind of prefix allowance."
  },
  {
   "where": "service/internal/executor/executor.go:1035-1043",
   "sibling": "triggerLoop injecting an extra system arg (e.g. parent action title or parent tracking ID) straight into the child's Arguments without going through the validated system-arg definitions",
   "why_realistic": "Triggers already copy parent Arguments and AuthenticatedUser into the child request; adding provenance info for the child script is a natural feature request."
  },
  {
   "where": "service/internal/executor/executor.go:750-753",
   "sibling": "a third injected system arg sourced from identity data (e.g. user group / provider from a JWT claim) added to injectSystemArgs but not to the shellAfterCompleted map, or vice versa",
   "why_realistic": "The two system-arg maps (:750-753 and :952-957) are maintained by hand in separate places, so adding to one and forgetting validation in the other is a realistic drift."
  }
 ],
 "O9_family": "CWE-20 improper input validation: allowlist filter bypass via reserved-prefix exception, plus unvalidated identity-derived system values into shell template/env (command-injection sink)",
 "O9_dos": false,
 "O10_build": {
  "language": "Go (service); Vue/JS frontend not needed for the affected logic",
  "toolchain": "go 1.25.10 (service/go.mod:3)",
  "services": [],
  "offline_after_build": true,
  "project_tests": "service/internal/executor/executor_test.go (stepParseArgs, filterToDefinedArgumentsOnly, e.g. TestFilterToDefinedArgumentsPreservesSystemArgs at :382), service/internal/executor/arguments_test.go (TypeSafetyCheck), service/internal/config/sanitize_test.go; go test ./internal/..."
 },
 "O11_fix_minutes": 40,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "A",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "service/internal/executor/executor.go, service/internal/executor/arguments.go, service/internal/config/sanitize.go, service/internal/config/config.go, frontend/resources/vue/views/ArgumentForm.vue",
  "j_sibling_sites": "no",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Delete the `|| strings.HasPrefix(name, \"ot_\")` in keepArgument and stop, leaving injection before the filter (which then drops the system args) and leaving ot_username unvalidated in both the main path and shellAfterCompleted."
 },
 "out_of_scope_notes": [
  "shellAfterCompleted templates the action's own stdout (`output`) into a shell string unvalidated (service/internal/executor/executor.go:953, still at latest/service/internal/executor/executor.go:1440); documented feature, a different second-order issue, so not listed in O8.",
  "Entity data (.CurrentEntity) is templated into shell commands without type checks (service/internal/tpl/templates.go:140-151); a different trust boundary.",
  "Webhook-tagged actions are refused Shell execution (service/internal/executor/executor.go:698-700), but shellAfterCompleted runs a shell regardless; a separate protection."
 ],
 "unverified": [
  "pinned_commit hash not given in the inputs and no git metadata was read.",
  "repo_mb unknown (no shell to measure); tiny_repo was not evaluated, though Go service source is probably small. It is a medium-size single-binary project.",
  "O1 counts the four API start RPCs; triggers propagate parent Arguments (executor.go:1035-1043) but are internal, not public entry points.",
  "ot_executionTrackingId was already constrained by isValidTrackingID at service/internal/executor/executor.go:36-40 and :518 before the fix; the fix adds a redundant ascii_identifier check.",
  "Whether the advisory text names shellAfterCompleted or the username explicitly is unknown (advisory text not provided beyond the summary)."
 ]
}
  ```
- Published fix sites:   - service/internal/executor/executor.go:736-739 — entry point: StartAction / StartActionAndWait RPCs (service/internal/api/api.go:127-150, service/internal/api/api.go:258-270) with client-supplied argument maps [core executor, argument filter]
  - service/internal/executor/executor.go:667-676 — entry point: every ExecRequest caller (API start RPCs, triggers, cron, calendar, file-in-dir, webhooks); system-arg injection moved after filtering [core executor, step ordering]
  - service/internal/executor/executor.go:750-753 — entry point: all API start RPCs (api.go:127, :258, :279, :302); username comes from trusted header / JWT / OAuth2 identity [core executor, system argument injection (now validated via validatedSystemArgs)]
  - service/internal/executor/executor.go:941-972 — entry point: any action with shellAfterCompleted, started via the API start RPCs [second implementation: separate system-args map and separate shell sink for post-completion command]
  - service/internal/executor/arguments.go:17-25 — entry point: TypeSafetyCheck / ValidateArgument (also ValidateArgumentType RPC, service/internal/api/api.go:792-802) [type registry; new shell_safe_identifier type so email-style usernames stay valid]
  - service/internal/config/sanitize.go:15-29 — entry point: config load and reload (service/internal/config/config_reloader.go:68) [config loader; rejects action arguments (top-level and dashboard inline actions) named with the reserved ot_ prefix]
  - service/internal/config/config.go:1-10 — entry point: constant ReservedArgumentNamePrefix (fix.diff:34-35) [config constant]
  - frontend/resources/vue/views/ArgumentForm.vue:177 — entry point: web UI argument form (fix.diff:21-22) [frontend; renders new type as text input]
- Uncovered routes to confirm (pattern B): none
- Design plan from the lead: TRACK = INJECTED (breaker recipe; mined tasks were all solved, injected-sibling tasks at a recurring check broke both models).

RECURRING CHECK / PROTECTED SINK: Which request-argument names may reach the shell template and process environment without a declared type check: stepParseArgs keeps any undeclared ot_-prefixed argument (keepArgument), injects system args before filtering, and inserts ot_username unvalidated 

STEP 1 - confirm the published fix's sites and these uncovered-route leads with tests on the pinned copy: none noted.
STEP 2 - at these recurring sites, add 2 to 4 realistic sibling GAPS in the same protection that a maintainer could plausibly have left unguarded (verify each by reading the code): service/internal/webhooks/handler.go:165-177 -> a prefix exception in the webhook's own filterToDefinedArguments that  (realistic: matcher.go:173-185 already produces webhook_method/path/quer); service/internal/executor/executor.go:1035-1043 -> triggerLoop injecting an extra system arg (e.g. parent action title or (realistic: Triggers already copy parent Arguments and AuthenticatedUser); service/internal/executor/executor.go:750-753 -> a third injected system arg sourced from identity data (e.g. user grou (realistic: The two system-arg maps (:750-753 and :952-957) are maintain). Each added gap MUST be code a maintainer could plausibly have written (no tell-tale names/comments/shortcuts; match surrounding style), reachable through the real public entry point, covered by a stated invariant, left where the published upstream fix never touches, and carry a DIFFERENT plausible reason a solver would skip it (legacy/compat path, internal/trusted caller, unsupported combination, neighbouring feature). Distinct reasons-to-skip are the lever.
STEP 3 - hidden security tests require closing the base flaw, every uncovered route AND every added gap through the real entry point. The oracle closes all; a fix that closes only the obvious sites must score < 1.0 (add a security_fail check patch for that partial fix).
STEP 4 - COUPLED MUST-KEEP-WORKING (one functional test per trap): System args ot_username and ot_executionTrackingId must still reach templates and env (OT_USERNAME) for every action and for shellAfterCompleted, and email-style usernames (alice@example.com, plus-add (near docs/modules/ROOT/pages/args/env.adoc:46-66; docs/); keep every legitimate use working.

Aim for >=3 levers with DIFFERENT reasons a solver would skip them. Every gap must be findable by a blind engineer from instruction.md + code; if not, drop it. instruction.md stays product-level: system, one impact with one user trigger, invariants covering EVERY route/gap (a natural list, no count); never name files/functions/fields/CVEs (all in manifest.leak_terms). Register each added gap and route in build/audit/uncovered-routes.tsv.
- Host notes: Language: Go (service); Vue/JS frontend not needed for the affected logic. Offline after build, no external services. Added gaps go in OUR copy only, register them. Recurring check (4 entry points). Build+test via real entry points; project's own area tests pass at the pinned commit. Pin at the vulnerable commit; keep unrelated earlier fixes. If the repo is a large monorepo, scope the build/tests to the affected package only.

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

## Environment (`tasks/olivetin-allowlist-inj/environment/Dockerfile`)
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

## Report to the solver (`tasks/olivetin-allowlist-inj/instruction.md`)
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

## Tests (`tasks/olivetin-allowlist-inj/tests/`)
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
- **Wrong-fix patches** go in `build/olivetin-allowlist-inj/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/olivetin-allowlist-inj/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/olivetin-allowlist-inj/manifest.json`:**
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

**Also in `build/olivetin-allowlist-inj/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py olivetin-allowlist-inj --only static
python3 -I builder/gate.py olivetin-allowlist-inj --only nop
python3 -I builder/gate.py olivetin-allowlist-inj --only oracle
python3 -I builder/gate.py olivetin-allowlist-inj --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/olivetin-allowlist-inj/`;
  - edit only `tasks/olivetin-allowlist-inj/`, `build/olivetin-allowlist-inj/` and, for pattern B, the register;
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
