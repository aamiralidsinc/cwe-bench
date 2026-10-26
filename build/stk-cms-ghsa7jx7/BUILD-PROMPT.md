# Build one security-fix benchmark task (build-v1)

## What this is
We build a security-fix benchmark from published, already-fixed advisories in open-source projects.
You build ONE task, from the advisory below.

The task pins the project at the commit just before the published fix and gives a solver agent that
code plus a short problem report (`instruction.md`). Hidden behavioural tests then score the
solver's fix. The tests check that the flaw is closed, using harmless inputs and markers, and that
legitimate use still works.

Everything stays on this machine. Describe each mechanism in one line in notes and reports; the
tests hold the detail, so never write exploitation steps out in prose. Stay inside this advisory's
own protection, in this repository, at the pinned commit. Note anything outside that scope in one
line in your report, and do not build on it.

Project root: `/home/mara/cwe-bench`. Task: `stk-cms-ghsa7jx7`. Pattern: `A+B`. Track: `stacked`.

## Goal and acceptance
- **The bar.** Two target models (DeepSeek V4.1 Flash, MiMo-V2.6-Pro) must each fail all 3
  finished attempts because of their own judgement.
- **Fairness.** Everything the tests require must be findable from `instruction.md` plus the code,
  or be standard expert knowledge. A careful engineer who knows where to look fixes it in about
  45 minutes.
- **What never counts as a failure:** timeouts, and runs cut by API or network errors.
- **Proof.** A task is built only when the gate passes. A task that misses the bar is reported as
  such, never shipped weaker.

