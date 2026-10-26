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

Project root: `/home/mara/cwe-bench`. Task: `electron-builder-mm`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: ["GHSA-P2F4-R6V6-J797", "CVE-2026-54673"]; electron-userland/electron-builder; credential leakage across a trust boundary (CWE-200): sensitive request headers forwarded on cross-origin redirect, plus secret redaction in logs/errors
- Pinned (vulnerable) commit: parent of 22a7532bd01b9fb42cff7c58d599c7ad683569fe (parent_commit not given in candidate). Published fix: 22a7532bd01b9fb42cff7c58d599c7ad683569fe.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "12765",
 "advisory_ids": [
  "GHSA-P2F4-R6V6-J797",
  "CVE-2026-54673"
 ],
 "repo": "electron-userland/electron-builder",
 "pinned_commit": "parent of 22a7532bd01b9fb42cff7c58d599c7ad683569fe (parent_commit not given in candidate)",
 "fix_commits": [
  "22a7532bd01b9fb42cff7c58d599c7ad683569fe"
 ],
 "trust_decision": {
  "summary": "On a redirect, HttpExecutor.prepareRedirectUrlOptions decides whether credential headers may follow to the new origin; at the pinned commit it only strips the exact lowercase `authorization` key, so PRIVATE-TOKEN, `Authorization`, X-Api-Key etc. are forwarded cross-origin. Under Electron the decision only runs when the request uses redirect:\"manual\".",
  "evidence": [
   "packages/builder-util-runtime/src/httpExecutor.ts:320-337",
   "packages/builder-util-runtime/src/httpExecutor.ts:323",
   "packages/builder-util-runtime/src/httpExecutor.ts:350-385",
   "packages/electron-updater/src/electronHttpExecutor.ts:76-94",
   "packages/electron-updater/src/providers/GitLabProvider.ts:224-239"
  ]
 },
 "landing_point": {
  "where": "packages/builder-util-runtime/src/httpExecutor.ts:323",
  "why": "The summary names builder-util-runtime, cross-origin redirect and Authorization; prepareRedirectUrlOptions is the only redirect-strip function and line 323 checks only `headers?.authorization`."
 },
 "fix_sites": [
  {
   "where": "packages/builder-util-runtime/src/httpExecutor.ts:320-337",
   "entry_point": "HttpExecutor.prepareRedirectUrlOptions (public static), reached by AppUpdater.checkForUpdates/downloadUpdate via ElectronHttpExecutor redirect handler and by electron-builder publish via NodeHttpExecutor.handleResponse (httpExecutor.ts:183-189)",
   "module_kind": "core HTTP library (builder-util-runtime)"
  },
  {
   "where": "packages/electron-updater/src/providers/GitLabProvider.ts:53-55",
   "entry_point": "AppUpdater.checkForUpdates with provider: gitlab (new createRequestOptions override forcing redirect:\"manual\", fix.diff:329-333)",
   "module_kind": "wrapper/provider in another package (electron-updater)"
  },
  {
   "where": "packages/builder-util-runtime/src/httpExecutor.ts:586-600",
   "entry_point": "safeStringifyJson (public API, debug logging of request options/body)",
   "module_kind": "core HTTP library log redaction"
  },
  {
   "where": "packages/builder-util-runtime/src/httpExecutor.ts:90",
   "entry_point": "HttpExecutor.request with JSON body under DEBUG=electron-builder",
   "module_kind": "core HTTP library log redaction"
  },
  {
   "where": "packages/builder-util-runtime/src/httpExecutor.ts:209",
   "entry_point": "HttpExecutor.doApiRequest error message for >=400 JSON responses",
   "module_kind": "core HTTP library error text"
  },
  {
   "where": "packages/builder-util/src/util.ts:51",
   "entry_point": "removePassword (used for exec/spawn logging in electron-builder CLI)",
   "module_kind": "build-time utility"
  },
  {
   "where": "packages/builder-util/src/util.ts:93",
   "entry_point": "stripSensitiveEnvVars (build-time utility)",
   "module_kind": "build-time utility"
  },
  {
   "where": "packages/builder-util/src/util.ts:103",
   "entry_point": "filterSensitiveEnv (build-time utility)",
   "module_kind": "build-time utility"
  },
  {
   "where": "packages/builder-util/src/util.ts:186",
   "entry_point": "exec() error message stdout (electron-builder CLI)",
   "module_kind": "build-time utility"
  },
  {
   "where": "packages/builder-util/src/util.ts:192",
   "entry_point": "exec() error message stderr (electron-builder CLI)",
   "module_kind": "build-time utility"
  },
  {
   "where": "packages/electron-publish/src/gitHubPublisher.ts:61",
   "entry_point": "electron-builder --publish with GitHub provider (invalid token error text)",
   "module_kind": "publisher"
  },
  {
   "where": "packages/electron-publish/src/gitlabPublisher.ts:49",
   "entry_point": "electron-builder --publish with GitLab provider (invalid token error text)",
   "module_kind": "publisher"
  },
  {
   "where": "packages/electron-publish/src/keygenPublisher.ts:182",
   "entry_point": "electron-builder --publish with Keygen provider (debug log of create-artifact body)",
   "module_kind": "publisher"
  },
  {
   "where": "packages/electron-publish/src/keygenPublisher.ts:254",
   "entry_point": "electron-builder --publish with Keygen provider (debug log of create-release body)",
   "module_kind": "publisher"
  }
 ],
 "O1_entry_points": 4,
 "O2_out_of_scope_site": {
  "kind": "wrapper_or_composition",
  "where": "packages/electron-updater/src/providers/GitLabProvider.ts:53-55 (fix adds createRequestOptions override setting redirect:\"manual\", fix.diff:329-333); without it Electron net follows redirects itself and electronHttpExecutor.ts:83-92 never calls prepareRedirectUrlOptions"
 },
 "O3_reason_to_dismiss": "Once prepareRedirectUrlOptions strips PRIVATE-TOKEN case-insensitively, the unit tests through the static helper pass, and the code comments say 'Electron net handles redirects automatically' (DifferentialDownloader.ts:238, multipleRangeDownloader.ts:124), so a solver can argue the provider/request-mode layer is outside the redirect-strip fix.",
 "O4_distance": {
  "files": 6,
  "packages": 4,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Same-origin redirects and the http->https same-host upgrade must keep PRIVATE-TOKEN/Authorization, and non-credential headers (User-Agent, Accept, range) must survive cross-origin redirects; an over-broad fix that drops all headers or strips on every redirect breaks GitLab/private-GitHub asset downloads.",
  "where": "packages/builder-util-runtime/src/httpExecutor.ts:360-369; fix.diff:412-425"
 },
 "O6_input_shapes": [
  "lowercase `authorization` (pre-existing)",
  "mixed-case `Authorization` and all-caps `AUTHORIZATION`",
  "`PRIVATE-TOKEN` (GitLab, hyphenated)",
  "underscore variants `PRIVATE_TOKEN`, `X_API_KEY`, `X_CSRF_TOKEN`",
  "other credential headers: Proxy-Authorization, X-Api-Key, X-Auth-Token, X-Access-Token, X-Gitlab-Token, Cookie",
  "several credential headers in one request alongside non-sensitive ones",
  "log redaction: camelCase/snake_case/UPPER field names containing token/password/secret/auth/credential/apikey/passphrase or ending in key"
 ],
 "O7_producer": {
  "kind": "mapper",
  "where": "packages/electron-updater/src/providers/GitLabProvider.ts:224-239 maps options.token to `PRIVATE-TOKEN` or `authorization`; packages/electron-updater/src/providers/Provider.ts:82-94 sets the request mode",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "Single-range differential download handles Electron 'redirect' by followRedirect() with unchanged headers and rewrites requestOptions to the new host, so all later range requests send requestHeaders/addAuthHeader/PrivateGitHub credentials to the redirect origin without prepareRedirectUrlOptions",
   "where": "packages/electron-updater/src/differentialDownloader/DifferentialDownloader.ts:260-264",
   "reason_to_dismiss": "Differential download is a blockmap optimisation in another subsystem, and the comment at :238 says Electron net handles redirects.",
   "distance": "different package (electron-updater) and subdirectory from builder-util-runtime/httpExecutor.ts; headers come from AppUpdater.ts:628-637 and DifferentialDownloader.ts:42-53",
   "present_in_latest": "yes",
   "latest_where": "latest/packages/electron-updater/src/differentialDownloader/DifferentialDownloader.ts:260-264"
  },
  {
   "route": "Multiple-range differential download builds requests without redirect:\"manual\" and registers no redirect handler, so Electron net auto-follows with all custom credential headers",
   "where": "packages/electron-updater/src/differentialDownloader/multipleRangeDownloader.ts:71-73",
   "reason_to_dismiss": "Comment at multipleRangeDownloader.ts:124 states Electron net handles redirects automatically; GitLab disables multi-range (GitLabProvider.ts:45-46).",
   "distance": "different package and subdirectory from the landing point",
   "present_in_latest": "unknown",
   "latest_where": "latest/packages/electron-updater/src/differentialDownloader/multipleRangeDownloader.ts:157"
  },
  {
   "route": "Metadata requests from Generic/GitHub/Bitbucket/Keygen providers go through Provider.createRequestOptions without redirect:\"manual\", so user requestHeaders (e.g. PRIVATE-TOKEN or X-Api-Key set via requestHeaders) follow Electron's automatic redirects unchecked",
   "where": "packages/electron-updater/src/providers/Provider.ts:82-94",
   "reason_to_dismiss": "Only GitLab and private GitHub send tokens themselves; credentials on other providers are user-supplied requestHeaders, a neighbouring feature.",
   "distance": "different package (electron-updater) from the landing point",
   "present_in_latest": "yes",
   "latest_where": "latest/packages/electron-updater/src/providers/Provider.ts:96-103"
  }
 ],
 "O8b_injection_room": [
  {
   "where": "packages/electron-updater/src/providers/Provider.ts:82-94",
   "sibling": "A further token-bearing provider (e.g. a self-hosted Gitea-style provider) that adds its own credential header but does not force redirect:\"manual\"",
   "why_realistic": "PrivateGitHubProvider.ts:26-30 shows the redirect-mode override is opt-in per provider, so a maintainer adding a provider could easily omit it."
  },
  {
   "where": "packages/electron-updater/src/electronHttpExecutor.ts:23-49",
   "sibling": "A second download helper (e.g. a buffer/stream variant) that builds requestOptions without redirect:\"manual\"",
   "why_realistic": "download() and downloadToBuffer (httpExecutor.ts:225-234) each set redirect:\"manual\" by hand, so a new helper could omit it."
  }
 ],
 "O9_family": "credential leakage across a trust boundary (CWE-200): sensitive request headers forwarded on cross-origin redirect, plus secret redaction in logs/errors",
 "O9_dos": false,
 "O10_build": {
  "language": "TypeScript",
  "toolchain": "Node.js + pnpm (packageManager pnpm@11.1.0), tsc --build, vitest",
  "services": [],
  "offline_after_build": true,
  "project_tests": "test/src/httpExecutorTest.ts (prepareRedirectUrlOptions unit tests), test/src/provider/gitlabProviderTest.ts (GitLab header selection, mocked executor)"
 },
 "O11_fix_minutes": 45,
 "O12_red_flags": [],
 "O13_recall_risk": "low",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "packages/builder-util-runtime/src/httpExecutor.ts, packages/builder-util-runtime/src/index.ts, packages/builder-util/src/util.ts, packages/electron-publish/src/gitHubPublisher.ts, packages/electron-publish/src/gitlabPublisher.ts, packages/electron-publish/src/keygenPublisher.ts, packages/electron-updater/src/providers/GitLabProvider.ts",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Add `|| headers['PRIVATE-TOKEN']` and a case-insensitive authorization delete in prepareRedirectUrlOptions, leaving GitLabProvider on Electron's automatic redirects and the differential-downloader followRedirect untouched."
 },
 "out_of_scope_notes": [
  "prepareRedirectUrlOptions shallow-copies options ({ ...options }, httpExecutor.ts:321), so deleting from headers also changes the caller's shared headers object; this is a correctness issue, not this advisory.",
  "Latest upstream adds Provider.feedBaseUrl origin-gating for download headers (latest/packages/electron-updater/src/providers/Provider.ts:71-79), which suggests later related advisories exist.",
  "The fix bundles unrelated log/error redaction (safeStringifyJson, removePassword, publisher error text), which widens the published fix beyond the redirect protection."
 ],
 "unverified": [
  "pinned_commit hash: parent_commit is null in the candidate and no git metadata was checked.",
  "Whether Electron/Chromium net in 'follow' mode itself drops Authorization on cross-origin redirects; it is assumed not to drop PRIVATE-TOKEN or X-* headers. This affects the severity of the O8 routes but not their existence.",
  "Whether latest multipleRangeDownloader still builds requests without redirect:\"manual\"; only the comment at latest :157 was seen.",
  "Whether latest AppUpdater feedBaseUrl gating (latest/packages/electron-updater/src/AppUpdater.ts:926-975) already removes credential headers before the DifferentialDownloader redirect route is reached.",
  "repo_mb: size not measured.",
  "Exercising the Electron-net routes (O2, O8) needs an Electron runtime or mocks; the central helper is plain Node-testable.",
  "O13 recall risk: the advisory is dated 2026-07-24, after the model's knowledge cutoff, so write-up coverage was not checked."
 ]
}
  ```
- Published fix sites:   - packages/builder-util-runtime/src/httpExecutor.ts:320-337 — entry point: HttpExecutor.prepareRedirectUrlOptions (public static), reached by AppUpdater.checkForUpdates/downloadUpdate via ElectronHttpExecutor redirect handler and by electron-builder publish via NodeHttpExecutor.handleResponse (httpExecutor.ts:183-189) [core HTTP library (builder-util-runtime)]
  - packages/electron-updater/src/providers/GitLabProvider.ts:53-55 — entry point: AppUpdater.checkForUpdates with provider: gitlab (new createRequestOptions override forcing redirect:"manual", fix.diff:329-333) [wrapper/provider in another package (electron-updater)]
  - packages/builder-util-runtime/src/httpExecutor.ts:586-600 — entry point: safeStringifyJson (public API, debug logging of request options/body) [core HTTP library log redaction]
  - packages/builder-util-runtime/src/httpExecutor.ts:90 — entry point: HttpExecutor.request with JSON body under DEBUG=electron-builder [core HTTP library log redaction]
  - packages/builder-util-runtime/src/httpExecutor.ts:209 — entry point: HttpExecutor.doApiRequest error message for >=400 JSON responses [core HTTP library error text]
  - packages/builder-util/src/util.ts:51 — entry point: removePassword (used for exec/spawn logging in electron-builder CLI) [build-time utility]
  - packages/builder-util/src/util.ts:93 — entry point: stripSensitiveEnvVars (build-time utility) [build-time utility]
  - packages/builder-util/src/util.ts:103 — entry point: filterSensitiveEnv (build-time utility) [build-time utility]
  - packages/builder-util/src/util.ts:186 — entry point: exec() error message stdout (electron-builder CLI) [build-time utility]
  - packages/builder-util/src/util.ts:192 — entry point: exec() error message stderr (electron-builder CLI) [build-time utility]
  - packages/electron-publish/src/gitHubPublisher.ts:61 — entry point: electron-builder --publish with GitHub provider (invalid token error text) [publisher]
  - packages/electron-publish/src/gitlabPublisher.ts:49 — entry point: electron-builder --publish with GitLab provider (invalid token error text) [publisher]
  - packages/electron-publish/src/keygenPublisher.ts:182 — entry point: electron-builder --publish with Keygen provider (debug log of create-artifact body) [publisher]
  - packages/electron-publish/src/keygenPublisher.ts:254 — entry point: electron-builder --publish with Keygen provider (debug log of create-release body) [publisher]
- Uncovered routes to confirm (pattern B):   - packages/electron-updater/src/differentialDownloader/DifferentialDownloader.ts:260-264 — Single-range differential download handles Electron 'redirect' by followRedirect() with unchanged headers and rewrites requestOptions to the new host, so all later range requests send requestHeaders/addAuthHeader/PrivateGitHub credentials to the redirect origin without prepareRedirectUrlOptions (reason to dismiss: Differential download is a blockmap optimisation in another subsystem, and the comment at :238 says Electron net handles redirects.; still in latest: yes)
  - packages/electron-updater/src/differentialDownloader/multipleRangeDownloader.ts:71-73 — Multiple-range differential download builds requests without redirect:"manual" and registers no redirect handler, so Electron net auto-follows with all custom credential headers (reason to dismiss: Comment at multipleRangeDownloader.ts:124 states Electron net handles redirects automatically; GitLab disables multi-range (GitLabProvider.ts:45-46).; still in latest: unknown)
  - packages/electron-updater/src/providers/Provider.ts:82-94 — Metadata requests from Generic/GitHub/Bitbucket/Keygen providers go through Provider.createRequestOptions without redirect:"manual", so user requestHeaders (e.g. PRIVATE-TOKEN or X-Api-Key set via requestHeaders) follow Electron's automatic redirects unchecked (reason to dismiss: Only GitLab and private GitHub send tokens themselves; credentials on other providers are user-supplied requestHeaders, a neighbouring feature.; still in latest: yes)
- Design plan from the lead: No lead plan is provided for this task — you are the lead as well as the builder. Using the Design section above and the screener record, design the task yourself and WRITE YOUR PLAN in `notes.md` BEFORE you build:
  - choose the main lever and at least one more, each with a DIFFERENT reason a solver would dismiss or skip it;
  - decide the sites, routes and input shapes the security tests will cover;
  - identify the coupled must-keep-working behaviour next to each lever, for the functional tests;
  - for the injected track: decide the realistic sibling gap(s) to add — each must be code a maintainer could plausibly have left, reachable through the real entry point, covered by a stated invariant, and placed where the published fix never touches. Add 2–4 siblings at a recurring trust decision, each with its own reason a solver would skip it;
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
2. **Pattern B: uncovered routes.**
   - Routes into the same protected sink where the advisory's own protection is missing at the
     pinned commit, and which the published fix did not touch.
   - They are unmodified upstream code, so a solver can argue they were never covered.
   - The strongest lever found so far: DeepSeek 6 of 6 on one; both models 0 of 3 on three combined.
3. **Input-shape variants** that the general rule covers but a one-case fix misses (a plain string
   and an array).
4. **A coupled must-keep-working behaviour** next to the sink, tested functionally, so an
   over-broad fix fails. MiMo tends to over-harden.
5. **Producer off the check's path.** The check depends on data produced elsewhere (a schema,
   serializer, cache, mapper or config loader) and does not call it. It counts only if the producer
   is infrastructure, not a request handler.
6. **Injected siblings**, only where the plan asks for them. Each must be:
   - code a maintainer could have written, with no deceptive names or comments;
   - reachable through the real entry point;
   - covered by a stated invariant;
   - placed where the upstream fix never touches.

Aim for at least two levers with **different** reasons to dismiss.

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

## Environment (`tasks/electron-builder-mm/environment/Dockerfile`)
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

## Report to the solver (`tasks/electron-builder-mm/instruction.md`)
**Write:**
- what the system is, at product level;
- one observed impact, with ONE concrete trigger at user level (HTTP request, CLI call or public API
  use);
- the security properties as **invariants**: who may do what to which data, or what attacker input
  must never achieve. Word each so it covers every tested route and shape ("no value of X may …").
  If there are several, give one natural list, never a count;
- every **contract** the tests need:
  - the refusal form ("a client error with no side effect");
  - any interface or field name a test uses;
  - preservation clauses ("works exactly as today");
  - a legitimate magnitude next to any attack magnitude;
- that examples are examples, not the full set;
- the standard constraints block: fix the problem and its close variants; keep legitimate use
  working; do not modify or add tests; do not look up the upstream fix; do not special-case the
  example.

**Never write:**
- file, package, function, class, field or parameter names a user would not see;
- line numbers, the root cause, the fix approach, or a CVE or GHSA id;
- a list of routes, spellings or roles;
- restricting adverbs ("directly", "only via");
- anything that names or paraphrases a far site, an uncovered route or an injected sibling.

Put every identifier that must not appear in `manifest.leak_terms`.

## Tests (`tasks/electron-builder-mm/tests/`)
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
- **Wrong-fix patches** go in `build/electron-builder-mm/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/electron-builder-mm/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/electron-builder-mm/manifest.json`:**
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

**Also in `build/electron-builder-mm/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py electron-builder-mm --only static
python3 -I builder/gate.py electron-builder-mm --only nop
python3 -I builder/gate.py electron-builder-mm --only oracle
python3 -I builder/gate.py electron-builder-mm --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/electron-builder-mm/`;
  - edit only `tasks/electron-builder-mm/`, `build/electron-builder-mm/` and, for pattern B, the register;
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
