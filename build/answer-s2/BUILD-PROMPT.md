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

Project root: `/home/mara/cwe-bench`. Task: `answer-s2`. Pattern: `B`. Track: `injected`.

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
- Advisory: ["GHSA-6QWM-5FM9-CVJX", "CVE-2026-34033", "GO-2026-6151"]; apache/answer; CWE-79/CWE-80 HTML injection (stored, via server-rendered email templates)
- Pinned (vulnerable) commit: 11c80384f13a27e27c871c05bb353489d1363ee2. Published fix: d1a4092c61ccd41988d1033fce47eb513adb433e.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v2",
 "model": "deepseek-flash",
 "entry_id": "16232",
 "advisory_ids": [
  "GHSA-6QWM-5FM9-CVJX",
  "CVE-2026-34033",
  "GO-2026-6151"
 ],
 "repo": "apache/answer",
 "pinned_commit": "11c80384f13a27e27c871c05bb353489d1363ee2",
 "fix_commits": [
  "d1a4092c61ccd41988d1033fce47eb513adb433e"
 ],
 "trust_decision": {
  "summary": "The email renderer trusts every value substituted into the HTML body templates to already be HTML-safe, and the whole decision is made at render time inside the four notification template methods of EmailService (escape each dynamic field, leave the template's own markup and the generated URLs untouched).",
  "evidence": [
   "internal/service/export/email_service.go:139",
   "internal/service/export/email_service.go:249",
   "internal/service/export/email_service.go:274",
   "internal/service/export/email_service.go:301",
   "internal/service/export/email_service.go:327",
   "i18n/en_US.yaml:495"
  ]
 },
 "landing_point": {
  "where": "internal/service/export/email_service.go:249",
  "why": "The advisory summary only says 'Cross-site Scripting' in Apache Answer; grepping the backend for the HTML mail body lands on the single place that renders email HTML (Send sets text/html at :139) and on the first notification template that interpolates a user display name and a question title."
 },
 "fix_sites": [
  {
   "where": "internal/service/export/email_service.go:249",
   "entry_point": "POST /answer (internal/router/answer_api_router.go:281) -> new_answer_notification.go:74",
   "module_kind": "internal service package: email template renderer (notification path)"
  },
  {
   "where": "internal/service/export/email_service.go:274",
   "entry_point": "PUT /question/invite (internal/router/answer_api_router.go:272) -> invite_answer_notification.go:74",
   "module_kind": "internal service package: email template renderer (invite path)"
  },
  {
   "where": "internal/service/export/email_service.go:301",
   "entry_point": "POST /comment (internal/router/answer_api_router.go:234) -> new_comment_notification.go:73",
   "module_kind": "internal service package: email template renderer (comment path)"
  },
  {
   "where": "internal/service/export/email_service.go:327",
   "entry_point": "POST /question (internal/router/answer_api_router.go:269) -> new_question_notification.go:180",
   "module_kind": "internal service package: email template renderer (question fan-out path)"
  },
  {
   "where": "fix.diff:21-23",
   "entry_point": "helper escapeEmailHTMLText used by all four sites above",
   "module_kind": "new package-private helper in the same file"
  }
 ],
 "O1_entry_points": 5,
 "O2_out_of_scope_site": {
  "kind": "save_reload_or_serialization",
  "where": "internal/service/siteinfo_common/siteinfo_service.go:83"
 },
 "O3_reason_to_dismiss": "The site name is set only by an admin and passes the `sanitizer` validator (internal/schema/siteinfo_schema.go:40, internal/base/validator/validator.go:140-146), so a solver can argue the register/pass-reset/change-email/test templates carry no attacker input - while GetSiteGeneral's html.UnescapeString (siteinfo_service.go:83) silently turns a stored '&lt;img src=x onerror=...&gt;' back into live markup before it is substituted.",
 "O4_distance": {
  "files": 8,
  "packages": 6,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "The body IS HTML and every template contains its own literal <br>, <blockquote> and <a href='...'> markup plus already-built link URLs; escaping the finished body, escaping the URL fields, or switching TrWithData to html/template escapes that markup too and every notification email is delivered as literal tag text.",
  "where": "i18n/en_US.yaml:495-510"
 },
 "O6_input_shapes": [
  "user display name: plain string, 2-30 chars, never sanitised (internal/schema/user_schema.go:262)",
  "question title: plain string, 6-150 chars, never sanitised (internal/schema/question_schema.go:80)",
  "answer/comment summary: excerpt text taken from stored HTML content",
  "tags: []string of slug names joined with ', ' before substitution (email_service.go:319)",
  "site name: stored entity-escaped, de-escaped on read (siteinfo_service.go:83)",
  "generated URLs: must stay verbatim (email_service.go:242,268,296,322)"
 ],
 "O7_producer": {
  "kind": "serializer",
  "where": "internal/service/siteinfo_common/siteinfo_service.go:83 (value comes back through the site_info cache/JSON path at internal/repo/site_info/siteinfo_repo.go:85-95)",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "Registration / activation email: SiteName substituted unescaped into an HTML body",
   "where": "internal/service/export/email_service.go:179",
   "reason_to_dismiss": "Site name is admin-set and sanitised at input, so it is not attacker data.",
   "distance": "2 packages (content/user_service.go:489, user_admin/user_backyard.go:616, user_external_login_service.go:327 -> export)",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "Password-reset email: SiteName substituted unescaped into an HTML body",
   "where": "internal/service/export/email_service.go:192-193",
   "reason_to_dismiss": "Same admin-controlled site name; the 'forgot password' path is also unauthenticated, so it is easy to argue it is out of the reported scope.",
   "distance": "2 packages (content/user_service.go:235 -> export)",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "Change-email confirmation email: SiteName substituted unescaped into an HTML body",
   "where": "internal/service/export/email_service.go:208-209",
   "reason_to_dismiss": "Same admin-controlled site name; the URL is a server-generated token link.",
   "distance": "2 packages (content/user_service.go:658 -> export)",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "Admin SMTP test email: SiteName substituted unescaped into an HTML body",
   "where": "internal/service/export/email_service.go:222-223",
   "reason_to_dismiss": "Only an admin can trigger it and only an admin sets the site name, so it is a self-inflicted sink.",
   "distance": "1 package (siteinfo/siteinfo_service.go:518 -> export)",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "Subject lines of the four fixed templates still substitute the same raw values (DisplayName, QuestionTitle)",
   "where": "internal/service/export/email_service.go:248,273,300,326",
   "reason_to_dismiss": "The title becomes the Subject header (email_service.go:138), not HTML, so escaping it is arguably wrong - and it would show '&amp;' to the recipient.",
   "distance": "same file",
   "present_in_latest": "unknown",
   "latest_where": ""
  }
 ],
 "O8b_injection_room": [
  {
   "where": "internal/service/export/email_service.go:167-225",
   "sibling": "A 'you were mentioned' / 'your post was edited' notification template that reuses the same site name + user content pattern",
   "why_realistic": "The four unescaped templates already live there and a maintainer adding a notification would copy this exact shape."
  },
  {
   "where": "internal/schema/email_template.go:59-77",
   "sibling": "New *TemplateData structs that carry a raw user-controlled field",
   "why_realistic": "Each new notification type adds a Data struct here and the field-by-field escaping decision has to be repeated."
  },
  {
   "where": "internal/service/notification/new_question_notification.go:59-66",
   "sibling": "A new fan-out that rebuilds raw template data from the queue message",
   "why_realistic": "Per-subscriber copies are built here, so a new subscriber class would add another producer of the same tainted fields."
  },
  {
   "where": "internal/service/siteinfo_common/siteinfo_service.go:83",
   "sibling": "Another site-info reader that html.UnescapeString's a field consumed by a template",
   "why_realistic": "Several site-info getters exist in this file and only the general one de-escapes, so a sibling reader would be a natural slip."
  }
 ],
 "O9_family": "CWE-79/CWE-80 HTML injection (stored, via server-rendered email templates)",
 "O9_dos": false,
 "O10_build": {
  "language": "Go",
  "toolchain": "go 1.24.0 with CGO tags 'sqlite sqlite_unlock_notify'; Makefile + Dockerfile (Node/pnpm only needed for the embedded UI bundle)",
  "services": [
   "database: MySQL, PostgreSQL or SQLite (SQLite in-process)",
   "optional Redis cache"
  ],
  "offline_after_build": true,
  "project_tests": "No tests in internal/service/export; the only service-level tests are internal/service/dashboard/dashboard_test.go and internal/service/siteinfo_common/siteinfo_service_test.go. Email rendering is testable offline because Send skips SMTP when the host is empty (email_service.go:129-131)."
 },
 "O11_fix_minutes": 20,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "internal/service/export/email_service.go",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Escape the finished body (or swap TrWithData for html/template), which escapes the templates' own <br>/<a href> markup and the generated URLs and breaks every email; then escape only the field reproduced (DisplayName in new_answer) and stop."
 },
 "out_of_scope_notes": [
  "The unescaped values also flow into the Subject header (email_service.go:138); header/CRLF injection there is a different weakness family and was not pursued.",
  "External notification plugins receive the same raw template data (plugin package boundary) and build their own mail bodies outside this repository."
 ],
 "unverified": [
  "Repository source size in MB (no shell available); the tree is clearly larger than 5 MB of source, so tiny_repo was not flagged.",
  "Whether the notice queue persists ExternalNotificationMsg as JSON before the consumer runs; the JSON tags at internal/schema/new_question_queue_schema.go:27-36 show the boundary but the queue storage was not read.",
  "Whether a non-admin can ever set the site name; only the install request (internal/install/install_req.go:125) and the admin site-info schema were read."
 ]
}
  ```
- Published fix sites:   - internal/service/export/email_service.go:249 — entry point: POST /answer (internal/router/answer_api_router.go:281) -> new_answer_notification.go:74 [internal service package: email template renderer (notification path)]
  - internal/service/export/email_service.go:274 — entry point: PUT /question/invite (internal/router/answer_api_router.go:272) -> invite_answer_notification.go:74 [internal service package: email template renderer (invite path)]
  - internal/service/export/email_service.go:301 — entry point: POST /comment (internal/router/answer_api_router.go:234) -> new_comment_notification.go:73 [internal service package: email template renderer (comment path)]
  - internal/service/export/email_service.go:327 — entry point: POST /question (internal/router/answer_api_router.go:269) -> new_question_notification.go:180 [internal service package: email template renderer (question fan-out path)]
  - fix.diff:21-23 — entry point: helper escapeEmailHTMLText used by all four sites above [new package-private helper in the same file]
- Uncovered routes to confirm (pattern B):   - internal/service/export/email_service.go:179 — Registration / activation email: SiteName substituted unescaped into an HTML body (reason to dismiss: Site name is admin-set and sanitised at input, so it is not attacker data.; still in latest: unknown)
  - internal/service/export/email_service.go:192-193 — Password-reset email: SiteName substituted unescaped into an HTML body (reason to dismiss: Same admin-controlled site name; the 'forgot password' path is also unauthenticated, so it is easy to argue it is out of the reported scope.; still in latest: unknown)
  - internal/service/export/email_service.go:208-209 — Change-email confirmation email: SiteName substituted unescaped into an HTML body (reason to dismiss: Same admin-controlled site name; the URL is a server-generated token link.; still in latest: unknown)
  - internal/service/export/email_service.go:222-223 — Admin SMTP test email: SiteName substituted unescaped into an HTML body (reason to dismiss: Only an admin can trigger it and only an admin sets the site name, so it is a self-inflicted sink.; still in latest: unknown)
  - internal/service/export/email_service.go:248,273,300,326 — Subject lines of the four fixed templates still substitute the same raw values (DisplayName, QuestionTitle) (reason to dismiss: The title becomes the Subject header (email_service.go:138), not HTML, so escaping it is arguably wrong - and it would show '&amp;' to the recipient.; still in latest: unknown)
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

## Environment (`tasks/answer-s2/environment/Dockerfile`)
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

## Report to the solver (`tasks/answer-s2/instruction.md`)
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

## Tests (`tasks/answer-s2/tests/`)
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
- **Wrong-fix patches** go in `build/answer-s2/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/answer-s2/`:**
- `instruction.md`;
- `task.toml`, from `common/builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/answer-s2/manifest.json`:**
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

**Also in `build/answer-s2/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `common/builder/templates/` and `common/trial/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I common/gate/gate.py answer-s2 --only static
python3 -I common/gate/gate.py answer-s2 --only nop
python3 -I common/gate/gate.py answer-s2 --only oracle
python3 -I common/gate/gate.py answer-s2 --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/answer-s2/`;
  - edit only `tasks/answer-s2/`, `build/answer-s2/` and, for pattern B, the register;
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
