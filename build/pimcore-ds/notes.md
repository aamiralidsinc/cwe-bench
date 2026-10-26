# pimcore-ds — build notes

- start UTC: 2026-10-19T18:21Z
- end UTC: 2026-10-19T19:19Z
- pinned: 3cb353b8cf602dd1ee25f1cfb5b5219b7d7c061f (parent of published fix a4f8c3cfee58b7d5fe4873d67782eff58dae9b9d)
- track: injected, pattern A+B.

## Plan (written before building)

Recurring trust decision: a value carried by a DataObject class definition is emitted into
generated PHP class files or into database DDL as if it were an identifier/code fragment.

Levers, each with the reason a solver skips it:

- L1 — Pattern A (published far site). DDL identifier construction in the shared
  `Model\DataObject\ClassDefinition\Helper\Dao` trait: index names/columns and ADD/CHANGE/DROP
  COLUMN statements backtick-wrap raw values, and `removeUnusedColumns`/`removeIndices` do the
  same, plus the separate `Objectbrick\Definition\Dao::removeIndices` override.
  Shape: structured-table row/column labels (only lower-cased) become `<field>__<row>#<column>`
  column names; existing DB column names come back through the drop paths. Dismiss: "once the
  field-name setter validates, this lower-level @internal helper only ever sees valid identifiers."
- L2 — Pattern B (real upstream). `Data\Classificationstore::setName` overrides the base setter and
  does not call it, so a definition-supplied name reaches generated getter/setter code unchecked.
  Dismiss: "the classification store is a separate key/group feature; its name is data, not a
  generated identifier." Real, unmodified upstream code.
- S1 — injected sibling. Generated class "Fields Summary" docblock includes the field's display
  title. Shape: a title carrying a comment terminator escapes the comment. Dismiss: "a title is
  display text; it only lands in a comment."
- S2 — injected sibling. A per-field legacy accessor alias (`legacyName`) that the class builder
  emits as `get<Alias>()` in addition to the normal accessor. Dismiss: "a backwards-compatibility
  alias, not the field's own name."
- S3 — injected sibling. A per-field raw SQL DEFAULT clause (`defaultValueSql`) passed by every
  Dao save loop to the column builder. Dismiss: "a DEFAULT clause is SQL by definition, and it is
  not a name."

Coupled must-keep-working (functional): valid names (1..63 chars, leading underscore, empty set
transiently), Localizedfields keeps the fixed name, generated getter/setter code for a normal
field is unchanged, normal titles still appear in the class docblock, a normal legacy alias still
emits its accessor, defaults such as ` DEFAULT 0` still reach DDL, structured-table labels with
`#`, space, hyphen and underscore still produce the same column/index names, date/dateRange and
input column types still work, unique localized indexes still carry the `language` column,
normal CHANGE/DROP statements keep their names, and the objectbrick drop still emits its index
drop.

Sites/routes covered by security tests:
- DDL: ADD COLUMN, CHANGE COLUMN, DROP COLUMN, ADD INDEX, DROP INDEX in the shared trait; the
  objectbrick override; structured-table labels; DB-returned column names; a definition-supplied
  DEFAULT clause.
- Code generation: base field names (several shapes incl. trailing newline, >63, backtick,
  metacharacters), the classification-store override, a display title, a legacy alias.

Not built (fairness): column `columnType` injection — `resolveBlockedVars()` strips `columnType`
on the json/import path, so it is not reachable from the reported producer; noted, not a lever.
Out of scope, noted: class/layout/custom-layout names are stored unvalidated; not built on.

Seam: the class-file path is driven through `PHPClassDumper`/`ClassBuilder` (the production
generation pipeline) with real `Data`/`ClassDefinition` objects; the DDL path is driven through
the real Dao classes and the real trait methods with a recording Doctrine connection and
per-table column answers (the DB is a stub that answers per resource, as the rules allow).
The project's own DB-backed codeception tests cannot run without the pimcore skeleton app and a
MySQL service; the project's DB-free expectation for generated setter code is reproduced in the
functional group instead.

## Verified during build

- The flaw reproduces at the pinned commit through the real import funnel
  (`Service::generateLayoutTreeFromArray` + the project's own DataLoader/LayoutLoader,
  the step `pimcore:definition:import:class` uses) and the real class-file generation
  step (`PHPClassDumper`/`ClassBuilder`), and through the real Dao classes on the DDL
  side. On the pinned+injected tree all 20 security tests fail and all 17 functional
  tests pass; the oracle makes both groups green.
- The published fix alone leaves 7 security tests failing (drop-path quoting, the
  objectbrick implementation, the classification store, and the three injected
  values).
- Every check patch behaves as declared in `manifest.patch_checks` on the task image
  (security_fail: functional all green; functional_fail: the named behaviour breaks;
  pass: reward 1.0 for both the hardening and the sink-side alternative).
- The image is offline after build: dependencies and the verifier's PHPUnit are
  installed at build time; `/app/.git` is removed and the pinned tree contains no
  regression test from the fix commit.

## Could not verify

- The project's own Codeception suites (e.g. `tests/Model/DataObject/ClassDefinitionTest.php`)
  need the pimcore skeleton application and a MySQL service; they are not runnable in this
  standalone core checkout. The one DB-free expectation they contain for this area (the exact
  generated setter code for an input field) is reproduced verbatim in the functional group.
- Whether the two target models actually miss the levers (trials are out of scope for the
  builder; the gate proves the tests, not the models).
- The admin class-editor HTTP route lives in a separate bundle, so it is named as a user-level
  entry point but not exercised directly.
