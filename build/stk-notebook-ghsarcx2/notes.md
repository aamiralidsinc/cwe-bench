# stk-notebook-ghsarcx2 build notes

Start (UTC): 2026-10-26T12:21Z
End (UTC): <filled after the gate>

## Design

Stacked (H3b1), three independent concepts on jupyter/notebook at
`b9d9e659e9b2edd70767129c06ac76761e046791`.

- **T1 — login redirect destination (MiMo-type, advisory route).** Pattern: shape trap (how-type).
  `notebook/auth/login.py:42-59`. The pinned check parses the value and reasons about the parsed
  path; a browser resolves the raw string. `///host` parses to an empty netloc with an in-prefix
  path, and a backslash is read as a slash. Reason to dismiss: the A fix already parses the target
  and rejects a netloc, so a value that looks like an in-tree link seems covered.
- **T2 — directory redirect (DeepSeek-type, uncovered upstream).** Pattern: route where the
  protection never existed. `notebook/base/handlers.py:858-867`. `TrailingSlashHandler` copies the
  origin-form request target into `Location` after stripping a trailing slash, so `//host/dir/`
  becomes a scheme-relative redirect. Reason to dismiss: `request.uri` is expected to start with
  `/`, the handler only trims a slash, and the route is unauthenticated, so it does not look like
  part of the redirect-trust path. Present in the pinned tree, untouched by every published fix
  commit for the two advisories; closed by a separate later advisory (GHSA-c7vm-f5p4-8fqh, 6.1.5,
  2020-11-18, commit 1abd95130).
- **T3 — configured landing address (DeepSeek-type, injection room).** Pattern: stored value that
  passes a prefix test. `notebook/notebookapp.py:1393-1395` together with `:1740`. `default_url`
  is rebased only when it does not start with `base_url`, so with `base_url='/'` a scheme-relative
  value is stored and mounted as the root redirect; the same stored value is sliced by `base_url`
  for the browser-open page. Reason to dismiss: an operator-only trait, and the prefix test looks
  like it keeps the value in-tree.

Reference fix: `solution/fix.patch` applies the complete upstream login fix (A plus B: authority-
free rendering comparison, backslash escaping, same-origin/CORS allowance) and adds target
validation at the trailing-slash redirect and a parse-and-rebase of the landing address.

## Verified

- Reproduced on the pinned tree through the real `NotebookApp` HTTP entry point: T1 (both shapes),
  T2 (both shapes), T3 (both shapes); full evidence in the manifest `verified.reproduced_on_pinned`.
- Project test `notebook/auth/tests/test_login.py` passes at the pinned commit in the image (2
  tests) and on the restored tree in the verifier.
- Local suites, one image: pinned 6/6 security fail, 10/10 functional pass (8 hidden + 2 project);
  reference 16/16 pass. Miss patches leave exactly their concept failing with functional passing.
  `upstream_first_fix` (remaining A commit) leaves 5 security failing; `upstream_fix` (A+B) leaves
  4 (T2, T3). `unlisted_route`/`check_after_adjustment`/`crash_as_refusal` security_fail;
  `refuse_all` functional_fail; `hardening` and `alternative` 16/16.
- Every `checks/*.patch` applies cleanly to the pinned tree with `patch -p1`.
- Register row added for T2 in `build/audit/uncovered-routes.tsv`.

## Could not verify

- The advisory text and any proof of concept for GHSA-rv62-4pmj-xw6h / GHSA-rcx2-m7jp-p9wj were not
  read; the tested shapes come from the pinned code, the published fix diffs and standard browser
  URL resolution (WHATWG special-authority slash/backslash handling).
- Whether the hidden tests match the shape of any future upstream regression test for T2; the
  upstream 6.1.5 fix trims leading and trailing slashes, a different but compatible approach.

## Deviation recorded

The build prompt and the reader record pin `b9d9e65`, which is A's first published fix commit
("parse urls when validating redirect targets"), not its parent. The pinned tree therefore already
contains A's core guard; B is the later completion. `checks/upstream_first_fix.patch` adds the
remaining published A commit (the backslash guard) on top of this state, and
`checks/upstream_fix.patch` adds A and B. Both are expected to fail, as recorded.

## Scope

Everything stayed inside this advisory, this repository and the pinned commit. No other component
was examined or built on.
