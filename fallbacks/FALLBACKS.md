# Fallbacks: pursue when the primary pipeline is insufficient

Pursue the approaches below as fallbacks when the primary pipeline cannot meet the project's
task count, quality, or delivery needs.

Published, already-fixed advisories remain the primary pipeline (patterns A and B in
`builder/PROMPT-TEMPLATES-SPEC.md`). Fallbacks provide additional sources of work.

## Fallback inventory

1. **Framework scouting without a published advisory as the starting point.** Investigate
   weaknesses in large frameworks, including Spring, Django and Rails, and assess the Django lead.
   For each investigation, record the repository, pinned commit, protection being studied and
   evidence needed to make a fair benchmark task.
2. **The jackson-databind polymorphic type-validator proposal.** Develop the brief from available
   evidence. Do not confuse this
   proposal with the existing `jackson-databind-sib2` task or inherit that task's results.
3. **Detailed technical briefs, notes and reports.** Use fuller mechanism explanations and local
   reproduction detail when summaries and tests alone are insufficient for design, verification
   or handoff. Keep solver-facing instructions subject to the existing fairness and answer-leakage
   rules; additional internal detail is not an excuse to disclose the solution to the solver.
4. **Incomplete or stopped briefs and replies.** Reassess and pursue them as
   fallbacks, including revisions, retries and model comparisons where the work is supported.
   Record attempt outcomes and the reason for each retry. Tool and provider restrictions apply
   to each attempt.
5. **Full handoffs and Hadi-derived task-design briefs.** Expand pointer-only handoffs when they
   omit useful reasoning, and develop a separate brief for applying Hadi's lessons to injected
   bugs when the shared builder brief is insufficient.
6. **Scout model comparisons.** Compare DeepSeek/MiMo and other available models for
   the scout when screener-only comparisons do not answer the fallback's needs.

## How to use a fallback

- Record the primary-path shortfall, selected fallback, intended scope and success criterion in
  the relevant task notes, then pursue that fallback.
- Keep advisory-backed screening records distinct from investigations with no published advisory.
  Use an explicit investigation brief for the latter; do not invent advisory IDs, published fixes,
  or pattern A/B labels to fit the existing screener schema.
- Record upstream leads in `build/audit/uncovered-routes.tsv`, including verification, current
  upstream status and disclosure status. Research eligibility does not settle the separate client
  decision about disclosure before external sharing.
- Apply the same build gate, blind fix, fairness review, trial acceptance bar and per-run audit.
  A fallback is a source of work, not evidence that a candidate works or meets the acceptance bar.
- Log prompt changes and attempt outcomes. If an attempt cannot proceed, retain the candidate
  and record the unresolved issue for reassessment.
