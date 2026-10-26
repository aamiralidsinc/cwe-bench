# Fairness review — stk-kyverno-ghsacvq5 (revision 2026-10-24, post-run audit)

Source of the required changes: `build/stk-kyverno-ghsacvq5/AUDIT-FIX-20261024.md` (attribution:
instruction-ambiguity). The audit found a contradiction: the instruction forbids a namespaced policy
reading cluster-scoped data, while a coupled functional test required it to read the cluster-scoped
Namespace object. Per the project rule of 2026-10-20 the instruction is kept and the test and
reference change. `TestFunc_NamespacedPolicyOwnNamespaceRecord` is replaced by
`TestFunc_NamespacedPolicyOwnNamespaceResource` (a namespaced resource in the policy's own
namespace); `TestSec_APICallOwnNamespaceObject` requires the Namespace object itself to be refused;
the reference refuses it; and the pre-change reference is kept as
`checks/upstream_namespace_object.patch` (`security_fail`). `instruction.md` is unchanged (audit
item 5), so the listing check result (PASS, all four traps GENERAL) stands.

## Tests and their covering instruction

| test | asserts | covering sentence | correct fix could fail? | risk |
|---|---|---|---|---|
| `security/zz_sec_apicall_test.go::TestSec_APICallCrossNamespace` | another namespace's Secret is refused, no request | "No policy that belongs to a namespace may read, or otherwise affect, data that belongs to another namespace…" | no | low |
| `…::TestSec_APICallDotSegment` | the same read via `..` segments refused | same; normalization is standard (CWE-22) | no | low |
| `…::TestSec_APICallNamespacePrefixCollision` | a namespace whose name starts with the policy's name refused | same ("another namespace") | no | low |
| `…::TestSec_APICallClusterWideList` | an all-namespace list path refused | same ("…or that is cluster-scoped") | no | low |
| `…::TestSec_APICallOwnNamespaceObject` | GET of `/api/v1/namespaces/team-a` (the Namespace object) refused, no request | same: the Namespace object is cluster-scoped; any refusal is accepted, no data returned ("A refusal is a client error and has no effect.") | no — error return, no request; no status asserted | low |
| `…::TestSec_APICallSubstitutedNamespace` | a path resolving through a variable to another namespace refused | same sentence; the guard must run after substitution | no | low |
| `…::TestSec_APICallWriteCrossNamespace` | a cross-namespace POST refused and reaches nothing | "…or otherwise affect…" + no-effect refusal | no | low |
| `security/zz_sec_configmap_test.go::TestSec_ConfigMapCrossNamespace` | a ConfigMap outside the policy namespace is refused and never resolved | same data property (the example's "an object") | no | low |
| `…::TestSec_ConfigMapEmptySubstitutedNamespace` | an empty resolved target never resolves outside the policy namespace | same property; empty must mean the policy's namespace | no | low |
| `security/zz_sec_service_test.go::TestSec_ServiceCallDoesNotUseKyvernoCredential` | Kyverno's own token is not sent on a namespaced policy's outbound call (refusal also fine) | "Kyverno's own cluster identity must never be used on behalf of a policy that belongs to a namespace…" | no — refusal or unauthenticated call both pass | low |
| `security/zz_sec_cleanup_test.go::TestSec_CleanupContextCrossNamespace` | a namespaced cleanup policy's context never resolves outside its namespace | same data property ("no policy that belongs to a namespace") | no | low |
| `functional/zz_func_context_test.go::TestFunc_NamespacedPolicyOwnNamespaceAPICall` | own-namespace ConfigMap list still fetched | "Everything that works today keeps working."; the rule forbids only other-namespace or cluster-scoped data | no | low |
| `…::TestFunc_NamespacedPolicyOwnNamespaceResource` | own-namespace Deployment still fetched (replaces the Namespace-object read) | same general keep-working sentence; a namespaced resource in the policy's namespace is not forbidden | no | low |
| `…::TestFunc_NamespacedPolicySubstitutedOwnNamespaceAPICall` | a target resolving to the policy's own namespace still works | keep-working | no | low |
| `…::TestFunc_ClusterPolicyUnrestrictedAPICall` | a ClusterPolicy keeps unrestricted reads | keep-working; the rule applies only to policies "that belong to a namespace" | no | low |
| `…::TestFunc_NamespacedPolicyOwnNamespaceConfigMap` | own-namespace ConfigMap still resolved | keep-working | no | low |
| `…::TestFunc_ClusterPolicyDefaultNamespaceConfigMap` | a ClusterPolicy's empty namespace still means `default` | keep-working | no | low |
| `…::TestFunc_ClusterPolicyCrossNamespaceConfigMap` | a ClusterPolicy keeps unrestricted ConfigMap access | keep-working; not namespaced | no | low |
| `…::TestFunc_NamespacedPolicyExternalCallStillWorks` | a namespaced policy's external HTTP call still works and stores its result | keep-working; the identity rule forbids lending Kyverno's identity, not calling an external service | no | low |
| `…::TestFunc_NamespacedPolicySuppliedCredentialPreserved` | the policy's own Authorization header is preserved | keep-working; no rule forbids using the policy's own credential | no | low |
| `…::TestFunc_ClusterPolicyServiceUsesKyvernoCredential` | a ClusterPolicy still uses Kyverno's identity | keep-working; the rule scopes to namespaced policies | no | low |
| `functional/zz_func_cleanup_test.go::TestFunc_CleanupNamespacedPolicyOwnNamespace` | a namespaced cleanup policy resolves context in its own namespace | keep-working | no | low |
| `…::TestFunc_CleanupClusterPolicyCrossNamespace` | a ClusterCleanupPolicy keeps unrestricted context access | keep-working; not namespaced | no | low |
| project tests (`apicall`, `context/loaders`, `factories`, two deterministic cleanup tests) | existing behaviour unchanged | keep-working | no | low |

## Leniency (QUALITY)

| wrong fix | caught by |
|---|---|
| refuse every namespaced-policy call | `functional_overbroad.patch` → `functional_fail` |
| guard only the literal reported path / no normalization | `malformed_identity.patch` → `security_fail` |
| guard only reads, not writes | `reads_only.patch` → `security_fail` |
| check before variable substitution | `check_before_substitution.patch` → `functional_fail` |
| refuse every nil-policy loader (breaks cleanup) | `adjacent_api.patch` → `functional_fail` |
| published-fix equivalent that still allows the cluster-scoped Namespace object | `upstream_namespace_object.patch` → `security_fail` (only the object test fails; all functional pass) |
| the published first fix (A alone) | `upstream_first_fix.patch` → 5 security fails |
| the complete published fix (A+B) | `upstream_fix.patch` → 3 security fails |
| miss one concept | `miss_concept_{apicall,service,configmap,cleanup}.patch` → that concept's security tests only |

## Hints (QUALITY)

No file, function, mechanism, trap, variant list or count is named. The one literal case in the
example is the advisory's own reported trigger and is explicitly called an example. The two
identity/data sentences state the protected outcome.

**Required: generalize** — none. The audit requires no instruction change (item 5) and none was made.

## Realism (QUALITY)

T1 and T3 are the published fix's sites (GHSA-8p9x-46gm-qfx2, GHSA-cvq5-hhx3-f99p). T2 and T8 are
real, unmodified upstream routes that both published fixes left open; leaving them open is a solver
judgement, not an out-of-scope finding. Nothing is planted.

## Stacking checks

Concepts: **T1** (apiCall URLPath confinement), **T2** (service-call credential lending),
**T3** (typed ConfigMap loader), **T8** (cleanup-controller null-policy wiring).

### S1 — Coupled traps

| functional value | concept | covering clause | security rule that could forbid it |
|---|---|---|---|
| `TestFunc_NamespacedPolicyOwnNamespaceAPICall` | T1 | "Everything that works today keeps working." | none: a ConfigMap list in the policy's own namespace is neither another namespace's data nor cluster-scoped |
| `TestFunc_NamespacedPolicyOwnNamespaceResource` | T1 | keep-working | none: a Deployment in the policy's own namespace is a namespaced resource |
| `TestFunc_NamespacedPolicySubstitutedOwnNamespaceAPICall` | T1 | keep-working | none: the value resolves inside the namespace |
| `TestFunc_ClusterPolicyUnrestrictedAPICall` | T1 | keep-working | none: a ClusterPolicy does not belong to a namespace |
| `TestFunc_NamespacedPolicyExternalCallStillWorks`, `TestFunc_NamespacedPolicySuppliedCredentialPreserved` | T2 | keep-working | none: Kyverno's own identity is not used |
| `TestFunc_ClusterPolicyServiceUsesKyvernoCredential` | T2 | keep-working | none: not namespaced |
| `TestFunc_NamespacedPolicyOwnNamespaceConfigMap`, `TestFunc_ClusterPolicyDefaultNamespaceConfigMap`, `TestFunc_ClusterPolicyCrossNamespaceConfigMap` | T3 | keep-working | none: own namespace, or a policy that does not belong to a namespace |
| `TestFunc_CleanupNamespacedPolicyOwnNamespace` | T8 | keep-working | none: own namespace |
| `TestFunc_CleanupClusterPolicyCrossNamespace` | T8 | keep-working | none: not namespaced |

Result: no contradiction in any concept. The only contradiction in v2 — the Namespace object held as
a keep-working value while the rule forbids cluster-scoped data — is removed by the test change, not
by adding a clause that names the value.

### S2 — Shape traps

| concept | refused shape | outside the legitimate set because |
|---|---|---|
| T1 | another namespace; `..`-normalized escape; a name sharing the policy-namespace prefix; an all-namespace list; the cluster-scoped Namespace object; a substituted other namespace; a cross-namespace write | legitimate shapes are namespaced resources **inside** the policy's own namespace, or any path for a cluster-scoped policy |
| T2 | a service call from a namespaced policy that would carry Kyverno's service-account token | legitimate external calls carry no Kyverno identity, or the policy's own credential |
| T3 | a ConfigMap in another namespace; an empty resolved target | legitimate is a ConfigMap in the policy's namespace, or any ConfigMap for a cluster-scoped policy (where empty still means `default`) |
| T8 | an empty target in a namespaced cleanup policy resolving outside it | legitimate is the policy's own namespace, or any target for a cluster cleanup policy |

### S3 — Fixtures and harness

Every fixture is a normal namespaced `Policy` / `ClusterPolicy` / `CleanupPolicy` with context
loading enabled (deferred loading at its default), and the standard service-account credential
fixture. No disabled, unconfigured or unauthorised state is used. `hiddenHarness.load` builds
`factories.DefaultContextLoaderFactory` and calls `Load` — the product's shared entry point — so a
guard at the factory, loader, apicaller or executor all pass; the cleanup cases drive
`cleanup.controller.cleanup` itself. Pass.

### S4 — Concept independence

| concept | security test(s) on pinned | own route | correct fix alone passes |
|---|---|---|---|
| T1 | the seven `TestSec_APICall*` tests | URLPath guard | yes — `miss_concept_apicall.patch` flips all seven, functional green |
| T2 | `TestSec_ServiceCallDoesNotUseKyvernoCredential` | outbound request headers | yes — `miss_concept_service.patch` flips only it, functional green |
| T3 | `TestSec_ConfigMap*` (two) | typed loader | yes — `miss_concept_configmap.patch` flips one, functional green |
| T8 | `TestSec_CleanupContextCrossNamespace` | cleanup controller | yes — `miss_concept_cleanup.patch` flips only it, functional green |

No masking (H3c) applies: pattern H3b, and every concept's security test fails on the pinned code
through its own route.

### S5 — History

H3b. `checks/upstream_first_fix.patch` (A alone) still allows the cluster-scoped Namespace object
for a namespaced policy and leaves the typed loader, the credential lending and the cleanup wiring
open — 5 security tests fail — so it violates the property read literally. The complete published
fix (A+B) still leaves the object, the credential lending and the cleanup wiring open — 3 security
tests fail. Both are wired `security_fail`; the new `upstream_namespace_object.patch` isolates the
object refusal. Pass.

### S6 — Contracts

Every test drives exported product API (`DefaultContextLoaderFactory`, `ContextLoader.Load`,
`controller.cleanup`) and ordinary context entries; no field or function name must be guessed. The
protected data is stated in product terms ("data that belongs to another namespace or that is
cluster-scoped", "Kyverno's own cluster identity"). The authority for the credential test is the
outbound request's Authorization header, which the test observes directly. No fail-open fallback is
involved. Pass.

### S7 — Decisive tests

No `build/stk-kyverno-ghsacvq5/trial_summary.md` exists, but the audit records that the failed
deepseek-r1 run was decided by one test, `TestFunc_NamespacedPolicyOwnNamespaceRecord`, a genuine
S1 contradiction with the instruction. Re-checked first against S1–S6: the value it held (the
cluster-scoped Namespace object) is forbidden by the primary property, so the fault was the test.
It is replaced by `TestFunc_NamespacedPolicyOwnNamespaceResource`, which holds only a namespaced
resource; `TestSec_APICallOwnNamespaceObject` now asserts the property for the object. No correct
fix fails either. No other test decided a run. `NEEDS_HUMAN_REVIEW: YES` stands for a human to
confirm the replaced test and the new object refusal.

## Verdict

The pinned code fails all 11 security tests; the reference passes all 23 hidden tests and every
functional value is covered by the general keep-working sentence with no security rule forbidding
it. Gate a is clear.

GATE_A: READY
NEEDS_HUMAN_REVIEW: YES
