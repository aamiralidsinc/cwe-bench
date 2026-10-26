# chrome-devtools-mcp-ds — build notes

- Start (UTC): 2026-10-24T02:42:10Z (build driver launch; this session began at 02:42Z)
- End (UTC): 2026-10-24T03:44:30Z
- Gate: static PASS 03:07; nop PASS 03:17 (8 security tests all fail on the vulnerable tree; 17 functional
  tests pass); oracle PASS 03:25 (3 runs, reward 1.0, identical); patches PASS 03:44 (all 8 checks as
  declared: L1 0.875, L2 0.625, L3 0.75, S1 0.875, S2 0.875, overbroad 0.0, hardening 1.0, alt 1.0).
- Advisory: GHSA-8QF9-62X2-82PP / CVE-2026-53766 (chromedevtools/chrome-devtools-mcp), CWE-22/CWE-59.
- Pinned vulnerable commit: 2eab50938093e848ca9786f2ce0c5bf371e63619 (parent of the only commit between it and
  the fix, 176eb695137d9c46a61e2d4d5571880c5145cf46). No advisory regression tests exist at the pinned commit.
- Pattern: B. Track: injected. Task slug: chrome-devtools-mcp-ds.

## Verified at the pinned commit (behavioural probes, no Chrome)

Harness for every probe/test: a real `McpContext` built over a stub browser/page (the browser is the external
boundary, not product logic), a real `ToolHandler` from the product's own tool registry, and real tool handlers.
Roots are set with `setRoots`; the "outside" tree lives under `$HOME`, never under `os.tmpdir()` (which is always
an allowed root).

| probe | pinned | published fix |
|---|---|---|
| take_screenshot to an in-root dir-link to an existing outside dir | writes outside | blocked |
| install_extension of an in-root dir-link to an outside dir | browser receives outside path | blocked |
| take_screenshot where the written name (ext rewrite) is an outside link | writes outside | **still writes outside** |
| take_heapsnapshot where the written name (ext rewrite) is an outside link | writes outside | **still writes outside** |
| take_screenshot to a dangling link under the root (target created outside) | creates outside | **still creates outside** |
| legit: nested not-yet-existing in-root output | works | works |

So the published fix (canonicalise the spelled path with realpath + nearest-ancestor walk, await the call sites)
closes the reported shape but leaves two real shapes open: a name the server derives from the path (extension
rewrite) and a link whose target does not exist yet. Both are real, unmodified upstream code.

## The single security property (as written in instruction.md)

Every file the server opens/reads/creates/changes/hands to another program or the browser while serving a tool
call must really be inside a workspace root (temp area counts); this covers the supplied path, paths the server
derives from it or keeps from an earlier step, and every link along the way, whether or not the target exists.
If it cannot establish that, it refuses with a client error and no side effect.

## Levers

### L1 — base, report-led (Pattern A). Existing in-root link to an outside file.
- Shape: a caller path traverses a symlinked directory (or a symlinked file) inside a root to an existing
  outside target; the lexical allow-list check passes and the tool reads/writes/installs through it.
- Where: `src/McpContext.ts:178-199` (`validatePath`), reached by every path-taking tool/handler.
- Reason to dismiss: none — this is the site the report leads to.
- Security tests: `security/write_symlink_dir.test.mjs` (take_screenshot), `security/install_symlink_dir.test.mjs`
  (install_extension).
- Coupled functional: in-root link whose target is also in-root; install from an in-root path.

### L2 — HOW-type shape: the file the server actually writes is not the path it checked.
- Shape: the checker validates the caller-spelled path, then the writer rewrites the name (extension swap) and
  writes the rewritten name; if that name is an outside link, the write escapes. The published fix validates only
  the spelled path, so this stays open.
- Where: `src/McpContext.ts:725-732` (`saveFile`, used by screenshot/snapshot/script/network/trace/lighthouse) and
  `src/tools/memory.ts:28-31` (`take_heapsnapshot`, its own extension rewrite). Real upstream code, untouched by
  the published fix.
- Reason to dismiss: "the extension swap leaves the file in the same directory, so the directory check covers it".
- Security tests: `security/write_renamed_target.test.mjs` (take_screenshot `x.txt` -> `x.png` link),
  `security/heap_renamed_target.test.mjs` (take_heapsnapshot `s.txt` -> `s.heapsnapshot` link).
- Coupled functional: normal in-root saves named with an arbitrary extension; nested new directories.

### L3 — HOW-type shape: a link whose target does not exist yet.
- Shape: an in-root link points at an outside path that does not exist. `realpath` fails ENOENT, the "nearest
  existing ancestor" fallback returns the link's own name as if it were a plain file, the check passes, and the
  write creates the target outside. The published fix has exactly this gap.
- Where: the same shared save sink and the heap-snapshot write; the gap is in the canonicalisation helper the
  published fix introduced (`src/utils/files.ts`, new function) and in every caller that relies on it.
- Reason to dismiss: "realpath plus a walk-up to the nearest existing ancestor already handles non-existent
  output files" — it handles missing *names*, not missing *link targets*.
- Security test: `security/write_dangling_link.test.mjs`.
- Coupled functional: saving to a genuinely absent nested path, and to a root reached through a link (a
  target-only canonicaliser denies these).

### L4 — coupled must-keep-working next to the sink (HOW-type, over-hardening).
- Behaviour: legitimate saves that a naive canonicaliser breaks: a not-yet-existing nested output; a root that is
  itself a link; a root list that contains an unresolvable root; no declared roots (legacy allow-all); the
  temporary area; an in-root link to an in-root target.
