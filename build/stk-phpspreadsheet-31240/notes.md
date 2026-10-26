# stk-phpspreadsheet-31240 — build notes

start_utc: 2026-10-26T12:27:09Z (build job start)
end_utc: (filled at the end)

## Stack

Single advisory, H4. Pinned commit `0577c74889e080c088e5af4585f3d71db9467804` is the parent of the
published fix `85f2556b0bf5269061bf45932ecda8a128d81750` (GHSA-2MRG-GJXQ-2GVR / CVE-2026-59932),
so the pin is exactly the commit before the fix. The published fix does two things: it bounds the
decoded size of a gzip-compressed `.gnumeric`, and it adds a per-chain visited-block set to the
four sector-chain walks in `Shared\OLERead` (reset before each chain).

Concepts (reference-fix edit sites): 4 — Gnumeric decompression bound `[T1]`; the four OLERead
chain walks `[T3,T4,T5,T6]`; the second container implementation `[T7]`; the archive-entry reads in
the zip-based readers `[T9]`.

## Levers (one line each)

- T1 (advisory route; both/easy): a gzip `.gnumeric` is inflated with no decoded-size bound;
  `gzdecode()` is the only decompression in the format reader and all four entry points funnel
  through it. `Reader/Gnumeric.php:195`. No reason to dismiss — it anchors the report.
- T3 (advisory route; both/hard): the SSAT chain walk in `OLERead::read` revisits a block forever.
  `Shared/OLERead.php:140`. Reason to dismiss: the report shows a Gnumeric gzip; this is the XLS
  container and has no gzip code.
- T4/T5/T6 (published-fix far sites; both/hard): the small-stream, big-stream and directory chain
  walks in the same file (`OLERead.php:175,198,218`). Reasons to dismiss: the small-stream chain is
  only reached after `read()` returns; the big-stream loop looks size-bounded because a block count
  is computed above it; `readData()` looks like it inherits whatever the other walkers get.
- T7 (uncovered upstream; deepseek/hard): a second implementation of the same sector-chain walk in
  the publicly exposed container class, with no guard. `Shared/OLE/ChainedBlockStream.php:78,87`;
  fixture drives `Shared\OLE::read`. Reason to dismiss: no Reader calls this class; only the XLS
  writer and a date helper use it, so it reads as legacy write-side code.
- T9 (uncovered upstream; deepseek/hard): a second decompression implementation — archive entries
  are pulled whole with no uncompressed-size bound. `Reader/Xlsx.php:415`, `Reader/Ods.php:322`.
  Reason to dismiss: a different container and compression primitive (libzip, not zlib gzip),
  which the advisory never names, and the readers pull whole entries so large legitimate parts
  survive.

Coupled must-keep-working for the OLERead group: `readData()` is re-walked for every small stream
and several streams are extracted from one container instance, so the visited set must be reset
before each chain. The naive file-global set breaks ordinary workbooks; `ff_global_visited.patch`
proves the functional suite catches it. The report covers this only through the general
keep-working sentence.

## Verified

- Fixtures generated locally; pinned-tree behaviour reproduced for every route before tests were
  written (each in a memory-capped, time-limited child process):
  - gzip bomb -> fatal memory exhaustion at `Gnumeric.php:195` through canRead/list/load;
  - SSAT, directory, small-stream and big-stream chain cycles -> fatal memory exhaustion in the
    four `OLERead` walks;
  - cyclic block chain -> fatal memory exhaustion in `ChainedBlockStream`;
  - (zip bombs verified inside the image — see below).
- Suites run with the project's own PHPUnit 10.5.63 and Composer tree.
- Results recorded below (filled after the gate).

## Could not verify / unknowns

- The advisory body was not supplied. The mapping of the OLERead hunks to CVE-2026-59932 comes from
  the screener record, not from an advisory text I read.
- `present_in_latest` for T7/T9 is recorded from a read of current upstream if reachable; otherwise
  `unknown`.
- The project's full test suite was not run (it is large); only the Shared area tests and the
  hidden suites.

## Fairness concerns I see myself

- The OLERead group's natural over-fix (a file-global visited set) breaks reading several streams
  from one container instance. This is discoverable from the code (readData() is called from
  read() and again for every small stream; loadOLE() extracts three streams) and is covered only
  by the general keep-working sentence, as the stacked rules require.
- T7's hidden test drives `Shared\OLE::read`, a public API that no Reader calls. The project's own
  OLETest exercises the same class the same way, and the report's property covers it, but a
  reviewer may still see it as outside the reported surface.
- The gzip bound must leave headroom: at the security probe's 64 MB limit, a decoded-size cap of
  memory_limit/4 (the published fix) and memory_limit/2 both refuse the bomb without exhausting
  memory; a cap equal to memory_limit does not. The report's refusal contract says a process killed
  for lack of memory is not a refusal, so this is stated behaviour rather than a trap.
- The zip-entry bound is exercised on `meta.xml` (ODS) and a worksheet part (XLSX); a fix that
  caps only the entry the reader parses first would miss one of the two. The property covers every
  entry, but this is the closest thing to a spelling variant that the task contains.

## Outside the advisory's own scope (not built on)

- `File::fileExists()` inflates an archive member to test for its presence, so a bomb placed in the
  member it probes (`content.xml` for ODS, `_rels/.rels` for XLSX) would still be inflated there.
  This shared helper is a neighbouring route, not one of the built levers; the reference fix does
  not depend on it and no hidden test drives it.
