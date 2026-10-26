# composer-symlink-path-inj — build notes

- Start UTC: 2026-10-18T10:07:06Z
- End UTC:   2026-10-18T10:30:00Z (approx; gate run follows)

## What this is
composer/composer, GHSA-96H3-5X6V-M776 / CVE-2026-59944 (CWE-22/59/732). A dependency's declared
binary that resolves OUTSIDE its own package install directory (via `..` metadata or an in-package
symlink pointing out) gets chmod'd / proxied — a hostile dependency flips the permissions of an
arbitrary host file during `install`/`update`/`reinstall`. Pinned `24e396b5` is the verified parent
of fix `53b8bb4c`. Track INJECTED, pattern A+B.

## Levers (one line each)
- L1 (A, base/report): BinaryInstaller::installBinaries, in-package bin that is a symlink escaping the
  package. src/Composer/Installer/BinaryInstaller.php:103. Dismiss: the obvious landing point.
- L2 (A, input-shape): same sink, `..` metadata STRING reaching via reinstall/installed.json (skips the
  solver-time validator). Dismiss: "the `..` validator already covers this".
- L3 (A, far site): FileDownloader::install single-file chmod loop. FileDownloader.php:368. Dismiss:
  lower download layer, single-file dists only, "can't be a symlink", `..` looks already rejected.
- S1 (injected): new BinaryInstaller::ensureBinariesExecutable (exec-bit refresh loop, no containment),
  wired into LibraryInstaller::ensureBinariesPresence. BinaryInstaller.php:144. Dismiss: refresh path
  "just delegates to the guarded installer".
- S2 (injected): new FileDownloader::ensureBinariesExecutable, wired into PathDownloader::install.
  FileDownloader.php:385. Dismiss: local path-repository = trusted source, symlinks expected there.

## Verified
- Pinned == parent of fix (git). Pinned copy HAS tests/; the advisory's own regression tests are NOT
  present at the pinned commit (they land only in the fix commit).
- Project area tests pass at pinned+injection: BinaryInstallerTest 4/4, FileDownloaderTest 9/9.
- Fast harness (apply each candidate fix in the injected image, run the hidden tests):
  - nop: 5/5 security FAIL, functional all pass.
  - oracle: all pass.
  - each sf-miss-{L1,L2,L3,S1,S2}: exactly 1 security test fails, functional all pass.
  - ff-overbroad (reject all symlinked bins): security all pass, 1 functional fail (in-package symlink).
  - pass-hardening, pass-alt: all pass.
- Offline: PHPUnit cache warmed at build (`vendor/bin/.phpunit`); `--network none` run green.

## Could not verify
- Target-model trials (DeepSeek V4.1 Flash, MiMo-V2.6-Pro) are run downstream, not here.
- `present_in_latest` for the injected siblings: they are our-copy-only code, so n/a (recorded `no`).

## Out of scope (one line)
- Root-package bins are resolved in EventDispatcher (root is trusted); the check-then-chmod window is a
  possible race — neither pursued, both outside this advisory.

## Pattern B register
Two rows appended to build/audit/uncovered-routes.tsv for the injected siblings S1 and S2
(real_upstream = no; injected, our copy only).
