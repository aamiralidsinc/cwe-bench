# knowns-mm — build notes

- Start: 2026-10-18T19:12:12Z
- End: (see end_utc.txt)

## Task
GHSA-9GFJ-28HW-JCHP / CVE-2026-86439, knowns-dev/knowns, CWE-22. Pattern A,
track INJECTED. Pinned `d3989829fb5095666d23d005b2f78a082832a396` (verified
direct parent of fix `09c5a96fd5817b941dc86669278c1a17db10ed4e`). Mechanism:
the storage layer turns a caller-supplied doc path / memory ID / template name
into a filename under `.knowns/{docs,memory,templates}` (or `~/.knowns/memory`)
with `filepath.Join` and never checks that the result stays inside.

## Seam
Pure Go tests against a temporary project folder, driving the MCP tool handlers
and the web UI HTTP routes exactly as the project's own tests do (`storage.NewStore`,
`store.Init`, `handleDocCreate(...)` / `httptest`). No server process, no network,
no services. Base `golang:1.24-bookworm`, `GOTOOLCHAIN=local`, module cache baked
in at image build, `go-junit-report` for JUnit XML.

## Verified escapes at pinned (Linux, through real entry points)
- doc create `folder` / get `path` / delete `path`: `../../../x` writes, reads and
  removes outside `.knowns/docs`.
- memory get/delete `id`: `../../../../../x` (the `memory-` filename prefix absorbs
  one `..`) reads and removes outside the memory dir.
- symlink inside `.knowns/docs` pointing outside: `link/out` reads through it.
- template name: `../../../x` resolves outside `.knowns/templates`.
- template preview `templateFile`: joined onto the template dir without containment.
- stored frontmatter id + promote: `moveLayer` rebuilds the filename from the id the
  parser took from the file and writes it outside the layer directory.

## NOT escapes on Linux (dropped as security shapes, per the screener's own limit)
absolute `/tmp/x` (Join folds it into a subdir), backslash / drive / UNC / device
prefixes, NUL, NTFS colon, and a one-segment memory id `../x` (becomes
`memory-../x.md`, still inside). These are not failing security tests.

## Levers (each with a different reason to dismiss; one line each)

- **L1 `doc_path_caller` (A, base / landing).** Caller-supplied document path via the
  documentation tool (create folder, get, update, update new-path, delete) joined onto
  the documents directory. Shape: forward-slash parent traversal `../../../x`.
  Dismiss: none — this is where the report lands.
  Coupled keep-working: nested paths (`guides/setup`), optional trailing `.md`,
  import-prefixed lookup with its short-path fallback.

- **L2 `memory_id_caller` (A, far).** Caller-supplied memory identifier via the memory
  tool (get, delete) joined onto the memory directory as `memory-<id>.md`.
  Dismiss: the report is about documents; memory is another tool and another
  directory; and a one-segment `../` looks harmless because the filename prefix
  absorbs it. Distance: different file, different tool.

- **L3 `memory_id_stored` (A, far, save/reload producer).** An identifier already
  recorded in a stored record's own on-disk metadata is reused when that record is
  moved between layers. The filename builder does not call the parser that produced
  the identifier. Shape: planted record, hostile metadata id, then a move.
  Dismiss: "the identifier came from our own file, and was accepted when the record
  was read."

- **L4 `template_name` (A, far, neighbouring feature).** Template name joined onto the
  templates directory (create/get), and the web interface's template-preview file
  argument joined onto that template's directory.
  Dismiss: templates are a neighbouring feature the report does not name; the preview
  is the web interface, not the assistant tools. Distance: separate package(s).
  Coupled keep-working: import-qualified names (`source/feature`) contain a slash by
  design; the default preview file when none is named.

- **S1 `doc_archive` (injected).** New document-archive operation mirroring the
  existing task archive: copies a document into the project's archive area, keyed by
  the document's path. Lives in a new file the published fix never touches; reached
  through a new action on the documentation tool.
  Dismiss: a derived copy in a separate archive area, not the live documents the
  report is about.

- **S2 `memory_history` (injected).** New memory-revision-history side record keyed by
  the memory identifier, in the versions area (same idiom as the existing task history
  file). Lives in a new file the published fix never touches; reached through a new
  action on the memory tool.
  Dismiss: a read of a system side-record in a different area; guarding the live
  record's own read/write is what the report asks for.

## Input shapes under L1
forward-slash parent traversal (tested), and a symlink inside the documents directory
pointing outside (tested — a purely lexical `..` check misses it, so it is a separate
security test). Windows/absolute/NUL shapes dropped (see above).

