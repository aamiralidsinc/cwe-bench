# Trial summary for astro-ds

Source: current runs (jobs/). Raw verifier results, not audited. A run solves at reward 1.0.

## Runs

| Model | Run | Reward | Security passed | Functional passed | Failing tests |
|---|---|---|---|---|---|
| deepseek | astro-ds-deepseek-r1-20261021-043046-n001 | 1.0 | 20/20 | 165/165 | 0 |

## Who solved

- deepseek: 1 graded run(s), solved 1 -> SOLVED

## Per trap (runs that failed the trap's tests / runs of that model)

| Trap | Shape | deepseek |
|---|---|---|
| T1-action-dispatch | pattern A landing: action execution reached before/without the origin-check middleware (RP | 0/1 (fixed every run) |
| T2-dispatch-without-middleware | pattern A far site: page/endpoint dispatch reached without the middleware step | 0/1 (fixed every run) |
| T3-lower-level-fetch-api | pattern A far site: the lower-level public astro/fetch primitives under the reported Hono  | 0/1 (fixed every run) |
| T4-input-shapes | input-shape variants of the general rule: non-safe methods, all form content types in any  | 0/1 (fixed every run) |
| T5-coupled-must-keep-working | coupled behaviour: non-form cross-site requests, safe methods and checkOrigin:false must p | 0/1 (fixed every run) |
| S1-endpoint-only-dispatcher | injected sibling: an API-only composable dispatcher renders the matched endpoint itself, w | 0/1 (fixed every run) |
| S2-form-action-dispatcher | injected sibling: a composable form-action step runs the action itself (getActionContext + | 0/1 (fixed every run) |
| S3-fragment-dispatcher | injected sibling: a composable fragment dispatcher renders page routes and carries a hand- | 0/1 (fixed every run) |

Read: a trap every run of the solving model fixed is not difficulty for that model. Add the kind of trap that model misses, and make sure no single trap carries the task.
