# filament-inv: instruction experiment (2026-10-16)

Same environment, tests, oracle and patch checks as filament; only instruction.md was rewritten in system+invariant style (BUILDER.md 3i). Fairness map: FAIRNESS.md in this folder. The notes of the original task follow.

# filament — build notes

Stacking task from `filamentphp/filament` (Laravel admin-panel framework, PHP).

## Commit C
`e1f36a7316d75476f3301e044cc360d7cb746c56` (v4.11.4+2), chosen as the parent of the
temp-upload fix so the CWE-862 upload issue is open while the three MFA-cluster
issues (fixed only at 4.12.5 / 4.12.6 / 4.13.3) are also still open.

## Co-present vulns included (all verified open at C by reproduction)
- CWE-862 unauthenticated temp file upload on auth pages (GHSA-44wp-g8f4-f4v5)
- CWE-204 password-validity oracle on panels the account cannot access (GHSA-xwpv-pqxp-5v36)
- CWE-294 authenticator code usable after a newer one / replay (GHSA-r3j6-gpjw-qfjr)
- CWE-306 disable-MFA action with no password reauthentication (GHSA-7m6h-rg42-m449)

## Dropped
- CWE-287 GHSA-52xp (MFA "bypass" when recovery enabled): empirically a
  usability-oriented change, not a deterministic login bypass; cache/rate-limit
  state dependent -> flaky. Dropped.
- CWE-287/288 GHSA-pvcv, CWE-362/841 GHSA-mc5j, CWE-208 GHSA-5w46: fixed by 4.11.5
  (not co-present with the 4.12 cluster) and/or inherently timing/race flaky.

