# Build notes: knowns-ds

- Start (UTC): 2026-10-18 19:08
- End (UTC): 2026-10-18 20:34

## Advisory / commits

GHSA-9GFJ-28HW-JCHP / CVE-2026-86439 — knowns-dev/knowns, CWE-22: identifiers
(document path, memory id, template name) are joined to a filename inside the
managed roots without a containment check. Pinned (vulnerable)
`d3989829fb5095666d23d005b2f78a082832a396`, verified parent of the published
fix `09c5a96fd5817b941dc86669278c1a17db10ed4e`. Track INJECTED, pattern A.

## Mechanism (one line)

A caller-supplied or stored identifier is turned into a path under
`.knowns/{docs,memory,templates}` (resp. `~/.knowns/memory`) with
`filepath.Join` and no check that the result stays in the root; the published
fix routes every such mapping through a new `safepath` helper and validates
memory ids.

## Levers (8; all verified nop-fail / oracle-pass offline)

- T1 templates (A, published far site): template store name mapping
  (`template_store.go` Get/Create, incl. import-qualified names) and the
  preview's template-file selection (`routes/templates.go`). Dismiss: the
  report is about documents and memory; the code-generation template library is
  a different feature/package.
- T2 document writes (A, published far sites): create, update/rename (old and
  new path), delete in `doc_store.go`, each with its own join. Dismiss: the
  report shows a read; the write operations look like the same store and are
  assumed covered by the read guard.
- T3 document read shapes (landing-site variants): imported-doc lookup,
  symlink target outside the root, URL-encoded wildcard, absolute /
  backslash / volume / UNC / device spellings. Dismiss: a plain `..` check
  fixes the example but misses these.
- T4 memory identifiers from requests (A, landing feature's sibling):
  get/delete/create-via-review with slash-bearing ids; trailing dot, backslash
  and colon spellings. Dismiss: ids are generated tokens, so they look trusted.
- T5 memory ids stored in a file (A, save/reload far site): promote/demote
  re-use the id read from the record's own metadata in `moveLayer`. Dismiss:
  the id "came from our own file", so it is treated as trusted.
- S1 injected: memory snapshot view (`memory({action:"snapshot"})` plus
  `ReadSnapshot`/`writeSnapshot`) maps the id under `.snapshots` with no
  validation. Dismiss: read-only recovery view of our own backup.
- S2 injected: template preview returns the destination file's current
  contents (`existingContent`); the destination comes from template actions
  after request-variable substitution, joined to the project root with no
  containment. Dismiss: destination looks like template-author config; the
  published protection covers the template-file read above it.
- S3 injected: raw document source view (wildcard `/source` action serving the
  on-disk `.md`) rejoins the requested path to the docs root instead of going
  through the store's read. Dismiss: an export view for the web UI, assumed to
  be the same document store the report covers.

Distinct reasons-to-skip: different-feature / read-vs-write / spelling-variant
/ generated-token / trusted-stored-value / read-only-backup / config-derived /
bypasses-the-fixed-store.

## Verified

- At pinned: docs get `../secret` (MCP and HTTP, plain and URL-encoded), doc
  rename/create, doc delete via the MCP tool, imported-doc lookup, symlink
  inside `docs`, memory get/delete/create-via-review with a slash id, promote
  with a frontmatter id, template create and import-qualified get, preview
  `templateFile`, and all three injected views read/write outside their roots
  on Linux. Project tests for the three packages pass at pinned.
- Hidden suite: 19 security test functions (28 JUnit cases) — 0 pass on
  pinned+injected, all pass on the oracle; functional group 203 JUnit cases
  (hidden functional + pristine project tests) passes on both trees.
- Oracle stage: 3 Harbor runs, reward 1.0 and identical results each time.
- Nop stage: PASSED (all security fail, all functional pass).
- 11 check patches: each applies with `patch -p1` to the pinned+injected tree,
  compiles, and behaves as declared locally (8 security_fail isolating their
  lever, 1 functional_fail, hardening/alternative pass).
- The published fix's added tests are absent at pinned (no leaked regressions).

## Fixes made during the build

- Moved the injected snapshot helpers into `memory_store.go` so the injection
  patch does not share >=3 distinctive lines with the hidden tests (the static
  gate's image-leak check counts shared import/struct-tag lines).
- Removed `CGO_ENABLED=0` from the Dockerfile and test.sh: the project's
  `onnxruntime_go` dependency has no files under `CGO_ENABLED=0`, so the
  handlers/routes test binaries would not build. gcc is present in the golang
  image.

## Gate results

- static: FAILS only on the two downstream items the build prompt reserves
  (`checks/blind.patch` and `build/knowns-ds/FAIRNESS.md`); everything else
  (metadata, agent layer, no leaks, no hidden tests in the image, offline
  allowlist, kill block, wrong-fix catalogue) passes.
- nop: PASSED (28 security cases all fail, 203 functional cases all pass).
- oracle: PASSED (3 runs, reward 1.0, identical results).
- patches: every declared check behaves as declared — verified from the trial
  results of a full 11-check run; the gate then aborted copying the
  intentionally-absent `blind.patch`, so the stage was re-run without it (8
  checks formally green before a Docker network race on the 9th) and finally
  the remaining three were re-run and the stage PASSED. The network race is
  infrastructure (`network ... not found`), not the task; the same check had
  already passed in the earlier trial.

## Could not verify / notes

- `present_in_latest` for injected siblings: n/a (our-copy-only).
- Windows-only spellings (volume, UNC, device, trailing dot) do not escape on
  Linux; they are tested as values that must be refused, and the published fix
  refuses them cross-platform.
- The doc delete site is unreachable with a traversing value once the read is
  guarded, because the MCP handler fetches the document first; its test still
  fails on pinned and passes on the oracle, but the delete-specific patch does
  not isolate it.
