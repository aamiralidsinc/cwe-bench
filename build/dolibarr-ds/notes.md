# dolibarr-ds build notes

- Start (UTC): 2026-10-24T02:43:42Z
- End (UTC): 2026-10-24T03:47:24Z

Task: Dolibarr REST API missing management-hierarchy check on employee records
(GHSA-7FG5-VC77-69FP / CVE-2026-10215), pinned at 3566f80aa88fd26b295ad8762d02327915ee79ec,
published fix ee93b6f2f9dd0f6aeefe9d718ab3ab0a44326b73. Pattern A+B, injected track.

## Levers (one line each)

1. **T1 / Pattern A far site (where-type).** Every per-record leave endpoint passes only the
   record id to the shared access helper; the expense-report API does the same for all 13 of
   its per-record and line endpoints. Reason to dismiss: the report is about leave requests, and
   expense reports are a separate module, so the second API reads as out of scope.
2. **T2 / Pattern B route where the protection never existed (how-type).** `GET
   /expensereports` returns every expense report in the entity to any holder of the ordinary
   read permission; the caller-controlled user filter looks deliberate and the per-object fix
   pattern does not apply. Fix needs a hierarchy filter over the list mechanism.
3. **T3 / Pattern B route where the protection never existed (how-type).** Creating a record
   accepts a target-user field from the payload, and updating one copies a request-supplied
   owner/approver after the object check. Reason to dismiss: creation has no existing object to
   check, and the update is considered covered because the check runs on the fetched record.
4. **T4 / injected sibling (how-type, shape trap).** A batch read hands the raw
   comma-separated id list to the shared check; the check sanitises it and, because it is not
   an object, silently skips the hierarchy test. Reason to dismiss: the check is visibly present
   at the entry point and looks correct.
5. **T5 / injected sibling (how-type, wrong object).** A derived summary authorises the
   owner's user record instead of the leave itself. Reason to dismiss: it returns an aggregate,
   not the record, and an access check does run.

Coupled must-keep-working: the designated approver keeps access to a leave whose owner is not
their report; self-service, subordinates, the all-user read permission and the all-user write
permission all keep working; list filtering and batch reads keep returning permitted records.

## Gate results

- static: PASS
- nop: PASS (security 0/32, functional 54/54)
- oracle: PASS, three runs each reward 1.0 with 86/86 and identical per-test maps
- patches: PASS, 9/9 checks behave as declared (six security_fail, one functional_fail, two pass)

## What was verified

- The flaw reproduces at the pinned commit through real HTTP: a MariaDB database built by the
  project's own installer, the app served by PHP's built-in server, DOLAPIKEY-authenticated
  requests. Every tested route (leave per-record actions, expense per-record actions and lines,
  list, creation, attribution update, batch, summary) succeeds against an outsider's record.
- The reference fix (`solution/fix.patch`, applied by `solution/solve.sh`) makes all 32 security
  tests pass and keeps all 54 functional tests (40 hidden + 14 project) passing.
- Every wrong-fix patch behaves as declared against the real suites (run in a scratch
  container with the same seed and runner): six security_fail patches leave only their lever
  open with all functional tests passing; the over-broad patch passes security but fails 28
  functional tests; the hardening and alternative fixes score a full pass.
- The project's own tests for the area (`HolidayTest`, `ExpenseReportTest`, 14 tests) pass on
  the pinned/injected tree, on the oracle and on every variant.
- Hidden tests never run in the agent image; the verifier copies them from /tests at grade time.
- The pinned tree contains no regression test for this advisory (the fix commit is the first
  test-related change and is not present).

## What could not be verified

- Long-run flakiness: the suites were exercised repeatedly in a scratch container but not under
  Harbor load. Each suite is short (under a second of PHPUnit work) and the server/DB are local.
- The verifier image build and the full test.sh were exercised by the gate (nop, oracle, patches) through Harbor, in addition to the local Docker builds.
- Upstream `develop` was inspected read-only to fill `present_in_latest`; whether the update-time
  attribution gap is still exploitable upstream is recorded as unknown.

## Fairness concerns

- The report names the two protected data classes (leave requests and expense reports) because
  the tests cover both; it names no route beyond the one impact example, no file, field,
  function or permission identifier, and no root cause. The list, creation, attribution, batch
  and summary shapes are covered only by the general rule.
- The all-user read and write permissions are stated in product terms; the solver must find the
  module permission names in the code (standard project knowledge from the rights definitions).
- The injected siblings are ordinary-looking additions beside existing endpoints; both are
  reachable from the report's rule and neither is described there.

## Out of scope (not built on)

- `dol_check_secure_access_document` passes the global `$user` instead of `$fuser`, and the
  generic documents API lists file metadata with only a module right; not pursued.
- The fix commit message cites GHSA-qjj8-wpvx-p54j rather than the advisory id above.
