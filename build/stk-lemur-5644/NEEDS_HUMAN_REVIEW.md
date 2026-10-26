# NEEDS_HUMAN_REVIEW: stk-lemur-5644 v3 (both-model BREAKER candidate), 2026-10-25T02:30Z

- DeepSeek 0/3 [0, 0, 0], MiMo 0/3 [0, 0, 0]; all 6 runs audited trustworthy model-failed (Opus 5.5-high;
  DS r1-r3 high, MiMo r1 medium, r2/r3 high). Fairness (v3, 2026-10-25T01:23Z): READY, NEEDS_HUMAN_REVIEW
  only to confirm the deciding test (confirmed below).
- **Same shape as mistral-rs: every failure is a keep-working regression.** Security passed 11/11 in all six
  runs. Each model also re-validated addresses that were ALREADY STORED (at fetch time, in the backend's own
  write-back via update_options, or by refusing an empty acmeUrl override), so legacy authorities (stored
  acme-v01 URL) stop working. Deciding tests: functional/test_legacy_directory.py
  (test_stored_directory_is_still_contacted, test_account_write_back_keeps_legacy_directory,
  test_configured_directory_is_still_contacted).
- Instruction: the check applies to an address "when it arrives in a user request", plus "Everything that
  works today keeps working". Several transcripts show the model saw the legacy case and over-fixed anyway
  ("defense-in-depth").
- Trap: T5 (origin uncovered_upstream): validating the effective/stored address instead of the incoming one.
- Decide: same question as mistral-rs (a breaker made only of keep-working regressions). Not committed, not shipped.

## User decision (2026-10-25 ~05:00Z)
KEEP. Ask Klavis together with mistral-rs (keep-working breaker class).