## Sites / routes the security tests will cover
MCP docs create, MCP docs get, MCP docs delete, MCP memory get, MCP memory delete,
MCP memory promote (stored id), MCP templates create/get, HTTP template preview
`templateFile`, MCP docs archive (S1), MCP memory history (S2), plus the symlink shape
on docs get.

## Coupled must-keep-working (functional)
- doc nested path `guides/setup`, doc path with a trailing `.md`, import-prefixed doc
  lookup with short-path fallback;
- ordinary memory identifiers (dots, dashes, underscores), memory title-slug reference
  fallback still resolves (or falls through) rather than hard-failing;
- a normally-named memory record with ordinary metadata still promotes;
- import-qualified template names (`source/feature`), default preview file `main.hbs`;
- an in-project symlink whose target stays inside must keep working (so an
  over-broad "reject every symlink" fix fails);
- the project's own suites for storage, MCP handlers and server routes.

## Oracle
Published fix reduced to source changes (new path-confinement helper, applied across
the doc, memory and template stores and the preview handler; plus the memory-identifier
validator) **plus** the same confinement applied at the two injected sibling sites.
Signature-stable: no public method signature changes, so the project's own tests
compile and pass unchanged.

## Wrong-fix patches planned (build/knowns-mm/checks/)
- `sec_miss_doc.patch` — fixes memory + templates + siblings, leaves the doc path open
  → security_fail
- `sec_miss_memory.patch` — fixes docs + templates + siblings, leaves caller memory ids
  open → security_fail
- `sec_miss_stored.patch` — validates only caller-supplied ids, not the stored-metadata
  id → security_fail
- `sec_miss_template.patch` — leaves the template name / preview file open
  → security_fail
- `sec_miss_archive.patch` — leaves the injected archive sibling open → security_fail
- `sec_miss_history.patch` — leaves the injected history sibling open → security_fail
- `func_overbroad.patch` — rejects every value containing `..` or any symlink
  → functional_fail
- `hardening.patch` — oracle + defensive hardening of the product code the security
  tests import → pass
- `alt_fix.patch` — a second valid design (lexical containment at the store boundary
  via a shared helper, plus realpath containment for the symlink shape) → pass
- `blind.patch` — NOT written here (downstream, as instructed)

## Pattern B
None required (prompt says "uncovered routes to confirm: none"). The screener's
candidate uncovered routes (codegen destination paths, imports RemoveAll, template
engine action sources) were reviewed and left alone — noted in the final report.

## Fairness notes
- The codebase already contains a memory-identifier validator for the decision-migration
  journal (`migrationMemoryIDPattern`), so the containment approach is discoverable.
- Refusal form is stated in the report as "a plain client error and no side effect".
  Tool handlers refuse via a tool error; the web preview route refuses with a client
  error (the published fix and both designed fixes return 400 there, matching the
  handler's existing "invalid request" style). No exact-status asserts: the preview
  test accepts any 4xx and rejects 5xx so a crash-as-refusal cannot pass.
- `CGO_ENABLED=1` is required to build the handlers/routes packages (an optional
  embedding dependency is cgo-only). Set in the Dockerfile and test.sh; not a
  solver-facing requirement.
- The report must not name: safepath, ValidateMemoryID, resolveDocPath, MemoryFileName,
  doc_store/memory_store/template_store, the archive or history siblings, CVE/GHSA ids,
  or the commit shas.

## Build-time verification (2026-10-18)
- Hidden suites: 13 security tests FAIL on inject and PASS on oracle; 8 functional
  tests PASS on both. Project models/storage/handlers/routes suites PASS on both.
- All nine written check patches verified at the expected outcome before the gate:
  six security_fail (each leaving only its own site open), func_overbroad
  functional_fail, hardening + alt_fix pass (13+192).
- Gate: static FAIL only on missing `checks/blind.patch` and missing `FAIRNESS.md`
  (both written downstream, as instructed). nop PASS. oracle PASS (3 identical runs).
  patches: all nine written checks PASS in-gate at the expected outcome.
- `tests/test.sh` skips `TestTaskAutoArchiveSweeper*` in the functional suite: those
  project tests wait on a 3s wall-clock deadline and flake under the shared VM.
  They cover task retention, which this report does not touch. Hidden functional
  tests and the rest of the project suites are unchanged.
- Patch headers were normalised to `a/` `b/` relative paths before the gate (the
  first generation left host paths in `+++` lines; `patch -p1` still applied, but
  the shipped artefacts must not carry them).
