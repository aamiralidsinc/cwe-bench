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

Project root: `/home/mara/cwe-bench`. Task: `knowns-ds`. Pattern: `A`. Track: `injected`.

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
- Advisory: ["GHSA-9GFJ-28HW-JCHP", "CVE-2026-86439"]; knowns-dev/knowns; path traversal / missing containment of identifier-to-filename mapping (CWE-22)
- Pinned (vulnerable) commit: parent of 09c5a96fd5817b941dc86669278c1a17db10ed4e (parent_commit not given in candidate). Published fix: 09c5a96fd5817b941dc86669278c1a17db10ed4e.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "10294",
 "advisory_ids": [
  "GHSA-9GFJ-28HW-JCHP",
  "CVE-2026-86439"
 ],
 "repo": "knowns-dev/knowns",
 "pinned_commit": "parent of 09c5a96fd5817b941dc86669278c1a17db10ed4e (parent_commit not given in candidate)",
 "fix_commits": [
  "09c5a96fd5817b941dc86669278c1a17db10ed4e"
 ],
 "trust_decision": {
  "summary": "Storage layer decides whether a caller-supplied doc path / memory ID / template name resolves to a file inside .knowns/{docs,memory,templates} (or ~/.knowns/memory); at the pinned commit it only joins the string with filepath.Join and never checks containment.",
  "evidence": [
   "internal/storage/doc_store.go:129",
   "internal/storage/doc_store.go:177",
   "internal/storage/doc_store.go:346",
   "internal/storage/memory_store.go:211",
   "internal/storage/memory_store.go:253",
   "internal/storage/memory_store.go:359",
   "internal/storage/template_store.go:115",
   "internal/server/routes/templates.go:304"
  ]
 },
 "landing_point": {
  "where": "internal/mcp/handlers/doc.go:28",
  "why": "Summary names the MCP Docs + Memory tools; the `path` param of the MCP `docs` tool (and `id` of the `memory` tool at internal/mcp/handlers/memory.go:28) is where a reader would start."
 },
 "fix_sites": [
  {
   "where": "internal/storage/doc_store.go:124",
   "entry_point": "MCP docs get/update (internal/mcp/handlers/doc.go:229), HTTP docs GET (internal/server/routes/docs.go:185), CLI doc view (internal/cli/doc.go:147)",
   "module_kind": "storage layer (lower-level API under handlers), incl. imports lookup at :146 and :158"
  },
  {
   "where": "internal/storage/doc_store.go:173",
   "entry_point": "MCP docs create (internal/mcp/handlers/doc.go:376), HTTP docs POST (internal/server/routes/docs.go:226), CLI doc create (internal/cli/doc.go:301)",
   "module_kind": "storage layer"
  },
  {
   "where": "internal/storage/doc_store.go:185",
   "entry_point": "MCP docs update (internal/mcp/handlers/doc.go:472), HTTP docs PUT (internal/server/routes/docs.go:306), CLI doc edit (internal/cli/doc.go:390), RewriteDocReferences (internal/storage/doc_store.go:284)",
   "module_kind": "storage layer"
  },
  {
   "where": "internal/storage/doc_store.go:200",
   "entry_point": "MCP docs rename (internal/mcp/handlers/doc.go:465), HTTP docs PUT rename (internal/server/routes/docs.go:297), CLI doc edit rename (internal/cli/doc.go:383)",
   "module_kind": "storage layer; two paths (old and new)"
  },
  {
   "where": "internal/storage/doc_store.go:344",
   "entry_point": "MCP docs delete (internal/mcp/handlers/doc.go:635), CLI doc delete (internal/cli/doc.go:439)",
   "module_kind": "storage layer"
  },
  {
   "where": "internal/storage/memory_store.go:135",
   "entry_point": "MCP memory get (internal/mcp/handlers/memory.go:189), HTTP memories GET (internal/server/routes/memories.go:95)",
   "module_kind": "storage layer"
  },
  {
   "where": "internal/storage/memory_store.go:203",
   "entry_point": "reached via MemoryStore.Get (internal/storage/memory_store.go:137)",
   "module_kind": "storage layer, lower-level public method"
  },
  {
   "where": "internal/storage/memory_store.go:219",
   "entry_point": "memory review/capture create (internal/memoryreview/review.go:300)",
   "module_kind": "storage layer"
  },
  {
   "where": "internal/storage/memory_store.go:258",
   "entry_point": "MCP memory update (internal/mcp/handlers/memory.go:481), HTTP memories PUT (internal/server/routes/memories.go:242), RewriteDocReferences (internal/storage/doc_store.go:335)",
   "module_kind": "storage layer; ID may come from file frontmatter"
  },
  {
   "where": "internal/storage/memory_store.go:332",
   "entry_point": "Update and RestoreLegacyDecisionMigration (internal/storage/memory_store.go:271, :298)",
   "module_kind": "storage layer, internal writer"
  },
  {
   "where": "internal/storage/memory_store.go:351",
   "entry_point": "MCP memory delete (internal/mcp/handlers/memory.go:525), HTTP memories DELETE (internal/server/routes/memories.go:724)",
   "module_kind": "storage layer"
  },
  {
   "where": "internal/storage/memory_store.go:435",
   "entry_point": "MCP memory promote/demote (internal/mcp/handlers/memory.go:551, :574)",
   "module_kind": "storage layer; uses entry.ID re-read from file frontmatter (save/reload)"
  },
  {
   "where": "internal/models/memory.go:176",
   "entry_point": "new ValidateMemoryID helper next to MemoryFileName (fix.diff:24-31)",
   "module_kind": "models package (validator)"
  },
  {
   "where": "internal/storage/template_store.go:108",
   "entry_point": "MCP templates get/run (internal/mcp/handlers/template.go:101, :144), HTTP templates",
   "module_kind": "storage layer, neighbouring feature (templates not named in the advisory summary); local and import-prefixed names"
  },
  {
   "where": "internal/storage/template_store.go:170",
   "entry_point": "MCP templates create (internal/mcp/handlers/template.go:193), CLI template create (internal/cli/template.go:284)",
   "module_kind": "storage layer, neighbouring feature"
  },
  {
   "where": "internal/server/routes/templates.go:304",
   "entry_point": "HTTP POST /templates/preview templateFile field (internal/server/routes/templates.go:274)",
   "module_kind": "HTTP handler, neighbouring feature (web UI, not MCP)"
  }
 ],
 "O1_entry_points": 10,
 "O2_out_of_scope_site": {
  "kind": "save_reload_or_serialization",
  "where": "internal/storage/memory_store.go:452 (moveLayer builds the filename from entry.ID that parseMemoryContent took from file frontmatter at internal/storage/memory_store.go:522; also Update via internal/storage/doc_store.go:324-335 and internal/server/routes/memories.go:191-242). Second out-of-scope cluster: template store + HTTP template preview (internal/storage/template_store.go:115, internal/server/routes/templates.go:304), a feature the advisory title does not name."
 },
 "O3_reason_to_dismiss": "Promote/demote and Update re-use an ID that was already validated on Get, so the ID 'came from our own file' and looks trusted; templates and the web-UI preview are not 'MCP Docs + Memory' and look like a separate feature.",
 "O4_distance": {
  "files": 6,
  "packages": 5,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Nested doc paths (guides/setup), optional .md suffix, and import-prefixed doc lookup with short-path fallback must keep working; memory title-slug reference fallback calls Get with non-ID strings and must fall through, not hard-fail; import-qualified template names (import/name) contain a slash by design.",
  "where": "internal/storage/doc_store.go:138-166; internal/storage/memory_store.go:150-182; internal/storage/template_store.go:110-113"
 },
 "O6_input_shapes": [
  "forward-slash parent traversal (../x)",
  "backslash traversal (..\\x)",
  "absolute POSIX path (/tmp/x)",
  "Windows volume path (C:\\x)",
  "UNC path (\\\\server\\share)",
  "Windows device prefix (\\\\?\\C:\\)",
  "NUL byte",
  "symlink inside root pointing outside",
  "NTFS alternate data stream colon (name:stream)",
  "memory ID containing a slash (nested/id) or ending in a dot",
  "import-qualified template name with traversal (import/../../escape)",
  "trailing .md suffix on doc path"
 ],
 "O7_producer": {
  "kind": "serializer",
  "where": "internal/storage/memory_store.go:501-551 (parseMemoryContent sets entry.ID from frontmatter at :522); internal/storage/memory_store.go:581 (renderMemory writes id unquoted)",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "Template engine reads action.Template / action.Source files joined to tmpl.Path (or taken as absolute) with no containment, the same template-dir boundary the fix added to /templates/preview.",
   "where": "internal/codegen/template_engine.go:326-333",
   "reason_to_dismiss": "Paths come from _template.yaml written by the template author, not from request input, and the engine is only reached from the local CLI (internal/cli/template.go:216-218); MCP run is not implemented (internal/mcp/handlers/template.go:169-176).",
   "distance": "internal/codegen package, 3 packages from the MCP landing point",
   "present_in_latest": "yes",
   "latest_where": "latest/internal/codegen/template_engine.go:331"
  },
  {
   "route": "Template engine add-many source dir joined from action.Source without containment.",
   "where": "internal/codegen/template_engine.go:145",
   "reason_to_dismiss": "Same as above: template-author config, CLI-only.",
   "distance": "internal/codegen package",
   "present_in_latest": "unknown",
   "latest_where": ""
  }
 ],
 "O8b_injection_room": [
  {
   "where": "internal/storage/version_store.go:335-338",
   "sibling": "legacyDocVersionPath builds versions/doc-<path>.json by replacing only '/' (backslash survives); a doc-history read/write route taking a raw path would be a natural sibling.",
   "why_realistic": "Doc history is keyed by doc path and a maintainer added a separate 'safe' replacer for stable IDs at :340-343 but not for legacy paths."
  },
  {
   "where": "internal/server/routes/templates.go:320-322",
   "sibling": "Preview's destination lookup by templateFile could plausibly read the existing destination file for a diff view.",
   "why_realistic": "The handler already maps templateFile to action.Path; showing current destination content is an obvious UI feature."
  },
  {
   "where": "internal/storage/memory_store.go:278-298",
   "sibling": "A memory 'restore from snapshot/journal' path taking an ID from a migration journal on disk.",
   "why_realistic": "RestoreLegacyDecisionMigration already writes using a snapshot entry's ID; a sibling restore route reading IDs from journal JSON is a realistic save/reload addition."
  }
 ],
 "O9_family": "path traversal / missing containment of identifier-to-filename mapping (CWE-22)",
 "O9_dos": false,
 "O10_build": {
  "language": "Go",
  "toolchain": "go 1.24.2 (go.mod:3); modernc.org/sqlite pure Go (go.mod:19); github.com/yalue/onnxruntime_go (go.mod:17) loads a shared lib at runtime, not needed for storage tests",
  "services": [],
  "offline_after_build": true,
  "project_tests": "internal/storage/doc_store_test.go, internal/storage/memory_store_test.go, internal/mcp/handlers/doc_test.go, internal/mcp/handlers/memory_test.go, internal/server/routes/memories_test.go (go test ./internal/storage/... ./internal/mcp/handlers/... ./internal/server/routes/...)"
 },
 "O11_fix_minutes": 60,
 "O12_red_flags": [],
 "O13_recall_risk": "low",
 "pattern_fit": "A",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "internal/models/memory.go, internal/safepath/path.go (new), internal/server/routes/templates.go, internal/storage/doc_store.go, internal/storage/memory_store.go, internal/storage/template_store.go",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 0,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Reject '..' in the MCP docs/memory handler params (or strings.Contains(path, \"..\") in DocStore.Create/Get), leaving delete/rename/promote, frontmatter-sourced IDs, absolute/backslash/symlink shapes and the template store + preview open."
 },
 "out_of_scope_notes": [
  "CWE-306 in the advisory suggests the local HTTP/MCP server lacks auth; not pursued.",
  "internal/server/routes/imports.go:93 and :601 join a request-supplied import name under .knowns/imports and RemoveAll it; different sink (imports), not checked.",
  "internal/codegen/template_engine.go:159-167 and :627-636 render destination paths from user vars and accept absolute paths; project-root write sink, not this advisory's protection."
 ],
 "unverified": [
  "pinned_commit hash not provided (parent_commit null); repo assumed to be the fix parent.",
  "repo size in MB not measured (no shell); tiny_repo/giant_repo not assessed.",
  "Whether the MCP memory tool lets a caller choose the ID on create (internal/mcp/handlers/memory.go:334) was not traced end to end.",
  "Whether onnxruntime_go requires cgo at build time was not checked.",
  "O1 count of 10 groups MCP docs/memory/templates, HTTP docs/memories/templates/preview, CLI doc/memory/template; exact grouping is a judgement.",
  "Doc Get no longer trims a leading '/' after the fix (fix.diff:380-385); whether any caller relies on that was not checked."
 ]
}
  ```
- Published fix sites:   - internal/storage/doc_store.go:124 — entry point: MCP docs get/update (internal/mcp/handlers/doc.go:229), HTTP docs GET (internal/server/routes/docs.go:185), CLI doc view (internal/cli/doc.go:147) [storage layer (lower-level API under handlers), incl. imports lookup at :146 and :158]
  - internal/storage/doc_store.go:173 — entry point: MCP docs create (internal/mcp/handlers/doc.go:376), HTTP docs POST (internal/server/routes/docs.go:226), CLI doc create (internal/cli/doc.go:301) [storage layer]
  - internal/storage/doc_store.go:185 — entry point: MCP docs update (internal/mcp/handlers/doc.go:472), HTTP docs PUT (internal/server/routes/docs.go:306), CLI doc edit (internal/cli/doc.go:390), RewriteDocReferences (internal/storage/doc_store.go:284) [storage layer]
  - internal/storage/doc_store.go:200 — entry point: MCP docs rename (internal/mcp/handlers/doc.go:465), HTTP docs PUT rename (internal/server/routes/docs.go:297), CLI doc edit rename (internal/cli/doc.go:383) [storage layer; two paths (old and new)]
  - internal/storage/doc_store.go:344 — entry point: MCP docs delete (internal/mcp/handlers/doc.go:635), CLI doc delete (internal/cli/doc.go:439) [storage layer]
  - internal/storage/memory_store.go:135 — entry point: MCP memory get (internal/mcp/handlers/memory.go:189), HTTP memories GET (internal/server/routes/memories.go:95) [storage layer]
  - internal/storage/memory_store.go:203 — entry point: reached via MemoryStore.Get (internal/storage/memory_store.go:137) [storage layer, lower-level public method]
  - internal/storage/memory_store.go:219 — entry point: memory review/capture create (internal/memoryreview/review.go:300) [storage layer]
  - internal/storage/memory_store.go:258 — entry point: MCP memory update (internal/mcp/handlers/memory.go:481), HTTP memories PUT (internal/server/routes/memories.go:242), RewriteDocReferences (internal/storage/doc_store.go:335) [storage layer; ID may come from file frontmatter]
  - internal/storage/memory_store.go:332 — entry point: Update and RestoreLegacyDecisionMigration (internal/storage/memory_store.go:271, :298) [storage layer, internal writer]
  - internal/storage/memory_store.go:351 — entry point: MCP memory delete (internal/mcp/handlers/memory.go:525), HTTP memories DELETE (internal/server/routes/memories.go:724) [storage layer]
  - internal/storage/memory_store.go:435 — entry point: MCP memory promote/demote (internal/mcp/handlers/memory.go:551, :574) [storage layer; uses entry.ID re-read from file frontmatter (save/reload)]
  - internal/models/memory.go:176 — entry point: new ValidateMemoryID helper next to MemoryFileName (fix.diff:24-31) [models package (validator)]
  - internal/storage/template_store.go:108 — entry point: MCP templates get/run (internal/mcp/handlers/template.go:101, :144), HTTP templates [storage layer, neighbouring feature (templates not named in the advisory summary); local and import-prefixed names]
  - internal/storage/template_store.go:170 — entry point: MCP templates create (internal/mcp/handlers/template.go:193), CLI template create (internal/cli/template.go:284) [storage layer, neighbouring feature]
  - internal/server/routes/templates.go:304 — entry point: HTTP POST /templates/preview templateFile field (internal/server/routes/templates.go:274) [HTTP handler, neighbouring feature (web UI, not MCP)]
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

## Environment (`tasks/knowns-ds/environment/Dockerfile`)
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

## Report to the solver (`tasks/knowns-ds/instruction.md`)
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

## Tests (`tasks/knowns-ds/tests/`)
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
- **Wrong-fix patches** go in `build/knowns-ds/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/knowns-ds/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/knowns-ds/manifest.json`:**
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

**Also in `build/knowns-ds/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py knowns-ds --only static
python3 -I builder/gate.py knowns-ds --only nop
python3 -I builder/gate.py knowns-ds --only oracle
python3 -I builder/gate.py knowns-ds --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/knowns-ds/`;
  - edit only `tasks/knowns-ds/`, `build/knowns-ds/` and, for pattern B, the register;
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
