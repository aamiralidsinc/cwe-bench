# Breaker confidence label (design, not implemented)

Status: design note, 2026-10-28 (client audit PO-3, process fix 5). Nothing below is built yet. The
per-run audit-confidence table in `queue.db` is a separate plan and is not part of this note.

## Why

The PO-3 review kept three breakers whose verdict rests on one reading: cline-s2 (one sentence about
ports), katex-s2 (auto-render only) and kuma-s2 (tools/xds-client only). The owner labelled them THIN in
the "Client audit PO-3" sections of their `HUMAN-DECISION.md`. Today that label is free text that no tool
reads, and the delivery does not carry it. Each delivered breaker should carry one label that says how much
of its verdict depends on judgement.

## The label

| Label | Meaning |
|---|---|
| `high` | Every counted failing run fails at least two independent fair tests (no single test decides it). The review has no conflicts and NEEDS_HUMAN_REVIEW is NO. Every audit is trustworthy at high confidence. |
| `medium` | At least one run is decided by a single test, but that test is fair on any reasonable reading. Or an audit has medium confidence. |
| `low` | A defensible other reading of one test or sentence would flip at least one model. The breaker is kept by an owner ruling. |
| `thin` | The verdict for a model rests on one route or one reading the client could plausibly dispute, for example a single narrow module or one ambiguous sentence. The owner keeps it and expects a challenge. |

The owner sets the label. The pipeline only proposes one (see below).

## Where it is recorded

The label goes in `build/<slug>/HUMAN-DECISION.md`, next to the decision it qualifies:

```
DECISION: KEEP
DATE: 2026-10-28
CONFIDENCE: thin
CONFIDENCE-WHY: DS 3/3 and MiMo r1 fail only contrib/auto-render
```

- The existing inline form (`CLIENT-AUDIT: KEEP, CONFIDENCE: THIN`) is also read.
- The last `CONFIDENCE:` in the file wins, so a later client-audit section overrides the first decision.
- The value is case-insensitive.
- Reader: `markers.confidence(b)` returns `(label, why)` or None, next to `markers.human_decision`.
  It uses the same regex style, and `fairness_verdict.py` reports the label after the decision.
- Contract checker (`markers.check`): a KEEP without a label gets a `warn` (`confidence-missing`); an unknown
  value gets an `error`.

## Proposal (mechanical, for the owner to confirm)

`fairness_verdict.py --propose-confidence <slug>` would print a label and its reasons. It reads only these
files:

- **Audits.** For each counted failing run, the `POSTMORTEM.json` confidence. Any `low` caps the label at
  `low`; any `medium` caps it at `medium`.
- **Deciding tests.** From `trial_summary.md` (the "Failing tests per run" section added 2026-10-28): a run
  with exactly one failing test caps the label at `medium`.
- **The review.** `NEEDS_HUMAN_REVIEW: YES` with a KEEP ruling caps it at `low`. A deciding conflict that the
  owner ruled fair also caps it at `low`.
- **Thin.** The pipeline never proposes `thin`. Only the owner sets it.

The proposal is printed in the inbox's keep section, so the owner confirms or changes it together with the
decision.

## Into the delivery

- `delivery.py prep` copies the label into `ready.json` (`confidence`, `confidence_why`).
- `cweq delivered` writes it as a fifth column (`confidence`) of `build/audit/delivered.tsv`. Old rows keep four
  columns; readers treat a missing column as unknown.
- `export_delivery.py` writes it into `EXPORT-REPORT.md` (internal).
- A missing label is a `ready.json` problem only after a switch-over date. Before that date it is a note, so
  the packages already staged are not blocked.

**Decision needed:** whether the label goes into the client package (for example `[metadata] confidence` in
`task.toml`, or a column in the client README). The default is internal only: the client sees the tasks, and
the label is a statement about our own certainty.

## Tests to add with the implementation

- **Reader:** the last label wins, the inline `CLIENT-AUDIT` form is read, and a bad value is an error.
- **Proposer:** each cap applies, and `thin` is never proposed.
- **Delivery:** `ready.json` carries the label, and the register gets its fifth column.
