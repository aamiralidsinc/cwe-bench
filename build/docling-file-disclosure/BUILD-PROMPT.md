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

Project root: `/home/mara/cwe-bench`. Task: `docling-file-disclosure`. Pattern: `B`. Track: `mined`.

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
- Advisory: GHSA-P944-4XH2-X776 / CVE-2026-105748 - docling-project/docling - local file disclosure via attacker-controlled file reference in deserialised document (CWE-73 external control of file name/path leading to CWE-200). Whether ImageRef.uri values inside an untrusted DoclingDocument JSON may point at local files (bare/relative paths, file: URIs) that later stages open and embed; at the pinned commit the JSON backend accepts any URI unchecked, and the fix d
- Pinned (vulnerable) commit: e4780063bb4c33b2b48222d2106ce9ba45eaf453. Published fix: d4bb776884aba9aa3132f54773f420853cf7afe4.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "4753",
 "advisory_ids": [
  "GHSA-P944-4XH2-X776",
  "CVE-2026-105748"
 ],
 "repo": "docling-project/docling",
 "pinned_commit": "parent of d4bb776884aba9aa3132f54773f420853cf7afe4 (parent_commit not given in candidate)",
 "fix_commits": [
  "d4bb776884aba9aa3132f54773f420853cf7afe4"
 ],
 "trust_decision": {
  "summary": "Whether ImageRef.uri values inside an untrusted DoclingDocument JSON may point at local files (bare/relative paths, file: URIs) that later stages open and embed; at the pinned commit the JSON backend accepts any URI unchecked, and the fix decides it in DoclingJSONBackend after parsing, gated by backend_options.enable_local_fetch (default False).",
  "evidence": [
   "docling/backend/json/docling_json_backend.py:57",
   "fix.diff:112-115",
   "fix.diff:119-142",
   "docling/datamodel/backend_options.py:28-30",
   "docling/backend/abstract_backend.py:83-85"
  ]
 },
 "landing_point": {
  "where": "docling/backend/json/docling_json_backend.py:57",
  "why": "The summary names 'crafted DoclingDocument JSON'; the only place docling parses JSON input into a DoclingDocument is this backend's model_validate_json call."
 },
 "fix_sites": [
  {
   "where": "docling/backend/json/docling_json_backend.py:19-22",
   "entry_point": "DoclingJSONBackend(in_doc, path_or_stream, options) public backend constructor, reached from InputDocument._init_doc (docling/datamodel/document.py:309-316) during DocumentConverter.convert",
   "module_kind": "backend (format parser)"
  },
  {
   "where": "docling/backend/json/docling_json_backend.py:57",
   "entry_point": "DocumentConverter.convert / convert_all on a .json DoclingDocument; `docling` CLI on a .json input",
   "module_kind": "backend (format parser); new tree-walk helper added at fix.diff:63-90"
  },
  {
   "where": "docling/document_converter.py:242-246",
   "entry_point": "new public DoclingJSONFormatOption class, passed in DocumentConverter(format_options=...)",
   "module_kind": "converter configuration / format option"
  },
  {
   "where": "docling/document_converter.py:391-393",
   "entry_point": "_get_default_option used by DocumentConverter when no format option is given (SDK and CLI)",
   "module_kind": "defaults route"
  }
 ],
 "O1_entry_points": 3,
 "O2_out_of_scope_site": {
  "kind": "defaults_or_merge_route",
  "where": "docling/document_converter.py:391-393 (fix.diff:185): the default JSON_DOCLING option is replaced by DoclingJSONFormatOption so backend_options can be carried; security-wise the default is already safe because DeclarativeDocumentBackend defaults enable_local_fetch=False (docling/backend/abstract_backend.py:83-85), so this site is about the opt-in, not the block"
 },
 "O3_reason_to_dismiss": "ConversionAssets.load only reloads an archive the user saved with ConversionAssets.save (docling/datamodel/document.py:506-576), so a solver can argue it is 'your own trusted output', not converter input, and leave its document.json ImageRefs alone.",
 "O4_distance": {
  "files": 2,
  "packages": 2,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "data: URIs and http(s) URLs in ImageRef must be kept (not fetched, not dropped), and with enable_local_fetch=True local paths must still load so REFERENCED-mode saves round-trip; an over-broad fix that drops all ImageRefs, or rejects the whole JSON, breaks these",
  "where": "fix.diff:60-64; fix.diff:349-389 (tests for opt-in and kept schemes)"
 },
 "O6_input_shapes": [
  "absolute filesystem Path",
  "relative Path (resolved against CWD)",
  "file: URI",
  "any other non data/http/https scheme",
  "ImageRef on any node type: pictures, pages (DoclingDocument.pages[n].image), tables and other items, found by a generic model-tree walk incl. lists/tuples/dicts"
 ],
 "O7_producer": {
  "kind": "schema",
  "where": "docling/backend/json/docling_json_backend.py:57 (DoclingDocument pydantic schema from docling-core, ImageRef.uri typed AnyUrl|Path, accepts local paths)",
  "check_calls_producer": true
 },
 "O8_uncovered_routes": [
  {
   "route": "ConversionAssets.load / ConversionResult.load reads document.json from a zip via DoclingDocument.model_validate with no local-ImageRef filtering; later EMBEDDED export or enrichment opens those paths",
   "where": "docling/datamodel/document.py:572-576",
   "reason_to_dismiss": "Load of the user's own saved archive, not a converter input format; the advisory names JSON conversion",
   "distance": "different package (docling/datamodel vs docling/backend/json), different file",
   "present_in_latest": "yes",
   "latest_where": "latest/docling/datamodel/document.py:578"
  },
  {
   "route": "Service client reconstructs a DoclingDocument from server 'json' artifacts with no URI filtering, and from resource bundles whose embed guard skips absolute Path and non-Path (file:) URIs, leaving them for a later local EMBEDDED export",
   "where": "docling/service_client/client.py:1784",
   "reason_to_dismiss": "Documents come from the user's own docling-serve; the code comments say bundles 'originate from our service' and the bundle path already has a containment guard (docling/service_client/client.py:1844-1854)",
   "distance": "different package (docling/service_client), far from the backend",
   "present_in_latest": "yes",
   "latest_where": "latest/docling/service_client/client.py:1784"
  }
 ],
 "O8b_injection_room": [
  {
   "where": "docling/backend/xml/doclang_archive_backend.py:43-64",
   "sibling": "DCLX archive backend loads a DoclingDocument via docling-core load_from_doclang_archive without any ImageRef URI filtering; a sibling where archive-referenced images may name paths outside the archive",
   "why_realistic": "Same 'declarative backend that deserialises a whole DoclingDocument' shape as the JSON backend, written without backend options (no options parameter at :22-25), so a maintainer would naturally not have thought to filter image URIs"
  },
  {
   "where": "docling/datamodel/document.py:576",
   "sibling": "save/reload of ConversionAssets carrying ImageRef local paths across the zip boundary",
   "why_realistic": "Persistence code uses plain model_validate for every component; filtering lives only in the backend, which this path never calls"
  }
 ],
 "O9_family": "local file disclosure via attacker-controlled file reference in deserialised document (CWE-73 external control of file name/path leading to CWE-200)",
 "O9_dos": false,
 "O10_build": {
  "language": "Python (>=3.10)",
  "toolchain": "pip/uv; package docling-slim with docling-core>=2.98.0 (pyproject.toml:46-51)",
  "services": [],
  "offline_after_build": true,
  "project_tests": "tests/test_backend_docling_json.py (3 existing tests at pinned commit: valid load, invalid load, BOM); the fix adds 4 behavioural tests there. JSON path uses SimplePipeline, no ML models needed."
 },
 "O11_fix_minutes": 40,
 "O12_red_flags": [],
 "O13_recall_risk": "low",
 "pattern_fit": "B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "docling/backend/json/docling_json_backend.py, docling/document_converter.py",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 0,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Null only PictureItem.image when uri is an absolute Path in DoclingJSONBackend, missing relative paths, file: URIs, page/table images and the ConversionAssets.load / service-client reload routes."
 },
 "out_of_scope_notes": [
  "CLI default --image-export-mode is EMBEDDED (docling/cli/main.py:824), which is what turns a kept local ImageRef into embedded output; not pursued.",
  "Service client bundle embed guard handles relative paths only; noted in O8, not explored further."
 ],
 "unverified": [
  "pinned_commit hash not provided (parent_commit null); described as parent of the fix commit.",
  "repo size in MB not measured (no shell); tiny_repo/giant_repo not assessed, docling is believed to be well above 5 MB.",
  "Whether docling-core load_from_doclang_archive resolves image URIs outside the archive (DCLX route) is in docling-core, outside this repository; listed only as injection room.",
  "Exact docling-core code that opens ImageRef local paths during get_image/EMBEDDED export not read (external dependency); the fix's docstring (fix.diff:122-125) states it.",
  "O1 counts SDK convert, CLI and direct backend construction; docling-serve is not in this repository."
 ]
}
  ```
- Published fix sites:   - docling/backend/json/docling_json_backend.py:19-22 — entry point: DoclingJSONBackend(in_doc, path_or_stream, options) public backend constructor, reached from InputDocument._init_doc (docling/datamodel/document.py:309-316) during DocumentConverter.convert [backend (format parser)]
  - docling/backend/json/docling_json_backend.py:57 — entry point: DocumentConverter.convert / convert_all on a .json DoclingDocument; `docling` CLI on a .json input [backend (format parser); new tree-walk helper added at fix.diff:63-90]
  - docling/document_converter.py:242-246 — entry point: new public DoclingJSONFormatOption class, passed in DocumentConverter(format_options=...) [converter configuration / format option]
  - docling/document_converter.py:391-393 — entry point: _get_default_option used by DocumentConverter when no format option is given (SDK and CLI) [defaults route]
- Uncovered routes to confirm (pattern B):   - docling/datamodel/document.py:572-576 — ConversionAssets.load / ConversionResult.load reads document.json from a zip via DoclingDocument.model_validate with no local-ImageRef filtering; later EMBEDDED export or enrichment opens those paths (reason to dismiss: Load of the user's own saved archive, not a converter input format; the advisory names JSON conversion; still in latest: yes)
  - docling/service_client/client.py:1784 — Service client reconstructs a DoclingDocument from server 'json' artifacts with no URI filtering, and from resource bundles whose embed guard skips absolute Path and non-Path (file:) URIs, leaving them for a later local EMBEDDED export (reason to dismiss: Documents come from the user's own docling-serve; the code comments say bundles 'originate from our service' and the bundle path already has a containment guard (docling/service_client/client.py:1844-1854); still in latest: yes)
- Design plan from the lead: MAIN LEVER: reproduce the published fix in full. Hidden tests require closing EVERY published fix site through its real entry point, including the out-of-scope-looking site (defaults_or_merge_route at docling/document_converter.py:391-393 (fix.diff:185): the default JSON_DOCLING o; dismissable because: ConversionAssets.load only reloads an archive the user saved with ConversionAssets.save (docling/datamodel/document.py:506-576), so a solver can argue it is 'your own trusted output', not converter in). Tempting wrong fix that must FAIL: Null only PictureItem.image when uri is an absolute Path in DoclingJSONBackend, missing relative paths, file: URIs, page/table images and the ConversionAssets.load / service-client reload routes..

INPUT-SHAPE / ROUTE VARIANTS (one security test each, through the real entry point, failing on pinned, passing on a correct fix): absolute filesystem Path; relative Path (resolved against CWD); file: URI; any other non data/http/https scheme; ImageRef on any node type: pictures, pages (DoclingDocument.pages[n].image), tables and other items, found by a generic model-tree walk incl. lists/tuples/dicts.

PATTERN B UNCOVERED ROUTES - confirm each with a behavioural test on the pinned copy, then add one row per route to build/audit/uncovered-routes.tsv: docling/datamodel/document.py:572-576 (dismiss: Load of the user's own saved archive, not a converter input format; the advisory; latest=yes); docling/service_client/client.py:1784 (dismiss: Documents come from the user's own docling-serve; the code comments say bundles ; latest=yes). Unmodified upstream code the published fix did not touch; the reference fix closes them too.

COUPLED MUST-KEEP-WORKING (one functional test per trap so an over-broad fix fails): data: URIs and http(s) URLs in ImageRef must be kept (not fetched, not dropped), and with enable_local_fetch=True local paths must still load so REFERENCED-mode saves round-trip; an over-broad fix that drops all ImageRef (near fix.diff:60-64; fix.diff:349-389 (tests for opt-in and kept ).

Aim for at least two levers with DIFFERENT reasons to dismiss. instruction.md stays at product level: system, one observed impact with one user-level trigger, security property as invariants covering every tested route/shape; keep legitimate use working; never name files/functions/fields/CVEs (all such identifiers go in manifest.leak_terms).
- Host notes: Language: Python (>=3.10). Offline after build, no external services. Test the security logic by calling the relevant functions/handlers directly with crafted inputs - do not stand up external services. Project's own tests for the area must pass at the pinned commit. Confirm each pattern-B route with a test on the pinned copy. Pin at the vulnerable commit; keep unrelated earlier fixes present.

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

## Environment (`tasks/docling-file-disclosure/environment/Dockerfile`)
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

## Report to the solver (`tasks/docling-file-disclosure/instruction.md`)
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

## Tests (`tasks/docling-file-disclosure/tests/`)
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
- **Wrong-fix patches** go in `build/docling-file-disclosure/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/docling-file-disclosure/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/docling-file-disclosure/manifest.json`:**
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

**Also in `build/docling-file-disclosure/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py docling-file-disclosure --only static
python3 -I builder/gate.py docling-file-disclosure --only nop
python3 -I builder/gate.py docling-file-disclosure --only oracle
python3 -I builder/gate.py docling-file-disclosure --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/docling-file-disclosure/`;
  - edit only `tasks/docling-file-disclosure/`, `build/docling-file-disclosure/` and, for pattern B, the register;
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
