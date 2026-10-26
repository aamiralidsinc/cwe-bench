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

Project root: `/home/mara/cwe-bench`. Task: `vault-secrets-webhook-s2`. Pattern: `B`. Track: `injected`.

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
- Advisory: ["GHSA-R2V3-8GWF-7GHM", "CVE-2026-54725", "GO-2026-6160"]; bank-vaults/vault-secrets-webhook; CWE-918 server-side request forgery — object-supplied Vault address (and object-supplied TLS-skip) drives the webhook's outbound client with an operator-minted ServiceAccount token; the skip-verify half is also CWE-295 improper certificate validation
- Pinned (vulnerable) commit: 71cfbb8907b2b7197e892570975428a447e615be. Published fix: 76db45976fee0f54cafd94dffa425e6b542f65a0.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v2",
 "model": "deepseek-flash[1m]",
 "entry_id": "19004",
 "advisory_ids": [
  "GHSA-R2V3-8GWF-7GHM",
  "CVE-2026-54725",
  "GO-2026-6160"
 ],
 "repo": "bank-vaults/vault-secrets-webhook",
 "pinned_commit": "71cfbb8907b2b7197e892570975428a447e615be",
 "fix_commits": [
  "76db45976fee0f54cafd94dffa425e6b542f65a0"
 ],
 "trust_decision": {
  "summary": "Whether the webhook trusts object-supplied Vault connection settings: pkg/webhook/webhook.go:196-221 must decide, before the client address is applied (webhook.go:204) and before a ServiceAccount token is minted for the annotation-named SA and attached to the client (webhook.go:285-302), that an address coming from the object annotation has passed an operator allowlist plus SSRF guard (fix.diff:79-87), and pkg/webhook/config.go:147-151 must decide that an object-supplied vault-skip-verify is ignored unless the operator opted in (fix.diff:28-33). Operator-configured vault_addr is trusted and must not be forced through the object policy (fix.diff:60-70).",
  "evidence": [
   "pkg/webhook/config.go:107-111",
   "pkg/webhook/config.go:147-151",
   "pkg/webhook/webhook.go:204-207",
   "pkg/webhook/webhook.go:285-302",
   "fix.diff:60-70",
   "fix.diff:79-87"
  ]
 },
 "landing_point": {
  "where": "pkg/webhook/config.go:107-111",
  "why": "The summary names the vault-addr annotation; this is the only place it is read, and the value goes straight into VaultConfig.Addr and from there to clientConfig.Address (pkg/webhook/webhook.go:204) and the SA-token auth exchange."
 },
 "fix_sites": [
  {
   "where": "fix.diff:13",
   "entry_point": "VaultConfig construction, reached from all four HTTP routes /pods, /secrets, /configmaps, /objects (main.go:168-171) through VaultSecretsMutator (pkg/webhook/webhook.go:53)",
   "module_kind": "config struct field (provenance flag)"
  },
  {
   "where": "fix.diff:21",
   "entry_point": "parseVaultConfig (pkg/webhook/config.go:94), the annotation config loader for every admission request",
   "module_kind": "annotation config loader"
  },
  {
   "where": "fix.diff:28-33",
   "entry_point": "parseVaultConfig, vault-skip-verify branch (pkg/webhook/config.go:147-151), all four routes",
   "module_kind": "annotation config loader / policy gate"
  },
  {
   "where": "fix.diff:38-40",
   "entry_point": "process start: main.go:43-45 init() -> SetConfigDefaults (pkg/webhook/config.go:467)",
   "module_kind": "viper defaults loader"
  },
  {
   "where": "fix.diff:60-70",
   "entry_point": "public method MutatingWebhook.newVaultClient (pkg/webhook/webhook.go:196), reached from /secrets (pkg/webhook/secret.go:96), /configmaps (pkg/webhook/configmap.go:49), /objects (pkg/webhook/object.go:127)",
   "module_kind": "policy assembly in the vault client factory"
  },
  {
   "where": "fix.diff:79-87",
   "entry_point": "same newVaultClient; the guard runs before clientConfig.Address (pkg/webhook/webhook.go:204) and before the TokenRequest mint (pkg/webhook/webhook.go:285-296)",
   "module_kind": "outbound client construction (sink guard)"
  }
 ],
 "O1_entry_points": 3,
 "O2_out_of_scope_site": {
  "kind": "second_implementation",
  "where": "pkg/webhook/registry.go:185-188 \u2014 the object-supplied registry-skip-verify annotation (pkg/webhook/config.go:283-287) sets InsecureSkipVerify on the webhook's outbound registry transport, reached from /pods via pkg/webhook/pod.go:279 -> registry.go:162-196; the same 'object annotation must not weaken the webhook's outbound TLS without operator opt-in' check the fix adds for the Vault client is not applied here"
 },
 "O3_reason_to_dismiss": "registry-skip-verify is a separate documented feature for private registries with self-signed certificates (pkg/common/common.go:29), a different annotation and a different outbound connection from the Vault one the advisory names, so it is a different control and needs no change.",
 "O4_distance": {
  "files": 4,
  "packages": 2,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "The vault-addr and vault-skip-verify annotations are a supported, documented feature that must keep working for every object kind: they are written verbatim into VAULT_ADDR/VAULT_SKIP_VERIFY for injected containers (pkg/webhook/pod.go:90, 94) and into the vault-agent/consul-template containers (pkg/webhook/pod.go:330, 334), and the e2e manifests point at a non-default cluster address (e2e/test/deployment.yaml:15, e2e/test/configmap.yaml:6, e2e/test/secret.yaml:6; documented at deploy/charts/vault-secrets-webhook/README.md:15). An over-broad fix that rejects or ignores the annotation in parseVaultConfig, or validates the operator default https://vault:8200 against an empty allowlist, breaks pod injection and every e2e fixture.",
  "where": "pkg/webhook/pod.go:87-96"
 },
 "O6_input_shapes": [
  "annotation present with a non-allowlisted host (https://evil.attacker.com) -> rejected",
  "cloud metadata literal (http://169.254.169.254/latest/meta-data/) -> rejected",
  "userinfo-bearing URL (https://attacker:pw@vault.prod.svc:8200) even when the host is allowlisted -> rejected",
  "non-http(s) scheme (file:///etc/passwd) -> rejected",
  "query string, fragment, missing host, empty value -> rejected",
  "metadata hostnames localhost / metadata.google.internal -> always rejected, even with AllowPrivate",
  "non-standard IPv4 literals: decimal 2130706433, octal 0177.0.0.1, hex 0x7f000001 -> rejected as ambiguous numeric hosts",
  "loopback / link-local / private / CGNAT (100.64.0.0/10) IP literals -> rejected unless vault_allow_private_addr",
  "allowlisted exact address (normalised scheme://host/path) -> accepted",
  "vault-skip-verify=true with no operator opt-in -> ignored and falls back to the operator default; with vault_allow_object_skip_verify=true -> honoured",
  "operator channel: annotation absent -> vault_addr / vault_skip_verify used and not subjected to the object policy"
 ],
 "O7_producer": {
  "kind": "config_loader",
  "where": "pkg/webhook/config.go:467-514 SetConfigDefaults fills viper; the check reads it directly at fix.diff:60-70 (vaultAddrPolicy) and pkg/common/policy.go:44-56 (ResolveObjectSkipVerify), so the new vault_addr_allowlist / vault_allow_object_skip_verify / vault_allow_private_addr keys are not load-bearing (unset -> empty/false)",
  "check_calls_producer": true
 },
 "O8_uncovered_routes": [
  {
   "route": "/pods: vault-addr and vault-skip-verify are propagated unchecked into the mutated pod's VAULT_ADDR/VAULT_SKIP_VERIFY env; the fix's check lives only in newVaultClient, which the pod path never calls",
   "where": "pkg/webhook/pod.go:87-96",
   "reason_to_dismiss": "the webhook never dials that address \u2014 the mutated workload does, with the tenant's own ServiceAccount \u2014 so no credential or trust boundary of the webhook is crossed, and the annotation is a documented feature",
   "distance": "same package, sibling file pkg/webhook/pod.go (also pkg/webhook/pod.go:327-335)",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "/pods -> image registry: the object's registry-skip-verify annotation disables TLS verification on the webhook's outbound registry call",
   "where": "pkg/webhook/registry.go:185-188",
   "reason_to_dismiss": "separate documented feature for self-signed private registries; the advisory is about the Vault address, not the registry transport",
   "distance": "same package, sibling file; producer at pkg/webhook/config.go:283-287, consumer at pkg/webhook/pod.go:279 -> registry.go:162-196",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "Vault TLS trust: the object's vault-tls-secret annotation selects the CA pool (RootCAs) used for the webhook's Vault connection, replacing the system roots",
   "where": "pkg/webhook/webhook.go:213-235",
   "reason_to_dismiss": "the Secret is read from the webhook's own namespace (webhook.go:214-215), so a tenant cannot plant the CA \u2014 only an existing operator-created secret can be named",
   "distance": "same file as the sink; producer at pkg/webhook/config.go:153-157",
   "present_in_latest": "unknown",
   "latest_where": ""
  }
 ],
 "O8b_injection_room": [
  {
   "where": "pkg/webhook/registry.go:185-188",
   "sibling": "a second object-controlled TLS behaviour on another outbound transport (registry skip-verify, or a registry/namespace allowlist)",
   "why_realistic": "the project already ships a per-object registry-skip-verify annotation and its own transport options right next to the Vault one; a maintainer hardening object-supplied connection settings would harden this too"
  },
  {
   "where": "pkg/webhook/webhook.go:213-235",
   "sibling": "object-supplied trust material for the same Vault connection (vault-tls-secret / a server-name or CA-PEM annotation), gated the same way as skip-verify",
   "why_realistic": "the TLSSecret branch sits inside newVaultClient beside the skip-verify handling and already consumes an object annotation"
  },
  {
   "where": "pkg/webhook/webhook.go:252-257",
   "sibling": "object-supplied vault-path / vault-auth-method used unvalidated in the client options",
   "why_realistic": "a maintainer treating all Vault connection settings from annotations as untrusted would extend the same allowlist policy to these two fields"
  },
  {
   "where": "pkg/webhook/pod.go:327-335",
   "sibling": "the pod path propagating VAULT_ADDR/VAULT_SKIP_VERIFY into every mutated container without the provenance check",
   "why_realistic": "the same VaultConfig fields are written into the mutated object here, so a second implementation of the policy is a natural next edit"
  }
 ],
 "O9_family": "CWE-918 server-side request forgery \u2014 object-supplied Vault address (and object-supplied TLS-skip) drives the webhook's outbound client with an operator-minted ServiceAccount token; the skip-verify half is also CWE-295 improper certificate validation",
 "O9_dos": false,
 "O10_build": {
  "language": "Go",
  "toolchain": "Go 1.26.3 (.go-version:1, go.mod:3); `go build -race -o build/webhook .` (Makefile:42-45); modules fetched via go.mod/go.sum, no vendor dir and no code generation",
  "services": [],
  "offline_after_build": true,
  "project_tests": "`go test -race -v ./...` (Makefile:65-67): pkg/webhook/webhook_test.go:33 TestNewVaultClientMetrics, pkg/webhook/pod_test.go, pkg/webhook/configmap_test.go, pkg/webhook/registry_test.go (fake.NewClientset + httptest, no external service), and pkg/common/addr_test.go + pkg/common/policy_test.go \u2014 note the guard's full expected behaviour is already specified in-tree at the pinned commit although ValidateObjectAddr/ResolveObjectSkipVerify have no production caller. e2e (`make test-e2e`, Makefile:69-75) needs a kind cluster and a Vault deployment and is not offline."
 },
 "O11_fix_minutes": 35,
 "O12_red_flags": [
  "tiny_repo"
 ],
 "O13_recall_risk": "medium",
 "pattern_fit": "B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "pkg/webhook/config.go, pkg/webhook/webhook.go",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 0,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Reject or ignore the vault-addr annotation in parseVaultConfig (or call ValidateObjectAddr unconditionally in newVaultClient), which rejects the operator default https://vault:8200 and strips the annotation from pods and e2e fixtures, while leaving registry-skip-verify and vault-tls-secret ungated."
 },
 "out_of_scope_notes": [],
 "unverified": [
  "Build and test runs were not performed (no shell in this session); O10 is read from go.mod:3, .go-version:1, Makefile:42-75 and the test files.",
  "repo_mb not measured; tiny_repo is inferred from the inventory (20 Go files, largest pkg/webhook/pod_test.go ~2000 lines, source far under 5 MB).",
  "No latest release or code provided (\"none\"), so every O8 route has present_in_latest=unknown and latest_where empty.",
  "Whether hidden behaviour tests treat the registry-skip-verify and pod-env propagation routes as in scope is unknown; they are recorded as O8 because the advisory text names only the Vault connection.",
  "The 'cluster-wide SA token theft' half of the summary was not established: pkg/webhook/webhook.go:259-302 mints a token only in ar.Namespace even though the ClusterRole grants serviceaccounts/token cluster-wide (deploy/charts/vault-secrets-webhook/templates/webhook-rbac.yaml:49-54), and the fix changes only the ordering relative to the address check, not the token path."
 ]
}
  ```
- Published fix sites:   - fix.diff:13 — entry point: VaultConfig construction, reached from all four HTTP routes /pods, /secrets, /configmaps, /objects (main.go:168-171) through VaultSecretsMutator (pkg/webhook/webhook.go:53) [config struct field (provenance flag)]
  - fix.diff:21 — entry point: parseVaultConfig (pkg/webhook/config.go:94), the annotation config loader for every admission request [annotation config loader]
  - fix.diff:28-33 — entry point: parseVaultConfig, vault-skip-verify branch (pkg/webhook/config.go:147-151), all four routes [annotation config loader / policy gate]
  - fix.diff:38-40 — entry point: process start: main.go:43-45 init() -> SetConfigDefaults (pkg/webhook/config.go:467) [viper defaults loader]
  - fix.diff:60-70 — entry point: public method MutatingWebhook.newVaultClient (pkg/webhook/webhook.go:196), reached from /secrets (pkg/webhook/secret.go:96), /configmaps (pkg/webhook/configmap.go:49), /objects (pkg/webhook/object.go:127) [policy assembly in the vault client factory]
  - fix.diff:79-87 — entry point: same newVaultClient; the guard runs before clientConfig.Address (pkg/webhook/webhook.go:204) and before the TokenRequest mint (pkg/webhook/webhook.go:285-296) [outbound client construction (sink guard)]
- Uncovered routes to confirm (pattern B):   - pkg/webhook/pod.go:87-96 — /pods: vault-addr and vault-skip-verify are propagated unchecked into the mutated pod's VAULT_ADDR/VAULT_SKIP_VERIFY env; the fix's check lives only in newVaultClient, which the pod path never calls (reason to dismiss: the webhook never dials that address — the mutated workload does, with the tenant's own ServiceAccount — so no credential or trust boundary of the webhook is crossed, and the annotation is a documented feature; still in latest: unknown)
  - pkg/webhook/registry.go:185-188 — /pods -> image registry: the object's registry-skip-verify annotation disables TLS verification on the webhook's outbound registry call (reason to dismiss: separate documented feature for self-signed private registries; the advisory is about the Vault address, not the registry transport; still in latest: unknown)
  - pkg/webhook/webhook.go:213-235 — Vault TLS trust: the object's vault-tls-secret annotation selects the CA pool (RootCAs) used for the webhook's Vault connection, replacing the system roots (reason to dismiss: the Secret is read from the webhook's own namespace (webhook.go:214-215), so a tenant cannot plant the CA — only an existing operator-created secret can be named; still in latest: unknown)
- Design plan from the lead: No lead plan is provided for this task — you are the lead as well as the builder. Using the Design section above and the screener record, design the task yourself and WRITE YOUR PLAN in `notes.md` BEFORE you build:
  - choose the main lever and at least one more, each with a DIFFERENT reason a solver would dismiss or skip it. The main lever must be HOW-type (its fix needs the mechanism understood: a producer the check never calls, a coupled must-keep-working value, a shape a plausible check mishandles, a route where the protection never existed); another entry point or a planted copy is only an extra;
  - decide the sites, routes and input shapes the security tests will cover;
  - identify the coupled must-keep-working behaviour next to each lever, for the functional tests;
  - for the injected track: decide the realistic sibling gap(s) to add — each must be code a maintainer could plausibly have left, reachable through the real entry point, covered by the task's one general property (never by a sentence of its own), and placed where the published fix never touches. First list EVERY possible sibling site and route you can find (the screener's O8/O8b leads plus your own search of the code). Then pick 2–4 of them: the most complex and hardest to find of all the candidates (how-type over where-type, far from where the report leads, with a plausible reason to dismiss), each with a different reason a solver would skip it. Record the full candidate list, and why each pick beat the others, in notes.md;
  - write the security property ONCE, in general terms over the protected data or outcome, before choosing routes. Every route and sibling must fall under it as written; the report must not describe where any of them lives;
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

## Environment (`tasks/vault-secrets-webhook-s2/environment/Dockerfile`)
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

## Report to the solver (`tasks/vault-secrets-webhook-s2/instruction.md`)
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

## Tests (`tasks/vault-secrets-webhook-s2/tests/`)
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
- **Wrong-fix patches** go in `build/vault-secrets-webhook-s2/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/vault-secrets-webhook-s2/`:**
- `instruction.md`;
- `task.toml`, from `common/builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/vault-secrets-webhook-s2/manifest.json`:**
- `slug`, `candidate`;
- `pattern`: `B`;
- `builder_prompt_version`: `build-v1`;
- `"strict_gate": true`;
- `verified`: entry point, sites, routes, services, project tests run;
- `leak_terms`, `patch_checks`, `wrong_fix_catalogue`;
- `traps`: one entry per lever, with `shape`, `where` (file:line), `security_tests`,
  `coupled_functional_tests`, `security_fail_patch`, and `realistic_because` (for pattern B: "real,
  unmodified upstream code");
- `status`.

**Also in `build/vault-secrets-webhook-s2/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `common/builder/templates/` and `common/trial/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I common/gate/gate.py vault-secrets-webhook-s2 --only static
python3 -I common/gate/gate.py vault-secrets-webhook-s2 --only nop
python3 -I common/gate/gate.py vault-secrets-webhook-s2 --only oracle
python3 -I common/gate/gate.py vault-secrets-webhook-s2 --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/vault-secrets-webhook-s2/`;
  - edit only `tasks/vault-secrets-webhook-s2/`, `build/vault-secrets-webhook-s2/` and, for pattern B, the register;
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
