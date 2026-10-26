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

Project root: `/home/mara/cwe-bench`. Task: `stk-vault-secrets-webhook-19004`. Pattern: `A+B`. Track: `stacked`.

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
- Advisory: 19004; CWE-918 server-side request forgery — object-supplied Vault address (a
- Pinned (vulnerable) commit: 71cfbb8907b2b7197e892570975428a447e615be. Published fix: 76db45976fee0f54cafd94dffa425e6b542f65a0.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "candidate_id": "h4-19004",
 "pattern": "H4",
 "repo": "bank-vaults/vault-secrets-webhook",
 "pinned_commit": "71cfbb8907b2b7197e892570975428a447e615be",
 "protections": [
  "P1 (address): an object-supplied Vault address must pass an operator allowlist and an SSRF guard before it becomes the address of the webhook's own Vault client, which carries a ServiceAccount token the webhook obtained for the object-named SA; an operator-configured vault_addr is trusted and must not be forced through that policy. One guard (common.ValidateObjectAddr, pkg/common/addr.go:42) closes the annotation case and the operator-default case is the coupled exemption.",
  "P2 (TLS skip): an object-supplied vault-skip-verify must not disable certificate verification on the webhook's own Vault connection unless the operator opted in; otherwise the operator's vault_skip_verify applies. Separate control, separate helper (common.ResolveObjectSkipVerify, pkg/common/policy.go:44), separate operator key.",
  "P3 (sibling, same rule, different transport): an object-supplied registry-skip-verify must not disable verification on the webhook's outbound image-registry transport without operator opt-in; the operator key registry_skip_verify already exists (pkg/webhook/config.go:502). This protection is not mentioned by the advisory but is the same rule applied to the only other outbound connection the webhook owns."
 ],
 "traps": [
  {
   "id": "T1",
   "mechanism": "M4",
   "origin": "advisory_route",
   "locations": [
    "pkg/webhook/config.go:107-111",
    "pkg/webhook/webhook.go:204",
    "pkg/webhook/webhook.go:310-314"
   ],
   "reason_to_dismiss": "",
   "distance": {
    "files": 2,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "easy",
   "tier_mimo": "easy",
   "type": "neither",
   "evidence": [
    "pkg/webhook/config.go:107-111",
    "pkg/webhook/webhook.go:204",
    "pkg/webhook/webhook.go:285-302",
    "pkg/webhook/webhook.go:310-314",
    "pkg/common/addr.go:42",
    "pkg/common/addr_test.go:23-180"
   ]
  },
  {
   "id": "T2",
   "mechanism": "M11",
   "origin": "advisory_route",
   "locations": [
    "pkg/webhook/config.go:107-111",
    "pkg/webhook/config.go:474",
    "pkg/webhook/webhook.go:196-204",
    "pkg/webhook/webhook_test.go:118-122"
   ],
   "reason_to_dismiss": "Just call the guard unconditionally in newVaultClient: every address that reaches it is 'object-supplied' from the solver's point of view, and a default-deny allowlist is the safest posture.",
   "distance": {
    "files": 2,
    "packages": 1
   },
   "protection_state": "weak",
   "tier_deepseek": "medium",
   "tier_mimo": "hard",
   "type": "mimo",
   "evidence": [
    "pkg/webhook/config.go:107-111",
    "pkg/webhook/config.go:474",
    "pkg/webhook/webhook.go:196-204",
    "pkg/webhook/webhook_test.go:118-122",
    "pkg/webhook/configmap_test.go:33",
    "pkg/webhook/configmap_test.go:60",
    "e2e/test/deployment.yaml:15",
    "e2e/test/configmap.yaml:6",
    "pkg/common/addr_test.go:48-53"
   ]
  },
  {
   "id": "T6",
   "mechanism": "M7",
   "origin": "advisory_route",
   "locations": [
    "pkg/webhook/webhook.go:204",
    "pkg/webhook/webhook.go:259-296"
   ],
   "reason_to_dismiss": "The token is minted for an SA in the object's own namespace and is never returned to the requester, so placing the address check anywhere before the login at webhook.go:310 still prevents the SSRF.",
   "distance": {
    "files": 1,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "medium",
   "tier_mimo": "hard",
   "type": "mimo",
   "evidence": [
    "pkg/webhook/webhook.go:204",
    "pkg/webhook/webhook.go:259-268",
    "pkg/webhook/webhook.go:276-296",
    "pkg/webhook/webhook.go:310-314",
    "deploy/charts/vault-secrets-webhook/templates/webhook-rbac.yaml:49-54"
   ]
  },
  {
   "id": "T3",
   "mechanism": "M4",
   "origin": "advisory_route",
   "locations": [
    "pkg/webhook/config.go:147-151",
    "pkg/webhook/webhook.go:206-207",
    "pkg/common/policy.go:44-56"
   ],
   "reason_to_dismiss": "vault-skip-verify is a documented user-facing annotation (the chart README recommends it verbatim), so honouring it is the feature, not the bug; and no operator opt-in key exists in the tree to honour it with.",
   "distance": {
    "files": 2,
    "packages": 2
   },
   "protection_state": "absent",
   "tier_deepseek": "medium",
   "tier_mimo": "hard",
   "type": "both",
   "evidence": [
    "pkg/webhook/config.go:147-151",
    "pkg/webhook/webhook.go:206-207",
    "pkg/common/policy.go:42-56",
    "pkg/common/policy_test.go:42-47",
    "deploy/charts/vault-secrets-webhook/README.md:18",
    "pkg/webhook/pod.go:93-94",
    "pkg/webhook/pod.go:333-334",
    "pkg/webhook/config.go:475"
   ]
  },
  {
   "id": "T4",
   "mechanism": "M2",
   "origin": "injection_room",
   "locations": [
    "pkg/webhook/config.go:283-287",
    "pkg/webhook/pod.go:279",
    "pkg/webhook/registry.go:185-188"
   ],
   "reason_to_dismiss": "registry-skip-verify is a separate documented feature for private registries with self-signed certificates (different annotation, different outbound connection); the advisory names the Vault address, not the registry transport, so it needs no change.",
   "distance": {
    "files": 3,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "both",
   "evidence": [
    "pkg/webhook/config.go:283-287",
    "pkg/webhook/config.go:502",
    "pkg/webhook/pod.go:279",
    "pkg/webhook/registry.go:163",
    "pkg/webhook/registry.go:180-189",
    "pkg/webhook/registry.go:196",
    "pkg/common/common.go:29",
    "pkg/common/policy.go:44",
    "pkg/webhook/registry.go:143-151"
   ]
  },
  {
   "id": "T5",
   "mechanism": "M4",
   "origin": "uncovered_upstream",
   "locations": [
    "pkg/webhook/pod.go:87-96",
    "pkg/webhook/pod.go:327-335",
    "pkg/webhook/pod.go:848-855"
   ],
   "reason_to_dismiss": "The webhook never dials that address: the mutated workload does, with the tenant's own ServiceAccount, and the tenant can set VAULT_ADDR in its own pod anyway. The annotation is the documented purpose of the feature, and the e2e fixtures rely on a non-default value.",
   "distance": {
    "files": 2,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "xhard",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "pkg/webhook/pod.go:87-96",
    "pkg/webhook/pod.go:153",
    "pkg/webhook/pod.go:158",
    "pkg/webhook/pod.go:189",
    "pkg/webhook/pod.go:223",
    "pkg/webhook/pod.go:327-335",
    "pkg/webhook/pod.go:848-855",
    "e2e/test/deployment.yaml:15",
    "e2e/test/deployment-template.yaml:56",
    "deploy/charts/vault-secrets-webhook/README.md:15",
    "pkg/webhook/config.go:107-111"
   ]
  },
  {
   "id": "T7",
   "mechanism": "M4",
   "origin": "uncovered_upstream",
   "locations": [
    "pkg/webhook/config.go:153-157",
    "pkg/webhook/webhook.go:213-235"
   ],
   "reason_to_dismiss": "The Secret is read from the webhook's own namespace (webhook.go:214-215), so a tenant cannot plant the CA; only an existing operator-created Secret can be named, and the pool replaces system roots only for the operator-named CA.",
   "distance": {
    "files": 2,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "pkg/webhook/config.go:153-157",
    "pkg/webhook/webhook.go:213-235",
    "pkg/webhook/webhook.go:224-234",
    "pkg/webhook/pod.go:535-560"
   ]
  },
  {
   "id": "T8",
   "mechanism": "M4",
   "origin": "injection_room",
   "locations": [
    "pkg/webhook/config.go:128-132",
    "pkg/webhook/config.go:134-138",
    "pkg/webhook/config.go:400-404",
    "pkg/webhook/webhook.go:252-257"
   ],
   "reason_to_dismiss": "Once the address is operator-approved these are documented annotations, and the auth exchange still happens against the operator's Vault, which authorises the role; Vault, not the webhook, is the policy decision point for path and auth method.",
   "distance": {
    "files": 2,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "medium",
   "tier_mimo": "medium",
   "type": "both",
   "evidence": [
    "pkg/webhook/config.go:128-138",
    "pkg/webhook/config.go:400-404",
    "pkg/webhook/webhook.go:252-257",
    "pkg/webhook/webhook.go:310-314",
    "pkg/webhook/pod.go:409-415"
   ]
  },
  {
   "id": "T9",
   "mechanism": "M10",
   "origin": "injection_room",
   "locations": [
    "pkg/webhook/config.go:141-145",
    "pkg/webhook/webhook.go:259-296",
    "pkg/webhook/webhook.go:60-74"
   ],
   "reason_to_dismiss": "The SA is looked up and minted in the object's own namespace (webhook.go:260, 285), so a tenant can only name SAs it shares a namespace with, and the minted token is not returned to the requester.",
   "distance": {
    "files": 3,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "medium",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "pkg/webhook/config.go:140",
    "pkg/webhook/config.go:141-145",
    "pkg/webhook/webhook.go:60-74",
    "pkg/webhook/webhook.go:259-268",
    "pkg/webhook/webhook.go:276-296",
    "deploy/charts/vault-secrets-webhook/templates/webhook-rbac.yaml:49-54"
   ]
  }
 ],
 "independent_groups": [
  [
   "T1",
   "T2",
   "T6"
  ],
  [
   "T3"
  ],
  [
   "T4"
  ],
  [
   "T5"
  ],
  [
   "T7"
  ],
  [
   "T8"
  ],
  [
   "T9"
  ]
 ],
 "history": {
  "a_fix_leaves_b_open": true,
  "b_in_code_a_wrote": false,
  "masking": [
   "The pinned commit already contains the policy library and its full behavioural test table with no production caller (pkg/common/addr.go:42, pkg/common/policy.go:44; callers exist only in pkg/common/addr_test.go:172 and pkg/common/policy_test.go:56), so the shape questions ('which inputs must be refused') are pre-answered in-tree and only the wiring decision remains; the dead helpers mask the difficulty of M8-style traps.",
   "The coupled T2 only becomes visible after T1 is fixed: an unconditional guard in newVaultClient breaks pkg/webhook/webhook_test.go:118-122 (httptest address http://127.0.0.1:PORT), which is a default-mode unit test, so the over-broad fix is detected by the repository's own suite rather than by a hidden test.",
   "Fixing P1 at the loader instead of the client factory makes the pod path reject a legitimate annotation, which is the failure mode the e2e fixtures encode (e2e/test/deployment.yaml:15, e2e/test/configmap.yaml:6, e2e/test/secret.yaml:6); that constraint is only observable once someone tries the loader."
  ],
  "dependency_bump_fix": false,
  "in_repo_fix_possible": true
 },
 "conflicts": [
  {
   "a": "T1",
   "b": "T2",
   "what": "Validating the annotation in the only producer, parseVaultConfig (pkg/webhook/config.go:107-111), closes T1 for all four routes at once but also rewrites the value handed to the mutated workload (pkg/webhook/pod.go:90) and to the operator-default path; if the check is applied unconditionally it rejects the operator default https://vault:8200 (pkg/webhook/config.go:474) and the in-repo client test that uses an httptest loopback address (pkg/webhook/webhook_test.go:118-122). The correct split needs a provenance flag on VaultConfig so only the annotation-derived address is vetted."
  },
  {
   "a": "T3",
   "b": "T5",
   "what": "SkipVerify is a single field with two consumers: the webhook's own TLS (pkg/webhook/webhook.go:206) and the env it writes into every mutated container (pkg/webhook/pod.go:94, 334). Gating the field in parseVaultConfig (the only producer) necessarily changes container behaviour that the chart README tells users to rely on (deploy/charts/vault-secrets-webhook/README.md:18); gating it only at webhook.go:206 leaves the container value object-controlled. Satisfying both needs the gated and propagated values to be separated."
  },
  {
   "a": "T9",
   "b": "T2",
   "what": "Any identity-side fix for the object-named SA has to work for /secrets and /configmaps, which have no service account of their own, and cannot compare against a pod SA because VaultConfig carries no such field (pkg/webhook/config.go:88); a naive binding check breaks pkg/webhook/webhook_test.go:50-57, which passes VaultConfig with only VaultServiceAccount set."
  }
 ],
 "fairness_risks": [
  "The operator knobs the fix needs (an address allowlist, a private-address opt-in, an object-skip-verify opt-in) do not exist anywhere in the pinned tree: no such viper key, chart value, env name or doc line is present, and only the test-local names test_allow_object_skip_verify / test_skip_verify appear (pkg/common/policy_test.go:33-34). If hidden tests set the real key names, they must be stated in the task report or the accepted-address and honoured-opt-in cases are unguessable.",
  "The guard is default-deny on an empty allowlist (pkg/common/addr_test.go:48-53), so a rule 'object address must be allowlisted' contradicts the repository's own e2e fixtures, which set non-default addresses with no allowlist configured (e2e/test/deployment.yaml:15, e2e/test/configmap.yaml:6, e2e/test/secret.yaml:6). Grading 'annotation still works' and 'annotation rejected' together is only possible if the test configures the allowlist.",
  "The rule 'every address passed to newVaultClient is checked' contradicts pkg/webhook/webhook_test.go:118-122 (httptest loopback) and pkg/webhook/configmap_test.go:33,60 (http://localhost:8200); the must-keep-working behaviour is enforced by the repo itself, so the hidden tests must not demand an unconditional check.",
  "Grading the /pods env propagation (T5) as a missing protection would contradict the documented purpose of the annotation (deploy/charts/vault-secrets-webhook/README.md:14-18, e2e/test/deployment-template.yaml:56) and provide no security benefit, since the tenant writes its own pod env anyway (pkg/webhook/pod.go:327-335).",
  "The refusal shapes are already fully specified by an in-tree test table (pkg/common/addr_test.go:23-180), so any hidden test that only re-asserts those shapes passes without any production change.",
  "parseVaultConfig and newVaultClient are unexported and no test calls the annotation loader (no test references parseVaultConfig), so hidden tests must live in package webhook or drive VaultSecretsMutator; a harness that drives the HTTP handlers would need a fake clientset for the token mint and the TLS-Secret read."
 ],
 "effort_minutes": 40,
 "usable": true,
 "design": {
  "traps": [
   "T1",
   "T2",
   "T6",
   "T3",
   "T4"
  ],
  "why": "Three independent groups, each with a different dismissal and a different fix site, all on the webhook's own credential-bearing outbound connections so no documented tenant use is broken. G1 (T1+T2+T6): the address policy must be enforced in newVaultClient with an explicit provenance flag and before the ServiceAccount token mint (pkg/webhook/webhook.go:204, 285-296) - the naive unconditional call is the MiMo failure mode and is caught by the repo's own test (pkg/webhook/webhook_test.go:118-122). G2 (T3): a second, separate control with its own helper and its own operator opt-in, so a solver who only fixes the address still leaves TLS verification object-controlled (pkg/webhook/config.go:147-151 -> pkg/webhook/webhook.go:206). G3 (T4): the same rule on the webhook's only other outbound transport, reachable from the same annotation loader, with a ready-made operator default (pkg/webhook/config.go:502) and a strong 'different documented feature' dismissal - the DeepSeek failure mode. This beats designs built on T5 (documented pod behaviour, no security gain, breaks e2e fixtures), T7 (the CA is read from the webhook's own namespace, so there is no tenant-controlled trust material) and T9 (no upstream change, and no definable policy for objects that have no SA), and it beats a single-site design because loader placement and factory placement conflict: one trap rewards each, which is exactly the judgement the stacked task should measure."
 },
 "unverified": [
  "No shell in this session: build, `go test ./...` and `make test-e2e` were not run; build facts are read from go.mod:3, .go-version:1 and Makefile:42-75.",
  "The screener's fix.diff is not present in the worktree, so the exact fix sites, the new viper key names and the claimed ordering (guard before clientConfig.Address and before the TokenRequest mint) could not be read; only the pinned tree and the screener record were used.",
  "Whether the helper library (pkg/common/addr.go, pkg/common/policy.go) and the wiring are separate upstream commits could not be checked (no git log access); the pinned HEAD message is the only evidence that the library landed alone.",
  "vault-sdk (github.com/bank-vaults/vault-sdk v0.12.0) internals were not read, so which credential ClientAuthMethod presents when no vault-serviceaccount is set (the webhook's own SA token versus an annotation-derived one) is not established; only the in-repo token path at pkg/webhook/webhook.go:259-302 was verified.",
  "It is unknown whether the graders' hidden tests cover the registry sibling (T4), the pod env route (T5) or the token identity (T9); those origins are injection_room / uncovered_upstream and no upstream fix touches them.",
  "Whether the task report given to solvers names the new operator keys is unknown; without that, the allowlist-accepted and opt-in-honoured cases are not gradeable.",
  "Repo size was not measured; the 'tiny_repo' penalty is accepted from the candidate metadata (20 Go files, all relevant logic in pkg/webhook and pkg/common)."
 ]
}
  ```
- Published fix sites:   - pkg/webhook/config.go:107-111 — T1 M4 (reason to dismiss: none)
  - pkg/webhook/webhook.go:204 — T1 M4 (reason to dismiss: none)
  - pkg/webhook/webhook.go:310-314 — T1 M4 (reason to dismiss: none)
  - pkg/webhook/config.go:107-111 — T2 M11 (reason to dismiss: Just call the guard unconditionally in newVaultClient: every address that reaches it is 'object-supplied' from the solver's point of view, and a default-deny allowlist is the safest posture.)
  - pkg/webhook/config.go:474 — T2 M11 (reason to dismiss: Just call the guard unconditionally in newVaultClient: every address that reaches it is 'object-supplied' from the solver's point of view, and a default-deny allowlist is the safest posture.)
  - pkg/webhook/webhook.go:196-204 — T2 M11 (reason to dismiss: Just call the guard unconditionally in newVaultClient: every address that reaches it is 'object-supplied' from the solver's point of view, and a default-deny allowlist is the safest posture.)
  - pkg/webhook/webhook_test.go:118-122 — T2 M11 (reason to dismiss: Just call the guard unconditionally in newVaultClient: every address that reaches it is 'object-supplied' from the solver's point of view, and a default-deny allowlist is the safest posture.)
  - pkg/webhook/webhook.go:204 — T6 M7 (reason to dismiss: The token is minted for an SA in the object's own namespace and is never returned to the requester, so placing the address check anywhere before the login at webhook.go:310 still prevents the SSRF.)
  - pkg/webhook/webhook.go:259-296 — T6 M7 (reason to dismiss: The token is minted for an SA in the object's own namespace and is never returned to the requester, so placing the address check anywhere before the login at webhook.go:310 still prevents the SSRF.)
  - pkg/webhook/config.go:147-151 — T3 M4 (reason to dismiss: vault-skip-verify is a documented user-facing annotation (the chart README recommends it verbatim), so honouring it is the feature, not the bug; and no operator opt-in key exists in the tree to honour it with.)
  - pkg/webhook/webhook.go:206-207 — T3 M4 (reason to dismiss: vault-skip-verify is a documented user-facing annotation (the chart README recommends it verbatim), so honouring it is the feature, not the bug; and no operator opt-in key exists in the tree to honour it with.)
  - pkg/common/policy.go:44-56 — T3 M4 (reason to dismiss: vault-skip-verify is a documented user-facing annotation (the chart README recommends it verbatim), so honouring it is the feature, not the bug; and no operator opt-in key exists in the tree to honour it with.)
- Uncovered routes to confirm (pattern B):   - pkg/webhook/pod.go:87-96 — T5 M4 (reason to dismiss: The webhook never dials that address: the mutated workload does, with the tenant's own ServiceAccount, and the tenant can set VAULT_ADDR in its own pod anyway. The annotation is the documented purpose of the feature, and the e2e fixtures rely on a non-default value.)
  - pkg/webhook/pod.go:327-335 — T5 M4 (reason to dismiss: The webhook never dials that address: the mutated workload does, with the tenant's own ServiceAccount, and the tenant can set VAULT_ADDR in its own pod anyway. The annotation is the documented purpose of the feature, and the e2e fixtures rely on a non-default value.)
  - pkg/webhook/pod.go:848-855 — T5 M4 (reason to dismiss: The webhook never dials that address: the mutated workload does, with the tenant's own ServiceAccount, and the tenant can set VAULT_ADDR in its own pod anyway. The annotation is the documented purpose of the feature, and the e2e fixtures rely on a non-default value.)
  - pkg/webhook/config.go:153-157 — T7 M4 (reason to dismiss: The Secret is read from the webhook's own namespace (webhook.go:214-215), so a tenant cannot plant the CA; only an existing operator-created Secret can be named, and the pool replaces system roots only for the operator-named CA.)
  - pkg/webhook/webhook.go:213-235 — T7 M4 (reason to dismiss: The Secret is read from the webhook's own namespace (webhook.go:214-215), so a tenant cannot plant the CA; only an existing operator-created Secret can be named, and the pool replaces system roots only for the operator-named CA.)
- Design plan from the lead: TRACK = STACKED (H4). Build the stacked design the reader chose: traps T1, T2, T6, T3, T4. Why: Three independent groups, each with a different dismissal and a different fix site, all on the webhook's own credential-bearing outbound connections so no documented tenant use is broken. G1 (T1+T2+T6): the address policy must be enforced in newVaultClient with an explicit provenance flag and before the ServiceAccount token mint (pkg/webhook/webhook.go:204, 285-296) - the naive unconditional call is the MiMo failure mode and is caught by the repo's own test (pkg/webhook/webhook_test.go:118-122). G2 (T3): a second, separate control with its own helper and its own operator opt-in, so a solver who only fixes the address still leaves TLS verification object-controlled (pkg/webhook/config.go:147-151 -> pkg/webhook/webhook.go:206). G3 (T4): the same rule on the webhook's only other outbound transport, reachable from the same annotation loader, with a ready-made operator default (pkg/webhook/config.go:502) and a strong 'different documented feature' dismissal - the DeepSeek failure mode. This beats designs built on T5 (documented pod behaviour, no security gain, breaks e2e fixtures), T7 (the CA is read from the webhook's own namespace, so there is no tenant-controlled trust material) and T9 (no upstream change, and no definable policy for objects that have no SA), and it beats a single-site design because loader placement and factory placement conflict: one trap rewards each, which is exactly the judgement the stacked task should measure. Follow the stacked-task rules appended at the end of this prompt; they add to the rules above.
- Host notes: Reader fairness risks (resolve each in the report's contracts or the tests): The operator knobs the fix needs (an address allowlist, a private-address opt-in, an object-skip-verify opt-in) do not exist anywhere in the pinned tree: no such viper key, chart value, env name or doc line is present, and only the test-local names test_allow_object_skip_verify / test_skip_verify appear (pkg/common/policy_test.go:33-34). If hidden tests set the real key names, they must be stated in the task report or the accepted-address and honoured-opt-in cases are unguessable. | The guard is default-deny on an empty allowlist (pkg/common/addr_test.go:48-53), so a rule 'object address must be allowlisted' contradicts the repository's own e2e fixtures, which set non-default addresses with no allowlist configured (e2e/test/deployment.yaml:15, e2e/test/configmap.yaml:6, e2e/test/secret.yaml:6). Grading 'annotation still works' and 'annotation rejected' together is only possible if the test configures the allowlist. | The rule 'every address passed to newVaultClient is checked' contradicts pkg/webhook/webhook_test.go:118-122 (httptest loopback) and pkg/webhook/configmap_test.go:33,60 (http://localhost:8200); the must-keep-working behaviour is enforced by the repo itself, so the hidden tests must not demand an unconditional check. | Grading the /pods env propagation (T5) as a missing protection would contradict the documented purpose of the annotation (deploy/charts/vault-secrets-webhook/README.md:14-18, e2e/test/deployment-template.yaml:56) and provide no security benefit, since the tenant writes its own pod env anyway (pkg/webhook/pod.go:327-335). | The refusal shapes are already fully specified by an in-tree test table (pkg/common/addr_test.go:23-180), so any hidden test that only re-asserts those shapes passes without any production change. | parseVaultConfig and newVaultClient are unexported and no test calls the annotation loader (no test references parseVaultConfig), so hidden tests must live in package webhook or drive VaultSecretsMutator; a harness that drives the HTTP handlers would need a fake clientset for the token mint and the TLS-Secret read.. Conflicts the reader found: Validating the annotation in the only producer, parseVaultConfig (pkg/webhook/config.go:107-111), closes T1 for all four routes at once but also rewrites the value handed to the mutated workload (pkg/webhook/pod.go:90) and to the operator-default path; if the check is applied unconditionally it rejects the operator default https://vault:8200 (pkg/webhook/config.go:474) and the in-repo client test that uses an httptest loopback address (pkg/webhook/webhook_test.go:118-122). The correct split needs a provenance flag on VaultConfig so only the annotation-derived address is vetted. | SkipVerify is a single field with two consumers: the webhook's own TLS (pkg/webhook/webhook.go:206) and the env it writes into every mutated container (pkg/webhook/pod.go:94, 334). Gating the field in parseVaultConfig (the only producer) necessarily changes container behaviour that the chart README tells users to rely on (deploy/charts/vault-secrets-webhook/README.md:18); gating it only at webhook.go:206 leaves the container value object-controlled. Satisfying both needs the gated and propagated values to be separated. | Any identity-side fix for the object-named SA has to work for /secrets and /configmaps, which have no service account of their own, and cannot compare against a pod SA because VaultConfig carries no such field (pkg/webhook/config.go:88); a naive binding check breaks pkg/webhook/webhook_test.go:50-57, which passes VaultConfig with only VaultServiceAccount set.

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

## Environment (`tasks/stk-vault-secrets-webhook-19004/environment/Dockerfile`)
- **Base and code.** A small official base image. The repo goes into `/app` at the pinned commit,
  and `/app/.git` is then deleted.
- **Offline.** Install every dependency, tool and service the project and tests need; nothing may
  be downloaded at test time. Services start from `test.sh`.
- **Packages:** `patch`, `curl`, `ca-certificates`, `bash`, `git`.
- **Agent layer.** Append `common/trial/claude-code.Dockerfile.snippet` unchanged at the end.
- **No test code in the image.** The agent shares the container. Pre-build against stubs; `test.sh`
  copies the real tests in at grading time.
- **Project tests.** The project's own tests for the affected area must pass in the image at the
  pinned commit.
- **No leaked regression tests.** The pinned commit must not already contain the advisory's
  regression tests (check `git log` between the pinned and fix commits).

## Report to the solver (`tasks/stk-vault-secrets-webhook-19004/instruction.md`)
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

## Tests (`tasks/stk-vault-secrets-webhook-19004/tests/`)
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
- **Wrong-fix patches** go in `build/stk-vault-secrets-webhook-19004/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/stk-vault-secrets-webhook-19004/`:**
- `instruction.md`;
- `task.toml`, from `common/builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/stk-vault-secrets-webhook-19004/manifest.json`:**
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

**Also in `build/stk-vault-secrets-webhook-19004/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `common/builder/templates/` and `common/trial/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I common/gate/gate.py stk-vault-secrets-webhook-19004 --only static
python3 -I common/gate/gate.py stk-vault-secrets-webhook-19004 --only nop
python3 -I common/gate/gate.py stk-vault-secrets-webhook-19004 --only oracle
python3 -I common/gate/gate.py stk-vault-secrets-webhook-19004 --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/stk-vault-secrets-webhook-19004/`;
  - edit only `tasks/stk-vault-secrets-webhook-19004/`, `build/stk-vault-secrets-webhook-19004/` and, for pattern B, the register;
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
is missing. The reader's record lists them, with evidence: `/home/mara/cwe-bench/pipelines/stacking/out/reader/h4-19004.json`. Verify each trap on the
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
5. **A coupled must-keep-working value next to every hidden route**, tested functionally. The
   report covers it ONLY through the general keep-working sentence ("everything that works today
   keeps working"); it never names or describes the value. If a security rule, read literally, would
   forbid that value, reword the security rule over its protected outcome instead of adding an
   exception that names the value.
6. **Effort budget.** A careful engineer who knows where to look fixes everything in about 45-60
   minutes. If the stack needs more, drop the weakest concept.

**The report**
7. **One general property per distinct protection, and nothing per trap.** Never one per route, and
   never a count. Describe no surface, as the build template already requires. If the stack spans two
   protections, state two properties, each over its protected data or outcome.
   - **The one-bug test:** for every sentence of the report, ask "would this sentence be here if the
     task had only the advisory's own route?" If not, delete it. That covers forms ("in every form it
     can be named"), timing ("and again when the call connects"), sources ("whichever response
     supplies it"), encodings, aliases, example values in keep-working lines, and lists of resources.
   - Only the advisory's own route may be shown, in the impact example.
   - General contracts that hold for every route stay: the refusal form (for example "a client
     error, with no effect"), an operator opt-in, "keep every legitimate use working".
   - Keep the report short: the goal in a few lines, the property, the general contracts.
   - After the build, `pipelines/stacking/4-listing/run_listing_check.sh` classifies every hidden trap against the
     report. One NAMED hidden trap, or more than one DESCRIBED hidden trap, is a FAIL. Once the
     reviewer is calibrated (`pipelines/stacking/4-listing/LISTING_ENFORCE`), a FAIL means the task is not marked sound.

**History rules** (by the record's `pattern`)
8. **H3a / H3b (fix of a fix):**
   - pin the parent of the earlier fix A's first commit;
   - the reference fix is the complete fix (A plus the later fix B, or an equivalent);
   - add `checks/upstream_first_fix.patch`, which is A's fix applied alone, with `expect: fail`, so
     upstream's first fix is proven to be a wrong fix.
9. **H3c (masking):** the masked bug's security test must fail on the pinned code through its own
   route, without relying on the masking bug, so the gate's nop stage holds.
10. **Conflicting fixes (F8):** when the record names a pair where the natural fix for one trap breaks
    a value another needs, test that value functionally. The report covers it only through the
    general keep-working sentence, as in rule 5; never by naming the value.
11. **Dependency-bump fixes (F5):** when upstream fixed a bug by upgrading a dependency, the task must
    be fixable inside the repository. The reference proves it. The report never asks for an upgrade,
    and the solver works offline.
12. **Recall check (every pattern):** add `checks/upstream_fix.patch` (every published fix commit for
    the stacked advisories, applied together) with `expect: fail`. If it passes, the stack adds
    nothing beyond what upstream shipped. Rework the design.

**The control task**
13. Also build `<slug>-control`: the same pinned code, the same report, but only the advisory's own
    route (the trap the report leads to) in the security tests and the reference. It isolates the
    effect of stacking from the effect of the host. The two `instruction.md` files stay byte-identical
    for the task's whole life: any later change to the stacked report (fairfix, upgrade) is copied to
    the control. `check_stack.py` checks it.

**Manifest:** add a `stacking` block containing:
- `pattern`;
- `reader_record`;
- `concepts` (groups of trap ids);
- `history`: advisories A and B with their fix commits, `pinned_commit` and its rule;
- `score_at_build`: copy the `score` of your job's row in `pipelines/stacking/out/stack_scores_ds.tsv` (do NOT run
  `score_stack.py`: it rewrites the shared selection file);
- `control_slug`.

**Exact manifest fields the static conformance check reads (step 5, `pipelines/stacking/3-build-gate/check_stack.py`). Emit these literally — the field NAMES and VALUES below must match, or the build is rejected before the container gate:**

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
  `{ "patch": "checks/miss_<concept>.patch", "kind": "security_fail", "expect": "security_fail", "misses": [<exactly this concept's trap ids>] }`.
  `misses` must be non-empty and be a subset of that concept's trap id group; one such check is required for every group in `stacking.concepts`.
- **Recall (always):** `{ "patch": "checks/upstream_fix.patch", "expect": "security_fail" }` — all published fix commits for the stacked advisories applied together.
- **Recall (H3a and every H3b variant):** also `{ "patch": "checks/upstream_first_fix.patch", "expect": "security_fail" }` — the earlier fix A applied alone.

Every `checks/*.patch` named above must be a real file in the task's `checks/` directory (the container gate then runs each with its `expect`ed outcome). A concept with no `security_fail` miss-check, a trap with no `type`, or a missing recall check/file each fails the conformance check.

**Report back:** also give the concept count, the DeepSeek-type and MiMo-type trap ids, the result of
each history check patch, and the control task's gate result.

Stacked task slug: `stk-vault-secrets-webhook-19004`. Control task slug: `stk-vault-secrets-webhook-19004-control`. Manifest `stacking.reader_record`: `pipelines/stacking/out/reader/h4-19004.json`.
