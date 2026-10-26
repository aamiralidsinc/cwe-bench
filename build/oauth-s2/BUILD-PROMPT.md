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

Project root: `/home/mara/cwe-bench`. Task: `oauth-s2`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: ["GHSA-G7VJ-C29H-3H5M", "CVE-2026-92161"]; friendsofflarum/oauth; insufficient verification of data authenticity (CWE-345): provider-asserted email trusted without proof, giving account takeover on signup/login
- Pinned (vulnerable) commit: 43e763c6cad1fd593d91df45a710578df423f4a3. Published fix: baca3466b3b7be51c70a7e0ba966901aefeb344a, bb4bf376832e6bb68c579715d2a4b5a92c4a2567.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v2",
 "model": "deepseek-flash",
 "entry_id": "34370",
 "advisory_ids": [
  "GHSA-G7VJ-C29H-3H5M",
  "CVE-2026-92161"
 ],
 "repo": "friendsofflarum/oauth",
 "pinned_commit": "43e763c6cad1fd593d91df45a710578df423f4a3",
 "fix_commits": [
  "baca3466b3b7be51c70a7e0ba966901aefeb344a",
  "bb4bf376832e6bb68c579715d2a4b5a92c4a2567"
 ],
 "trust_decision": {
  "summary": "Whether the email a provider returns is proven verified decides between Registration::provideTrustedEmail (auto-trusted: the login is matched to an existing account with that address) and Registration::suggestEmail (untrusted suggestion); at the pinned commit every provider calls provideTrustedEmail unconditionally, inside its own suggestions() at the provider-to-Flarum Registration boundary, never in the controllers.",
  "evidence": [
   "src/Providers/Discord.php:63",
   "src/Providers/GitLab.php:66",
   "src/Providers/Google.php:68",
   "src/Providers/LinkedIn.php:69",
   "src/Providers/Facebook.php:54",
   "src/Providers/GitHub.php:64",
   "src/Providers/Twitter.php:70",
   "src/Provider.php:59-62",
   "src/Controllers/AuthController.php:79-86"
  ]
 },
 "landing_point": {
  "where": "src/Providers/Discord.php:63",
  "why": "The advisory names Discord, so an engineer opens src/Providers/Discord.php and finds the unconditional provideTrustedEmail at the end of suggestions(); the only nearby guard, verifyEmail at src/Provider.php:76-81, merely rejects null/empty, so the line reads as the sink."
 },
 "fix_sites": [
  {
   "where": "src/Providers/Discord.php:62-65 (fix.diff:32-37)",
   "entry_point": "GET /auth/discord -> Controllers/AuthController::setSuggestions -> Discord::suggestions (route built from src/OAuth2RoutePattern.php:40, registered at src/OAuthServiceProvider.php:40)",
   "module_kind": "provider adapter (third-party OAuth2 client wrapper)"
  },
  {
   "where": "src/Providers/GitLab.php:65-68 (fix.diff:114-120)",
   "entry_point": "GET /auth/gitlab -> Controllers/AuthController::setSuggestions -> GitLab::suggestions",
   "module_kind": "provider adapter (third-party OAuth2 client wrapper)"
  },
  {
   "where": "src/Providers/Google.php:67-70 (fix.diff:153-157)",
   "entry_point": "GET /auth/google -> Controllers/AuthController::setSuggestions -> Google::suggestions",
   "module_kind": "provider adapter (third-party OAuth2 client wrapper)"
  },
  {
   "where": "src/Providers/LinkedIn.php:68-71 (fix.diff:187-191)",
   "entry_point": "GET /auth/linkedin -> Controllers/AuthController::setSuggestions -> LinkedIn::suggestions",
   "module_kind": "provider adapter over an in-repo custom league client (src/Providers/Custom/LinkedIn/Provider/LinkedIn.php)"
  },
  {
   "where": "src/Providers/Facebook.php:53-56 (fix.diff:63-65)",
   "entry_point": "GET /auth/facebook -> Controllers/AuthController::setSuggestions -> Facebook::suggestions",
   "module_kind": "provider adapter; docblock only, no behaviour change in the diff"
  },
  {
   "where": "src/Providers/GitHub.php:63-66 (fix.diff:85-87)",
   "entry_point": "GET /auth/github -> Controllers/AuthController::setSuggestions -> GitHub::suggestions",
   "module_kind": "provider adapter; docblock only, no behaviour change in the diff"
  }
 ],
 "O1_entry_points": 4,
 "O2_out_of_scope_site": {
  "kind": "second_implementation",
  "where": "src/Providers/Twitter.php:70 (OAuth1 transport, reached only through src/Controllers/TwitterAuthController.php:125-131, provider excluded from the shared route at src/Providers/Twitter.php:39-42)"
 },
 "O3_reason_to_dismiss": "Twitter is a separate OAuth1 code path with its own controller and no resource-owner payload containing any verification attribute, so after the published fix only touched providers that expose a verified/confirmed field, a solver can read Twitter's unconditional provideTrustedEmail as an accepted design (Twitter returns an already-confirmed account email) rather than an untouched sibling.",
 "O4_distance": {
  "files": 5,
  "packages": 0,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Verified-email fast path plus the payload chain must keep working: a genuinely verified provider email must still auto-link/log the user into the existing account, and setPayload()/getPayload() must keep feeding the avatar merge, so an over-broad 'always suggestEmail' (or a rewrite of the shared src/Provider.php helper) breaks login-for-existing-users and avatar assignment. The in-tree integration test's GitLab resource owner carries no confirmed_at, so it also shows the gate demoting a login to a suggestion.",
  "where": "src/Provider.php:92-105 (provideAvatar reads and rewrites the payload), src/Listeners/AssignToUser.php:64 (avatar URL read from the payload), tests/integration/AuthenticationFlowTest.php:60-95 with the resource owner built at tests/integration/AuthenticationFlowTest.php:137, src/Listeners/UpdateEmailFromProvider.php:37-46 with the default at extend.php:61"
 },
 "O6_input_shapes": [
  "boolean payload key read as an array: $payload['verified'] ?? false (Discord, fix.diff:33)",
  "timestamp/string payload key tested for emptiness: !empty($payload['confirmed_at']) (GitLab, fix.diff:116)",
  "boolean attribute read through the resource owner accessor: $user->getAttribute('email_verified') (LinkedIn, fix.diff:187), with email_verified requested in src/Providers/Custom/LinkedIn/Provider/LinkedIn.php:42-44",
  "vendor helper method instead of a raw key: $user->isEmailTrustworthy() (Google, fix.diff:153)",
  "payload extracted once into $payload = $user->toArray() and reused for setPayload(), so the check sees the same array the app persists (Discord/GitLab, fix.diff:31,114)"
 ],
 "O7_producer": {
  "kind": "mapper",
  "where": "Resource-owner mappers supply the verification attribute: in-tree src/Providers/Custom/LinkedIn/Provider/LinkedInResourceOwner.php:59-62 and :215-218 (raw userinfo array), while the Discord/Facebook/GitHub/Google/GitLab resource owners are vendor mappers pulled in at composer.json:34-39 and are not vendored in this tree",
  "check_calls_producer": true
 },
 "O8_uncovered_routes": [
  {
   "route": "GET /auth/twitter -> TwitterAuthController::work -> Twitter::suggestions still calls provideTrustedEmail unconditionally for an OAuth1 user object",
   "where": "src/Providers/Twitter.php:70",
   "reason_to_dismiss": "OAuth1 Twitter has no verification attribute at all and the fix deliberately left this file untouched, so it reads as an unsupported/legacy combination outside the advisory's Discord report.",
   "distance": "1 controller + 1 provider file away from the landing point, in a different transport (league/oauth1-client, src/Providers/Twitter.php:49-56) than the shared OAuth2 route",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "GET /auth/facebook -> AuthController::setSuggestions -> Facebook::suggestions calls provideTrustedEmail unconditionally; the published fix only added a docblock to this file",
   "where": "src/Providers/Facebook.php:54",
   "reason_to_dismiss": "Facebook's Graph API exposes no email-verification field, so a 'cannot check it, so leave it' reading is plausible, and the fix touching the file with a docblock only looks like a deliberate decision that Facebook is safe.",
   "distance": "1 sibling file in the same directory as the landing point (src/Providers/)",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "GET /auth/github -> AuthController::setSuggestions -> GitHub::suggestions calls provideTrustedEmail unconditionally on the profile email; only the API fallback path filters verified addresses",
   "where": "src/Providers/GitHub.php:64",
   "reason_to_dismiss": "GitHub's getEmailFromApi already checks primary AND verified (src/Providers/GitHub.php:81-85), so a solver can argue the provider is covered elsewhere and the top-level trust is fine.",
   "distance": "1 sibling file in src/Providers/",
   "present_in_latest": "unknown",
   "latest_where": ""
  }
 ],
 "O8b_injection_room": [
  {
   "where": "src/Provider.php:59-62",
   "sibling": "A shared protected helper on the abstract Provider (e.g. trustEmailOrSuggest(Registration, $email, bool $trusted)) that every provider calls",
   "why_realistic": "The base class already owns the shared helpers verifyEmail and provideAvatar, so a maintainer de-duplicating six near-identical suggestions() bodies would naturally land the trust gate here, which then also covers the Twitter path at src/Providers/Twitter.php:70."
  },
  {
   "where": "src/Controllers/AuthController.php:79-86",
   "sibling": "A controller-side gate that inspects the resource owner before/after the provider's suggestions() and downgrades the trusted email",
   "why_realistic": "setSuggestions already wraps every provider call and dispatches SettingSuggestions, so it is the obvious place for a cross-provider policy, and a maintainer would then have to duplicate it in src/Controllers/TwitterAuthController.php:125-131."
  },
  {
   "where": "src/Providers/Custom/LinkedIn/Provider/LinkedInResourceOwner.php:59-62",
   "sibling": "A getEmailVerified()/isEmailTrustworthy() helper on this in-repo resource owner, with 'email_verified' removed from the requested fields list at src/Providers/Custom/LinkedIn/Provider/LinkedIn.php:42-44",
   "why_realistic": "This class already implements feature-by-feature accessors (getEmail, getFirstName, getId) and its fields array is configurable, so a maintainer could centralise the check there or forget to keep requesting the email_verified field."
  },
  {
   "where": "src/Jobs/CheckAndUpdateUserEmail.php:70-83",
   "sibling": "A gate on the email-change-on-login job that consults the provider's verification state before writing the provider email onto the linked user",
   "why_realistic": "This job already rewrites a user's email from the provider on every login when update_email_from_provider is on (default true at extend.php:61), so a maintainer extending the same property would have to decide whether an unverified provider email may overwrite the account address."
  }
 ],
 "O9_family": "insufficient verification of data authenticity (CWE-345): provider-asserted email trusted without proof, giving account takeover on signup/login",
 "O9_dos": false,
 "O10_build": {
  "language": "PHP",
  "toolchain": "Composer; PHP ^7.4 || ^8.0 (composer.json:31), flarum/core ^1.8.1 plus league/oauth1-client, league/oauth2-{facebook,github,google}, omines/oauth2-gitlab, wohali/oauth2-discord-new (composer.json:30-39); tests run with phpunit via composer scripts test:unit / test:integration (composer.json:97-103) using tests/phpunit.integration.xml",
  "services": [
   "MySQL/MariaDB database for the Flarum integration-test bootstrap (tests/integration/setup.php:12-18)"
  ],
  "offline_after_build": true,
  "project_tests": "tests/integration/AuthenticationFlowTest.php:60-95 drives GET /auth/gitlab end to end with a mocked Gitlab provider and resource owner (:117-149) and asserts the login completes; tests/integration/api/ForumSerializerTest.php and tests/integration/api/CurrentUserAttributesTest.php cover the serializers. No test asserts trusted-versus-suggested email, and the mocked GitlabResourceOwner at tests/integration/AuthenticationFlowTest.php:137 carries only id+email, i.e. no confirmed_at, so provider behaviour can be exercised offline without network."
 },
 "O11_fix_minutes": 35,
 "O12_red_flags": [
  "tiny_repo"
 ],
 "O13_recall_risk": "medium",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "src/Providers/Discord.php, src/Providers/Facebook.php, src/Providers/GitHub.php, src/Providers/GitLab.php, src/Providers/Google.php, src/Providers/LinkedIn.php",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 0,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "In src/Providers/Discord.php only, swap provideTrustedEmail for `$payload['verified'] ? provideTrustedEmail : suggestEmail` (or make it suggestEmail outright) and leave the other five providers, especially the OAuth1 Twitter path, trusting unconditionally."
 },
 "out_of_scope_notes": [
  "The second listed fix commit bb4bf37 has context lines with `suggestions(Registration $registration, mixed $user, ...)`, which is not the pinned tree's signature (src/Providers/Discord.php:53), so it targets a different base; only baca3466's hunks apply to this commit.",
  "Third-party providers registered through src/Extend/RegisterProvider.php and the SettingSuggestions event (src/Controllers/AuthController.php:83-85) are supplied outside this repository."
 ],
 "unverified": [
  "Repo size in MB: no shell was available in this session, so tiny_repo was judged from the tree's breadth (25 PHP source files under src/ plus a small js/src tree) rather than measured; O4 repo_mb is left null.",
  "Vendor resource-owner behaviour (Wohali DiscordResourceOwner verified key, league FacebookUser/GithubResourceOwner, league/oauth2-google GoogleUser::isEmailTrustworthy, Omines GitlabResourceOwner confirmed_at) is not vendored at the pinned commit and could not be read, so the exact semantics of each attribute are unconfirmed.",
  "Flarum core Registration::provideTrustedEmail versus suggestEmail semantics come from the call sites here; flarum/core is not vendored so the account-matching behaviour behind them is inferred, not read.",
  "present_in_latest for all three O8 routes: only the pinned tree and the fix diff were available and the inputs say 'latest release: none', so no later tree could be checked; the fix diff does not modify src/Providers/Twitter.php, src/Providers/Facebook.php:54 or src/Providers/GitHub.php:64.",
  "regression_tests_in_pinned_commit not flagged: the fix diff adds or changes no test files at all."
 ]
}
  ```
- Published fix sites:   - src/Providers/Discord.php:62-65 (fix.diff:32-37) — entry point: GET /auth/discord -> Controllers/AuthController::setSuggestions -> Discord::suggestions (route built from src/OAuth2RoutePattern.php:40, registered at src/OAuthServiceProvider.php:40) [provider adapter (third-party OAuth2 client wrapper)]
  - src/Providers/GitLab.php:65-68 (fix.diff:114-120) — entry point: GET /auth/gitlab -> Controllers/AuthController::setSuggestions -> GitLab::suggestions [provider adapter (third-party OAuth2 client wrapper)]
  - src/Providers/Google.php:67-70 (fix.diff:153-157) — entry point: GET /auth/google -> Controllers/AuthController::setSuggestions -> Google::suggestions [provider adapter (third-party OAuth2 client wrapper)]
  - src/Providers/LinkedIn.php:68-71 (fix.diff:187-191) — entry point: GET /auth/linkedin -> Controllers/AuthController::setSuggestions -> LinkedIn::suggestions [provider adapter over an in-repo custom league client (src/Providers/Custom/LinkedIn/Provider/LinkedIn.php)]
  - src/Providers/Facebook.php:53-56 (fix.diff:63-65) — entry point: GET /auth/facebook -> Controllers/AuthController::setSuggestions -> Facebook::suggestions [provider adapter; docblock only, no behaviour change in the diff]
  - src/Providers/GitHub.php:63-66 (fix.diff:85-87) — entry point: GET /auth/github -> Controllers/AuthController::setSuggestions -> GitHub::suggestions [provider adapter; docblock only, no behaviour change in the diff]
- Uncovered routes to confirm (pattern B):   - src/Providers/Twitter.php:70 — GET /auth/twitter -> TwitterAuthController::work -> Twitter::suggestions still calls provideTrustedEmail unconditionally for an OAuth1 user object (reason to dismiss: OAuth1 Twitter has no verification attribute at all and the fix deliberately left this file untouched, so it reads as an unsupported/legacy combination outside the advisory's Discord report.; still in latest: unknown)
  - src/Providers/Facebook.php:54 — GET /auth/facebook -> AuthController::setSuggestions -> Facebook::suggestions calls provideTrustedEmail unconditionally; the published fix only added a docblock to this file (reason to dismiss: Facebook's Graph API exposes no email-verification field, so a 'cannot check it, so leave it' reading is plausible, and the fix touching the file with a docblock only looks like a deliberate decision that Facebook is safe.; still in latest: unknown)
  - src/Providers/GitHub.php:64 — GET /auth/github -> AuthController::setSuggestions -> GitHub::suggestions calls provideTrustedEmail unconditionally on the profile email; only the API fallback path filters verified addresses (reason to dismiss: GitHub's getEmailFromApi already checks primary AND verified (src/Providers/GitHub.php:81-85), so a solver can argue the provider is covered elsewhere and the top-level trust is fine.; still in latest: unknown)
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

## Environment (`tasks/oauth-s2/environment/Dockerfile`)
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

## Report to the solver (`tasks/oauth-s2/instruction.md`)
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

## Tests (`tasks/oauth-s2/tests/`)
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
- **Wrong-fix patches** go in `build/oauth-s2/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/oauth-s2/`:**
- `instruction.md`;
- `task.toml`, from `common/builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/oauth-s2/manifest.json`:**
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

**Also in `build/oauth-s2/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `common/builder/templates/` and `common/trial/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I common/gate/gate.py oauth-s2 --only static
python3 -I common/gate/gate.py oauth-s2 --only nop
python3 -I common/gate/gate.py oauth-s2 --only oracle
python3 -I common/gate/gate.py oauth-s2 --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/oauth-s2/`;
  - edit only `tasks/oauth-s2/`, `build/oauth-s2/` and, for pattern B, the register;
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
