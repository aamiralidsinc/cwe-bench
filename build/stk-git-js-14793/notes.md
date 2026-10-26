# stk-git-js-14793 build notes

- Start (UTC): 2026-10-26T02:09:12Z (from `start_utc.txt`)
- End (UTC): 2026-10-26T04:56Z

## Task

`steveukx/git-js` (simple-git + `@simple-git/argv-parser`) at the parent of the published fix
(`76f308e`), with the unsafe-operations guard at the spawn boundary. Advisory GHSA-X6JW-M9V5-85VH /
CVE-2026-102828 (incomplete denylist, CWE-184, leading to command execution). Pattern A+B, stacked H4.

## Levers (one line each)

- **T1** (advisory route, A): the config-key denylist has no `trailer.<token>.cmd` / `.command` rows.
  `detect-vulnerable-config-writes.ts:39-71`. Reason to dismiss: the docs call the list a
  non-exhaustive safety net, and trailer formatting does not read like a command-binary row.
- **T2** (published-fix far site, A, DeepSeek): no rebase `-x` / `--exec` matcher in the flag
  denylist. `detect-vulnerable-flags.ts:65-79`. Reason to dismiss: the rebase half is a separately
  credited report in the same commit.
- **T3** (published-fix far site, A, MiMo): the per-command switch table has no rebase entry, so
  `-qx` / `-ix` / `-x/bin/true` stay opaque to the tokeniser. `flag-specs.ts:43-102`,
  `token-expander.ts:33-65`. Reason to dismiss: it is a parsing schema, not a security check.
- **T4** (uncovered upstream, B, DeepSeek): a section rename reports the source section as the key
  and the destination as the value, so the created name is never checked.
  `detect-config-action.ts:42-55`. Reason to dismiss: a rename is a structural edit, not a
  key/value write.
- **T6** (uncovered upstream, B, DeepSeek): every token after the argument separator is a path, so a
  config invocation naming its setting after the separator has no operands and the denylist never
  sees the key. `parse-task-flags.ts:34-40`. Reason to dismiss: the separator is the documented path
  mechanism.

## Concepts (stacking)

- `[T2, T3]` — rebase exec: the denylist row and the switch table are both required; removing
  either leaves security cases failing while the other concepts stay closed (the `miss_rebase`
  patch removes both; a row-only or table-only patch was validated as `sf_long_only` /
  `sf_no_attached`).
- `[T4]` — rename destination.
- `[T6]` — separator operands.

DeepSeek-type: T2, T4, T6. MiMo-type: T3. T1 is the advisory route (not a concept) but is tested.

## What I verified on the pinned tree (local, before Docker)

- Every security assertion fails on the pinned code (the recording `git` stand-in is started) and
  passes under the reference fix.
- The reference fix keeps 313 functional cases green: 23 hidden legitimate-use cases, the
  project's `packages/argv-parser` suite (minus the one case that asserts the pre-fix rename
  semantics and the four permanently-disabled upstream cases), and the affected `simple-git` unit
  suites.
- `upstream_fix.patch` (the published source fix alone) leaves 7 security cases failing (T4, T6).
- Each per-concept miss patch leaves exactly its concept's security cases failing with all
  functional cases green.
- The alternative implementation (`pass_alt`) and the hardening variant both score 1.0.
- Control task: pinned 0/7 security + 313/313 functional; reference 7/7 + 313/313.

## Verifier staging fix

The first container run exposed a staging bug: `/tests` is locked to `0600 root`, and `cp -a` of the
pristine project test files and their vite configs preserved that mode, so the uid-1000 runner could
not read two configs and the project suites silently produced no XML. `test.sh` now runs
`chmod -R a+rX` over the restored project files and treats a missing
`functional.xml` / `project-argv-parser.xml` / `project-simple-git.xml` as a verifier defect
(`infra:missing_functional_results`), so the project suites cannot be dropped from the score again.

## Gate results (stacked task)

- `static`: PASS.
- `nop`: PASS — 23/23 security cases fail on the pinned code, 313/313 functional cases pass.
- `oracle`: PASS — three runs, reward 1.0 each, 336/336 tests each, identical.
- `patches`: PASS — every `checks/*.patch` behaved as declared (see below).

| check | expectation | observed |
|---|---|---|
| `miss_rebase.patch` | security_fail (misses T2,T3) | security 14 pass / 9 fail, functional 313 pass |
| `miss_rename.patch` | security_fail (misses T4) | security 20 / 3, functional 313 |
| `miss_separator.patch` | security_fail (misses T6) | security 19 / 4, functional 313 |
| `miss_trailer.patch` | security_fail (misses T1) | security 9 / 14, functional 313 |
| `upstream_fix.patch` | security_fail (recall) | security 16 / 7, functional 313 |
| `sf_long_only.patch` | security_fail | security 17 / 6, functional 313 |
| `sf_no_attached.patch` | security_fail | security 22 / 1, functional 313 |
| `ff_case_insensitive.patch` | functional_fail | functional 311 pass / 2 fail |
| `ff_global_x.patch` | functional_fail | functional 328 / 8 |
| `ff_refuse_all.patch` | functional_fail | functional 235 / 101 |
| `pass_alt.patch` | pass | reward 1.0, 336/336 |
| `pass_hardening.patch` | pass | reward 1.0, 336/336 |

## Gate results (control task)

- `static`: PASS.
- `nop`: PASS — 7/7 security cases fail, 313/313 functional pass.
- `oracle`: PASS — three runs, reward 1.0 each, 320/320 tests each.
- `patches`: PASS — `sf_only_cmd.patch` security 1 pass / 6 fail with 313/313 functional;
  `ff_refuse_all.patch` 220/320 (100 functional fail); `pass_alt.patch` and
  `pass_hardening.patch` reward 1.0 each, 320/320.

## What I could not verify

- The published fix commit is not present in the pinned worktree (history is removed in the image);
  the fix-site claims come from the supplied screener/reader record and the clone used here.
- `core.alternateRefsCommand` and other out-of-scope siblings were not built on.
- The `--rename-section` route needs an existing section with a `command` key for a full exploit
  chain; the hidden case asserts the guard refuses the rename before any child process starts, which
  is the property the task states.
- No upstream release tree was checked, so `present_in_latest` for the pattern-B routes is unknown
  (recorded as such in the register).

## Outside scope noticed

- The screener notes further unguarded command-naming options (`git difftool -x`, possibly
  `git grep -O`); not verified and not built on.
