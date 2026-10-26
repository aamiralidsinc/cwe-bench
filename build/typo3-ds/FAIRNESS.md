# FAIRNESS — typo3-ds

## 1. Test-by-test fairness

S1 = "The set of stored form definitions, the content of each one, and whether each one counts as present or removed, change only through the form framework's own persistence path … No other operation may bring a definition into the stored set, alter one, take one out, or make a removed one count as present again — whatever it is called, whichever values it carries, and whoever invokes it."
S2 = "…refused with no side effect … the refusal is surfaced through the invoking operation's own normal error result. A refusal must not surface as an unhandled error or a crash."
S3 = "Everything that does go through it keeps working exactly as today, for every operation the product performs on stored definitions…"
S4 = "A stored definition may contain any configuration the form setup allows."
S5 = "Existing forms keep rendering and being submitted, and every existing way of managing stored definitions that goes through the framework's path keeps saving changes. Public interfaces, names and options stay as they are."

| Test (file::name) | What it asserts | Covering instruction sentence (or standard expert knowledge) | Could a correct fix fail it? | Risk |
|---|---|---|---|---|
| security/RecordApiWriteTest::creatingADefinitionThroughTheRecordApiIsRefused | NEW-key datamap write by non-admin: `errorLog` non-empty, no row with the identifier | S1 "bring a definition into the stored set … whoever invokes it"; S2 normal error result | no | low |
| security/RecordApiWriteTest::anAdministrativeRecordWriteOfADefinitionIsRefused | Same write as the harness admin: `errorLog` non-empty, no row | S1 "whoever invokes it"; S3 product legitimacy only via the path | no | low |
| security/RecordApiWriteTest::changingAStoredDefinitionThroughTheRecordApiIsRefused | Full update (label+identifier+config): `errorLog` non-empty, stored label/config unchanged | S1 "alter one — whichever values it carries" | no | low |
| security/RecordApiWriteTest::aPartialRecordUpdateOfADefinitionIsRefused | Label-only update carries no configuration: `errorLog` non-empty, label unchanged | S1 "alter one — whichever values it carries" | no | low |
| security/RecordApiCommandTest::deletingADefinitionThroughTheRecordApiIsRefused | cmdmap delete: `errorLog` non-empty, `deleted` unchanged | S1 "take one out" | no | low |
| security/RecordApiCommandTest::reActivatingADefinitionThroughTheRecordApiIsRefused | cmdmap undelete of the soft-deleted fixture: `errorLog` non-empty, `deleted` stays 1 | S1 "make a removed one count as present again" | no | low |
| security/RecordApiCommandTest::copyingADefinitionThroughTheRecordCommandIsRefused | cmdmap copy: `errorLog` non-empty, total row count unchanged (3) | S1 "bring a definition into the stored set … whatever it is called"; S2 error result | no — oracle blocks the nested insert and the refusal reaches the outer error log; a fix that denies the command itself and logs also passes | low |
| security/AdministrativeImportTest::importingANestedConfigurationIsRefusedOrStoredThroughTheValidatedPath | Either exit≠0 with no row, or exit 0 with exactly the `FormData`-normalised configuration | S1 (a raw insert is not the validated path); S2 (normal refusal result) | no — both allowed outcomes pass; a raw insert stores the un-normalised shape and is not a correct fix | low |
| security/AdministrativeImportTest::importingASerializedConfigurationIsRefusedOrStoredThroughTheValidatedPath | Same, with a JSON-string configuration | Same | no | low |
| functional/LegitimatePersistenceTest::theFormManagerCanCreateANewFormDefinition | Manager save creates a row; `load()` returns it | S3 "everything that does go through it keeps working"; S5 | no | low |
| functional/LegitimatePersistenceTest::theFormManagerCanUpdateAnExistingFormDefinition | Manager save updates label and `load()` reflects it | S3; S5 | no | low |
| functional/LegitimatePersistenceTest::theFormManagerCanRemoveAFormDefinition | Manager delete sets `deleted`=1 | S3 | no | low |
| functional/LegitimatePersistenceTest::aFormRemovedThroughTheManagerCanBeRestoredByTheRestoreTool | Restore command exits 0 and sets `deleted`=0 | S3 "reversing any removal that the framework's own path performed" (or, after generalisation, the path may change present/removed state) | no — granting the product's own repository restore, or rerouting it through the persistence path, both pass | low |
| functional/LegitimatePersistenceTest::theTransferCommandStoresAFileBasedFormInTheDatabase | Transfer command stores and lists `test-extension-form_1` | S5 "every existing way … that goes through the framework's path keeps saving changes" | no | low |
| functional/Storage/DatabaseStorageAdapterFunctionalTest::crudRoundtripWorksWithRealDatabase | Adapter create (NEW→numeric), read, update, delete | standard expert knowledge: existing adapter behaviour; S5 "public interfaces … stay as they are" | no | low |
| …::readReturnsFormDataFromDatabaseFixture | Adapter read of uid 1 | standard expert knowledge: existing behaviour; S5 | no | low |
| …::readInFrontendContextSkipsPermissionCheck | FE read without a BE user succeeds | S5 "existing forms keep rendering and being submitted" | no | low |
| …::readThrowsExceptionForInvalidJsonInDatabase | Invalid JSON read → `PersistenceManagerException` 1767199444 | standard expert knowledge: existing behaviour (visible project test); S5 | no | low |
| …::readThrowsExceptionForDoubleEncodedJsonInDatabase | Double-encoded invalid JSON → same exception/code | standard expert knowledge: existing behaviour (visible project test); S5 | no | low |
| …::existsReturnsTrueForExistingRecord | `exists(1)` true | standard expert knowledge: existing behaviour | no | low |
| …::existsReturnsFalseForNonExistingRecord | `exists(9999)` false | standard expert knowledge: existing behaviour | no | low |
| …::existsReturnsFalseForSoftDeletedRecord | `exists(2)` false (deleted=1) | standard expert knowledge: existing behaviour | no | low |
| …::findAllReturnsOnlyNonDeletedRecords | Lists 1 and 3, not 2 | standard expert knowledge: existing behaviour; S5 | no | low |
| …::deleteMarkRecordAsDeletedInDatabase | Adapter delete → `exists` false; `findByUid` null | S3 (path delete); standard expert knowledge | no | low |
| …::deleteThrowsExceptionForNonExistingRecord | Delete 9999 → exception code 1767199431 | standard expert knowledge: existing behaviour (visible project test) | no — the adapter's exists/permission checks run before any record-API guard | low |
| …::writeThrowsExceptionWhenUpdatingNonExistingRecord | Re-write of a removed uid → exception code 1767199424 | standard expert knowledge: existing behaviour (visible project test); S3 "exactly as today" | no — the natural fix grants from the repository and the existing failure path is unchanged; only a fix that deliberately changes this error contract fails, which S5 forbids | low |
| …::existsByFormIdentifierReturnsTrueForExistingForm | Identifier lookup true | standard expert knowledge: existing behaviour | no | low |
| …::existsByFormIdentifierReturnsFalseForNonExistingForm | Identifier lookup false | standard expert knowledge: existing behaviour | no | low |
| functional/Storage/DatabaseStoragePermissionFunctionalTest::adminUserCanReadFormInBackendContext | Admin BE read of uid 1 | standard expert knowledge: existing behaviour; S5 | no | low |
| …::adminUserCanWriteNewForm | Admin adapter write creates | standard expert knowledge: existing behaviour; S3 | no | low |
| …::adminUserCanDeleteForm | Admin adapter delete | standard expert knowledge: existing behaviour; S3 | no | low |
| …::nonAdminWithoutTableSelectCannotReadForm | Read → exception code 1774364031 | standard expert knowledge: existing permission behaviour | no — permission check precedes the repository/guard | low |
| …::nonAdminWithoutTableSelectCannotSeeFormsInFindAll | Zero forms in listing | standard expert knowledge: existing permission behaviour | no | low |
| …::nonAdminWithoutTableModifyCannotWriteNewForm | Write → exception code 1767199435 | standard expert knowledge: existing permission behaviour | no — permission check precedes the repository/guard | low |
| …::nonAdminWithReadOnlyAccessCanReadForm | Read-only user can read | standard expert knowledge: existing permission behaviour | no | low |
| …::nonAdminWithReadOnlyAccessSeesFormsInFindAll | Listing non-empty | standard expert knowledge: existing permission behaviour | no | low |
| …::nonAdminWithReadOnlyAccessCannotWriteNewForm | Write → code 1767199435 | standard expert knowledge: existing permission behaviour | no | low |
| …::nonAdminWithReadOnlyAccessFindAllMarksFormsAsReadOnly | `readOnly` true, `removable` false | standard expert knowledge: existing metadata behaviour | no | low |
| …::frontendContextAlwaysAllowsReadEvenWithoutBackendUser | FE read with no BE user | S5 "existing forms keep rendering and being submitted" | no | low |
| …::frontendContextAllowsReadEvenWithRestrictedBackendUser | FE read with a restricted BE user | S5 | no | low |
| …::isAccessibleReturnsTrueForAdmin | `isAccessible()` by role | standard expert knowledge: existing behaviour | no | low |
| …::isAccessibleReturnsFalseForUserWithoutTableModify | `isAccessible()` by role | standard expert knowledge: existing behaviour | no | low |
| …::isAccessibleReturnsFalseForReadOnlyUser | `isAccessible()` by role | standard expert knowledge: existing behaviour | no | low |

