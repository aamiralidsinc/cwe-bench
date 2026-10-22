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

Project root: `/home/mara/cwe-bench`. Task: `arc-ds`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: ["GHSA-P2J4-C4G6-RPF5", "CVE-2026-47735", "GO-2026-5523"]; basekick-labs/arc; path traversal / arbitrary file read and SSRF via an embedded query engine's I/O functions (access-control bypass, CWE-22/CWE-200/CWE-918)
- Pinned (vulnerable) commit: parent of 91bdc29d1a02178ccf8c66375eccf85203108dfb (parent_commit not given in candidate). Published fix: 91bdc29d1a02178ccf8c66375eccf85203108dfb.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "18523",
 "advisory_ids": [
  "GHSA-P2J4-C4G6-RPF5",
  "CVE-2026-47735",
  "GO-2026-5523"
 ],
 "repo": "basekick-labs/arc",
 "pinned_commit": "parent of 91bdc29d1a02178ccf8c66375eccf85203108dfb (parent_commit not given in candidate)",
 "fix_commits": [
  "91bdc29d1a02178ccf8c66375eccf85203108dfb"
 ],
 "trust_decision": {
  "summary": "Whether user-supplied SQL run on Arc's shared DuckDB may open local files or URLs; at the pinned commit this is decided only by a text denylist (read_parquet( / arc_partition_agg( / DDL keywords) in ValidateSQLRequest plus RBAC FROM/JOIN table extraction in internal/api, with no DuckDB-level file-access restriction in configureDatabase.",
  "evidence": [
   "internal/api/query.go:1847-1871",
   "internal/api/query.go:1880-1885",
   "internal/api/query.go:943-974",
   "internal/api/query.go:1043-1060",
   "internal/database/duckdb.go:247",
   "internal/database/duckdb.go:315"
  ]
 },
 "landing_point": {
  "where": "internal/api/query.go:1858",
  "why": "The summary names DuckDB I/O functions bypassing RBAC on the query API; the read_parquet( denylist in ValidateSQLRequest is the obvious place that already blocks one I/O function."
 },
 "fix_sites": [
  {
   "where": "fix.diff:1555-1604",
   "entry_point": "database.New -> configureDatabase (new lockdownExternalAccess, internal/database/sandbox.go); covers POST /api/v1/query, /query/arrow, /query/msgpack, /query/estimate, GET /api/v1/query/:measurement, admin /api/v1/delete and /api/v1/continuous_queries",
   "module_kind": "lower-level database layer (new file)"
  },
  {
   "where": "fix.diff:1616-1680",
   "entry_point": "buildAllowedDirectories, called by lockdownExternalAccess at startup",
   "module_kind": "lower-level database layer, allowlist builder from config"
  },
  {
   "where": "internal/database/duckdb.go:315",
   "entry_point": "configureDatabase (lockdown appended after arcx load; arcx LOAD moved from per-connection connInitFn to one-shot)",
   "module_kind": "lower-level database layer"
  },
  {
   "where": "internal/database/duckdb.go:185",
   "entry_point": "openDuckDB replaced by sql.Open + loadArcxExtension (fix.diff:775-892)",
   "module_kind": "lower-level database layer, extension loader"
  },
  {
   "where": "internal/database/duckdb.go:757",
   "entry_point": "POST /api/v1/query with profile mode -> QueryWithProfileContext (profile output moved into TempDirectory)",
   "module_kind": "lower-level database layer"
  },
  {
   "where": "internal/database/duckdb_arrow.go:80",
   "entry_point": "POST /api/v1/query/arrow with profile -> ArrowQueryWithProfileContext",
   "module_kind": "second implementation of profile query path"
  },
  {
   "where": "internal/api/import.go:193",
   "entry_point": "multipart import handlers (CSV/Parquet) -> handleFileImport (upload dir moved into allowlisted dir)",
   "module_kind": "HTTP handler, compatibility with sandbox"
  },
  {
   "where": "internal/api/delete.go:789",
   "entry_point": "POST /api/v1/delete (admin) -> rewriteS3File (staging file moved into allowlisted dir)",
   "module_kind": "HTTP handler, compatibility with sandbox"
  },
  {
   "where": "cmd/arc/main.go:232",
   "entry_point": "arc server startup: path resolution, denied roots, symlink resolution, upload dir creation (fix.diff:138-377)",
   "module_kind": "startup / config wiring"
  }
 ],
 "O1_entry_points": 5,
 "O2_out_of_scope_site": {
  "kind": "lower_level_api",
  "where": "internal/database/duckdb.go:247-320 (configureDatabase; the fix adds internal/database/sandbox.go, fix.diff:1555-1604) and the second profile-output implementation at internal/database/duckdb_arrow.go:80"
 },
 "O3_reason_to_dismiss": "Once the DuckDB sandbox blocks /etc and other outside paths, files under the storage root look like Arc's own data, so a solver can argue cross-database reads via read_csv/parquet_scan/glob inside the allowlist, or through the measurement WHERE clause, are an RBAC matter outside the reported local-file-read bug.",
 "O4_distance": {
  "files": 6,
  "packages": 3,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Arc's own rewriter emits read_parquet over storage-root paths for every table query, CSV/Parquet import runs read_csv/read_parquet on the uploaded temp file, DELETE on S3 COPYs to a local staging file, and profile mode writes PRAGMA profiling_output; blocking all I/O at the DuckDB layer or leaving the allowlist without these dirs breaks them.",
  "where": "internal/api/import.go:701-705; internal/api/delete.go:789; internal/database/duckdb.go:757; internal/database/duckdb_arrow.go:80; internal/tiering/router.go:177-185"
 },
 "O6_input_shapes": [
  "read_csv / read_csv_auto (fix.diff:1355-1356)",
  "read_json / read_json_auto (fix.diff:1357-1358)",
  "read_text / read_blob (fix.diff:1359-1360)",
  "glob (fix.diff:1361)",
  "parquet_metadata / parquet_schema / read_parquet outside allowlist (fix.diff:1362-1364)",
  "read_xlsx via extension (fix.diff:1369)",
  "http/https URL (SSRF to instance metadata) (fix.diff:1394-1396)",
  "COPY TO local path and to s3:// attacker bucket (fix.diff:1402-1423)",
  "EXPORT DATABASE outside allowlist (fix.diff:1429)",
  "INSTALL after lockdown and SET enable_external_access=true (fix.diff:1437-1446)",
  "enforcement across distinct pool connections (fix.diff:1452-1481)"
 ],
 "O7_producer": {
  "kind": "config_loader",
  "where": "internal/config/config.go:762 (storage.local_path default ./data/arc), internal/config/config.go:794 (auth.db_path ./data/arc.db), internal/config/config.go:810 (compaction.temp_directory); resolved into the allowlist via cmd/arc/main.go:232 and fix.diff:185-301",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "POST /api/v1/query (and arrow/msgpack/estimate): I/O-family functions and the parquet_scan alias read other databases' files inside the allowlisted storage root, bypassing RBAC table extraction",
   "where": "internal/api/query.go:1858-1885",
   "reason_to_dismiss": "Sandbox now blocks files outside Arc's directories; data inside the storage root is 'Arc's own' and RBAC is a separate (licensed) feature.",
   "distance": "same file as landing point; the fix's allowlist of the whole storage root is in internal/database/sandbox.go (fix.diff:1619-1620)",
   "present_in_latest": "no",
   "latest_where": "latest/internal/api/query.go:2502-2515"
  },
  {
   "route": "GET /api/v1/query/:measurement?where=...: WHERE is concatenated into SQL and checked only by a keyword list that has no I/O functions; RBAC checks only the path measurement",
   "where": "internal/api/query.go:3390-3416",
   "reason_to_dismiss": "Looks like a neighbouring convenience endpoint with its own validator, not the /api/v1/query route the report shows.",
   "distance": "same file, about 1500 lines from the landing point; validator at internal/api/query.go:709-729",
   "present_in_latest": "no",
   "latest_where": "latest/internal/api/query.go:916-952"
  },
  {
   "route": "POST /api/v1/delete (admin): WHERE keyword denylist omits I/O functions such as glob/read_csv inside the predicate",
   "where": "internal/api/delete.go:442-473",
   "reason_to_dismiss": "Admin-only endpoint; admins are trusted.",
   "distance": "different file in the same package (internal/api/delete.go)",
   "present_in_latest": "no",
   "latest_where": "latest/internal/api/delete.go:261-271"
  },
  {
   "route": "Continuous queries (admin): query text stored in SQLite without ValidateSQLRequest and later executed on DuckDB (save/reload)",
   "where": "internal/api/continuous_query.go:283-294",
   "reason_to_dismiss": "Admin-only, scheduled background job rather than the interactive query API.",
   "distance": "different file in internal/api; execution at internal/api/continuous_query.go:476 and internal/api/continuous_query.go:704",
   "present_in_latest": "unknown",
   "latest_where": "latest/internal/api/cq_revalidate_test.go:29"
  }
 ],
 "O8b_injection_room": [
  {
   "where": "internal/compaction/subprocess.go:97",
   "sibling": "A second DuckDB opened with sql.Open outside database.New (so outside configureDatabase), fed a user-influenced path or SQL fragment",
   "why_realistic": "Compaction already opens its own unsandboxed DuckDB in a subprocess; a maintainer adding an export or preview worker would copy this pattern."
  },
  {
   "where": "internal/api/query.go:3413",
   "sibling": "Another measurement-style endpoint that concatenates a user filter or select-list fragment into SQL behind a small keyword list",
   "why_realistic": "queryMeasurement already builds SQL this way with its own validator separate from ValidateSQLRequest."
  }
 ],
 "O9_family": "path traversal / arbitrary file read and SSRF via an embedded query engine's I/O functions (access-control bypass, CWE-22/CWE-200/CWE-918)",
 "O9_dos": false,
 "O10_build": {
  "language": "Go (cgo)",
  "toolchain": "go 1.26 (go.mod:3), duckdb-go v2.10501.0 with prebuilt duckdb-go-bindings libs (go.mod:17, go.mod:60-65)",
  "services": [],
  "offline_after_build": true,
  "project_tests": "internal/api/query_test.go:1033-1040 (denylist cases for read_parquet/arc_partition_agg); fix adds internal/database/duckdb_sandbox_test.go (fix.diff:1123-1502)"
 },
 "O11_fix_minutes": 75,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "cmd/arc/main.go, internal/api/delete.go, internal/api/import.go, internal/database/duckdb.go, internal/database/duckdb_arrow.go, internal/database/sandbox.go (new)",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Add read_csv/read_json/read_text/glob/... to the read_parquet( regex in ValidateSQLRequest (internal/api/query.go:1858), which misses aliases (parquet_scan), quoted identifiers, the measurement WHERE route and SSRF/COPY shapes."
 },
 "out_of_scope_notes": [
  "Allowlisting the whole TempDirectory also exposes other users' in-flight import uploads and spill files to user SQL; not pursued.",
  "Compaction subprocess DuckDB (internal/compaction/subprocess.go:97) is not sandboxed; it is not reached by user SQL at the pinned commit as far as read."
 ],
 "unverified": [
  "pinned_commit hash: the candidate gives parent_commit null; repo is assumed to be the parent of the fix commit.",
  "O1 count of 5 non-admin entry points assumes /api/v1/query/msgpack delegates to executeQuery and /api/v1/query/estimate runs user SQL on DuckDB; not traced.",
  "repo_mb unknown (no size measurement done); tiny_repo/giant_repo not assessed.",
  "Continuous-query revalidation in latest is inferred from a test name only (latest/internal/api/cq_revalidate_test.go:29); the source site was not located.",
  "Later incomplete-fix advisory GHSA-93cm-2v4m-c56c is named in latest/internal/api/query.go:2515; its exact scope not read in full."
 ]
}
  ```
- Published fix sites:   - fix.diff:1555-1604 — entry point: database.New -> configureDatabase (new lockdownExternalAccess, internal/database/sandbox.go); covers POST /api/v1/query, /query/arrow, /query/msgpack, /query/estimate, GET /api/v1/query/:measurement, admin /api/v1/delete and /api/v1/continuous_queries [lower-level database layer (new file)]
  - fix.diff:1616-1680 — entry point: buildAllowedDirectories, called by lockdownExternalAccess at startup [lower-level database layer, allowlist builder from config]
  - internal/database/duckdb.go:315 — entry point: configureDatabase (lockdown appended after arcx load; arcx LOAD moved from per-connection connInitFn to one-shot) [lower-level database layer]
  - internal/database/duckdb.go:185 — entry point: openDuckDB replaced by sql.Open + loadArcxExtension (fix.diff:775-892) [lower-level database layer, extension loader]
  - internal/database/duckdb.go:757 — entry point: POST /api/v1/query with profile mode -> QueryWithProfileContext (profile output moved into TempDirectory) [lower-level database layer]
  - internal/database/duckdb_arrow.go:80 — entry point: POST /api/v1/query/arrow with profile -> ArrowQueryWithProfileContext [second implementation of profile query path]
  - internal/api/import.go:193 — entry point: multipart import handlers (CSV/Parquet) -> handleFileImport (upload dir moved into allowlisted dir) [HTTP handler, compatibility with sandbox]
  - internal/api/delete.go:789 — entry point: POST /api/v1/delete (admin) -> rewriteS3File (staging file moved into allowlisted dir) [HTTP handler, compatibility with sandbox]
  - cmd/arc/main.go:232 — entry point: arc server startup: path resolution, denied roots, symlink resolution, upload dir creation (fix.diff:138-377) [startup / config wiring]
- Uncovered routes to confirm (pattern B):   - internal/api/query.go:1858-1885 — POST /api/v1/query (and arrow/msgpack/estimate): I/O-family functions and the parquet_scan alias read other databases' files inside the allowlisted storage root, bypassing RBAC table extraction (reason to dismiss: Sandbox now blocks files outside Arc's directories; data inside the storage root is 'Arc's own' and RBAC is a separate (licensed) feature.; still in latest: no)
  - internal/api/query.go:3390-3416 — GET /api/v1/query/:measurement?where=...: WHERE is concatenated into SQL and checked only by a keyword list that has no I/O functions; RBAC checks only the path measurement (reason to dismiss: Looks like a neighbouring convenience endpoint with its own validator, not the /api/v1/query route the report shows.; still in latest: no)
  - internal/api/delete.go:442-473 — POST /api/v1/delete (admin): WHERE keyword denylist omits I/O functions such as glob/read_csv inside the predicate (reason to dismiss: Admin-only endpoint; admins are trusted.; still in latest: no)
  - internal/api/continuous_query.go:283-294 — Continuous queries (admin): query text stored in SQLite without ValidateSQLRequest and later executed on DuckDB (save/reload) (reason to dismiss: Admin-only, scheduled background job rather than the interactive query API.; still in latest: unknown)
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

## Environment (`tasks/arc-ds/environment/Dockerfile`)
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

## Report to the solver (`tasks/arc-ds/instruction.md`)
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

## Tests (`tasks/arc-ds/tests/`)
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
- **Wrong-fix patches** go in `build/arc-ds/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/arc-ds/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/arc-ds/manifest.json`:**
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

**Also in `build/arc-ds/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py arc-ds --only static
python3 -I builder/gate.py arc-ds --only nop
python3 -I builder/gate.py arc-ds --only oracle
python3 -I builder/gate.py arc-ds --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/arc-ds/`;
  - edit only `tasks/arc-ds/`, `build/arc-ds/` and, for pattern B, the register;
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
