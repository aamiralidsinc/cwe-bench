# Fairness review: stk-kyverno-ghsacvq5-control

Revision for `AUDIT-FIX-20261024.md` (post-run audit of the stacked task; this control carries the
same coupled test). The instruction is unchanged. The coupled functional test no longer requires a
namespaced policy to read the cluster-scoped Namespace object: it now exercises an ordinary namespaced
resource in the policy's own namespace. A security test now requires the Namespace object itself to be
refused, and the reference refuses it. The pre-change reference (published-fix equivalent) is kept as
`checks/upstream_namespace_object.patch` and must now fail a security test.

## Security tests (tests/security/zz_sec_apicall_test.go)

| Test | What it asserts | Justified by | Could a correct fix fail? | Risk |
|---|---|---|---|---|
| TestSec_APICallCrossNamespace | a namespaced policy reading another namespace's Secret is refused with no request made | "No policy that belongs to a namespace may read ... data that belongs to another namespace or that is cluster-scoped." | no | low |
| TestSec_APICallDotSegment | the same read reached through `..` segments is refused | same sentence; normalization is standard (CWE-22) | no | low |
| TestSec_APICallNamespacePrefixCollision | a namespace whose name starts with the policy's name is refused | same sentence ("another namespace") | no | low |
| TestSec_APICallClusterWideList | an all-namespace list path is refused | same sentence ("cluster-scoped" / outside the namespace) | no | low |
| TestSec_APICallSubstitutedNamespace | a path that resolves through a variable to another namespace is refused | same sentence; the guard must run after substitution (standard) | no | low |
| TestSec_APICallWriteCrossNamespace | a cross-namespace POST is refused and reaches nothing | same sentence ("or otherwise affect"); "A refusal is a client error and has no effect." | no | low |
| TestSec_APICallOwnNamespaceObject | GET of `/api/v1/namespaces/team-a` (the Namespace object) by a team-a policy is refused with no request made | the Namespace object is cluster-scoped, and the rule forbids "data ... that is cluster-scoped"; a namespaced policy holding that object is the audit's conflict, resolved by the project rule (instruction kept) | no: any refusal is accepted and no status is asserted | low |

## Functional tests (tests/functional/zz_func_context_test.go)

| Test | What it asserts | Justified by | Could a correct fix fail? | Risk |
|---|---|---|---|---|
| TestFunc_NamespacedPolicyOwnNamespaceAPICall | a namespaced policy still GETs configmaps in its own namespace | "Everything that works today keeps working."; the security rule forbids only other-namespace or cluster-scoped data | no | low |
| TestFunc_NamespacedPolicyOwnNamespaceResource | a namespaced policy still GETs deployments in its own namespace (replaces the Namespace-object read) | same general keep-working sentence; a namespaced resource inside the policy's namespace is not forbidden by the rule | no | low |
| TestFunc_NamespacedPolicySubstitutedOwnNamespaceAPICall | a target that resolves to the policy's own namespace still works | same sentence | no | low |
| TestFunc_ClusterPolicyUnrestrictedAPICall | a ClusterPolicy keeps unrestricted reads | same sentence; the rule applies to policies "that belong to a namespace" | no | low |

## Stacking checks

The control carries a single concept (T1, the advisory's API-path route); the parent stack's other
concepts have their own suites and are outside this control's build.

| Check | Concept | Result |
|---|---|---|
| S1 Coupled traps | T1 | The four functional values (own-namespace configmaps/deployments, templated own-namespace target, cluster policy) are covered by "Everything that works today keeps working." No security sentence forbids them: they are neither another namespace's data nor cluster-scoped, and a ClusterPolicy does not belong to a namespace. The prior contradiction (Namespace object held as keep-working while the rule forbids cluster-scoped data) is removed by the test change, not by rewording. |
| S2 Shape traps | T1 | Every refused shape lies outside the legitimate set: another namespace, a normalized path that leaves the namespace, a different namespace whose name shares a prefix, an all-namespace list, a variable resolving outside, a write to another namespace, and the cluster-scoped Namespace object. Legitimate shapes are namespaced resources inside the policy's own namespace. |
| S3 Fixtures and harness | T1 | Every fixture is a normal namespaced Policy or ClusterPolicy; no disabled/unconfigured state is used. `hiddenHarness.load` builds `factories.DefaultContextLoaderFactory` and calls `Load`, the product's shared entry point, so a guard at the factory, loader, or apicall layer all pass. |
| S4 Concept independence | T1 | One concept; vacuous across concepts. The new security test fails on the pinned code through its own route (pinned accepts every path). |
| S5 History | T1 | Parent pattern H3b (published fix A, later completion B). `checks/upstream_namespace_object.patch` is the reference before this change and is exactly the published-fix behaviour: it satisfies neither the literal property (it allows a cluster-scoped read). It is wired `security_fail`, so the gate proves upstream's behaviour is a wrong fix. |
| S6 Contracts | T1 | No field or function name must be guessed; tests drive only exported product API. The protected object class is stated in product terms ("policy that belongs to a namespace", "cluster-scoped data"). No fail-open fallback is involved. |
| S7 Decisive tests | T1 | No `build/stk-kyverno-ghsacvq5-control/trial_summary.md` exists (the postmortem cited by the audit is the parent's). Nothing to re-check; NEEDS_HUMAN_REVIEW stays NO. |

## Leniency / wrong fixes

| Wrong fix | Caught by |
|---|---|
| refuse every API path for namespaced policies | `control_overbroad.patch` (functional_fail) |
| guard only the literal reported path (malformed/partial identity) | `control_malformed_identity.patch` (security_fail) |
| published-fix equivalent that still allows the cluster-scoped Namespace object | `upstream_namespace_object.patch` (security_fail) |

## Required: generalize

None: the instruction was not changed (AUDIT-FIX item 5), and no sentence was added.

## Quality to tighten

No open item. The new refusal test asserts only that the read was refused and made no request, so it
accepts any refusal the instruction allows (error return, no data). It does not require a status or a
message.

GATE_A: READY
NEEDS_HUMAN_REVIEW: NO
