# stk-cms-ghsa7jx7 — build notes

start_utc: 2026-10-26T02:07:57Z (build job start)
end_utc: 2026-10-26T04:07Z

## Stack

Pinned commit c17f497e5e40d07a376ae94334855179500f312d (Craft CMS 4.16.16 line) is the
first parent of ec43c497edde, the 4.x-line commit of advisory A's first fix
(GHSA-255j-qw47-wjh5, authenticated RCE via a maliciously configured Yii Behavior).
The same change landed on 5.x as 27f55886098b and was amended by 6e608a1a5bfb
(cleanse after the settings merge). Advisory B (GHSA-7jx7-3846-m7w7) was fixed on the
4.x line by 395c64f0b80b, which descends from the pin and cleanses the field layout
save service; the task is H3b.

## Levers (one line each)

- T1 (A, advisory route; mimo/hard): the two control-panel layout settings actions build a
  tab object and an element through the posted config and the parsed settings namespace; both
  must refuse a class-bearing key while legitimate tab/element settings keep rendering.
  src/controllers/FieldsController.php:442-482; published fix ec43c497edde. Reason to
  dismiss: structural admin JSON and the element type check look like validation.
- T2 (A+B, advisory route; both/hard): the field layout save service decodes one nested layout
  document and builds it; the refusal must be recursive because tabs and elements are object-
  ified from sub-arrays. src/services/Fields.php:1247-1287; published fixes ec43c497edde /
  395c64f0b80b. Reason to dismiss: one document, so a top-level key check looks sufficient.
- T3 (B, uncovered_upstream; deepseek): the layout and tab config factories build through the
  model constructor, which the published request-boundary fixes never touch, so stored project
  configuration can name a class. src/models/FieldLayout.php:172-187,
  src/models/FieldLayoutTab.php:43-47. Reason to dismiss: project config is developer-supplied.
- T4 (B, uncovered_upstream; mimo): the public element-duplication API applies caller attributes
  through the configure loop and instantiates a behavior named in the behavior list; it must
  refuse class-bearing values while the application's own draft/revision behavior objects keep
  attaching. src/services/Elements.php:1575-1594,1716-1721. Reason to dismiss: public plumbing
  whose core callers pass fixed draft/revision configuration.

Concepts (reference-fix edit sites): T1, T2, T3, T4 — four independent concepts, one security_fail
miss check each. DeepSeek-type: T3. MiMo-type: T1 and T4.

## Verified

- Every route was reproduced behaviourally on the pinned tree in a real `craft\web\Application`
  (isInstalled=false, no database) before the tests were written: both controller actions, the
  layout save service at three nesting depths, the layout/tab factories, and duplication with a
  behavior class string, a behavior config array, an attribute key and a site-attribute key.
- Hidden security: 14 tests, all fail on the pinned tree and pass on the reference fix.
- Hidden functional: 7 tests, all pass on the pinned tree and on the reference fix.
- Check patches were each applied to the pinned tree and run against both suites; results:
  fix 14/14+7/7; miss_controller_config 3 security failures; miss_layout_save 3;
  miss_factories 4; miss_duplicate 4; upstream_first_fix 11; upstream_fix 8;
  sf-crash-as-refusal 3; sf-cleanse-before-merge 1; ff-refuse-all 2 functional errors;
  ff-craft-create-object 1 functional failure; pass-hardening and pass-alt 14/14+7/7.
- The control task uses only the advisory route (the layout save service) with four input
  shapes, plus all seven functional tests; its reference is the 4.x published fix for that route.
- Pattern B register rows appended for T3 and T4; both routes are still unprotected in
  origin/5.x (checked 2026-10-26), so `present_in_latest` is yes.

## Could not verify

- The project's own Codeception suite was not run: it requires a MySQL server and the dev
  Composer dependencies, and the task's offline verifier deliberately runs without a database.
  The affected classes were exercised through the real application instead.
- Whether a real install has a gadget class usable in the behavior position was not tested; the
  tests observe the protected outcome (construction/attachment of the named class), not RCE.
- The exact relation between the 5.x commits 27f55886098b/6e608a1a5bfb and the 4.x commit
  ec43c497edde is inferred from identical source changes; the 5.x commits cannot apply to the
  4.x tree.

## Report

`pipelines/stacking/out/reader/h3-ghsa-7jx7-3846-m7w7.json` does not exist; the reader record
used is `pipelines/stacking/out/reader-ds/h3-ghsa-7jx7-3846-m7w7.json`, which is the same
candidate id and content produced by the DeepSeek reader run.

## Gate (stacked task)

- static: PASSED.
- nop: PASSED — 14 security tests failing on the pinned tree, 7 functional tests passing.
- oracle: PASSED — 3/3 runs at reward 1.0 with identical results.
- patches: PASSED — 12/12 declared outcomes: four per-concept `security_fail` checks
  (3/3/4/4 security failures, no functional failures), 2 `functional_fail` checks,
  2 further `security_fail` shape checks, both upstream recall checks (11 and 8 security
  failures), and the hardening and alternative fixes both at reward 1.0.
- `checks/blind.patch` is intentionally absent; it is produced after the first gate.

The shared VM's Docker daemon intermittently stalled compose teardown; each stalled stage was
unblocked by terminating that stage's own stuck `docker compose` process (no task or test change).
