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

Project root: `/home/mara/cwe-bench`. Task: `assisted-migration-agent-ds`. Pattern: `A`. Track: `injected`.

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
- Advisory: ["GHSA-8G5P-JXP9-457C", "CVE-2026-53475", "GO-2026-6232"]; kubev2v/assisted-migration-agent; CWE-295 improper certificate validation (hardcoded TLS skip-verify on outbound vCenter connections)
- Pinned (vulnerable) commit: e350e7b68e6d3f320cf3ef1d0030e280999533f0. Published fix: b940fec9f5032a0801e994054d30e81d64b2942a.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v2",
 "model": "claude-opus-5-5",
 "entry_id": "16657",
 "advisory_ids": [
  "GHSA-8G5P-JXP9-457C",
  "CVE-2026-53475",
  "GO-2026-6232"
 ],
 "repo": "kubev2v/assisted-migration-agent",
 "pinned_commit": "e350e7b68e6d3f320cf3ef1d0030e280999533f0",
 "fix_commits": [
  "b940fec9f5032a0801e994054d30e81d64b2942a"
 ],
 "trust_decision": {
  "summary": "Whether the agent verifies the vCenter server TLS certificate (against a caller-supplied CA or system roots) is decided at every vCenter connection point; at the pinned commit each one hardcodes skip-verify=true and the API has no field to request verification.",
  "evidence": [
   "pkg/vmware/client.go:35",
   "pkg/vmware/auth.go:78",
   "internal/services/forecaster.go:114",
   "internal/services/forecaster.go:194",
   "internal/services/inspector.go:97",
   "internal/services/rightsizing.go:258",
   "pkg/collector/vsphere.go:118",
   "internal/models/vcenter.go:4-8"
  ]
 },
 "landing_point": {
  "where": "pkg/vmware/client.go:27-35",
  "why": "NewVsphereClient is the obvious shared vCenter client constructor with an `insecure` parameter that callers pass `true`; searching for the summary's 'hardcoded insecure TLS' goes here and to pkg/vmware/auth.go:78 first."
 },
 "fix_sites": [
  {
   "where": "fix.diff:21-43",
   "entry_point": "api/v1 CredsFromAPI (new mapper, used by all 6 handlers below)",
   "module_kind": "API type mapper"
  },
  {
   "where": "fix.diff:496-551",
   "entry_point": "api/v1 and api/v2 VcenterCredentials gain cacert/skipTls (generated types + openapi)",
   "module_kind": "API schema (generated)"
  },
  {
   "where": "internal/handlers/v1/collector.go:29",
   "entry_point": "POST /collector (api/v1/spec.gen.go:1186)",
   "module_kind": "HTTP handler"
  },
  {
   "where": "internal/handlers/v1/forecaster.go:55",
   "entry_point": "POST /forecaster (api/v1/spec.gen.go:1189), optional nested credentials",
   "module_kind": "HTTP handler"
  },
  {
   "where": "internal/handlers/v1/forecaster.go:159",
   "entry_point": "PUT /forecaster/credentials (api/v1/spec.gen.go:1191)",
   "module_kind": "HTTP handler"
  },
  {
   "where": "internal/handlers/v1/inspector.go:42",
   "entry_point": "POST /inspector (api/v1/spec.gen.go:1204), nested credentials",
   "module_kind": "HTTP handler"
  },
  {
   "where": "internal/handlers/v1/inspector.go:110",
   "entry_point": "POST /inspector/credentials (api/v1/spec.gen.go:1205)",
   "module_kind": "HTTP handler"
  },
  {
   "where": "internal/handlers/v1/rightsizing.go:67",
   "entry_point": "POST /rightsizing (api/v1/spec.gen.go:1210), nested credentials",
   "module_kind": "HTTP handler"
  },
  {
   "where": "internal/models/vcenter.go:4-8",
   "entry_point": "models.Credentials gains CACert/SkipTLS + Validate (all routes)",
   "module_kind": "domain model"
  },
  {
   "where": "internal/services/forecaster.go:114",
   "entry_point": "POST /forecaster -> ForecasterService.Start -> NewVsphereClient",
   "module_kind": "service"
  },
  {
   "where": "internal/services/forecaster.go:194",
   "entry_point": "PUT /forecaster/credentials and POST /forecaster -> verifyCredentialsAndPrivileges (own soap.NewClient copy)",
   "module_kind": "service (second implementation of verify)"
  },
  {
   "where": "internal/services/forecaster.go:248-249",
   "entry_point": "POST /forecaster -> resolveCredentials (Validate added)",
   "module_kind": "service"
  },
  {
   "where": "internal/services/inspector.go:97",
   "entry_point": "POST /inspector -> InspectorService.Start",
   "module_kind": "service"
  },
  {
   "where": "internal/services/rightsizing.go:258",
   "entry_point": "POST /rightsizing and POST /collector (auto rightsizing work unit, internal/services/rightsizing.go:466-481) -> buildVSphereConfig",
   "module_kind": "service config builder"
  },
  {
   "where": "pkg/collector/vsphere.go:109-121",
   "entry_point": "POST /collector -> collectorWorkFactory.collect (internal/services/collector_work.go:151) -> createSecret for forklift collector",
   "module_kind": "library wrapper (forklift Secret builder)"
  },
  {
   "where": "pkg/rightsizing/vsphere.go:67-74",
   "entry_point": "POST /rightsizing -> rsig.Connect (internal/services/rightsizing.go:391)",
   "module_kind": "library (separate connect implementation)"
  },
  {
   "where": "pkg/vmware/auth.go:67-78",
   "entry_point": "POST /inspector/credentials (internal/services/inspector.go:150) and POST /collector verify step (pkg/collector/vsphere.go:48-49, internal/services/collector_work.go:137)",
   "module_kind": "library"
  },
  {
   "where": "pkg/vmware/client.go:27-35",
   "entry_point": "POST /forecaster, POST /inspector via NewVsphereClient",
   "module_kind": "library"
  },
  {
   "where": "fix.diff:1507-1542",
   "entry_point": "new pkg/vmware/tls.go NewSoapClient helper (CA pool loading)",
   "module_kind": "library helper"
  }
 ],
 "O1_entry_points": 6,
 "O2_out_of_scope_site": {
  "kind": "second_implementation",
  "where": "pkg/collector/vsphere.go:109-121 (TLS decision serialized as the string \"insecureSkipVerify\" into a k8s Secret consumed by the vendored forklift vSphere collector, a separate connection stack); also pkg/rightsizing/vsphere.go:67-74 (separate Connect with its own soap.NewClient, fed by internal/services/rightsizing.go:258)"
 },
 "O3_reason_to_dismiss": "The rightsizing path documents an explicit, reasoned risk acceptance for skip-verify (internal/services/rightsizing.go:252-257: self-signed on-prem vCenters, SAN mismatch, in-network threat model), and the collector's TLS is performed by third-party forklift code reading a Secret map, so a solver can argue both are 'by design' or 'not our transport'.",
 "O4_distance": {
  "files": 14,
  "packages": 8,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Backwards compatibility: requests with neither cacert nor skipTls must still connect with skip-verify (self-signed vCenters, vcsim-based tests); skipTls=true alone must still work; cacert+skipTls=true must be rejected with 400; the collector->auto-rightsizing flow must carry the same TLS options. Forcing verification everywhere breaks self-signed vCenters and the existing simulator tests.",
  "where": "fix.diff:38-41; fix.diff:650-665; internal/services/rightsizing.go:252-257; internal/services/rightsizing.go:466-481; internal/services/inspector_test.go:24"
 },
 "O6_input_shapes": [
  "credentials as top-level body (POST /collector, PUT /forecaster/credentials, POST /inspector/credentials)",
  "credentials nested under `credentials` (POST /inspector, POST /rightsizing)",
  "optional nested credentials pointer (POST /forecaster), absent -> cached savedCreds reused",
  "cacert only -> verify against supplied PEM pool",
  "skipTls=true only -> skip verify",
  "skipTls=false without cacert -> verify against system roots",
  "neither field -> skip verify (back-compat default)",
  "cacert + skipTls=true -> 400 mutually exclusive",
  "cacert with no valid PEM -> 400"
 ],
 "O7_producer": {
  "kind": "mapper",
  "where": "pkg/collector/vsphere.go:109-121 (createSecret maps Credentials into forklift Secret data; TLS state is produced as the \"insecureSkipVerify\"/\"ca.crt\" keys) and the API->model mapping in each handler, e.g. internal/handlers/v1/collector.go:29",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "POST /inspector builds a vmdetect.Detector with only URL/username/password, so the VM-migration-detective connection to vCenter gets no CA/skip-TLS options; the fix did not touch it.",
   "where": "internal/services/inspector.go:105-110",
   "reason_to_dismiss": "Detector is an external module (github.com/kubev2v/vm-migration-detective) with its own config type; looks like a neighbouring feature / dependency concern.",
   "distance": "same file as fixed inspector site (internal/services/inspector.go:97); TLS behaviour lives in an external module not in the tree",
   "present_in_latest": "unknown",
   "latest_where": ""
  }
 ],
 "O8b_injection_room": [
  {
   "where": "pkg/crypto/crypto.go:167-171",
   "sibling": "Encrypt/Decrypt rebuild Credentials with only URL/Username/Password, dropping CACert/SkipTLS across the encrypted save/reload boundary.",
   "why_realistic": "CredentialsService (internal/services/credentials.go:109-130) was added one commit earlier for saved per-source credentials; a maintainer wiring saved creds into the collector/forecaster would naturally reuse these field-by-field copies and the 3-column store (internal/store/credentials.go:85-86)."
  },
  {
   "where": "internal/services/forecaster.go:252-261",
   "sibling": "Forecaster caches verified creds in savedCreds and reuses them when POST /forecaster omits credentials; a cache that stored only URL/user/password would silently revert to the skip-verify default.",
   "why_realistic": "An in-memory reuse path already exists; a field-subset copy or a later persisted cache is a plausible maintainer change."
  },
  {
   "where": "internal/services/rightsizing.go:466-481",
   "sibling": "Collector-triggered auto rightsizing rebuilds RightsizingParams from collector creds; a variant that constructs a fresh Credentials{URL,User,Pass} would lose TLS options.",
   "why_realistic": "Cross-service work-unit closure far from the handlers; easy to rebuild params instead of passing the struct."
  }
 ],
 "O9_family": "CWE-295 improper certificate validation (hardcoded TLS skip-verify on outbound vCenter connections)",
 "O9_dos": false,
 "O10_build": {
  "language": "Go",
  "toolchain": "Go 1.25 (go.mod:3), Makefile, ginkgo/gomega tests",
  "services": [],
  "offline_after_build": null,
  "project_tests": "internal/handlers/v1/*_test.go (collector, forecaster, inspector, rightsizing handler suites), internal/services/inspector_test.go (vcsim-style https://localhost:8989/sdk at internal/services/inspector_test.go:24), internal/services/rightsizing_test.go, internal/services/collector_test.go"
 },
 "O11_fix_minutes": 60,
 "O12_red_flags": [],
 "O13_recall_risk": "low",
 "pattern_fit": "A",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "api/v1/extension.go, api/v1/types.gen.go, api/v2/types.gen.go, internal/handlers/v1/{collector,forecaster,inspector,rightsizing}.go, internal/models/vcenter.go, internal/services/{forecaster,inspector,rightsizing}.go, pkg/collector/vsphere.go, pkg/rightsizing/vsphere.go, pkg/vmware/{auth,client,tls}.go",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 0,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Flip the hardcoded `true` in pkg/vmware (client.go/auth.go) to a SkipTLS field and stop, missing the forecaster's own soap.NewClient copy, the rightsizing package's Insecure:true config, and the forklift Secret's \"insecureSkipVerify\" string."
 },
 "out_of_scope_notes": [
  "api/v2 declares StartCollector with VcenterCredentials (api/v2/types.gen.go:533) but no v2 handler exists in internal/handlers at the pinned commit.",
  "test/e2e/* clients use InsecureSkipVerify against the agent's own HTTPS server; unrelated test code.",
  "pkg/vmware/diskmanager_test.go:43 calls NewVsphereClient(..., true); test only."
 ],
 "unverified": [
  "Whether vm-migration-detective's Detector actually opens a TLS connection to vCenter and how it verifies certs (external module, not in tree); O8 route depends on it.",
  "Whether forklift's vSphere collector honours the \"ca.crt\" Secret key the fix adds (vendored module not in tree).",
  "Repo size in MB (not measured).",
  "offline_after_build: unit tests appear to use mocks or a local simulator, but not confirmed without running.",
  "present_in_latest for the O8 route: no latest release supplied."
 ]
}
  ```
- Published fix sites:   - fix.diff:21-43 — entry point: api/v1 CredsFromAPI (new mapper, used by all 6 handlers below) [API type mapper]
  - fix.diff:496-551 — entry point: api/v1 and api/v2 VcenterCredentials gain cacert/skipTls (generated types + openapi) [API schema (generated)]
  - internal/handlers/v1/collector.go:29 — entry point: POST /collector (api/v1/spec.gen.go:1186) [HTTP handler]
  - internal/handlers/v1/forecaster.go:55 — entry point: POST /forecaster (api/v1/spec.gen.go:1189), optional nested credentials [HTTP handler]
  - internal/handlers/v1/forecaster.go:159 — entry point: PUT /forecaster/credentials (api/v1/spec.gen.go:1191) [HTTP handler]
  - internal/handlers/v1/inspector.go:42 — entry point: POST /inspector (api/v1/spec.gen.go:1204), nested credentials [HTTP handler]
  - internal/handlers/v1/inspector.go:110 — entry point: POST /inspector/credentials (api/v1/spec.gen.go:1205) [HTTP handler]
  - internal/handlers/v1/rightsizing.go:67 — entry point: POST /rightsizing (api/v1/spec.gen.go:1210), nested credentials [HTTP handler]
  - internal/models/vcenter.go:4-8 — entry point: models.Credentials gains CACert/SkipTLS + Validate (all routes) [domain model]
  - internal/services/forecaster.go:114 — entry point: POST /forecaster -> ForecasterService.Start -> NewVsphereClient [service]
  - internal/services/forecaster.go:194 — entry point: PUT /forecaster/credentials and POST /forecaster -> verifyCredentialsAndPrivileges (own soap.NewClient copy) [service (second implementation of verify)]
  - internal/services/forecaster.go:248-249 — entry point: POST /forecaster -> resolveCredentials (Validate added) [service]
  - internal/services/inspector.go:97 — entry point: POST /inspector -> InspectorService.Start [service]
  - internal/services/rightsizing.go:258 — entry point: POST /rightsizing and POST /collector (auto rightsizing work unit, internal/services/rightsizing.go:466-481) -> buildVSphereConfig [service config builder]
  - pkg/collector/vsphere.go:109-121 — entry point: POST /collector -> collectorWorkFactory.collect (internal/services/collector_work.go:151) -> createSecret for forklift collector [library wrapper (forklift Secret builder)]
  - pkg/rightsizing/vsphere.go:67-74 — entry point: POST /rightsizing -> rsig.Connect (internal/services/rightsizing.go:391) [library (separate connect implementation)]
  - pkg/vmware/auth.go:67-78 — entry point: POST /inspector/credentials (internal/services/inspector.go:150) and POST /collector verify step (pkg/collector/vsphere.go:48-49, internal/services/collector_work.go:137) [library]
  - pkg/vmware/client.go:27-35 — entry point: POST /forecaster, POST /inspector via NewVsphereClient [library]
  - fix.diff:1507-1542 — entry point: new pkg/vmware/tls.go NewSoapClient helper (CA pool loading) [library helper]
- Uncovered routes to confirm (pattern B): none
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

## Environment (`tasks/assisted-migration-agent-ds/environment/Dockerfile`)
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

## Report to the solver (`tasks/assisted-migration-agent-ds/instruction.md`)
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

## Tests (`tasks/assisted-migration-agent-ds/tests/`)
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
- **Wrong-fix patches** go in `build/assisted-migration-agent-ds/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/assisted-migration-agent-ds/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/assisted-migration-agent-ds/manifest.json`:**
- `slug`, `candidate`;
- `pattern`: `A`;
- `builder_prompt_version`: `build-v1`;
- `"strict_gate": true`;
- `verified`: entry point, sites, routes, services, project tests run;
- `leak_terms`, `patch_checks`, `wrong_fix_catalogue`;
- `traps`: one entry per lever, with `shape`, `where` (file:line), `security_tests`,
  `coupled_functional_tests`, `security_fail_patch`, and `realistic_because` (for pattern B: "real,
  unmodified upstream code");
- `status`.

**Also in `build/assisted-migration-agent-ds/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py assisted-migration-agent-ds --only static
python3 -I builder/gate.py assisted-migration-agent-ds --only nop
python3 -I builder/gate.py assisted-migration-agent-ds --only oracle
python3 -I builder/gate.py assisted-migration-agent-ds --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/assisted-migration-agent-ds/`;
  - edit only `tasks/assisted-migration-agent-ds/`, `build/assisted-migration-agent-ds/` and, for pattern B, the register;
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
