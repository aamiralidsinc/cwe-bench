# Trial summary for jetty.project-ds

Source: current runs (jobs/). Raw verifier results, not audited. A run solves at reward 1.0.

## Runs

| Model | Run | Reward | Security passed | Functional passed | Failing tests |
|---|---|---|---|---|---|
| deepseek | jetty.project-ds-deepseek-r1-20261020-074654-n001 | 0.0 | 7/7 | 9/11 | 2 |
| deepseek | jetty.project-ds-deepseek-r1-20261020-104432-n001 | 1.0 | 7/7 | 11/11 | 0 |
| deepseek | jetty.project-ds-deepseek-r1-20261020-121423-n001 | 1.0 | 7/7 | 11/11 | 0 |
| deepseek | jetty.project-ds-deepseek-r2-20261020-081756-n002 | 1.0 | 7/7 | 11/11 | 0 |

## Who solved

- deepseek: 4 graded run(s), solved 3 -> SOLVED

## Per trap (runs that failed the trap's tests / runs of that model)

| Trap | Shape | deepseek |
|---|---|---|
| reported_digest | the reported sink: the server recomputes the Digest response hash H(A1) over the stored pl | 0/4 (fixed every run) |
| servlet_second_implementation | far site: the servlet-environment module carries its own copy of the same Digest decision  | 1/4 |
| stored_digest_credential_route | a second route into the same password decision: a stored pre-computed digest (MD5:) is che | 0/4 (fixed every run) |
| stronger_digest_algorithm_injected | injected sibling: when the deployment selects the stronger digest algorithm, the server co | 0/4 (fixed every run) |
| stored_strong_digest_injected | injected sibling: a stored SHA-256 digest credential type is checked by hashing the submit | 0/4 (fixed every run) |
| stored_credential_producer | producer the check never calls (M6): the account's stored credential is minted by the serv | 0/4 (fixed every run) |

Read: a trap every run of the solving model fixed is not difficulty for that model. Add the kind of trap that model misses, and make sure no single trap carries the task.
