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

Project root: `/home/mara/cwe-bench`. Task: `stk-kyverno-ghsacvq5`. Pattern: `A+B`. Track: `stacked`.

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
- Advisory: GHSA-8p9x-46gm-qfx2; GHSA-cvq5-hhx3-f99p
- Pinned (vulnerable) commit: 99260bd2900290d7d898933c421d2a51d01172a6. Published fix: e0ba4de4f1e0, eba60fa856c7, bbf3e5c01391.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "candidate_id": "h3-ghsa-cvq5-hhx3-f99p",
 "pattern": "H3b",
 "repo": "kyverno/kyverno",
 "pinned_commit": "99260bd2900290d7d898933c421d2a51d01172a6",
 "protections": [
  "P1: data a namespaced policy (Policy / CleanupPolicy) pulls into its rule context through Kyverno's own credentials must stay inside the policy's namespace. Today the context loader factory throws the policy away (pkg/engine/factories/contextloaderfactory.go:21), so no loader can scope by namespace. Precedents in the same repo: CEL namespacedImpl (pkg/cel/libs/resource/namespaced_impl.go:27,93) and mutate targets (pkg/engine/handlers/mutation/load_targets.go:93-96)."
 ],
 "traps": [
  {
   "id": "T1",
   "mechanism": "M4",
   "origin": "advisory_route",
   "locations": [
    "pkg/engine/apicall/apiCall.go:60-65",
    "pkg/engine/apicall/executor.go:46-47",
    "pkg/engine/apicall/executor.go:52-57",
    "pkg/engine/factories/contextloaderfactory.go:21",
    "pkg/engine/factories/contextloaderfactory.go:109-112",
    "pkg/clients/dclient/client.go:166-170"
   ],
   "reason_to_dismiss": "",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "easy",
   "tier_mimo": "easy",
   "type": "neither",
   "evidence": [
    "pkg/engine/apicall/executor.go:47 passes the raw urlPath straight to RawAbsPath without checking the namespace",
    "pkg/clients/dclient/client.go:168 does GET RequestURI(path) using Kyverno's own rest client",
    "pkg/engine/factories/contextloaderfactory.go:21 ignores the PolicyInterface argument (`_`), so the loader never knows the policy's namespace",
    "pkg/validation/policy/validate.go:1411-1435 validateAPICall checks only Service/URLPath exclusivity and JMESPath syntax, not the namespace"
   ]
  },
  {
   "id": "T2",
   "mechanism": "M1",
   "origin": "uncovered_upstream",
   "locations": [
    "pkg/engine/apicall/executor.go:49",
    "pkg/engine/apicall/executor.go:65-80",
    "pkg/engine/apicall/executor.go:131",
    "pkg/engine/apicall/executor.go:143-153",
    "pkg/engine/apicall/executor.go:158-166"
   ],
   "reason_to_dismiss": "service calls are meant for external HTTP services, not the kube API, so a urlPath namespace check looks complete; any URL that points back at the API server reads like a separate SSRF concern",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "xhard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "pkg/engine/apicall/executor.go:148-152 adds Kyverno's own service-account bearer token whenever the policy sets no Authorization header",
    "pkg/engine/apicall/executor.go:159 reads that token from /var/run/secrets/kubernetes.io/serviceaccount/token",
    "pkg/engine/apicall/executor.go:131 uses apiCall.Service.URL exactly as the policy wrote it, so it can name the API server and any namespace path"
   ]
  },
  {
   "id": "T3",
   "mechanism": "M2",
   "origin": "uncovered_upstream",
   "locations": [
    "pkg/engine/context/loaders/configmap.go:65-83",
    "pkg/engine/factories/contextloaderfactory.go:101-104",
    "pkg/validation/policy/validate.go:1399-1409",
    "pkg/engine/context/resolvers/resolvers.go:25-27",
    "pkg/engine/context/resolvers/resolvers.go:40-42"
   ],
   "reason_to_dismiss": "configMap entries are a typed, non-secret lookup and differ from raw apiCall paths; the advisory talks about apiCall/RBAC, so a solver may treat ConfigMaps as low-sensitivity shared config",
   "distance": {
    "files": 1,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "medium",
   "tier_mimo": "medium",
   "type": "neither",
   "evidence": [
    "pkg/engine/context/loaders/configmap.go:76 takes the namespace from the policy entry after variable substitution",
    "pkg/engine/context/loaders/configmap.go:83 resolver.Get(namespace, name) runs with no policy-namespace comparison",
    "pkg/engine/context/resolvers/resolvers.go:41 the client resolver reads ConfigMaps in any namespace with Kyverno's credentials",
    "pkg/validation/policy/validate.go:1404 requires only a non-empty namespace"
   ]
  },
  {
   "id": "T4",
   "mechanism": "M5",
   "origin": "injection_room",
   "locations": [
    "pkg/engine/context/loaders/configmap.go:76-82"
   ],
   "reason_to_dismiss": "admission validation already rejects an empty configMap namespace (validate.go:1404), so the \"default\" fallback looks unreachable",
   "distance": {
    "files": 1,
    "packages": 1
   },
   "protection_state": "weak",
   "tier_deepseek": "hard",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "pkg/engine/context/loaders/configmap.go:80-82 replaces an empty substituted namespace with \"default\", not with the policy's namespace",
    "pkg/validation/policy/validate.go:1404 checks the raw template string, so a `{{...}}` that substitutes to \"\" passes admission and reaches the fallback"
   ]
  },
  {
   "id": "T5",
   "mechanism": "M7",
   "origin": "injection_room",
   "locations": [
    "pkg/engine/apicall/apiCall.go:61",
    "pkg/validation/policy/validate.go:1411-1420"
   ],
   "reason_to_dismiss": "a namespace check at policy admission (validateAPICall) feels like the natural place for a static policy-authoring rule",
   "distance": {
    "files": 1,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "medium",
   "tier_mimo": "medium",
   "type": "neither",
   "evidence": [
    "pkg/engine/apicall/apiCall.go:61 substitutes variables into the whole APICall (including urlPath) only at runtime, so an admission-time check sees templates, not final paths"
   ]
  },
  {
   "id": "T6",
   "mechanism": "M8",
   "origin": "injection_room",
   "locations": [
    "pkg/engine/apicall/executor.go:46-47",
    "pkg/clients/dclient/client.go:168-170"
   ],
   "reason_to_dismiss": "a check that the path contains /namespaces/<policy-ns>/ looks sufficient",
   "distance": {
    "files": 1,
    "packages": 2
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "mimo",
   "evidence": [
    "pkg/clients/dclient/client.go:168,170 RequestURI(path) forwards the path, query and dot-segments to the API server unchanged, so a lexical prefix/substring check can be fooled by: all-namespace list paths (no /namespaces/ segment), `<ns>-suffix` prefix collisions, `..` segments and query strings",
    "pkg/engine/apicall/executor.go:46-47 any non-empty urlPath goes to the kube API, with GET or POST"
   ]
  },
  {
   "id": "T7",
   "mechanism": "M11",
   "origin": "injection_room",
   "locations": [
    "pkg/engine/factories/contextloaderfactory.go:20-21",
    "pkg/engine/apicall/executor.go:46-47",
    "pkg/clients/dclient/client.go:169-170"
   ],
   "reason_to_dismiss": "",
   "distance": {
    "files": 1,
    "packages": 2
   },
   "protection_state": "weak",
   "tier_deepseek": "medium",
   "tier_mimo": "hard",
   "type": "mimo",
   "evidence": [
    "These must keep working next to the hidden cross-namespace path: ClusterPolicy (empty namespace) must keep cluster-wide apiCall access; a namespaced policy must keep reading its own namespace's objects and plausibly the Namespace object /api/v1/namespaces/<own-ns> itself (that path has no trailing namespaced segment)",
    "pkg/clients/dclient/client.go:170 POST through urlPath is supported, so a policy may legitimately POST to cluster-scoped review endpoints"
   ]
  },
  {
   "id": "T8",
   "mechanism": "M10",
   "origin": "uncovered_upstream",
   "locations": [
    "pkg/controllers/cleanup/controller.go:171-183",
    "api/kyverno/v2/cleanup_policy_types.go:207",
    "api/kyverno/v2beta1/cleanup_policy_types.go:207"
   ],
   "reason_to_dismiss": "the cleanup controller is a separate component, its context only feeds deletion conditions, and it never shows up on the admission webhook path the report points at",
   "distance": {
    "files": 2,
    "packages": 2
   },
   "protection_state": "bypassed",
   "tier_deepseek": "xhard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "pkg/controllers/cleanup/controller.go:173 calls ctxFactory(nil, kyvernov1.Rule{}) and passes a nil policy, so a factory-level check keyed on the policy's namespace treats a namespaced CleanupPolicy as cluster-scoped",
    "pkg/controllers/cleanup/controller.go:174-181 loads spec.Context (apiCall/configMap entries) with c.client before any namespace scoping",
    "pkg/controllers/cleanup/controller.go:187 the rest of the controller scopes by policy.GetNamespace(), showing the namespace is available here"
   ]
  },
  {
   "id": "T9",
   "mechanism": "M8",
   "origin": "injection_room",
   "locations": [
    "pkg/validation/policy/validate.go:1294-1303",
    "api/kyverno/v1/common_types.go:426",
    "api/kyverno/v1/common_types.go:726",
    "api/kyverno/v1/common_types.go:836",
    "api/kyverno/v1/resource_spec_types.go:48",
    "pkg/engine/handlers/mutation/common.go:97",
    "pkg/engine/handlers/validation/validate_resource.go:264",
    "pkg/engine/handlers/mutation/mutate_existing.go:83"
   ],
   "reason_to_dismiss": "rule.Context is the documented place for context entries; nested foreach and mutate-target contexts look like the same feature",
   "distance": {
    "files": 2,
    "packages": 3
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "medium",
   "type": "neither",
   "evidence": [
    "pkg/validation/policy/validate.go:1303 validateRuleContext walks only rule.Context, never ForEachMutation/ForEachValidation/ForEachGeneration.Context or ResourceSpec.Context",
    "pkg/engine/handlers/mutation/common.go:97 and pkg/engine/handlers/mutation/mutate_existing.go:83 load nested contexts through the same loader at runtime"
   ]
  },
  {
   "id": "T10",
   "mechanism": "M4",
   "origin": "uncovered_upstream",
   "locations": [
    "pkg/engine/context/loaders/globalcontext.go:78-107",
    "pkg/engine/factories/contextloaderfactory.go:117-120",
    "pkg/cel/policies/vpol/compiler/compiler.go:242-244",
    "pkg/cel/policies/dpol/compiler/compiler.go:136-138",
    "pkg/imageverification/evaluator/compiler.go:202-204"
   ],
   "reason_to_dismiss": "GlobalContextEntry data is curated by a cluster admin and is meant to be shared, so reading it from a namespaced policy is arguably by design",
   "distance": {
    "files": 2,
    "packages": 3
   },
   "protection_state": "absent",
   "tier_deepseek": "xhard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "pkg/engine/context/loaders/globalcontext.go:97 gctxStore.Get(gctxName) runs with no policy-namespace filter",
    "pkg/cel/policies/vpol/compiler/compiler.go:254-256 the resource lib is namespace-scoped, while globalcontext.Lib at :242-244 takes no namespace"
   ]
  }
 ],
 "independent_groups": [
  [
   "T1",
   "T5",
   "T6",
   "T7",
   "T9"
  ],
  [
   "T2"
  ],
  [
   "T3",
   "T4"
  ],
  [
   "T8"
  ],
  [
   "T10"
  ]
 ],
 "history": {
  "a_fix_leaves_b_open": null,
  "b_in_code_a_wrote": false,
  "masking": [
   "T8 only shows up once a fix for T1/T3 is placed in the shared contextloaderfactory and keyed on the policy argument: the nil policy at cleanup/controller.go:173 then bypasses it silently"
  ],
  "dependency_bump_fix": false,
  "in_repo_fix_possible": true
 },
 "conflicts": [
  {
   "a": "T6",
   "b": "T7",
   "what": "a strict rule (path must start with /api(s)/.../namespaces/<own-ns>/, GET only) closes the path shapes in T6 but breaks reading the policy's own Namespace object and POSTs to cluster-scoped review endpoints"
  },
  {
   "a": "T4",
   "b": "T7",
   "what": "changing the \"default\" fallback for every policy instead of only namespaced ones changes behaviour that ClusterPolicy configMap entries rely on"
  },
  {
   "a": "T8",
   "b": "T7",
   "what": "treating a nil policy as forbidden (fail-closed) breaks ClusterCleanupPolicy context loading; the real fix is to pass the cleanup policy's namespace into the factory"
  }
 ],
 "fairness_risks": [
  "ClusterPolicy / ClusterCleanupPolicy (empty namespace) must keep unrestricted apiCall and configMap access (contextloaderfactory.go:20-21 shared by both)",
  "Namespaced policies reading the policy's own Namespace object (/api/v1/namespaces/<ns>) is a common legitimate pattern, and a trailing-slash-only rule refuses it",
  "Service apiCalls to genuine external services must keep working; tests for T2 should check only that Kyverno's SA token is not attached for namespaced policies (or that API-server targets are refused), not ban services",
  "T10: blocking globalReference in namespaced policies may contradict the intended GlobalContextEntry sharing model; do not test it as a must-refuse"
 ],
 "effort_minutes": 120,
 "usable": true,
 "design": {
  "traps": [
   "T1",
   "T2",
   "T3",
   "T8"
  ],
  "why": "There are four independent fix sites, each with a different reason to dismiss: T1 is the advisory urlPath route, and its hidden tests should include the T6 path shapes and the T7 own-namespace/ClusterPolicy keep-working cases, which makes this group the mimo-type how/coupled-value test. T2 is deepseek-type: the service-call route that silently attaches Kyverno's token is easy to wave off as 'external SSRF'. T3 (with the T4 default-namespace fallback) is a second loader implementation (medium M2/M5). T8 is deepseek-type: the cleanup controller passes a nil policy, a wrong-object bypass that only matters once the obvious factory fix lands. T10 is left out because it is arguably by-design and carries a fairness risk. T5/T9 sit inside the T1 group, so they add no independent judgement."
 },
 "unverified": [
  "Which route the published B fix (bbf3e5c01391) actually closed: I could not read the fix commits from the pinned tree. B is most likely T3 (configMap) or T2 (service call) given szz_status H3b-elsewhere, but this is unconfirmed",
  "The A fix (e0ba4de4f1e0; eba60fa856c7) is absent from the pinned tree: there is no namespace check in pkg/engine/apicall or validateAPICall (validate.go:1411-1435). So whether A's code leaves B open, and whether A sits at admission or runtime, cannot be checked here",
  "Whether GlobalContextEntry is cluster-scoped and admin-only (T10's reason to dismiss) was not checked against the CRD scope in api/",
  "Whether the cleanup controller's client has broader read RBAC than the admission controller (T8's impact) was not checked in the charts",
  "The CEL http lib (pkg/cel/libs/http) adds no SA token automatically (only test fixtures set Authorization), so it was not recorded as a route"
 ]
}
  ```
- Published fix sites:   - pkg/engine/apicall/apiCall.go:60-65 — T1 M4 (reason to dismiss: none)
  - pkg/engine/apicall/executor.go:46-47 — T1 M4 (reason to dismiss: none)
  - pkg/engine/apicall/executor.go:52-57 — T1 M4 (reason to dismiss: none)
  - pkg/engine/factories/contextloaderfactory.go:21 — T1 M4 (reason to dismiss: none)
  - pkg/engine/factories/contextloaderfactory.go:109-112 — T1 M4 (reason to dismiss: none)
  - pkg/clients/dclient/client.go:166-170 — T1 M4 (reason to dismiss: none)
- Uncovered routes to confirm (pattern B):   - pkg/engine/apicall/executor.go:49 — T2 M1 (reason to dismiss: service calls are meant for external HTTP services, not the kube API, so a urlPath namespace check looks complete; any URL that points back at the API server reads like a separate SSRF concern)
  - pkg/engine/apicall/executor.go:65-80 — T2 M1 (reason to dismiss: service calls are meant for external HTTP services, not the kube API, so a urlPath namespace check looks complete; any URL that points back at the API server reads like a separate SSRF concern)
  - pkg/engine/apicall/executor.go:131 — T2 M1 (reason to dismiss: service calls are meant for external HTTP services, not the kube API, so a urlPath namespace check looks complete; any URL that points back at the API server reads like a separate SSRF concern)
  - pkg/engine/apicall/executor.go:143-153 — T2 M1 (reason to dismiss: service calls are meant for external HTTP services, not the kube API, so a urlPath namespace check looks complete; any URL that points back at the API server reads like a separate SSRF concern)
  - pkg/engine/apicall/executor.go:158-166 — T2 M1 (reason to dismiss: service calls are meant for external HTTP services, not the kube API, so a urlPath namespace check looks complete; any URL that points back at the API server reads like a separate SSRF concern)
  - pkg/engine/context/loaders/configmap.go:65-83 — T3 M2 (reason to dismiss: configMap entries are a typed, non-secret lookup and differ from raw apiCall paths; the advisory talks about apiCall/RBAC, so a solver may treat ConfigMaps as low-sensitivity shared config)
  - pkg/engine/factories/contextloaderfactory.go:101-104 — T3 M2 (reason to dismiss: configMap entries are a typed, non-secret lookup and differ from raw apiCall paths; the advisory talks about apiCall/RBAC, so a solver may treat ConfigMaps as low-sensitivity shared config)
  - pkg/validation/policy/validate.go:1399-1409 — T3 M2 (reason to dismiss: configMap entries are a typed, non-secret lookup and differ from raw apiCall paths; the advisory talks about apiCall/RBAC, so a solver may treat ConfigMaps as low-sensitivity shared config)
  - pkg/engine/context/resolvers/resolvers.go:25-27 — T3 M2 (reason to dismiss: configMap entries are a typed, non-secret lookup and differ from raw apiCall paths; the advisory talks about apiCall/RBAC, so a solver may treat ConfigMaps as low-sensitivity shared config)
  - pkg/engine/context/resolvers/resolvers.go:40-42 — T3 M2 (reason to dismiss: configMap entries are a typed, non-secret lookup and differ from raw apiCall paths; the advisory talks about apiCall/RBAC, so a solver may treat ConfigMaps as low-sensitivity shared config)
  - pkg/controllers/cleanup/controller.go:171-183 — T8 M10 (reason to dismiss: the cleanup controller is a separate component, its context only feeds deletion conditions, and it never shows up on the admission webhook path the report points at)
  - api/kyverno/v2/cleanup_policy_types.go:207 — T8 M10 (reason to dismiss: the cleanup controller is a separate component, its context only feeds deletion conditions, and it never shows up on the admission webhook path the report points at)
  - api/kyverno/v2beta1/cleanup_policy_types.go:207 — T8 M10 (reason to dismiss: the cleanup controller is a separate component, its context only feeds deletion conditions, and it never shows up on the admission webhook path the report points at)
  - pkg/engine/context/loaders/globalcontext.go:78-107 — T10 M4 (reason to dismiss: GlobalContextEntry data is curated by a cluster admin and is meant to be shared, so reading it from a namespaced policy is arguably by design)
  - pkg/engine/factories/contextloaderfactory.go:117-120 — T10 M4 (reason to dismiss: GlobalContextEntry data is curated by a cluster admin and is meant to be shared, so reading it from a namespaced policy is arguably by design)
  - pkg/cel/policies/vpol/compiler/compiler.go:242-244 — T10 M4 (reason to dismiss: GlobalContextEntry data is curated by a cluster admin and is meant to be shared, so reading it from a namespaced policy is arguably by design)
  - pkg/cel/policies/dpol/compiler/compiler.go:136-138 — T10 M4 (reason to dismiss: GlobalContextEntry data is curated by a cluster admin and is meant to be shared, so reading it from a namespaced policy is arguably by design)
  - pkg/imageverification/evaluator/compiler.go:202-204 — T10 M4 (reason to dismiss: GlobalContextEntry data is curated by a cluster admin and is meant to be shared, so reading it from a namespaced policy is arguably by design)
- Design plan from the lead: TRACK = STACKED (H3b). Build the stacked design the reader chose: traps T1, T2, T3, T8. Why: There are four independent fix sites, each with a different reason to dismiss: T1 is the advisory urlPath route, and its hidden tests should include the T6 path shapes and the T7 own-namespace/ClusterPolicy keep-working cases, which makes this group the mimo-type how/coupled-value test. T2 is deepseek-type: the service-call route that silently attaches Kyverno's token is easy to wave off as 'external SSRF'. T3 (with the T4 default-namespace fallback) is a second loader implementation (medium M2/M5). T8 is deepseek-type: the cleanup controller passes a nil policy, a wrong-object bypass that only matters once the obvious factory fix lands. T10 is left out because it is arguably by-design and carries a fairness risk. T5/T9 sit inside the T1 group, so they add no independent judgement. Follow the stacked-task rules appended at the end of this prompt; they add to the rules above.
- Host notes: Reader fairness risks (resolve each in the report's contracts or the tests): ClusterPolicy / ClusterCleanupPolicy (empty namespace) must keep unrestricted apiCall and configMap access (contextloaderfactory.go:20-21 shared by both) | Namespaced policies reading the policy's own Namespace object (/api/v1/namespaces/<ns>) is a common legitimate pattern, and a trailing-slash-only rule refuses it | Service apiCalls to genuine external services must keep working; tests for T2 should check only that Kyverno's SA token is not attached for namespaced policies (or that API-server targets are refused), not ban services | T10: blocking globalReference in namespaced policies may contradict the intended GlobalContextEntry sharing model; do not test it as a must-refuse. Conflicts the reader found: a strict rule (path must start with /api(s)/.../namespaces/<own-ns>/, GET only) closes the path shapes in T6 but breaks reading the policy's own Namespace object and POSTs to cluster-scoped review endpoints | changing the "default" fallback for every policy instead of only namespaced ones changes behaviour that ClusterPolicy configMap entries rely on | treating a nil policy as forbidden (fail-closed) breaks ClusterCleanupPolicy context loading; the real fix is to pass the cleanup policy's namespace into the factory

## Design: where difficulty comes from
Models find the code the report leads to and diagnose it correctly. They fail on scope. Build these
in, in order of evidence:
1. **Pattern A: the published fix's far sites.**
   - The report leads to one site. The tests cover every entry point the published fix protects,
     including one in a module that looks out of scope: a second implementation, a lower-level
     public API, a wrapper, a save/reload path, or a defaults or merge route.
   - Give it a plausible **reason to dismiss**, and **distance**: another file or package from the
     landing point.
   - **A second implementation is the strongest form of this**: separate code doing the same
     guarded operation (a fallback backend, another package, another transport, a legacy version),
     so fixing the reported copy changes nothing in the other. Models fix the copy the example hits,
     re-run the example and stop. Prefer a real one (Pattern A or B) over a planted one. Find
     candidates by searching for the low-level primitive across packages (redirect following,
     header copying, file writes, message construction). It only counts if the report never
     describes it.
2. **Pattern B: uncovered routes.**
   - Routes into the same protected sink where the advisory's own protection is missing at the
     pinned commit, and which the published fix did not touch.
   - They are unmodified upstream code. A solver may argue they were never covered, but the task's
     general property covers them, so leaving one open is a model failure, not out of scope. The
     same holds for a route where the protection never existed: the property requires it.
   - Make sure the property, read literally, really covers each route (no word that excludes it),
     and that its test fails only when the protection is really missing (it must pass a correct
     fix placed at any valid layer).
   - The strongest lever found so far: DeepSeek 6 of 6 on one; both models 0 of 3 on three combined.
3. **Shape traps: an input form that a plausible check mishandles.** Examples: a value given as an
   array where the check only handles a string; a name split on the first separator when it can
   contain the separator; a resolved path against a lexical check; a rename or rewrite that happens
   after the check; a nested expression the check never inspects. Two conditions: the general
   property must cover the form literally, and the form must not fall inside anything a
   must-keep-working clause or a test fixture calls legitimate. A pure spelling, encoding, verb,
   protocol or role variant of a stated input is NOT a shape trap: both models always catch those
   (see "Never add").
4. **A coupled must-keep-working behaviour** next to the sink, tested functionally, so an
   over-broad fix fails. MiMo tends to over-harden.
5. **Producer off the check's path.** The check depends on data produced elsewhere (a schema,
   serializer, cache, mapper, table builder or config loader) and does not call it; the data
   reaches the check on a separate path (saved and reloaded, rebuilt from config). The fix needs
   both the check and the producer. Models trace into what the check calls, never back to where
   its data comes from. Rules:
   - it counts only if the producer is infrastructure, not a request handler;
   - verify that the check does **not** call the producer; if it does, the model follows the call
     and fixes it;
   - the report describes impact only through the check's path and states the property abstractly
     ("including data saved earlier"); it never points at the producer or the reload path;
   - avoid fixes where the check cannot compile without the producer change (that forces the find);
   - hidden tests must not need a field or function name the solver would have to guess;
   - prefer a producer deep in internal machinery (a table or schema builder). One behind a path
     that is easy to follow falls as soon as anything points at it.
6. **Injected siblings**, only where the plan asks for them. Each must be:
   - code a maintainer could have written, with no deceptive names or comments;
   - reachable through the real entry point;
   - covered by the task's general property, never by a sentence of its own;
   - placed where the upstream fix never touches.
7. **Wrong object.** The authorization check exists but decides on a different object than the one
   the request actually touches: a neighbouring or proxy resource (a parent or container instead of
   the item written), or an identity field the caller supplies (an account inside a caller-provided
   resource name; a parent read from one part of the request while the write uses another). Models
   copy the nearby precedent. Rules:
   - the instruction names the protected object class in product terms ("the objects that hold the
     limits"), never the check or its location;
   - the security test denies exactly the object touched while the proxy object stays allowed;
   - a functional test keeps a legitimate request on that same object working.
8. **Ordering.** The check is right but runs at the wrong moment: after an adjustment turns the
   attacker's value into a different bad value (an offset, a clamp, a unit conversion, a
   normalisation), or after a side effect has already happened (a directory created, a file cleared,
   copied or re-permissioned, a request sent) before the refusal. Rules:
   - the instruction states the property over the attacker's input or the outcome ("nothing outside
     the folder is created or changed, even when the request is refused"), never the order of steps;
   - the security test checks the side effect itself, not only the response;
   - any fix that keeps the property passes, wherever it places the check.
9. **Route where the protection never existed.** Real code reaches the protected sink but never had
   the check at all, so its absence reads as design (DeepSeek missed one 6 of 6 times). Rules:
   - it needs a plausible reason to dismiss: an unsupported combination, a legacy path, a
     neighbouring feature. If the project documents the protection as applying everywhere with no
     exceptions, there is no reason to dismiss and the route adds nothing;
   - the general property must cover it literally; never describe it in the instruction;
   - confirm it with a behavioural test on the pinned copy, like any Pattern B route.
10. **Merged or defaults route.** The restricted value reaches the sink through defaults, a merge,
    inheritance, a patch, or stored configuration rather than the request field the report shows.
    Models treat the report's example fields as the whole set. Rules:
    - state the property over the sink ("anything a submitter supplies that ends up in X, however
      it gets there"), not over the entry or field;
    - the security test drives the merged or stored route through the real entry point;
    - a functional test keeps legitimate defaults and merges working.

Aim for at least two levers with **different** reasons to dismiss.

**At least one lever must be how-type**: its fix needs the mechanism understood, not only found.
How-type levers are a producer off the check's path (5), a coupled must-keep-working value (4), a
shape that a plausible check mishandles (3: a separator split, a rename after the check), and a
route where the protection never existed. Where-type levers (another entry point into the same code,
a second copy, injected siblings) only cost a search. They held only when the report stayed general,
so count them as extras, never as the task's main difficulty.

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

## Environment (`tasks/stk-kyverno-ghsacvq5/environment/Dockerfile`)
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

## Report to the solver (`tasks/stk-kyverno-ghsacvq5/instruction.md`)
**Write:**
- what the system is, at product level;
- one observed impact, with ONE concrete trigger at user level (HTTP request, CLI call or public API
  use);
- the security property as an **invariant**, stated once in general terms: who may do what to which
  data, or what attacker input must never achieve ("no value of X may …, however it arrives"). It is
  fair when, read literally, it covers every tested route and shape; it must not point at any of
  them. Write a second property only for a genuinely different protection, never one per route,
  and never a count;
- every **contract** the tests need, each stated once for the whole product, never per route:
  - the refusal form ("a client error with no side effect");
  - any interface or field name a test uses, stated so it applies everywhere. If a sibling's test
    would need a contract that only that sibling uses, change the test so it does not, or drop the
    sibling;
  - preservation clauses ("everything that works today keeps working exactly as today"). Name a
    coupled legitimate value in property terms ("visible values keep binding even next to a hidden
    one"), not by the feature or route it sits on;
  - a legitimate magnitude next to any attack magnitude;
- that examples are examples, not the full set;
- the standard constraints block: fix the problem and its close variants; keep legitimate use
  working; do not look up the upstream fix; do not special-case the
  example.

**Never write:**
- file, package, function, class, field or parameter names a user would not see;
- line numbers, the root cause, the fix approach, or a CVE or GHSA id;
- a list of routes, spellings or roles;
- restricting adverbs ("directly", "only via");
- anything that names or paraphrases a far site, an uncovered route or an injected sibling;
- any clause that describes where a far site, uncovered route or injected sibling lives, even in
  product terms: no route, operation, command, channel, object kind, stage or format that points
  at one of them. State each property once, over the protected data or outcome, so it covers every
  route without pointing at any;
- a word that is general but is also the name of one stage or entry point ("loading" when the
  product has a load call). Pick wording that cannot be read as one surface.

Check before you finish: for each sentence of the report, ask whether it exists to cover one
specific route or trap. If it does, delete it or widen it into the general property.

Put every identifier that must not appear in `manifest.leak_terms`.

## Tests (`tasks/stk-kyverno-ghsacvq5/tests/`)
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
- **Wrong-fix patches** go in `build/stk-kyverno-ghsacvq5/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/stk-kyverno-ghsacvq5/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/stk-kyverno-ghsacvq5/manifest.json`:**
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

**Also in `build/stk-kyverno-ghsacvq5/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py stk-kyverno-ghsacvq5 --only static
python3 -I builder/gate.py stk-kyverno-ghsacvq5 --only nop
python3 -I builder/gate.py stk-kyverno-ghsacvq5 --only oracle
python3 -I builder/gate.py stk-kyverno-ghsacvq5 --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/stk-kyverno-ghsacvq5/`;
  - edit only `tasks/stk-kyverno-ghsacvq5/`, `build/stk-kyverno-ghsacvq5/` and, for pattern B, the register;
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


## Stacked task: additional rules

You are building a **stacked** task: one checkout with several independent places where a protection
is missing. The reader's record lists them, with evidence: `/home/mara/cwe-bench/stacking/out/reader/h3-ghsa-cvq5-hhx3-f99p.json`. Verify each trap on the
pinned code before you rely on it. The record is a lead.

**The stack**
1. **At least 3 independent concepts.** If one guard or one fix site would close two traps, they are
   ONE concept. Count your reference fix's independent edit sites, not advisories or routes.
2. **Each concept is hard on its own** for at least one target model (tier hard or xhard in the
   record).
3. **Both models covered.** At least one DeepSeek-type trap (a route where the protection never
   existed, with a plausible reason to dismiss it) and at least one MiMo-type trap (a coupled
   must-keep-working value next to a hidden one, or a how-type mechanism).
4. **No single trap carries the task.** A fix that closes every concept except the hardest must still
   fail. Add one `security_fail` check patch per concept (a fix that misses only that concept).
5. **A coupled must-keep-working value next to every hidden route**, tested functionally.
6. **Effort budget.** A careful engineer who knows where to look fixes everything in about 45-60
   minutes. If the stack needs more, drop the weakest concept.

**The report**
7. **One general property per distinct protection.** Never one per route, and never a count. Describe
   no surface, as the build template already requires. If the stack spans two protections, state two
   properties, each over its protected data or outcome.

**History rules** (by the record's `pattern`)
8. **H3a / H3b (fix of a fix):**
   - pin the parent of the earlier fix A's first commit;
   - the reference fix is the complete fix (A plus the later fix B, or an equivalent);
   - add `checks/upstream_first_fix.patch`, which is A's fix applied alone, with `expect: fail`, so
     upstream's first fix is proven to be a wrong fix.
9. **H3c (masking):** the masked bug's security test must fail on the pinned code through its own
   route, without relying on the masking bug, so the gate's nop stage holds.
10. **Conflicting fixes (F8):** when the record names a pair where the natural fix for one trap breaks
    a value another needs, test that value functionally. State it in the report as a
    must-keep-working behaviour, in property terms.
11. **Dependency-bump fixes (F5):** when upstream fixed a bug by upgrading a dependency, the task must
    be fixable inside the repository. The reference proves it. The report never asks for an upgrade,
    and the solver works offline.
12. **Recall check (every pattern):** add `checks/upstream_fix.patch` (every published fix commit for
    the stacked advisories, applied together) with `expect: fail`. If it passes, the stack adds
    nothing beyond what upstream shipped. Rework the design.

**The control task**
13. Also build `<slug>-control`: the same pinned code, the same report, but only the advisory's own
    route (the trap the report leads to) in the security tests and the reference. It isolates the
    effect of stacking from the effect of the host.

**Manifest:** add a `stacking` block containing:
- `pattern`;
- `reader_record`;
- `concepts` (groups of trap ids);
- `history`: advisories A and B with their fix commits, `pinned_commit` and its rule;
- `score_at_build`: from `stacking/score_stack.py`;
- `control_slug`.

**Exact manifest fields the static conformance check reads (step 5, `stacking/check_stack.py`). Emit these literally — the field NAMES and VALUES below must match, or the build is rejected before the container gate:**

`manifest.traps[]` — one object per trap:
- `id` (string) — referenced by `stacking.concepts`.
- `type` — exactly one of `"deepseek"`, `"mimo"`, or `"both"`. At least one trap must be `"deepseek"` or `"both"`, and at least one must be `"mimo"` or `"both"`.
- `origin` — for a hidden route, one of `"uncovered_upstream"`, `"published_fix_far_site"`, `"injection_room"`. Any trap with such an `origin` must also carry `coupled_functional_tests`: a non-empty list of the functional-test ids that keep its must-keep-working value honest.

`manifest.stacking` — an object with exactly these keys (all required):
- `pattern` — e.g. `"H3a"`, `"H3b1"`, `"H3b2"`, `"H4"`.
- `concepts` — a list of **at least 3** groups; each group is a list of trap `id`s forming one independent concept. Every id must exist in `manifest.traps`.
- `history`, `control_slug`, `score_at_build`, `reader_record` — as described above.

`manifest.patch_checks[]` — in addition to the task's normal patch checks, add:
- **One per concept** (a fix that closes every concept EXCEPT this one, so its security tests still fail):
  `{ "patch": "checks/miss_<concept>.patch", "kind": "security_fail", "expect": "fail", "misses": [<exactly this concept's trap ids>] }`.
  `misses` must be non-empty and be a subset of that concept's trap id group; one such check is required for every group in `stacking.concepts`.
- **Recall (always):** `{ "patch": "checks/upstream_fix.patch", "expect": "fail" }` — all published fix commits for the stacked advisories applied together.
- **Recall (H3a and every H3b variant):** also `{ "patch": "checks/upstream_first_fix.patch", "expect": "fail" }` — the earlier fix A applied alone.

Every `checks/*.patch` named above must be a real file in the task's `checks/` directory (the container gate then runs each with its `expect`ed outcome). A concept with no `security_fail` miss-check, a trap with no `type`, or a missing recall check/file each fails the conformance check.

**Report back:** also give the concept count, the DeepSeek-type and MiMo-type trap ids, the result of
each history check patch, and the control task's gate result.

Stacked task slug: `stk-kyverno-ghsacvq5`. Control task slug: `stk-kyverno-ghsacvq5-control`. Manifest `stacking.reader_record`: `stacking/out/reader/h3-ghsa-cvq5-hhx3-f99p.json`.
