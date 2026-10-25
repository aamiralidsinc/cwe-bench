# Batch-level metrics for comparing pipelines

**Status:** agreed 2026-10-25, before the first sibling-vs-stacking quality audit. These metrics may be revised
after that audit; record any change and its reason at the end of this file.

**Purpose:** decide which pipeline to scale toward the 100–200 task target by comparing *breaker quality*, not only
breaker count.

**Sources for every metric:**
- `build/audit/ledger.md` (from `common/audit/audit_results.py`), the only source of verdicts;
- per-run audits (`postmortem-*/verdict.json`);
- fairness reviews (`build/<slug>/FAIRNESS.md`);
- task manifests (`build/<slug>/manifest.json`: traps, origins);
- stage records (`build-run.json`, gate reports, trial details).

A metric is computed only from **audited, final** verdicts.

## A. Throughput and cost (per batch)

| # | Metric | Definition |
|---|---|---|
| A1 | Stage funnel | screened → built → gated sound → trialled → both-model breakers / single-model breakers, with the drop at each step |
| A2 | Breaker yield | both-model breakers ÷ built tasks, and ÷ screened candidates |
| A3 | Cost per breaker | agent-hours and tokens (builder, gate, trials, audits, repairs) ÷ breakers |
| A4 | Wall-clock per breaker | elapsed days ÷ breakers, at the concurrency actually run |
| A5 | Repair burden | test faults, fairfix rounds and in-place fixes per task before it was fair; human decisions needed |

## B. Breaker strength (per breaker, summarised per batch)

| # | Metric | Definition |
|---|---|---|
| B1 | Failure type | **security miss** (a hole left open), **keep-working regression** (broke legitimate use), or **contract only** (wrong status code or error form). The share of each |
| B2 | Decisiveness | number of distinct tests that decided the failing runs. One test is fragile; several are robust |
| B3 | Margin | reward per run; whether any run came close to solving |
| B4 | Consistency | the same failure in every run, or different failures |
| B5 | Audit confidence | the confidence of every failing run's audit (high/medium); fairness READY with or without an open human-review flag |
| B6 | Open-internet survival | is the decisive trap covered by the public upstream fix? Traps it does not cover ("uncovered upstream") survive a model that looks the fix up |
| B7 | Hint exposure | did the instruction leak traps (listing check / surface-leakage rule)? Did it fail even with hints? |
| B8 | Solvability | the reference fix passes; an independent blind fix passed the strict gate |

## C. Diversity and similarity (across breakers)

| # | Metric | Definition |
|---|---|---|
| C1 | Coverage spread | distribution over CWE class, mechanism (path traversal, SSRF, authz, injection, …), language/ecosystem and repo domain |
| C2 | Trap-shape spread | trap origin (uncovered upstream / published far site / keep-working value / injection room) and the decisive pattern (e.g. "missed second copy", "missed alias", "over-validated stored data") |
| C3 | Near-duplicates | pairwise similarity on C1 + C2 + B1; flag re-skins. The client's agent generates variants itself, so re-skins add no value |
| C4 | Concentration | share of breakers in the largest similarity cluster; repo reuse (several tasks from one repo) |

## D. Pipeline-specific

| # | Metric | Definition |
|---|---|---|
| D1 | Stacking lift | stacked vs one-bug control fail rate: does stacking itself add the difficulty? |
| D2 | Injection realism | sibling: are injected sites plausible code an engineer would write, or obviously planted? |

## E. Headline: strong breakers

A **strong breaker** meets all six:
1. Both models fail 0/3.
2. Every failing run is audited trustworthy, and most at high confidence.
3. Fairness is READY, with no open human question.
4. At least one decisive failure is a **security miss** (not only a regression or a contract failure).
5. The decisive trap is not covered by the public upstream fix.
6. It is not a near-duplicate of another breaker.

The headline comparison between pipelines is **strong-breaker yield per batch** and **cost per strong breaker**.

## F. Single-model breakers (in case single-model breakers are accepted)

| # | Metric | Definition |
|---|---|---|
| F1 | Single-model yield | exactly one model fails 3/3 (audited and fair) and the other solved, ÷ built tasks. DeepSeek-only and MiMo-only are reported separately |
| F2 | Combined yield | (both-model + single-model breakers) ÷ built tasks |
| F3 | Strong single-model | the E test applied to the failing model |
| F4 | Near-miss rate | single-model breakers where the solving model needed all 3 runs or solved only once. These are the closest to becoming both-model breakers |

## Reporting rules

- **Sample sizes are small** (stacking batch 1: 30 tasks; sibling eras: about 125). Report counts with ranges, not
  only point estimates.
- **Scope of the first audit:** sibling batch-1 lane plus the injected rounds (sibling2 is excluded because it is
  untrialled), and stacking batch 1. It runs after all pending audits are recorded.

## Revisions

- 2026-10-25: initial list (A–E), plus F (single-model breakers) at the user's request.