## Harness
PHP 8.4 (composer.lock pins symfony 8.1 which needs php>=8.4.1). The verifier runs
PHPUnit test classes under /tests that extend the framework's Orchestra Testbench
`Filament\Tests\TestCase` (autoloaded from /app/tests/src) with an in-memory SQLite
DB. Two fixtures live under /tests/src: an inaccessible MFA panel provider (its id is
absent from the User fixture's access allow-list) and a Livewire component exposing a
real file-upload field (for the legitimate-upload functional test).

## What the gate cannot see
The combined fix.patch is the real upstream source fixes ported onto C (overlapping
files meant the four upstream commits could not be applied verbatim as one series).
Manual in-container verification before the gate: nop -> 8/8 security fail, 7/7
functional pass; oracle -> 15/15 pass; subset_fix -> 2 security fail (CWE-306),
functional clean; disable_feature -> 1 functional fail; alt_correct_fix -> 15/15 pass.

## 2026-10-16 test repair
Brief: `build/audit/REPAIR-BRIEF-2026-10-16.md`. Items: `build/audit/lenient_items_2026-10-16.txt`
(filament RECs; `research/own-runs/TEST-REPAIRS.md` has no filament section) plus one item from
our notes (the upload refusal helper accepted any throwable).

### Items and decisions
- **Upload tests demand exactly 403** (REC mimo-r1-n002, mimo-r11): already fixed (2026-10-15/16:
  "exception or any 4xx"); the gate's exact-status check covers it.
- **Upload helper accepts any throwable, so a crash counts as a refusal** (our notes; == mimo-r11
  item; REC mimo-r11 "assert no signed URL / no upload event / not an Error"): fixed. New
  `tests/src/AssertsRefusal.php`: an escaping exception counts only when the app's own exception
  handler (the real one, not Livewire's rethrowing test wrapper) answers it with a 4xx other than
  419; a returned response must be a 4xx other than 419, or carry a validation error, and must not
  be 5xx/419; then no side effect: no `upload:generatedSignedUrl`, no `upload:finished`, nothing
  attached to the target property. 419 is excluded because Livewire answers every TypeError during
  a component update with 419 "Page Expired" (HandleRequests, when not in debug), so a 419 marks a
  crash. No exact class or status is demanded.
- **ManagementReauthTest catches any Throwable** (REC deepseek-r1-n002 (b)): fixed with the same
  helper: an escaping exception must render as a non-419 4xx; a returned response must not be
  5xx/419; side effect = secret AND recovery codes still set. Not required: an error on a field
  named `password` (in-form refusals such as a halted action stay valid).
- **Instruction sentence** (needed because a deliberate generic exception renders as HTTP 500,
  which the narrowed helper now fails; the instruction never said how to refuse). Added to the
  opening paragraph: "Wherever a request has to be refused, answer it as a client error (for
  example forbidden, or a validation error), not by failing with a server error." Static gate
  (leaks) passes.
- **Grader loads Filament\Tests\TestCase / tests/bootstrap.php from agent-writable /app/tests**
  (REC deepseek-r1-n002 (c)): skipped. The verifier runs in the agent's container and also trusts
  /app/vendor (phpunit, Livewire, Laravel); pinning /app/tests alone gives no integrity. Harness-wide
  issue of shared-mode grading; no run showed tampering.
- **Confirm nop still fails the upload tests** (REC deepseek-r12): done; nop fails 8/8 security
  (both upload tests with "accepted").
- **Harness items** (REC deepseek-r11: WebSearch through the provider, harvest misses tracked
  source; REC mimo-r11: regrade replay markers): skipped, outside tasks/filament (harness/tools).
- **Postmortem bundle lacks final-code/changes.patch** (several RECs): skipped, tooling.

### New patch checks (both on top of the reference fix; both PASS the old tests, verified)
- `upload_crash_refusal.patch` (security_fail): the login upload guard looks the field up and uses
  it without a null check, so a non-file target "refuses" by `Error` (HTTP 500). Fails both upload
  tests; functional clean.
- `reauth_crash_refusal.patch` (security_fail): the password is checked through a helper typed
  `string`; a wrong password gets a validation error, a missing one a TypeError (Livewire 419).
  Fails `test_disabling_mfa_without_a_password_is_rejected`; functional clean.
In-container: nop 8/8 sec fail, 7/7 func pass; oracle and alt_correct_fix 15/15; subset_fix
2 sec fail; disable_feature 1 func fail.

### Gate
`python3 build/slot.py 3 -- python3 -I builder/gate.py filament`: **PASSED** (stages ran 05:26-06:05
UTC; every stage has real per-test results, none errored despite the disk-full window): nop 0/8 sec,
7/7 func; oracle x2 15/15; subset_fix 6/8 sec; disable_feature 6/7 func; alt_correct_fix 15/15;
upload_crash_refusal 6/8 sec (both upload tests); reauth_crash_refusal 7/8 sec (no-password test).
Hardening/blind pass patches still absent (pre-2026-10-16 task, warning only).

### Regrade (saved final code, repaired tests; both ran 05:19-05:20 UTC, before the disk-full window)
| trial | old | new | failing tests |
|---|---|---|---|
| deepseek-r12 filament__ShThBfS | 1.0 (regrade) | 1.0 (regrade-20261016T051936Z) | none |
| mimo-r11 filament__nQD6JG9 | 1.0 (regrade) | 0.75 (regrade-20261016T051955Z) | UnauthenticatedUploadTest start + finish |
| deepseek-r11 filament__4dLdCRt | 1.0 (verifier) | not regraded | - |

- **mimo-r11 drop**: its guard refuses non-file targets by throwing its own
  `UnauthorizedTemporaryFileUploadException extends Exception` (no render/HTTP status), which
  Laravel answers with HTTP 500. Nothing is staged, so it has NO security defect; it fails only the
  "refuse as a client error" contract, which the instruction now states but did not state when
  the run happened. Recommendation: keep (filament, mimo) as solved from the previous regrade;
  do not let this regrade change the verdict.
- **deepseek-r11 not regraded**: its harvest is truncated (HARVEST.json truncated=true; 343 files,
  all vendor/ or .phpunit.cache, zero product source), so a replay would grade untouched code and
  write a false 0.0 that audit_results.py would prefer. The run is already excluded from offline
  pass@k (provider-side web search).
- Other filament trials have no final-code/changes.patch and cannot be regraded.