## 2. Leniency (QUALITY, non-blocking)

By security property:

- **Only the validated path changes the set (S1).** The plausible wrong fixes are: harden only the form editor/manager or the UI (caught by all six record-API tests, e.g. `creatingADefinitionThroughTheRecordApiIsRefused`, `sf-miss-create.patch`); refuse only non-administrative callers (caught by `anAdministrativeRecordWriteOfADefinitionIsRefused`); trust a well-formed payload whose `identifier` matches the row (caught by `creatingADefinitionThrough…` and `changingAStoredDefinitionThrough…`, `sf-check-after.patch`); guard the wrong resource, e.g. only rows with `pid != 0` (caught by the same tests, `sf-wrong-resource.patch`); guard reads only / no write guard (caught by every record-API test, `sf-reads-only.patch`); fail open (caught by every record-API test, `sf-failopen.patch`).
- **Refusal with no side effect, normal error result, no crash (S2).** Crash-as-refusal is caught by `deleting…`/`reActivating…` (`sf-crash.patch` — the unhandled `RuntimeException` errors the test); a silent `commandIsProcessed` denial is caught by the `errorLog` assertions, notably `copyingADefinition…` (`hardening.patch` had to add a log for exactly this).
- **Product path keeps working (S3).** Refuse-all is caught by the five `LegitimatePersistenceTest` cases and `crudRoundtripWorksWithRealDatabase` (`ff-deny-all.patch`, functional_fail); blocking the product's undelete is caught by `aFormRemovedThroughTheManagerCanBeRestoredByTheRestoreTool`.
- **Any configuration allowed (S4).** A guard that only inspects updates which carry a `configuration` field is caught by `aPartialRecordUpdateOfADefinitionIsRefused` (`sf-miss-partial.patch`); a guard that only accepts a configuration identical to the stored one is caught by `theFormManagerCanUpdateAnExistingFormDefinition`.
- **Existing behaviour (S5).** Making frontend reads enforce backend permissions is caught by `readInFrontendContextSkipsPermissionCheck`, `frontendContextAlwaysAllowsReadEvenWithoutBackendUser` and `frontendContextAllowsReadEvenWithRestrictedBackendUser` (`ff-adjacent-read.patch`).

