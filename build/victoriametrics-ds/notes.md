# victoriametrics-ds — build notes

- Started (UTC): 2026-10-24T04:21:25Z (pipeline), design written 2026-10-24T04:26Z.
- Pattern: A+B. Track: injected. Advisory: GHSA-8Q3C-RJR9-XXRP / CVE-2026-61625 /
  GO-2026-6366 (VictoriaMetrics/VictoriaMetrics, CWE-22 path traversal leading to arbitrary
  file write: untrusted remote object names mapped to local paths).
- Pinned commit `0ceeb140763f1a3dbdd00476b6b9336e75038526` is the direct parent of the
  published fix `710c920d6083327042a309e449fae4383617d817` ("app/vmrestore: disallow restoring
  parts outside the configured -storageDataPath directory"). Verified with `git rev-parse
  <fix>^`. The fix adds `Part.IsLocalPathInsideDir` (common), an upfront loop over `srcParts`
  in `actions.Restore.Run`, and a `logger.Fatalf` assertion in `fslocal.NewDirectWriteCloser`,
  and a `common/part_test.go` regression test. The pinned image must not contain that test and
  does not (it is added by the fix commit).

## Seam for tests

The hidden tests are `package actions_test` Go tests staged into `lib/backup/actions/` at
grading time. They drive the real public orchestration APIs used by the shipped CLIs:
`actions.Restore.Run` (vmrestore) and `actions.RemoteBackupCopy.Run` (vmbackup with `-origin`
and no `-snapshotName`, i.e. a remote-to-local backup copy), with real `fslocal.FS` and
`fsremote.FS` sinks and a test-local `common.RemoteFS` source. The stub is faithful to the real
S3/GCS/Azure listers: it returns `common.Part` values whose `Path` came from an object name,
exactly what `ParseFromRemotePath` produces (it strips only a leading `/`). No product code is
used to compute an expectation or to clean up.

## General security property (written once, before routes)

No data carried by a backup source may cause this program to create, overwrite, truncate,
rename or delete any file or directory outside the local directory chosen for that operation;
an operation that would do so must fail with an error the caller can handle, and nothing outside
that directory may be created, changed or left behind. Names that resolve to a place inside the
directory keep working, including names containing `..` segments that stay inside, names that
merely begin with `..`, and absolute-looking names that `filepath.Join` keeps inside.

Every route and sibling below is covered by that sentence as written. The report names the
reported operation (vmrestore / -storageDataPath) for the observed impact and then states the
property over the outcome, without naming any other operation, source kind or data channel.

## Levers (each with a different reason a solver skips it)

- **T1 `containment-shape` — how-type, published helper semantics.** A plausible containment
  check is `strings.HasPrefix(p.LocalPath(dir), dir)` or `strings.Contains(p.Path, "..")`. The
  first lets a sibling whose name shares the directory's character prefix (`../storagefoo/x`)
  through; the second rejects legitimate in-directory `..` shapes (`..foo.txt`,
  `foo/../bar/file.dat`, `/inside.txt`). Reason to skip: the example (`../outside`) is caught by
  both naive forms, so the check looks done. Coupled must-keep-working: the legitimate shapes
  restore into the directory.
  Sites: `lib/backup/common/part.go:72` (LocalPath) and the published helper location;
  `lib/backup/actions/restore.go:94`.

- **T2 `preallocate-order` — how-type, ordering/side effect.** The restore pre-allocates a file
  before opening the writer (`actions/restore.go:184` then `:242`). A fix that guards only the
  write path (`fslocal.NewDirectWriteCloser`) refuses the write but has already created the
  destination's parent directories and the `.tmp` file outside the directory. Reason to skip:
  preallocation looks like space reservation, and the writer is where bytes are written.
  Coupled must-keep-working: preallocation + finalize still restore legitimate files (the
  existing `TestFSListPartsWithTrailingSlashInDir` project test also runs).
  Sites: `lib/backup/fslocal/fslocal.go:157` (PreallocateFile), `:131` (NewDirectWriteCloser),
  `:167` (FinalizeFile); `lib/backup/actions/restore.go:184`.

- **T3 `copy-route` — how-type, route where the protection never existed (real upstream).**
  `vmbackup -origin=<remote> -dst=fs://<dir>` with no snapshot performs
  `actions.RemoteBackupCopy.Run`; the origin's remote-listed object names are joined onto the
  local destination by `fsremote.FS.path` in `CopyPart`/`UploadPart` with no containment check.
  The published fix never touches `lib/backup/actions/copy.go`, `lib/backup/actions/backup.go`
  or `lib/backup/fsremote`. Reason to dismiss: the advisory is about vmrestore and
  `-storageDataPath`; a backup *destination* is a remote, and the origin looks like a
  neighbouring optimisation. Confirmed vulnerable at the pinned commit through the public API.
  Sites: `lib/backup/actions/backup.go:244-250,297` (copySrcParts/crossTypeCopy),
  `lib/backup/fsremote/fsremote.go:161-166,196-198` (UploadPart/path), `copy.go:35,44,56`.

- **T4 `excluded-paths` — how-type, producer off the check's path (injected sibling).**
  A backup may carry a plain excluded-paths list at its root; restore removes those paths from
  the destination after copying, so an operator can restore only a subset into a shared
  location. The list is read from the backup source and its entries go to `fslocal.DeletePath`
  on a path the part-name check never inspects. Reason to dismiss: the reported flaw is about
  part names; the list is a small restore convenience and its entries look like canonical
  relative names. Injected in `lib/backup/actions/restore.go` (`applyExcludedPaths`, called at
  the end of `Restore.Run`) so no new file or import block is added; the call is far from the
  published fix hunk.
  Sink: `lib/backup/fslocal/fslocal.go:213` (DeletePath). `DeletePath` is real upstream code
  with no containment check; the published fix does not touch it.

- **T5 `service-files` — how-type, producer off the check's path (injected sibling).**
  Backup metadata (a plain JSON file written by the backup action) records the service files a
  backup carries (retention-protection / restore marks). A remote backup copy replays them from
  the origin to the destination via `CreateFile`. The names come from the metadata content, not
  from a part listing, and land in `fsremote.CreateFile`, which joins them onto the local
  destination. Reason to dismiss: it is copy metadata plumbing, not part restoration; and the
  metadata is the tool's own file. Injected in `lib/backup/actions/copy.go` (metadata parse)
  and `lib/backup/actions/backup.go` (`storeMetadata` records what is present); the published
  fix never touches either file. Sink: `lib/backup/fsremote/fsremote.go:215` (CreateFile).

## Candidate sibling list (all found; picks are marked)

1. `fsremote.UploadPart` reached through cross-type copy (`actions/backup.go:297`) — REAL
   upstream, picked T3 (main). Behaves as described in the screener's O8-1.
2. `fslocal.PreallocateFile` / `FinalizeFile` reached through `Restore.Run` — REAL upstream,
   picked T2. Cannot be reached with a malicious part except through the action, so it is an
   ordering lever, not a separate route.
3. `fsremote.CopyPart` same-type route (`actions/backup.go:263`) — REAL upstream, NOT picked:
   the only same-type local origin is `fsremote`, whose `ListParts` walks a real directory, and
   walked relative paths can never contain `..`, so no attacker-controlled name reaches it.
4. `fslocal.DeletePath` driven by a remote manifest — injected, picked T4 (O8b-2).
5. `fsremote.CreateFile` driven by remote metadata content — injected, picked T5 (O8b-3).
6. `fsremote.DeleteFile` driven by the same service-file list — not picked: it is the delete
   twin of T5's single data path and adds no new reason to dismiss.
7. `Restore.Run` `pathsToDelete` — not a route: the paths come from a local directory walk, not
   from the backup source.
8. `fscommon` symlink following (a lexical check does not resolve symlinks already inside the
   destination) — NOT built: outside the advisory's own protection (the advisory and its fix are
   about `..` components in object names); noted as out of scope.
