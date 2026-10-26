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

Project root: `/home/mara/cwe-bench`. Task: `tinacms-ds`. Pattern: `A`. Track: `injected`.

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
- Advisory: ["GHSA-8MQ9-5FW2-5RM4", "CVE-2026-59992"]; tinacms/tinacms; Broken access control / object-key path traversal: caller-controlled storage keys are not confined to the configured mediaRoot (CWE-639/CWE-862, A01)
- Pinned (vulnerable) commit: parent of d44558e9b4502d4f4fc2c970d22985339fe2b6ce (parent_commit not given in candidate). Published fix: d44558e9b4502d4f4fc2c970d22985339fe2b6ce.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "9983",
 "advisory_ids": [
  "GHSA-8MQ9-5FW2-5RM4",
  "CVE-2026-59992"
 ],
 "repo": "tinacms/tinacms",
 "pinned_commit": "parent of d44558e9b4502d4f4fc2c970d22985339fe2b6ce (parent_commit not given in candidate)",
 "fix_commits": [
  "d44558e9b4502d4f4fc2c970d22985339fe2b6ce"
 ],
 "trust_decision": {
  "summary": "Each media adapter's Next.js handler decides which bucket/container key an authorized editor may presign, write, delete or list. At the pinned commit it takes the caller-supplied key or directory as-is, with no traversal check and no confinement to the operator's mediaRoot.",
  "evidence": [
   "packages/next-tinacms-s3/src/handlers.ts:68-89",
   "packages/next-tinacms-s3/src/handlers.ts:205-211",
   "packages/next-tinacms-dos/src/handlers.ts:117-121",
   "packages/next-tinacms-azure/src/handlers.ts:62",
   "packages/next-tinacms-cloudinary/src/handlers.ts:195-197"
  ]
 },
 "landing_point": {
  "where": "packages/next-tinacms-s3/src/handlers.ts:68-89",
  "why": "The advisory title names next-tinacms-s3 and 'arbitrary bucket-key write'. The presigned-upload GET branch is the S3 write primitive, and it passes req.query.key straight to getSignedUrl."
 },
 "fix_sites": [
  {
   "where": "packages/next-tinacms-s3/src/handlers.ts:68-89",
   "entry_point": "GET /api/s3/media/upload_url?key=&expiresIn= (createMediaHandler)",
   "module_kind": "primary adapter handler (S3, pages router)"
  },
  {
   "where": "packages/next-tinacms-s3/src/handlers.ts:133-139",
   "entry_point": "GET /api/s3/media?directory= (listMedia)",
   "module_kind": "primary adapter handler (S3)"
  },
  {
   "where": "packages/next-tinacms-s3/src/handlers.ts:205-211",
   "entry_point": "DELETE /api/s3/media/[key] (deleteAsset; mediaRoot newly passed at :93)",
   "module_kind": "primary adapter handler (S3)"
  },
  {
   "where": "packages/next-tinacms-dos/src/handlers.ts:105-121",
   "entry_point": "POST /api/dos/media multipart directory+file (uploadMedia)",
   "module_kind": "second implementation (DigitalOcean Spaces, S3-compatible copy)"
  },
  {
   "where": "packages/next-tinacms-dos/src/handlers.ts:186-192",
   "entry_point": "GET /api/dos/media?directory= (listMedia)",
   "module_kind": "second implementation (DOS)"
  },
  {
   "where": "packages/next-tinacms-dos/src/handlers.ts:255-266",
   "entry_point": "DELETE /api/dos/media/[...key] (deleteAsset, split segments joined; mediaRoot newly passed at :72)",
   "module_kind": "second implementation (DOS)"
  },
  {
   "where": "packages/next-tinacms-azure/src/handlers.ts:51-62",
   "entry_point": "POST route handler, formData directory+filename (createMediaHandlers.POST)",
   "module_kind": "second implementation (Azure Blob, app router, no mediaRoot concept)"
  },
  {
   "where": "packages/next-tinacms-azure/src/handlers.ts:78-79",
   "entry_point": "DELETE route handler params.media (createMediaHandlers.DELETE)",
   "module_kind": "second implementation (Azure)"
  },
  {
   "where": "packages/next-tinacms-azure/src/handlers.ts:118-122",
   "entry_point": "GET route handler ?directory= (createMediaHandlers.GET)",
   "module_kind": "second implementation (Azure)"
  },
  {
   "where": "packages/next-tinacms-cloudinary/src/handlers.ts:73-78",
   "entry_point": "POST /api/cloudinary/media multipart directory+file (uploadMedia)",
   "module_kind": "second implementation (Cloudinary, no mediaRoot concept)"
  },
  {
   "where": "packages/next-tinacms-cloudinary/src/handlers.ts:108-110",
   "entry_point": "GET /api/cloudinary/media?directory= (listMedia; validation only)",
   "module_kind": "second implementation (Cloudinary)"
  },
  {
   "where": "packages/next-tinacms-cloudinary/src/handlers.ts:195-197",
   "entry_point": "DELETE /api/cloudinary/media/[public_id] (deleteAsset)",
   "module_kind": "second implementation (Cloudinary)"
  }
 ],
 "O1_entry_points": 12,
 "O2_out_of_scope_site": {
  "kind": "second_implementation",
  "where": "packages/next-tinacms-azure/src/handlers.ts:62 and packages/next-tinacms-cloudinary/src/handlers.ts:195-197 (sibling adapter packages with no mediaRoot option). The closest twin is packages/next-tinacms-dos/src/handlers.ts:117-121."
 },
 "O3_reason_to_dismiss": "Azure and Cloudinary have no mediaRoot option (the fix itself says so at fix.diff:61-62 and fix.diff:307-308), so a solver can argue there is no boundary to escape there and that an authorized editor already owns the whole container. The listing routes can likewise be dismissed as read-only.",
 "O4_distance": {
  "files": 4,
  "packages": 4,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Deleting an item from the list must keep working. The list mapper returns id = the full object key, already prefixed with mediaRoot, and the client sends that id to DELETE. A fix that always prepends mediaRoot (or rejects keys that already carry it) double-prefixes or breaks delete. Other legitimate behaviour: literal '%' in names must not be re-decoded, inner '..' that stays inside is collapsed rather than rejected, and DOS keys split across route segments must still resolve.",
  "where": "packages/next-tinacms-s3/src/handlers.ts:263-271; packages/next-tinacms-s3/src/s3-media-store.ts:113-115; packages/next-tinacms-dos/src/handlers.ts:257-262; fix.diff:229-235; fix.diff:1124-1125"
 },
 "O6_input_shapes": [
  "query key as string or array (req.query.key[0]) \u2014 packages/next-tinacms-s3/src/handlers.ts:71-75",
  "route key as one segment or split across several segments joined with '/' \u2014 packages/next-tinacms-dos/src/handlers.ts:257-262",
  "multipart body directory + filename combined into one key \u2014 packages/next-tinacms-dos/src/handlers.ts:105-121; packages/next-tinacms-azure/src/handlers.ts:51-62",
  "leading '../', inner a/../../ climbing past the root, percent-encoded %2e%2e and ..%2f \u2014 fix.diff:1142-1148",
  "absolute POSIX path and Windows drive letter \u2014 fix.diff:1143-1144",
  "backslash separator and NUL byte \u2014 fix.diff:1147; fix.diff:1231-1232",
  "empty, whitespace-only or non-string key \u2014 fix.diff:1140-1152",
  "listing directory with leading slash followed by traversal \u2014 fix.diff:1229"
 ],
 "O7_producer": {
  "kind": "mapper",
  "where": "packages/next-tinacms-s3/src/handlers.ts:263-271 (getS3ToTinaFunc sets id = file.Key, which includes mediaRoot); the DOS twin is at packages/next-tinacms-dos/src/handlers.ts:280-290",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [],
 "O8b_injection_room": [
  {
   "where": "packages/next-tinacms-s3/src/handlers.ts:66-96",
   "sibling": "A server-side upload or rename/move branch (PUT/POST with CopyObject/PutObject) next to the presign GET",
   "why_realistic": "DOS already has a server-side POST upload with the same S3 SDK (packages/next-tinacms-dos/src/handlers.ts:69-70). A maintainer adding a non-presigned fallback would copy that code without the key check."
  },
  {
   "where": "packages/next-tinacms-s3/src/handlers.ts:199-223",
   "sibling": "A batch delete (DeleteObjectsCommand) for multi-select deletion in the media manager",
   "why_realistic": "It is a natural feature extension that takes an array of keys from the body, a different input shape from the single route segment the solver reproduces."
  },
  {
   "where": "packages/next-tinacms-azure/src/handlers.ts:13-42",
   "sibling": "An app-router variant of the S3/DOS handlers modelled on Azure's createMediaHandlers",
   "why_realistic": "Azure already ships the app-router style, so a parallel S3 app-router export placed in another file is a plausible second implementation that lower-level tests would miss."
  }
 ],
 "O9_family": "Broken access control / object-key path traversal: caller-controlled storage keys are not confined to the configured mediaRoot (CWE-639/CWE-862, A01)",
 "O9_dos": false,
 "O10_build": {
  "language": "TypeScript",
  "toolchain": "Node 22.x/24.x, pnpm 11.7.0 workspace, turbo, vitest ^2.1.9 (package.json:11,22,41,48)",
  "services": [],
  "offline_after_build": true,
  "project_tests": "None for the adapter handlers at the pinned commit; only tests/build-verification.test.ts exists. The fix adds tests/media-key.test.ts, which tests the pure helper. Hidden handler tests would need a mocked S3Client.send, Azure BlobServiceClient and cloudinary SDK."
 },
 "O11_fix_minutes": 50,
 "O12_red_flags": [],
 "O13_recall_risk": "low",
 "pattern_fit": "A",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "packages/next-tinacms-s3/src/handlers.ts, packages/next-tinacms-dos/src/handlers.ts, packages/next-tinacms-azure/src/handlers.ts, packages/next-tinacms-cloudinary/src/handlers.ts (plus four new byte-identical media-key.ts helpers)",
  "j_sibling_sites": "no",
  "j_cause_other_layer": 0,
  "j_defence_ineffective": 0,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Reject '..' in req.query.key on the S3 presign GET only (string shape), leaving S3 delete/list, the DOS/Azure/Cloudinary copies and mediaRoot confinement untouched."
 },
 "out_of_scope_notes": [
  "packages/next-tinacms-azure/src/delivery-handlers.ts:52-53 mints a read SAS for any context.params.path blob with no auth check and no key validation. It is a read path, not write/delete, and is unchanged in latest/packages/next-tinacms-azure/src/delivery-handlers.ts:52.",
  "Cloudinary listing still interpolates the raw directory into the search expression (fix.diff:336-341 calls it a separate follow-up, SEC-5).",
  "The CLI dev-server media routes (packages/@tinacms/cli/src/next/commands/dev-command/server/media.ts) guard the local filesystem with their own path checks. That is a different sink and was not reviewed."
 ],
 "unverified": [
  "The pinned commit SHA is not given (parent_commit is null); the repo directory is assumed to be the parent of the fix commit.",
  "repo_mb is not measured (no shell); the tree has about 5350 files, so tiny_repo is assumed not to apply.",
  "offline_after_build assumes the cloud SDK clients can be mocked; nothing was run.",
  "Whether the hidden task report can drop the advisory summary's '(and sibling production media adapters)' wording, which would otherwise expose the O2 lever.",
  "recall_risk 'low' rests only on the 2026-08-19 publication date; write-up coverage was not checked."
 ]
}
  ```
- Published fix sites:   - packages/next-tinacms-s3/src/handlers.ts:68-89 — entry point: GET /api/s3/media/upload_url?key=&expiresIn= (createMediaHandler) [primary adapter handler (S3, pages router)]
  - packages/next-tinacms-s3/src/handlers.ts:133-139 — entry point: GET /api/s3/media?directory= (listMedia) [primary adapter handler (S3)]
  - packages/next-tinacms-s3/src/handlers.ts:205-211 — entry point: DELETE /api/s3/media/[key] (deleteAsset; mediaRoot newly passed at :93) [primary adapter handler (S3)]
  - packages/next-tinacms-dos/src/handlers.ts:105-121 — entry point: POST /api/dos/media multipart directory+file (uploadMedia) [second implementation (DigitalOcean Spaces, S3-compatible copy)]
  - packages/next-tinacms-dos/src/handlers.ts:186-192 — entry point: GET /api/dos/media?directory= (listMedia) [second implementation (DOS)]
  - packages/next-tinacms-dos/src/handlers.ts:255-266 — entry point: DELETE /api/dos/media/[...key] (deleteAsset, split segments joined; mediaRoot newly passed at :72) [second implementation (DOS)]
  - packages/next-tinacms-azure/src/handlers.ts:51-62 — entry point: POST route handler, formData directory+filename (createMediaHandlers.POST) [second implementation (Azure Blob, app router, no mediaRoot concept)]
  - packages/next-tinacms-azure/src/handlers.ts:78-79 — entry point: DELETE route handler params.media (createMediaHandlers.DELETE) [second implementation (Azure)]
  - packages/next-tinacms-azure/src/handlers.ts:118-122 — entry point: GET route handler ?directory= (createMediaHandlers.GET) [second implementation (Azure)]
  - packages/next-tinacms-cloudinary/src/handlers.ts:73-78 — entry point: POST /api/cloudinary/media multipart directory+file (uploadMedia) [second implementation (Cloudinary, no mediaRoot concept)]
  - packages/next-tinacms-cloudinary/src/handlers.ts:108-110 — entry point: GET /api/cloudinary/media?directory= (listMedia; validation only) [second implementation (Cloudinary)]
  - packages/next-tinacms-cloudinary/src/handlers.ts:195-197 — entry point: DELETE /api/cloudinary/media/[public_id] (deleteAsset) [second implementation (Cloudinary)]
- Uncovered routes to confirm (pattern B): none
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

## Environment (`tasks/tinacms-ds/environment/Dockerfile`)
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

## Report to the solver (`tasks/tinacms-ds/instruction.md`)
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

## Tests (`tasks/tinacms-ds/tests/`)
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
- **Wrong-fix patches** go in `build/tinacms-ds/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/tinacms-ds/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/tinacms-ds/manifest.json`:**
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

**Also in `build/tinacms-ds/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py tinacms-ds --only static
python3 -I builder/gate.py tinacms-ds --only nop
python3 -I builder/gate.py tinacms-ds --only oracle
python3 -I builder/gate.py tinacms-ds --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/tinacms-ds/`;
  - edit only `tasks/tinacms-ds/`, `build/tinacms-ds/` and, for pattern B, the register;
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
