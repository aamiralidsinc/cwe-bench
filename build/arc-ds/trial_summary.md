# Trial summary for arc-ds

Source: current runs (jobs/). Raw verifier results, not audited. A run solves at reward 1.0.

## Runs

| Model | Run | Reward | Security passed | Functional passed | Failing tests |
|---|---|---|---|---|---|
| deepseek | arc-ds-deepseek-r1-20261020-074636-n001 | 1.0 | 10/10 | 9/9 | 0 |
| deepseek | arc-ds-deepseek-r1-20261020-094441-n001 | 1.0 | 10/10 | 9/9 | 0 |
| deepseek | arc-ds-deepseek-r1-20261020-111428-n001 | 1.0 | 10/10 | 9/9 | 0 |
| deepseek | arc-ds-deepseek-r1-20261020-124405-n001 | 1.0 | 10/10 | 9/9 | 0 |

## Who solved

- deepseek: 4 graded run(s), solved 4 -> SOLVED

## Per trap (runs that failed the trap's tests / runs of that model)

| Trap | Shape | deepseek |
|---|---|---|
| T1_io_function_family | read_text/read_csv/read_csv_auto/read_json/read_blob/glob/parquet_scan/parquet_metadata on | 0/4 (fixed every run) |
| T2_remote_url | read_csv_auto over a caller-supplied http:// URL served by a test-local HTTP server | 0/4 (fixed every run) |
| T3_measurement_route | GET per-measurement route with a where fragment containing a comma-joined read_text/read_c | 0/4 (fixed every run) |
| T4_continuous_query | continuous-query definition whose query reads a local text file, executed explicitly; the  | 0/4 (fixed every run) |
| T5_preview_helper | POST /api/v1/query/preview with SQL reading a local file; the helper opens its own in-memo | 0/4 (fixed every run) |
| T6_export_download | GET /api/v1/export/download?path=../../<outside file>; a plain traversal out of the export | 0/4 (fixed every run) |
| T7_engine_entry_point_siblings | the same caller statement posted to the Arrow handler and to the count-only handler; both  | 0/4 (fixed every run) |

Read: a trap every run of the solving model fixed is not difficulty for that model. Add the kind of trap that model misses, and make sure no single trap carries the task.
