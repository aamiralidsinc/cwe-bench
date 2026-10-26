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

Project root: `/home/mara/cwe-bench`. Task: `ghost-mm`. Pattern: `A`. Track: `injected`.

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
- Advisory: ["GHSA-HQQ2-XQR2-FMX2", "BIT-GHOST-2026-105644", "CVE-2026-105644"]; tryghost/ghost; unrestricted upload / missing content validation leading to stored XSS (CWE-434 + CWE-79), SVG sanitization gap on import routes
- Pinned (vulnerable) commit: parent of 1be06f4e95a5eb159d14abda7660e689af13cff1 (parent_commit not given in candidate). Published fix: 1be06f4e95a5eb159d14abda7660e689af13cff1.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "11910",
 "advisory_ids": [
  "GHSA-HQQ2-XQR2-FMX2",
  "BIT-GHOST-2026-105644",
  "CVE-2026-105644"
 ],
 "repo": "tryghost/ghost",
 "pinned_commit": "parent of 1be06f4e95a5eb159d14abda7660e689af13cff1 (parent_commit not given in candidate)",
 "fix_commits": [
  "1be06f4e95a5eb159d14abda7660e689af13cff1"
 ],
 "trust_decision": {
  "summary": "Whether a file picked out of an import (or fetched by the media inliner) by extension alone may be stored in image storage and served from the site origin as an image: at the pinned commit only the direct upload middleware sanitizes SVG; the import image handler and the media inliner store bytes as-is with no SVG sanitizing and no content check.",
  "evidence": [
   "ghost/core/core/server/web/api/middleware/upload.js:385-396",
   "ghost/core/core/server/data/importer/handlers/image.js:13-50",
   "ghost/core/core/server/data/importer/import-manager.js:155-157",
   "ghost/core/core/server/services/media-inliner/service.js:22-24",
   "ghost/core/core/server/services/media-inliner/external-media-inliner.js:185-202"
  ]
 },
 "landing_point": {
  "where": "ghost/core/core/server/data/importer/handlers/image.js:13",
  "why": "The summary says 'SVG files in content imports'; ImageHandler.loadFile is the importer's image handler, and the existing sanitizer to copy sits next door in upload.js."
 },
 "fix_sites": [
  {
   "where": "ghost/core/core/server/data/importer/handlers/image.js:13",
   "entry_point": "POST /ghost/api/admin/db (importfile zip, routes.js:375-381) and POST /ghost/api/admin/posts/upload (CSV zip via content-import assets.ts:137)",
   "module_kind": "import handler (landing point)"
  },
  {
   "where": "ghost/core/core/server/services/media-inliner/external-media-inliner.js:185",
   "entry_point": "POST /ghost/api/admin/db/media/inline (routes.js:385) background job; also CSV content import remote media (content-import/import/media.ts:166)",
   "module_kind": "second ingestion pipeline (remote fetch -> saveRaw)"
  },
  {
   "where": "ghost/core/core/server/services/media-inliner/service.js:22",
   "entry_point": "same as media inliner (getMediaStorage dependency injected at service init)",
   "module_kind": "service wiring / storage picker"
  },
  {
   "where": "ghost/core/core/server/services/oembed/oembed-service.js:62",
   "entry_point": "GET /ghost/api/admin/oembed (routes.js:505), bookmark icon/thumbnail processImageFromUrl",
   "module_kind": "neighbouring feature (oembed image fetch + rasterize)"
  },
  {
   "where": "ghost/core/core/server/web/api/middleware/upload.js:347",
   "entry_point": "POST /images/upload (routes.js:450-456), PUT /media/thumbnail/upload (routes.js:466-472), POST /media/upload thumbnail (routes.js:459-465)",
   "module_kind": "upload validation middleware (content check added; sanitizer moved to lib)"
  },
  {
   "where": "ghost/core/core/boot.js:101",
   "entry_point": "process boot; affects every sharp decode (handle-image-sizes, oembed rasterize, image upload processing)",
   "module_kind": "boot-time process-wide config (sharp loader block)"
  },
  {
   "where": "fix.diff:98-205",
   "entry_point": "library used by all the above (new lib/image/image-content.ts)",
   "module_kind": "new shared helper"
  },
  {
   "where": "fix.diff:320-406",
   "entry_point": "library used by importer, inliner, upload middleware (new lib/image/svg-sanitizer.ts)",
   "module_kind": "new shared helper (sanitizer extracted from upload.js)"
  },
  {
   "where": "fix.diff:206-319",
   "entry_point": "boot (new image-decoders.ts, image-formats.ts)",
   "module_kind": "new shared helper"
  }
 ],
 "O1_entry_points": 7,
 "O2_out_of_scope_site": {
  "kind": "second_implementation",
  "where": "ghost/core/core/server/services/media-inliner/external-media-inliner.js:117-202 with storage picker ghost/core/core/server/services/media-inliner/service.js:22-24"
 },
 "O3_reason_to_dismiss": "The media inliner downloads remote URLs in a background job, not files inside the uploaded import archive, so a solver can argue it is a separate 'external media' feature outside 'SVG files in content imports'.",
 "O4_distance": {
  "files": 10,
  "packages": 1,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Legitimate SVG/SVGZ images in an import must still be imported (sanitized in place, not dropped) and real JPEG/PNG/GIF/ICO/WebP must pass with extension aliases (.jpg vs .jpeg); .svg in content/files must keep going to files storage verbatim. Blanket-rejecting SVG or dropping files whose content check fails too strictly breaks these.",
  "where": "ghost/core/core/shared/config/overrides.json:42; fix.diff:1001-1010; ghost/core/core/server/data/importer/content-files.ts:27-35"
 },
 "O6_input_shapes": [
  "plain .svg file in import zip (images/ or content/images/)",
  "gzipped .svgz (sanitized after gunzip, re-gzipped)",
  "uppercase extension (.SVG / .JPG), lowercased before the check",
  "SVG/text content behind a raster extension (e.g. text.png)",
  "mismatched raster content (avif bytes named .jpg)",
  "extension aliases compared by format (.jpg/.jpeg/.jpe/.jfif, .tif/.tiff, .png/.apng, .heic/.heif)",
  "inliner: extension derived from response Content-Type (image/svg+xml) or URL path when file-type cannot detect",
  "buffer input (inliner, oembed) vs file-path input (importer, upload)"
 ],
 "O7_producer": {
  "kind": "mapper",
  "where": "ghost/core/core/server/services/media-inliner/external-media-inliner.js:117-177 (extractFileDataFromResponse derives media.extension from file-type, else Content-Type/URL)",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "Import zip .svg under files/ or content/files/ goes through the generic content-file handler into files storage with no SVG sanitizing",
   "where": "ghost/core/core/server/data/importer/handlers/importer-content-file-handler.js:38-86",
   "reason_to_dismiss": "Files storage is a download store served with an inert content type (.svg -> application/octet-stream), so it is not an image sink.",
   "distance": "same package, sibling handler file next to handlers/image.js; wired in data/importer/content-files.ts:27-35",
   "present_in_latest": "unknown",
   "latest_where": ""
  }
 ],
 "O8b_injection_room": [
  {
   "where": "ghost/core/core/server/data/importer/content-files.ts:15-36",
   "sibling": "An 'images' ImporterContentFileHandler (generic class) for a new asset directory (e.g. CSV importer gallery/thumbnails) that bypasses ImageHandler's validation",
   "why_realistic": "The generic class already supports type 'images' in its JSDoc (importer-content-file-handler.js:5,20); a maintainer adding an asset kind would reuse it instead of ImageHandler."
  },
  {
   "where": "ghost/core/core/server/services/content-import/import/assets.ts:117-137",
   "sibling": "CSV importer path that prepares image assets with its own handler list (deps.handlers) rather than createContentFileHandlers()",
   "why_realistic": "The function already accepts injected handlers; a newer CSV/Substack-style importer could supply its own image handler."
  },
  {
   "where": "ghost/core/core/server/services/oembed/oembed-service.js:215-270",
   "sibling": "A second remote-image fetch (e.g. author avatar or publication icon) that saveRaw()s into image storage with URL-derived extension",
   "why_realistic": "processImageFromUrl is the pattern for fetched images; a parallel helper for another card type is plausible."
  }
 ],
 "O9_family": "unrestricted upload / missing content validation leading to stored XSS (CWE-434 + CWE-79), SVG sanitization gap on import routes",
 "O9_dos": false,
 "O10_build": {
  "language": "JavaScript / TypeScript (Node.js)",
  "toolchain": "pnpm monorepo (pnpm-workspace.yaml), tsc, vitest; native sharp (fix bumps 0.35.4 -> 0.35.5), jsdom + dompurify, file-type (ESM)",
  "services": [
   "SQLite (or MySQL) for DB/e2e tests only; unit tests need none"
  ],
  "offline_after_build": true,
  "project_tests": "ghost/core/test/unit/server/data/importer/handlers/image.test.js, ghost/core/test/unit/server/web/api/middleware/upload.test.js, ghost/core/test/unit/server/services/media-inliner/, ghost/core/test/unit/server/services/oembed/oembed-service.test.js, ghost/core/test/e2e-api/admin/posts-importer.test.js, ghost/core/test/integration/importer/content-import-source.test.ts"
 },
 "O11_fix_minutes": 60,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "A",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "ghost/core/core/boot.js, ghost/core/core/server/data/importer/handlers/image.js, ghost/core/core/server/lib/image/image-content.ts (new), ghost/core/core/server/lib/image/image-decoders.ts (new), ghost/core/core/server/lib/image/image-formats.ts (new), ghost/core/core/server/lib/image/svg-sanitizer.ts (new), ghost/core/core/server/services/media-inliner/external-media-inliner.js, ghost/core/core/server/services/media-inliner/service.js, ghost/core/core/server/services/oembed/oembed-service.js, ghost/core/core/server/web/api/middleware/upload.js",
  "j_sibling_sites": "no",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 0,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Copy upload.js's sanitizeSvg into ImageHandler.loadFile for files ending in .svg only, leaving .svgz, SVG behind raster extensions, and the media inliner untouched."
 },
 "out_of_scope_notes": [
  "Theme zip uploads (routes.js:354) can carry SVG assets served from the site origin; separate sink and trust model, not pursued.",
  "Fix also restricts libvips loaders process-wide at boot (decoder confusion hardening); that is a separate concern from SVG XSS."
 ],
 "unverified": [
  "pinned_commit hash not provided (parent_commit null); assumed the repo dir is the parent of the fix commit.",
  "latest/ tree is absent (latest.txt gives only upstream HEAD d4952f1d), so present_in_latest is unknown.",
  "repo_mb unknown: no size measurement without a shell; ~18k files in tree, likely under 1.5 GB.",
  "O8 route is mitigated at serve time (ghost/core/core/server/adapters/storage/LocalFilesStorage.ts:32-35; S3 import saves carry no file.type, S3Storage.ts:226); treated as not a real sibling gap, hence j_sibling_sites=no.",
  "Advisory text itself was not provided; summary used as the report.",
  "Whether sharp 0.35.5 bump is required for sharp.block/unblock at the pinned version not checked."
 ]
}
  ```
- Published fix sites:   - ghost/core/core/server/data/importer/handlers/image.js:13 — entry point: POST /ghost/api/admin/db (importfile zip, routes.js:375-381) and POST /ghost/api/admin/posts/upload (CSV zip via content-import assets.ts:137) [import handler (landing point)]
  - ghost/core/core/server/services/media-inliner/external-media-inliner.js:185 — entry point: POST /ghost/api/admin/db/media/inline (routes.js:385) background job; also CSV content import remote media (content-import/import/media.ts:166) [second ingestion pipeline (remote fetch -> saveRaw)]
  - ghost/core/core/server/services/media-inliner/service.js:22 — entry point: same as media inliner (getMediaStorage dependency injected at service init) [service wiring / storage picker]
  - ghost/core/core/server/services/oembed/oembed-service.js:62 — entry point: GET /ghost/api/admin/oembed (routes.js:505), bookmark icon/thumbnail processImageFromUrl [neighbouring feature (oembed image fetch + rasterize)]
  - ghost/core/core/server/web/api/middleware/upload.js:347 — entry point: POST /images/upload (routes.js:450-456), PUT /media/thumbnail/upload (routes.js:466-472), POST /media/upload thumbnail (routes.js:459-465) [upload validation middleware (content check added; sanitizer moved to lib)]
  - ghost/core/core/boot.js:101 — entry point: process boot; affects every sharp decode (handle-image-sizes, oembed rasterize, image upload processing) [boot-time process-wide config (sharp loader block)]
  - fix.diff:98-205 — entry point: library used by all the above (new lib/image/image-content.ts) [new shared helper]
  - fix.diff:320-406 — entry point: library used by importer, inliner, upload middleware (new lib/image/svg-sanitizer.ts) [new shared helper (sanitizer extracted from upload.js)]
  - fix.diff:206-319 — entry point: boot (new image-decoders.ts, image-formats.ts) [new shared helper]
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

## Environment (`tasks/ghost-mm/environment/Dockerfile`)
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

## Report to the solver (`tasks/ghost-mm/instruction.md`)
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

## Tests (`tasks/ghost-mm/tests/`)
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
- **Wrong-fix patches** go in `build/ghost-mm/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/ghost-mm/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/ghost-mm/manifest.json`:**
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

**Also in `build/ghost-mm/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py ghost-mm --only static
python3 -I builder/gate.py ghost-mm --only nop
python3 -I builder/gate.py ghost-mm --only oracle
python3 -I builder/gate.py ghost-mm --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/ghost-mm/`;
  - edit only `tasks/ghost-mm/`, `build/ghost-mm/` and, for pattern B, the register;
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