9. s3/gcs/az `CopyPart`/`UploadPart` with `../` in object keys — NOT built: writes land on the
   remote object store, not a local filesystem.
10. `actions.Backup.Run` with `-origin` and a snapshot — not a route: only origin parts that
    intersect the snapshot's own part keys are copied, so an origin name cannot introduce a new
    path.
11. `fslocal.NewReadCloser` / `fsremote.DownloadPart` traversal reads — outside the advisory
    (arbitrary file write), not built.
12. `fslocal.CleanupTmpFiles` / `RemoveEmptyDirs` — walk inside the configured directory; no
    source-supplied name reaches them.
13. `storeMetadata` / `RemoteBackupCopy.Run` `CreateFile`/`DeleteFile` with the fixed
    `backup_complete.ignore` / `backup_metadata.ignore` names — not a route (constant names).

Picks beat the rest because they are how-type (T3 protection never existed; T4/T5 producer on a
separate data path), far from the reported site (T3 another app/package; T5 another action),
and each has a distinct dismissal reason (neighbouring feature / it is only a manifest /
it is metadata plumbing).

## Input shapes covered by security tests

- leading `../` (`../outside/marker.txt`)
- mid-path traversal (`a/../../outside/marker.txt`)
- prefix-sharing sibling (`../storagefoo/evil.txt` vs `/…/storage`)
- the same three shapes through the remote-copy destination (`../backupfoo/evil.txt`)
- a manifest entry that is `../…`
- a metadata service-file name that is `../…`
- side-effect assertion on the parent directory and the `.tmp` file (T2)

