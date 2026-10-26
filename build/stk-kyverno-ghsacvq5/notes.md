# stk-kyverno-ghsacvq5 — build notes

start_utc: 2026-10-22T19:19:24Z (first pass; analysis, tests, checks, task files)
resume_utc: 2026-10-22T22:17:41Z (second pass; reconstruction and gate)
end_utc: 2026-10-23T00:21:07Z (control gate complete; both tasks green)

## Stack

Pinned commit 99260bd2900290d7d898933c421d2a51d01172a6 is the first parent of A's fix
eba60fa856c781bcb9c3be066061a3df03ae4e3e (verified with `git merge-base --is-ancestor`;
e0ba4de4f1e0 is the same change merged on another branch). B's fix is
bbf3e5c01391d612968440659028ae98e565a777, a later commit on a much later tree; the reference applies
the equivalent of its source change (config-map namespace confinement) to the pinned tree. The task
is H3b: A is the earlier fix, B the later incomplete-fix completion, and the stack adds two
unmodified upstream routes the published fixes never touched.

## Levers (one line each)

- T1 (A, advisory route; mimo/how): the URLPath namespace guard must survive dot segments,
  namespace-name prefixes, all-namespace list paths and post-substitution values, and must keep
  own-namespace reads, the own-namespace record, templated own-namespace targets and cluster-scoped
  policies working.
- T2 (B, uncovered_upstream; deepseek): the outbound service path silently attaches Kyverno's own
  service-account token to any endpoint a namespaced policy names; external calls and the policy's
  own credential must keep working and cluster-scoped policies must keep Kyverno's identity.
- T3 (A, published-fix far site; deepseek): the typed ConfigMap loader takes the namespace from the
  policy entry with no comparison to the policy namespace (second implementation of the same
  protection; B fixed it only after the pinned commit).
- T8 (B, uncovered_upstream; deepseek): the cleanup controller builds the shared context loader with
  a nil policy, so a namespaced CleanupPolicy's context is resolved as cluster-scoped.

Concepts in the manifest: [["T1"], ["T2"], ["T3"], ["T8"]]; one `miss_concept_*` security_fail
check per concept.

## Verified

- Every attack route was reproduced behaviourally on the pinned tree before any test was written
  (cross-namespace URLPath, dot-segment and prefix shapes, all-namespace list, substituted path,
  service-call credential, ConfigMap cross-namespace and empty substitution, cleanup nil policy).
- Hidden security: 10 tests, all fail on pinned and pass on the oracle; the cleanup pair lives in
  `pkg/controllers/cleanup` because it drives that package's own `cleanup` entry point.
- Hidden functional: 12 tests plus the project's own tests for apicall / loaders / factories /
  cleanup. All pass on pinned, oracle, alternative and hardening.
- Check patches were each applied to the pinned copy and run against the full local suites before
  being listed in the manifest (results in the report).
- `upstream_first_fix.patch` (A alone) and `upstream_fix.patch` (A+B) both leave security and
  functional tests failing; upstream's service-call refusal is itself a functional regression.
- Pattern B register rows appended for T2 and T8.
- Control task `stk-kyverno-ghsacvq5-control` rebuilt with only the advisory's apiCall URLPath
  route: static PASSED, nop 6/6 security failing and 4/4 functional passing, oracle and its two
  check patches run below.

## Gate (this pass)

- static: only the missing `blind` pass patch (permitted; it is written after the build).
- nop: PASSED — 10 security tests all failing on the pinned tree, 21 functional passing.
- oracle: PASSED — 3/3 identical runs at reward 1.0.
- patches: PASSED — 13/13 declared outcomes, including the four per-concept `security_fail`
  checks (6/1/1/1 security failures, no functional failures), the three functional_fail shape
  checks, both upstream recall checks, the alternative fix (1.0) and the hardening fix (1.0).
- control `stk-kyverno-ghsacvq5-control`: PASSED all stages (static; nop 6 security failing / 10 functional passing; oracle 2/2 identical at 1.0; patches 2/2).

## Not verified / guesses

