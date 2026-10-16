# Pipeline at a glance

**Goal:** Harbor security-fix tasks that **both** DeepSeek V4.1 Flash (effort max) and MiMo-V2.6-Pro fail in all 3
attempts. The failure must be the model's fault, not the task's. Details per stage are in [01-07](README.md).

| Stage | What it does | Key rules |
|---|---|---|
| **1 Mining** | Collects PyPI/npm advisories from OSV, GHSA and huntr, and resolves each fix commit | Fix commit must be after `PUBLISHED_AFTER` (2026-08-01), so the fix is not in the models' training data. A series of fixes is merged; for a backport the default-branch copy is used. Known advisories are never re-mined. |
| **2 Screening** | Keeps candidates that can become a good task, and scores them | Rejects dependency-bump, config, docs, CI and template-only fixes; fixes with no source change; repos with no tests; repos over 400 MB; fixes that are too small or too big. Score = breadth: up to 8 files, up to 4 directories, line band. |
| **3 Task builder** | Picks the best candidates, checks out the vulnerable commit, then **Opus 5.5** writes the task | **Ranking** = score + what results taught: families that never broke a model rank lower, and repos already solved, unbuildable or safety-flagged are skipped. **Docker build check** first. Opus writes the report, hidden tests and 3 check patches. **Validators:** no file or function names in the report, ≥3 security + ≥3 functional tests, no skips, check patches well formed. If Opus 5.5 declines, Opus 4.8 takes over. A safety flag retires the candidate. |
| **4 Validation** | Proves the task is sound before any model sees it | **Rubric** (10 blocking criteria: accurate, solvable from the report, real entry point, implementation-agnostic, realistic, not config). **Recall probe**: reject if both models name the fix file from the report alone. **Leak scan** of the whole image. **Reference fix scores 1.0** twice; **vulnerable code fails** the security tests. **Existing repo tests** pass before and after. **Shallow fix must fail**, **feature-removal fix must fail**, **alternative correct fix must pass**. A failure sends the task back for a rewrite (max 2) with feedback. |
| **5 Evaluation** | Runs both models, 3 attempts each | Harbor + **Claude Code agent** in the task image; 2 h per attempt; 5 tasks in parallel. Agent network is **allowlisted to the model API only**. **Grading in a separate fresh container**: only the agent's source patch crosses over. **Deterministic verdict**: solved = 1.0; partial fix or broken feature = failure; timeout = not counted. Early stop once a model solves. |
| **6 Packaging** | Writes the accepted task | Final reference-fix run, then the Harbor layout (`instruction.md`, `task.toml` with CWE/language/repo/source/entry point, `environment/`, `solution/`, `tests/`) in `data/05_accepted_harbor/<id>/`. |
| **Knowledge loop** | Every verdict teaches the next round | Automatic: `C_RESULTS.md`, model failure map, **failure analyses from trajectories**, **technique scoreboard**, learned ranking. The generator reads them every round. |

## Rules that make a task good

1. **Report**: behaviour only (impact and trigger), 150-400 words, no file, function or line hints, no fix
   prescription.
2. **Tests through a real entry point**, implementation-agnostic, offline and deterministic.
3. **Variants beyond the report** (other entry points, encodings, shapes, round-trips), **one test per variant**, so
   a partial fix still fails.
4. **Functional tests near the boundary**, so over-blocking fails.
5. **Fair**: the reference fix passes everything, no undisclosed numbers, variants share the root cause.
6. **Techniques that break the models** (measured): unnamed sibling path, parallel implementation, a "must keep
   working" clause that argues against the fix, second public API or input-shape variants, and big multi-file fixes.

## What can never happen

- The agent sees the hidden tests, the fix or the advisory, or reaches the internet.
- An LLM decides whether a model passed.
- A timeout is counted as a model failure.
- A task with a flaky or unfair test is accepted: the reference fix must score 1.0 and an alternative fix must pass.
