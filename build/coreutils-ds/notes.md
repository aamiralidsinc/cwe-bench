# coreutils-ds — build notes

started: 2026-10-18T19:33:36Z
ended: 2026-10-18T20:22:16Z

Gate (run one stage at a time):
- static: reports only the two downstream items (checks/blind.patch and FAIRNESS.md); everything
  else passes (metadata, agent layer, no instruction leaks, no hidden tests in the image,
  wrong-fix catalogue, hardening/alt pass patches).
- nop: PASSED — security 0/9 (all nine fail on the vulnerable code), functional 100/100
  (11 hidden + 89 project install tests).
- oracle: PASSED — three runs, reward 1.0 each, identical results.
- patches: PASSED — all checks behave as declared (blind.patch temporarily omitted from
  patch_checks because it is written downstream; the manifest was restored afterwards):
  sf-base 4 security failing, sf-target-dir 2, sf-dir-mode 2, sf-backup 1, sf-after-create 3,
  sf-crash 8, ff-overbroad 1 functional failing (security all pass), pass-hardening 1.0,
  pass-alt 1.0. All security_fail checks keep functional 100/100.

Track: injected. Pattern A+B. Pinned: 5dcdba102e2c4dc8ce83778b804ced06a3e9ac47 (verified
parent of the published fix 0c41299975f3c1e21cf5ca968d42cad55ceb42a1; the fetched pinned tree
is byte-identical to the screener tree at /home/mara/screen5/hosts/21068/repo). All work is in
this repository at that commit; nothing outside the advisory's protection was built on.

## Levers (one line each)

- L1 (A, reported landing): `install -D SRC DEST` — the leading directories are created with a
  path-based `create_dir_all`, which follows a symbolic link standing where a missing component
  must be created (install.rs:699 in the injected tree). Reason to dismiss: none; this is the site
  the report leads to. Security tests: four shapes (intermediate link, destination-directory link,
  relative path, link below an existing ancestor).
- L2 (A, far site / second implementation): `install -D -t DIR SRC` — creation of the target
  directory lives in a helper (install.rs:561) that calls `uucore::fs::create_dir_all_absolute`
  (uucore fs.rs:566). Reason to dismiss: -t names the directory explicitly, the copy never creates
  it, and the implementation is in the shared lower-level crate, not the reported function.
- L3 (B, real unmodified upstream): `install -d DIR` — directory mode still calls
  `fs::create_dir_all` at install.rs:485 and follows a link in the components it creates. Real
  upstream code at the pinned commit and still present at latest upstream. Reason to dismiss: the
  advisory says -D, -d writes no destination file, the code comment calls this create "safe", and
  the published fix only changed a cfg attribute in that function.
- L4 (injected sibling, different operation): `install -b SRC DEST` — `perform_backup` resolves the
  destination with `canonicalize` before renaming, so a symbolic link at the destination makes the
  rename move the file it points at (install.rs:847). Reason to dismiss: backup is a separate
  feature, the advisory is about directory creation, and the link is replaced afterwards anyway.

Injected only: L2's helper split and the uucore `create_dir_all_absolute` wrapper; L4's canonicalize
in `perform_backup`. L1 and L3 are unmodified upstream code. L4's function body is untouched by the
published fix's hunks.

## Verified

- Flaw reproduces deterministically through the CLI on the pinned+injected tree for every security
  test (9/9 fail), and every functional test passes (11/11) on that same tree.
- Reference fix: security 9/9 and functional 11/11 pass; the project's own 89 install integration
  tests and 20 safe_traversal unit tests pass at the injected commit and at the reference fix.
- Wrong-fix patches (all against the injected tree, validated by building and running the hidden
  tests locally): sf-base (4 security fail), sf-target-dir (2), sf-dir-mode (2), sf-backup (1),
  sf-after-create (3), sf-crash (8, refused by the panic assertion), ff-overbroad (security 9/9 but
  the legitimate symlinked-prefix functional test fails), pass-hardening and pass-alt (all pass).
  All security_fail variants keep the 89 project tests passing; ff-overbroad does too (its
  functional failure is the shared-helper over-blocking).
- Offline: the image fetches and compiles every locked crate, pre-builds the utility and the project
  test target, and installs nextest; grading runs with CARGO_NET_OFFLINE=1 and no network.
- The pinned commit does not contain the advisory's regression tests (the two symlink tests are
  added only by the fix diff; checked against the fix diff's test hunk).
- build/audit/uncovered-routes.tsv: one row appended for L3.

## The published fix's symlink semantics

The published fix replaces a pre-existing symlink found in the region it creates (its uucore tests
assert replacement); later upstream reversed that to follow pre-existing symlinks (GNU behaviour).
This task follows the advisory-era protection: a link in the creation region must not redirect
anything. The security tests accept both a clean refusal (reference fix) and replacement (pass-alt);
the functional tests keep links in the already-existing prefix working. Implementations that follow
the link into the creation region fail the security tests, as the instruction's invariant requires.

