# Trial summary for portainer-ds

Source: current runs (jobs/). Raw verifier results, not audited. A run solves at reward 1.0.

## Runs

| Model | Run | Reward | Security passed | Functional passed | Failing tests |
|---|---|---|---|---|---|
| deepseek | portainer-ds-deepseek-r1-20261021-043102-n001 | 1.0 | 10/10 | 48/48 | 0 |

## Who solved

- deepseek: 1 graded run(s), solved 1 -> SOLVED

## Per trap (runs that failed the trap's tests / runs of that model)

| Trap | Shape | deepseek |
|---|---|---|
| T0_restore_upload | multipart archive upload; header missing | 0/1 (fixed every run) |
| T1_admin_init_far_site | JSON body, missing and wrong header | 0/1 (fixed every run) |
| T2_restore_local_sibling | JSON backup file name; header missing and wrong | 0/1 (fixed every run) |
| T3_legacy_admin_init_sibling | JSON body, missing and wrong header | 0/1 (fixed every run) |
| T4_startup_token_producer | startup configuration: pinned env token vs no pinned token vs existing administrator; rest | 0/1 (fixed every run) |

Read: a trap every run of the solving model fixed is not difficulty for that model. Add the kind of trap that model misses, and make sure no single trap carries the task.
