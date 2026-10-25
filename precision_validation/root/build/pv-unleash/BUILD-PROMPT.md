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

Project root: `/home/mara/cwe-bench/precision_validation/root`. Task: `pv-unleash`. Pattern: `A`. Track: `injected`.

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
- Advisory: ["GHSA-5VF6-JRQR-78FJ", "CVE-2026-63004"]; unleash/unleash; SSRF (CWE-918): server-side request to an admin-supplied URL with no destination-address filtering, no DNS pinning and redirects followed
- Pinned (vulnerable) commit: unknown (parent of 2100db76af3473f13e6fb40096cf17a9c2b741a1; parent_commit null in candidate; tree at hosts/8843/repo, package version 7.6.4). Published fix: 2100db76af3473f13e6fb40096cf17a9c2b741a1, d45f99df924c0d24747b3e45e46fcda7dcd3c1c1, d862562a5ab8f2d1e40f6519c64cf0b4fdaf806d.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "8843",
 "advisory_ids": [
  "GHSA-5VF6-JRQR-78FJ",
  "CVE-2026-63004"
 ],
 "repo": "unleash/unleash",
 "pinned_commit": "unknown (parent of 2100db76af3473f13e6fb40096cf17a9c2b741a1; parent_commit null in candidate; tree at hosts/8843/repo, package version 7.6.4)",
 "fix_commits": [
  "2100db76af3473f13e6fb40096cf17a9c2b741a1",
  "d45f99df924c0d24747b3e45e46fcda7dcd3c1c1",
  "d862562a5ab8f2d1e40f6519c64cf0b4fdaf806d"
 ],
 "trust_decision": {
  "summary": "Whether an admin-configured integration URL may be dialed server-side when it resolves to a non-public address (or redirects there). At the pinned commit this is decided nowhere: Addon.fetchRetry passes the stored URL straight to ky, and create/update only check that required params exist. The fix decides it in validateUrl, called both at dispatch (fetchRetry, with DNS pinning and no redirect following) and at write time (AddonService.validateUrlParameter).",
  "evidence": [
   "src/lib/addons/addon.ts:58-68",
   "src/lib/services/addon-service.ts:224-233",
   "src/lib/services/addon-service.ts:259-276",
   "fix.diff:81-92",
   "fix.diff:116-128",
   "fix.diff:723-766",
   "fix.diff:1094-1101"
  ]
 },
 "landing_point": {
  "where": "src/lib/addons/webhook.ts:91",
  "why": "The summary says the 'Addon webhook URL is dialed server-side', so a reader starts at the Webhook addon's fetchRetry(url, ...) call. It sends user-chosen customHeaders and authorization (webhook.ts:70-90), which is the header-exfiltration part of the summary."
 },
 "fix_sites": [
  {
   "where": "src/lib/addons/addon.ts:58",
   "entry_point": "event dispatch: any Unleash event -> AddonService.handleEvent -> provider.handleEvent -> fetchRetry, for the webhook, slack, teams, datadog and new-relic providers (webhook.ts:91, slack.ts:108, teams.ts:98, datadog.ts:103, new-relic.ts:106)",
   "module_kind": "shared base class / lower-level API (Addon.fetchRetry); the fix adds validateUrl, DNS-pinned connect and redirect:'manual'"
  },
  {
   "where": "src/lib/services/addon-service.ts:224",
   "entry_point": "POST /api/admin/addons (src/lib/routes/admin-api/addon.ts:95-99)",
   "module_kind": "service layer, write-time validation of persisted config (createAddon)"
  },
  {
   "where": "src/lib/services/addon-service.ts:259",
   "entry_point": "PUT /api/admin/addons/:id (src/lib/routes/admin-api/addon.ts:136-140)",
   "module_kind": "service layer, write-time validation of persisted config (updateAddon, after MASKED_VALUE merge point)"
  },
  {
   "where": "src/lib/services/addon-service.ts:86-94",
   "entry_point": "server startup: AddonService constructor builds providers via getAddons (src/lib/addons/index.ts:14-22)",
   "module_kind": "composition/wiring that passes allowPrivateUrls/allowList into every provider"
  },
  {
   "where": "src/lib/create-config.ts:589",
   "entry_point": "createConfig options / env UNLEASH_ALLOW_PRIVATE_URL_IN_INTEGRATION, UNLEASH_ALLOW_LIST_INTEGRATION (fix.diff:775-785)",
   "module_kind": "config loader / defaults route for the opt-out and allow-list"
  },
  {
   "where": "src/lib/addons/new-relic.ts:127",
   "entry_point": "GET /api/admin/addons/:id/events (src/lib/routes/admin-api/addon.ts:179-183): the URL is no longer recorded in integration-event details",
   "module_kind": "provider implementation (secondary hardening)"
  },
  {
   "where": "src/lib/addons/teams.ts:119",
   "entry_point": "GET /api/admin/addons/:id/events (src/lib/routes/admin-api/addon.ts:179-183): the URL is no longer recorded in integration-event details",
   "module_kind": "provider implementation (secondary hardening)"
  }
 ],
 "O1_entry_points": 3,
 "O2_out_of_scope_site": {
  "kind": "save_reload_or_serialization",
  "where": "src/lib/services/addon-service.ts:224-233 and src/lib/services/addon-service.ts:259-276 (write-time validation of the persisted URL, in services/, away from the addons/ dial site), plus src/lib/services/addon-service.ts:101-107 (dispatch reads stored rows through a memoized store read, so rows saved before the fix reach the dial without passing a write-time check)"
 },
 "O3_reason_to_dismiss": "Either way round: 'the runtime check in fetchRetry already blocks every dial, so save-time validation is only UX', or 'validating on create/update is enough, because stored configs were entered by an admin with CREATE_ADDON permission and are trusted'. The second leaves pre-existing rows and DNS rebinding or redirects open.",
 "O4_distance": {
  "files": 9,
  "packages": 4,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "1) Updating an integration while the masked url '*****' is echoed back must keep working: the fix skips validation for MASKED_VALUE, and the existing value is merged back in. 2) Self-hosted deployments that point webhooks at internal hosts need an opt-out (allowPrivateUrlInIntegration) or a host allow-list. 3) Datadog with no url falls back to its public default URL. 4) A 30x response is returned as a status, not followed and not thrown. A fix that rejects every non-public address without an override, or that validates the masked placeholder, breaks these.",
  "where": "src/lib/services/addon-service.ts:262-275; src/lib/addons/datadog.ts:53-54; fix.diff:775-785; fix.diff:1094-1100; fix.diff:120-127"
 },
 "O6_input_shapes": [
  "hostname that DNS-resolves to a private/loopback/link-local address (fix.diff:733-758)",
  "literal IPv4 address in the URL (fix.diff:732-735, fix.diff:638-655)",
  "literal IPv6 address incl. IPv4-mapped ::ffff:a.b.c.d, ULA, link-local (fix.diff:657-672)",
  "non-http(s) scheme such as file: (fix.diff:728-730)",
  "any of several resolved addresses being private (fix.diff:750)",
  "30x redirect to an internal host (fix.diff:122-125)",
  "DNS rebinding between check and connect: the connect is pinned to the validated IP (fix.diff:149-165)",
  "host on the allow-list, case-insensitive (fix.diff:715-721)",
  "masked placeholder '*****' on update (fix.diff:1095)"
 ],
 "O7_producer": {
  "kind": "cache",
  "where": "src/lib/services/addon-service.ts:101-107 (memoizee'd addonStore.getAll({enabled:true}) feeding handleEvent at src/lib/services/addon-service.ts:136-161)",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [],
 "O8b_injection_room": [
  {
   "where": "src/lib/addons/slack-app.ts:37",
   "sibling": "Slack App client built with a configurable slackApiUrl (for GovSlack or Enterprise Grid) taken from addon parameters, bypassing fetchRetry",
   "why_realistic": "WebClient accepts a slackApiUrl option, and region or alternative endpoints are a common feature request. A maintainer would wire it straight into new WebClient(...) rather than through Addon.fetchRetry."
  },
  {
   "where": "src/lib/routes/admin-api/addon.ts:95-114",
   "sibling": "a 'send test event' or 'test connection' admin route that dials parameters.url directly with ky before saving",
   "why_realistic": "Integration UIs commonly add a test button. That route would naturally run before createAddon's validation and might call ky directly, the way the existing services do (src/lib/services/version-service.ts:1)."
  },
  {
   "where": "src/lib/addons/index.ts:15-22",
   "sibling": "a new provider (e.g. a generic chat webhook) whose handleEvent calls ky/fetch itself instead of this.fetchRetry",
   "why_realistic": "Each provider owns its own handleEvent, and nothing in the Addon base class forces use of fetchRetry."
  }
 ],
 "O9_family": "SSRF (CWE-918): server-side request to an admin-supplied URL with no destination-address filtering, no DNS pinning and redirects followed",
 "O9_dos": false,
 "O10_build": {
  "language": "TypeScript (ESM)",
  "toolchain": "Node >=22, yarn, tsc, vitest 4, nock; ip-address ^10.1.0 and ky ^1.14.3 already dependencies at the pinned commit (package.json:103, package.json:110)",
  "services": [
   "PostgreSQL (only for e2e tests under src/test/e2e; addon unit tests run without a DB)"
  ],
  "offline_after_build": true,
  "project_tests": "src/lib/addons/{webhook,slack,teams,datadog,new-relic,addon}.test.ts (nock-based unit tests); src/lib/services/addon-service.test.ts (fake stores); src/test/e2e/api/admin/addon.e2e.test.ts and src/test/e2e/services/addon-service.e2e.test.ts (need Postgres)"
 },
 "O11_fix_minutes": 60,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "A",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "src/lib/addons/addon.ts, src/lib/addons/validate-url.ts (new), src/lib/services/addon-service.ts, src/lib/create-config.ts, src/lib/types/model.ts, src/lib/types/option.ts, src/lib/addons/new-relic.ts, src/lib/addons/teams.ts (plus unrelated src/lib/error/bad-data-error.ts, src/lib/routes/util.ts and a typo fix in src/lib/addons/datadog-definition.ts)",
  "j_sibling_sites": "no",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 0,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Reject private/loopback hostnames by string or literal-IP match in AddonService.createAddon/updateAddon (or only in webhook.ts). This misses already-stored configs, DNS names that resolve internally, rebinding, redirect following, and the IPv6/IPv4-mapped forms."
 },
 "out_of_scope_notes": [
  "The fix commits bundle an unrelated hardening: JSON.stringify of deeply nested values in src/lib/error/bad-data-error.ts and src/lib/routes/util.ts (fix.diff:797-833, fix.diff:904-919). Not part of the SSRF protection.",
  "The sensitive webhook/slack/datadog URL is still recorded in integration-event details (src/lib/addons/webhook.ts:119, src/lib/addons/slack.ts:141, src/lib/addons/datadog.ts:124), while the fix removed it only for new-relic and teams. This is a separate secret-masking protection and was not pursued.",
  "The ky calls in src/lib/services/version-service.ts:1 and src/lib/util/load-index-html.ts:4 use operator-configured URLs, so they are outside this protection."
 ],
 "unverified": [
  "Repo size in MB was not measured (no shell). It is probably well above 5 MB (backend plus frontend), so tiny_repo was not flagged.",
  "Pinned commit hash: parent_commit is null in the candidate, so the hash was not recorded.",
  "Whether a fourth fix commit exists beyond the three listed was not checked.",
  "Hidden-test design caveat: the published tests drive validation through an injected validateUrlOptions.lookup (fix.diff:490-492). A solver's API will differ, so behavioural tests should use literal IPs (127.0.0.1, ::ffff:127.0.0.1, 169.254.169.254) and a local redirecting server. Also, defaultLookup returns a fake public IP under NODE_ENV=test (fix.diff:703-712), which belongs to the fix, not the pinned code.",
  "The default-deny hurts fairness: the fix makes private URLs blocked by default and changes existing tests to opt in (fix.diff:1146, fix.diff:1158). The report must state the opt-out config names (allowPrivateUrlInIntegration / allowListIntegration), or hidden tests must not depend on them.",
  "Recall risk: the advisory was published 2026-08-21, after the model knowledge cutoff, so how widely it has been written up is a guess."
 ]
}
  ```
- Published fix sites:   - src/lib/addons/addon.ts:58 — entry point: event dispatch: any Unleash event -> AddonService.handleEvent -> provider.handleEvent -> fetchRetry, for the webhook, slack, teams, datadog and new-relic providers (webhook.ts:91, slack.ts:108, teams.ts:98, datadog.ts:103, new-relic.ts:106) [shared base class / lower-level API (Addon.fetchRetry); the fix adds validateUrl, DNS-pinned connect and redirect:'manual']
  - src/lib/services/addon-service.ts:224 — entry point: POST /api/admin/addons (src/lib/routes/admin-api/addon.ts:95-99) [service layer, write-time validation of persisted config (createAddon)]
  - src/lib/services/addon-service.ts:259 — entry point: PUT /api/admin/addons/:id (src/lib/routes/admin-api/addon.ts:136-140) [service layer, write-time validation of persisted config (updateAddon, after MASKED_VALUE merge point)]
  - src/lib/services/addon-service.ts:86-94 — entry point: server startup: AddonService constructor builds providers via getAddons (src/lib/addons/index.ts:14-22) [composition/wiring that passes allowPrivateUrls/allowList into every provider]
  - src/lib/create-config.ts:589 — entry point: createConfig options / env UNLEASH_ALLOW_PRIVATE_URL_IN_INTEGRATION, UNLEASH_ALLOW_LIST_INTEGRATION (fix.diff:775-785) [config loader / defaults route for the opt-out and allow-list]
  - src/lib/addons/new-relic.ts:127 — entry point: GET /api/admin/addons/:id/events (src/lib/routes/admin-api/addon.ts:179-183): the URL is no longer recorded in integration-event details [provider implementation (secondary hardening)]
  - src/lib/addons/teams.ts:119 — entry point: GET /api/admin/addons/:id/events (src/lib/routes/admin-api/addon.ts:179-183): the URL is no longer recorded in integration-event details [provider implementation (secondary hardening)]
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
- Append one row per route to `/home/mara/cwe-bench/precision_validation/root/build/audit/uncovered-routes.tsv`, using its existing
  header. Columns:
  - `task`, `repo`, `advisory`;
  - `trap_ref` (the manifest trap id only; no mechanism text, since the manifest holds the detail);
  - `real_upstream`;
  - `present_in_latest` (`yes`, `no` or `unknown`, from a read-only look at current upstream code if
    you can reach it);
  - `public_upstream_report`, `in_current_scope`, `built`, `note`;
  - `disclosure_status` (`pending client decision`).

## Environment (`tasks/pv-unleash/environment/Dockerfile`)
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

## Report to the solver (`tasks/pv-unleash/instruction.md`)
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

## Tests (`tasks/pv-unleash/tests/`)
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
- **Wrong-fix patches** go in `build/pv-unleash/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/pv-unleash/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/pv-unleash/manifest.json`:**
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

**Also in `build/pv-unleash/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py pv-unleash --only static
python3 -I builder/gate.py pv-unleash --only nop
python3 -I builder/gate.py pv-unleash --only oracle
python3 -I builder/gate.py pv-unleash --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/pv-unleash/`;
  - edit only `tasks/pv-unleash/`, `build/pv-unleash/` and, for pattern B, the register;
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
