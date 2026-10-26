# flyto-core-mm — build notes (build-v1)

Task: flytohub/flyto-core, GHSA-2956-977X-2W3R / CVE-2026-67429 / PYSEC-2026-3568.
CWE-22 / CWE-73 — caller-influenced file writes escape the operator sandbox
(`FLYTO_SANDBOX_DIR`). Pattern **A+B**, track **INJECTED**.

- Start (UTC): 2026-10-18T19:12:12Z
- End (UTC): (end of file)

## Why a new task on the same advisory
`flyto-core-path-traversal` (mined, no injections) was built earlier and **missed the bar**:
DeepSeek and MiMo each scored 0.96 then 1.0 on their finished runs. This task is the
injected-track redesign: same advisory and same published fix sites (which the tests must
still cover), with a harder trap stack whose difficulty comes from sibling gaps a solver
must find on its own.

## Shipped `/app`
pinned commit `9103529c204cad3e698b726ed958b626bcfbc182` (verified sole parent of fix
`d5f89d7`) + `environment/injection.patch` (three sibling gaps). `/app/.git` removed.
Oracle = `solution/fix.patch` = published source changes + fixes for every uncovered
route and every injected sibling.

## Design plan (written before build)

### The recurring trust decision
"May this caller-influenced destination be written?" It must resolve inside
`FLYTO_SANDBOX_DIR`, decided by `validate_path_with_env_config` (realpath + prefix check,
`src/core/utils.py`). Every lever is a place where that decision is missing or wrong.

### Levers (pattern, shape, where, reason to dismiss)

