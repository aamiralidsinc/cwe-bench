# stk-git-js-ghsa9p95 — build notes

Start (UTC): 2026-10-26T02:06:30Z
End (UTC): (filled after the gate)

## Task

- Repo: `steveukx/git-js` (npm `simple-git`), pinned at `9bf9baa54b9389e797992d717afdfc05dceaa524` (3.4.0).
- Advisories: GHSA-28xr-mwxg-3qc8 / CVE-2022-24066 (a clone accepts a caller-supplied upload program;
  the fetch-side allowance was fixed earlier as CVE-2022-24433 and is already in the pinned tree) and
  GHSA-9p95-fxvg-qgq2 / CVE-2022-25912 (caller-supplied protocol-permission configuration enables the
  `ext::` transport helper; recorded as an incomplete fix of the earlier advisory).
- Published fixes: `2040de601c89` (clone-side upload-program refusal, advisory A) and
  `774648049eb3` (release commit carrying the `unsafe` plugin from code commit `6b3c631`).
- History rule H3b: the pin is the parent of A's first commit; the reference fix is A plus the later
  fix B, plus the uncovered routes below.

## Levers (one line each)

- **T1** (advisory route, both): clone and its mirror alias pass a caller-supplied pack-program option
  straight through (`simple-git/src/lib/tasks/clone.ts:23-33`); reason to dismiss: it is the reported
  route. Missed by `miss_pack.patch`.
- **T2** (published-fix far sites, deepseek): the same program-selection class on pull, push, raw and
  clone's short spelling (`pull.ts:7-11`, `push.ts:13-20`, `git.js:366-390`); reason to dismiss: the
  published fix extended the fetch check to clone only, so the class reads as handled. Missed by
  `miss_pack.patch`.
- **T3** (advisory route, both): a protocol-permission switch beside a helper address on clone/raw
  (`git-factory.ts:52-54`, `command-config-prefixing-plugin.ts:10`, `clone.ts:24`); reason to dismiss:
  it is the reported route. Missed by `miss_protocol.patch`.
- **T4** (hidden forms, mimo): the same permission change through the config alias in one or two
  tokens, the general protocol switch, and the instance configuration the factory prefixes onto every
  spawn (`git-factory.ts:52-54`, `simple-git-options.ts:6`, `clone.ts:24-26`);
  reason to dismiss: a guard keyed on the exact switch token looks complete, and the configuration is
  merged outside the task builders. Missed by `miss_protocol.patch`.
- **T5** (stored address, deepseek): a helper remote address stored by `remote add` and run by a later
  fetch (`remote.ts:5-7`, `fetch.ts:11-15`); reason to dismiss: adding a remote only writes
  configuration, and the address never appears in the command that runs it. Missed by
  `miss_remotes.patch`.
- Coupled must-keep-working values: ordinary clone/fetch/pull/push/remote/raw, ordinary `-c` and
  `--config` configuration, commit messages and grep terms containing helper-like text, the existing
  fetch refusal message, and the `unsafe.allowUnsafeProtocolOverride` opt-in for helper transports.
  They are tested functionally and are covered by the report only through the general keep-working
  sentence and the operator opt-in.

## Reference fix

Three spawn-time guards plus the opt-in type: a pack-program guard, a protocol-permission guard (all
argument spellings and the instance-configuration prefix) and a stored-helper-address guard. The
alternative check patch places all three rules in one plugin; both pass.

## Verified

- Container gate: static PASSED, nop PASSED (16/16 security tests fail on the pinned code, 14/14 functional pass), oracle PASSED (three runs, reward 1.0, 16/16 security and 14/14 functional each, identical results), patches PASSED (all nine checks behaved as declared: the three per-concept misses left exactly their concept's security tests failing with all functionals green; upstream_fix and upstream_first_fix left 9 and 13 security tests failing; overbroad and refuse_all failed functional tests; hardening and alternative scored 1.0).

- Every security route reproduces through the public API on the pinned bundle with a harmless marker
  program, and every functional case passes on the pinned bundle (14/14).
- Reference fix: security 16/16, functional 14/14 (three repeated runs, identical).
- `upstream_first_fix.patch` (A alone): security 0/3 in the control, 7/16 in the stacked task;
  `upstream_fix.patch` (A+B): security 7/16 — both leave routes open, functional 14/14.
- Per-concept misses: pack 9/16, protocol 9/16, remotes 14/16 (each fails only its concept's routes);
  functionals 14/14 for each.
- Over-broad/refuse-all patches fail functional cases; hardening and alternative pass 1.0.
- The project's own unit suite (49 suites, 521 tests) passes at the pin and with the reference fix;
  it is run in the environment image at build time.

## Could not verify / unknowns

- The minted upstream checksum `774648049eb3` is the release commit that carries the security code
  (`6b3c631`); the raw commit diff does not apply to the pinned tree, so the recall patch is an
  equivalent source application of the published plugin onto the pinned files.
- Whether the hidden shape levers would be considered out of the advisory's scope by a reviewer: T5
  needs a repository whose own git configuration already permits the helper transport (the test writes
  it as setup); the library's own storage path is what the fix guards.
- The reader record named in the manifest is the path given in the build prompt
  (`pipelines/stacking/out/reader/...`); the actual record used here is the identical one under
  `pipelines/stacking/out/reader-ds/...`.

## Pattern B register

Three rows appended to `build/audit/uncovered-routes.tsv` for T2, T4 and T5 (see the file), all with
`disclosure_status = pending client decision`.

## Outside the scope (one line)

The later upstream v4 guard also refuses many other configuration keys (hooks, pager, ssh command,
environment-based config); this task stays within the two advisories' program-selection and
transport-permission protection and does not build on those other routes.
