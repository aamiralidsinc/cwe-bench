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

Project root: `/home/mara/cwe-bench`. Task: `contrast-continuous-application-security-plugin-mm`. Pattern: `A`. Track: `injected`.

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
- Advisory: ["GHSA-8263-QV4G-VFXR", "CVE-2026-57299"]; jenkinsci/contrast-continuous-application-security-plugin; missing authorization / wrong permission context on Jenkins Stapler form endpoints (CWE-862, A01)
- Pinned (vulnerable) commit: parent of d7776646af26d928cb0d50922d61dadc2c6aa11c (parent_commit not given in candidate). Published fix: d7776646af26d928cb0d50922d61dadc2c6aa11c.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "24304",
 "advisory_ids": [
  "GHSA-8263-QV4G-VFXR",
  "CVE-2026-57299"
 ],
 "repo": "jenkinsci/contrast-continuous-application-security-plugin",
 "pinned_commit": "parent of d7776646af26d928cb0d50922d61dadc2c6aa11c (parent_commit not given in candidate)",
 "fix_commits": [
  "d7776646af26d928cb0d50922d61dadc2c6aa11c"
 ],
 "trust_decision": {
  "summary": "Who may make the plugin's Stapler form endpoints list global Contrast connection profiles, apps and rules (and query TeamServer with the stored credentials): decided per endpoint inside each descriptor; at pinned some check Jenkins-root Item.CONFIGURE (wrong context), others check nothing; fix requires Item.CONFIGURE on the ancestor item, or ADMINISTER when there is no item.",
  "evidence": [
   "src/main/java/com/aspectsecurity/contrast/contrastjenkins/ContrastPluginConfig.java:110-115",
   "src/main/java/com/aspectsecurity/contrast/contrastjenkins/VulnerabilityTrendRecorder.java:442-450",
   "src/main/java/com/aspectsecurity/contrast/contrastjenkins/ThresholdCondition.java:279-315",
   "fix.diff:64-69"
  ]
 },
 "landing_point": {
  "where": "src/main/java/com/aspectsecurity/contrast/contrastjenkins/VulnerabilityTrendRecorder.java:448",
  "why": "The main Freestyle publisher's profile-name fill has no permission check at all; it is the most obvious 'missing permission check' a Jenkins engineer would grep for (doFill* without hasPermission)."
 },
 "fix_sites": [
  {
   "where": "src/main/java/com/aspectsecurity/contrast/contrastjenkins/ContrastAgentStep.java:87",
   "entry_point": "HTTP .../descriptorByName/...ContrastAgentStep/fillProfileItems (pipeline snippet generator)",
   "module_kind": "pipeline step descriptor (second implementation of profile fill)"
  },
  {
   "where": "src/main/java/com/aspectsecurity/contrast/contrastjenkins/ContrastPluginConfig.java:110",
   "entry_point": "HTTP .../ContrastPluginConfig/fillTeamServerProfileNameItems (global config + job property)",
   "module_kind": "JobProperty/global-config descriptor"
  },
  {
   "where": "src/main/java/com/aspectsecurity/contrast/contrastjenkins/ContrastPluginConfig.java:122",
   "entry_point": "HTTP .../ContrastPluginConfig/fillThresholdVulnTypeItems?teamServerProfileName=",
   "module_kind": "JobProperty/global-config descriptor"
  },
  {
   "where": "src/main/java/com/aspectsecurity/contrast/contrastjenkins/ThresholdCondition.java:279",
   "entry_point": "HTTP .../ThresholdCondition/checkApplicationId (form validation, outbound TeamServer call with stored creds)",
   "module_kind": "nested describable descriptor (composed into recorder form)"
  },
  {
   "where": "src/main/java/com/aspectsecurity/contrast/contrastjenkins/ThresholdCondition.java:306",
   "entry_point": "HTTP .../ThresholdCondition/fillApplicationIdItems (also refreshes and saves app cache; fix adds @RequirePOST)",
   "module_kind": "nested describable descriptor"
  },
  {
   "where": "src/main/java/com/aspectsecurity/contrast/contrastjenkins/ThresholdCondition.java:340",
   "entry_point": "HTTP .../ThresholdCondition/fillThresholdVulnTypeItems",
   "module_kind": "nested describable descriptor"
  },
  {
   "where": "src/main/java/com/aspectsecurity/contrast/contrastjenkins/VulnerabilityTrendRecorder.java:443",
   "entry_point": "Stapler JS proxy (st:bind) isAllowGlobalThresholdConditionsOverride",
   "module_kind": "@JavaScriptMethod on publisher descriptor"
  },
  {
   "where": "src/main/java/com/aspectsecurity/contrast/contrastjenkins/VulnerabilityTrendRecorder.java:448",
   "entry_point": "HTTP .../VulnerabilityTrendRecorder/fillTeamServerProfileNameItems",
   "module_kind": "publisher descriptor"
  },
  {
   "where": "src/main/java/com/aspectsecurity/contrast/contrastjenkins/VulnerabilityTrendStep.java:221",
   "entry_point": "HTTP .../VulnerabilityTrendStep/fillProfileItems",
   "module_kind": "pipeline step descriptor"
  },
  {
   "where": "src/main/java/com/aspectsecurity/contrast/contrastjenkins/VulnerabilityTrendStep.java:233",
   "entry_point": "HTTP .../VulnerabilityTrendStep/fillApplicationIdItems?profile=",
   "module_kind": "pipeline step descriptor"
  },
  {
   "where": "src/main/java/com/aspectsecurity/contrast/contrastjenkins/VulnerabilityTrendStep.java:241",
   "entry_point": "HTTP .../VulnerabilityTrendStep/fillRuleItems?profile=",
   "module_kind": "pipeline step descriptor"
  }
 ],
 "O1_entry_points": 11,
 "O2_out_of_scope_site": {
  "kind": "wrapper_or_composition",
  "where": "src/main/java/com/aspectsecurity/contrast/contrastjenkins/ThresholdCondition.java:279-342 (nested describable composed into the recorder form at src/main/resources/com/aspectsecurity/contrast/contrastjenkins/VulnerabilityTrendRecorder/config.jelly:13-17); also the JS-proxy method src/main/java/com/aspectsecurity/contrast/contrastjenkins/VulnerabilityTrendRecorder.java:442-445"
 },
 "O3_reason_to_dismiss": "ThresholdCondition is only a sub-form inside the recorder (a solver guards the recorder and assumes the sub-form is covered), doCheckApplicationId 'only returns a warning', and isAllowGlobalThresholdConditionsOverride 'only returns a boolean' so it looks like no data leaks.",
 "O4_distance": {
  "files": 5,
  "packages": 1,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Users with Item.CONFIGURE on a specific job (folder/project-matrix scoped, no global permission) and admins on the global config page (no ancestor item) must still get populated profile/app/rule lists; requiring ADMINISTER everywhere, or keeping the Jenkins-root check, breaks job configuration. Static fills (agent type, severity, build result) must stay open.",
  "where": "src/main/java/com/aspectsecurity/contrast/contrastjenkins/ContrastPluginConfig.java:110-127; src/main/java/com/aspectsecurity/contrast/contrastjenkins/VulnerabilityTrendStep.java:248-251; src/main/java/com/aspectsecurity/contrast/contrastjenkins/ContrastAgentStep.java:94-97"
 },
 "O6_input_shapes": [
  "ancestor item present (job-config context) -> item.hasPermission(Item.CONFIGURE)",
  "no ancestor item (global config / root descriptorByName URL) -> Jenkins ADMINISTER",
  "return-type variants: ListBoxModel, ComboBoxModel, FormValidation (doCheck), boolean (@JavaScriptMethod)",
  "GET vs POST on the state-changing fillApplicationIdItems (@RequirePOST added, fix.diff:127)"
 ],
 "O7_producer": {
  "kind": "cache",
  "where": "src/main/java/com/aspectsecurity/contrast/contrastjenkins/ThresholdCondition.java:317-329 (refreshApps re-fetches apps with stored creds and persists them via contrastPluginConfigDescriptor.save()); read back by getApplicationIdsComboBoxModel at src/main/java/com/aspectsecurity/contrast/contrastjenkins/ThresholdCondition.java:314",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [],
 "O8b_injection_room": [
  {
   "where": "src/main/java/com/aspectsecurity/contrast/contrastjenkins/VulnerabilityTrendStep.java:248-251",
   "sibling": "a doCheckApplicationId on the pipeline step descriptor mirroring ThresholdCondition's TeamServer lookup",
   "why_realistic": "ThresholdCondition already has this validation (src/main/java/com/aspectsecurity/contrast/contrastjenkins/ThresholdCondition.java:279-299); a maintainer would copy it to the step for snippet-generator parity."
  },
  {
   "where": "src/main/java/com/aspectsecurity/contrast/contrastjenkins/GlobalThresholdCondition.java:12",
   "sibling": "a Descriptor with doFillTeamServerProfileNameItems / doFillThresholdVulnTypeItems for global threshold conditions",
   "why_realistic": "GlobalThresholdCondition has no descriptor today and its fills are borrowed from ContrastPluginConfig; extracting a proper descriptor is a natural refactor that would copy the fill bodies."
  },
  {
   "where": "src/main/java/com/aspectsecurity/contrast/contrastjenkins/ContrastAgentStep.java:94-97",
   "sibling": "a @JavaScriptMethod or doFill returning the profile's TeamServer URL/org for the agent step",
   "why_realistic": "The agent-download step already resolves profile URL and creds at src/main/java/com/aspectsecurity/contrast/contrastjenkins/ContrastAgentStep.java:120-129; surfacing it in the UI is a plausible feature."
  }
 ],
 "O9_family": "missing authorization / wrong permission context on Jenkins Stapler form endpoints (CWE-862, A01)",
 "O9_dos": false,
 "O10_build": {
  "language": "Java",
  "toolchain": "Maven, Jenkins plugin parent pom 5.31, jenkins.version 2.479.3 (pom.xml:7-8, pom.xml:27); Lombok; contrast-sdk-java 3.4.1",
  "services": [],
  "offline_after_build": true,
  "project_tests": "JUnit4 + PowerMock unit tests; src/test/java/com/aspectsecurity/contrast/contrastjenkins/ContrastPluginConfigSecurityTest.java already exists at pinned and covers the old global-check behaviour; ThresholdConditionStub provides a descriptor stub"
 },
 "O11_fix_minutes": 30,
 "O12_red_flags": [],
 "O13_recall_risk": "low",
 "pattern_fit": "A",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "ContrastAgentStep.java, ContrastPluginConfig.java, ThresholdCondition.java, VulnerabilityTrendRecorder.java, VulnerabilityTrendStep.java",
  "j_sibling_sites": "no",
  "j_cause_other_layer": 0,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Copy the existing Jenkins.getActiveInstance().hasPermission(Item.CONFIGURE) guard onto the unguarded recorder/threshold fills, leaving the wrong root-level context everywhere and skipping the doCheck and @JavaScriptMethod routes."
 },
 "out_of_scope_notes": [
  "Fix also adds a blank-host URL check in doTestTeamServerConnection (fix.diff:78-80); input validation, not the permission check.",
  "Latest tree adds @RequirePOST on doCheckApplicationId (latest ThresholdCondition.java:282), not part of this fix; CSRF hardening, outside this advisory."
 ],
 "unverified": [
  "Whether @AncestorInPath is honoured for a @JavaScriptMethod: the JS caller passes one argument (src/main/resources/com/aspectsecurity/contrast/contrastjenkins/VulnerabilityTrendRecorder/config.jelly:179) while the fixed signature takes (Item, String); the published fix for that route may be ineffective or break the UI toggle. Not checked against Stapler source.",
  "j_defence_ineffective=1 relies on the pre-fix Jenkins-root hasPermission(Item.CONFIGURE) checks (e.g. src/main/java/com/aspectsecurity/contrast/contrastjenkins/VulnerabilityTrendStep.java:222) being the wrong context, not a bypass; the candidate metadata says c_defence_present=0.",
  "pinned commit SHA not given (parent_commit null); repo size in MB not measured.",
  "Whether the advisory text names specific endpoints (advisory text not available locally); recall risk is a guess from it being a small plugin and a recent publication.",
  "Possible red flag tiny_repo: the plugin has about 19 main source files and is likely under 5 MB, but this was not measured, so the flag is not set."
 ]
}
  ```
- Published fix sites:   - src/main/java/com/aspectsecurity/contrast/contrastjenkins/ContrastAgentStep.java:87 — entry point: HTTP .../descriptorByName/...ContrastAgentStep/fillProfileItems (pipeline snippet generator) [pipeline step descriptor (second implementation of profile fill)]
  - src/main/java/com/aspectsecurity/contrast/contrastjenkins/ContrastPluginConfig.java:110 — entry point: HTTP .../ContrastPluginConfig/fillTeamServerProfileNameItems (global config + job property) [JobProperty/global-config descriptor]
  - src/main/java/com/aspectsecurity/contrast/contrastjenkins/ContrastPluginConfig.java:122 — entry point: HTTP .../ContrastPluginConfig/fillThresholdVulnTypeItems?teamServerProfileName= [JobProperty/global-config descriptor]
  - src/main/java/com/aspectsecurity/contrast/contrastjenkins/ThresholdCondition.java:279 — entry point: HTTP .../ThresholdCondition/checkApplicationId (form validation, outbound TeamServer call with stored creds) [nested describable descriptor (composed into recorder form)]
  - src/main/java/com/aspectsecurity/contrast/contrastjenkins/ThresholdCondition.java:306 — entry point: HTTP .../ThresholdCondition/fillApplicationIdItems (also refreshes and saves app cache; fix adds @RequirePOST) [nested describable descriptor]
  - src/main/java/com/aspectsecurity/contrast/contrastjenkins/ThresholdCondition.java:340 — entry point: HTTP .../ThresholdCondition/fillThresholdVulnTypeItems [nested describable descriptor]
  - src/main/java/com/aspectsecurity/contrast/contrastjenkins/VulnerabilityTrendRecorder.java:443 — entry point: Stapler JS proxy (st:bind) isAllowGlobalThresholdConditionsOverride [@JavaScriptMethod on publisher descriptor]
  - src/main/java/com/aspectsecurity/contrast/contrastjenkins/VulnerabilityTrendRecorder.java:448 — entry point: HTTP .../VulnerabilityTrendRecorder/fillTeamServerProfileNameItems [publisher descriptor]
  - src/main/java/com/aspectsecurity/contrast/contrastjenkins/VulnerabilityTrendStep.java:221 — entry point: HTTP .../VulnerabilityTrendStep/fillProfileItems [pipeline step descriptor]
  - src/main/java/com/aspectsecurity/contrast/contrastjenkins/VulnerabilityTrendStep.java:233 — entry point: HTTP .../VulnerabilityTrendStep/fillApplicationIdItems?profile= [pipeline step descriptor]
  - src/main/java/com/aspectsecurity/contrast/contrastjenkins/VulnerabilityTrendStep.java:241 — entry point: HTTP .../VulnerabilityTrendStep/fillRuleItems?profile= [pipeline step descriptor]
- Uncovered routes to confirm (pattern B): none
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

## Environment (`tasks/contrast-continuous-application-security-plugin-mm/environment/Dockerfile`)
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

## Report to the solver (`tasks/contrast-continuous-application-security-plugin-mm/instruction.md`)
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

## Tests (`tasks/contrast-continuous-application-security-plugin-mm/tests/`)
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
- **Wrong-fix patches** go in `build/contrast-continuous-application-security-plugin-mm/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/contrast-continuous-application-security-plugin-mm/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/contrast-continuous-application-security-plugin-mm/manifest.json`:**
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

**Also in `build/contrast-continuous-application-security-plugin-mm/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py contrast-continuous-application-security-plugin-mm --only static
python3 -I builder/gate.py contrast-continuous-application-security-plugin-mm --only nop
python3 -I builder/gate.py contrast-continuous-application-security-plugin-mm --only oracle
python3 -I builder/gate.py contrast-continuous-application-security-plugin-mm --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/contrast-continuous-application-security-plugin-mm/`;
  - edit only `tasks/contrast-continuous-application-security-plugin-mm/`, `build/contrast-continuous-application-security-plugin-mm/` and, for pattern B, the register;
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
