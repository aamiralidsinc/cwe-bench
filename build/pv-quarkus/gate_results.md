# pv-quarkus gate results (stages run one at a time)

| stage | outcome | detail |
|---|---|---|
| static | all checks pass except the missing blind pass patch | the blind patch and FAIRNESS.md are written by the pipeline after the builder, as instructed |
| nop | PASSED | 11 security testcases (all failing on the delivered tree), 143 functional testcases (all passing) |
| oracle | PASSED | 3 runs, each 11 security + 143 functional, reward 1.0, identical results |
| patches | PASSED | security_fail_static_exclusion: 2 security fail / 0 functional fail (0.8182); security_fail_undertow: 4 / 0 (0.6364); functional_fail_over_normalization: 0 / 1 (0.0); pass_hardening: reward 1.0; pass_alternative: reward 1.0 |

Trial evidence lives under `~/.tb-graders/cwe/gate-jobs/pv-quarkus-{nop,oracle1..3,chk-*}-*`.
