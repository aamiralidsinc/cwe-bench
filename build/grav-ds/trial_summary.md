# Trial summary for grav-ds

Source: current runs (jobs/). Raw verifier results, not audited. A run solves at reward 1.0.

## Runs

| Model | Run | Reward | Security passed | Functional passed | Failing tests |
|---|---|---|---|---|---|
| deepseek | grav-ds-deepseek-r1-20261020-074702-n001 | None | - | - | 0 |
| deepseek | grav-ds-deepseek-r1-20261020-074739-n002 | 1.0 | 28/28 | 22/22 | 0 |
| deepseek | grav-ds-deepseek-r1-20261020-091502-n001 | 1.0 | 28/28 | 22/22 | 0 |

## Who solved

- deepseek: 3 graded run(s), solved 2 -> SOLVED

## Per trap (runs that failed the trap's tests / runs of that model)

| Trap | Shape | deepseek |
|---|---|---|
| base | published fix's protected sink: the container accessor returns the raw config, then any du | 0/3 (fixed every run) |
| string_function | the conversion helper's array path calls the raw encoder; the published fix guarded only t | 0/3 (fixed every run) |
| array_cast_yaml | the type-cast helper (filter and function form) flattens an object that carries config int | 0/3 (fixed every run) |
| sibling_to_json | pretty-print JSON filter and function beside the decode helper; calls the raw encoder dire | 0/3 (fixed every run) |
| sibling_inspect | always-on readable dump beside the debug dumpers; flattens objects through toArray()/array | 0/3 (fixed every run) |
| sibling_accessor | dotted-path setting lookup with a site-config fallback read straight from the container, p | 0/3 (fixed every run) |

Read: a trap every run of the solving model fixed is not difficulty for that model. Add the kind of trap that model misses, and make sure no single trap carries the task.
