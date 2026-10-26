# stk-nanoid-7632 — build notes

Start (UTC): 2026-10-26T02:24Z
End (UTC): pending (control gate still running under a load average of ~200)

Repo: ai/nanoid, pinned 095b73d4a051e21081b281a5b2a1aabb4bc9a061 (verified first parent of the
published fix cb3626d0f3342fdf179cd425fd9c4fbb92c7d0e7 with `git rev-parse cb3626d^`). Reader
record: `pipelines/stacking/out/reader-ds/h4-7632.json` (the path named in the prompt,
`pipelines/stacking/out/reader/h4-7632.json`, does not exist in this checkout; the DeepSeek reader
record was used).

## Levers (one line each)

- C1 / T1+T5+T8+T9 — the custom generator closure decides on the effective size after defaulting;
  zero/negative (T1), non-numeric/unbounded (T5), the defaulted-call coupling (T8) and the bundled
  tool's overflowing size literal (T9). where: index.js:53-56, bin/nanoid.js:35-38. Dismiss: the
  reported example is one zero size.
- C2 / T2+T10 — the bundler/react-native copy of the same closure has its own arithmetic (a zero
  default returns one character there) and its own blind spot for non-numeric/unbounded sizes.
  where: index.browser.js:36-45. Dismiss: only selected by the browser/react-native export
  condition, so a Node reproduction never reaches it.
- C3 / T3+T4 — the documented non-secure module's two countdown loops block on a negative size
  (including numeric text). where: non-secure/index.js:14-17 and 27-29. Dismiss: documented as the
  non-secure alternative; size 0 already returns an empty ID there.
- C4 / T6+T7 — progress is decided at creation time: an alphabet with no symbols blocks both
  generator copies (T6), and a non-positive creation default blocks even when the call passes a
  valid positive size (T7). where: index.js:51-56, index.browser.js:34-39. Dismiss: alphabet
  validity is the caller's precondition; a positive call size looks valid and the exit test
  compares it.

Concepts: [`T1`,`T5`,`T8`,`T9`], [`T2`,`T10`], [`T3`,`T4`], [`T6`,`T7`].

## Verified by execution (Node 20.19.2, pinned tree and a prototype fix)

- Every security case blocks or returns the wrong answer on the pinned tree, and every one returns
  the stated answer with the reference fix. The runners were exercised locally with a 1.2 s
  per-case timeout.
- All 27 hidden functional cases pass on the pinned tree and on the reference fix; the project's
  own 47 cases (test/index.test.js, test/non-secure.test.js, test/bin.test.js) pass on both.
- The check patches behave as declared: the four `miss_c*` patches each leave exactly their
  concept's security cases failing with functional green; `upstream_fix` (the published final
  `size <= 0` decision on the two ESM copies) leaves 15 security cases failing; `crash_refusal`
  (the first published fix, a throw on size 0) leaves all security cases failing; the over-broad
  integer-only patch fails two functional cases; the alternative fix and the hardening patch score
  green.
- The control's four security cases fail on the pinned tree and pass with its reference fix; its
  miss patch leaves them failing and its over-broad patch fails two functional cases.

## Published-fix reconstruction

Only cb3626d (index.js, `size === 0`) applies to this line and its parent is the pinned commit.
e10f8d4 and f9d13f1 are later maintenance-line commits (e10f8d4 touches async/index.native.js;
f9d13f1 touches async/* and index.cjs/index.browser.cjs), and none of those files exist at the
pinned tree (`git ls-tree 095b73d` — verified). `checks/upstream_fix.patch` therefore applies the
final published `size <= 0` decision where its hunks exist in this tree (index.js and
index.browser.js); the stack's extra routes are exactly what that patch leaves open (15 security
cases fail).

## Gate (run 2026-10-26, `TMPDIR` pointed at the big-disk scratch after a /tmp inode infra error)

- `static` PASSED (only the later `blind` patch and FAIRNESS.md are absent, as the build stage expects).
- `nop` PASSED: 23 security tests all fail on the pinned tree, 74 functional tests (27 hidden + 47
  project) all pass. One retry was needed: the first attempt died in Harbor's compose step with
  `/tmp/...: no such file or directory` under /tmp inode pressure (gate verdict `infra`), and the
  retry with `TMPDIR=/home/mara/.tb-graders/cwe/tmpgate` passed.
- `oracle` PASSED: 3 runs, each reward 1.0, 97/97 tests, identical results.
- `patches` PASSED 9/9: four `miss_c*` security_fail checks (5, 7, 4, 4 security failures
  respectively with functional green), `upstream_fix` security_fail (15), `crash_refusal`
  security_fail (23), `functional_overbroad` functional_fail (2), `alt_correct_fix` and `hardening`
  reward 1.0.

## What could not be verified

- The advisory text itself was not available; the impact example was derived from the published fix
  commits and the pinned source, not from a report body.
- The reader's claim that the three fix commits are one linear series is false for this checkout
  (e10f8d4/f9d13f1 are not descendants of cb3626d in this clone); the reconstruction above uses
  only the hunks that exist.
- Whether current upstream (origin/main 35ea7d0) still blocks on every route was checked by
  running the probe: the non-secure loops and the CLI size check are fixed there, the Node/bundler
  empty-alphabet route and the text-size route still block; the reader record was not updated with
  that observation.

## Fairness concerns

- The report states the empty-string answer as the product's contract (the published maintenance
  fix uses it, and the non-secure module already answers an empty string for size 0); a fix that
  throws instead is therefore a wrong fix, and `checks/crash_refusal.patch` proves the tests catch
  it.
- The factory-default route (T7) requires a fix that also inspects creation-time progress; a fix
  that recomputes the loop quantity from the call size is accepted (the case allows either an
  empty ID or the requested length).
