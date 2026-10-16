# Handoff and next steps (2026-10-16)

Read this first in a new conversation. Commit only to `aamiralidsinc/cwe-bench`.

## Read these, in order
1. `plan.md`: the goal and the overall plan.
2. `RESULTS.md`: results; the "Round 2 (2026-10-16)" section is the latest.
3. `build/audit/ledger.md`: per-task verdicts. Regenerate with `python3 build/audit_results.py`;
   this is the only source of truth.
4. `builder/BUILDER.md`: how a task is built (sections 3h–3j are the 2026-10-16 defaults).
5. `builder/BRIEF-trap-stack.md`: the builder brief, with every lesson learned so far.
6. `research/instruction-experiment.md` and `research/round1-analysis/`: the analyses.
7. `sourcer/rerank-v4-draft/README.md`: the draft host ranking.

## Briefs used in the pipeline (all in `builder/`)
- `BRIEF-trap-stack.md`: the builder.
- `BLIND-FIX-BRIEF.md`: the blind fix.
- `FAIRNESS-REVIEW-BRIEF.md`: the pre-trial fairness review.
- `build/audit/REPAIR-BRIEF-2026-10-16.md`: test repair.
- The post-run audit brief is written per run by `build/postmortem.py prepare`.

## Process (per task)
1. Build.
2. Blind fix.
3. Fairness review.
4. Strict gate.
5. Trials, both models, up to 3 runs each, offline, 2 h limit.
6. An audit of every graded run, before it counts.

## Rules
- Every graded run is audited before it counts.
- A run cut by an API or network error is never a failure; the code enforces this.
- Timeouts are not failures.
- Never add tests after seeing a solve unless the user approves, and then regrade every saved run
  of every model.
- Ask the user before changing parallelism, and never prune the Docker build cache.

## Next steps
1. Reader pass over the top 30 of `sourcer/rerank-v4-draft/host-shortlist-40.tsv`.
2. Build the confirmed hosts in the process above, following `BRIEF-trap-stack.md`.
3. Write one shared screener prompt and one shared task-build template, with per-task inputs.
   Keep both on published, already-fixed advisories and on building the benchmark task. If a
   brief is stopped by a safety check, do not route it through another model; narrow it instead.
4. Raise with the client:
   - `jackson-databind-sib2` (the breaker candidate);
   - Hadi's DeepSeek-only result;
   - `research/partial-progress-60min.md`;
   - whether the maintainers should be told about previously unreported gaps used in tasks.
