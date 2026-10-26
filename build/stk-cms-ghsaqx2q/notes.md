# stk-cms-ghsaqx2q build notes

- Start: 2026-10-26T02:23:18Z (from `build/stk-cms-ghsaqx2q/start_utc.txt`)
- End: (filled when the gate finishes)
- Pinned: `craftcms/cms` `cfa8266e1455bd906bb41a70b23869f8afb7365c` — the 4.x line, parent of the
  GHSA-7jx7-3846-m7w7 fix.
- Advisories: GHSA-7jx7-3846-m7w7 (fix `395c64f0b80b`), GHSA-qx2q-q59v-wf3j (fix `d37389dbffaf`,
  which lands on the later 5.x line).

## Levers (one line each)

- **T1 — reported, both.** A posted field-layout definition carrying a behavior/event-handler entry
  at the layout or tab level: `Fields::assembleLayoutFromPost()` decodes the `fieldLayout` body
  parameter and hands it to `Craft::createObject()` without a cleanse
  (`src/services/Fields.php:1283-1287`; reported route `src/controllers/SectionsController.php:347`).
- **T2 — MiMo, how-type.** A tab whose `elements` value arrives as a JSON string:
  `FieldLayoutTab::__construct()` decodes it after the outer layout has already been cleansed, so
  the element configs still carry the wiring (`src/models/FieldLayoutTab.php:115-122`).
- **T3 — DeepSeek, far site.** The project-config handlers call `FieldLayout::createFromConfig()`,
  which builds the layout and its tabs with `new` + `Model::__construct`; the posted-path cleanse
  never runs (`src/models/FieldLayout.php:172-187`, `src/services/Users.php:1496-1500`).
- **T4 — DeepSeek, uncovered route.** A native element-source definition whose `criteria` carry the
  wiring: `ElementIndexesController::elementQuery()` configures the query with them, while the
  request criteria a few dozen lines below are already cleansed
  (`src/controllers/ElementIndexesController.php:576-578`; `src/services/ElementSources.php:75-113`).

## Verified

- Each lever reproduces on the pinned tree through a real entry point (the marker behavior/handler is
  instantiated): posted layout through `SectionsController::actionSaveEntryType()`; project config
  through `ProjectConfig::set('users.fieldLayouts', ...)`; element index through
  `ElementIndexesController::beforeAction()`.
- Each `miss_*.patch` (the oracle minus one concept) leaves exactly that concept's security tests
  failing and every other security test plus all functional tests passing: m1 4 failures, m2 2,
  m3 2, m4 1.
- `upstream_fix.patch` (the published fix A alone) leaves T2/T3/T4 failing (5 security failures) with
  all functional tests passing, so the stack adds work beyond upstream.
- `hardening.patch` scores 9/9 security and 5/5 functional; `overbroad_refuse_elements.patch` and
  `wrong_refuse_all.patch` break functional tests.
- The project's own unit test for the affected helper runs under Codeception:
  `ComponentHelperTest` — OK (29 tests, 35 assertions) against a freshly installed Craft schema.
- The control task passes the static gate; its patch checks behave as declared (miss → 4/4 security
  fail, over-broad → 3 functional errors, hardening → security and functional pass).

## Could not verify / unknowns

- GHSA-qx2q's published fix (`d37389dbffaf`) is on the 5.x line and targets
  `src/controllers/EntryTypesController.php`, which does not exist at the pinned 4.x commit; the 4.x
  line has no equivalent sink. The recall patch therefore applies fix A only.
- No gadget-chain feasibility run was made; CWE-470 exploitability is inferred from Yii's handling of
  `as <name>` / `on <name>` keys in `Component::__set()` and the marker behavior.
- The relation-field sink (`src/fields/BaseRelationField.php:653-654`) shares T4's mechanism but is
  not separately tested; the hardening patch cleanses it defensively.
- The `duplicateElement()` behaviors lever described in the single-advisory reader record was not
  used: it is a public service API with no core request route.
- The six sibling `assembleLayoutFromPost()` controllers are not separately tested: one cleanse at the
  service closes them all, so they are the same concept as T1.
- Out of scope: the other advisories in the repository's changelog; nothing was built on them.

## Gate

(filled when the gate finishes)
