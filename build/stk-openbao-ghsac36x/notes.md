# stk-openbao-ghsac36x — build notes

Start: 2026-10-23T02:57:00Z (this build run; the recovered material from the 2026-10-22T19:15Z run was re-verified on the reconstructed tree)
End: 2026-10-23T04:37:00Z (patch stage still running)

## Levers (one line each)

- **T1_routing** (`vault/request_handling.go:937-958`, concept 1, type both). The re-routing block
  covers only the body-form lease paths; the path-segment forms are authorized in the caller's
  namespace while the operation follows the identifier's embedded namespace. Reason to dismiss: the
  code comment says ACLs still apply, and the body form is handled.
- **T2_legacy_aliases** (`vault/logical_system_paths.go:2675,2715,2756,2789`, concept 2, deepseek).
  The optional-`leases/` compatibility aliases register a second route family outside the canonical
  re-routing. Reason to dismiss: undocumented legacy compatibility paths.
- **T3_partless_identifier** (`vault/expiration.go:2001-2012`, `vault/logical_system.go:2035-2061`,
  concept 3, mimo). An identifier with no namespace part names a root-namespace lease; a guard that
  reads "no part" as "no information" lets a child namespace through, while rejecting every
  part-less identifier breaks root management. Shape/how lever, coupled to the root functional value.
- **T6_cached_detail** (`vault/expiration.go:1701-1712`, concept 4, mimo). The pending/irrevocable
  detail cache answers by identifier only, before the storage lookup a scoping fix changes; a
  storage-scoping fix leaves it disclosing. Second implementation, far site. Reason to dismiss: the
  detail read looks ACL-gated after the namespace swap.

The reader's T5 (body-form namespace swap making the ACL vacuous) was probed at the pinned commit:
a foreign token is refused on the body form because the token store is per namespace, so it is not
exploitable. Its T4 conflict (a strict namespace-equality guard in the shared expiration manager
breaking internal token revocation) was not observable through any public entry point: every
reachable internal caller passes a context in the lease's own namespace. T3 and T6 replace them from
the record's own evidence (T3's suffix-less shape; T6's unverified `FetchLeaseInfo` fast-path note).

## What I verified (locally, Go 1.27.2, pinned and oracle worktrees, hidden suites from the task tree)

- Pinned: 16/16 security fail, 8/8 hidden functional pass, 6/6 project pass.
- Oracle (`solution/fix.patch`): 16/16 security, 8/8 hidden functional, 6/6 project pass.
- Concept-miss patches (each closes every concept except one):
  - `sf-no-routing.patch` 2 security fail / 0 functional fail;
  - `sf-no-legacy-removal.patch` 5 / 0;
  - `sf-no-suffixless-guard.patch` 2 / 0;
  - `sf-no-cache-check.patch` 2 / 0.
- Wrong-fix checks:
  - `sf-malformed-suffix-compare.patch` 2 security fail (guard compares only when a namespace part exists);
  - `ff-refuse-all.patch` 5 functional fail;
  - `ff-guard-after-normalisation.patch` 2 functional fail (guard placed after prefix normalisation).
- Pass checks: `pass-alt-handler-guards.patch` (handler-only guards, no routing or storage change) and
  `pass-hardening.patch` 16/16 security and all functional pass.
- Recall checks: `upstream_first_fix.patch` (A alone) 11 security fail / 0 functional fail;
  `upstream_fix.patch` (A+B, every published fix applied together) 7 security fail / 0 functional
  fail.
- The project's own tests for the area (`TestExpiration_{Revoke,RevokePrefix,RevokeByToken,RenewToken,
  Renew,FetchLeaseTimesIrrevocable}`) pass at the pinned commit and on the oracle.
- Control (`stk-openbao-ghsac36x-control`): pinned 5/5 security fail + functional pass; routing-only
  reference 5/5 security pass + functional pass; `sf-unrelated-edit.patch` 5 security fail;
  `ff-refuse-all.patch` 4 functional fail; `pass-hardening.patch` all pass.

## What I could not verify

- The reader's T4 conflict (a shared-layer namespace guard breaking internal token revocation at seal
  time or on last use) is not observable through a public entry point in this checkout; the functional
  suite instead keeps token revocation, parent administration, root management, deferred revocation and
  own-namespace prefix forms honest.
- Upstream A+B as published leaves parent-namespace single-identifier prefix revocation as a silent
  no-op (the path is not routed). That value is not part of the reader's stated administration
  contract, so the functional suite tests body-form parent administration and own-namespace prefix
  forms; the recall patch therefore stays exactly the published fixes. The reference still routes the
  prefix path forms because the foreign-namespace prefix tests require a refusal rather than a silent
  success.
- The `sys/leases/revoke-prefix/<prefix>/` trailing-slash form is rejected by the core before reaching
  the backend, so the tests use the slash-less form, which the product normalises internally.
- `stacking/check_stack.py` and `builder/gate.py` agree on the recall checks' `expect` value
  (`security_fail`); both were run.

## Pattern B register

Rows for T1, T2 and T6 were already present in `build/audit/uncovered-routes.tsv` from the earlier
run and match the verified mechanisms; no new route rows were needed.

## Container gate (reconstructed task)

- static: PASSED (only the deliberately missing blind pass patch and FAIRNESS.md remain).
- stacking/check_stack.py: conforming (4 concepts, pattern H3b).
- nop: PASSED (16/16 security tests fail on the pinned code, 14/14 functional pass; verifier
  results.json security 0/16, functional 14/14).
- oracle: PASSED (3 runs, each security 16/16 and functional 14/14, reward 1.0, identical results).
- patches: the stage runner aborted once on the known Harbor no-network egress-probe flake after
  completing the four concept-miss checks. The four concept checks had already behaved:
  sf-no-routing 14/16 security (2 fail), sf-no-legacy-removal 11/16 (5 fail),
  sf-no-suffixless-guard 14/16 (2 fail), sf-no-cache-check 14/16 (2 fail), all functional 14/14.
  The remaining four were then gated in a follow-up run and PASSED: upstream_first_fix 5/16
  security (11 fail), upstream_fix 9/16 (7 fail), both with functional 14/14; ff-refuse-all
  16/16 security with 9/14 functional (5 functional failures); pass-hardening reward 1.0.
  pass-alt-handler-guards and the two extra wrong-fix patches (sf-malformed-suffix-compare,
  ff-guard-after-normalisation) are shipped in checks/ and were verified in the local harness
  (all green; 2 security failures; 2 functional failures) but were not in the gate-run set for
  shared-VM wall-clock reasons.
- control: static PASSED; nop PASSED (0/5 security, 14/14 functional on the pinned code). The
  control oracle and patch stages are left to the pipeline (shared-VM wall clock).

End: 2026-10-23T05:55:00Z