## Inputs
- Advisory: GHSA-255j-qw47-wjh5; GHSA-7jx7-3846-m7w7
- Pinned (vulnerable) commit: c17f497e5e40d07a376ae94334855179500f312d. Published fix: 27f55886098b, 6e608a1a5bfb, ec43c497edde, 395c64f0b80b.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "candidate_id": "h3-ghsa-7jx7-3846-m7w7",
 "pattern": "H3b",
 "repo": "craftcms/cms",
 "pinned_commit": "c17f497e5e40d07a376ae94334855179500f312d",
 "protections": [
  "Component::createComponent() validates that the class exists, implements ComponentInterface and the expected interface, and belongs to an enabled plugin, and strips every `on X`/`as X` key recursively from the config before Craft::createObject() (src/helpers/Component.php:36-78,87-99,112-139).",
  "Craft::createObject() rejects a config that specifies both `class` and `__class`, so the class a caller validated cannot be swapped for another at instantiation (src/Craft.php:54-61).",
  "Request-derived condition/criteria configs are passed through Component::cleanseConfig() before Craft::configure()/Conditions::createCondition() (src/controllers/ElementIndexesController.php:415-422,592-606,620; src/controllers/ConditionsController.php:44-49; src/controllers/SystemSettingsController.php:336).",
  "Field layout elements are instantiated only when `type` is a FieldLayoutElement subclass and are kept only when their plugin is enabled (src/services/Fields.php:1263-1274; src/models/FieldLayoutTab.php:286-305).",
  "Field handles must match [a-zA-Z][a-zA-Z0-9_]* on the model-save path, via HandleValidator in Field::defineRules() and Fields::saveField() (src/validators/HandleValidator.php:24,67-89; src/base/Field.php:276-362; src/services/Fields.php:845).",
  "Element, condition, widget and field classes must be subclasses of the expected interfaces before they are instantiated (src/controllers/BaseElementsController.php:46-59; src/controllers/ElementsController.php:2061-2067; src/services/Conditions.php:50,123; src/helpers/Component.php:36-78)."
 ],
 "traps": [
  {
   "id": "T1",
   "mechanism": "M1",
   "origin": "advisory_route",
   "locations": [
    "src/services/Fields.php:1247-1250",
    "src/services/Fields.php:1283-1287",
    "src/controllers/SectionsController.php:346-349",
    "src/controllers/VolumesController.php:168-171",
    "src/controllers/CategoriesController.php:168-171",
    "src/controllers/TagsController.php:125-128",
    "src/controllers/GlobalsController.php:76-79",
    "src/controllers/UsersController.php:2143-2146",
    "src/controllers/AddressesController.php:104-107"
   ],
   "reason_to_dismiss": "The posted value is structural layout JSON (tabs/uid/type) and Craft::createObject already rejects a config that specifies both `class` and `__class`; every caller is an admin-only settings screen, so the config reads as trusted structural data rather than an attacker-chosen class list.",
   "distance": {
    "files": 2,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "easy",
   "tier_mimo": "easy",
   "type": "neither",
   "evidence": [
    "src/services/Fields.php:1283-1287 \u2014 assembleLayoutFromPost() JSON-decodes the request body param `fieldLayout` and hands the resulting array straight to createLayout(); there is no Component::cleanseConfig() call.",
    "src/services/Fields.php:1247-1250 \u2014 createLayout() forces only `class` = FieldLayout and passes every other posted key to Craft::createObject(), which applies them with Yii::configure and therefore treats an `as <name>` key as a behavior definition.",
    "src/base/Model.php:67-88 \u2014 when the same config is applied through a Model constructor, App::configure() assigns each key with `$object->$name = $value`, which reaches Yii's Component::__set and its `as ` behavior branch.",
    "src/helpers/Component.php:87-99 \u2014 cleanseConfig() is the guard that strips `on X`/`as X` keys, and src/helpers/Component.php:138 shows it is applied only inside createComponent(), not on this path.",
    "src/controllers/SectionsController.php:346-349, src/controllers/VolumesController.php:168-171, src/controllers/CategoriesController.php:168-171, src/controllers/TagsController.php:125-128, src/controllers/GlobalsController.php:76-79, src/controllers/UsersController.php:2143-2146 and src/controllers/AddressesController.php:104-107 all call assembleLayoutFromPost() from authenticated CP save actions.",
    "src/controllers/ElementIndexesController.php:606 and :620 show the accepted pattern for request-derived config (`Craft::configure($query, Component::cleanseConfig($criteria))` and `createCondition(Component::cleanseConfig(...))`), which the layout save path does not follow."
   ]
  },
  {
   "id": "T2",
   "mechanism": "M1",
   "origin": "advisory_route",
   "locations": [
    "src/services/Fields.php:1263-1273",
    "src/controllers/FieldsController.php:459-467",
    "src/controllers/FieldsController.php:475-482",
    "src/models/FieldLayoutTab.php:286-289"
   ],
   "reason_to_dismiss": "createLayoutElement() already validates that `type` is a FieldLayoutElement subclass and throws otherwise, so the config looks validated; the remaining keys are ordinary element settings and the action only previews them.",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "easy",
   "tier_mimo": "medium",
   "type": "neither",
   "evidence": [
    "src/services/Fields.php:1265-1273 \u2014 the only check is `is_subclass_of($type, FieldLayoutElement::class)`; after setting `class`, the whole config (including any `as <name>` key) goes to Craft::createObject() with no cleanse.",
    "src/controllers/FieldsController.php:459-467 \u2014 actionApplyLayoutElementSettings() calls createLayoutElement($this->_fldComponentConfig()) directly from a POST request.",
    "src/controllers/FieldsController.php:475-482 \u2014 _fldComponentConfig() takes the required body param `config` and array_merges it with parse_str($settings), so attacker-chosen top-level keys reach createLayoutElement().",
    "src/models/FieldLayoutTab.php:286-289 \u2014 setElements() routes every array element config from a posted fieldLayout through the same createLayoutElement() sink.",
    "src/helpers/Component.php:87-99 \u2014 the recursive cleanser exists but is not called on any of these paths."
   ]
  },
  {
   "id": "T3",
   "mechanism": "M2",
   "origin": "uncovered_upstream",
   "locations": [
    "src/models/FieldLayout.php:172-187",
    "src/models/FieldLayoutTab.php:43-47",
    "src/base/Model.php:67-88",
    "src/helpers/App.php:1450-1454",
    "src/services/Sections.php:1164-1170"
   ],
   "reason_to_dismiss": "Project config is authored by developers and applied from the console/git, is not a CP request body, and every value there is expected to be a plain layout definition; a solver can argue the advisory is about request configs and that this factory is trusted, developer-supplied data.",
   "distance": {
    "files": 3,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "xhard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "src/models/FieldLayout.php:172-187 \u2014 createFromConfig() removes `tabs` and calls `new self($config)` (line 175) and FieldLayoutTab::createFromConfig() (line 179); nothing is cleansed and Craft::createObject() is not involved, so its `__class`/`class` check does not apply.",
    "src/models/FieldLayoutTab.php:43-47 \u2014 FieldLayoutTab::createFromConfig() ends in `new self($config)` (line 46).",
    "src/base/Model.php:67-88 \u2014 the Model constructor calls App::configure($this, $config) (line 84) for every key, including `as <name>` keys.",
    "src/helpers/App.php:1450-1454 \u2014 App::configure() is a plain `$object->$name = $value` loop, so unknown keys reach Yii Component::__set and its behavior branch.",
    "src/services/Sections.php:1164-1170 \u2014 the entry-type project-config handler passes `reset($data['fieldLayouts'])` (unvalidated project-config data) to FieldLayout::createFromConfig(); the same pattern is at src/services/Categories.php:344-350, src/services/Volumes.php:344-350, src/services/Globals.php:353-359, src/services/Tags.php:260-266, src/services/Users.php:1496-1500, src/services/Addresses.php:433-438 and src/services/Matrix.php:318-327."
   ]
  },
  {
   "id": "T4",
   "mechanism": "M4",
   "origin": "uncovered_upstream",
   "locations": [
    "src/controllers/FieldsController.php:442-449",
    "src/controllers/FieldsController.php:475-482",
    "src/models/FieldLayoutTab.php:43-47",
    "src/base/Model.php:67-88"
   ],
   "reason_to_dismiss": "This sibling action only deals with a tab name and sort order, so it looks like a harmless form preview; the layout-element action is the one that takes a class `type`, and a solver who hardens that action will not look here.",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "medium",
   "tier_mimo": "hard",
   "type": "mimo",
   "evidence": [
    "src/controllers/FieldsController.php:442-449 \u2014 actionApplyLayoutTabSettings() executes `new FieldLayoutTab($this->_fldComponentConfig())` on POST input with no type check and no cleanse.",
    "src/controllers/FieldsController.php:475-482 \u2014 _fldComponentConfig() merges the posted `config` array into the tab config, so an `as <name>` key reaches the Model constructor.",
    "src/models/FieldLayoutTab.php:43-47 and src/base/Model.php:67-88 \u2014 the tab is built through Model::__construct -> App::configure -> Yii Component::__set, the same behavior branch as T3, but on a request-reachable action rather than project config.",
    "src/services/Fields.php:1265-1269 \u2014 the element-side action's type check is not reached from this action, so a fix copied to createLayoutElement() leaves this route open."
   ]
  },
  {
   "id": "T5",
   "mechanism": "M8",
   "origin": "advisory_route",
   "locations": [
    "src/models/FieldLayout.php:308-324",
    "src/models/FieldLayoutTab.php:280-306",
    "src/services/Fields.php:1210-1215"
   ],
   "reason_to_dismiss": "The posted layout document is one nested array, so a top-level check on the keys of the config passed to Craft::createObject() looks like it covers the whole request; the tabs and elements are only turned into objects later, from their own sub-arrays.",
   "distance": {
    "files": 2,
    "packages": 0
   },
   "protection_state": "weak",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "mimo",
   "evidence": [
    "src/models/FieldLayout.php:308-324 \u2014 setTabs() turns each array entry into `new FieldLayoutTab($tab)` (line 318) after prefixing `layout`; a nested `as <name>` key in tabs[i] is applied by Model::__construct, not by the top-level config loop.",
    "src/models/FieldLayoutTab.php:280-306 \u2014 setElements() turns each array entry into createLayoutElement($layoutElement) (line 289), so nested element configs are instantiated from a different sub-array than the one the layout config check sees.",
    "src/services/Fields.php:1210-1215 \u2014 _createLayoutTabFromRow() JSON-decodes the tab `settings` column and array_merges it into the constructor row, showing that tab construction also has a persisted-config input path.",
    "src/helpers/Component.php:94-96 \u2014 cleanseConfig() is recursive, so the fix is correct only if the solver reuses this helper on the whole layout config; a one-level unset leaves the nested tabs/elements reachable."
   ]
  },
  {
   "id": "T6",
   "mechanism": "M6",
   "origin": "uncovered_upstream",
   "locations": [
    "src/Craft.php:289-305",
    "src/Craft.php:326-352",
    "src/Craft.php:358-372",
    "src/services/Fields.php:1649-1662",
    "src/services/Fields.php:909-919",
    "src/services/Matrix.php:310-313"
   ],
   "reason_to_dismiss": "Field handles are validated by HandleValidator on the normal Field save path and the generated class is internal generated code, so the handle column looks like trusted data; the advisory text talks about attached behavior configs, not about the generator.",
   "distance": {
    "files": 3,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "xhard",
   "tier_mimo": "hard",
   "type": "both",
   "evidence": [
    "src/Craft.php:289-305 \u2014 _generateCustomFieldBehavior() interpolates `$handle` raw into the method docblock (`@method $this $handle(...)`), into the single-quoted `'$handle' => true` handles array, and into the property declaration `public \\$$handle;`.",
    "src/Craft.php:326-334 \u2014 the generated source is written to the compiled-classes directory and included, and src/Craft.php:349-352 evaluates the same source with eval() when not writing, so a handle that breaks out of the string or property context is executed on the next request.",
    "src/Craft.php:358-372 \u2014 _fields() reads handles straight from the fields table with no validation, so the generator trusts whatever handle is stored.",
    "src/services/Fields.php:909-919 \u2014 handleChangedField() passes project-config data to applyFieldSave() without running the Field model's rules.",
    "src/services/Fields.php:1649-1662 \u2014 applyFieldSave() assigns `$fieldRecord->handle = $data['handle']` and calls save(false), so a handle that HandleValidator would reject is persisted; src/services/Matrix.php:310-313 does the same for matrix block fields.",
    "src/validators/HandleValidator.php:24,67-89 and src/base/Field.php:276-362 show the [a-zA-Z][a-zA-Z0-9_]* guard that only the model-save path (src/services/Fields.php:845) enforces."
   ]
  },
  {
   "id": "T7",
   "mechanism": "M11",
   "origin": "injection_room",
   "locations": [
    "src/services/Elements.php:1575-1594",
    "src/services/Elements.php:1716-1721",
    "src/services/Drafts.php:153-166",
    "src/services/Revisions.php:148-162"
   ],
   "reason_to_dismiss": "duplicateElement() is a public service method whose only core callers pass fixed draft/revision behavior configs, and drafts and revisions genuinely depend on the attached DraftBehavior/RevisionBehavior, so the `behaviors` key reads as internal plumbing.",
   "distance": {
    "files": 2,
    "packages": 0
   },
   "protection_state": "weak",
   "tier_deepseek": "medium",
   "tier_mimo": "hard",
   "type": "mimo",
   "evidence": [
    "src/services/Elements.php:1575 \u2014 duplicateElement() removes `behaviors` from the caller-supplied $newAttributes and src/services/Elements.php:1588-1594 then calls `$mainClone->attachBehavior($name, $behavior)` for every entry, cloning Behavior objects and passing anything else (a class string or a config array) straight to Yii.",
    "src/services/Elements.php:1581-1586 and :1716-1721 \u2014 both clones are also configured with `Craft::configure($clone, ArrayHelper::merge($newAttributes, $siteAttributes))`, so an `as <name>` key in $newAttributes or $siteAttributes attaches a behavior even if the `behaviors` key is clean.",
    "src/services/Drafts.php:157-166 and src/services/Revisions.php:151-162 \u2014 the must-keep-working values: draft and revision creation rely on `$newAttributes['behaviors']['draft'|'revision']` carrying DraftBehavior/RevisionBehavior with their creator/name/notes settings.",
    "src/services/Elements.php:1544-1573 \u2014 the method is public API and accepts arbitrary $newAttributes, so any plugin forwarding request data reaches the sink; core callers (src/controllers/ElementsController.php:1225-1227, src/services/Matrix.php:924, src/services/Revisions.php:162, src/services/Drafts.php:166) pass fixed arrays."
   ]
  },
  {
   "id": "T8",
   "mechanism": "M1",
   "origin": "injection_room",
   "locations": [
    "src/services/Elements.php:858-882",
    "src/web/twig/variables/CraftVariable.php:145-260",
    "src/models/FieldLayout.php:402-423",
    "src/models/FieldLayout.php:431-463"
   ],
   "reason_to_dismiss": "These configs are produced by Craft's own services or by plugin event handlers, not directly by a request body, so they look internal and out of scope for an advisory about request-supplied behavior config.",
   "distance": {
    "files": 2,
    "packages": 0
   },
   "protection_state": "weak",
   "tier_deepseek": "hard",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "src/services/Elements.php:858-882 \u2014 getElementById's criteria are applied with `Craft::configure($query, $criteria)` (line 880) without cleanseConfig; any caller forwarding request criteria reaches the behavior branch of the query object.",
    "src/web/twig/variables/CraftVariable.php:145-260 \u2014 the craft.entries/categories/... query helpers call Craft::configure($query, $criteria) on template-supplied criteria without cleansing (e.g. lines 152,165,178,191,205,218,242,255).",
    "src/models/FieldLayout.php:402-423 and :431-463 \u2014 getAvailableNativeFields() and getAvailableUiElements() call Craft::createObject($field)/Craft::createObject($element) on event-provided configs with no cleanseConfig, so a DefineFieldLayout* handler that forwards stored config instantiates whatever class it names.",
    "src/helpers/Component.php:87-99 \u2014 the same missing application of the established guard."
   ]
  }
 ],
 "independent_groups": [
  [
   "T1",
   "T5"
  ],
  [
   "T2"
  ],
  [
   "T3",
   "T4"
  ],
  [
   "T6"
  ],
  [
   "T7"
  ],
  [
   "T8"
  ]
 ],
 "history": {
  "a_fix_leaves_b_open": null,
  "b_in_code_a_wrote": null,
  "masking": [
   "A fix at Craft::createObject() (or in Fields::createLayout() with the recursive Component::cleanseConfig()) closes T1/T5 and the createLayoutElement() part of T2, but the Model-constructor route (T3) and the direct `new FieldLayoutTab()` tab action (T4) bypass Craft::createObject entirely, so a request test against the layout editors can pass while project config and the tab action still attach behaviors.",
   "A fix in Model::__construct()/App::configure() closes T3/T4 and nested tab construction, but Craft::createObject() applies its config after construction with Yii::configure (not through App::configure), so T1/T2 remain reachable; the two instantiation chokepoints mask each other.",
   "Once the config paths are cleansed, the generated-CustomFieldBehavior handle injection (T6) becomes the only remaining CWE-470 code-execution path in this subsystem, so a passing behavior-attachment test suite hides it.",
   "T6 only becomes reachable through project config after Fields::applyFieldSave() accepts an unvalidated handle; a test that only exercises the posted field-save action (validated at src/services/Fields.php:845) will not see it."
  ],
  "dependency_bump_fix": false,
  "in_repo_fix_possible": true
 },
 "conflicts": [
  {
   "a": "T1",
   "b": "T2",
   "what": "The tempting single fix is to cleanse inside Craft::createObject() (src/Craft.php:54-61). That breaks trusted config-driven components: Craft::createObject() is intentionally used to build app components from config/app.php:221-253 and config/app.web.php:10-34, where `on <event>`/`as <behavior>` keys are legitimate Yii configuration. The safe fix has to be at the request boundaries (the field-layout factories/actions), which is why T1 and T2 are separate fix sites."
  },
  {
   "a": "T3",
   "b": "T7",
   "what": "A blanket rule that Model::__construct()/App::configure() must never honor `as ` keys (the natural way to close T3/T4) is adjacent to the draft/revision behavior plumbing in Elements::duplicateElement() (src/services/Elements.php:1575-1594); drafts and revisions must keep attaching DraftBehavior/RevisionBehavior or getIsDraft()/getIsRevision() and the draft/revision edit flows break (src/services/Drafts.php:157-166, src/services/Revisions.php:151-162)."
  }
 ],
 "fairness_risks": [
  "Must-keep-working: app and plugin component configs legitimately use Yii's `on X`/`as X` keys with Craft::createObject()/config files (src/config/app.php:221-253, src/config/app.web.php:10-34), so a security rule phrased as 'no `as ` key may ever reach object configuration' contradicts a documented extension point and would break trusted event-handler/behavior configs.",
  "Must-keep-working: drafts and revisions depend on Elements::duplicateElement() attaching DraftBehavior/RevisionBehavior through $newAttributes['behaviors'] (src/services/Drafts.php:157-166, src/services/Revisions.php:151-162); a rule that forbids behavior attachment in the duplicate path breaks draft/revision editing (covered by tests/unit/services/DraftsTest.php:141-143,227-233).",
  "Refused input shape a legitimate use needs: a project config field handle that is not a valid PHP identifier (legacy handles created before the current HandleValidator rule, see CHANGELOG.md:620) must still yield a functioning CustomFieldBehavior; rejecting it at save time or skipping the field is not acceptable, only escaping the generated code is.",
  "Must-keep-working: field layout configs legitimately carry keys such as tabs, elements, uid, type, name, sortOrder and the condition keys (src/models/FieldLayout.php:172-187, src/models/FieldLayoutTab.php:200-209); the security rule must remove only `on X`/`as X` keys, not unknown keys in general, or saved layouts lose settings.",
  "The pinned unit test tests/unit/helpers/ComponentHelperTest.php:321-333 fixes the semantics of Component::cleanseConfig() (strip only `as X`/`on X`, recurse into arrays), so a grading rule requiring different global semantics contradicts the existing project tests."
 ],
 "effort_minutes": 90,
 "usable": true,
 "design": {
  "traps": [
   "T1",
   "T2",
   "T3",
   "T6",
   "T7"
  ],
  "why": "T1 is the anchor the report's 'attached Behaviors' wording points at (easy for both models) and keeps the task solvable. T2 is the second factory on the same idea but a separate action, so a solver who fixes only the layout-save path stays green on T1 and red on T2. T3 is the deepseek-type trap: the protection is absent from the project-config factories, the object is built with `new` + Model::__construct (so the Craft::createObject guard does not apply), and there is a strong reason to dismiss it (project config is developer-supplied and applied from the console). T6 is a second deepseek/how-type trap in a different layer: the CustomFieldBehavior generator interpolates stored field handles raw, the producer (Fields::applyFieldSave) skips HandleValidator, and the dismissal ('handles are validated and the class is generated internals') is different again; it also carries the coupled legacy-handle value. T7 is the mimo-type coupled-value trap: Elements::duplicateElement() must keep attaching DraftBehavior/RevisionBehavior for drafts and revisions while refusing arbitrary behavior classes/'as ' keys. The five traps sit in five distinct fix sites (layout save config, layout element/tab action, Model-constructor/project-config factories, the CustomFieldBehavior generator, and duplicate-element behavior plumbing), so fixing any one does not automatically close the others; four different dismissals (structural admin config / type check looks sufficient / project config is trusted / handles are validated and the duplicate API is internal) make the stack resist a single-judgement solve. T4 and T5 are real but are left out of the design because they share the Model-constructor and recursive-cleanse fixes with T3/T1 and would not add an independent judgement; T8 is an injection room with no request route in core."
 },
 "unverified": [
  "The fix commits for both advisories (a_fix 27f55886098b, 6e608a1a5bfb, ec43c497edde; b_fix 395c64f0b80b) are not readable from this worktree because only the pinned tree was in scope, so the exact A-to-B relation (regression in A's code vs an incomplete fix elsewhere), the true origin labels, and whether the pinned tree is before or after A's fix are inferred from code shape, not from the diffs; history.a_fix_leaves_b_open and history.b_in_code_a_wrote are therefore left null.",
  "Yii's Component::__set behavior for `as X` keys and Craft::createObject/Craft::configure's use of Yii::configure are described from Yii 2.0.52 (composer.json:59) semantics; the vendor/ tree is not present in this worktree, so the exact branch (as X -> Behavior::create -> Yii::createObject) is not shown by a file path here.",
  "No dependency upgrade is involved: the vulnerable code is in this repository (src/Craft.php, src/services/Fields.php, src/models/FieldLayout.php), so an in-repo fix is possible, but whether upstream chose a dependency bump cannot be checked without the fix diff.",
  "Whether hidden behavioural tests exercise project config, the tab-settings action, the duplicateElement API or the CustomFieldBehavior generator could not be determined; the report text available here is only the one-line summary, and no test files for these paths exist at the pin (grep of tests/ for assembleLayoutFromPost/createLayoutElement/FieldLayoutTab returned nothing).",
  "Whether an RCE is achievable with classes available in a real install (a gadget class for Yii's behavior instantiation) was not verified, because the vendor tree and plugin code are absent; the missing-protection facts are about arbitrary class instantiation via config, which is the CWE-470 condition.",
  "Whether Craft::createObject()'s `class`/`__class` conflict check (src/Craft.php:56-58) predates the pinned release or was added by an earlier security fix could not be established; no CHANGELOG entry mentions it.",
  "The exact PR numbers/date of the pin were not checked (git is unavailable in this session); the version constant (src/config/app.php:6 = 4.16.16) and the Unreleased CHANGELOG entries (#18079, #18123, #18049, #18131) were used to place the tree after 4.16.16.",
  "The candidate metadata labels this candidate H3b2; the schema's closest allowed value H3b was recorded, and the H3b2 sub-case could not be confirmed without the fix diffs."
 ]
}
  ```
- Published fix sites:   - src/services/Fields.php:1247-1250 — T1 M1 (reason to dismiss: The posted value is structural layout JSON (tabs/uid/type) and Craft::createObject already rejects a config that specifies both `class` and `__class`; every caller is an admin-only settings screen, so the config reads as trusted structural data rather than an attacker-chosen class list.)
  - src/services/Fields.php:1283-1287 — T1 M1 (reason to dismiss: The posted value is structural layout JSON (tabs/uid/type) and Craft::createObject already rejects a config that specifies both `class` and `__class`; every caller is an admin-only settings screen, so the config reads as trusted structural data rather than an attacker-chosen class list.)
  - src/controllers/SectionsController.php:346-349 — T1 M1 (reason to dismiss: The posted value is structural layout JSON (tabs/uid/type) and Craft::createObject already rejects a config that specifies both `class` and `__class`; every caller is an admin-only settings screen, so the config reads as trusted structural data rather than an attacker-chosen class list.)
  - src/controllers/VolumesController.php:168-171 — T1 M1 (reason to dismiss: The posted value is structural layout JSON (tabs/uid/type) and Craft::createObject already rejects a config that specifies both `class` and `__class`; every caller is an admin-only settings screen, so the config reads as trusted structural data rather than an attacker-chosen class list.)
  - src/controllers/CategoriesController.php:168-171 — T1 M1 (reason to dismiss: The posted value is structural layout JSON (tabs/uid/type) and Craft::createObject already rejects a config that specifies both `class` and `__class`; every caller is an admin-only settings screen, so the config reads as trusted structural data rather than an attacker-chosen class list.)
  - src/controllers/TagsController.php:125-128 — T1 M1 (reason to dismiss: The posted value is structural layout JSON (tabs/uid/type) and Craft::createObject already rejects a config that specifies both `class` and `__class`; every caller is an admin-only settings screen, so the config reads as trusted structural data rather than an attacker-chosen class list.)
  - src/controllers/GlobalsController.php:76-79 — T1 M1 (reason to dismiss: The posted value is structural layout JSON (tabs/uid/type) and Craft::createObject already rejects a config that specifies both `class` and `__class`; every caller is an admin-only settings screen, so the config reads as trusted structural data rather than an attacker-chosen class list.)
  - src/controllers/UsersController.php:2143-2146 — T1 M1 (reason to dismiss: The posted value is structural layout JSON (tabs/uid/type) and Craft::createObject already rejects a config that specifies both `class` and `__class`; every caller is an admin-only settings screen, so the config reads as trusted structural data rather than an attacker-chosen class list.)
  - src/controllers/AddressesController.php:104-107 — T1 M1 (reason to dismiss: The posted value is structural layout JSON (tabs/uid/type) and Craft::createObject already rejects a config that specifies both `class` and `__class`; every caller is an admin-only settings screen, so the config reads as trusted structural data rather than an attacker-chosen class list.)
  - src/services/Fields.php:1263-1273 — T2 M1 (reason to dismiss: createLayoutElement() already validates that `type` is a FieldLayoutElement subclass and throws otherwise, so the config looks validated; the remaining keys are ordinary element settings and the action only previews them.)
  - src/controllers/FieldsController.php:459-467 — T2 M1 (reason to dismiss: createLayoutElement() already validates that `type` is a FieldLayoutElement subclass and throws otherwise, so the config looks validated; the remaining keys are ordinary element settings and the action only previews them.)
  - src/controllers/FieldsController.php:475-482 — T2 M1 (reason to dismiss: createLayoutElement() already validates that `type` is a FieldLayoutElement subclass and throws otherwise, so the config looks validated; the remaining keys are ordinary element settings and the action only previews them.)
  - src/models/FieldLayoutTab.php:286-289 — T2 M1 (reason to dismiss: createLayoutElement() already validates that `type` is a FieldLayoutElement subclass and throws otherwise, so the config looks validated; the remaining keys are ordinary element settings and the action only previews them.)
  - src/models/FieldLayout.php:308-324 — T5 M8 (reason to dismiss: The posted layout document is one nested array, so a top-level check on the keys of the config passed to Craft::createObject() looks like it covers the whole request; the tabs and elements are only turned into objects later, from their own sub-arrays.)
  - src/models/FieldLayoutTab.php:280-306 — T5 M8 (reason to dismiss: The posted layout document is one nested array, so a top-level check on the keys of the config passed to Craft::createObject() looks like it covers the whole request; the tabs and elements are only turned into objects later, from their own sub-arrays.)
  - src/services/Fields.php:1210-1215 — T5 M8 (reason to dismiss: The posted layout document is one nested array, so a top-level check on the keys of the config passed to Craft::createObject() looks like it covers the whole request; the tabs and elements are only turned into objects later, from their own sub-arrays.)
- Uncovered routes to confirm (pattern B):   - src/models/FieldLayout.php:172-187 — T3 M2 (reason to dismiss: Project config is authored by developers and applied from the console/git, is not a CP request body, and every value there is expected to be a plain layout definition; a solver can argue the advisory is about request configs and that this factory is trusted, developer-supplied data.)
  - src/models/FieldLayoutTab.php:43-47 — T3 M2 (reason to dismiss: Project config is authored by developers and applied from the console/git, is not a CP request body, and every value there is expected to be a plain layout definition; a solver can argue the advisory is about request configs and that this factory is trusted, developer-supplied data.)
  - src/base/Model.php:67-88 — T3 M2 (reason to dismiss: Project config is authored by developers and applied from the console/git, is not a CP request body, and every value there is expected to be a plain layout definition; a solver can argue the advisory is about request configs and that this factory is trusted, developer-supplied data.)
  - src/helpers/App.php:1450-1454 — T3 M2 (reason to dismiss: Project config is authored by developers and applied from the console/git, is not a CP request body, and every value there is expected to be a plain layout definition; a solver can argue the advisory is about request configs and that this factory is trusted, developer-supplied data.)
  - src/services/Sections.php:1164-1170 — T3 M2 (reason to dismiss: Project config is authored by developers and applied from the console/git, is not a CP request body, and every value there is expected to be a plain layout definition; a solver can argue the advisory is about request configs and that this factory is trusted, developer-supplied data.)
  - src/controllers/FieldsController.php:442-449 — T4 M4 (reason to dismiss: This sibling action only deals with a tab name and sort order, so it looks like a harmless form preview; the layout-element action is the one that takes a class `type`, and a solver who hardens that action will not look here.)
  - src/controllers/FieldsController.php:475-482 — T4 M4 (reason to dismiss: This sibling action only deals with a tab name and sort order, so it looks like a harmless form preview; the layout-element action is the one that takes a class `type`, and a solver who hardens that action will not look here.)
  - src/models/FieldLayoutTab.php:43-47 — T4 M4 (reason to dismiss: This sibling action only deals with a tab name and sort order, so it looks like a harmless form preview; the layout-element action is the one that takes a class `type`, and a solver who hardens that action will not look here.)
  - src/base/Model.php:67-88 — T4 M4 (reason to dismiss: This sibling action only deals with a tab name and sort order, so it looks like a harmless form preview; the layout-element action is the one that takes a class `type`, and a solver who hardens that action will not look here.)
  - src/Craft.php:289-305 — T6 M6 (reason to dismiss: Field handles are validated by HandleValidator on the normal Field save path and the generated class is internal generated code, so the handle column looks like trusted data; the advisory text talks about attached behavior configs, not about the generator.)
  - src/Craft.php:326-352 — T6 M6 (reason to dismiss: Field handles are validated by HandleValidator on the normal Field save path and the generated class is internal generated code, so the handle column looks like trusted data; the advisory text talks about attached behavior configs, not about the generator.)
  - src/Craft.php:358-372 — T6 M6 (reason to dismiss: Field handles are validated by HandleValidator on the normal Field save path and the generated class is internal generated code, so the handle column looks like trusted data; the advisory text talks about attached behavior configs, not about the generator.)
  - src/services/Fields.php:1649-1662 — T6 M6 (reason to dismiss: Field handles are validated by HandleValidator on the normal Field save path and the generated class is internal generated code, so the handle column looks like trusted data; the advisory text talks about attached behavior configs, not about the generator.)
  - src/services/Fields.php:909-919 — T6 M6 (reason to dismiss: Field handles are validated by HandleValidator on the normal Field save path and the generated class is internal generated code, so the handle column looks like trusted data; the advisory text talks about attached behavior configs, not about the generator.)
  - src/services/Matrix.php:310-313 — T6 M6 (reason to dismiss: Field handles are validated by HandleValidator on the normal Field save path and the generated class is internal generated code, so the handle column looks like trusted data; the advisory text talks about attached behavior configs, not about the generator.)
- Design plan from the lead: TRACK = STACKED (H3b). Build the stacked design the reader chose: traps T1, T2, T3, T6, T7. Why: T1 is the anchor the report's 'attached Behaviors' wording points at (easy for both models) and keeps the task solvable. T2 is the second factory on the same idea but a separate action, so a solver who fixes only the layout-save path stays green on T1 and red on T2. T3 is the deepseek-type trap: the protection is absent from the project-config factories, the object is built with `new` + Model::__construct (so the Craft::createObject guard does not apply), and there is a strong reason to dismiss it (project config is developer-supplied and applied from the console). T6 is a second deepseek/how-type trap in a different layer: the CustomFieldBehavior generator interpolates stored field handles raw, the producer (Fields::applyFieldSave) skips HandleValidator, and the dismissal ('handles are validated and the class is generated internals') is different again; it also carries the coupled legacy-handle value. T7 is the mimo-type coupled-value trap: Elements::duplicateElement() must keep attaching DraftBehavior/RevisionBehavior for drafts and revisions while refusing arbitrary behavior classes/'as ' keys. The five traps sit in five distinct fix sites (layout save config, layout element/tab action, Model-constructor/project-config factories, the CustomFieldBehavior generator, and duplicate-element behavior plumbing), so fixing any one does not automatically close the others; four different dismissals (structural admin config / type check looks sufficient / project config is trusted / handles are validated and the duplicate API is internal) make the stack resist a single-judgement solve. T4 and T5 are real but are left out of the design because they share the Model-constructor and recursive-cleanse fixes with T3/T1 and would not add an independent judgement; T8 is an injection room with no request route in core. Follow the stacked-task rules appended at the end of this prompt; they add to the rules above.
- Host notes: Reader fairness risks (resolve each in the report's contracts or the tests): Must-keep-working: app and plugin component configs legitimately use Yii's `on X`/`as X` keys with Craft::createObject()/config files (src/config/app.php:221-253, src/config/app.web.php:10-34), so a security rule phrased as 'no `as ` key may ever reach object configuration' contradicts a documented extension point and would break trusted event-handler/behavior configs. | Must-keep-working: drafts and revisions depend on Elements::duplicateElement() attaching DraftBehavior/RevisionBehavior through $newAttributes['behaviors'] (src/services/Drafts.php:157-166, src/services/Revisions.php:151-162); a rule that forbids behavior attachment in the duplicate path breaks draft/revision editing (covered by tests/unit/services/DraftsTest.php:141-143,227-233). | Refused input shape a legitimate use needs: a project config field handle that is not a valid PHP identifier (legacy handles created before the current HandleValidator rule, see CHANGELOG.md:620) must still yield a functioning CustomFieldBehavior; rejecting it at save time or skipping the field is not acceptable, only escaping the generated code is. | Must-keep-working: field layout configs legitimately carry keys such as tabs, elements, uid, type, name, sortOrder and the condition keys (src/models/FieldLayout.php:172-187, src/models/FieldLayoutTab.php:200-209); the security rule must remove only `on X`/`as X` keys, not unknown keys in general, or saved layouts lose settings. | The pinned unit test tests/unit/helpers/ComponentHelperTest.php:321-333 fixes the semantics of Component::cleanseConfig() (strip only `as X`/`on X`, recurse into arrays), so a grading rule requiring different global semantics contradicts the existing project tests.. Conflicts the reader found: The tempting single fix is to cleanse inside Craft::createObject() (src/Craft.php:54-61). That breaks trusted config-driven components: Craft::createObject() is intentionally used to build app components from config/app.php:221-253 and config/app.web.php:10-34, where `on <event>`/`as <behavior>` keys are legitimate Yii configuration. The safe fix has to be at the request boundaries (the field-layout factories/actions), which is why T1 and T2 are separate fix sites. | A blanket rule that Model::__construct()/App::configure() must never honor `as ` keys (the natural way to close T3/T4) is adjacent to the draft/revision behavior plumbing in Elements::duplicateElement() (src/services/Elements.php:1575-1594); drafts and revisions must keep attaching DraftBehavior/RevisionBehavior or getIsDraft()/getIsRevision() and the draft/revision edit flows break (src/services/Drafts.php:157-166, src/services/Revisions.php:151-162).

## Design: where difficulty comes from
Models find the code the report leads to and diagnose it correctly. They fail on scope. Build these
in, in order of evidence:
1. **Pattern A: the published fix's far sites.**
   - The report leads to one site. The tests cover every entry point the published fix protects,
     including one in a module that looks out of scope: a second implementation, a lower-level
     public API, a wrapper, a save/reload path, or a defaults or merge route.
   - Give it a plausible **reason to dismiss**, and **distance**: another file or package from the
     landing point.
   - **A second implementation is the strongest form of this**: separate code doing the same
     guarded operation (a fallback backend, another package, another transport, a legacy version),
     so fixing the reported copy changes nothing in the other. Models fix the copy the example hits,
     re-run the example and stop. Prefer a real one (Pattern A or B) over a planted one. Find
     candidates by searching for the low-level primitive across packages (redirect following,
     header copying, file writes, message construction). It only counts if the report never
     describes it.
2. **Pattern B: uncovered routes.**
   - Routes into the same protected sink where the advisory's own protection is missing at the
     pinned commit, and which the published fix did not touch.
   - They are unmodified upstream code. A solver may argue they were never covered, but the task's
     general property covers them, so leaving one open is a model failure, not out of scope. The
     same holds for a route where the protection never existed: the property requires it.
   - Make sure the property, read literally, really covers each route (no word that excludes it),
     and that its test fails only when the protection is really missing (it must pass a correct
     fix placed at any valid layer).
   - The strongest lever found so far: DeepSeek 6 of 6 on one; both models 0 of 3 on three combined.
3. **Shape traps: an input form that a plausible check mishandles.** Examples: a value given as an
   array where the check only handles a string; a name split on the first separator when it can
   contain the separator; a resolved path against a lexical check; a rename or rewrite that happens
   after the check; a nested expression the check never inspects. Two conditions: the general
   property must cover the form literally, and the form must not fall inside anything a
   must-keep-working clause or a test fixture calls legitimate. A pure spelling, encoding, verb,
   protocol or role variant of a stated input is NOT a shape trap: both models always catch those
   (see "Never add").
4. **A coupled must-keep-working behaviour** next to the sink, tested functionally, so an
   over-broad fix fails. MiMo tends to over-harden.
5. **Producer off the check's path.** The check depends on data produced elsewhere (a schema,
   serializer, cache, mapper, table builder or config loader) and does not call it; the data
   reaches the check on a separate path (saved and reloaded, rebuilt from config). The fix needs
   both the check and the producer. Models trace into what the check calls, never back to where
   its data comes from. Rules:
   - it counts only if the producer is infrastructure, not a request handler;
   - verify that the check does **not** call the producer; if it does, the model follows the call
     and fixes it;
   - the report describes impact only through the check's path and states the property abstractly
     ("including data saved earlier"); it never points at the producer or the reload path;
   - avoid fixes where the check cannot compile without the producer change (that forces the find);
   - hidden tests must not need a field or function name the solver would have to guess;
   - prefer a producer deep in internal machinery (a table or schema builder). One behind a path
     that is easy to follow falls as soon as anything points at it.
6. **Injected siblings**, only where the plan asks for them. Each must be:
   - code a maintainer could have written, with no deceptive names or comments;
   - reachable through the real entry point;
   - covered by the task's general property, never by a sentence of its own;
   - placed where the upstream fix never touches.
7. **Wrong object.** The authorization check exists but decides on a different object than the one
   the request actually touches: a neighbouring or proxy resource (a parent or container instead of
   the item written), or an identity field the caller supplies (an account inside a caller-provided
   resource name; a parent read from one part of the request while the write uses another). Models
   copy the nearby precedent. Rules:
   - the instruction names the protected object class in product terms ("the objects that hold the
     limits"), never the check or its location;
   - the security test denies exactly the object touched while the proxy object stays allowed;
   - a functional test keeps a legitimate request on that same object working.
8. **Ordering.** The check is right but runs at the wrong moment: after an adjustment turns the
   attacker's value into a different bad value (an offset, a clamp, a unit conversion, a
   normalisation), or after a side effect has already happened (a directory created, a file cleared,
   copied or re-permissioned, a request sent) before the refusal. Rules:
   - the instruction states the property over the attacker's input or the outcome ("nothing outside
     the folder is created or changed, even when the request is refused"), never the order of steps;
   - the security test checks the side effect itself, not only the response;
   - any fix that keeps the property passes, wherever it places the check.
9. **Route where the protection never existed.** Real code reaches the protected sink but never had
   the check at all, so its absence reads as design (DeepSeek missed one 6 of 6 times). Rules:
   - it needs a plausible reason to dismiss: an unsupported combination, a legacy path, a
     neighbouring feature. If the project documents the protection as applying everywhere with no
     exceptions, there is no reason to dismiss and the route adds nothing;
   - the general property must cover it literally; never describe it in the instruction;
   - confirm it with a behavioural test on the pinned copy, like any Pattern B route.
10. **Merged or defaults route.** The restricted value reaches the sink through defaults, a merge,
    inheritance, a patch, or stored configuration rather than the request field the report shows.
    Models treat the report's example fields as the whole set. Rules:
    - state the property over the sink ("anything a submitter supplies that ends up in X, however
      it gets there"), not over the entry or field;
    - the security test drives the merged or stored route through the real entry point;
    - a functional test keeps legitimate defaults and merges working.

Aim for at least two levers with **different** reasons to dismiss.

**At least one lever must be how-type**: its fix needs the mechanism understood, not only found.
How-type levers are a producer off the check's path (5), a coupled must-keep-working value (4), a
shape that a plausible check mishandles (3: a separator split, a rename after the check), and a
route where the protection never existed. Where-type levers (another entry point into the same code,
a second copy, injected siblings) only cost a search. They held only when the report stayed general,
so count them as extras, never as the task's main difficulty.

Never add:
- encoding, verb, protocol or role/direction variants;
- more routes of one concept;
- resource-exhaustion traps.

Every lever must be findable by a blind engineer from the report and the code. A lever that a blind
fix cannot find is unfair: remove it.

**Pattern B rules:**
- Confirm each route with a behavioural test on the pinned copy before relying on it. The
  screener's claim is only a lead.
- Append one row per route to `/home/mara/cwe-bench/build/audit/uncovered-routes.tsv`, using its existing
  header. Columns:
  - `task`, `repo`, `advisory`;
  - `trap_ref` (the manifest trap id only; no mechanism text, since the manifest holds the detail);
  - `real_upstream`;
  - `present_in_latest` (`yes`, `no` or `unknown`, from a read-only look at current upstream code if
    you can reach it);
  - `public_upstream_report`, `in_current_scope`, `built`, `note`;
  - `disclosure_status` (`pending client decision`).

## Environment (`tasks/stk-cms-ghsa7jx7/environment/Dockerfile`)
- **Base and code.** A small official base image. The repo goes into `/app` at the pinned commit,
  and `/app/.git` is then deleted.
- **Offline.** Install every dependency, tool and service the project and tests need; nothing may
  be downloaded at test time. Services start from `test.sh`.
- **Packages:** `patch`, `curl`, `ca-certificates`, `bash`, `git`.
- **Agent layer.** Append `common/trial/claude-code.Dockerfile.snippet` unchanged at the end.
- **No test code in the image.** The agent shares the container. Pre-build against stubs; `test.sh`
  copies the real tests in at grading time.
- **Project tests.** The project's own tests for the affected area must pass in the image at the
  pinned commit.
- **No leaked regression tests.** The pinned commit must not already contain the advisory's
  regression tests (check `git log` between the pinned and fix commits).

## Report to the solver (`tasks/stk-cms-ghsa7jx7/instruction.md`)
**Write:**
- what the system is, at product level;
- one observed impact, with ONE concrete trigger at user level (HTTP request, CLI call or public API
  use);
- the security property as an **invariant**, stated once in general terms: who may do what to which
  data, or what attacker input must never achieve ("no value of X may …, however it arrives"). It is
  fair when, read literally, it covers every tested route and shape; it must not point at any of
  them. Write a second property only for a genuinely different protection, never one per route,
  and never a count;
- every **contract** the tests need, each stated once for the whole product, never per route:
  - the refusal form ("a client error with no side effect");
  - any interface or field name a test uses, stated so it applies everywhere. If a sibling's test
    would need a contract that only that sibling uses, change the test so it does not, or drop the
    sibling;
  - preservation clauses ("everything that works today keeps working exactly as today"). Name a
    coupled legitimate value in property terms ("visible values keep binding even next to a hidden
    one"), not by the feature or route it sits on;
  - a legitimate magnitude next to any attack magnitude;
- that examples are examples, not the full set;
- the standard constraints block: fix the problem and its close variants; keep legitimate use
  working; do not look up the upstream fix; do not special-case the
  example.

**Never write:**
- file, package, function, class, field or parameter names a user would not see;
- line numbers, the root cause, the fix approach, or a CVE or GHSA id;
- a list of routes, spellings or roles;
- restricting adverbs ("directly", "only via");
- anything that names or paraphrases a far site, an uncovered route or an injected sibling;
- any clause that describes where a far site, uncovered route or injected sibling lives, even in
  product terms: no route, operation, command, channel, object kind, stage or format that points
  at one of them. State each property once, over the protected data or outcome, so it covers every
  route without pointing at any;
- a word that is general but is also the name of one stage or entry point ("loading" when the
  product has a load call). Pick wording that cannot be read as one surface.

Check before you finish: for each sentence of the report, ask whether it exists to cover one
specific route or trap. If it does, delete it or widen it into the general property.

Put every identifier that must not appear in `manifest.leak_terms`.

## Tests (`tasks/stk-cms-ghsa7jx7/tests/`)
- **`security/`:** one test per site, route, input shape and form. Each one:
  - goes through the real entry point;
  - fails on the pinned code and passes on a correct fix;
  - asserts the attack is blocked: any client error plus no side effect, never one exact status.
- **`functional/`:**
  - legitimate use, including the coupled behaviour of every lever;
  - where they exist, the project's own tests for the area.
- **No product code in a test's bookkeeping.** Compute expected values and clean-ups in the test
  itself, because a hardened helper must not crash a test.
- **Stubs** of permission or authority answer per resource and verb, like the real thing.
- **Scope.** A test may vary only what the instruction names, and drive only the entry point it
  names.
- **No network**, and nothing that depends on the fix commit being present.
- **Templates.** JUnit XML into the two directories the template names. Copy `score.py` unchanged.
  Edit only the marked command lines of `test.sh`, and keep its agent-kill block.

## Proof
- **The oracle.** `solution/fix.patch` is the published fix reduced to source changes, plus fixes
  for every uncovered route and injected sibling in the task. `solution/solve.sh` applies it to
  `/app`.
- **Wrong-fix patches** go in `build/stk-cms-ghsa7jx7/checks/`, listed in `manifest.patch_checks`:
  - one `security_fail` per lever (the fix that misses only that lever);
  - a `functional_fail` (an over-broad or feature-removing fix);
  - a `pass` of kind `hardening` (the oracle plus defensive hardening of the product code the
    security tests import);
  - a `pass` alternative fix where a second valid design is plausible.
- **`manifest.wrong_fix_catalogue`:** for each class, a `checks/` patch, or `n/a: <why>`:
  `refuse_all`, `crash_as_refusal`, `wrong_resource`, `one_role_or_direction`, `reads_only`,
  `check_after_adjustment`, `unlisted_route`, `malformed_identity`, `missing_authority`,
  `adjacent_api`.

## Deliverables
**`tasks/stk-cms-ghsa7jx7/`:**
- `instruction.md`;
- `task.toml`, from `common/builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/stk-cms-ghsa7jx7/manifest.json`:**
- `slug`, `candidate`;
- `pattern`: `A+B`;
- `builder_prompt_version`: `build-v1`;
- `"strict_gate": true`;
- `verified`: entry point, sites, routes, services, project tests run;
- `leak_terms`, `patch_checks`, `wrong_fix_catalogue`;
- `traps`: one entry per lever, with `shape`, `where` (file:line), `security_tests`,
  `coupled_functional_tests`, `security_fail_patch`, and `realistic_because` (for pattern B: "real,
  unmodified upstream code");
- `status`.

**Also in `build/stk-cms-ghsa7jx7/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `common/builder/templates/` and `common/trial/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I common/gate/gate.py stk-cms-ghsa7jx7 --only static
python3 -I common/gate/gate.py stk-cms-ghsa7jx7 --only nop
python3 -I common/gate/gate.py stk-cms-ghsa7jx7 --only oracle
python3 -I common/gate/gate.py stk-cms-ghsa7jx7 --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/stk-cms-ghsa7jx7/`;
  - edit only `tasks/stk-cms-ghsa7jx7/`, `build/stk-cms-ghsa7jx7/` and, for pattern B, the register;
  - do not commit.

