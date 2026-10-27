# Router: the three-step scale run

Design: `docs/PIPELINE-3STEP-DESIGN.md`. Every candidate repo gets one chance at the strongest recipe first:

1. **Stacking** builds the best usable stacked design of every repo it selected.
2. **Sibling injection** builds from one general pool: the screened repos stacking did **not** take, plus
3. the repos whose **stacked task was solved** by any model (both solved, or one solved = a single-model breaker).
   Step 3 only routes a solved stacked task into that general pool; it is ranked with every other sibling candidate
   and built only where its score places it (owner rule 2026-10-27).

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
python3 -I pipelines/router/route.py pool          # general pool file, without built and batched repos
export LANE_RECS=pipelines/router/out/step2/screener LANE_PIPE=pipelines/router/out/step2/pipeline LANE_SUFFIX=s2
bash pipelines/sibling/4-select/select.sh deepseek && python3 -I pipelines/sibling/4-select/lane.py prepare deepseek
#   build: pipelines/sibling/6-build/run_pipeline.sh deepseek <slug> per slug in $LANE_PIPE/slugs_deepseek.txt

# Step 3: whenever stacked verdicts arrive (the work queue's step3 job runs this every half hour)
python3 -I common/audit/audit_results.py >/dev/null && python3 -I pipelines/router/route.py step3
python3 -I pipelines/router/route.py pool

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
| Step 3 routes a solved stacked task once (state: `out/step3/routed.tsv`) into the general pool `out/step2/screener/`; skips a repo that already has a sibling build; prepares and selects nothing | `step3` |
| Step 2 keeps routed solved stacked tasks in the general pool when it rebuilds it | `step2` |
| The pool file leaves out repos with a sibling task and candidates already in a batch (`pool_excluded.tsv`) | `pool` |
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
| `out/step2/screener/`, `out/step2/pipeline/` | the general sibling pool (screen records) and the lane's files for it (`pool.jsonl`, `pool_excluded.tsv`, selections) |
| `out/step3/routed.tsv`, `out/step3/screener/` | routing record of solved stacked tasks (each is also in the general pool) |
| `out/step3/pipeline/` | the former step-3 lane (selection and BUILD-PROMPTs of 2026-10-25 to 27); history only |
