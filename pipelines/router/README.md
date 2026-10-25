# Router: the three-step scale run

Design: `docs/PIPELINE-3STEP-DESIGN.md`. Every candidate repo gets one chance at the strongest recipe first:

1. **Stacking** builds the best usable stacked design of every repo it selected.
2. **Sibling injection (step 2)** builds from the screened repos stacking did **not** take.
3. **Sibling injection (step 3)** builds from the repos whose **stacked task was solved** by any model (both
   solved, or one solved = a single-model breaker; owner decision 2026-10-25).

All model work runs on DeepSeek (client requirement). Everything runs on the VM from `~/cwe-bench`.

## Run order

```
# Selection inputs (done 2026-10-25 for the full OSV pool): DeepSeek screens + reader + scores
bash pipelines/stacking/1-select/select_ds_fullpool.sh            # rebuilds out/screener-ds/, H4 ranking, reader jobs
#   ... run_reader.py (DeepSeek, --parallel 70) and score_stack.py, see that script's header

# Step 1: stacking batch, BUILD-PROMPTs, then the stacking queue (build phase; postbuild runs inside)
python3 -I pipelines/router/route.py stacking-batch --name batch2 --prepare
nohup python3 -I pipelines/stacking/6-trial/stk_queue.py build --slugs-file pipelines/stacking/out/batch2.txt --slots 25 \
  > pipelines/stacking/out/queue/batch2.nohup 2>&1 &

# Step 2: sibling pool from what stacking did not take; the sibling lane in the router's folders
python3 -I pipelines/router/route.py step2
export LANE_RECS=pipelines/router/out/step2/screener LANE_PIPE=pipelines/router/out/step2/pipeline LANE_SUFFIX=s2
python3 -I pipelines/sibling/4-select/lane.py pool && bash pipelines/sibling/4-select/select.sh deepseek \
  && python3 -I pipelines/sibling/4-select/lane.py prepare deepseek
#   build: pipelines/sibling/6-build/run_pipeline.sh deepseek <slug> per slug in $LANE_PIPE/slugs_deepseek.txt

# Step 3: whenever stacked verdicts arrive
python3 -I common/audit/audit_results.py >/dev/null && python3 -I pipelines/router/route.py step3
LANE_RECS=pipelines/router/out/step3/screener LANE_PIPE=pipelines/router/out/step3/pipeline LANE_SUFFIX=s3 \
  python3 -I pipelines/sibling/4-select/lane.py prepare deepseek

python3 -I pipelines/router/route.py status
```

Steps run as streams: step 2 can start as soon as the stacking batch is registered; step 3 is re-run as verdicts
come in. Trials, audits (failing runs only) and fairness follow each pipeline's GUIDE.

## Rules

| Rule | Where |
|---|---|
| One screen per repo feeds both recipes (same prompt) | `out/screener-ds/` |
| Stacking takes one design per repo: the best usable one; a batch file is never rewritten | `stacking-batch` |
| Step 2 excludes every repo any stacking batch took, every repo with an `stk-` build, every built repo | `step2` |
| Step 3 routes a stacked task once (state: `out/step3/routed.tsv`); skips a repo that already has a sibling build | `step3` |
| Task names: `stk-<repo>-<id>`, `<repo>-s2`, `<repo>-s3` | lane `LANE_SUFFIX` |
| Post-build checks run together (gate stages in parallel, blind fix, listing for stacking) | `common/gate/postbuild.sh` |
| Controls: not gated or trialled in the scale run (`STACK_CONTROLS=1` restores them) | `run_stack_pipeline.sh`, `stk_queue.py` |
| A gate covers only the files it gated; trials and regrades refuse a stale task | `common/gate/fingerprint.py` |
| Human answers to fairness questions: `build/<slug>/HUMAN-DECISION.md` (`DECISION: KEEP/REPAIR/DROP`) | `common/fairness/fairness_verdict.py` |

## Files

| Path | What |
|---|---|
| `route.py` | the router (this folder's only code) |
| `out/stacking_batches.txt` | registered stacking batches (names of `pipelines/stacking/out/<name>.tsv`) |
| `out/step2/screener/`, `out/step2/pipeline/` | step 2 pool and the sibling lane's files for it |
| `out/step3/screener/`, `out/step3/pipeline/`, `out/step3/routed.tsv` | step 3 pool, selection and routing state |
