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

Project root: `/home/mara/cwe-bench`. Task: `jetty.project-mm`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: ["GHSA-2FVJ-HGJ9-J2GR", "CVE-2026-10050"]; jetty/jetty.project; authentication bypass via lossy character encoding / improper handling of alternate encoding (CWE-173, CWE-303)
- Pinned (vulnerable) commit: parent of 4bcdbc7db387ce9e20e2c7571a7250280466221d (parent_commit not given in candidate; tree at /home/mara/screen5/hosts/22394/repo). Published fix: 4bcdbc7db387ce9e20e2c7571a7250280466221d, d0bb829ccecbf19e3ad3d32f2649b2800f01222d.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "22394",
 "advisory_ids": [
  "GHSA-2FVJ-HGJ9-J2GR",
  "CVE-2026-10050"
 ],
 "repo": "jetty/jetty.project",
 "pinned_commit": "parent of 4bcdbc7db387ce9e20e2c7571a7250280466221d (parent_commit not given in candidate; tree at /home/mara/screen5/hosts/22394/repo)",
 "fix_commits": [
  "4bcdbc7db387ce9e20e2c7571a7250280466221d",
  "d0bb829ccecbf19e3ad3d32f2649b2800f01222d"
 ],
 "trust_decision": {
  "summary": "Server decides a Digest login is valid by recomputing the response hash from username/realm/stored password/URI. Those strings are encoded as ISO-8859-1, which silently maps every non-Latin-1 char to '?', so distinct passwords/usernames collide. Decided in Digest.check of each DigestAuthenticator.",
  "evidence": [
   "jetty-core/jetty-security/src/main/java/org/eclipse/jetty/security/authentication/DigestAuthenticator.java:305-361",
   "jetty-core/jetty-security/src/main/java/org/eclipse/jetty/security/authentication/DigestAuthenticator.java:326-337",
   "jetty-ee9/jetty-ee9-security/src/main/java/org/eclipse/jetty/ee9/security/authentication/DigestAuthenticator.java:330",
   "jetty-ee9/jetty-ee9-security/src/main/java/org/eclipse/jetty/ee9/security/authentication/DigestAuthenticator.java:351-362",
   "jetty-core/jetty-security/src/main/java/org/eclipse/jetty/security/UserPrincipal.java:44"
  ]
 },
 "landing_point": {
  "where": "jetty-core/jetty-security/src/main/java/org/eclipse/jetty/security/authentication/DigestAuthenticator.java:326",
  "why": "The summary names 'Digest Authentication' with 'ISO-8859-1'. Searching for that pairs DigestAuthenticator with StandardCharsets.ISO_8859_1 in the core jetty-security module, where H(A1) is built."
 },
 "fix_sites": [
  {
   "where": "jetty-core/jetty-security/src/main/java/org/eclipse/jetty/security/authentication/DigestAuthenticator.java:326-357",
   "entry_point": "HTTP request with 'Authorization: Digest' header to a core/ee10 SecurityHandler using DigestAuthenticator (validateRequest at :102)",
   "module_kind": "primary server implementation (jetty-core/jetty-security)"
  },
  {
   "where": "jetty-core/jetty-security/src/main/java/org/eclipse/jetty/security/authentication/DigestAuthenticator.java:115-162",
   "entry_point": "same HTTP route; parser rewritten to add username*/userhash and decode the RFC 5987 username (fix.diff:532-647)",
   "module_kind": "primary server implementation (header parsing)"
  },
  {
   "where": "jetty-ee9/jetty-ee9-security/src/main/java/org/eclipse/jetty/ee9/security/authentication/DigestAuthenticator.java:351-382",
   "entry_point": "HTTP request with 'Authorization: Digest' to an ee9 (and generated ee8) servlet SecurityHandler (validateRequest at :111)",
   "module_kind": "second implementation (legacy EE9 servlet environment; ee8 is generated from it)"
  },
  {
   "where": "jetty-core/jetty-client/src/main/java/org/eclipse/jetty/client/DigestAuthentication.java:171-196",
   "entry_point": "public API: HttpClient.getAuthenticationStore().addAuthentication(new DigestAuthentication(...)) -> DigestResult.apply at :164",
   "module_kind": "client-side implementation (different module, jetty-client)"
  }
 ],
 "O1_entry_points": 3,
 "O2_out_of_scope_site": {
  "kind": "second_implementation",
  "where": "jetty-ee9/jetty-ee9-security/src/main/java/org/eclipse/jetty/ee9/security/authentication/DigestAuthenticator.java:351-382 (also covers ee8 by source generation, jetty-ee8/jetty-ee8-security/pom.xml:16)"
 },
 "O3_reason_to_dismiss": "ee9 is a legacy servlet environment with its own copy of the authenticator, and the client is 'not the server doing auth'. Credential.MD5 is Basic/Form password storage, not Digest, and changing its encoding would invalidate existing MD5: hashes.",
 "O4_distance": {
  "files": 4,
  "packages": 4,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Users whose real password is non-ASCII (e.g. a realm.properties user with password '\u20ac') must still authenticate when the client hashes with UTF-8. Pre-hashed MD5: credentials must also keep being used directly as H(A1). An over-broad fix that rejects every non-ASCII/non-Latin-1 credential, or re-hashes MD5 credentials, breaks these.",
  "where": "jetty-core/jetty-security/src/main/java/org/eclipse/jetty/security/authentication/DigestAuthenticator.java:316-321; fix.diff:306-314; fix.diff:327"
 },
 "O6_input_shapes": [
  "non-Latin-1 password in stored credential / client password (A1)",
  "non-Latin-1 plain username= parameter",
  "RFC 5987 username*=UTF-8''... parameter (new in fix, fix.diff:590,636-639,693-709)",
  "userhash=true hashed username (fix.diff:589,621-631)",
  "non-Latin-1 request URI in A2 (fix.diff:1031-1032)",
  "client side: server challenge with/without charset=UTF-8 (fix.diff:89-92,146)"
 ],
 "O7_producer": {
  "kind": "config_loader",
  "where": "jetty-core/jetty-security/src/main/java/org/eclipse/jetty/security/PropertyUserStore.java:187 (Credential.getCredential builds the stored Password/MD5 credential that Digest.check hashes)",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "Credential.MD5.check hashes the submitted password with lossy ISO-8859-1, so non-Latin-1 chars collapse to '?' when a Basic/Form login (e.g. BasicAuthenticator with charset UTF-8) is checked against an MD5: stored credential",
   "where": "jetty-core/jetty-util/src/main/java/org/eclipse/jetty/util/security/Credential.java:213",
   "reason_to_dismiss": "Lives in jetty-util and serves Basic/Form, not Digest. It is a legacy MD5 password format, and changing the encoding breaks hashes already stored by the password tool.",
   "distance": "different module (jetty-core/jetty-util, package org.eclipse.jetty.util.security) from the landing point in jetty-security",
   "present_in_latest": "yes",
   "latest_where": "latest/jetty-core/jetty-util/src/main/java/org/eclipse/jetty/util/security/Credential.java:279"
  },
  {
   "route": "Credential.MD5.digest (producer used by the Password CLI tool to create MD5: entries) encodes with lossy ISO-8859-1, so a non-Latin-1 password is stored as the hash of '?'-substituted text",
   "where": "jetty-core/jetty-util/src/main/java/org/eclipse/jetty/util/security/Credential.java:273",
   "reason_to_dismiss": "An offline CLI helper ('Used only by Command Line Password utility'), not a request path.",
   "distance": "different module (jetty-core/jetty-util)",
   "present_in_latest": "yes",
   "latest_where": "latest/jetty-core/jetty-util/src/main/java/org/eclipse/jetty/util/security/Credential.java:263"
  }
 ],
 "O8b_injection_room": [
  {
   "where": "jetty-core/jetty-security/src/main/java/org/eclipse/jetty/security/authentication/DigestAuthenticator.java:305-309",
   "sibling": "a helper that pre-normalises the plain password via getBytes(ISO_8859_1) before hashing for a pre-hashed 'MD:<alg>' credential",
   "why_realistic": "The fix makes the algorithm configurable (SHA-256), so a maintainer would plausibly add support for pre-hashed SHA-256 H(A1) credentials alongside the MD5 branch."
  },
  {
   "where": "jetty-core/jetty-security/src/main/java/org/eclipse/jetty/security/authentication/BasicAuthenticator.java:64-67",
   "sibling": "a Basic-auth helper that re-encodes the decoded password to ISO-8859-1 before handing it to login",
   "why_realistic": "The same file already defaults to ISO-8859-1 for legacy clients, so a 'compatibility' re-encode would look natural."
  }
 ],
 "O9_family": "authentication bypass via lossy character encoding / improper handling of alternate encoding (CWE-173, CWE-303)",
 "O9_dos": false,
 "O10_build": {
  "language": "Java",
  "toolchain": "Maven (multi-module); JDK 17+ assumed for the jetty-12 line",
  "services": [],
  "offline_after_build": true,
  "project_tests": "jetty-core/jetty-client HttpClientAuthenticationTest (testDigest*); jetty-ee10/jetty-ee10-servlet ConstraintTest (digest()); jetty-ee9/jetty-ee9-security ConstraintTest; ee9/ee10 DigestPostTest integration tests"
 },
 "O11_fix_minutes": 50,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "jetty-core/jetty-security/.../authentication/DigestAuthenticator.java; jetty-ee9/jetty-ee9-security/.../authentication/DigestAuthenticator.java; jetty-core/jetty-client/.../client/DigestAuthentication.java",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 0,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Replace ISO_8859_1 with UTF_8 in the core DigestAuthenticator.Digest.check only, leaving the ee9 copy, the client, and Credential.MD5 untouched."
 },
 "out_of_scope_notes": [
  "The published fix bundles unrelated RFC 7616 hardening: SHA-256 default algorithm, HMAC stateless nonce, opaque verification, request-URI binding, nc length 8, removal of qop-less/auth-int on the client (fix.diff:382-387, 477-497, 610-618, 837-872). Hidden tests must not depend on these.",
  "jetty-ee9/ee10 jaspi BaseAuthModule decodes Basic with ISO-8859-1 (bijective decode, not this mechanism); not pursued.",
  "Credential.Crypt/UnixCrypt char handling not inspected."
 ],
 "unverified": [
  "pinned_commit hash: parent_commit is null in the candidate. The tree given is assumed to be the parent of 4bcdbc7.",
  "repo_mb not measured (no shell). Jetty is a large multi-module repo, so tiny_repo/giant_repo were not asserted.",
  "Contents of the second fix commit d0bb829 are not separately identified in fix.diff.",
  "JDK version requirement not checked in pom.xml.",
  "O8 routes are a different auth scheme (Basic/Form) sharing the password-verification sink (UserPrincipal.authenticate -> Credential.check). Whether a task author counts this as 'same protected sink' is a judgement call.",
  "Whether UnixCrypt (CRYPT: credentials) truncates non-Latin-1 chars was not checked."
 ]
}
  ```
- Published fix sites:   - jetty-core/jetty-security/src/main/java/org/eclipse/jetty/security/authentication/DigestAuthenticator.java:326-357 — entry point: HTTP request with 'Authorization: Digest' header to a core/ee10 SecurityHandler using DigestAuthenticator (validateRequest at :102) [primary server implementation (jetty-core/jetty-security)]
  - jetty-core/jetty-security/src/main/java/org/eclipse/jetty/security/authentication/DigestAuthenticator.java:115-162 — entry point: same HTTP route; parser rewritten to add username*/userhash and decode the RFC 5987 username (fix.diff:532-647) [primary server implementation (header parsing)]
  - jetty-ee9/jetty-ee9-security/src/main/java/org/eclipse/jetty/ee9/security/authentication/DigestAuthenticator.java:351-382 — entry point: HTTP request with 'Authorization: Digest' to an ee9 (and generated ee8) servlet SecurityHandler (validateRequest at :111) [second implementation (legacy EE9 servlet environment; ee8 is generated from it)]
  - jetty-core/jetty-client/src/main/java/org/eclipse/jetty/client/DigestAuthentication.java:171-196 — entry point: public API: HttpClient.getAuthenticationStore().addAuthentication(new DigestAuthentication(...)) -> DigestResult.apply at :164 [client-side implementation (different module, jetty-client)]
- Uncovered routes to confirm (pattern B):   - jetty-core/jetty-util/src/main/java/org/eclipse/jetty/util/security/Credential.java:213 — Credential.MD5.check hashes the submitted password with lossy ISO-8859-1, so non-Latin-1 chars collapse to '?' when a Basic/Form login (e.g. BasicAuthenticator with charset UTF-8) is checked against an MD5: stored credential (reason to dismiss: Lives in jetty-util and serves Basic/Form, not Digest. It is a legacy MD5 password format, and changing the encoding breaks hashes already stored by the password tool.; still in latest: yes)
  - jetty-core/jetty-util/src/main/java/org/eclipse/jetty/util/security/Credential.java:273 — Credential.MD5.digest (producer used by the Password CLI tool to create MD5: entries) encodes with lossy ISO-8859-1, so a non-Latin-1 password is stored as the hash of '?'-substituted text (reason to dismiss: An offline CLI helper ('Used only by Command Line Password utility'), not a request path.; still in latest: yes)
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

## Environment (`tasks/jetty.project-mm/environment/Dockerfile`)
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

## Report to the solver (`tasks/jetty.project-mm/instruction.md`)
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

## Tests (`tasks/jetty.project-mm/tests/`)
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
- **Wrong-fix patches** go in `build/jetty.project-mm/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/jetty.project-mm/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/jetty.project-mm/manifest.json`:**
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

**Also in `build/jetty.project-mm/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py jetty.project-mm --only static
python3 -I builder/gate.py jetty.project-mm --only nop
python3 -I builder/gate.py jetty.project-mm --only oracle
python3 -I builder/gate.py jetty.project-mm --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/jetty.project-mm/`;
  - edit only `tasks/jetty.project-mm/`, `build/jetty.project-mm/` and, for pattern B, the register;
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
