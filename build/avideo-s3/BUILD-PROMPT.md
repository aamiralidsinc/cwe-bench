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

Project root: `/home/mara/cwe-bench`. Task: `avideo-s3`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: ["GHSA-95JH-7R58-XMXW", "CVE-2026-33731"]; wwbn/avideo; insufficient verification of data authenticity / forged payment data (CWE-345), webhook signature bypass leading to wallet balance inflation
- Pinned (vulnerable) commit: 36dfae22059fbd66fd34bbc5568a838fc0efd66c. Published fix: 033e83ae904cacb99495dbea7cbcfb3738cf42e4.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v2",
 "model": "deepseek-flash",
 "entry_id": "33406",
 "advisory_ids": [
  "GHSA-95JH-7R58-XMXW",
  "CVE-2026-33731"
 ],
 "repo": "wwbn/avideo",
 "pinned_commit": "36dfae22059fbd66fd34bbc5568a838fc0efd66c",
 "fix_commits": [
  "033e83ae904cacb99495dbea7cbcfb3738cf42e4"
 ],
 "trust_decision": {
  "summary": "Whether an unauthenticated POST to plugin/AuthorizeNet/webhook.php really came from Authorize.Net (HMAC-SHA512 over the raw body keyed with the configured Signature Key), and whether the users_id / amount / currency / plans_id / isApproved that get credited to the wallet come from Authorize.Net's API rather than from the request body; decided in AuthorizeNet::verifySignature + parseWebhookRequest (AuthorizeNet.php:51-128), gated in webhook.php:9-38 and 44-58, with the wallet credit sink at AuthorizeNet.php:283.",
  "evidence": [
   "plugin/AuthorizeNet/AuthorizeNet.php:51-64",
   "plugin/AuthorizeNet/AuthorizeNet.php:54",
   "plugin/AuthorizeNet/AuthorizeNet.php:57-58",
   "plugin/AuthorizeNet/AuthorizeNet.php:90",
   "plugin/AuthorizeNet/AuthorizeNet.php:166-228",
   "plugin/AuthorizeNet/webhook.php:33",
   "plugin/AuthorizeNet/webhook.php:44-58",
   "plugin/AuthorizeNet/webhook.php:68",
   "plugin/AuthorizeNet/AuthorizeNet.php:283",
   "fix.diff:26-39",
   "fix.diff:179-190"
  ]
 },
 "landing_point": {
  "where": "plugin/AuthorizeNet/webhook.php:33",
  "why": "The summary names a webhook signature bypass, so the first grep lands in webhook.php; line 32-33 literally reads 'Block only if both invalid signature AND no valid txn info', which is the bypass, and the adjacent call at webhook.php:10 leads straight to AuthorizeNet::verifySignature."
 },
 "fix_sites": [
  {
   "where": "plugin/AuthorizeNet/webhook.php:9-38",
   "entry_point": "POST /plugin/AuthorizeNet/webhook.php (unauthenticated public webhook; same-domain check disabled at webhook.php:4)",
   "module_kind": "http_handler"
  },
  {
   "where": "plugin/AuthorizeNet/AuthorizeNet.php:51-64",
   "entry_point": "public static AuthorizeNet::verifySignature() (public class API, called from parseWebhookRequest at AuthorizeNet.php:90)",
   "module_kind": "lower_level_public_api"
  },
  {
   "where": "plugin/AuthorizeNet/AuthorizeNet.php:87-128",
   "entry_point": "public static AuthorizeNet::parseWebhookRequest() (public class API used by the webhook handler)",
   "module_kind": "library_helper"
  },
  {
   "where": "plugin/AuthorizeNet/AuthorizeNet.php:1014-1027",
   "entry_point": "public static AuthorizeNet::getTransactionDetails() (called from webhook.php:30)",
   "module_kind": "sdk_mapper"
  },
  {
   "where": "plugin/AuthorizeNet/registerWebhook.json.php:1-39",
   "entry_point": "GET/POST /plugin/AuthorizeNet/registerWebhook.json.php (new admin-only endpoint added by the fix; additive, not part of the bypass)",
   "module_kind": "admin_http_handler"
  }
 ],
 "O1_entry_points": 1,
 "O2_out_of_scope_site": {
  "kind": "lower_level_api",
  "where": "plugin/AuthorizeNet/AuthorizeNet.php:253-298 (AuthorizeNet::processSinglePayment; also reachable via processSubscriptionCharge at AuthorizeNet.php:312-354 and processSubscriptionChargeWithPlan at AuthorizeNet.php:365-413)"
 },
 "O3_reason_to_dismiss": "processSinglePayment is an internal library function with no HTTP route of its own; the advisory is about the public webhook handler, so a solver can argue the API is only reached by trusted plugin code after the webhook check, even though it credits any caller-supplied users_id/amount straight to YPTWallet::addBalance (AuthorizeNet.php:283) and was left untouched by the fix.",
 "O4_distance": {
  "files": 1,
  "packages": 0,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "The fix's new gate 'if (empty($analysis['isApproved'])) exit' (fix.diff:253-262) consumes $txnInfo['isApproved'] produced by getTransactionDetails, whose comparison is case-sensitive against the camelCase constants 'capturedPendingSettlement'/'settledSuccessfully' (AuthorizeNet.php:1027) while the sibling analyzer already lowercases (AuthorizeNet.php:224-225); the published fix had to change exactly that line (fix.diff:110), so a solver who adds the approval gate without fixing the producer rejects every genuine payment. Likewise the legitimate duplicate-delivery path must keep returning HTTP 200 'duplicate' (webhook.php:22-27) and the payload->txnInfo fallbacks at webhook.php:44-58 must keep filling values the payload legitimately lacks (e.g. plans_id only present on the ARB order description).",
  "where": "plugin/AuthorizeNet/AuthorizeNet.php:1027"
 },
 "O6_input_shapes": [
  "Signature header value in lowercase vs uppercase hex (fix lowercases the received header before hash_equals, fix.diff:38-39)",
  "Signature key treated as raw ASCII vs hex-decoded bytes (old hex2bin + ctype_xdigit guard at AuthorizeNet.php:54-57 removed, fix.diff:26-32)",
  "Missing / empty Signature Key or missing signature header (rejected outright instead of being ignored)",
  "Body amount supplied as 'amount' or 'authAmount' vs the API's getAuthAmount (AuthorizeNet.php:109, 171)",
  "Body metadata.users_id / metadata.plans_id vs the users_id/plans_id decoded from the ARB order description (AuthorizeNet.php:169-170, 188-213, 1054-1055)",
  "Body responseCode as approval evidence vs the API transaction status string, including its casing (AuthorizeNet.php:226-227 vs 1027)",
  "Transaction id supplied under payload.id or payload.transId (AuthorizeNet.php:108)",
  "eventType outside the allow-list net.authorize.payment.authcapture.created (AuthorizeNet.php:97-105)"
 ],
 "O7_producer": {
  "kind": "config_loader",
  "where": "plugin/Plugin.abstract.php:193-245 - PluginAbstract::getDataObject() reads plugins.object_data from the DB, merges it with getEmptyDataObject() defaults and type-coerces each key (Plugin.abstract.php:204-223); the AuthorizeNet default is signatureKey = '' (plugin/AuthorizeNet/AuthorizeNet.php:1257) and the protected check consumes it at AuthorizeNet.php:90. A non-string (e.g. numeric) stored signatureKey is silently replaced by the empty default, which disables verification entirely rather than failing loudly.",
  "check_calls_producer": true
 },
 "O8_uncovered_routes": [
  {
   "route": "POST /plugin/AuthorizeNet/processPayment.json.php for any logged-in user credits YPTWallet with a client-supplied 'amount' and a hard-coded $paymentSuccess = true, without any webhook, signature, or gateway call",
   "where": "plugin/AuthorizeNet/processPayment.json.php:7-25",
   "reason_to_dismiss": "It is not a webhook at all - no signature header is involved, the file is marked '// TODO: Implement payment logic' and '// Simulate payment success for now', and nothing in the plugin references it, so a solver reading a report about webhook signature verification has a plausible reason to call it an unfinished neighbour and leave it.",
   "distance": "same plugin directory, 1 file from the landing point; an authenticated-user route (User::getId() at processPayment.json.php:19) rather than an unauthenticated one",
   "present_in_latest": "unknown",
   "latest_where": ""
  }
 ],
 "O8b_injection_room": [
  {
   "where": "plugin/YPTWallet/plugins/YPTWalletStripe/requestPayment.json.php:32",
   "sibling": "A YPTWalletAuthorizeNet gateway folder (requestPayment.json.php / redirect_url.php) that credits the wallet on the browser return from the Accept Hosted page",
   "why_realistic": "Every other YPTWallet gateway already has such a folder and credits from the return leg (StripeYPT here, RazorPay at plugin/YPTWallet/plugins/YPTWalletRazorPay/redirect_url.php:72), and AuthorizeNet already exposes a hosted payment page with acceptHostedReturn.php as its return URL, so a maintainer would copy the pattern."
  },
  {
   "where": "plugin/AuthorizeNet/AuthorizeNet.php:935-962",
   "sibling": "A second webhook file for the other event types createWebhookIfNotExists can register (subscription charged, void, refund) that credits or reverses wallet balance",
   "why_realistic": "The event list is already a parameter of createWebhookIfNotExists and updateWebhookEventTypes (AuthorizeNet.php:930), so adding siblings of net.authorize.payment.authcapture.created is a one-line change a maintainer would make without touching the existing handler."
  },
  {
   "where": "plugin/AuthorizeNet/View/Anet_webhook_log/add.json.php:17-31",
   "sibling": "A 'reprocess' action on a webhook-log row that calls AuthorizeNet::processSinglePayment with the stored payload",
   "why_realistic": "Admins already hand-edit anet_webhook_log rows here (uniq_key, payload_json, processed), so a replay/reprocess button is the obvious next admin feature and would reach the same sink with no signature at all."
  }
 ],
 "O9_family": "insufficient verification of data authenticity / forged payment data (CWE-345), webhook signature bypass leading to wallet balance inflation",
 "O9_dos": false,
 "O10_build": {
  "language": "PHP (^7.3|^8, composer platform php 8)",
  "toolchain": "composer with vendor/ committed (vendor/authorizenet, vendor/aws, vendor/google present); phpunit 9.6 via phpunit.xml plus tests/bootstrap.php; web server + PHP extensions curl/json",
  "services": [
   "MySQL/MariaDB (anet_webhook_log schema at plugin/AuthorizeNet/install/install.sql, plus the core AVideo schema)",
   "Apache/nginx + PHP (getallheaders, php://input)",
   "Outbound HTTPS to api.authorize.net / apitest.authorize.net for getTransactionDetails and the webhook REST calls"
  ],
  "offline_after_build": false,
  "project_tests": "tests/ has phpunit Security/Unit suites but no test mentions AuthorizeNet, webhook or verifySignature; the published fix adds no test files either, so this area has no tests at the pinned commit."
 },
 "O11_fix_minutes": 45,
 "O12_red_flags": [
  "needs_network_at_runtime"
 ],
 "O13_recall_risk": "medium",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "plugin/AuthorizeNet/webhook.php, plugin/AuthorizeNet/AuthorizeNet.php, plugin/AuthorizeNet/registerWebhook.json.php",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Repair the hex/ctype key handling in verifySignature (or the casing of the signature header) and add an early 401 in webhook.php, leaving the 'or a valid transaction exists' fallback, the payload-precedence rules and processPayment.json.php untouched."
 },
 "out_of_scope_notes": [
  "Other payment plugins credit the same YPTWallet sink with their own verification (plugin/StripeYPT/ipn.php:83 -> StripeYPT.php:753-766, plugin/PayPalYPT/ipn.php:32, plugin/BTCPayments/webhook.php:90, plugin/BlockonomicsYPT/callback.php:62); outside this advisory's Authorize.Net property and not pursued."
 ],
 "unverified": [
  "Repo size in MB: no shell was available, so O4.repo_mb is null and tiny_repo/giant_repo were not asserted; the tree clearly contains a large committed vendor/ (google/apiclient-services, aws-sdk-php) plus media assets.",
  "present_in_latest for the O8 route: the task states 'latest release: none', so there is no later tree to compare and it stays unknown.",
  "Whether the live Authorize.Net API returns transaction status in a casing that the pinned getTransactionDetails comparison misses: inferred only from the fix itself having to add strtolower at fix.diff:110; not exercised.",
  "needs_network_at_runtime: the signature gate itself is offline-testable through AuthorizeNet::verifySignature / parseWebhookRequest (no I/O), but the credit path and the txnInfo-precedence behaviour both require getTransactionDetails, a static call into the Authorize.Net SDK with no injection seam, so end-to-end credit assertions cannot run offline.",
  "O8 route reachability was read, not run: processPayment.json.php requires a logged-in user (User::getId()) and is referenced by no other file in the tree."
 ]
}
  ```
- Published fix sites:   - plugin/AuthorizeNet/webhook.php:9-38 — entry point: POST /plugin/AuthorizeNet/webhook.php (unauthenticated public webhook; same-domain check disabled at webhook.php:4) [http_handler]
  - plugin/AuthorizeNet/AuthorizeNet.php:51-64 — entry point: public static AuthorizeNet::verifySignature() (public class API, called from parseWebhookRequest at AuthorizeNet.php:90) [lower_level_public_api]
  - plugin/AuthorizeNet/AuthorizeNet.php:87-128 — entry point: public static AuthorizeNet::parseWebhookRequest() (public class API used by the webhook handler) [library_helper]
  - plugin/AuthorizeNet/AuthorizeNet.php:1014-1027 — entry point: public static AuthorizeNet::getTransactionDetails() (called from webhook.php:30) [sdk_mapper]
  - plugin/AuthorizeNet/registerWebhook.json.php:1-39 — entry point: GET/POST /plugin/AuthorizeNet/registerWebhook.json.php (new admin-only endpoint added by the fix; additive, not part of the bypass) [admin_http_handler]
- Uncovered routes to confirm (pattern B):   - plugin/AuthorizeNet/processPayment.json.php:7-25 — POST /plugin/AuthorizeNet/processPayment.json.php for any logged-in user credits YPTWallet with a client-supplied 'amount' and a hard-coded $paymentSuccess = true, without any webhook, signature, or gateway call (reason to dismiss: It is not a webhook at all - no signature header is involved, the file is marked '// TODO: Implement payment logic' and '// Simulate payment success for now', and nothing in the plugin references it, so a solver reading a report about webhook signature verification has a plausible reason to call it an unfinished neighbour and leave it.; still in latest: unknown)
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

## Environment (`tasks/avideo-s3/environment/Dockerfile`)
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

## Report to the solver (`tasks/avideo-s3/instruction.md`)
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

## Tests (`tasks/avideo-s3/tests/`)
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
- **Wrong-fix patches** go in `build/avideo-s3/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/avideo-s3/`:**
- `instruction.md`;
- `task.toml`, from `common/builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/avideo-s3/manifest.json`:**
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

**Also in `build/avideo-s3/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `common/builder/templates/` and `common/trial/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I common/gate/gate.py avideo-s3 --only static
python3 -I common/gate/gate.py avideo-s3 --only nop
python3 -I common/gate/gate.py avideo-s3 --only oracle
python3 -I common/gate/gate.py avideo-s3 --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/avideo-s3/`;
  - edit only `tasks/avideo-s3/`, `build/avideo-s3/` and, for pattern B, the register;
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
