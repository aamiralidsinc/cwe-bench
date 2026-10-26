# typo3-ds — build notes

- Start (UTC): 2026-10-19T18:12Z
- End (UTC): 2026-10-19T19:29Z

Advisory: GHSA-JH32-V29G-68PQ / CVE-2026-49741 (TYPO3 CMS form framework, CWE-862 leading to
CWE-89 in the save-to-database finisher). Pinned (vulnerable) commit: 44c2fa9807944136218a0842e3051c0a379a002d,
the parent of the published fix c90493c13b633f328cf2c066182c90a1655ff0fc.

## Levers (one line each)

- T1 (pattern A, far site): generic record write (create) of a stored definition through the core
  DataHandler API — `typo3/sysext/core/Classes/DataHandling/DataHandler.php:708-709`; dismissed as
  "the table is UI-protected and this is generic core code in another package".
- T2 (pattern A, another verb): generic record command (soft delete) — `DataHandler.php:3233-3241,3300`;
  dismissed as "removal writes no configuration, so the injection impact does not apply".
- T3 (input shape): partial record update with an integer uid and no configuration field —
  `DataHandler.php:708-709`; dismissed as "ordinary partial saves are how the record API works".
- T4 (pattern B / injected maintenance path): re-activating a soft-deleted definition through the
  record command — `DataHandler.php:3303-3305` (real, unmodified upstream core; the published hook
  returns early for commands other than delete), with an injected `form:definition:restore` command
  as the legitimate user of the same command; dismissed as "restoring writes no configuration".
- T5 (injected sibling): administrative import command that writes definitions through a raw
  connection — `FormTransferService.php:171` + `ImportFormDefinitionsCommand.php:67`; dismissed as
  "a command-line tool runs as an administrator and is outside the advisory".

T1–T3 are the published fix's far site (core record API vs the form extension); the fix also covers
delete. T4 is an upstream-uncovered route; T5 is the injected sibling. Coupled legitimate behaviour:
manager save/update/remove, the restore command for definitions removed through the form framework,
and the extension-to-database transfer.

## Verified

- Toolchain: PHP 8.2 (`php:8.2-cli-bookworm`, intl/pdo_sqlite/mbstring), `composer install` from the
  committed lock (typo3/testing-framework 1a571c8, phpunit 11.5.55), sqlite functional tests, all
  offline after the image build. The full `typo3/sysext/form/Tests/Functional` suite is green on the
  pinned tree (379 tests).
- Pinned+injected tree: a non-admin backend user with table-modify permission can create, fully
  update, partially update, delete and undelete stored definitions through the record API, and the
  import command stores an unvalidated definition (nested and serialized shapes). All 7 hidden
  security tests fail; all 34 hidden functional tests pass.
- Oracle tree: 7/7 security and 34/34 functional pass, reward 1.0.
- Wrong-fix patches: the gate `patches` stage passed all 14 declared checks at 2026-10-19T19:28Z
  (`build/typo3-ds/gate_report.partial.json`): 10 security_fail (each with functional all green),
  2 functional_fail, hardening pass reward 1.0, alt-fix pass reward 1.0. Earlier stage attempts were
  cut only by the shared-machine docker-network-prune race during `docker compose up`, an
  infrastructure failure; the stage passed as soon as a trial sequence was not cut that way.
- The instruction names no file, class, table, command or advisory identifier; the static gate
  passes every check except the two downstream-owned items (blind patch, FAIRNESS.md).

## Not verified / guesses

- The pinned commit was not stated by the advisory; it is the parent of the published fix commit
  (44c2fa9807…). The repository copy's git metadata shows it as the fix's direct parent.
- `addRaw` (raw insert for the install-tool upgrade wizard) was not made a lever: it is an
  administrator/install-tool migration path and the screener dismissed it; not reachable from a
  backend user's request.
- DataHandler `move` was probed: it changes only pid, adds no definition content and is outside the
  property (storage placement is not the definition or its present/removed state), so it is not
  tested. `copy` was initially dismissed on the same ground; the 2026-10-20 upgrade showed that is
  wrong: the copy command stores a *new* definition in the stored set (verified: the pinned tree
  goes from 3 to 4 rows), so it is now covered (see below).
- Whether the published hook's field HMAC would accept every shape a future legitimate caller sends
  was not explored; the oracle's legitimate paths are the ones the hidden functional tests drive.

## Out of scope noted, not built

- Frontend reads skip backend permission checks by design (DatabaseStorageAdapter); not pursued.
- `addRaw` / install-tool migration and deleting a parent page's records by cascade were not used.

## Upgrade 2026-10-20 (sibling-injection rules §2–§8)

- Instruction: rewritten to state one property over the stored definitions and their stored state
  ("present or removed"). Removed every pointer to a route/channel/operation kind/field shape:
  "record write", "record editing interface", "record operation", "command exits non-zero",
  "operations that carry no configuration field at all", "the form editor, the form manager and the
  product's command-line tools", and the "save-to-database" example. The must-keep contracts stay,
  stated generally (the framework's own path keeps working, including bringing back a definition it
  itself removed; an operation counts as legitimate only when it goes through that path).