- `stacking/check_stack.py` requires `expect: "fail"` for concept and recall checks, while
  `builder/gate.py` accepts only `security_fail | functional_fail | pass` and rejects `fail`. The
  manifest follows the gate (the explicit acceptance target); the stacking checker therefore
  reports the expect-value mismatch on those entries. Not fixed locally because only tasks/ and
  build/ may be edited. The concept coverage itself is present: every concept has a
  `security_fail` check with `misses` set to that concept's trap id.
- T4 (empty substituted namespace falling back to "default") is not an independent security lever
  once the cross-namespace comparison exists: an empty name then resolves to the policy namespace
  (namespaced) and is refused if it differs. The empty-substitution cases are kept as shape tests
  of T3/T8, not as a fifth concept.
- T10 (GlobalContextEntry sharing) deliberately not built: the reader flags it as arguably
  by-design.
- Current-upstream state was read read-only at c659c1d1a3b: T2's credential attachment is
  unchanged; T3/T1 are fixed; the cleanup controller path described by T8 no longer exists at that
  location.
- `present_in_latest` for T8 is therefore "no" for the route as written, not a claim that the
  underlying wrong-policy wiring was fixed elsewhere.
- The control's `control_overbroad.patch` was regenerated in this pass so the refuse-all variant
  still compiles (the earlier generation left unused imports); it now shows 3 functional failures
  and all security tests passing, as declared.

## Files/gates

- environment image: golang:1.26.3-bookworm, pinned checkout, module and build caches warmed,
  history removed, fresh one-commit baseline, agent layer appended.
- verifier image: same toolchain and warm commands, go-junit-report installed, the credential
  fixture directory created writable by uid 1000.
- `tests/test.sh` runs the project's own tests for the affected packages before staging the hidden
  suites, so the hidden cleanup helpers never enter the project run.
- Reconstruction (second pass): the prepared `tasks/stk-kyverno-ghsacvq5` tree and
  `build/stk-kyverno-ghsacvq5/manifest.json` were missing at resume. The task tree was recovered
  from the gate's temporary copy (file contents verified identical to the work-tree test sources),
  `solution/fix.patch` restored from the recorded oracle patch, the manifests regenerated from the
  recorded builder script, and the control task and its two checks rebuilt. The files were then
  re-gated from scratch.

## Reconstruction pass (2026-10-23T03:01Z)

`stacking_restart.sh` (02:57) deleted `tasks/<slug>`, `tasks/<slug>-control` and `build/<slug>-control`
and the main manifest ahead of relaunching the batch. This pass restored the prepared task and
re-ran every stage from scratch:

- Main task tree restored from the gate's temporary copy at `/tmp/gate-c6vdoghs/stk-kyverno-ghsacvq5`
  (the copy the prior pass verified against the gated run); `solution/fix.patch` restored from the
  recorded oracle patch in the work dir (the temp copy had a check patch there). Manifest regenerated
  from the recorded builder script, with the blind-patch declaration the gate requires.
- Control task rebuilt from the same report and pinned tree: only the advisory's apiCall URLPath
  route in its suites and reference; control check patches regenerated (`control_malformed_identity`,
  `control_overbroad`).
- Local behavioural cross-check before the container stages (Go 1.27, warm module cache, pinned
  checkout): oracle passes all 10 security + 12 functional hidden tests and all project tests; the
  pinned tree fails all 10 security and passes all 12 functional; `alt_correct_fix` and `hardening`
  pass; every main check patch reproduces its declared outcome (6 concept/security patches:
  sec>0 fun=0; 3 functional patches: fun>0; both recall patches: sec>0 and fun>0). Both control
  patches reproduce theirs (security-only failure; functional failures).
- Harbor on this host rejects `no-network` when its 30 s egress-kernel probe is slow under shared
  load; stages were started through a probe-gated retry loop (`~/.tb-graders/cwe/work/.../run_stage.sh`),
  per the recorded shared-VM rule. The task's network mode was not changed.

### Stage results this pass

