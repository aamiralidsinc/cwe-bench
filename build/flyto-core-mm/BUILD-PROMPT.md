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

Project root: `/home/mara/cwe-bench`. Task: `flyto-core-mm`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: ["GHSA-2956-977X-2W3R", "CVE-2026-67429", "PYSEC-2026-3568"]; flytohub/flyto-core; path traversal / arbitrary file write outside sandbox (CWE-22, CWE-73)
- Pinned (vulnerable) commit: parent of d5f89d71303e3c1e6418d347c5c55fcd173cc8cc (parent_commit not given in candidate). Published fix: d5f89d71303e3c1e6418d347c5c55fcd173cc8cc.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "105",
 "advisory_ids": [
  "GHSA-2956-977X-2W3R",
  "CVE-2026-67429",
  "PYSEC-2026-3568"
 ],
 "repo": "flytohub/flyto-core",
 "pinned_commit": "parent of d5f89d71303e3c1e6418d347c5c55fcd173cc8cc (parent_commit not given in candidate)",
 "fix_commits": [
  "d5f89d71303e3c1e6418d347c5c55fcd173cc8cc"
 ],
 "trust_decision": {
  "summary": "Whether a caller-supplied output path for a file-writing workflow module may be written: it must resolve inside the operator's FLYTO_SANDBOX_DIR, decided per module by calling validate_path_with_env_config (realpath + prefix check) in src/core/utils.py.",
  "evidence": [
   "src/core/utils.py:679-704",
   "src/core/utils.py:707-723",
   "src/core/utils.py:657-667",
   "src/core/modules/atomic/file/write.py:90"
  ]
 },
 "landing_point": {
  "where": "src/core/modules/atomic/image/download.py:139-143",
  "why": "The advisory title names image.download; its existing check compares output_path against the caller-supplied output_dir, so it is a no-op (base and target both caller-controlled)."
 },
 "fix_sites": [
  {
   "where": "src/core/modules/atomic/image/download.py:139-143",
   "entry_point": "image download module via POST /v1/execute (src/core/api/routes/modules.py:93), POST /workflow/run (src/core/api/routes/workflows.py:31), MCP, flyto CLI",
   "module_kind": "primary module named in advisory; replaces ineffective caller-relative commonpath check; mkdir moved after check (fix.diff:383, fix.diff:405)"
  },
  {
   "where": "src/core/modules/atomic/image/compress.py:168",
   "entry_point": "image compress module via /v1/execute or workflow run",
   "module_kind": "sibling module, same package"
  },
  {
   "where": "src/core/modules/atomic/image/convert.py:177",
   "entry_point": "image convert module via /v1/execute or workflow run",
   "module_kind": "sibling module, same package; mkdir removed from helper at convert.py:56 (fix.diff:317)"
  },
  {
   "where": "src/core/modules/atomic/image/crop.py:189",
   "entry_point": "image crop module via /v1/execute or workflow run",
   "module_kind": "sibling module, same package"
  },
  {
   "where": "src/core/modules/atomic/image/resize.py:151",
   "entry_point": "image resize module via /v1/execute or workflow run",
   "module_kind": "sibling module, same package (default derived output path)"
  },
  {
   "where": "src/core/modules/atomic/image/rotate.py:176",
   "entry_point": "image rotate module via /v1/execute or workflow run",
   "module_kind": "sibling module, same package"
  },
  {
   "where": "src/core/modules/atomic/image/watermark.py:246",
   "entry_point": "image watermark module via /v1/execute or workflow run",
   "module_kind": "sibling module, same package"
  },
  {
   "where": "src/core/modules/atomic/image/qrcode_generate.py:53",
   "entry_point": "QR code generate module via /v1/execute or workflow run",
   "module_kind": "sibling module, internal helper _create_qr_code (path rewritten .png->.svg before check)"
  },
  {
   "where": "src/core/modules/atomic/document/excel_write.py:108",
   "entry_point": "excel write module via /v1/execute or workflow run",
   "module_kind": "other package (document)"
  },
  {
   "where": "src/core/modules/atomic/document/pdf_fill_form.py:122",
   "entry_point": "pdf fill form module via /v1/execute or workflow run",
   "module_kind": "other package (document)"
  },
  {
   "where": "src/core/modules/atomic/document/pdf_to_word.py:108",
   "entry_point": "pdf to word module via /v1/execute or workflow run",
   "module_kind": "other package (document), derived default output"
  },
  {
   "where": "src/core/modules/atomic/document/word_to_pdf.py:96",
   "entry_point": "word to pdf module via /v1/execute or workflow run",
   "module_kind": "other package (document), derived default output"
  },
  {
   "where": "src/core/modules/atomic/browser/pagination.py:323",
   "entry_point": "browser pagination module (checkpoint_path param) via /v1/execute or workflow run",
   "module_kind": "other package (browser); checkpoint save/resume state file"
  }
 ],
 "O1_entry_points": 13,
 "O2_out_of_scope_site": {
  "kind": "save_reload_or_serialization",
  "where": "src/core/modules/atomic/browser/pagination.py:323 (checkpoint_path) -> written by src/core/browser/checkpoint.py:109-112 (also derives a sibling .jsonl at src/core/browser/checkpoint.py:50)"
 },
 "O3_reason_to_dismiss": "The pagination checkpoint is internal resume state for a browser scraping feature, not an 'output file' like the image/document writers named in the report; and csv_write/json_to_csv already reject '..' so look protected (src/core/modules/atomic/data/csv_write.py:95-96).",
 "O4_distance": {
  "files": 13,
  "packages": 3,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Legitimate writes inside FLYTO_SANDBOX_DIR must keep working, including absolute in-sandbox paths (FLYTO_ALLOW_ABSOLUTE_PATHS defaults true), default-derived outputs (resize '_resized' suffix, image download filename derived from URL into output_dir); an over-broad fix that rejects absolute paths, drops output_dir defaults, or rejects any path with a dot-segment breaks these. The fix's own test fixture sets FLYTO_SANDBOX_DIR=tmp_path to keep image tests passing (fix.diff:730-735).",
  "where": "src/core/utils.py:691; src/core/modules/atomic/image/resize.py:151; src/core/modules/atomic/image/download.py:29-34"
 },
 "O6_input_shapes": [
  "relative path with ../ segments",
  "absolute path outside the sandbox",
  "symlinked directory resolving outside (realpath at src/core/utils.py:653)",
  "~ home expansion (src/core/utils.py:643)",
  "output_path omitted: path derived from input_path or caller output_dir (src/core/modules/atomic/image/download.py:29-34, src/core/modules/atomic/image/resize.py:151)",
  "path rewritten before write (.png -> .svg in src/core/modules/atomic/image/qrcode_generate.py:54-55)",
  "directory creation side effect before the check (mkdir moved after validation: fix.diff:317, fix.diff:383)"
 ],
 "O7_producer": {
  "kind": "serializer",
  "where": "src/core/browser/checkpoint.py:93-112 (PaginationCheckpoint.save writes metadata and derived .jsonl)",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "data CSV write module writes caller file_path; only a '..' substring check, absolute paths pass",
   "where": "src/core/modules/atomic/data/csv_write.py:95-118",
   "reason_to_dismiss": "already has a traversal check, looks protected",
   "distance": "other package (data)",
   "present_in_latest": "no",
   "latest_where": "latest/src/core/modules/atomic/data/csv_write.py:99"
  },
  {
   "route": "json_to_csv writes caller output_path; '..' substring check after makedirs, absolute paths pass",
   "where": "src/core/modules/atomic/data/json_to_csv.py:161-168",
   "reason_to_dismiss": "already has a traversal check; a data-conversion utility, not a file module",
   "distance": "other package (data)",
   "present_in_latest": "no",
   "latest_where": "latest/src/core/modules/atomic/data/json_to_csv.py:237"
  },
  {
   "route": "word_parse extracts embedded images into caller images_output_dir with the same no-op caller-relative commonpath check as image.download",
   "where": "src/core/modules/atomic/document/word_parse.py:178-200",
   "reason_to_dismiss": "a parser/reader module; filenames are generated (image_N.ext), so it looks safe",
   "distance": "same package as document fix sites",
   "present_in_latest": "no",
   "latest_where": "latest/src/core/modules/atomic/document/word_parse.py:112"
  },
  {
   "route": "pdf_generate writes caller output_path with no sandbox check",
   "where": "src/core/modules/atomic/document/pdf_generate.py:102-127",
   "reason_to_dismiss": "generates new content rather than transforming a user file; not listed in report",
   "distance": "same package as document fix sites",
   "present_in_latest": "no",
   "latest_where": "latest/src/core/modules/atomic/document/pdf_generate.py:92"
  },
  {
   "route": "file copy module writes caller destination with no sandbox check",
   "where": "src/core/modules/atomic/file/copy.py:98-106",
   "reason_to_dismiss": "generic file-ops module, neighbouring feature to file.write which is already guarded",
   "distance": "other package (file)",
   "present_in_latest": "no",
   "latest_where": "latest/src/core/modules/atomic/file/copy.py:266"
  },
  {
   "route": "file move module writes caller destination with no sandbox check",
   "where": "src/core/modules/atomic/file/move.py:93-97",
   "reason_to_dismiss": "generic file-ops module, not named in report",
   "distance": "other package (file)",
   "present_in_latest": "no",
   "latest_where": "latest/src/core/modules/atomic/file/move.py:279"
  },
  {
   "route": "browser download module saves to caller save_path; parent mkdir in validate_params",
   "where": "src/core/modules/atomic/browser/download.py:83-108",
   "reason_to_dismiss": "browser automation feature; needs a browser; writes browser-delivered content",
   "distance": "other package (browser)",
   "present_in_latest": "no",
   "latest_where": "latest/src/core/modules/atomic/browser/download.py:172"
  },
  {
   "route": "browser screenshot module writes caller path",
   "where": "src/core/modules/atomic/browser/screenshot.py:60-79",
   "reason_to_dismiss": "browser feature; path passed to driver wrapper, not opened directly",
   "distance": "other package (browser)",
   "present_in_latest": "no",
   "latest_where": "latest/src/core/modules/atomic/browser/screenshot.py:235"
  },
  {
   "route": "browser cookies-to-file writes caller file_path",
   "where": "src/core/modules/atomic/browser/cookies_file.py:102-103",
   "reason_to_dismiss": "session save/reload helper, not an output writer",
   "distance": "other package (browser)",
   "present_in_latest": "no",
   "latest_where": "latest/src/core/modules/atomic/browser/cookies_file.py:337"
  },
  {
   "route": "knowledge export writes caller output path",
   "where": "src/core/modules/atomic/vector/knowledge_manager.py:331-337",
   "reason_to_dismiss": "vector/RAG feature, export side path",
   "distance": "other package (vector)",
   "present_in_latest": "no",
   "latest_where": "latest/src/core/modules/atomic/vector/knowledge_manager.py:333"
  }
 ],
 "O8b_injection_room": [
  {
   "where": "src/core/modules/atomic/image/qrcode_generate.py:116",
   "sibling": "second save path in the same module (svg/png variant) left without the check",
   "why_realistic": "the module already has two separate save calls (qrcode_generate.py:78 and :116); a maintainer patching one helper could miss the other"
  },
  {
   "where": "src/core/browser/checkpoint.py:50",
   "sibling": "derived .jsonl items path written beside the validated checkpoint path",
   "why_realistic": "the derived path is computed in a different package from where the check is applied"
  }
 ],
 "O9_family": "path traversal / arbitrary file write outside sandbox (CWE-22, CWE-73)",
 "O9_dos": false,
 "O10_build": {
  "language": "Python (>=3.9)",
  "toolchain": "pip install -e . with pytest (pyproject.toml:47, pyproject.toml:139-142); Pillow, openpyxl, pypdf, python-docx, reportlab for affected modules",
  "services": [],
  "offline_after_build": true,
  "project_tests": "tests/modules/test_new_modules.py (TestImageModules at line 592); fix adds only a FLYTO_SANDBOX_DIR fixture there"
 },
 "O11_fix_minutes": 60,
 "O12_red_flags": [],
 "O13_recall_risk": "low",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "src/core/modules/atomic/image/{download,compress,convert,crop,resize,rotate,watermark,qrcode_generate}.py; src/core/modules/atomic/document/{excel_write,pdf_fill_form,pdf_to_word,word_to_pdf}.py; src/core/modules/atomic/browser/pagination.py",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Fix image.download's commonpath check (or the image package only) and stop, or add '..' rejection like csv_write which leaves absolute paths open."
 },
 "out_of_scope_notes": [
  "The same fix commit also bundles GHSA-hr7p-wg7r-hg9m (${env.*} interpolation gate, src/core/engine/variable_resolver.py, src/core/module_policy.py) and GHSA-qq9q-xgm3-xv9g (env API key forwarded to caller base_url: ai/model.py, llm/agent.py, llm/chat.py, vector/connector.py, utils.py); not part of this advisory's protection.",
  "Further unguarded writers exist in verify/*, warroom/report.py, storage/kv.py, llm/code_fix.py, browser/record.py, browser/trace.py, browser/snapshot.py, third_party/cloud/azure.py; not enumerated further."
 ],
 "unverified": [
  "Exact pinned commit hash not provided (parent_commit null); assumed parent of the fix commit.",
  "Repo size in MB not measured (no shell); tiny_repo/giant_repo not assessed.",
  "image.download needs an HTTP fetch; testing it offline needs a mocked aiohttp session or a local server allowed by SSRF config; other sites are offline.",
  "Whether browser-based routes (download, screenshot, cookies, pagination) can run in the test environment without Playwright browsers installed.",
  "Advisory text itself was not available locally; scope inferred from the summary and fix diff.",
  "Line numbers for O8 latest_where are first matching validate_path_with_env_config call, not a full read of each latest file."
 ]
}
  ```
- Published fix sites:   - src/core/modules/atomic/image/download.py:139-143 — entry point: image download module via POST /v1/execute (src/core/api/routes/modules.py:93), POST /workflow/run (src/core/api/routes/workflows.py:31), MCP, flyto CLI [primary module named in advisory; replaces ineffective caller-relative commonpath check; mkdir moved after check (fix.diff:383, fix.diff:405)]
  - src/core/modules/atomic/image/compress.py:168 — entry point: image compress module via /v1/execute or workflow run [sibling module, same package]
  - src/core/modules/atomic/image/convert.py:177 — entry point: image convert module via /v1/execute or workflow run [sibling module, same package; mkdir removed from helper at convert.py:56 (fix.diff:317)]
  - src/core/modules/atomic/image/crop.py:189 — entry point: image crop module via /v1/execute or workflow run [sibling module, same package]
  - src/core/modules/atomic/image/resize.py:151 — entry point: image resize module via /v1/execute or workflow run [sibling module, same package (default derived output path)]
  - src/core/modules/atomic/image/rotate.py:176 — entry point: image rotate module via /v1/execute or workflow run [sibling module, same package]
  - src/core/modules/atomic/image/watermark.py:246 — entry point: image watermark module via /v1/execute or workflow run [sibling module, same package]
  - src/core/modules/atomic/image/qrcode_generate.py:53 — entry point: QR code generate module via /v1/execute or workflow run [sibling module, internal helper _create_qr_code (path rewritten .png->.svg before check)]
  - src/core/modules/atomic/document/excel_write.py:108 — entry point: excel write module via /v1/execute or workflow run [other package (document)]
  - src/core/modules/atomic/document/pdf_fill_form.py:122 — entry point: pdf fill form module via /v1/execute or workflow run [other package (document)]
  - src/core/modules/atomic/document/pdf_to_word.py:108 — entry point: pdf to word module via /v1/execute or workflow run [other package (document), derived default output]
  - src/core/modules/atomic/document/word_to_pdf.py:96 — entry point: word to pdf module via /v1/execute or workflow run [other package (document), derived default output]
  - src/core/modules/atomic/browser/pagination.py:323 — entry point: browser pagination module (checkpoint_path param) via /v1/execute or workflow run [other package (browser); checkpoint save/resume state file]
- Uncovered routes to confirm (pattern B):   - src/core/modules/atomic/data/csv_write.py:95-118 — data CSV write module writes caller file_path; only a '..' substring check, absolute paths pass (reason to dismiss: already has a traversal check, looks protected; still in latest: no)
  - src/core/modules/atomic/data/json_to_csv.py:161-168 — json_to_csv writes caller output_path; '..' substring check after makedirs, absolute paths pass (reason to dismiss: already has a traversal check; a data-conversion utility, not a file module; still in latest: no)
  - src/core/modules/atomic/document/word_parse.py:178-200 — word_parse extracts embedded images into caller images_output_dir with the same no-op caller-relative commonpath check as image.download (reason to dismiss: a parser/reader module; filenames are generated (image_N.ext), so it looks safe; still in latest: no)
  - src/core/modules/atomic/document/pdf_generate.py:102-127 — pdf_generate writes caller output_path with no sandbox check (reason to dismiss: generates new content rather than transforming a user file; not listed in report; still in latest: no)
  - src/core/modules/atomic/file/copy.py:98-106 — file copy module writes caller destination with no sandbox check (reason to dismiss: generic file-ops module, neighbouring feature to file.write which is already guarded; still in latest: no)
  - src/core/modules/atomic/file/move.py:93-97 — file move module writes caller destination with no sandbox check (reason to dismiss: generic file-ops module, not named in report; still in latest: no)
  - src/core/modules/atomic/browser/download.py:83-108 — browser download module saves to caller save_path; parent mkdir in validate_params (reason to dismiss: browser automation feature; needs a browser; writes browser-delivered content; still in latest: no)
  - src/core/modules/atomic/browser/screenshot.py:60-79 — browser screenshot module writes caller path (reason to dismiss: browser feature; path passed to driver wrapper, not opened directly; still in latest: no)
  - src/core/modules/atomic/browser/cookies_file.py:102-103 — browser cookies-to-file writes caller file_path (reason to dismiss: session save/reload helper, not an output writer; still in latest: no)
  - src/core/modules/atomic/vector/knowledge_manager.py:331-337 — knowledge export writes caller output path (reason to dismiss: vector/RAG feature, export side path; still in latest: no)
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

## Environment (`tasks/flyto-core-mm/environment/Dockerfile`)
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

## Report to the solver (`tasks/flyto-core-mm/instruction.md`)
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

## Tests (`tasks/flyto-core-mm/tests/`)
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
- **Wrong-fix patches** go in `build/flyto-core-mm/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/flyto-core-mm/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/flyto-core-mm/manifest.json`:**
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

**Also in `build/flyto-core-mm/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py flyto-core-mm --only static
python3 -I builder/gate.py flyto-core-mm --only nop
python3 -I builder/gate.py flyto-core-mm --only oracle
python3 -I builder/gate.py flyto-core-mm --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/flyto-core-mm/`;
  - edit only `tasks/flyto-core-mm/`, `build/flyto-core-mm/` and, for pattern B, the register;
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
