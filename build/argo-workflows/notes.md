# argo-workflows (stacking) build notes

## Commit C
`4cac12c75de720889ad2cae8a6cc63c566b1d8d8` on `origin/release-4.0` (module
`github.com/argoproj/argo-workflows/v4`, Go 1.25). Chosen as the parent of the
release-4.0 fix for CVE-2026-28229, which keeps that authorization bug open while
every other target advisory is still open too.

## Co-present vulns verified OPEN at C (5)
1. CVE-2026-28229 (CWE-200/863) — WorkflowTemplate/ClusterWorkflowTemplate `Get`
   has no access review. Verified: no `CanI` call in either server's Get at C.
2. CVE-2026-42297 (CWE-862/863) — configmap sync-limit CRUD has no access review.
   Verified: no permission check in the configmap provider at C.
3. CVE-2026-42295 (CWE-522) — artifact logging wrapper logs the whole driver
   struct (credentials). Verified: 6 `WithField("driver", ...)` call sites at C.
4. CVE-2026-42294 (CWE-770) — webhook interceptor reads the whole body unbounded.
   Verified: `io.ReadAll(r.Body)` with no limit at C.
5. CVE-2026-42296 (CWE-863) — templateReferencing restriction only blocks
   podSpecPatch; hostNetwork/securityContext/serviceAccountName overrides pass.
   Verified: only the podSpecPatch check present at C.

Each was reproduced on the vulnerable checkout: all 16 security tests FAIL at C and
PASS after the fix; all 9 functional tests PASS at C and after the fix.

## Dropped
- CVE-2026-31892 (podSpecPatch bypass): already fixed at C.
- CVE-2026-54526 (ArtifactGC.PodSpecPatch): introduced after C.
- CVE-2026-40886 (pod-informer crash): controller informer path, no mined fix.
- CVE-2026-42183 (gatekeeper SSO nil-deref): co-present but needs elaborate SSO
  delegation setup; dropped to keep the set clean (LOW severity).

## Offline strategy
No live Kubernetes cluster. The verifier injects Go test files into the affected
packages and drives the gRPC/HTTP handlers and library APIs directly against
`k8s.io/client-go/kubernetes/fake` clients (and the project's own
`newController`/`operate` harness), exactly as argo's server/controller unit tests
do. The module and build caches are baked into the image; no test touches the
network.

## Build cost
Heaviest build in the batch. Image `golang:1.25-bookworm` + full `go mod download`
+ compile of server/controller packages. Final image ~2.46 GB. First build
(cold module+build cache) ~15 min wall under the loaded host; subsequent verifier
runs recompile only changed packages. `go build -p 2` used to cap compiler memory.

## Fixes
`solution/fix.patch` = upstream release-4.0 source fixes for the 5 advisories,
source-only, 8 files. `alt_correct_fix.patch` relocates the sync-limit access
check from the configmap provider to the gRPC dispatch layer (a valid alternative).

## 2026-10-16 test repair
Brief: `build/audit/REPAIR-BRIEF-2026-10-16.md`. Items from `build/audit/lenient_items_2026-10-16.txt`,
`research/own-runs/TEST-REPAIRS.md` and our notes (per verb and namespace, like real RBAC).

