# microceph-ds build notes

Start (UTC): 2026-10-24T04:20:52Z (pipeline start)
Build work start (UTC): 2026-10-24T04:20Z
Build work end (UTC): 2026-10-24T08:53Z
Gate: static PASS, nop PASS (16 security failing / 59 functional passing), oracle PASS (3 runs,
reward 1.0, identical), patches PASS (11/11). See gate-summary.md.

Project: canonical/microceph at 2688eaec23a0e6a0dd8c40de78b58c4732f7c252
Published fix: 5c2760d8fb765d670e2673d3a537b67eae4b67c6 (GHSA-XG3J-C7Q4-F9PH / CVE-2026-10720 / GO-2026-5755)
Pattern: A, track: injected. Slug: microceph-ds.

## One line per lever

- T1 (how-type; producer off the check's path): a remote name recorded by an earlier request is
  read back from the database by the replication-enable flow and becomes the mirror peer token
  file name (`microceph/ceph/rbd_mirror.go:708`); fixing the import handler never sees it.
- T2 (published-fix far site + injected sibling): the re-render route
  (`microceph/api/remote_refresh.go:35`, injected) hands its path name to the shared config/keyring
  writer (`microceph/ceph/configwriter.go:28`), which the import flow also uses.
- T3 (published-fix far site + injected sibling): the bulk-removal route
  (`microceph/api/remote_refresh.go:60`, injected) passes body names to the database removal helper
  (`microceph/database/remote_extras.go:71`).
- T4 (shape): a charset-valid name equal to a file base name the local cluster owns (`ceph`,
  `radosgw`) passes a containment/alphabet check and overwrites or deletes the local file
  (`microceph/api/remote.go:47`, `:105`).
- T5 (wrong object): the request path names one remote and the body another; the handler acts on
  the body (`microceph/api/remote.go:47`).
- T6 (shape): the existing `^[a-z0-9]+$` regex accepts any length; the 63-character bound is in the
  shared validator (`microceph/constants/constants.go:92`).

## What I verified

- At the pinned commit, each security path was reproduced through the registered handler with the
  real request plumbing, a temp snap-style state directory (SNAP_DATA/SNAP_COMMON/current), and
  stubs only for the database, the external command runner and the stored-remote read:
  import, single removal, re-render, bulk removal, replication enable (stored name).
- Every security test fails on the pinned+injected tree and passes on the oracle tree; every
  functional test passes on both.
- Each `miss-*` patch fails only its lever's security test(s) and keeps all functional tests
  passing. `refresh`/`bulk` siblings are blocked by the published fix's far sites (shared writer /
  database helper), so they are genuinely required by the tests.
- `pass-alt` is an independent design (a non-regex validator in `constants` called from the sinks)
  and scores 1.0; `pass-hardening` adds redundant guards and scores 1.0.
- The remote lookup in the tests is a real in-memory SQLite database with the product schema and
  prepared statements, seeded with the stored record, not a stub of the lookup helper. A fix that
  validates inside the lookup helper itself also scores 1.0 (checked with a throwaway variant), so
  the stored-name lever accepts a correct fix at any valid layer.
- `go build ./...` and the project's own affected tests (api disks, ceph configwriter, ceph
  rbd_mirror) pass at the pinned commit and on the oracle tree, as uid 1000, offline.
- The shipped verifier image and test.sh were exercised end to end locally in separate-mode
  style (workspace extracted from the agent image, tests mounted at /tests): pinned+injected gave
  reward 0.0 with all 16 security test cases failing and all 59 functional cases passing; the
  oracle gave 1.0; a single-lever miss (miss-token) gave 0.9375 with only that security case
  failing and functional intact.
- Compatibility note: `microcluster` v3.0.2's Go bindings need a dqlite with the snapshot
  trailing-strategy constants; Debian trixie's 1.18.1 lacks them, so both images build
  canonical/dqlite v1.18.7 from source (same as the project's snap recipe, newer tag).

## What I could not verify

- Repo size in MB (not measured).
- Whether the rbd/ceph CLI resolves `--cluster <name>` to `ConfPath/<name>.conf` in the snap; not
  needed by any test.
- The published fix's GET-name guard and cluster-export length refactor are included in the oracle
  (defence in depth) but are not behaviourally exercised: neither reaches a file sink, so there is
  no side effect to assert. The property is stated so that they are covered if a solver guards them.

## Siblings considered but not taken

- `peerBootstrapImport` builds a token path from a stored name and hands it to the rbd CLI (read
  only, external process): outside a property about creating/replacing/removing files.
- cephfs replication passes the stored name as `--cluster` to an external CLI (not a file the
  product opens).
- adopt/bootstrap temporary file names use constants only, so a sibling there would need a new
  user-supplied name source; rejected as less plausible than the two remote routes chosen.
- service placement symlink names come from the service registry and cluster state, not a request.

## Pattern B register

No Pattern B register row: this task is Pattern A plus injected siblings. The only real upstream
routes used are sites the published fix itself protects (covered by the oracle), not uncovered
upstream routes.