- static: PASSED (main and control).
- nop: PASSED (10 security tests fail on the pinned tree; 21 functional pass, including the
  project's own apicall/loaders/factories/cleanup tests).
- oracle: PASSED, 3/3 runs at reward 1.0.
- patches, first run (04:05Z): stopped at `malformed_identity.patch` because the project's own
  `cleanup::TestReconcile_ClampPastNextExecution` (a wall-clock assertion around the next cron
  minute, pinned upstream code) failed with "expected delay to next cron minute, got 493.29495ms"
  while the patch's intended security test failed correctly. That is a pre-existing clock race,
  not a task defect; it can zero a correct fix. `tests/test.sh` now runs the cleanup package's two
  deterministic project tests explicitly (`-run`) instead of the scheduler assertion, and keeps
  the same tests for every other package. The hidden cleanup suites (T8) are unchanged. The stage
  was re-run from the start after this fix.

- patches, second run (04:46Z): the four concept checks passed with functional all passing
  (rewards 0.4 / 0.9 / 0.9 / 0.9), then the stage hit the shared host's 30 s egress-probe infra
  flake at `reads_only` (no trial started). A full re-run could not fit the 3 h build-session
  budget, so the remaining nine checks were run through the gate's own `check_patches` code
  (same task tree, same `checks/*.patch`, same declared outcomes) in three parallel subsets.
  Outcomes are recorded below.
- `stacking/check_stack.py` requires the two recall checks to declare `expect: "security_fail"`,
  while `builder/gate.py` executes a `security_fail` check as "some security test fails AND every
  functional test passes". Both recall patches (upstream's A alone and A+B) genuinely regress a
  must-keep-working behaviour: upstream refuses every outbound service call for a namespaced
  policy, so `TestFunc_NamespacedPolicyExternalCallStillWorks` and
  `TestFunc_NamespacedPolicySuppliedCredentialPreserved` fail (sec 3/fun 2 and sec 1/fun 2 in the
  local runs). The only declaration the gate accepts for them is `functional_fail`; check_stack
  therefore reports exactly those two entries as non-conforming. The acceptance target named by
  the build prompt is `builder/gate.py`, and the manifest follows it.

### Patch-check evidence (all 13 declared outcomes)

Run on the real task tree with the manifest's `checks/*.patch` through gate.py's `check_patches`
(`run_patch_subset.py` only restricts the list passed to that same function).

| patch | declared | observed |
|---|---|---|
| miss_concept_apicall | security_fail | sec 6 / fun 0, reward 0.4 |
| miss_concept_service | security_fail | sec 1 / fun 0, reward 0.9 |
| miss_concept_configmap | security_fail | sec 1 / fun 0, reward 0.9 |
| miss_concept_cleanup | security_fail | sec 1 / fun 0, reward 0.9 |
| reads_only | security_fail | sec 1 / fun 0, reward 0.9 |
| malformed_identity | security_fail | sec 1 / fun 0, reward 0.9 |
| check_before_substitution | functional_fail | sec 0 / fun 1, reward 0.0 |
| adjacent_api | functional_fail | sec 0 / fun 3, reward 0.0 |
| upstream_first_fix | functional_fail | sec 3 / fun 2, reward 0.0 |
| upstream_fix | functional_fail | sec 1 / fun 2, reward 0.0 |
| alt_correct_fix | pass | reward 1.0 |
| hardening | pass | reward 1.0 |
| functional_overbroad | functional_fail | two container attempts aborted by the host egress-probe infra flake (no trial); local reproduction: sec 0 / fun 2 |

Both recall patches fail functional tests because upstream's A fix refuses every namespaced
policy's outbound HTTP call, which the task's must-keep-working clause forbids.

- functional_overbroad: after two host egress-probe aborts, the third attempt passed the gate's
  `check_patches` with `functional_fail` (sec 0 / fun 2, reward 0.0). All 13 declared check
  outcomes are therefore reproduced through the gate's own per-check code.
- Control task: static PASSED; nop PASSED (6 security fail / 10 functional pass); oracle PASSED
  (2/2 runs at reward 1.0). Its two patch checks were started at 05:47Z; the build session's
  3 h limit ended before their container run completed. Both were reproduced locally against the
  pinned tree through the same suites (control_malformed_identity: security-only failure with all
  functional passing; control_overbroad: 3 functional failures with all security passing).
end_utc: 2026-10-23T06:00:00Z

## Audit-fix pass (2026-10-24)

Source: `build/stk-kyverno-ghsacvq5/AUDIT-FIX-20261024.md` (post-run audit of v2; attribution
instruction-ambiguity). The conflict: the instruction forbids a namespaced policy reading
cluster-scoped data, while `TestFunc_NamespacedPolicyOwnNamespaceRecord` required the cluster-scoped
Namespace object to stay readable. Resolution per the project rule of 2026-10-20 (keep the
instruction; change test and reference).

- `tests/functional/zz_func_context_test.go`: `TestFunc_NamespacedPolicyOwnNamespaceRecord` ->
  `TestFunc_NamespacedPolicyOwnNamespaceResource`, reading `/apis/apps/v1/namespaces/team-a/deployments`
  (an ordinary namespaced resource) instead of `/api/v1/namespaces/team-a`.
- `tests/security/zz_sec_apicall_test.go`: added `TestSec_APICallOwnNamespaceObject` (the Namespace
  object for a namespaced policy is refused with no request made; any refusal accepted).
- `solution/fix.patch`: the URLPath guard now requires a namespaced resource inside the namespace
  (`^/api(s)?/.*?/namespaces/([^/]+)(/.*)?$` plus `matches[3] != ""`), so the cluster-scoped
  Namespace object is refused even when it names the policy's own namespace. ClusterPolicies keep
  unrestricted access (empty policy namespace skips the guard).
- `checks/upstream_namespace_object.patch`: the pre-change reference (allows the Namespace object),
  wired `security_fail`; locally it fails only `TestSec_APICallOwnNamespaceObject` with every
  functional test passing.
- `checks/alt_correct_fix.patch`, `checks/hardening.patch` and the three per-concept
  `miss_concept_{service,configmap,cleanup}.patch` carry the revised guard so they keep their
  declared outcomes (pass, pass, and one security failure each).
- Instruction unchanged (audit item 5), so the listing check (PASS, all four traps GENERAL) and the
  control instruction stay valid. `manifest.traps[T1]` shape and coupled/security test lists updated.
- `stacking/check_stack.py`'s expect conflict is resolved: `upstream_first_fix.patch` and
  `upstream_fix.patch` are now declared `security_fail` (their guardfix versions no longer refuse
  service calls; they leave 5 / 3 security tests failing with all functional passing).

### Local verification (pinned checkout, Go 1.27)

- pinned: all 11 security tests fail, all 12 functional pass.
- oracle: all 23 pass. `alt_correct_fix` and `hardening`: all 23 pass.
- `upstream_namespace_object`: 1 security fail (the object test), 0 functional fails.
- per-concept checks: `miss_concept_apicall` 7 / 0; `miss_concept_service`, `miss_concept_configmap`,
  `miss_concept_cleanup` 1 / 0 each.
- `reads_only`, `malformed_identity`: 2 / 0; `check_before_substitution`: 1 / 1;
  `adjacent_api`, `functional_overbroad`: 1 / 2; `upstream_first_fix` 5 / 0; `upstream_fix` 3 / 0.

### Gate on the final tree (2026-10-24)

- static: PASSED.
- nop: PASSED — 11 security tests all failing on the pinned tree, 20 functional passing
  (10 hidden vtesting + 2 hidden cleanup + 8 project test cases).
- oracle: PASSED — 3/3 runs, reward 1.0, identical results.
- patches: PASSED — all 14 file-backed checks as declared:
  miss_concept_apicall 7sec/0fun (0.3636); miss_concept_service, miss_concept_configmap,
  miss_concept_cleanup 1/0 each (0.9091); upstream_namespace_object 1/0 (0.9091); reads_only,
  malformed_identity 2/0 (0.8182); functional_overbroad 1sec/2fun (0.0);
  check_before_substitution 1/1 (0.0); adjacent_api 1/3 (0.0); upstream_first_fix 5/0 (0.5455);
  upstream_fix 3/0 (0.7273); alt_correct_fix and hardening reward 1.0.
  (`blind.patch` is absent and filtered, as before.)
- `stacking/check_stack.py stk-kyverno-ghsacvq5`: conforming (4 concepts, pattern H3b).
- The first patches attempt hit the known shared-host allowlist egress-probe flake
  (`network_mode='allowlist' is not supported…` at trial launch, no trial started); the stage was
  re-run through the probe-gated retry script (`run_stage.sh`) and passed on attempt 1. task.toml
  was not weakened.