- Out of scope, noted only: `ClassDefinition::setName`, `Layout::setName` and
  `CustomLayout::setName` also store names unvalidated; column `columnType` injection is not
  reachable from a JSON definition import (blocked-vars strip it there) and was dropped.

## Residual risks

- The pinned repository has no composer.lock, so the image resolves dependency versions at
  build time. It was built and verified on 2026-10-19; a later rebuild could resolve newer
  compatible versions.
- Docker compose network setup for Harbor flaked once with "network ... not found" from
  concurrent gate runs; the gate does not classify that as retryable, so the stage was re-run.

## Upgrade 2026-10-20 (BETTER-PATTERNS §2-§8, reusing the build)

- Instruction rewritten to one general invariant over definition-supplied values and
  values embedded in a storage statement. Removed the command/route naming, the
  identifier enumeration (field/column/index/constant/property/method), the
  comment/string clause, the storage-config enumeration, and the per-feature
  must-keep-working list (localized container, structured-table labels, date/range
  columns, language column, `DEFAULT 0`, renames). Preservation is now stated once,
  generally.
- Levers unchanged; no repo code changed and no image rebuild. How-type levers already
  present: T2 = M4 (DDL routes where the protection never existed), T3 = M6 (the
  classification-store override is a producer the base check never calls); T4/T5/T6 are
  M8/M6/M8-M11 shapes. Manifest traps now record `lever_type`.
- Coverage strengthened (no new lever): the shared trait's unused-column index-drop
  (`u_index_`) branch is now exercised too. `testDatabaseColumnNameCannotBreakOutOfDropColumn`
  registers the obsolete column's index so a database-supplied name reaches both the
  DROP COLUMN and the DROP INDEX statement, and asserts the index-drop statement was
  emitted. This is a route the published fix left open; the oracle already quotes it.
  No new check patch needed (sf-no-ddl-quoting still removes that quoting).
- Expected effect: nop still 0/20 security (the extended assertion fails on the
  unquoted tree), oracle still 20/20, all 12 check patches unchanged.

## Gate (final)

- static: FAIL only on `missing blind patch` and `missing FAIRNESS.md` (the two post-build
  inputs the builder must not write); every other static check passed.
- nop: PASS.
- oracle: PASS (3 runs, identical, reward 1.0).
- patches: PASS, 12/12 checks as declared (saved in gate_report.patches.json).
- The patches stage needed several re-runs because of a Docker compose network race on this
  shared machine ("network ... not found" while other agents' gate runs were active); each
  re-run was triggered only by that infrastructure signature.

## Harden round 2026-10-22 (T7/T8/T9 + Frontier 1.4)

- start UTC: 2026-10-22T00:58Z (worktree ~/.tb-graders/cwe/work/pimcore-ds/harden2)
- Both target models solved v2 and a fairness review found it fair, so the round added new
  fair levers and converted the delivery format.

Levers added (each with a different reason a solver skips it):
- T7 — injected sibling. `FieldDefinitionPropertiesBuilder` now also emits a generated
  `$fieldLabels` map for the UI, with each field's display title inside a double-quoted
  string. Dismiss: "the title is display text; the docblock path already strips comment
  terminators". A comment-marker fix does not help a string literal.
- T8 — injected sibling. The four definition save loops pass the field's help text to the
  shared DDL builder, which appends it as ` COMMENT '<text>'`. Dismiss: "help text is UI
  copy, not an identifier, and no name check applies to it."
- T9 — pattern B (real upstream). Date/Datetime/DateRange override `resolveBlockedVars()`
  so `columnType` is NOT stripped by the import funnel; a definition document therefore
  reaches `setColumnType` and the same DDL builder concatenates the value in the SQL type
  position (single-column and the two-column range shape). Dismiss: "column types are
  internal metadata, not a definition value." The earlier build note that resolveBlockedVars
  strips columnType was wrong for these three types.
- T7 extends the title concept (T4) with a different producer/construct; T8 and T9 are
  independent concepts and mechanisms, so no single trap carries the task.

Tests: 24 security (20 v2 + 4: label map, column comment, date type, range type) and 20
functional (17 v2 + 3 coupled: ordinary title stays a string literal, ordinary help text is
written as the comment, configured column types are applied). Oracle extended; T7/T8/T9 each
have a security_fail check patch; all 15 patches regenerated against the new injected tree,
plus a blind correct fix. Local runs on the pimcore 8.3 image: injected 0/24 security and
20/20 functional; oracle 24/24 and 20/20; each variant as declared.

Delivery format: schema 1.4, /workspace, separate offline verifier (tests/Dockerfile),
uid-1000 agent, artifacts restore, no agent allowlist, dual scoring, fresh canary GUID.

Not used (fairness): class-level parentClass/id via the stored-definition rebuild (not "an
entry it declares"); structured-table `length` (typed `?int`, a string is rejected before it
reaches SQL, so it is not a lever); ClassDefinition/class title (not imported by the JSON
import path).

## Gate (harden round, 2026-10-22)

- conformance_check: conforming.
- static: PASS (all 16 check patches declared, no leaks, B7 metadata + canary, no test/grading mention).
- nop: PASS (24/24 security fail, 20/20 functional pass; trial pimcore-ds-nop-1792631528).
- oracle: PASS (3 runs, reward 1.0; 24/24 + 20/20 each).
- patches: PASS 16/16 as declared (security_fail 1-15 sec failures with functional green; functional_fail 8/1;
  pass-hardening, pass-alt-sink and blind = 1.0).
