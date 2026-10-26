# fission-podspec-passthrough: build notes (build-v1)

Start: 2026-10-17T03:41:01Z. End: see the bottom of this file.

## Levers (one line each)
- T1 (A, far site on a second CRD): admission of the container-executor Function pod spec, `pkg/apis/core/v1/validation.go:296`. Reason to dismiss: "the report is about Environments".
- T2 (A, merge/defaults route): controllers build pods from already-stored objects through the shared pod-spec merge, `pkg/executor/util/merge.go:83,145-167`. Reason to dismiss: "admission already refuses these fields, and operator patches share this code".
- T3 (B, uncovered, 2 routes): the runtime and builder single-container overrides reach the same pods. Nothing checks them at admission (`validation.go:655`), and the container merge (`merge.go:35-55`) carries them. The published fix did not touch them. Reason to dismiss: "it is a convenience container field, not a pod spec".
- Also tested (published sites, not counted as levers): builder pod spec, UPDATE registration in the chart, the deprecated service-account alias.
- Coupled must-keep-working: pod-level securityContext from the operator patch and from the tenant; benign added capabilities (NET_BIND_SERVICE, CHOWN); explicit privileged/allowPrivilegeEscalation set to false; volumes, node selection, resources, env.

## Verified
- The pinned commit 8fa79941 is the parent of fix e484df84. The fix's regression tests are absent at the pinned commit.
- The project's tests for the area pass offline in the image at the pinned commit.
- Nop (local and gate): all 65 security testcases fail by assertion, and all 116 functional testcases pass.
- Both T3 routes were confirmed open on the pinned code, and also with the published fix applied (`published_fix_only.patch`: 10 subtests fail).
- Oracle = published source changes, plus a container-level validator for the two override fields, plus sanitising in the container merge. Locally it scored 1.0 in 39 s on 2 CPUs.
- Every check patch behaved as declared, both locally and in the gate (see below).
- Current upstream (read-only `git show origin/HEAD`) closes T3 in the merge (GHSA-m63v-2g9w-2w6v), so present_in_latest = no.
- The deprecated service-account alias is asserted only where it actually takes effect: at admission, and in the container executor, which sets no service account. In pool and builder pods `serviceAccountName` wins, so those tests check the effective account.

## Not verified / judgement calls
- The UPDATE test reads the Helm chart's webhook registration as text. A fix that changes only the kubebuilder marker fails it. I judge this fair: every other Fission webhook in the chart lists UPDATE, and the instruction says "on any later update".
- The dangerous-capability set: the tests use only SYS_ADMIN (refused) and NET_BIND_SERVICE/CHOWN (kept). DAC_OVERRIDE etc. are not tested, so both allowlist and denylist designs pass.
- No cluster or real admission round-trip was run. The webhook is driven through its Go validator (ValidateCreate/ValidateUpdate), as the project's own tests do.
- Recall risk: upstream fix comments name the GHSAs; the image has no git history.

## Out of scope (one line)
- Upstream later moved to a capability allowlist with forced drop:[ALL] (GHSA-qf5v). MessageQueueTrigger pod specs use their own allowlist. Neither was examined further.

## Gate
- static: passes except the two items written by others (blind patch, FAIRNESS.md).
- nop: PASSED (65 security testcases all fail, 116 functional all pass).
- oracle: PASSED (3 identical runs, reward 1.0).
- patches: PASSED (all 13 behave as declared).

End: 2026-10-17T04:29:08Z.

## Fairness revision (2026-10-17)
- Oracle: capability denylist gains `ALL`; names are upper-cased and stripped of `CAP_` before lookup (one shared helper used by admission and the container merge). The previous oracle is kept as `checks/cap_exact_match.patch` (expect security_fail).
- Tests: `TestSecZZEnvAddedCapabilityVariants` (ALL, NET_ADMIN, SYS_PTRACE, SYS_MODULE, `cap_sys_admin`, `all`) at admission on the runtime pod spec, runtime/builder containers and builder pod spec; the same variants on Function; stored ALL/SYS_PTRACE/NET_ADMIN/SYS_MODULE/lowercase/CAP_-prefixed cases in poolmgr, container, buildermgr. Stored-object detectors now flag SYS_ADMIN, NET_ADMIN, SYS_PTRACE, SYS_MODULE and ALL in any spelling.
- newdeploy route: `TestSecZZNewDeployStoredRuntimePodSpec` / `...StoredRuntimeContainer` with coupled `TestFuncZZNewDeployTenantCustomisation` / `...OperatorPatch`.
- Minor gaps closed: Function hostIPC, `serviceAccount` alias, init-container allowPrivilegeEscalation; builder pod spec hostIPC; builder container allowPrivilegeEscalation.
- Chart UPDATE test kept: the chart is the only production registration (Makefile `generate-webhooks` says marker changes are ported there); `test/e2e/framework/webhook-manifest.yaml` is an envtest fixture.
- Instruction: the service-account bullet no longer hints at "any field that selects one".
