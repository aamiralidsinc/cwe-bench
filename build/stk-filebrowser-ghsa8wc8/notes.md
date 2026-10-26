# stk-filebrowser-ghsa8wc8 — build notes

- Start (UTC): 2026-10-23T07:15Z (reconstruction of a build whose task tree was lost; the earlier
  run in this directory started 2026-10-23T00:44Z and left checks/, evidence/ and these notes)
- End (UTC): see the end marker written when the gate finishes.

## Design

Stacked H3a task on filebrowser/filebrowser, pinned at `3406d3d7` (the parent of the earlier fix
`7c2c0a11`; the later fix `64511ce4` changes `files/scoped.go`, which `7c2c0a11` added). The
reader's four traps (T1, T3, T4, T5) were re-verified on the pinned tree through the real HTTP
handlers with a bolt-backed user store and a forged token (`go test ./http` in a pristine worktree).

Why an equivalent call-site design instead of the literal upstream patch: the published fix A is a
filesystem-layer refactor (`ScopedFs` wraps every operation), so a solver who implements A closes
T3, T4 and T5 incidentally and the stack would collapse to one concept. The reference fix repairs
the containment predicate and applies it at each missing sink, which keeps T3/T4/T5 as independent,
load-bearing edit sites. It also resolves a target whose `..` follows a symlinked component, a
shape neither published fix gets right — that is what makes `checks/upstream_fix.patch` fail (the
recall rule).

## Levers, one line each

1. **T1** (MiMo-type, how): a link inside the folder whose target is outside and does not exist
   yet, written to through the upload and resumable-upload routes — absolute, relative, or passing
   through another symlinked folder before a `..` — `files/file.go:186-228`. Reason to dismiss: a
   single `Readlink` plus a lexical `Join`/prefix check looks complete (and the pinned comment said
   a dangling link "resolves to its parent and is therefore allowed").
2. **T3** (DeepSeek-type): directory creation through an existing escaping directory link —
   `http/resource.go:128-135`. Reason to dismiss: it only makes an empty directory, and the report
   is about dangling links that create files.
3. **T4** (DeepSeek-type): a recursive copy whose destination tree holds an escaping link named
   like a source child — `fileutils/dir.go:31,46-56`, `fileutils/file.go:53-59,76`. Reason to
   dismiss: the handler already checks the top-level destination and the copy helpers check the
   source.
4. **T5** (DeepSeek-type): recursive listing rooted below an escaping directory link —
   `http/resource.go:405-448`. Reason to dismiss: it returns only names, sizes and mtimes.

## Verified

- Every security test fails on the pinned tree through the real product router (`fbhttp.handle`, a
  bolt user store, `users.Clean`-built filesystem, forged JWT) and passes on the reference.
- Every functional test passes on the pinned tree, on the reference, and under each wrong-fix patch
  that must keep functional tests green.
- Local matrix (worktree, `go test ./http -run '^Test(Sec|Func)_'`): `miss_resolver` fails only
  T1's four tests; `miss_mkdir` only T3; `miss_copy` only T4; `miss_recursive` only T5.
  `crash_as_refusal`, `wrong_resource` and `check_after_adjustment` fail security only;
  `refuse_all` and `overbroad_symlink` fail functional only (both also break the project's own
  symlink tests); `hardening` and `alternative` pass all 17 hidden tests plus the project's tests.
- `upstream_first_fix` (A alone) fails 5 security tests (plain dangling POST/TUS and the `..`
  shapes, plus T4) and passes every functional test.
- `upstream_fix` (A+B) still creates the file outside for a dangling target whose `..` follows a
  symlinked component (absolute and relative) and still follows the copy destination link.
- The project's own tests (`go test ./files ./fileutils ./http`) pass at the pinned commit and
  under the reference, alternative and hardening patches.
- The pinned tree contains no regression tests from either published fix (A/B's test files postdate
  the pin; the pin's own `fileutils/copy_test.go` test is the earlier GHSA-c2gv incomplete-fix
  test, which covers a different property).

## Could not verify

- The upstream A+B fix reports a permission error on the copy route, so the security contract "a
  client error" holds there; the recall patch fails on the two `..` shapes.
- `stacking/check_stack.py` wants `expect == "security_fail"` for the per-concept and recall
  checks; `builder/gate.py` accepts `security_fail`, which is what the manifest uses. Both agree.
- Whether the `..`-after-a-symlinked-component shape would be considered in scope of the published
  advisories by their authors; it is a write outside the user's scope through a link that exists out
  of band, exactly the property both advisories describe.
- `present_in_latest` for the three uncovered routes is recorded as `unknown`: the call sites still
  carry no explicit containment check in current upstream, but the published `ScopedFs` wrapper is
  expected to enforce it; this was not verified behaviourally.

## Control task

`stk-filebrowser-ghsa8wc8-control` (same pin and report; security tests cover only the advisory's
own dangling-link upload route): reference = the resolved-target fix alone; `miss_naive` (one-level
`Readlink`) fails only the two `..`-shape tests.

## Gate

Main task (`stk-filebrowser-ghsa8wc8`), stages run one at a time on 2026-10-23:

- `static`: PASSED (only the missing `blind` patch remains).
- `nop`: PASSED — 7/7 security tests fail through the real handlers; 65/65 functional (10 hidden +
  55 project) pass.
- `oracle`: PASSED — three runs, reward 1.0, 7/7 security and 65/65 functional each, identical.
- `patches`: PASSED — 13/13 checks behaved as declared:
  `miss_resolver` fails exactly T1's four tests (0.4286); `miss_mkdir`, `miss_copy` and
  `miss_recursive` fail exactly their one test each (0.8571); `upstream_first_fix` (A alone) fails
  five (0.2857); `upstream_fix` (A+B) still fails the two `..`-shape tests and the copy route
  (0.5714); `refuse_all` and `overbroad_symlink` fail functional (0.0); `crash_as_refusal`,
  `wrong_resource` and `check_after_adjustment` fail only their security test; `hardening` and
  `alternative` score 1.0.

Control task (`stk-filebrowser-ghsa8wc8-control`), same pin and report, advisory route only:

- `static`: PASSED.
- `nop`: PASSED — 4/4 security tests fail; 65/65 functional pass.
- `oracle`: PASSED — three runs, reward 1.0, 4/4 security and 65/65 functional, identical.
- `patches`: PASSED — `miss_naive` (one-level `Readlink`) fails exactly the two `..`-shape tests
  (0.5) with functional green; `refuse_all` fails functional (0.0); `hardening` scores 1.0.

End (UTC): 2026-10-23T08:37Z.
