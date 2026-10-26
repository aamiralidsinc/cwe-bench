# stk-tomcat-ghsap26v — build notes

- Start: 2026-10-26T02:04:59Z (build-run start recorded in `start_utc.txt`).
- End: 2026-10-26T04:00Z (UTC), before the first gate run.
- Pinned: apache/tomcat `b39a8d8272b5f3fdf024e7cc6b6f4c2b1a97955a` (7.0.10-dev, 2011-03-02,
  the 7.0.x commit immediately before the CVE-2011-1088 series; the trunk parent of the same
  change is `2449df2f`, and the two trees are identical for every file the fix touches).
- Advisories: GHSA-mg4v-rf8p-ghqq (CVE-2011-1088) and GHSA-p26v-97vp-jcx6 (CVE-2011-1183,
  the incorrect-fix follow-up). H3b: the reference fix is A+B; `checks/upstream_first_fix.patch`
  is A alone and must fail; `checks/upstream_fix.patch` is A+B and must also fail because the
  stack's uncovered routes are still open.

## Levers (one line each)

1. **T1 — action rules on a programmatically registered servlet are never read** (deepseek,
   advisory route). Sites: `StandardContext.dynamicServletAdded/dynamicServletCreated`,
   `StandardWrapper.load`, `AuthenticatorBase.invoke`. Dismissal: annotations are convenience;
   the descriptor or the application is authoritative. Reference: scan a created servlet's
   annotation before the first constraint check (and on load for descriptor-declared servlets).
2. **T2 — no authenticator exists when no constraint was visible at CONFIGURE_START** (both,
   published far site). Sites: `ContextConfig.authenticatorConfig`, `Tomcat.FixContextListener`.
   Dismissal: only API-registered constraints are affected and the application can install its
   own valve. Reference: install an authenticator unless the deployment is metadata-complete and
   declares no constraints, and add one in the embedded launcher.
3. **T3 — registration rules are computed from the mappings known when they are set** (mimo,
   `uncovered_upstream`, how-type). Sites: `ApplicationServletRegistration.addMapping`,
   `StandardContext.addServletSecurity`, `SecurityConstraint.createConstraint`. Dismissal:
   addMapping is an initialisation-time call and normal applications map first. Reference: keep
   the element on the registration, re-apply it on every added pattern, and mark dynamically
   created collections as not-from-descriptor. Coupled: the deferral trap — computing the
   constraints at the end of start-up pushes them past the authenticator decision.
4. **T6 — the form-login action is exempted from role checks by a path suffix** (both,
   `uncovered_upstream`, shape trap). Sites: `RealmBase.hasResourcePermission`,
   `AuthenticatorBase.invoke`. Dismissal: the action is the login endpoint and must stay outside
   constraints; no servlet is normally mapped there. Reference: compare the exact action path.

## What was verified (behavioural, on the pinned copy and the reference)

- Every planned request shape was run first as a standalone probe against a compiled pinned tree
  and again against the compiled reference tree: annotation via `createServlet` (webapp and
  embedded), descriptor-declared annotation, role and method constraints, `setServletSecurity`
  before and after `addMapping`, dual mappings, and a real form-login session reaching a servlet
  mapped under the action name. All security shapes flip from 200+marker to 4xx+no-marker; the
  coupled positives stay 200.
- The 11 hidden security tests and 11 hidden functional tests were run against the pinned tree
  (11 fail / 11 pass), the reference (22 pass), and each check variant. The two project test
  classes (`TestStandardContext`, `TestContextConfigAnnotation`, 12 tests) pass on the pinned
  tree, the reference and every check variant.
- The complete verifier (`tests/test.sh` under the built tests image) was run against the pinned
  tree (reward 0.0, 11 security failures, 23 functional passes) and the reference (reward 1.0,
  34/34).
- `present_in_latest` for T3 and T6 was checked read-only against current upstream: modern
  `ApplicationServletRegistration.addMapping` re-applies the stored element, and modern
  `RealmBase.hasResourcePermission` no longer carries the form-action exemption.

## Gate results

- `static`: PASSED.
- `nop`: PASSED — 11 security tests (all fail on the pinned tree) and 24 functional tests (12 hidden + 12 project, all pass); trial
  `stk-tomcat-ghsap26v__vy8grLd`.
- `oracle` and `patches`: the Harbor jobs were still building images under the shared VM's load when the
  build session's remaining budget ran out; their stage results are not in `gate_report.partial.json`.
  The same checks were validated end-to-end with the verifier's own image (`tests/test.sh` against a
  copied pinned tree with each patch applied): reference and control reference `reward 1.0`;
  `alt_correct_fix` `1.0` (35/35); `hardening` `1.0` (35/35); `adjacent_api` `0.0` with one functional
  failure; `functional_overbroad` (11 security and 7 functional failures through the verifier) and `crash_as_refusal` (3 hidden functional failures) break functional tests; `firstfix` gives four
  security failures with every functional test passing.
- Pre-gate matrix (hidden suites plus, where noted, the project tests): `firstfix`/`upstream` 4 security
  failures with functional all passing; `miss_annotation` 5; `miss_authenticator` 10; `miss_concept_mapping`
  3; `miss_concept_formaction` 1; `alt_correct_fix` and `hardening` all pass; `functional_overbroad`,
  `crash_as_refusal` and `adjacent_api` each break functional tests; `noop` leaves all 11 security tests
  failing. The 12 project tests pass for `firstfix`, `upstream`, `miss_annotation`, `miss_authenticator`,
  `miss_concept_mapping` and `miss_concept_formaction`.

## What could not be verified

- The exact advisory-to-commit mapping could not be read from a local advisory database; it was
  established from the GitHub advisory API (CVE ids, affected and fixed versions) and from the
  fetched commit messages (`13fe121edb6f` says it completes CVE-2011-1088;
  `b7b5c63a932f` says "This includes the fix for CVE-2011-1183").
- The prompt's reader-record path (`pipelines/stacking/out/reader/h3-ghsa-p26v-97vp-jcx6.json`)
  does not exist in this checkout; the record is present at
  `pipelines/stacking/out/reader-ds/h3-ghsa-p26v-97vp-jcx6.json` and the manifest points there.
- The reader's T1/T2/T3/T6 evidence lines were used as a lead only. T5 and T7 were not built
  (T7's exact-directory welcome-file shape was not reproduced through a real entry point in the
  time budget; T5 is folded into T3's `setFromDescriptor` bookkeeping).

## Outside this advisory's scope

- Tomcat's JSP compilation path (JDT/ECJ) and the clustering packages are excluded from the
  build helper; nothing in this task's protection depends on them.

## Notes on the build

- The helper compiles the `java/` tree with `-source 1.6` because the snapshot's bundled XML
  parser cannot read newer class-file versions.
- The verifier and the agent image use the same JDK 8 base and the same compiler settings; the
  verifier's build script is a separate implementation with the same flags.