By trap:

- T1 → `creatingADefinitionThroughTheRecordApiIsRefused` (`sf-miss-create.patch`).
- T2 → `deletingADefinitionThroughTheRecordApiIsRefused` (`sf-miss-delete.patch`).
- T3 → `aPartialRecordUpdateOfADefinitionIsRefused` (`sf-miss-partial.patch`).
- T4 → `reActivatingADefinitionThroughTheRecordApiIsRefused` (`sf-miss-undelete.patch`).
- T5 → both `AdministrativeImportTest` cases (`sf-miss-import.patch`; a raw insert stores the un-normalised configuration).
- T6 → `copyingADefinitionThroughTheRecordCommandIsRefused` (`sf-miss-copy.patch`).

Wrong fixes no test catches:

1. The raw maintenance insert (`FormDefinitionRepository::addRaw`, install-tool upgrade wizard) is never driven; a guard that leaves it open passes. (Recorded as a leniency gap in the manifest.)
2. A fix that refuses definitions containing finisher options such as `SaveToDatabase` inside the validated path: no functional test saves such a definition through the manager, so S4 is unenforced for that payload.
3. A fix that lets the write happen and then compensates by writing the same label/configuration/`deleted` values back: the tests compare only those columns, not `tstamp`/`crdate`, so the side effect is invisible.
4. A fix keyed on a caller/context flag that no attack request sets (e.g. a CLI or session marker) is not exercised, because no test forges such a marker.

