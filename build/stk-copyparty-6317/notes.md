# stk-copyparty-6317 build notes

- Start: 2026-10-26T02:19Z
- End: 2026-10-26T05:05Z (stacked gate green: static, nop, oracle, patches; control static, nop, oracle green; control patches locally 6/6, container stage retried after a shared-VM egress-probe infra flake)
- Pinned (vulnerable) commit: `89040874f53e426e54a94787a3e3ddfa2acd1bad`; published fix
  `e40755331ba9449993ff482456e6bdd2c6deb950` (verified as the direct child of the pinned
  commit). The published diff is one line in the browser listing emitter: no folder key when a
  file key authorized the request. No regression test for the advisory exists in the pinned tree.
- Advisory: GHSA-x5pq-m9p8-f4vx, CWE-863: a valid filekey can be converted into a dirkey for the
  containing folder. Never named in `instruction.md`.

## Levers (one line each)

- T1 (advisory route, type both): a valid per-file key plus the viewer query makes the browser
  listing emitter mint the containing folder's key; `copyparty/httpcli.py:7207-7215` with the
  `?v` rewrite at `6932-6962`. Fixed by a folder-access predicate, not by the published
  one-liner alone.
- T2 (DeepSeek-type, uncovered): the documented index.html exemption for html permission sets
  `fk_pass` and leaves `add_og` set, so a keyless file request reaches the same emitter;
  `copyparty/httpcli.py:6932-6962`.
- T3 (DeepSeek-type, uncovered): a get-only caller on a `dks` volume without file keys fetches a
  named file with the viewer query and receives the folder key; `copyparty/httpcli.py:6851-6853,
  6942-6962`.
- T4 (DeepSeek-type, injection room): every share node copies the source volume's flags, so a
  single-file share page carries the source folder's key; `copyparty/authsrv.py:3166-3181`.
- T6 (DeepSeek-type, uncovered, how-type): the multipart archive selection validates the request
  folder's key but passes the caller's item list straight to the archive builder, so a
  subfolder-free folder key reaches subfolder contents; `copyparty/httpcli.py:2953-2970`.
- T5 (MiMo-type, coupled): a folder-key recipient keeps its per-file links and its subfolder
  links, and a file-key holder keeps its page; `copyparty/httpcli.py:7293-7308,7671-7684`.
- Reference fix: folder-access predicate at the emitter; strip folder-key flags from single-file
  share nodes only; refuse an archive selection that names anything outside a subfolder-free
  folder's own files. `solution/fix.patch`.

## Verified

- Each attack (T1, T2, T3, T4, T6) reproduced on the pinned tree with the product's own
  socket-level harness (`tests/util.py` `VHttpConn` + `HttpCli.run`, i.e. the real request parser
  and dispatcher), and each is closed by `solution/fix.patch`.
- The functional values (T5 plus the coupled value of each hidden route) pass on the pinned tree,
  on the reference and on every declared pass patch: folder-key listing with per-file and
  subfolder links, file-key viewer, keyless index.html, get-only named download, folder-share
  subfolder navigation, archive selection of visible files, read-caller subfolder archive,
  subfolder-enabled folder archive, and the project's own `tests/test_dots.py::TestDots::test_dk_fk`.
- Local patch matrix (same harness; `SEC` counts security tests passing out of 6, `FUN` hidden
  functional out of 8, `PRJ` the project case):
  - nop 0/6, 8/8, 1/1
  - reference 6/6, 8/8, 1/1
  - upstream_fix (published one-liner alone) 1/6, 8/8, 1/1 -> recall check fails as required
  - miss_emitter 3/6; miss_share 5/6; miss_zip 4/6 (functional 8/8 each)
  - sf-crash 4/6; sf-filekey-authorizes 5/6; sf-keyless-open 4/6; sf-index-open 5/6 (functional 8/8)
  - ff-refuse-dirkey 6/6, functional 8/9; ff-adjacent 6/6, functional 8/9
  - pass-alt 6/6, 8/8, 1/1; pass-hardening 6/6, 8/8, 1/1
- Control task `stk-copyparty-6317-control`: same pinned tree and byte-identical report; its
  security suite is four cases of the advisory's own route only and its reference is the
  published one-liner. Local matrix: nop 0/4 + 8/8 + 1/1; oracle 4/4 + 8/8 + 1/1;
  sf-filekey-authorizes 0/4; ff-refuse-dirkey and ff-adjacent functional 8/9; pass-alt and
  pass-hardening 4/4 + 8/8 + 1/1.

## Could not verify / not built

- The reader's subvolume exposure (`copyparty/authsrv.py:786-803`) was probed directly: a
  configured subvolume has `dbv None`, so the `vn2.dbv == dbv` shortcut never matches and the
  subvolume's key is never minted for a caller without access to it in the configurations tried.
  Not used as a lever.
- The search backend (`copyparty/u2idx.py`) does not expose share volumes (`aread` excludes
  paths under the share root when sharing is enabled), so the share-source search leak is closed
  by design at the pinned commit. Not used.
- The file-key echo into the opengraph thumbnail/raw links (T5 evidence) was not exercised
  functionally: the in-process harness has no thumbnail service. The template is untouched and
  the two tested coupled values catch the same over-hardening rule.
- Outside this advisory's published fix, one line: later upstream commits fix related key-feature
  issues (GHSA-mc69-pxc8-4xf4 archive scope, GHSA-3c88-p299-7hvr shadowing, GHSA-hg99-jqfp-rf76
  xvol/xdev, constant-time key compare). Only the archive-scope route is built (T6), because it
  is literally within the task's stated capability-scope property and it is unmodified code at
  the pinned commit; the others are not built.