- Levers: unchanged T1–T5. How-type levers were already present: T4 is a route the published fix
  left open (undelete) coupled to the product's legitimate restore through the same command (M4/M11);
  T5 is a producer the check never calls (raw insert on the import path, M6).
- Coverage: a route the property covers literally was untested — the record command that copies a
  definition. On the pinned+injected tree a non-admin with table modify duplicates a definition
  (3 → 4 rows); the oracle refuses it through the nested DataHandler datamap guard. Added
  `RecordApiCommandTest::copyingADefinitionThroughTheRecordCommandIsRefused` (row count + error
  result, computed in the test) and `checks/sf-miss-copy.patch` (a fix that trusts internally
  generated identifiers and misses only this route).
- `checks/hardening.patch` was extended so its unknown-command denial is reported through the
  operation's normal error result; without that it refused the copy silently and failed the new
  test. It is now a stricter correct fix (reward 1.0).
- Local verification (dev harness, `typo3-dev-base`, same tests dir the grader uses): nop 8/8
  security fail, 34/34 functional pass; oracle 1.0; alt-fix 1.0; hardening 1.0; sf-miss-copy
  security_fail with functional all green and exactly the copy test failing.
- No repo code changed, so the image was NOT rebuilt; tests/solution/environment unchanged except
  the added security test (tests/) and the check patches (build/checks/).
- Static gate: PASS except the two downstream-owned items (blind patch, FAIRNESS.md).

## Fairness revision 2026-10-20 (build/typo3-ds/FAIRNESS.md)

- Gate a: the two import tests demanded refusal for a definition a correct fix could
  legitimately store through the framework's validated path. They now accept either (a) a
  non-zero exit with no stored row, or (b) exit 0 with exactly one row whose `configuration`
  is the definition as the framework's own persistence path normalises it
  (`FormData::fromArray(...)->toArray()`); a raw insert stores the un-normalised input and
  still fails. Test names updated to say so.
- Instruction: applied all six "Required: generalize" rewritings, removed the root-cause
  sentence and the partial-save hint, and narrowed "every existing way of managing stored
  definitions keeps saving changes" to "…that goes through the framework's path".
- Coverage (quality): added `anAdministrativeRecordWriteOfADefinitionIsRefused` to the
  record-API write tests. It runs with the harness's administrator user and catches a guard
  that refuses only non-administrative callers.
- Not done (quality gap): no test drives the raw maintenance insert (`addRaw`, used by the
  install-tool upgrade wizard). Exercising it needs the upgrade-wizard/filemount staging
  context, and guarding it would need an oracle change that could regress the legitimate
  install-tool migration. The general property covers the route, so this is leniency, not
  fairness.

## Hardening 2026-10-22 (Frontier 1.4 conversion)

- Why: in the six graded runs every record-layer trap (T1/T2/T3/T4/T6) was fixed by every
  run of both models; only the raw-connection bulk import (T5) was missed by every run, so
  one trap carried the task. T7 and T8 give two more independent traps with different
  reasons to dismiss, so a run that fixes the import still fails on another.
- T7 (maintenance delete): `DataHandler::deleteAction()` is called directly by the recycler
  (`DeletedRecords::deleteData`) and by `cleanup:deletedrecords`, so the record-command map
  hook the published-style fix relies on never runs. The oracle also implements
  `processCmdmap_deleteAction` and leaves the repository's delete grant for it, so the
  manager's own delete still works. Security test: `RecordApiMaintenanceTest`. Coupled:
  permanently deleting an ordinary `tt_content` row through the same API still works
  (`MaintenanceApiTest`).
- T8 (preset rewrite): the injected `FormDefinitionPresetService`
  (`form:definition:apply-preset`) merges a preset into a stored definition and writes it
  with a raw connection `UPDATE`; no record-layer check sees it. The oracle routes it
  through `FormPersistenceManager`, and the security test accepts either a refusal with no
  side effect or the framework-normalised store. Coupled: the manager still saves a
  definition that contains a `SaveToDatabase` finisher (instruction bullet "A stored
  definition may contain any configuration the form setup allows").
- Checks: `sf-miss-maintenance.patch` and `sf-miss-preset.patch` each fail exactly their
  own test with all functional tests green; `hardening.patch` and `alt-fix.patch` were
  extended to close T7/T8; `blind.patch` is an independent trusted-scope correct fix
  (required by the strict static gate's blind pass control).
- Delivery: Frontier schema 1.4 — `/workspace` in both images, separate offline verifier,
  uid-1000 non-root grading, canary GUID, `artifacts` restore, dual scoring/metrics.json.
  The hidden suites are copied to `/workspace/.htests` at grade time; all test-internal
  paths now derive from that copy.
- Local verification (built env toolchain): pinned 11/11 security fail + 36/36 functional
  pass (reward 0); oracle 11/11 + 36/36 (reward 1.0); each new check patch fails only its
  own test; hardening/alt-fix/blind 11/11 + 36/36.
- Gate: static PASS (`conformance_check` prints "conforming"); nop PASS (11 security fail,
  36 functional pass); oracle PASS (3/3 reward 1.0, identical); patches PASS (18/18: 13
  security_fail with functional green, 2 functional_fail, hardening/alt-fix/blind at 1.0;
  sf-miss-maintenance and sf-miss-preset each fail exactly their own test).