## Could not verify / guesses

- Real TOCTOU races are not tested: every security test uses a pre-existing link, which is the
  deterministic equivalent of the post-race state (and what the published regression tests use).
  The copy-helper path-based write and the post-copy metadata operations are only racy and were
  therefore not used as levers; the screener listed them as uncovered routes.
- The reference fix refuses a symlink in the creation region rather than replacing it; "replace"
  was validated as the second valid design (pass-alt).
- Timing of a full gate image build on the shared VM was not measured before building.
- `bug: parent_commit` in the screener record was null; the pinned hash came from pinned.txt and was
  confirmed to be the parent of the fix by the local fix.diff and tree comparison (the fix diff
  applies to this tree).

## Out of scope (noted, not built on)

- `mkdir -p` builds parents path-based in another utility; same mechanism, outside this advisory.

## v2 hardening + Frontier 1.4 conversion (2026-10-21)

Reason: both target models solved or nearly solved v1 (MiMo solved 1 of 3; DeepSeek 0 of 3 but two
8/9 runs). L1 and L4 were fixed by nearly every run, so they carried little difficulty. Two new
fair levers were added; the task was then converted to the Frontier 1.4 delivery format.

New levers (different kinds and reasons to dismiss):
- L5 (real unmodified upstream code, a route with no protection): an existing destination directory
  that is itself a symbolic link is resolved by path and the file is written at the link's target
  (`install -D SRC DIR`, `install SRC... DIR`, trailing-separator spelling). No directory is created,
  so the reported creation flow and the published fix never inspect this branch. The trailing
  separator is an input-shape trap: the kernel resolves the final link, so a naive final-component
  `lstat` does not see it unless the name is normalised. The same-file diagnostic that install
  already reports for this situation is preserved (the project's own `test_install_symlink_same_file`
  depends on it), which makes a blanket "refuse every symlinked directory" fix fail functionals.
- L6 (injected sibling on a separate write path): the loop copy used for `-t`, multiple sources and
  an existing destination directory takes an in-place overwrite fast path (`copy_over_existing`);
  that path uses `fs::copy`, which follows a symbolic link at the destination file name. The
  published fix gates its descriptor-anchored write on a single source and no `-t`, so this copy is
  untouched. Realistic as a maintainer's inode/ownership-preserving re-install optimisation.

Injected v2: `inject.patch` now also carries `copy_over_existing` and its call. L1-L4 are unchanged;
`fix.patch` extends the reference fix with L5/L6.

Local validation (containerised, before the gate):
- pinned+injected tree: 15/15 hidden security tests fail, 15/15 hidden functional and 89/89 project
  install tests pass.
- reference fix: 15/15 + 15/15 + 89/89 pass.
- checks: sf-base 4 security fail (L1), sf-target-dir 1 (L2), sf-dir-mode 2 (L3), sf-backup 1 (L4),
  sf-existing-dir 3 (L5), sf-loop-write 3 (L6), sf-after-create 3, sf-crash 8; every security_fail
  keeps functional + project green. ff-overbroad passes all security and fails the symlinked-prefix
  functional test. pass-alt (replace the directory link with a real directory; unlink a destination
  link before copying), pass-hardening (reference + backup entry hardening) and blind all score
  15/15 + 15/15 + 89/89.

Delivery format: `/workspace`, separate offline verifier via `artifacts`, uid-1000 non-root grading,
pytest + cargo-nextest groups, fresh git baseline, canary GUID.

Gate (2026-10-21/22):
- static: PASSED (conformance_check prints "conforming").
- nop: PASSED - 0/15 security, 104/104 functional (15 hidden + 89 project).
- oracle: PASSED - three runs, reward 1.0 each, identical results.
- patches: PASSED - all 12 checks as declared: sf-base 4 security fail, sf-target-dir 1,
  sf-dir-mode 2, sf-backup 1, sf-existing-dir 3 (L5), sf-loop-write 3 (L6), sf-after-create 3,
  sf-crash 8; every security_fail keeps functional green; ff-overbroad passes all security and
  fails the functional prefix test; pass-hardening, pass-alt and blind score 1.0.
Verdict in `harden_verdict.json`.

Verifier-image gotcha found during validation: a few crates (pin-utils) ship 0600 source files, so
the root-run `cargo fetch` left them unreadable to the uid-1000 verifier; both Dockerfiles now make
the cache world-readable and the cargo lock files writable.

Fairness notes: the "must keep working" bullet now says symbolic links in the *parent path* of an
existing destination directory keep working, so the legitimate symlinked-prefix case stays allowed
while the link that stands for the destination directory itself is covered by the security
property ("a symbolic link at a path component must not redirect the work"). No file, function or
route is named in `instruction.md`; the project's own visible tests keep the same-file behaviour
discoverable.
