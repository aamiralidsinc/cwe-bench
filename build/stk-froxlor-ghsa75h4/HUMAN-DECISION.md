# Human decision: stk-froxlor-ghsa75h4

DECISION: KEEP
DATE: 2026-10-26
BY: project owner
SOURCE: build/stk-froxlor-ghsa75h4/FAIRNESS.md (NEEDS_HUMAN_REVIEW: YES)

WHY: The fairness question was which security test was the sole failure in the 0.875 runs. The Opus post-run audits
(6 runs, all trustworthy model-failed, high) answer it: StatisticsOwnershipSecurityTest::testOwnershipPassDoesNotFollowLinkOutOfFolder
decided every run; no test was judged unfair. Both-model breaker kept.
