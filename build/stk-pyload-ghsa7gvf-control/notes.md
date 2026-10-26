# stk-pyload-ghsa7gvf-control — build notes

- Start (UTC): 2026-10-23T08:20Z; end (UTC): 2026-10-23T08:48Z.
- Purpose: the same pinned tree (6176863f1348) and the same instruction.md as
  `stk-pyload-ghsa7gvf`, with only the advisory's own route (the download of a user-supplied
  link) in the security suite and upstream's first fix (b76b6d4ee5e3) as the reference.
- Security suite: four non-public destinations on that one route (127.0.0.1, `localhost`,
  127.0.0.2, `::1`), each driven through the API add-package + downloader plugin lifecycle.
  Each case uses its own package name; the product otherwise deduplicates same-named packages
  and later cases pass vacuously.
- Functional group: the same five legitimate-fetch tests plus the project's two pristine test
  files (8 tests).
- Checks: `sf-unrelated-edit.patch` (a comment-only edit; all four security tests fail with
  functional passing), `ff-refuse-all.patch` (three functional failures), `pass-hardening.patch`
  (upstream's fix with a fail-closed empty resolution; reward 1.0).
- Gate, run in this session: static PASSED; nop PASSED (security 0/4, functional 8/8); oracle
  PASSED (three runs, each reward 1.0, 12/12); patches PASSED (all three behaved as declared).
