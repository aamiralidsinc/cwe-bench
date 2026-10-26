# FAIRNESS review: fission-podspec-passthrough

Reviewer: pre-trial fairness/leniency gate (BUILDER.md 3h). I did not write the tests. I ran nothing: no Docker, trials or gates.
Inputs read: instruction.md, all of tests/ (security, functional, test.sh, score.py), solution/fix.patch, manifest.json, notes.md, and these checks/*.patch: alt_refuse_allowlist, hardening, admission_only, no_update, crash_on_unsafe, validate_old_on_update, drop_pod_security_context. For the other check patches I relied on the manifest's descriptions.

## 1. Per-test fairness

"Instr" quotes instruction.md. "Correct fix fails?" asks whether a correct fix that a competent engineer writes from the instruction alone could fail the test.

### Security group (`TestSecZZ*`)

| Test | Asserts | Fair because | Correct fix fails? | Risk |
|---|---|---|---|---|
| webhook::TestSecZZEnvRuntimePodSpecHostNamespaces (hostNetwork/hostPID/hostIPC) | Env webhook ValidateCreate errors | Instr: "share the node's network, PID or IPC namespace"; "Admission must refuse such an object with a validation error" | no | low |
| webhook::TestSecZZEnvRuntimePodSpecServiceAccount (serviceAccountName, serviceAccount) | both SA fields refused at admission | Instr: "run under a service account the tenant chose, through any field that selects one"; expert knowledge: `serviceAccount` is the deprecated alias that k8s still honours | no | low |
| webhook::TestSecZZEnvRuntimePodSpecHostPathVolume | a hostPath volume listed 2nd, after a configMap, is refused | Instr: "mount a path from the node's filesystem" | no | low |
| webhook::TestSecZZEnvRuntimePodSpecContainerPrivileges (privileged sidecar, init APE, init privileged) | refused | Instr: "run a privileged container, or a container that allows privilege escalation"; "any pod" covers init containers | no | low |
| webhook::TestSecZZEnvRuntimePodSpecAddedCapability | `[NET_BIND_SERVICE, SYS_ADMIN]` refused | Instr names SYS_ADMIN | no. Refusing is required here, and stripping is not enough, because admission must refuse | low |
| webhook::TestSecZZEnvBuilderPodSpec (4 subtests) | builder podspec refused | Instr: "every part of these objects that shapes the resulting pods" plus "any pod that the platform creates" (builder pods are named in the intro) | no | low |
| webhook::TestSecZZEnvRuntimeContainerPrivileges (3) | `spec.runtime.container` SC refused | Instr: "every part of these objects that shapes the resulting pods" | no. A careful reader of the Environment type finds this field | low |
| webhook::TestSecZZEnvBuilderContainerPrivileges (2) | `spec.builder.container` SC refused | same as above | no | low |
| webhook::TestSecZZEnvUpdate/update_is_validated | ValidateUpdate(old clean, new hostPID) errors | Instr: "on any later update or patch" | no | low |
| webhook::TestSecZZEnvUpdate/installed_webhook_receives_updates | the Helm chart `webhooks.yaml` entry for `/validate-fission-io-v1-environment` lists UPDATE or `*` | Instr: "on any later update or patch"; expert knowledge: the operations in a ValidatingWebhookConfiguration control which verbs reach the validator | **maybe**. A fix that changes only the kubebuilder `verbs=` marker, or only a controller-gen manifest outside `charts/fission-all`, fails it. The parser accepts block and flow styles and quoted forms, so formatting is not the issue | **medium** |
| webhook::TestSecZZFunctionPodSpec (6) | Function create and update refused | Instr: "No Environment or Function object" | no | low |
| poolmgr::TestSecZZPoolStoredRuntimePodSpec (8) | `genDeploymentSpec` returns an error, or a spec with none of the forbidden settings (effective SA checked) | Instr: "Objects that are already stored … must never yield such pods … may decline … or deploy them without" | no. Both refusing and stripping pass. A panic fails, which matches "no component may crash" | low |
| poolmgr::TestSecZZPoolStoredRuntimeContainer (3) | same, via `spec.runtime.container` | same | no | low |
| container::TestSecZZContainerExecutorStoredFunctionPodSpec (7) | `getDeploymentSpec` returns an error, or a clean deployment | same | no | low |
| buildermgr::TestSecZZBuilderStoredBuilderPodSpec (5) / ...StoredBuilderContainer (2) | no Deployment created in the fake client carries the settings | same | no | low |

### Functional group (hidden `TestFuncZZ*` plus the project's 14 restored test files)

| Test | Asserts | Fair because | Correct fix fails? | Risk |
|---|---|---|---|---|
| webhook::TestFuncZZEnvPlainAccepted | plain Env accepted on create and update | Instr "Keep legitimate use working" | no | low |
| webhook::TestFuncZZEnvRuntimePodSpecCustomisationAccepted / ...BuilderPodSpec... | hardened pod SC, nodeSelector, tolerations, configMap/emptyDir, sidecar plus init container with drop ALL, add NET_BIND_SERVICE/CHOWN, privileged=false, APE=false, automount=false: all accepted | Instr "Must keep working" bullets 1–3 | no | low |
| webhook::TestFuncZZEnvContainerCustomisationAccepted | the same hardening on runtime and builder container overrides is accepted | same | no | low |
| webhook::TestFuncZZFunctionContainerExecutorAccepted | a customised Function is accepted on create and update | same | no | low |
| poolmgr::TestFuncZZPoolTenantPodSpecCustomisation | the customisation reaches the pod, SA stays `fission-fetcher`, NET_BIND_SERVICE is kept | same, plus bullet 3 | no | low |
| poolmgr::TestFuncZZPoolRuntimeContainerCustomisation | env, limits, hardening and NET_BIND_SERVICE from the override reach the `py` container | same | no | low |
| poolmgr::TestFuncZZPoolOperatorPatch / buildermgr::TestFuncZZBuilderOperatorPatch | the operator patch's pod SC, scheduling settings and tolerations reach the pod | Instr bullet 4 | no | low |
| container::TestFuncZZContainerExecutorPodSpec | the Function podspec reaches the deployment, and `Capabilities.Add` is exactly `[NET_BIND_SERVICE]` | bullets 1–3 | no. A fix that injects extra caps would be odd | low |
| buildermgr::TestFuncZZBuilderTenantCustomisation | the builder customisation reaches the pod, SA stays `fission-builder`, Add is exactly `[CHOWN]` | same | no | low |
| project tests (14 files restored pristine) | existing behaviour | Instr "The project's existing test suite" | maybe, if a fix adds default hardening (for example forcing APE=false on every container) and a deep-equal merge test breaks. The instruction does not ask for that | low |

Cross-cutting: the hidden tests call unexported internals: `GenericPool{podSpecPatch,...}.genDeploymentSpec(env)`, `Container.getDeploymentSpec(ctx, fn, nil, name, ns, labels, nil)`, `environmentWatcher{...}.createBuilderDeployment`, and the webhook `Logger`/`Validator` fields. A fix that changes any of those signatures or fields breaks compilation of the whole package, which takes the functional group with it and gives reward 0. A minimal fix would not do that, but a refactoring fix (for example threading a validator through `genDeploymentSpec`) could. **Risk: low–medium.** Nothing to change. Note it in the trial review if a trial fails at compile time.

## 2. Leniency (wrong fixes vs. tests)

| Property / trap | Most plausible wrong fix | Caught by | Check patch |
|---|---|---|---|
| Env runtime podspec at admission only (the j_tempting fix) | checks only `Runtime.PodSpec` | TestSecZZEnvBuilderPodSpec, TestSecZZFunctionPodSpec, the Stored* tests | env_runtime_only.patch |
| T1 Function podspec | skips Function | TestSecZZFunctionPodSpec | no_function.patch |
| T2 merge/stored route | admission only | Pool/Builder/ContainerExecutor Stored* | admission_only.patch |
| T3 container overrides | podspecs only (the published fix) | TestSecZZEnv{Runtime,Builder}ContainerPrivileges, PoolStoredRuntimeContainer, BuilderStoredBuilderContainer | published_fix_only.patch |
| UPDATE verb | marker or chart left CREATE-only | installed_webhook_receives_updates | no_update.patch (it touches neither marker nor chart, and only the chart test catches it) |
| Update validates the wrong object | validates `oldObj` | update_is_validated, zzSecFnRejected (update leg) | validate_old_on_update.patch |
| SA alias | checks `serviceAccountName` only | TestSecZZEnvRuntimePodSpecServiceAccount/serviceAccount, ContainerExecutorStored…/serviceAccount | no_deprecated_sa.patch |
| Crash as refusal | panics in the merge | Stored* (a panic fails the test) | crash_on_unsafe.patch |
| Over-hardening | drops pod SC; refuses every capability added; refuses all customisation | the Func tests | drop_pod_security_context, refuse_added_capabilities, refuse_all |

**Wrong fixes that no test catches:**

1. **`capabilities.add: ["ALL"]` (HIGH).** It grants every capability, SYS_ADMIN included, so the instruction plainly covers it ("add a Linux capability that grants administrative … power"). No test uses it, and **the oracle `fix.patch` itself admits it and passes it through the merge**: its denylist lacks `ALL`. `hardening.patch` adds `ALL`, which shows the builder knew about the gap. As things stand, the reference solution does not meet its own instruction.
2. **Non-canonical spellings: `sys_admin`, `CAP_SYS_ADMIN`, `all` (MEDIUM).** The CRI runtime (containerd) uppercases capability names and adds the `CAP_` prefix, so on such clusters these names take effect. The oracle's lookup is exact-match and case-sensitive. The test detectors normalise spelling, but no test feeds in such a name.
3. **A denylist of `{SYS_ADMIN}` only (MEDIUM).** The instruction names NET_ADMIN, SYS_PTRACE and SYS_MODULE, but every test uses SYS_ADMIN. A one-entry denylist passes.
4. **newdeploy executor route (MEDIUM).** newdeploy builds pods from the stored Environment through the same merge (manifest T3 cites newdeploy.go:185). No Stored* test drives newdeploy. A controller-local fix that sanitises in poolmgr, buildermgr and the container executor but not in the shared merge passes, and leaves newdeploy pods open for stored objects.
5. **Minor gaps (LOW).** Function admission does not test hostIPC, `serviceAccount` alias, initContainers or allowPrivilegeEscalation. The builder tests do not cover hostIPC, nor allowPrivilegeEscalation on the builder override. A separately written Function or builder validator could miss these.
6. **Out of scope (not required).** hostPort, `procMount: Unmasked`, Windows hostProcess, ephemeral containers. The instruction does not list them, so not testing them is consistent.

## 3. Hints in instruction.md

The instruction names no file, function or field path, and contains none of the manifest leak_terms. It does give a behavioural cue for nearly every trap. Most of these cues are needed to make the tests fair; two could be softened.

| Quote | Paraphrases | Proposal |
|---|---|---|
| "through any field that selects one" | the deprecated SA alias trap | Optional: "run under a service account other than the one the platform assigns." The behaviour is the same and less pointed, and the alias stays fair as expert knowledge. |
| "Objects that are already stored in the cluster, such as objects created before an upgrade or while admission was unavailable" | T2 (merge/controller route) | Keep. Without it the Stored* tests would be unfair. |
| "The platform may decline to deploy them, or deploy them without the forbidden settings, but no component may crash." | the crash_on_unsafe trap, and it allows both designs | Keep (fairness). |
| "This covers every part of these objects that shapes the resulting pods" | T3 (container overrides) | Keep. It is generic and needed. |
| "both when an object is created and on any later update or patch" | the UPDATE flaw | Keep. |
| "including their pod-level security context" | drop_pod_security_context trap | Keep. It is a must-keep-working requirement. |
| "Adding capabilities from the container runtime's default set, such as NET_BIND_SERVICE or CHOWN" | refuse_added_capabilities trap | Keep. |

No flaw count and no variant list (the line "The examples above are illustrations, not the full set" is fine).

## 4. Realism

- T1, T2 and T3 are real upstream code at the pinned commit (T3 was fixed upstream later). All are reached through the real entry points: the admission validators via ValidateCreate/ValidateUpdate, and the controllers' deployment builders. Nothing looks planted.
- The chart-text UPDATE test is the only non-behavioural assertion. The chart is the artefact that actually registers the webhook, so the test is realistic, but it is brittle (see the medium row in §1).

## 5. Verdict: **NOT READY**

Required:
1. **Oracle and tests for `ALL`:** add `"ALL"` to both denylists in `solution/fix.patch`, with case and `CAP_` normalisation (as hardening.patch already does). Then add `ALL` subtests: at admission (Env runtime podspec, Env runtime container, Function) and stored (poolmgr, and container or buildermgr). Re-run the gate; hardening.patch and alt_refuse_allowlist.patch should still pass (the allowlist rejects ALL).
2. **Tighten capability coverage:** add at least one non-SYS_ADMIN capability from the instruction's list (for example `SYS_PTRACE` or `NET_ADMIN`) at admission and stored, plus one lowercase or `CAP_`-prefixed spelling such as `cap_sys_admin`. The oracle must then normalise (see 1).
3. **newdeploy route:** add a stored-Environment security test for the newdeploy executor (runtime podspec hostNetwork plus runtime container privileged), with a coupled functional test. Alternatively, record in the manifest why that route is out of scope.

Recommended:
4. Make `installed_webhook_receives_updates` also accept a fix where the marker and every committed webhook manifest agree, or confirm that the chart is the only committed registration. Keep the test either way.
5. Optionally soften "through any field that selects one" (§3).