## 3. Hints (QUALITY, non-blocking)

- "The examples above are examples, not the full set of the cases the property covers." — a coverage nudge that presupposes an example set; the instruction has one observation, not examples. Neutral: delete it (the property is already general).
- "Fix the problem and its close variants, not just the example." — same nudge ("close variants" invites hunting for unstated cases). Neutral: "Fix the problem; the property above covers every case." or delete.

## 3a. Required: generalize

- "…including reversing any removal that the framework's own path performed." — names one operation kind (reversal/restore) and exists only to keep the restore route fair; it is an operation pointer. General rewording: "Everything that does go through it keeps working exactly as today, for every operation the product performs on stored definitions and on whether each one counts as present or removed." This states the property once over the protected data; the state dimension is already in S1 and no route is named.

## 4. Realism (QUALITY, non-blocking)

T1–T3 are real core `DataHandler` code reachable through the generic record API; T4 (undelete) and T6 (copy through a nested `DataHandler`) are real, unmodified upstream routes the published hook left open and are realistic by definition. T5 (raw-connection bulk import) and the restore command are injected, but both are plausible maintainer code and reachable through the real `form:definition:import` / `form:definition:restore` commands. No planted or contrived trap code. (The `sf-miss-copy.patch` shortcut uses `dontProcessTransformations` as a trust marker; that is a wrong-fix check, not trap code.)

## 5. Verdict

**Gate a: READY.** Every security test is covered by the general property read literally: the six record-API tests drive an operation that would create, alter, remove, re-activate or duplicate a stored definition, and each refusal assertion asks for the invoking operation's own normal error result (`errorLog`; CLI exit status), which S2 requires. "Whoever invokes it" covers the administrative write. The two import tests accept either a normal refusal with no row or a store through the validated path normalised as `FormData`, so no single outcome is demanded; a raw insert is not a correct fix. Functional tests assert only that framework-path operations keep working and that the visible project behaviour is preserved. The natural fix following the stated mechanism (guard the generic record API; grant from the framework's persistence path) passes all 43 tests; the oracle's 3/3 reward-1.0 runs corroborate. A guard placed only at the HTTP/`tce_db` dispatcher is not a correct fix under S1 ("whoever invokes it" — CLI and internal callers stay open), so the DataHandler-driven tests do not unfairly fail a valid layer. No contradiction, synthetic harness or impossible demand.

**Required: generalize** — the restore clause listed in 3a.

**Quality to tighten**

- Add a functional test that stores a `SaveToDatabase` definition through the manager (enforces S4; currently a finisher whitelist wrong fix passes).
- Add a test driving `addRaw` (install-tool maintenance insert).
- Assert no side effect beyond label/configuration/`deleted` (e.g. `tstamp`/`crdate`) so a write-then-compensate fix is caught.
- Delete the two "examples/close variants" nudges.
- Keep the 3a rewording; it removes the only operation pointer without weakening the restore coverage.

GATE_A: READY
NEEDS_HUMAN_REVIEW: NO
