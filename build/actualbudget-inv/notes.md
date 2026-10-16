# actualbudget-inv: instruction experiment (2026-10-16)

Same environment, tests, oracle and patch checks as actualbudget; only instruction.md was rewritten in system+invariant style (BUILDER.md 3i). Fairness map: FAIRNESS.md in this folder. The notes of the original task follow.

# actualbudget notes

## 2026-10-16 test repair

Brief: build/audit/REPAIR-BRIEF-2026-10-16.md. Flagged items came from build/audit/lenient_items_2026-10-16.txt
(deepseek-r11 n001, deepseek-seq1, mimo-r4, mimo-r5, mimo-r6) and research/own-runs/TEST-REPAIRS.md. All of them say
security/03-file-authorization is too lenient. The caller's notes added two more items.

### Items and decisions
| Item | Decision | Reason |
|---|---|---|
| Cross-user overwrite of an existing file (upload-user-file) | fixed | The instruction says "overwrite it". New test: an attacker uploads over the victim's file and must get a 4xx. |
| Cross-user reset-user-file | fixed | The instruction says "reset it". New test: must get a 4xx. |
| Cross-user download-user-file | fixed | Follows from the stated property ("checks only that the caller is logged in, not that the caller owns the target file"), and What-to-fix names download as a file endpoint. In the new test the victim uploads a real file, and the attacker's download must get a 4xx. |
| Cross-user /sync | skipped | /sync is not among the actions the instruction lists. Reaching it would need the product's protobuf request plus a sync-state fixture (group id, key and format must all match) so that the attack succeeds on the vulnerable code. That is fragile, and the three probes above already close the leniency. The reference, alt and hardening fixes guard /sync anyway. |
| Unauthenticated probe on a second SimpleFIN/Pluggy endpoint | fixed | The instruction says "the endpoints that report and return bank-connection data" (plural). New tests: unauthenticated POST /accounts on SimpleFIN and on Pluggy.ai must get a 4xx. Both return 200 on the vulnerable code. |
| Second traversal payload (mimo-r4 rec) | skipped | Out of this repair's scope (security/02 was not flagged). |
| Any-4xx leniency (mimo-r4 note) | kept | §3g requires any-4xx, not one exact status. |

No change to instruction.md. Every new assertion is any-4xx and uses no product helpers.

### New patch checks
- `narrow_file_authz.patch` (security_fail): the reference fix without the per-file access check on upload (existing file), reset and download. Gate result: reward 0.8. It fails only the overwrite, reset and download probes; functional tests all pass.
- `bank_status_only_auth.patch` (security_fail): the reference fix with the session check attached only to /status, not to the whole router. Gate result: reward 0.8667. It fails only the two /accounts probes; functional tests all pass.

### Gate
`python3 build/slot.py 3 -- python3 -I builder/gate.py actualbudget` printed PASSED (log: gate-20261016-repair.log).
- nop: all 15 security tests fail and all 13 functional tests pass.
- oracle: 1.0 on both runs.
- Existing patch checks are unchanged:
  - subset_fix: security_fail
  - disable_feature: functional_fail
  - alt_correct_fix: 1.0
  - hardened_helper_fix: 1.0
- Warning carried over from before (pre-10-16 task): there is no `blind` pass patch.

### Regrade (tests tightened only, so only the 1.0 runs were regraded)
| Trial | Old | New | Failing tests |
|---|---|---|---|
| deepseek-r11-20261015-220916-n001/actualbudget__9dvaA4h | 1.0 | 1.0 | none |
| mimo-r4-20261015-181823-n001/actualbudget__fTfWRhc | 1.0 | 1.0 | none |
| mimo-r5-20261015-181843-n001/actualbudget__85umakJ | 1.0 | 1.0 | none |
| mimo-r6-20261015-181903-n001/actualbudget__gUsWnax | 1.0 | 1.0 | none |

deepseek-seq1-1791999676/actualbudget__Ddhvfz2 (1.0) could not be regraded because it has no final-code/changes.patch.
The other seq runs also have no final-code; mimo-seq1/2/3 are at 0.9.
