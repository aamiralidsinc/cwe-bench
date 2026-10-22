# Trial summary for airflow-ds

Source: current runs (jobs/). Raw verifier results, not audited. A run solves at reward 1.0.

## Runs

| Model | Run | Reward | Security passed | Functional passed | Failing tests |
|---|---|---|---|---|---|
| deepseek | airflow-ds-deepseek-r1-20261020-233104-n001 | 0.9091 | 30/33 | 318/318 | 3 |
| deepseek | airflow-ds-deepseek-r1-20261020-233225-n001 | 1.0 | 33/33 | 318/318 | 0 |

## Who solved

- deepseek: 2 graded run(s), solved 1 -> SOLVED

## Per trap (runs that failed the trap's tests / runs of that model)

| Trap | Shape | deepseek |
|---|---|---|
| T1_landing_single_option | [team=section] file section, sensitive key; JSON and text accept; team name with '-' | 0/2 (fixed every run) |
| T2_listing_file_sections | [team=section] in the full and section-filtered listing | 0/2 (fixed every run) |
| T3_env_var_spelling | team env var reported under section '<team>' key '_<section>__<key>', incl. underscored te | 0/2 (fixed every run) |
| T4_cli_listing | airflow config list --show-values --hide-sensitive, full and --section | 0/2 (fixed every run) |
| T5_cmd_secret_shapes | team _cmd/_secret fallbacks in file sections and as env vars (never resolved for teams) | 0/2 (fixed every run) |
| T6_log_redaction | team file-section and team env-var values registered with the secrets masker at start-up | 1/2 |
| T7_per_key_backend_kwargs | team env var and [team=secrets] per-key backend kwarg in GET /config | 0/2 (fixed every run) |
| T8_injected_team_view | GET /config?team_name=<team>: team overrides copied over the masked listing, skipped only  | 0/2 (fixed every run) |
| T9_injected_get_value_hide | airflow config get-value <team=section> <key> --hide-sensitive using the literal registry  | 0/2 (fixed every run) |
| T10_arbitrary_team_name | team name containing the section separator ('='), and a team name with a character outside | 1/2 |

Read: a trap every run of the solving model fixed is not difficulty for that model. Add the kind of trap that model misses, and make sure no single trap carries the task.
