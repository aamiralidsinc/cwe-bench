# Instruction experiment: does "system + invariant" wording make round-1 tasks hard? (2026-10-16)

**Question.** Round-1 instructions were 409–687 words. They named parameters, folders, root causes and the
fix approach, listed every tested variant, and gave stacked tasks one section per flaw. The public
CWE-bench states only the system and the invariant. Would rewriting the instructions in that style be
enough to make our existing tasks fail?

**Design.**
- 7 round-1 tasks were copied to `tasks/<slug>-inv`. Only `instruction.md` changed; the environment,
  tests, oracle and patch checks are identical.
- Each rewrite was made by an Opus agent under a fixed brief, with a per-test fairness map
  (`build/<slug>-inv/FAIRNESS.md`). Each was reviewed by the lead before launch.
- Trials used the round-1 settings: offline, 2 h limit, both models, early stop at the first solve.
- Every graded run was audited by an Opus 5.5 sub-agent before it counted.

## Results (first graded run per model; minutes = agent phase)

| Task | DeepSeek (round 1 → -inv) | MiMo (round 1 → -inv) | Outcome |
|---|---|---|---|
| webob-inv | solved 15 → solved 15 | solved 41 → solved 33 | both solved (audited) |
| ruby-saml-inv | solved 16 → solved 26 (audit: lenient test) | solved 64 → solved 42 | both solved |
| actualbudget-inv | solved 9 → solved 42 | solved 28 → solved (retry after a build timeout) | both solved (audited) |
| async-http-client-inv | solved 65 → solved (100 wall) | solved 73 → solved 48 | both solved (audited) |
| asyncssh-inv | 0.92 → solved 65 | solved 96 → solved (108 wall) | both solved |
| filament-inv | solved 48 → *running* | solved 84 → *running* | |
| argo-workflows-inv | solved 47 → *running* | solved 77 → *running* | |

## Conclusion

**Wording is not the lever.** Every finished run solved the rewritten task. The terser report
sometimes made DeepSeek search longer (actualbudget 9 → 42 min, ruby-saml 16 → 26), but it never
made it miss anything. MiMo was, if anything, faster.

So both models infer the full set of variants from an invariant as readily as from a list. This
matches round-1 analysis B: they reliably cover breadth (encodings, verbs, roles, routes of one
accepted concept). Difficulty must therefore come from what the task contains:
- concepts the model dismisses (a protection that one route silently ignores);
- second-order consequences (a coupled value the natural fix breaks).

How a report is worded matters less than what the task contains.

**What changes in the pipeline.**
- BUILDER.md 3i (system + invariant style) stays as the instruction standard. It is closer to
  CWE-bench and removes fix hints the client would object to, but it is hygiene, not a difficulty lever.
- Effort moves to 3j (trap stacking on real pre-existing gaps). See `jackson-databind-sib2` (both
  models failed run 1, audited) and `marshmallow-readonly-sib`.
- The screener's role is now finding hosts with a protection marker that one route ignores
  (class A) plus coupled values. See the scout briefs used for marshmallow.

**Side findings.**
- Two audits (ruby-saml DeepSeek, asyncssh DeepSeek r12) found tests too lenient to separate a
  complete fix from an incomplete one. No test was added after the fact (`build/<task>/notes.md`). The
  new pre-trial fairness review (BUILDER 3h) asks exactly this question before trials.
- On this connection, Docker builds are not cached and take about 7 min each (×2 per run); one
  heavy image hit Harbor's 30-min environment-start timeout when 13 builds ran at once.