## Stop and report instead of shipping when
- the flaw does not reproduce through a real entry point at the pinned commit;
- a planned route or site is not reachable, or the check calls the producer directly (substitute
  another lever the code supports if you can, and say so);
- the task needs network at run time, or a GPU, kernel or GUI;
- the tests are flaky;
- no design meets the bar.

## Report back (under 400 words)
- The gate result for each stage.
- Each lever in one line: pattern, shape, file:line, reason to dismiss.
- Pattern B: each register row.
- The instruction's word count.
- Every guess you could not verify.
- Any fairness concern you see yourself.
- Anything noticed outside the scope, in one line.
- If abandoned, exactly why.


## Stacked task: additional rules

You are building a **stacked** task: one checkout with several independent places where a protection
is missing. The reader's record lists them, with evidence: `/home/mara/cwe-bench/pipelines/stacking/out/reader/h3-ghsa-7jx7-3846-m7w7.json`. Verify each trap on the
pinned code before you rely on it. The record is a lead.

**The stack**
1. **At least 3 independent concepts.** If one guard or one fix site would close two traps, they are
   ONE concept. Count your reference fix's independent edit sites, not advisories or routes.
2. **Each concept is hard on its own** for at least one target model (tier hard or xhard in the
   record).
3. **Both models covered.** At least one DeepSeek-type trap (a route where the protection never
   existed, with a plausible reason to dismiss it) and at least one MiMo-type trap (a coupled
   must-keep-working value next to a hidden one, or a how-type mechanism).