**Pattern A — the published fix's far sites (report leads to one).**
- **A1 landing (report's example).** `image.download`: the existing check compares the
  output against a caller-supplied base, so both sides are attacker-controlled.
  Dismiss: none — this is what the report points at. Lever: a base-only fix misses the
  derived-name and mkdir-before-check shapes.
- **A2 image package siblings.** compress/convert/crop/resize/rotate/watermark/qrcode
  (incl. the `.png`→`.svg` rewrite before the write). Dismiss: "the example is the
  download module" / "same package, I got them all".
- **A3 document package writers.** excel_write, pdf_fill_form, pdf_to_word, word_to_pdf
  (incl. derived default outputs). Dismiss: "the example is an image module; document
  conversion is a different feature".
- **A4 save/reload state file.** browser pagination's checkpoint path → written by
  `core/browser/checkpoint.py`. Dismiss: "internal resume state, not an output file".

**Pattern B — uncovered routes (real, unmodified upstream; published fix never touches).**
- **B1 existing weak check.** `data/csv_write.py` + `data/json_to_csv.py`: a `..`
  substring test only; absolute destinations pass. Dismiss: "already has a traversal
  check".
- **B2 generic file ops.** `file/copy.py` + `file/move.py` destinations, and `file/move`
  **source** removal (an outside file is removed by moving it in). Dismiss: "generic file
  ops next to the already-guarded write; the report is about output files".
- **B3 delete module.** `file/delete.py` removes any caller path. **Dropped after the
  probe:** it is in `_DEFAULT_DENYLIST`, so it is not reachable through the real entry
  point at the pinned commit. A solver would reasonably say it is already blocked by
  policy.
- **B4 reader with a generated-name output directory.** `document/word_parse.py`
  extracts embedded images into a caller directory with the same no-op caller-relative
  check as the landing point. Dismiss: "a parser/reader; the file names are generated".
- **B5 content generator.** `document/pdf_generate.py` writes a caller output path with
  no check. Dismiss: "generates new content rather than transforming a user file".
- **B6 state/cache file.** `data/dedup.py` `hash_file` — cross-run hash list written to
  a caller path with no check. Dismiss: "a cache of seen hashes, not a module output".
- **B7 archive entries (content-derived names).** `archive/zip_extract.py` and
  `archive/tar_extract.py` already reject `..` entries with a raw string-prefix test, so
  a sibling directory whose name extends the output directory name slips past.
  **Dropped after the probe:** the stdlib defends the sink (`zipfile._extract_member`
  strips `..` components; `tarfile.extractall(filter='data')` refuses escapes), so the
  route does not reproduce at runtime.

**Input shapes (covered across the sites above).** absolute outside; relative with `..`
segments; in-sandbox `..`/`.` spellings that stay inside (must keep working); symlink
inside the sandbox resolving outside; module-derived default output; path rewritten
before the write; directory created before the check.

**Coupled must-keep-working (over-broad fix fails).** Absolute and relative paths that
land inside; `..`/`.` spellings that still end up inside; new sub-directories created as
today; default-derived outputs that fall inside; `FLYTO_ALLOW_ABSOLUTE_PATHS` default
true; the already-guarded write module keeps working without its optional extras;
namespaced state store keeps working when no override is given; a normal archive
extracts as today; the dedup hash file keeps working inside the sandbox.

### Injected siblings (track requirement: 2–4 at the recurring trust decision)
Each is new product code a maintainer could plausibly have left, reachable through
`POST /v1/execute`, covered by a stated invariant, and in a file the published fix never
touches. Each has its own reason a solver would skip it.

- **S1 `file.write` optional `backup_path`** — `src/core/modules/atomic/file/write.py`.
  Before overwriting, copy the previous contents to a caller-supplied path (unchecked).
  Mechanism: a second full caller-supplied destination beside a validated one.
  Dismiss: "this module already validates its path (its tags even say `path_restricted`),
  so it is known-safe; the backup is only a copy of an in-sandbox file".
  Realistic: backup-before-overwrite is a stock write-module feature.

- **S2 `storage.set` optional `file_path`** — `src/core/modules/atomic/storage/kv.py`.
  When given, the record is also persisted to that caller path (unchecked). The module's
  own design is a namespaced key-value store that writes to a fixed directory with a
  sanitised namespace.
  Mechanism: an optional path override on a module that otherwise has no path parameter.
  Dismiss: "this is a key-value store, not a file-output module; it writes to a fixed
  directory".
  Realistic: "also keep a copy where I say" is a natural export convenience.

- **S3 `data.export_records` (new module)** — `src/core/modules/atomic/data/export_records.py`.
  Writes one file per input record into `output_dir`. `output_dir` **is** validated with
  the existing helper (so the module looks protected); the file names are built from a
  field of each record and are not.
  Mechanism: a destination assembled from untrusted data content rather than from a path
  parameter — nothing to point the helper at.
  Dismiss: "the output directory is validated; the names come from the records, not from
  a path parameter".
  Realistic: "split a dataset into one file per record" is a normal workflow step.

### Why the levers do not fall together
S1/S2 are "a second caller-supplied destination" but sit in modules whose existing check
or design makes them look finished; S3 has no path parameter at all, so a sweep that
validates path-typed parameters finds nothing to fix. B3 is a removal, B6 is a cache,
B7 is content-derived names behind a check that looks correct. B1 looks already
protected. A1–A4 are the published scope and are far apart (image / document / browser).

### Sites, routes and shapes the security tests will cover
One test per (site, shape) that is distinct in mechanism — see `traps` in the manifest for
the exact mapping. 37 security tests: 11 image (A1/A2 incl. derived default and
symlink), 6 document (A3 incl. derived defaults), 2 pagination (A4 interrupted and
completed), 4 data writers (B1 incl. mkdir-before-check), 3 file copy/move (B2),
1 word_parse images (B4), 1 pdf_generate (B5), 2 dedup (B6), 2 file.write backup (S1),
2 storage extra file (S2), 3 export_records names (S3).

### Functional tests
36 in-sandbox tests: absolute and relative writes; in-sandbox `..`/`.` spellings; new
sub-directories; derived defaults inside; QR svg variant; download default name into an
in-sandbox directory; checkpoint save+resume inside; file.write with and without
backup_path (backup inside works); storage.set namespaced and with an in-sandbox
override; export_records with benign names (including a plain sub-path name); dedup hash
file inside; plus the project's own tests for the affected area
(`tests/modules/test_new_modules.py::TestImageModules`, `tests/browser/test_checkpoint.py`)
run from pristine copies with TMPDIR/basetemp inside the sandbox.

### Instruction shape
Product-level system description; ONE concrete trigger at user level (a `POST /v1/execute`
body); the properties as invariants ("no value of X may …"), worded to cover every tested
route and shape without listing them; the refusal contract (`"ok": false` or any 4xx,
no side effect — including directories); the preservation clauses; "examples are
examples"; the standard constraints block. No file/function/parameter names beyond the
one in the example trigger, no line numbers, no root cause, no CVE id, no route list.

### Fairness / things to watch
- Refusal must be required explicitly (a clamp-or-redirect fix must fail).
- Do not name `backup_path`, `file_path`, `export_records`, `hash_file`, `trash`/`move`
  sources, `images_output_dir`, archive entry names, or any helper name in the
  instruction; all of these go in `manifest.leak_terms`.
- Compute every expected path and clean-up inside the tests (never call product code to
  do it).
- Assert "any client error / not ok + no side effect", never one exact status.
- Project tests must run with `TMPDIR` and `--basetemp` inside the sandbox so a
  sink-level guard is not punished for the tests' own scratch files.
- `image.download` needs a fetch: a local 127.0.0.1 HTTP server allowed by
  `FLYTO_ALLOW_PRIVATE_NETWORK` + `FLYTO_HTTP_ALLOWED_PORTS`; no external network.
- Pagination is driven with a stub browser session registered in the server's session
  table (no Playwright browsers); the product code performs every file write.

## Verified
- Pinned commit `9103529c204cad3e698b726ed958b626bcfbc182` is the sole parent of the
  published fix `d5f89d7` (`git rev-parse d5f89d7^`).
- `environment/injection.patch` applies cleanly to a pristine pinned tree
  (`patch -p1 --dry-run`), touching 4 files, all outside the published fix's file list.
- All three injected siblings and every planned lever reproduce through
  `POST /v1/execute` on the pinned+injected tree (probe: 34/38 initially; A4 fixed with
  an interrupted run; B3 and B7 dropped, see below).
- Hidden tests on the oracle (fix.patch): 37/37 security pass, 36/36 functional pass.
- Hidden tests on pinned+injected: 37/37 security fail (every lever reproduces).
- Project tests (`tests/modules/test_new_modules.py::TestImageModules`,
  `tests/browser/test_checkpoint.py`, 15 cases) pass on the oracle offline with
  TMPDIR/`--basetemp` inside the sandbox.
- `solution/fix.patch` applies cleanly to the pinned+injected tree and is byte-identical
  to the intended fix tree (23 files, all under `src/`).
- instruction.md contains none of `manifest.leak_terms`, no advisory id, no fix sha, and
  no basename of any file the fix touches (gate-style regexes).
- Local variant check: every `checks/` patch was applied to a clean inject tree and run
  against `tests/security` + `tests/functional` in the same Python 3.12 venv the image
  uses, before the Docker gate. All 21 behave as declared: 16 `security_fail`
  (≥1 security failure, 0 functional failures), 3 `functional_fail`, 2 `pass`.
- Two shape patches were first generated wrong and were caught and fixed before the
  gate: `sf-explicit-only` / `sf-mkdir-before-check` produced invalid Python (a
  mis-indented `try` in the download site; a mis-indented mkdir in the nested dedup
  site), and `sf-mkdir-before-check` / `sf-normpath-no-symlinks` called `os.makedirs`
  / `os.path.normpath` in `data/dedup.py` and `browser/pagination.py`, which do not
  import `os`. Caught by a compile pass and by the JUnit `name 'os' is not defined`
  functional failures; both fixed (mkdir via `Path(...).parent.mkdir`, `import os`
  added where `os.path.normpath` is used) and re-verified.
- Gate `static` fails only on the two artefacts this brief forbids writing
  (`blind` pass patch, `FAIRNESS.md`). Gate `nop` and `oracle` pass.
- Gate `patches` is held up by shared-box contention, not by a check-patch verdict:
  17 concurrent `gate.py` runs on the 8-CPU VM pushed the 1-minute load to 32–47, and
  the stage aborts before judging any check with either `Docker compose command failed`
  or `network_mode='allowlist' is not supported by EnvironmentType.DOCKER` (the egress
  sidecar that enforces the allowlist fails to start under that load). Different checks
  abort on successive attempts, which is the flake signature. A load-aware retry is
  running. This is outside the task's scope and is not built on.

## Not verified / not built
- **B3 `file.delete`** — dropped. It is in `core/module_policy.py` `_DEFAULT_DENYLIST`,
  so it is not reachable through the real entry point at the pinned commit. Testing it
  would require clearing `FLYTO_MODULE_DENYLIST` before `core` is imported, which would
  make the route depend on a setting the instruction does not name.
- **B7 archive entry names** (`archive/zip_extract.py`, `archive/tar_extract.py`) —
  dropped. The modules' own `startswith` checks are weak, but CPython defends the sink:
  `zipfile._extract_member` strips `''`/`'.'`/`'..'` components, and
  `tarfile.extractall(filter='data')` refuses escapes. The route does not reproduce at
  runtime, so it is not a fair test.
- `browser/download.py`, `browser/screenshot.py` — the write is done by the browser
  driver, not reachable with a stub.
- `browser/cookies_file.py` — reachable, but same concept as A4 (save/reload state);
  left out to avoid stacking routes of one concept. Used only as extra hardening in
  `checks/pass-hardening.patch`.
- Out-of-scope bundled changes in the published fix commit (different advisories; not
  built on): `engine/variable_resolver.py`, `module_policy.py`, `ai/model.py`,
  `llm/agent.py`, `llm/chat.py`, `vector/connector.py`.
- No trials and no target model were run. `blind.patch` and `FAIRNESS.md` are not
  written here — others write those.
