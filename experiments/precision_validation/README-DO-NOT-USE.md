# precision_validation: FAILED EXPERIMENT. Do not use its code or builder.

**Status:** closed, 2026-10-24. It is kept for the record only. **Nothing in this folder is part of either
production pipeline.**

## What it tested

The question was whether a frozen pre-build score (the "new screener", `screener/`, `results/rule.json`) raises
the both-model breaker rate per build. Two arms were built with a frozen copy of the sibling builder (`root/`):
- **arm A:** 21 candidates above the bar of 3.8;
- **arm B:** 40 random candidates below the bar.

The runs happened on GitHub Actions (`actions/`), not on the VM.

## Result

The score did not hold up:

| Arm | Both-model breakers |
|---|---|
| A | 2 / 21 (about 10%) |
| B | 5 / 40 (about 12.5%) |

There was no throughput gain, and the new screener did worse. Production keeps the sibling screener
(`common/screener/`).

## Why the code here must not be reused

- `root/` is a **frozen, stale copy** of the builder and gate as they stood on 2026-10-21. It lacks the later gate
  fixes: blind-skip, harbor retry, `--allow-agent-host`, and parallel gate.
- It adds "rule (a)", a competent-partial-fix control that was **never adopted**. It also edited its own frozen
  copies after the outcomes existed, which breaks its pre-registration.
- The live builder and gate are in `common/builder/` and `common/gate/`.

## The one live dependency

`pipelines/sibling/1-pick/pick.py` reads three things here so that candidates this experiment already consumed
are **excluded** from fresh batches:
- `results/*.csv`
- `results/screener_v2/*.json`
- `inputs/*.jsonl`

Keep those paths, or update `pick.py` and `common/paths.py` (`PRECISION_VALIDATION`) together.

## What is not in git

`actions/` (23 GB of payloads and results) and the `*.local.json` account and run ids stay local; see `.gitignore`.
The detailed docs are `PLAN.md`, `PREREGISTRATION.md` and `PROVENANCE.md`.
