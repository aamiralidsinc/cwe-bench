# Trial summary for airflow-info-exposure-inj

Source: current runs (jobs/). Raw verifier results, not audited. A run solves at reward 1.0.

## Runs

| Model | Run | Reward | Security passed | Functional passed | Failing tests |
|---|---|---|---|---|---|
| deepseek | airflow-info-exposure-inj-deepseek-r1-20261018-175709-n001 | 0.95 | 19/20 | 316/316 | 1 |
| deepseek | airflow-info-exposure-inj-deepseek-r2-20261018-181159-n002 | 0.0 | 19/20 | 315/316 | 2 |
| deepseek | airflow-info-exposure-inj-deepseek-r3-20261018-183158-n003 | 1.0 | 20/20 | 316/316 | 0 |
| mimo | airflow-info-exposure-inj-mimo-r1-20261018-175709-n001 | 0.0 | 19/20 | 315/316 | 2 |
| mimo | airflow-info-exposure-inj-mimo-r2-20261018-184946-n002 | 0.0 | 17/20 | 315/316 | 4 |
| mimo | airflow-info-exposure-inj-mimo-r3-20261018-193857-n003 | 0.0 | 16/20 | 315/316 | 5 |

## Who solved

- deepseek: 3 graded run(s), solved 1 -> SOLVED
- mimo: 3 graded run(s), solved 0 -> not solved

## Per trap (runs that failed the trap's tests / runs of that model)

| Trap | Shape | deepseek | mimo |
|---|---|---|---|
| T1_landing_single_option | [team=section] file section, sensitive key; JSON and text accept; team name with '-' | 0/3 (fixed every run) | 0/3 (fixed every run) |
| T2_listing_file_sections | [team=section] in the full and section-filtered listing | 0/3 (fixed every run) | 0/3 (fixed every run) |
| T3_env_var_spelling | team env var reported under section '<team>' key '_<section>__<key>', incl. underscored te | 1/3 | 3/3 |
| T4_cli_listing | airflow config list --show-values --hide-sensitive, full and --section | 0/3 (fixed every run) | 0/3 (fixed every run) |
| T5_cmd_secret_shapes | team _cmd/_secret fallbacks in file sections and as env vars (never resolved for teams) | 0/3 (fixed every run) | 2/3 |
| T6_log_redaction | team file-section and team env-var values registered with the secrets masker at start-up | 0/3 (fixed every run) | 1/3 |
| T7_per_key_backend_kwargs | team env var and [team=secrets] per-key backend kwarg in GET /config | 2/3 | 3/3 |
| T8_injected_team_view | GET /config?team_name=<team>: team overrides copied over the masked listing, skipped only  | 0/3 (fixed every run) | 0/3 (fixed every run) |
| T9_injected_get_value_hide | airflow config get-value <team=section> <key> --hide-sensitive using the literal registry  | 0/3 (fixed every run) | 0/3 (fixed every run) |

Read: a trap every run of the solving model fixed is not difficulty for that model. Add the kind of trap that model misses, and make sure no single trap carries the task.
