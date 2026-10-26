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

Project root: `/home/mara/cwe-bench`. Task: `bifrost-s2`. Pattern: `B`. Track: `injected`.

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
- Advisory: ["GHSA-W98G-5W9P-P3RC", "CVE-2026-55245", "GO-2026-6320"]; maximhq/bifrost; CWE-918 server-side request forgery via an incomplete IP deny-list (CGNAT, IPv6 transition addresses, deprecated site-local)
- Pinned (vulnerable) commit: 9dda29f586ff8c989c03264aedfbb6914b00fbad. Published fix: 54ec431fc5255ff42c36420d88549477e0b33d89.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v2",
 "model": "deepseek-flash[1m]",
 "entry_id": "19592",
 "advisory_ids": [
  "GHSA-W98G-5W9P-P3RC",
  "CVE-2026-55245",
  "GO-2026-6320"
 ],
 "repo": "maximhq/bifrost",
 "pinned_commit": "9dda29f586ff8c989c03264aedfbb6914b00fbad",
 "fix_commits": [
  "54ec431fc5255ff42c36420d88549477e0b33d89"
 ],
 "trust_decision": {
  "summary": "At dial time, FetchAndEncodeURL resolves the request-supplied host and trusts isPublicIP's verdict on every resolved address, refusing the fetch unless all are public; the trust decision is a hand-written address deny-list, not a positive allow-list.",
  "evidence": [
   "core/providers/utils/fetch.go:50-54",
   "core/providers/utils/fetch.go:107-118"
  ]
 },
 "landing_point": {
  "where": "core/providers/utils/fetch.go:107",
  "why": "The advisory names isPublicIP by name; anyone reading the summary opens this function first and sees one netip predicate chain with no CGNAT, no IPv6-transition unwrapping and no fec0::/10 case."
 },
 "fix_sites": [
  {
   "where": "core/providers/utils/fetch.go:107-118",
   "entry_point": "POST /v1/chat/completions (Bedrock image_url and file.url document blocks; Vertex-Anthropic file.url document blocks) and POST /v1/responses (Bedrock image_url via responses.go:3264,4251) -> FetchAndEncodeURL",
   "module_kind": "core provider-utils library (internal Go package, module github.com/maximhq/bifrost/core)"
  }
 ],
 "O1_entry_points": 3,
 "O2_out_of_scope_site": {
  "kind": "second_implementation",
  "where": "core/providers/utils/utils.go:294-304"
 },
 "O3_reason_to_dismiss": "ConfigureDialer's deny-list guards operator-configured provider base URLs over the fasthttp transport, and it deliberately permits loopback plus (with AllowPrivateNetwork) RFC 1918 for self-hosted providers such as Ollama/vLLM/SGL, so it reads as an intentionally narrower legacy path that the fetch.go advisory never covered.",
 "O4_distance": {
  "files": 6,
  "packages": 5,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Public IPv4 reached through 6to4 or NAT64 must remain fetchable (NAT64 is the normal path from IPv6-only clusters to the IPv4 internet); the correct fix unwraps the embedded IPv4 and re-checks it rather than blocking 2002::/16 or 64:ff9b::/96 wholesale, so an over-broad prefix block breaks legitimate public fetches (the fix's own test keeps 2002:0808:0808:: allowed).",
  "where": "core/providers/utils/fetch.go:107"
 },
 "O6_input_shapes": [
  "4-byte net.IP IPv4 (CGNAT 100.64.0.0/10, 255.255.255.255)",
  "16-byte IPv4-mapped IPv6 (collapsed by Unmap)",
  "6to4 2002::/16 carrying an IPv4 in bytes 2..5",
  "NAT64 well-known 64:ff9b::/96 carrying an IPv4 in bytes 12..15",
  "NAT64 local-use 64:ff9b:1::/48 with RFC 6052 u-octet skipped (bytes 6,7,9,10)",
  "deprecated IPv6 site-local fec0::/10",
  "hostname form resolved by net.Resolver versus a bracketed IPv6 literal in the URL"
 ],
 "O7_producer": {
  "kind": "handler",
  "where": "core/providers/bedrock/utils.go:898",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "All provider outbound traffic (including user-chosen provider base URLs saved through POST /api/providers) goes through the fasthttp dial closure, whose deny-list uses network.IsPrivateIP and has no CGNAT, 6to4/NAT64 unwrapping or fec0::/10 case.",
   "where": "core/providers/utils/utils.go:302",
   "reason_to_dismiss": "Base URLs are operator configuration, not request input, and the path intentionally allows loopback and RFC 1918 for local providers.",
   "distance": "same package as the fix, different transport (fasthttp) and different public function; shared classifier in core/network",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "Shared lower-level classifier network.IsPrivateIP (used by both ValidateExternalURL and ConfigureDialer) returns false for CGNAT, 6to4/NAT64-wrapped internal IPv4 and fec0::/10.",
   "where": "core/network/utils.go:43",
   "reason_to_dismiss": "It is a generic 'private address' helper with its own callers, not the SSRF check named in the advisory; hardening it would also change provider connectivity policy.",
   "distance": "one package away (core/network), reached only through callers",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "Pricing URL is fetched with a bare http.Client (no dial-time IP check) after only a save-time ValidateExternalURL(..., allowPrivateNetwork=true) that skips loopback entirely.",
   "where": "framework/modelcatalog/sync.go:130-138",
   "reason_to_dismiss": "Pricing is operator-supplied framework configuration fetched at startup, and the save-time validator is the intended control for it.",
   "distance": "separate Go module (framework), different package, different client stack (net/http with default transport)",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "Model-parameters URL takes the same bare-client path with only save-time ValidateExternalURL.",
   "where": "framework/modelcatalog/sync.go:514-522",
   "reason_to_dismiss": "Same config-not-input argument; a neighbouring feature to pricing sync.",
   "distance": "single file from the pricing route, framework module",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "Admin config save performs a server-side GET of the submitted PricingURL/ModelParametersURL with a bare http.Client after ValidateExternalURL(rawURL, true), which passes loopback, CGNAT and 6to4/NAT64-wrapped internal addresses.",
   "where": "transports/bifrost-http/handlers/config.go:1004-1008",
   "reason_to_dismiss": "Admin-only endpoint whose whole purpose is to probe reachability, so it looks intentional that it is not locked down like the model-facing fetcher.",
   "distance": "different module (transports) and different package from the fix",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "Provider base-URL validation on create/update goes through ValidateExternalURL, which skips loopback and never unwraps IPv6 transition addresses.",
   "where": "core/utils.go:504-518",
   "reason_to_dismiss": "loopback is skipped by design for local deployments and AllowPrivateNetwork is an explicit opt-in, so the weakness looks like intended policy.",
   "distance": "different package (core root package bifrost) from the landing point",
   "present_in_latest": "unknown",
   "latest_where": ""
  }
 ],
 "O8b_injection_room": [
  {
   "where": "core/network/utils.go:43",
   "sibling": "A second 'is this address internal?' classifier kept next to the subnet table",
   "why_realistic": "The tree already carries two address classifiers (fetch.go's netip predicate chain and network.IsPrivateIP over net.IP), so a maintainer hardening one and not the other is exactly the drift we see here."
  },
  {
   "where": "core/providers/utils/utils.go:258",
   "sibling": "A dial-time guard for the fasthttp provider clients that must stay loopback-permissive",
   "why_realistic": "Every provider constructs its client through ConfigureProxy/ConfigureDialer/ConfigureTLS, so a security fix author would plausibly add the check there and then have to keep local providers working."
  },
  {
   "where": "core/providers/bedrock/utils.go:1171",
   "sibling": "A per-provider URL inliner wrapper (sanitize image URL, then fetch)",
   "why_realistic": "Providers whose upstream only accepts inline bytes each grew their own inliner, so a new provider would get a copy of this wrapper."
  },
  {
   "where": "framework/modelcatalog/sync.go:114",
   "sibling": "A config-URL loader that fetches with a plain http.Client and relies on the save-time validator",
   "why_realistic": "The pricing/model-parameters loaders already do this twice in one file, so a third loader is a natural extension."
  }
 ],
 "O9_family": "CWE-918 server-side request forgery via an incomplete IP deny-list (CGNAT, IPv6 transition addresses, deprecated site-local)",
 "O9_dos": false,
 "O10_build": {
  "language": "Go",
  "toolchain": "go 1.26.3 declared in core/go.mod; multi-module workspace by convention (core, framework, transports, plugins, cli each have their own go.mod and there is no go.work), so each module builds and tests independently",
  "services": [],
  "offline_after_build": true,
  "project_tests": "core/providers/utils/dialer_test.go (TestConfigureDialer_SSRFProtection, _SSRFProxyBypass, _SSRFZeroTimeout, _SSRFMultiIPAllFail), core/utils_test.go (TestValidateExternalURL, TestIsPrivateIP), transports/bifrost-http/handlers/utils_test.go (checkURLAccessibility); the fix adds a new core/providers/utils/fetch_test.go (TestIsPublicIP) which does not exist at the pinned commit"
 },
 "O11_fix_minutes": 60,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "core/providers/utils/fetch.go",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Block 100.64.0.0/10, 2002::/16, 64:ff9b::/96 and fec0::/10 inside isPublicIP only, which both kills legitimate public 6to4/NAT64 targets and leaves network.IsPrivateIP, the ConfigureDialer dial path and the pricing/config URL fetchers unhardened."
 },
 "out_of_scope_notes": [
  "Sighted outside this advisory's scope and not pursued: the pricing/model-parameters loaders accept file:// URLs and read arbitrary local paths (framework/modelcatalog/sync.go:124-128, :508-512) and checkURLAccessibility stats arbitrary local files (transports/bifrost-http/handlers/config.go:994-1002); these are path/host-file reads, a different weakness family from the SSRF deny-list."
 ],
 "unverified": [
  "Repository size in MB (du/tree unavailable in this session); file count suggests a mid-size multi-module repo, neither under 5 MB source nor over 1.5 GB.",
  "Whether the O8 routes are still present in the latest release: no release tree was supplied, so present_in_latest is unknown for every route.",
  "That hidden behavioural tests can reach any of the O8 config-driven routes offline without an admin API token; only the isPublicIP classifier itself is trivially unit-testable."
 ]
}
  ```
- Published fix sites:   - core/providers/utils/fetch.go:107-118 — entry point: POST /v1/chat/completions (Bedrock image_url and file.url document blocks; Vertex-Anthropic file.url document blocks) and POST /v1/responses (Bedrock image_url via responses.go:3264,4251) -> FetchAndEncodeURL [core provider-utils library (internal Go package, module github.com/maximhq/bifrost/core)]
- Uncovered routes to confirm (pattern B):   - core/providers/utils/utils.go:302 — All provider outbound traffic (including user-chosen provider base URLs saved through POST /api/providers) goes through the fasthttp dial closure, whose deny-list uses network.IsPrivateIP and has no CGNAT, 6to4/NAT64 unwrapping or fec0::/10 case. (reason to dismiss: Base URLs are operator configuration, not request input, and the path intentionally allows loopback and RFC 1918 for local providers.; still in latest: unknown)
  - core/network/utils.go:43 — Shared lower-level classifier network.IsPrivateIP (used by both ValidateExternalURL and ConfigureDialer) returns false for CGNAT, 6to4/NAT64-wrapped internal IPv4 and fec0::/10. (reason to dismiss: It is a generic 'private address' helper with its own callers, not the SSRF check named in the advisory; hardening it would also change provider connectivity policy.; still in latest: unknown)
  - framework/modelcatalog/sync.go:130-138 — Pricing URL is fetched with a bare http.Client (no dial-time IP check) after only a save-time ValidateExternalURL(..., allowPrivateNetwork=true) that skips loopback entirely. (reason to dismiss: Pricing is operator-supplied framework configuration fetched at startup, and the save-time validator is the intended control for it.; still in latest: unknown)
  - framework/modelcatalog/sync.go:514-522 — Model-parameters URL takes the same bare-client path with only save-time ValidateExternalURL. (reason to dismiss: Same config-not-input argument; a neighbouring feature to pricing sync.; still in latest: unknown)
  - transports/bifrost-http/handlers/config.go:1004-1008 — Admin config save performs a server-side GET of the submitted PricingURL/ModelParametersURL with a bare http.Client after ValidateExternalURL(rawURL, true), which passes loopback, CGNAT and 6to4/NAT64-wrapped internal addresses. (reason to dismiss: Admin-only endpoint whose whole purpose is to probe reachability, so it looks intentional that it is not locked down like the model-facing fetcher.; still in latest: unknown)
  - core/utils.go:504-518 — Provider base-URL validation on create/update goes through ValidateExternalURL, which skips loopback and never unwraps IPv6 transition addresses. (reason to dismiss: loopback is skipped by design for local deployments and AllowPrivateNetwork is an explicit opt-in, so the weakness looks like intended policy.; still in latest: unknown)
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

## Environment (`tasks/bifrost-s2/environment/Dockerfile`)
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

## Report to the solver (`tasks/bifrost-s2/instruction.md`)
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

## Tests (`tasks/bifrost-s2/tests/`)
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
- **Wrong-fix patches** go in `build/bifrost-s2/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/bifrost-s2/`:**
- `instruction.md`;
- `task.toml`, from `common/builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/bifrost-s2/manifest.json`:**
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

**Also in `build/bifrost-s2/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `common/builder/templates/` and `common/trial/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I common/gate/gate.py bifrost-s2 --only static
python3 -I common/gate/gate.py bifrost-s2 --only nop
python3 -I common/gate/gate.py bifrost-s2 --only oracle
python3 -I common/gate/gate.py bifrost-s2 --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/bifrost-s2/`;
  - edit only `tasks/bifrost-s2/`, `build/bifrost-s2/` and, for pattern B, the register;
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
