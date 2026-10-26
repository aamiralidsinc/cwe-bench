# NEEDS_HUMAN_REVIEW: stk-gitpython-ghsawvpp v2 (both-model BREAKER candidate), 2026-10-25T00:20Z

- DeepSeek 0/3 [0.875 x3], MiMo 0/3 [0.375, 0.625, 0.375]; all 6 runs audited trustworthy model-failed
  (Opus 5.5-high; DS r1 high, r2/r3 medium; MiMo r1-r3 high). Ledger: build/audit/ledger.md.
- Fairness (stacking/run_fairness_stack.sh, DeepSeek): READY (gate a). FAIRNESS.md S7 sets
  NEEDS_HUMAN_REVIEW: YES because each DeepSeek run was decided by ONE test,
  test_remote_listing_refuses_program_option_value (ls-remote --exec, git's documented alias of
  --upload-pack, not named in the instruction; the invariant "no caller option value may make git run a
  program of the caller's choosing" covers it read literally).
- MiMo failed more widely: dash-prefixed / joined single-char option values on clone, archive --output
  (it never touched the shared candidate builder).
- Decide: is the --exec alias fair unstated expert knowledge? Quality items (non-blocking) are in
  FAIRNESS.md "Quality to tighten". Not committed, not shipped.
