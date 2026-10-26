# stk-go-git-18880 — build notes

start_utc: 2026-10-26T02:10:39Z (pipeline start; this pass re-ran the build)
end_utc: (pending — gate in progress)

## Stack

Pinned commit f9d1128c6950c923a057d2bb77c54d1c702c258a is the first parent of the published fix
for this branch, da9f7d8a0e98b475600177348d6ece384a370f36 ("dotgit ref-name containment", v6). The
second published commit, 4a0e66d555de5f9a30c31e2df64f445f42bd01e7, is the same advisory's backport
to the v5 line; it cannot apply to this v6 module path and additionally tightens the policy to
`refs/`-or-root-ref, changing the shared storage tests that the pinned tree still runs. The recall
check therefore uses da9f7d8a's source change (the fix shipped for this branch); this is recorded in
`stacking.history.recall_check`.

The reader's design (T1, T3, T4, T5, T7) was verified on the pinned code and extended with one more
uncovered route (T6) found during verification, because the published fix leaves it open.

## Levers (one line each)

- T1 (advisory route; both): a stored reference name resolves onto unrelated repository metadata or
  climbs out of the reference tree; verified with `config`, `hooks/pre-commit`, `refs/../../config`.
  Fix site `storage/filesystem/dotgit/dotgit.go:1047` (SetRef).
- T2 (published-fix far site; deepseek): the second write implementation
  (`dotgit_setref.go:63`) is chosen when a backend cannot open files read-write and has the same
  unguarded join; exercised with a `noReadWriteFS` billy wrapper.
- T3 (advisory route; deepseek): `RemoveRef` (`dotgit.go:1145`) removes `.git/config` /
  `.git/packed-refs` by name; the prior existence check does not prove the name is a reference.
- T4 (advisory route; deepseek): `Ref` (`dotgit.go:1082`) returns metadata content as a reference.
- T5 (uncovered upstream; deepseek): `ReflogReader`/`ReflogWriter`/`DeleteReflog`
  (`dotgit.go:270/284/293`) join into `logs/` with no check.
- T6 (uncovered upstream; deepseek): `Repository.Tag` / `DeleteTag` (`repository.go:1032-1053`)
  normalise the short name with `path.Join` before the storage sees it, so `DeleteTag("../heads/main")`
  deletes the branch. Neither published commit touches this; a later upstream change removes the same
  normalisation.
- T7 (advisory route; mimo): the rule must not become `refs/`-only or reuse the existing validator:
  `bar`, `HEAD`/`ORIG_HEAD`/`FETCH_HEAD`/`MERGE_HEAD`, `refs/heads/.invalid`, symbolic HEAD and
  `logs/HEAD` keep working.

Concepts: [["T1","T2"],["T3"],["T4"],["T5"],["T6"]]; one `miss_*.patch` security_fail check each.

## Verified

- Every route was reproduced behaviourally on the pinned tree before a test was written: write,
  second implementation, read, delete, reflog append/read/delete, and the tag short-name route.
- Hidden security: 14 tests, all 14 fail on pinned, all pass on the oracle. Hidden functional: 7
  tests, all pass on pinned and on the oracle.
- Project tests (`./storage/filesystem/dotgit ./storage/filesystem ./plumbing` with Go 1.26.4) pass
  on pinned, oracle, alternative, hardening and every miss patch that expects functional green.
  Go 1.27 changes deflate output and breaks two pinned object-size tests, so the images pin 1.26.4.
- Check patches were each applied to the pinned tree and run against the hidden suites before being
  listed: miss_write 4 security failures, miss_delete 2, miss_read 3 (two read + the tag read),
  miss_reflog 3, miss_tag 2; upstream_fix (da9f7d8a alone) 7; overbroad_refs_only 2 functional;
  refuse_all 4 security + 7 functional; hardening and alternative 0 failures.
- Control task built: same instruction byte-for-byte, write-route-only security tests (4) and a
  write-only reference; its own static stage passes.

## Not verified

- The published fix's *intent* for single-component names: the v5 backport rejects them and edits the
  shared storage tests, while the v6 fix keeps them. The task keeps the v6 behaviour because the
  pinned project's own tests require it; the report covers it only through the general keep-working
  sentence.
- Whether the upstream authors considered the tag short-name normalisation in scope; it is the same
  name-containment protection and is reachable from the same public surface, so the general property
  covers it.
- The exact GHSA/CVE identifier for advisory 18880 was not available; the report never names one.

## Gate (this pass)

- static (stacked): PASSED.
- static (control): PASSED.
- check_stack.py: conforming (5 concepts, pattern H4).
- nop: PASSED — 14/14 security tests fail on the pinned tree, 300/300 functional pass (7 hidden + the storage/plumbing project suites).
- oracle: PASSED — 3/3 identical runs at reward 1.0.
- patches: running (10 checks).
