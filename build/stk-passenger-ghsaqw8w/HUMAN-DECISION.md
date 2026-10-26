# Human decision: stk-passenger-ghsaqw8w

DECISION: KEEP
DATE: 2026-10-26
BY: project owner
SOURCE: build/stk-passenger-ghsaqw8w/FAIRNESS.md (NEEDS_HUMAN_REVIEW: YES)

WHY: The fairness question was which single security test produced the 5/6 runs. The Opus post-run audits (6 runs,
all trustworthy model-failed) answer it: sec_tmpexedir_prepared_link (PlatformInfo.tmpexedir writes through a planted
link) decided every run; no test was judged unfair. The two keep-working tests the review flagged
(func_instance_symlinked_parent, func_instance_fresh_create_and_reuse) passed in every run, so they decided nothing.
Both-model breaker kept.
