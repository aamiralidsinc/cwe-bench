# stk-git-js-ghsahffm — build notes

Start: 2026-10-26T02:14:58Z (recorded by the pipeline)
End: 2026-10-26T04:52:56Z

## Task

simple-git (steveukx/git-js) at 47030d5980d9ffab86d4c725c0df8ffd587ab9f6, the merge that shipped
advisory A's guard (GHSA-9p95-fxvg-qgq2 / CVE-2022-25912). Advisory B (GHSA-hffm-xvc3-vprc /
CVE-2026-6951) is the incomplete-fix repair, published as 89a2294febed. H3b2: the pinned code already
contains A, and the stack is the routes A's guard and B's repair still leave open.

The reference fix is one file, `simple-git/src/lib/plugins/block-unsafe-operations-plugin.ts`, with
four independent edit sites (one per concept). No other source file changes.

## Levers (one line each)

- T1 (advisory route, both): the guard matches the exact token `-c` and one value shape, so
  `--config`, its attached form and `--config-env` reach the same sink — plugin:6-24.
- T2 (deepseek, uncovered): the configuration-writing subcommand (`addConfig`, or raw `config`)
  writes the same permission without ever carrying an inline switch — tasks/config.ts:24-45.
- T3 (mimo/how-type, uncovered): the caller names a configuration source that git expands after the
  guard has run, so the assignment never appears in argv — plugin:31-39.
- T4 (deepseek, uncovered): the pack-command guard exists on clone and fetch but not on pull,
  ls-remote or push (which uses a differently named flag) — remote.ts:26-33, pull.ts:7-24,
  push.ts:13-30.

Coupled keep-working values, tested functionally: data-carrying configuration (`--config
http.extraheader=...`, `addConfig('user.name', ...)`, an instance-wide setting), the existing
protocol opt-in, and ordinary remote listing/pull/push.

## Verified

- Pinned tree, built library: all 9 security cases fail (side effects observed: the protocol setting
  is stored or in effect, the pack command runs) and all 8 functional cases pass. The four project
  jest files pass (49 tests) on the pin.
- Reference: 9/9 security and 8/8 functional pass; the four project jest files pass; the full project
  suite (83 suites, 629 tests) passes.
- Check patches, each applied to a fresh pinned copy: miss_config_forms 3 security fail, 0 functional
  fail; miss_config_api 2/0; miss_include 1/0; miss_sibling_commands 3/0; upstream_fix (A+B reduced
  to this code) 1/0; upstream_first_fix (A's published commit alone) 9/0; hardening 0/0 (all pass);
  alternative 0/0 (all pass); refuse_all 8 functional fail; crash_as_refusal project suite fails;
  overbroad 3 functional fail.
- All 12 check patches apply cleanly to the pinned tree with `patch -p1`.
- `check_stack.py`: conforming, 4 concepts, pattern H3b2.
- Gate: static PASSED; nop PASSED (in the verifier container: 9/9 security tests fail on the pin, 8/8
  hidden functional and 49/49 project tests pass, reward 0); oracle PASSED (3 runs, reward 1.0,
  identical results); patches PASSED (11/11 checks matched their declared outcome, including both
  recall checks). blind.patch is produced by the post-gate blindfix run.

## Could not verify / open items

- The published fix commits were read from a read-only sibling clone of the repository (the reader's
  session could not read them). Upstream later closed T3 in c427fba (PR #1167, 2026-05-10) by adding
  an include-screening category; advisory B's published commit (89a2294) does not contain it, which
  is why the recall patch leaves T3 open. That later commit is outside this task's two advisories
  and was not built on beyond confirming the route is real. `upstream_fix.patch` is the published repair reduced to the pinned
  code: config carriers, the config subcommand and global pack flags; it deliberately omits the
  published fix's environment-variable scanning, which no test of this task drives.
- The control task's static stage passed; its container stages were not run in this window (the
  shared VM's Docker daemon was saturated, and the stacked task's four stages consumed the build
  time). Its reference and its four security cases were verified locally: the pin fails 4/4, the
  control fix passes 4/4 security and 8/8 functional.
- The listing check was not run (it needs a model launch, which this build must not perform).
- Gateway/network flake risk: the environment image installs the 2022 yarn lockfile at build time;
  it was reproduced locally before the image build.

## Scope

Only the two advisories for this repository and their protection are in scope. Noticed outside it,
not built on: the published repair also screens child-process environment variables and a longer
list of program-naming configuration keys, which this task's tests do not drive.
