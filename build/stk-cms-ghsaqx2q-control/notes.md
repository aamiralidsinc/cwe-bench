# stk-cms-ghsaqx2q-control build notes

- Control for `stk-cms-ghsaqx2q`; same pinned commit, byte-identical `instruction.md`, same
  environment, same functional suites.
- Only the advisory's own route is in the security suite: `PostedLayoutSecurityTest` (4 tests).
- Reference fix: the published request-boundary cleanse alone (`src/services/Fields.php`,
  `assembleLayoutFromPost`).
- Patch checks: `control_miss_posted.patch` (element-factory cleanse only) leaves all 4 security
  tests failing with all functional tests passing; `control_overbroad.patch` (published fix plus a
  refusal of encoded elements) breaks three functional tests; `control_hardening.patch` (published
  fix plus the defensive element-factory cleanse) passes security and functional.
- The project's own `ComponentHelperTest` runs under Codeception with the same result as the stacked
  task (29 tests, 35 assertions, OK).
- Gate: (filled when the gate finishes)
