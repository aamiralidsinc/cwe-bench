# NEEDS_HUMAN_REVIEW: stk-senaite-core-4280 v2 (both-model BREAKER candidate), 2026-10-25T01:25Z

- DeepSeek 0/3 [0.8182 x3], MiMo 0/3 [0.8182 x3] on the corrected tests; all 6 counted runs audited
  trustworthy model-failed (Opus 5.5-high; mostly MEDIUM: the report never names the read route).
  MiMo r1 was a test fault (record-parsing test demanded a refusal the instruction does not state) and is
  excluded; MiMo r2 crashed (CancelledError, ungraded).
- **The one decisive miss, all 6 runs:** the read route's include_methods (load_method_values) still runs
  any method the caller names (e.g. refreshTotals), so a read changes stored data the caller may not
  write. Both models fixed the per-field write checks and the eval sinks.
- Fairness: READY (gate a), review written 2026-10-24T22:26Z on v2. **Caveat:** at ~23:19Z I fixed the
  record-parsing security test IN PLACE (removed a stored-value assertion; backup in
  build/stk-senaite-core-4280/testfix-20261024/). No version bump: the DeepSeek runs passed that test
  either way. The fairness review predates that edit.
- Decide: is "a read changes data" covered fairly by the general first requirement without naming
  reads? Not committed, not shipped.

## User decision (2026-10-25 ~02:35Z)
FAIR, KEEP. The fixture stand-in (refreshTotals) stays: project rule is that tests never call original product functions; fixtures model the behaviour. The real sink (load_method_values runs any caller-named zero-arg method; real writers include Client.remove_group/create_group, Worksheet.workflow_script_reject) is the bug the fixture models.