Legitimate shapes kept working by functional tests: `parts/a.bin`, `..foo.txt`,
`foo/../bar/file.dat`, `/leading.txt`, trailing slash in the directory, a directory containing
`..` components, the normal incremental delete of a destination file absent from the source,
legitimate preallocation, and ordinary remote-copy parts / service files.

## Gate (run 2026-10-24)

- static: PASSED (no leaks, no exact-status assertions, hardening + blind pass patches declared,
  wrong-fix catalogue complete; `blind-fix.patch` and FAIRNESS.md are produced later by the
  pipeline, not here).
- nop: PASSED — security 0/8, functional 8/8 (7 hidden feature tests + the project's own
  `TestFSListPartsWithTrailingSlashInDir`). Trial:
  `victoriametrics-ds-nop-1792816905/victoriametrics-ds__wqoYcLn`.
- oracle: PASSED — three strict runs, each reward 1.0, identical security/functional maps.
  Trials: `-oracle1-1792817724`, `-oracle2-1792817902`, `-oracle3-1792818135`.
- patches: PASSED — all 10 check patches matched their declared expectation:
  `sf-no-copy-upload` (2 security fail), `sf-no-copy-createfile` (1), `sf-no-deletepath` (1),
  `sf-writer-only` (4), `sf-prefix-check` (2), `sf-read-only` (8), `ff-overbroad` (1 functional
  fail), `ff-refuse-all` (7 functional fail), `pass-alternative` (reward 1.0),
  `pass-hardening` (reward 1.0); every security_fail left functional green.
  The last `--only patches` run passed; the earlier attempts were cut by infrastructure, not
  by the task: a 90-minute background-command cap during Harbor artifact collection (9/10
  verified), then a host Docker daemon deadlock (operator pause), then one
  `network_mode` egress-probe timeout after five green checks (known shared-VM flake), then a
  probe-gated retry that passed. `retry-patches.sh` in this directory is the retry driver.
- Host-side score simulation with the real score.py: oracle 8/8 + 8/8 = reward 1.0;
  injected tree 0/8 + 8/8 = reward 0.0. A Go build failure produces a JUnit error element
  (go-junit-report `[build failed]`), so a broken submission scores 0 rather than a verifier
  error.

- End (UTC): 2026-10-24T09:12Z. Final separate `--only static` re-run after the last
  instruction edit: PASSED.

## Design changes during build

- The excluded-paths helper was first a new file; the static gate rejected the resulting
  injection patch because its import block shared three distinctive lines with the hidden
  tests. The helper and its constant now live in `restore.go` / `backupnames`, and the only new
  import in the injection is `"strings"` (below the leak threshold). Re-verified: 0 shared lines.