- Where (values): `src/McpContext.ts:161-172` (`roots()` appends temp), `:178-199`, `:706-732`.
- Functional tests: `functional/legit_saves.test.mjs`, `functional/legit_roots.test.mjs`,
  `functional/legit_temp_and_install.test.mjs` and the project's own `tests/utils/files.test.ts` (pristine copy).
- Wrong-fix check: `ff-overbroad.patch` (realpath-only canonicaliser) must fail these.

### S1 — injected sibling: re-install from a remembered path, no containment decision.
- Shape: the reload operation re-installs an extension from the path the browser reports instead of going through
  the guarded install path, so a path outside the roots is handed to the browser. Protection never existed on
  this route.
- Where: `src/tools/extensions.ts` (reload handler) + a new Context method in `src/McpContext.ts`; the published
  fix never touches either site.
- Reason to dismiss: the path is not the caller's — it came from the browser's own extension list — so it reads
  as already trusted; the request only carries an opaque id.
- Security test: `security/reload_outside_path.test.mjs`.
- Coupled functional: reload of an in-root extension still re-installs it.

### S2 — injected sibling: companion cache read in the snapshot manager, no containment decision.
- Shape: when loading a heap snapshot's summary, the manager first consults a companion cache file derived from
  the snapshot path. The snapshot path is checked; the derived cache path is not, so a link planted at the cache
  name reads an outside file and its contents are returned in the tool's answer.
- Where: `src/HeapSnapshotManager.ts` (stats/static-data cache), reached through the existing summary tool.
  The published fix never touches the manager.
- Reason to dismiss: "the snapshot was already checked and the cache sits next to it" — a derived path in an
  internal cache, not a caller argument.
- Security test: `security/heap_cache_outside_read.test.mjs`.
- Coupled functional: a genuine in-root cache is still used (the feature is not removed).

## Candidate sibling sites considered (full list) and why the picks won

Real upstream candidates found by search:
1. `take_heapsnapshot` extension rewrite (real route) -> promoted to L2, not a sibling.
2. `saveFile` extension rewrite (real route) -> L2.
3. `screencast_start` extension rewrite (real route, experimental + ffmpeg) -> dropped: same concept as L2 and
   requires ffmpeg at run time.
4. `lighthouse_audit` outputDirPath -> child report write (real route) -> same derived-path concept as L2 and needs
   a live Lighthouse run; dropped.
5. `get_network_request` request/response body files (real route) -> same saveFile sink as L2; needs a live network
   collector; dropped.
6. `getHeapSnapshotRetainers` missing check (real Pattern A far site; the published fix adds it) -> dropped as a
   *security* lever: the tool-level check masks it, so a test would have to call the lower-level API directly and
   a solver who fixed the check properly would still fail on an internal API a caller cannot reach. Kept as part
   of the oracle for defence in depth only.
7. `HeapSnapshotManager.#loadSnapshot` reads by path with no check (real) -> became S2's home (the injected cache
   adds a reachable, observable derived read); a bare snapshot read is not observable without a valid snapshot.
8. `reload_extension` re-install from a stored path (O8b) -> S1.
9. `daemon/client.ts` image export writes to a temp path (real) -> dropped: the path is not caller-chosen and the
   CLI user is the local operator, not the MCP client (out of the advisory's threat model).
10. `logger.ts`/`telemetry`/`check-for-updates`/browser user-data-dir paths (real) -> operator/env supplied, not
    caller supplied; out of scope.
11. `upload_file` read through a link (real base route) -> same as L1's mechanism; needs a live DOM snapshot to
    resolve the element handle; dropped in favour of install_extension for the "hand off" variant.
12. A second containment helper with a prefix-boundary bug -> rejected: the shared, correct check would still
    refuse on write paths, so it does not create a hole without also inventing a new sink.

Picks S1 and S2 beat the rest because they are the only candidates that are (a) real code a maintainer could
have left, (b) reachable through an existing non-page tool with no browser, (c) invisible to the published fix,
and (d) covered by the one general property without a sentence of their own.

## Check-patch verification (local, product tree swapped per variant)

Every check patch was applied to a fresh copy of the injected tree, built, and run against the hidden
suites before being listed in the manifest:

| variant | security | functional |
|---|---|---|
| oracle (solution/fix.patch) | 8/8 pass | 10/10 pass |
| pass-alt | 8/8 pass | 10/10 pass |
| pass-hardening | 8/8 pass | 10/10 pass |
| ff-overbroad | 8/8 pass (stricter) | 5 fail (new/absent outputs refused) |
| sf-miss-L1 | 1 fail (install hand-off) | 10/10 pass |
| sf-miss-L2 | 3 fail (both renamed writes + derived dangling) | 10/10 pass |
| sf-miss-L3 | 2 fail (supplied dangling + derived dangling) | 10/10 pass |
| sf-miss-S1 | 1 fail (reload hand-off) | 10/10 pass |
| sf-miss-S2 | 1 fail (summary cache read) | 10/10 pass |

The project test (`tests/utils/files.test.ts`, 7 cases) runs green on the pinned+injected and oracle
trees. It is copied from a pristine source at grade time and needs no browser.

## Things not built / out of scope
- Check-then-use races (a link swapped between the check and the write) are not addressed by any version of the
  fix; not tested.
- `roots === undefined` allowing every path is by design and is kept.
- Actual Chrome/puppeteer behaviour (heap-snapshot writer, screenshot writer) is represented by a stub at the
  browser boundary; the write itself is not the product logic under test.
