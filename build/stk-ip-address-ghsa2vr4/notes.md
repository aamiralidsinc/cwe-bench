# stk-ip-address-ghsa2vr4 — build notes

Start (UTC): 2026-10-26T02:21:20Z (from start_utc.txt)
End (UTC): <pending>

## What the task is

`beaugunderson/ip-address` at e82a681 (v10.2.0), the first parent of the A advisory fix
4a1f613 (GHSA-22jq-vg5j-6vgg), with the B advisory fix ab3dc88 (GHSA-2vr4-cq9g-pvrc) as the
later fix of the fix. Pattern A+B / stacking H3a. Solver fixes the special-range classification
of IPv6 (and IPv4) addresses.

## Levers (one line each)

- T1 (advisory A, deepseek): IPv4-mapped and NAT64 well-known IPv6 values are classified by the
  wrapper, not the embedded IPv4 address (`src/ipv6.ts:1219-1220,1267-1268,1283-1284,567-575`;
  `src/v6/constants.ts:25-53`); dismissed because `isMapped4()` exists and the type table names
  NAT64.
- T2 (uncovered, deepseek): `isLinkLocal()` compares the first 64 bits with `fe80:0:0:0` while
  the type table uses `fe80::/10` (`src/ipv6.ts:1203-1213`, `src/v6/constants.ts:47`); dismissed
  by the in-code "zeroes are required" comment and by `getType()` already saying link-local.
- T3 (uncovered, mimo): every special-range classifier runs on `isInSubnet`, which returns false
  when the address's own CIDR prefix is shorter than the checked range
  (`src/common.ts:10-12`, `src/ipv6.ts:567-575,1231-1293`, `src/ipv4.ts:456-506`); dismissed
  because that is correct subnet-containment arithmetic, pinned by the project's tests, and a
  prefix-bearing host is documented input.
- T4 (advisory B, both): the NAT64 local-use block `64:ff9b:1::/48` has no public/internal
  answer (`src/ipv6.ts:1089-1116,1291-1293`, `src/v6/constants.ts:52`); dismissed because
  `getType()` already names it, the decode default is documented, and the operator-chosen prefix
  length makes `null` look like the contract.

## Concept independence

- T1: embedded delegation + mapped type label.
- T2: the native link-local branch.
- T3: the shared host-bits primitive.
- T4: the private check on Address6 (and the local-use range).
One guard does not close two: the miss patches each fail only their concept's security tests.

## Verified

- Pinned tree: the project's own `functionality-v4-test.ts` + `functionality-v6-test.ts`
  (258 cases) pass; the 25 security cases all fail; the 11 functional cases all pass.
- Reference fix (`solution/fix.patch`, 4 source files): 0 security and 0 functional failures;
  project tests pass; `tsc --noEmit` passes.
- `checks/upstream_first_fix.patch` (A alone): 15 security failures (T2+T3+T4) -> expect fail.
- `checks/upstream_fix.patch` (A+B plus the helper B requires): 12 security failures (T2+T3) ->
  expect fail, so the stack adds beyond what upstream shipped.
- `checks/miss_embedded.patch`: 8 failures, all T1. `miss_link_local.patch`: 4, all T2.
  `miss_suffix.patch`: 8, all T3. `miss_local_use.patch`: 3, all T4.
- `checks/functional_overbroad.patch` (relax `isInSubnet` itself): security passes, 2 hidden
  functional cases and 2 project tests fail -> functional_fail.
- `checks/alt_correct_fix.patch` (private local helper instead of the shared primitive) and
  `checks/hardening.patch` (reference + deprecated IPv4-compatible decode): 0 failures.
- The control `stk-ip-address-ghsa2vr4-control` (advisory routes T1+T4 only): 13 security cases
  fail on the pin and pass on the A+B fix, functional passes.

## Gate

- static: PASSED for the task and the control.
- check_stack.py: conforming (4 concepts, H3a).
- nop: PASSED (security 0/25 pass, functional 269/269 pass).
- oracle: PASSED on re-run (TMPDIR=/var/tmp): 3/3 trials at reward 1.0, identical results. The
  first attempt was an infra-only failure (the tmpfs `/tmp` filled while Docker compose wrote its
  build-metadata file); one trial of that attempt still completed at reward 1.0 with 294/294 tests.
- patches: <pending>
- control gate: <pending>

## Guesses / unverified

- The reader record at `pipelines/stacking/out/reader/h3-ghsa-2vr4-cq9g-pvrc.json` says
  `usable: false` and a different four-trap design (getScope, a NAT64 predicate, the decode
  default, suffix handling). The build prompt's candidate record and design plan (traps
  T1/T2/T3/T4/T7) were used instead, but T1 ("no boolean NAT64 predicate") and T7 ("default
  decode must handle local-use") were not used: a hidden test would have to guess a new method
  name, and the default decode is documented and deliberate. They were replaced by T4 as the
  B advisory's real fix (`isPrivate` for the local-use block), which is testable through the
  interface contract stated in the report.
- The reference fix is a superset of A+B's source changes plus the separate follow-up that moved
  classification off `isInSubnet` (v10.2.2). The `upstream_fix.patch` is A+B plus the minimal
  `isHostInSubnet` helper B needs to compile, because B's diff is based on a tree that already
  has that helper.
- `present_in_latest` in the pattern-B register was read from the current default branch
  (db0dbda): both hidden routes are fixed there (link-local uses `fe80::/10`; classifiers use
  host bits).
- No trial was run (per the build prompt). The 45-60 minute effort estimate is a judgement; the
  screener estimated 90 minutes for a larger five-trap set.
