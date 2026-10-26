# Human decision: fastify-s2

DECISION: KEEP
DATE: 2026-10-26
BY: project owner
SOURCE: build/fastify-s2/FAIRNESS.md (NEEDS_HUMAN_REVIEW: YES)

WHY: The fairness questions (custom_compiler.test.js `received` assertions; whether `body: null` counts as "explicitly
leaves empty") concern tests that decided no run: every run of both models failed the fallback_handler tests (the
not-found handler's request schemas are never enforced), audited trustworthy. Both-model breaker kept.
FOLLOW-UP before shipping: relax invalid_schema_value.test.js so a fix that warns and serves on `body: null` is accepted
(the run audit judged the null case instruction-ambiguous).
