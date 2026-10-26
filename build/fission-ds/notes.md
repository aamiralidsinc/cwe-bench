# fission-ds: build notes (build-v1, injected track)

Start: 2026-10-18T19:33:36Z. End: see the bottom of this file.

## Advisory and pin
- Advisory GHSA-gx55-f84r-v3r7 / CVE-2026-50564 / GO-2026-5855, fission/fission.
- Pinned (vulnerable) commit: 8fa799417c77ce8a0189d9858bfe11ece29b84a6, the parent of the published fix e484df8460bb4e8026e24210120602aa7f181f64 (verified with `git log`; the fix's regression tests are absent at the pin).
- Product: a Kubernetes serverless framework. Tenants write Environment and Function objects; the platform's executor and buildermgr controllers build Deployments for them under platform service accounts.

## Levers (one line each)

Pattern A, published far sites:
- T1 (A, second CRD): admission of the container-executor Function pod spec, `pkg/apis/core/v1/validation.go:296` (published fix site). Reason to dismiss: the report leads with Environments; Functions are another object and another executor.
- T2 (A, lower-level merge/defaults route): controllers build pods from objects already stored in the cluster through the shared pod-spec merge, `pkg/executor/util/merge.go:58-199` (published fix site). Reason to dismiss: admission refuses those fields now, and the same helper carries the operator's trusted install-time patch.

Pattern B, real unmodified upstream:
- T3 (B, uncovered): the Environment runtime and builder single-container override fields, merged by `pkg/executor/util/merge.go:35-55` at `poolmgr/gp_deployment.go:111`, `newdeploy/newdeploy.go:185`, `buildermgr/envwatcher.go:418`; no admission check at `validation.go:655`. Reason to dismiss: a convenience container override, not a pod spec.

Injected siblings (this track):
- S1: a Function-level `sidecars` list appended to the container-executor pod after the pod-spec merge (`container/deployment.go`). Reason to dismiss: extra containers are not pod-level settings, and the platform already adds its own fetcher container.
- S2: an Environment runtime `podSpecPatch` (a YAML/JSON strategic merge patch string) applied after the typed pod spec in `poolmgr/gp_deployment.go` and `newdeploy/newdeploy.go`. Reason to dismiss: it mirrors the operator's install-time pod-spec patch and is a serialized value, not a typed pod field.
- S3: a compatibility exemption keyed by an object annotation in `pkg/webhook` (Environment and Function admission). Reason to dismiss: the annotation reads as operator-set compatibility metadata, not as tenant input.

Also tested (published sites, not counted as levers): builder pod spec at admission; the Environment webhook's UPDATE registration (kubebuilder marker + Helm chart); the deprecated service-account alias; capability spellings (ALL, lowercase, CAP_ prefix).

## Coupled must-keep-working (functional)
- Ordinary pod customisation reaches the pods: resources, env, extra unprivileged containers and init containers, ConfigMap/Secret/emptyDir volumes, nodeSelector, tolerations, affinity.
- Tenant hardening: pod/container securityContext (runAsNonRoot, runAsUser, fsGroup, seccomp, read-only root fs), drop ALL, explicit privileged/allowPrivilegeEscalation=false, benign added capabilities NET_BIND_SERVICE and CHOWN.
- Operator install-time pod-spec patch (pod-level securityContext, scheduling) still propagates.
- A legitimate serialized runtime override (nodeSelector, tolerations, resources, runtimeClass, explicit false values) still applies.
- Ordinary labels/annotations do not block acceptance; objects with the compatibility annotation and a benign pod spec are still accepted.
- The project's own tests for the affected packages pass unchanged.

## Security input shapes the tests cover
- pod-level hostNetwork / hostPID / hostIPC
- serviceAccountName and the deprecated serviceAccount alias
- hostPath volumes anywhere in the volume list
- containers[] and initContainers[] separately
- privileged and allowPrivilegeEscalation pointer bools
- capabilities.add mixing benign and administrative entries, including ALL and non-canonical spellings
- runtime pod spec, builder pod spec, Function pod spec, runtime/builder container overrides, Function sidecars, runtime serialized patch
- annotated objects; create and update

## Injection mechanics (one line each)
- S1 adds `FunctionSpec.Sidecars` and appends it in the container executor after the merge.
- S2 adds `Runtime.PodSpecPatch` and a strategic-merge helper, applied after the typed pod spec in the two runtime sinks.
- S3 adds a grandfathering annotation check in the Environment and Function admission entry points.
- The injection is applied by the image build; the applied source keeps no marker of the task.

## Verification plan / results
- The injected pinned tree: every security testcase fails by assertion, every functional testcase passes.
- Oracle = the published source changes plus fixes for T3, S1, S2, S3, the UPDATE registration and the annotation exemption.
- Wrong-fix patches: one per lever, three over-broad/feature-removing functional failures, a hardening pass, an alternative pass.
- Gate static / nop / oracle / patches, one at a time (results appended below).

## Out of scope (one line)
- MessageQueueTrigger has its own pod-spec allowlist from a different advisory; not examined or built on.

## Not verified / judgement calls
- The generated CRD schemas (`crds/v1/*.yaml`) were not regenerated for the two injected fields; the project's own tests and the hidden tests drive the Go types directly, as the project's tests do. A real release would regenerate them.
- No cluster or real admission round-trip was run; the webhook is driven through its Go validator (ValidateCreate/ValidateUpdate), as the project's own tests do.
- The UPDATE registration test reads the Helm chart text (the only production registration). A fix that changes only the kubebuilder marker fails it. I judge this fair: the installed webhook is what gates updates, and the instruction says updates and patches are covered.
- Capability policy in the oracle is a denylist with ALL and case/CAP_ normalisation; the tests use SYS_ADMIN, NET_ADMIN, SYS_PTRACE, SYS_MODULE, ALL and spellings, and benign NET_BIND_SERVICE/CHOWN. An allowlist design also passes.
- Hidden tests call unexported controller methods and struct fields, as the project's own tests do; a fix that changes those signatures would fail to compile. Noted as in the prior task.

## Gate
(filled in at the end)

## Upgrade 2026-10-20 (BETTER-PATTERNS §2–§8)
- Instruction only. The old report named both object kinds, listed the far sites' mechanisms
  (extra containers, serialized override, updates/patches), told the solver metadata could not
  exempt an object, and required stored objects to be handled. The new report states the property
  once over the protected pod outcome ("no value a tenant supplies ... may cause any pod ... to
  share/schedule/mount/run as ..."), with the refusal and already-stored contracts and the
  preservation clauses in general terms. No route, object kind, stage, format, file, function or
  count is named.
- Levers unchanged: T1 (far site, second object kind — where-type), T2 (merge/defaults producer
  the admission check never calls — how-type), T3 (real upstream route where protection never
  existed — how-type), S1 (injected extra container list), S2 (serialized pod override — parser/
  shape differential, how-type), S3 (metadata exemption). At least three levers are how-type, so
  no new lever and no repo-code change.
- Coverage unchanged and complete for the stated property: admission create/update (both kinds),
  the installed update registration, the metadata exemption, and the stored-object paths through
  poolmgr, newdeploy, the container executor and buildermgr, each with the corresponding
  functional control. No test, oracle or check patch was changed.
- Static leak scan passes (only the separately-wired blind patch and FAIRNESS.md remain).
- The prebuilt image was not rebuilt. The Dockerfile was re-built from the layer cache to confirm
  it still yields the injected tree (the 2026-10-20 05:17 nop stress run reported missing injected
  fields; that run was one of 20 concurrent compose builds and the rebuilt image contains them, so
  it is an environment/cache flake, not task drift).

## Hardening 2026-10-21 (harden-v1, Frontier 1.4)

Both target models solved the previous version (each fixed all six traps). Two new fair levers were
added, one aimed at each model's documented miss, and the task was converted to the Frontier
delivery format.

- N1 (producer off the admission check's path, MiMo-type): a namespace-scoped pod-spec overlay is
  read from the tenant-writable `fission-pod-overrides` ConfigMap and strategic-merged into the
  runtime and builder pods after the typed merge, in the pool, new-deploy and builder controllers
  (`pkg/executor/util/pod_overrides.go`). Reason to dismiss: a ConfigMap is ordinary stored data,
  not pod configuration; the typed Environment fields are what the checks look at.
- N2 (route where the protection never existed, legacy path; DeepSeek-type): version-1
  Environments restore their pod-spec settings (host namespaces, service account, hostPath volumes,
  container security context) after the shared merge has sanitised them
  (`pkg/executor/util/podspec_legacy.go`). Reason to dismiss: version-1 objects are a legacy
  compatibility path, not the current merge the report describes.

Both are closed by the reference fix: the overlay is validated before it is merged, and the legacy
restoration copies only values scrubbed by the shared sanitiser. The check patches
`no_namespace_overrides.patch` and `no_legacy_restore.patch` leave each lever open on their own.

Tests: a security test and a coupled functional test per lever at every sink it reaches (pool,
new-deploy, builder). The coupled tests keep benign overlays and version-1 customisation working
(node selectors, tolerations, runtime class, benign added capabilities, explicit
`privileged: false`, non-host volumes), so an over-broad fix fails.

Delivery: schema 1.4, /workspace, separate offline verifier built from tests/Dockerfile, uid-1000
agent, artifacts restore, dual scoring, fresh canary GUID. `conformance_check.py` prints conforming.
Local verification (host Go 1.26.3 toolchain): nop fails every security test and passes every
functional test; the oracle passes both; every check patch behaves as declared. Gate nop/oracle/patches were then
run via Harbor (see gate_verdict.json).

Remaining static item: the externally-wired `blind` pass patch (and FAIRNESS.md) are produced after
the builder, per the build brief; the manifest was not weakened to hide this.

## Gate results (Harbor, separate mode + non-root verifier)

- nop: PASSED. 202 security test cases all fail on the injected pinned tree; 131 functional cases pass.
- oracle: PASSED, 3/3 runs reward 1.0 with identical results.
- patches: PASSED. All 18 check patches behave as declared: 13 security_fail, 3 functional_fail,
  hardening and alt_refuse_at_sinks pass; the two new patches (no_namespace_overrides, no_legacy_restore)
  each leave only their lever open.
- static: every agent-owned check passes (conformance prints conforming, no leaks, catalogue complete,
  all patch files present). The single remaining failure is the `blind` pass patch, which the build
  brief assigns to a separate post-builder stage; it was not fabricated here and strict_gate was not
  weakened.