| # | Item (source run) | Decision |
|---|---|---|
| 1 | Sync SSAR fake answers the same for every resource (deepseek r1, deepseek r11, mimo r11) | already fixed (earlier today: only `configmaps` is denied). Proof patch added: `sync_wrong_resource_fix` |
| 2 | Template Get SSAR fakes answer the same for every resource (deepseek r1, mimo r11) | already fixed (earlier today: only `workflowtemplates` / `clusterworkflowtemplates` denied). Proof patch added: `template_wrong_resource_fix` |
| 3 | Our note: answer per verb and namespace too | fix. Sync: the server's namespace is now `argo` (all granted), the target `victim-ns` grants everything except ConfigMaps, where only the listed verbs are granted; no cluster-wide ConfigMap rights. Get is tested with no ConfigMap rights; Create/Update/Delete with a READ-ONLY caller (get/list/watch), so any write verb (create/update/patch/delete) passes but a read-verb check fails. Templates: only read verbs (get/list/watch/*) on the resource in the template's namespace (cluster scope for the cluster template) follow `allowed`; a namespaced review of the cluster-scoped template is granted (a wildcard Role somewhere grants it in real RBAC); a cluster-wide review of the namespaced template is denied |
| 4 | Exact `codes.PermissionDenied` in sync and template security tests (§3g) | fix (relaxed): any error refuses, plus no data in the response (Get) or no side effect in the fake cluster (Create: no ConfigMap; Update/Delete: limit still 5) |
| 5 | Ref-mode tests probe only the 3 named fields; denylists pass (deepseek r11, deepseek r12 REC) | fix. New `TestSecZZRefModeRejectsTemplateDefaultsSecurityContext`: `spec.templateDefaults.securityContext.runAsUser=0`. Fair: the instruction's property is "a submitter can still set ... a pod security context ... and those values take effect"; on the vulnerable code this route was verified to reach the pod (the created pod ran as UID 0 with the submitter's service account). Both r12 fixes (written blind) already reject templateDefaults overrides. Not added: probes for `templates` / `podMetadata` (not "pod-level protections" the instruction names; would need an instruction change, so skipped) |
| 6 | New functional `TestFuncZZSyncAuthorisedUpdateDelete` (authorised update then delete of a limit) | added; protects "an authorized caller must still be able to manage limits normally" |
| - | REC: add changes.patch to postmortem bundles; mimo r12 chunked webhook variant | skip (tooling / optional, not a test gap) |

No instruction change. Counts: 17 security, 10 functional.

New patch checks (all checked in a scratch container first, then by the gate):
- `sync_wrong_resource_fix` (security_fail): sync checks `workflows` → 4 sync security tests fail.
- `template_wrong_resource_fix` (security_fail): template checks `workflows` → both template Get tests fail.
- `sync_read_verb_fix` (security_fail): every sync op checks only `get` → Create/Update/Delete fail.
- `sync_wrong_namespace_fix` (security_fail): alt layer, checks the server's own namespace → 4 sync tests fail.
- `sync_cluster_scope_fix` (functional_fail): checks namespace "" → the 3 sync functional tests fail.
- `refmode_denylist_fix` (security_fail): denylist of the spec's own pod fields, no templateDefaults → the new test fails.

Pass patches before the gate (scratch, 27/27): reference, `alt_correct_fix`, `larger_cap_fix`, and the
final code of deepseek r12 (X2oZisd) and mimo r12 (r9KDmMg).

Gate: **PASSED** (`gate-20261016f.log`, slot cap 2). Runs d/e were infra failures, not test results:
d had a full Docker disk ("no space left on device" building chk-larger_cap_fix), e was stopped by
the coordinator for the slot cap. Gate f: nop 0.0 (all 17 security fail, functional pass); oracle
1.0 twice; subset 0.7647; disable_feature 0.0; alt_correct 1.0; larger_cap 1.0;
sync_wrong_resource 0.7647; template_wrong_resource 0.8824; sync_read_verb 0.8235;
sync_wrong_namespace 0.7647; sync_cluster_scope 0.0 (functional); refmode_denylist 0.9412.
Still warned (pre-2026-10-16 task): no `hardening` or `blind` pass patch.

Regrade (all 4 trials with final-code/changes.patch; also the ones below 1.0, because the
exact-status checks were relaxed). Log: `regrade-repair-20261016.log`.

| trial | old | new | failing tests |
|---|---|---|---|
| deepseek r12 X2oZisd | 1.0 (verifier) | 1.0 | none |
| mimo r12 r9KDmMg | 1.0 (verifier) | 1.0 | none |
| deepseek r11 QprUNQg | 0.75 (regrade 011009Z) | 0.7059 | 4 sync tests (checks `workflows`, not ConfigMaps; unchanged) + TemplateDefaultsSecurityContext |
| mimo r11 b5WYen5 | 0.75 (regrade 011140Z) | 0.7059 | 4 sync tests (same, unchanged) + TemplateDefaultsSecurityContext |

No run dropped from 1.0. The new failure in both r11 runs is a real defect: their ref-mode checks
are denylists of the spec's own top-level fields (deepseek: 16 fields in `PodLevelFields()`;
mimo: 10 in `HasPodLevelOverrides()`) and never look at `spec.templateDefaults`, and neither touches
the spec merge. So `templateDefaults.securityContext` / `serviceAccountName` still reach the pod,
as verified on the vulnerable code. Not regradable (no final-code/changes.patch): deepseek r1
oovj8GZ (1.0), mimo r1 VSELT69 (0.9375), mimo r2 kEzV7rB (1.0).
