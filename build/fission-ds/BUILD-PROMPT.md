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

Project root: `/home/mara/cwe-bench`. Task: `fission-ds`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: ["GHSA-GX55-F84R-V3R7", "CVE-2026-50564", "GO-2026-5855"]; fission/fission; privilege escalation via unchecked pod-spec passthrough (CWE-269/284/693, missing authorization on security-sensitive fields)
- Pinned (vulnerable) commit: parent of e484df8460bb4e8026e24210120602aa7f181f64 (parent_commit not given in candidate). Published fix: e484df8460bb4e8026e24210120602aa7f181f64.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "17734",
 "advisory_ids": [
  "GHSA-GX55-F84R-V3R7",
  "CVE-2026-50564",
  "GO-2026-5855"
 ],
 "repo": "fission/fission",
 "pinned_commit": "parent of e484df8460bb4e8026e24210120602aa7f181f64 (parent_commit not given in candidate)",
 "fix_commits": [
  "e484df8460bb4e8026e24210120602aa7f181f64"
 ],
 "trust_decision": {
  "summary": "Whether tenant-supplied pod fields in Environment (runtime/builder) and Function CRDs may carry host-namespace, privileged, hostPath, capability or ServiceAccount settings onto pods the executor/buildermgr create with their own SA; decided at admission (Environment/Function Validate behind the validating webhook) and at the controller merge layer (MergePodSpec).",
  "evidence": [
   "pkg/apis/core/v1/validation.go:655-669",
   "pkg/apis/core/v1/validation.go:296",
   "pkg/webhook/environment.go:45-55",
   "pkg/executor/util/merge.go:145-167",
   "pkg/executor/util/merge.go:83",
   "charts/fission-all/templates/webhook-server/webhooks.yaml:65-76"
  ]
 },
 "landing_point": {
  "where": "pkg/apis/core/v1/validation.go:655",
  "why": "Summary names the Environment CRD podspec passthrough; Environment.Validate (called by the Environment webhook, pkg/webhook/environment.go:49-50) is where podspec checks already live (validation.go:662-668)."
 },
 "fix_sites": [
  {
   "where": "pkg/apis/core/v1/validation.go:669 (fix.diff:365-366)",
   "entry_point": "Kubernetes API create of fission.io/v1 Environment (spec.runtime.podspec, spec.builder.podspec) via validating webhook /validate-fission-io-v1-environment",
   "module_kind": "API type validation (admission)"
  },
  {
   "where": "pkg/apis/core/v1/validation.go:296 (fix.diff:354)",
   "entry_point": "Kubernetes API create/update of fission.io/v1 Function (spec.podspec, container executor) via /validate-fission-io-v1-function",
   "module_kind": "API type validation for a second CRD (Function)"
  },
  {
   "where": "pkg/apis/core/v1/podspec_safety.go (new, fix.diff:72-135)",
   "entry_point": "shared helper ValidatePodSpecSafety called by both Validate sites",
   "module_kind": "new validation helper"
  },
  {
   "where": "pkg/webhook/environment.go:45 (fix.diff:711)",
   "entry_point": "Kubernetes API UPDATE/PATCH of Environment (webhook previously CREATE-only)",
   "module_kind": "webhook registration marker"
  },
  {
   "where": "charts/fission-all/templates/webhook-server/webhooks.yaml:74 (fix.diff:9)",
   "entry_point": "Helm-installed ValidatingWebhookConfiguration operations for environments",
   "module_kind": "deployment config (chart)"
  },
  {
   "where": "pkg/executor/util/merge.go:83 and pkg/executor/util/merge.go:145-167 (fix.diff:388-402, 427-456)",
   "entry_point": "controller reconcile: poolmgr genDeploymentSpec (pkg/executor/executortype/poolmgr/gp_deployment.go:222), newdeploy (pkg/executor/executortype/newdeploy/newdeploy.go:316), container executor (pkg/executor/executortype/container/deployment.go:245), buildermgr (pkg/buildermgr/envwatcher.go:520)",
   "module_kind": "lower-level merge utility (defence in depth for webhook-bypass / stale objects)"
  }
 ],
 "O1_entry_points": 4,
 "O2_out_of_scope_site": {
  "kind": "defaults_or_merge_route",
  "where": "pkg/executor/util/merge.go:58-199 (MergePodSpec copies HostNetwork/HostPID/HostIPC/ServiceAccountName at 145-167, appends hostPath volumes at 83, container SecurityContext via mergeContainerList at 68-80); second CRD route at pkg/apis/core/v1/validation.go:296 (Function.spec.podspec)"
 },
 "O3_reason_to_dismiss": "The admission webhook (failurePolicy=Fail) now rejects these fields, so changing the shared merge utility looks redundant and risky for operator podSpecPatch users; Function.spec.podspec belongs to the container executor, a different CRD/advisory than the Environment report.",
 "O4_distance": {
  "files": 5,
  "packages": 3,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Operator-supplied podSpecPatch (chart runtimePodSpec/builderPodSpec) and tenant pod-level SecurityContext hardening (runAsNonRoot, runAsUser, fsGroup) must still propagate through MergePodSpec; benign capabilities (NET_BIND_SERVICE, CHOWN), configMap volumes, nodeSelector, tolerations must still be accepted. Dropping SecurityContext or rejecting all podspec containers breaks these.",
  "where": "pkg/executor/util/merge.go:115-118; pkg/executor/executortype/poolmgr/gp_deployment.go:174-186; pkg/buildermgr/envwatcher.go:464-483; fix.diff:410-421; fix.diff:325-343"
 },
 "O6_input_shapes": [
  "pod-level booleans hostNetwork / hostPID / hostIPC",
  "serviceAccountName and the deprecated serviceAccount alias",
  "hostPath entries anywhere in the volumes list",
  "containers[] and initContainers[] (separate lists)",
  "securityContext.privileged and allowPrivilegeEscalation pointer bools",
  "capabilities.add list mixing dangerous and benign entries",
  "runtime.podspec vs builder.podspec vs Function.spec.podspec",
  "CREATE vs UPDATE/PATCH of an existing Environment"
 ],
 "O7_producer": {
  "kind": "mapper",
  "where": "pkg/executor/util/merge.go:58 (MergePodSpec) and pkg/executor/util/merge.go:35 (MergeContainer) build the final pod spec; operator patch loaded by util.GetSpecFromConfigMap at pkg/executor/executor.go:278 and pkg/buildermgr/buildermgr.go:58",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "Environment.spec.runtime.container (single Container field, not a PodSpec) is merged via MergeContainer with mergo.WithOverride, carrying securityContext.privileged/allowPrivilegeEscalation/capabilities into poolmgr and newdeploy pods; neither ValidatePodSpecSafety nor the merge-layer sanitizer reaches it.",
   "where": "pkg/executor/executortype/poolmgr/gp_deployment.go:111-144; pkg/executor/executortype/newdeploy/newdeploy.go:185-215; pkg/executor/util/merge.go:35-55",
   "reason_to_dismiss": "The advisory is about 'podspec passthrough'; runtime.container is a separate field that only overrides the runtime container, not pod-level host settings.",
   "distance": "same package as the merge fix (pkg/executor/util/merge.go), call sites in two executor packages; validation would sit beside the fix in pkg/apis/core/v1/validation.go",
   "present_in_latest": "no",
   "latest_where": "latest/pkg/executor/util/merge.go:41-50; latest/pkg/apis/core/v1/validation.go:1394-1398"
  },
  {
   "route": "Environment.spec.builder.container is merged the same way into the builder deployment that runs under the fission-builder SA.",
   "where": "pkg/buildermgr/envwatcher.go:418-437; pkg/executor/util/merge.go:35-55",
   "reason_to_dismiss": "Builder container is a build-time helper; the advisory example is runtime pods and podspec fields.",
   "distance": "another package (pkg/buildermgr) from the landing point",
   "present_in_latest": "no",
   "latest_where": "latest/pkg/apis/core/v1/validation.go:1399; latest/pkg/executor/util/merge.go:50"
  }
 ],
 "O8b_injection_room": [
  {
   "where": "pkg/executor/util/merge.go:189-191",
   "sibling": "a merge of targetPodSpec.EphemeralContainers or a new pod-level field (e.g. ShareProcessNamespace-like) copied without sanitizing",
   "why_realistic": "MergePodSpec is a hand-written field-by-field copier with TODOs; maintainers add fields here as users request them."
  },
  {
   "where": "pkg/apis/core/v1/validation.go:296",
   "sibling": "a second Function-level container field (e.g. sidecar/init override) validated only by name, not by ValidatePodSpecSafety",
   "why_realistic": "Environment already has both PodSpec and Container fields; mirroring that on Function is a plausible feature."
  }
 ],
 "O9_family": "privilege escalation via unchecked pod-spec passthrough (CWE-269/284/693, missing authorization on security-sensitive fields)",
 "O9_dos": false,
 "O10_build": {
  "language": "Go",
  "toolchain": "go 1.26.3 (go.mod:3), Go modules",
  "services": [],
  "offline_after_build": true,
  "project_tests": "Pure unit tests: pkg/executor/util/merge_test.go, pkg/webhook/function_test.go (calls Validate directly), pkg/executor/executortype/poolmgr/gp_deployment_test.go, pkg/executor/executortype/newdeploy/newdeploy_test.go, pkg/buildermgr/envwatcher_test.go; no cluster needed for these."
 },
 "O11_fix_minutes": 45,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "pkg/apis/core/v1/podspec_safety.go (new), pkg/apis/core/v1/validation.go, pkg/executor/util/merge.go, pkg/webhook/environment.go, charts/fission-all/templates/webhook-server/webhooks.yaml",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Add hostNetwork/hostPID/privileged checks for spec.runtime.podspec in Environment.Validate only, leaving builder podspec, Function podspec, UPDATE verb, the merge layer and the runtime/builder Container fields open."
 },
 "out_of_scope_notes": [
  "MessageQueueTrigger.spec.podspec uses a separate allowlist (pkg/executor/util/merge_allowlist.go:110, pkg/webhook/messagequeuetrigger.go:78) from a different advisory; not examined."
 ],
 "unverified": [
  "pinned_commit hash: candidate gives parent_commit null; repo dir assumed to be the parent of the fix commit.",
  "repo_mb not measured (no shell available); tiny_repo/giant_repo flags not assessed, repo appears to be a large multi-package Go project.",
  "Pod-level SecurityContext (sysctls, seLinuxOptions, windowsOptions) is still propagated by design (pkg/executor/util/merge.go:115-118, kept in latest/pkg/executor/util/merge.go:145-146); not treated as an O8 route because the fix documents it as intended.",
  "j_defence_ineffective=1 refers to the existing Environment webhook being CREATE-only (pkg/webhook/environment.go:45, charts/fission-all/templates/webhook-server/webhooks.yaml:74), so PATCH bypassed admission.",
  "Recall: fix comments name three GHSAs and upstream later published GHSA-m63v-2g9w-2w6v for the Container-field sibling (latest/pkg/executor/util/merge.go:48), so the O8 route is itself publicly documented."
 ]
}
  ```
- Published fix sites:   - pkg/apis/core/v1/validation.go:669 (fix.diff:365-366) — entry point: Kubernetes API create of fission.io/v1 Environment (spec.runtime.podspec, spec.builder.podspec) via validating webhook /validate-fission-io-v1-environment [API type validation (admission)]
  - pkg/apis/core/v1/validation.go:296 (fix.diff:354) — entry point: Kubernetes API create/update of fission.io/v1 Function (spec.podspec, container executor) via /validate-fission-io-v1-function [API type validation for a second CRD (Function)]
  - pkg/apis/core/v1/podspec_safety.go (new, fix.diff:72-135) — entry point: shared helper ValidatePodSpecSafety called by both Validate sites [new validation helper]
  - pkg/webhook/environment.go:45 (fix.diff:711) — entry point: Kubernetes API UPDATE/PATCH of Environment (webhook previously CREATE-only) [webhook registration marker]
  - charts/fission-all/templates/webhook-server/webhooks.yaml:74 (fix.diff:9) — entry point: Helm-installed ValidatingWebhookConfiguration operations for environments [deployment config (chart)]
  - pkg/executor/util/merge.go:83 and pkg/executor/util/merge.go:145-167 (fix.diff:388-402, 427-456) — entry point: controller reconcile: poolmgr genDeploymentSpec (pkg/executor/executortype/poolmgr/gp_deployment.go:222), newdeploy (pkg/executor/executortype/newdeploy/newdeploy.go:316), container executor (pkg/executor/executortype/container/deployment.go:245), buildermgr (pkg/buildermgr/envwatcher.go:520) [lower-level merge utility (defence in depth for webhook-bypass / stale objects)]
- Uncovered routes to confirm (pattern B):   - pkg/executor/executortype/poolmgr/gp_deployment.go:111-144; pkg/executor/executortype/newdeploy/newdeploy.go:185-215; pkg/executor/util/merge.go:35-55 — Environment.spec.runtime.container (single Container field, not a PodSpec) is merged via MergeContainer with mergo.WithOverride, carrying securityContext.privileged/allowPrivilegeEscalation/capabilities into poolmgr and newdeploy pods; neither ValidatePodSpecSafety nor the merge-layer sanitizer reaches it. (reason to dismiss: The advisory is about 'podspec passthrough'; runtime.container is a separate field that only overrides the runtime container, not pod-level host settings.; still in latest: no)
  - pkg/buildermgr/envwatcher.go:418-437; pkg/executor/util/merge.go:35-55 — Environment.spec.builder.container is merged the same way into the builder deployment that runs under the fission-builder SA. (reason to dismiss: Builder container is a build-time helper; the advisory example is runtime pods and podspec fields.; still in latest: no)
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

## Environment (`tasks/fission-ds/environment/Dockerfile`)
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

## Report to the solver (`tasks/fission-ds/instruction.md`)
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

## Tests (`tasks/fission-ds/tests/`)
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
- **Wrong-fix patches** go in `build/fission-ds/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/fission-ds/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/fission-ds/manifest.json`:**
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

**Also in `build/fission-ds/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py fission-ds --only static
python3 -I builder/gate.py fission-ds --only nop
python3 -I builder/gate.py fission-ds --only oracle
python3 -I builder/gate.py fission-ds --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/fission-ds/`;
  - edit only `tasks/fission-ds/`, `build/fission-ds/` and, for pattern B, the register;
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
