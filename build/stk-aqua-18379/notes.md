# stk-aqua-18379 — build notes

Start (UTC): 2026-10-26T02:21:49Z (pipeline start; this session continued it)
End (UTC): 2026-10-26T03:54Z (build session; the pipeline postbuild gate runs separately)

Task: aquaproj/aqua, GHSA-MF5C-HW34-4HPP / CVE-2026-55569, pinned
d6b9448fc421c58d83ae2fa372e61122f14620f5 (verified `git rev-parse d5b02b22^` ==
d6b9448f). Fix commit d5b02b220188de376a661b3aabfa912202a1a59a. Pattern A+B, stacked,
H4. 3 concepts, 4 manifest traps (T1, T3, T2, T4) plus the injected T7, 6 security tests,
7 security tests (one of them the ordering shape), 5 hidden functional tests, 2 project tests.

## Levers (one line each)

- T1/T3 — concept 1, entry-name containment. `pkg/unarchive/archives.go:26-30`: the
  destination is `filepath.Join(dest, normalizePath(NameInArchive))` and is used with no
  containment decision. The guard has to be on the joined/cleaned path (the backslash
  shape and a sibling named `dest-*` both defeat a raw-name or bare-prefix check).
  The check must run before the first outside effect: an entry `../newdir/evil` must not leave
  the outside parent directory behind even when the write is refused. Reason to dismiss:
  `filepath.Join` already normalises `..`, so the raw name looks safe.
- T2/T4 — concept 2, link-target containment. `pkg/unarchive/archives.go:41-52`: a symlink
  entry's target is created verbatim (absolute and relative both escape), and a later
  entry at the same path is written through it. Relative targets must resolve against the
  link's own directory, and dangling in-destination targets must keep being created.
  Reason to dismiss: packages legitimately ship relative/dangling links
  (`libfoo.so.1 -> libfoo.so.1.2.3`).
- T7 — concept 3, hard-link target containment (injected sibling). In
  `pkg/unarchive/archives.go:48-54`: hard-link entries are created with their target
  resolved from the archive root. A guard that reuses the symlink-relative rule leaves a
  nested link (`sub/h -> ../outside/target`) escaping. Reason to dismiss: the link target
  is an archive-internal name and the entry's own path is already contained.
- T5 (screener, dropped): `pkg/unarchive/dmg.go:56` `osfile.Copy`. otiai10/copy v1.14.1
  defaults a symlink to `Shallow` (recreate the link), so the mounted-volume copy does not
  itself write outside dest. No outside write reproduced; not built.
- T6 (screener, dropped): `pkg/unarchive/pkg.go:32` delegates expansion to
  `pkgutil --expand-full` (macOS, unavailable offline). No in-repo path decision exists and
  a fake executor would only test the fake; not built.
- T8 (screener, dropped): `archives.go:129` joins `filepath.Base(src.Filename)` minus its
  extension; it cannot escape dest. Not a usable route.

## What was verified

- Every built route reproduces on the pinned+injected tree through the public
  `unarchive.New(...).Unarchive(...)` entry point: forward-slash and backslash entry names,
  the `dest-*` sibling shape, absolute and relative symlink targets, and the nested
  hard-link target. Each wrote the outside sentinel and returned nil; the ordering shape
  creates the outside parent directory before the write.
- The reference fix closes all six security tests and keeps all five functional tests
  (nested/dot-prefixed names, Windows backslash names, relative dangling symlink, absolute
  in-destination symlink, in-package hard link).
- Wrong-fix matrix (local, Go 1.27.2): see manifest `verified.local_runs`; each miss patch
  fails only its concept's security tests and leaves functional green; `upstream_fix`
  fails only the hard-link test; the two pass patches score 1.0.
- Project tests: `TestIsUnarchived` and the offline `TestUnarchiver_Unarchive/raw` subtest
  pass on the pinned tree, the reference fix and the published-fix-only tree. The upstream
  file's other two cases download fixtures over the network and are excluded.
- `patch -p1` applies the injection, the reference fix and every check patch to a fresh
  checkout of the pinned commit (dry run).
- Static gate and stacked conformance (`check_stack.py`): see below.

## What could not be verified

- The GHSA text was not fetched; the published fix's source diff was read from the fix
  commit and its regression tests are absent from the pinned tree (checked: no
  `TestUnarchiver_Unarchive_*Traversal` in the pinned tree).
- DMG/PKG routes were not run on macOS; see T5/T6 above.
- The reader record referenced by the build prompt as `pipelines/stacking/out/reader/`
  exists on disk at `pipelines/stacking/out/reader-ds/h4-18379.json`; the manifest points
  at the existing path.
- `repo_mb` was not measured (repo checkout is ~7.3 MB; the module cache lives outside
  the tree).

## Fairness notes

- The backslash entry shape is not an encoding variant of a stated input: the product
  deliberately rewrites backslashes in `normalizePath` before joining, so a guard on the
  raw name is decided on a different value than the one used. A legitimate Windows-written
  archive keeps extracting (functional test), so the shape does not punish an over-broad
  ban alone.
- The instruction states that an escaping asset is refused with an error. A
  skip-and-continue design would satisfy "no outside effect" but not that stated contract;
  this is deliberate and matches the library's error-returning API.
- T7 is an injected sibling (source = mined+injected). It is plain code a maintainer could
  have written, reachable through the real entry point, and covered only by the general
  property. The published fix's recall check is rebased onto the injected tree so it keeps
  the hard-link branch, and it still fails.
- The two core concepts (entry and symlink containment) are what upstream fixed; the
  stack's extra reach beyond upstream is the hard-link concept. This is recorded rather
  than hidden: the reader's T5/T6 were not built because they could not be reproduced or
  fixed in-repo.

## Gate results

Static (stacked): PASS. `check_stack.py`: conforming (3 concepts, pattern H4).
Static (control): PASS.

Container stage history on the shared VM (2026-10-26; load average 60-150 from other
agents' concurrent builds):
- attempt 1 (02:35-03:00 UTC): `docker compose build` sat idle in the classic builder's
  queue for ~25 min with no containers; stopped.
- attempt 2 (03:08): infra `RuntimeError [disk full]` — the daemon could not create
  `/tmp/containerd-mount...` (host /tmp tmpfs exhausted at that moment). Not a task
  failure; the local verification is unaffected.
- attempt 3 (03:29-): the classic builder stalled again; a scratch BuildKit build
  succeeded instantly, so this stage was rerun with `DOCKER_BUILDKIT=1`
  (`COMPOSE_DOCKER_CLI_BUILD=1`); the environment image built and the trial reached Harbor's artifact
  collection (before the verifier).

Container result: NOT PROVEN in-session. Four attempts:
- 03:29-03:42 (BuildKit): environment image built; the trial reached artifact collection, but the
  main container was already gone and Harbor's `docker inspect` of the built image returned 1 (the
  daemon's image/container API was wedged); the collection deadlocked.
- 03:45-03:50 (BuildKit, cached image): same deadlock at artifact collection.
The shared daemon showed 16+ concurrent stuck `docker run alpine` Harbor kernel probes from other
agents, and `/images/json` timed out while `/version` answered. `gate.py` classified every failure
as infra. No task assertion failed at any point; the local matrix above is the behavioural proof.
The pipeline postbuild gate retries infra failures (MAX_INFRA=4), and the images are now cached in
the BuildKit cache, so it should complete when the daemon is free.

Final static re-checks after the last edits: stacked static PASS, check_stack conforming (3
concepts, H4), control static PASS.