4. **No single trap carries the task.** A fix that closes every concept except the hardest must still
   fail. Add one `security_fail` check patch per concept (a fix that misses only that concept).
5. **A coupled must-keep-working value next to every hidden route**, tested functionally. The
   report covers it ONLY through the general keep-working sentence ("everything that works today
   keeps working"); it never names or describes the value. If a security rule, read literally, would
   forbid that value, reword the security rule over its protected outcome instead of adding an
   exception that names the value.
6. **Effort budget.** A careful engineer who knows where to look fixes everything in about 45-60
   minutes. If the stack needs more, drop the weakest concept.

**The report**
7. **One general property per distinct protection, and nothing per trap.** Never one per route, and
   never a count. Describe no surface, as the build template already requires. If the stack spans two
   protections, state two properties, each over its protected data or outcome.
   - **The one-bug test:** for every sentence of the report, ask "would this sentence be here if the
     task had only the advisory's own route?" If not, delete it. That covers forms ("in every form it
     can be named"), timing ("and again when the call connects"), sources ("whichever response
     supplies it"), encodings, aliases, example values in keep-working lines, and lists of resources.
   - Only the advisory's own route may be shown, in the impact example.
   - General contracts that hold for every route stay: the refusal form (for example "a client
     error, with no effect"), an operator opt-in, "keep every legitimate use working".
   - Keep the report short: the goal in a few lines, the property, the general contracts.
   - After the build, `pipelines/stacking/4-listing/run_listing_check.sh` classifies every hidden trap against the
     report. One NAMED hidden trap, or more than one DESCRIBED hidden trap, is a FAIL. Once the
     reviewer is calibrated (`pipelines/stacking/4-listing/LISTING_ENFORCE`), a FAIL means the task is not marked sound.

**History rules** (by the record's `pattern`)
8. **H3a / H3b (fix of a fix):**
   - pin the parent of the earlier fix A's first commit;
   - the reference fix is the complete fix (A plus the later fix B, or an equivalent);
   - add `checks/upstream_first_fix.patch`, which is A's fix applied alone, with `expect: fail`, so
     upstream's first fix is proven to be a wrong fix.
9. **H3c (masking):** the masked bug's security test must fail on the pinned code through its own
   route, without relying on the masking bug, so the gate's nop stage holds.
10. **Conflicting fixes (F8):** when the record names a pair where the natural fix for one trap breaks
    a value another needs, test that value functionally. The report covers it only through the
    general keep-working sentence, as in rule 5; never by naming the value.
11. **Dependency-bump fixes (F5):** when upstream fixed a bug by upgrading a dependency, the task must
    be fixable inside the repository. The reference proves it. The report never asks for an upgrade,
    and the solver works offline.
12. **Recall check (every pattern):** add `checks/upstream_fix.patch` (every published fix commit for
    the stacked advisories, applied together) with `expect: fail`. If it passes, the stack adds
    nothing beyond what upstream shipped. Rework the design.

**The control task**
13. Also build `<slug>-control`: the same pinned code, the same report, but only the advisory's own
    route (the trap the report leads to) in the security tests and the reference. It isolates the
    effect of stacking from the effect of the host. The two `instruction.md` files stay byte-identical
    for the task's whole life: any later change to the stacked report (fairfix, upgrade) is copied to
    the control. `check_stack.py` checks it.

**Manifest:** add a `stacking` block containing:
- `pattern`;
- `reader_record`;
- `concepts` (groups of trap ids);
- `history`: advisories A and B with their fix commits, `pinned_commit` and its rule;
- `score_at_build`: copy the `score` of your job's row in `pipelines/stacking/out/stack_scores_ds.tsv` (do NOT run
  `score_stack.py`: it rewrites the shared selection file);
- `control_slug`.

**Exact manifest fields the static conformance check reads (step 5, `pipelines/stacking/3-build-gate/check_stack.py`). Emit these literally — the field NAMES and VALUES below must match, or the build is rejected before the container gate:**

`manifest.traps[]` — one object per trap:
- `id` (string) — referenced by `stacking.concepts`.
- `type` — exactly one of `"deepseek"`, `"mimo"`, or `"both"`. At least one trap must be `"deepseek"` or `"both"`, and at least one must be `"mimo"` or `"both"`.
- `origin` — for a hidden route, one of `"uncovered_upstream"`, `"published_fix_far_site"`, `"injection_room"`. Any trap with such an `origin` must also carry `coupled_functional_tests`: a non-empty list of the functional-test ids that keep its must-keep-working value honest.

`manifest.stacking` — an object with exactly these keys (all required):
- `pattern` — e.g. `"H3a"`, `"H3b1"`, `"H3b2"`, `"H4"`.
- `concepts` — a list of **at least 3** groups; each group is a list of trap `id`s forming one independent concept. Every id must exist in `manifest.traps`.
- `history`, `control_slug`, `score_at_build`, `reader_record` — as described above.

`manifest.patch_checks[]` — in addition to the task's normal patch checks, add:
- **One per concept** (a fix that closes every concept EXCEPT this one, so its security tests still fail):
  `{ "patch": "checks/miss_<concept>.patch", "kind": "security_fail", "expect": "security_fail", "misses": [<exactly this concept's trap ids>] }`.
  `misses` must be non-empty and be a subset of that concept's trap id group; one such check is required for every group in `stacking.concepts`.
- **Recall (always):** `{ "patch": "checks/upstream_fix.patch", "expect": "security_fail" }` — all published fix commits for the stacked advisories applied together.
- **Recall (H3a and every H3b variant):** also `{ "patch": "checks/upstream_first_fix.patch", "expect": "security_fail" }` — the earlier fix A applied alone.

Every `checks/*.patch` named above must be a real file in the task's `checks/` directory (the container gate then runs each with its `expect`ed outcome). A concept with no `security_fail` miss-check, a trap with no `type`, or a missing recall check/file each fails the conformance check.

**Report back:** also give the concept count, the DeepSeek-type and MiMo-type trap ids, the result of
each history check patch, and the control task's gate result.

Stacked task slug: `stk-cms-ghsa7jx7`. Control task slug: `stk-cms-ghsa7jx7-control`. Manifest `stacking.reader_record`: `pipelines/stacking/out/reader/h3-ghsa-7jx7-3846-m7w7.json`.
