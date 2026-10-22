# FAIRNESS — airflow-info-exposure-inj

Reviewed: `tasks/airflow-info-exposure-inj/instruction.md`, every file under `tests/`,
`solution/fix.patch`, `environment/injection.patch`, `build/airflow-info-exposure-inj/manifest.json`,
`notes.md`, and all 15 `checks/*.patch`. Nothing was run (no Docker, trial or gate).

Abbreviations used below:

- **Props** — the instruction's "Security properties that must hold".
- **Contract-H** — the "Hidden form" contract; **Contract-P** — the "Preservation" contract.
- **ISEK** — standard expert knowledge about this repository/Airflow (the visible code, the visible
  project tests, and the existing API/CLI contracts).

Verdict in short: **READY**. Every test is derivable from the instruction (or ISEK) and the oracle
passes all 20 security, 21 hidden functional and 295 project cases. Quality findings are in sections
2–4; none of them makes a correct fix fail.

---

## 1. Test-by-test fairness

| Test (`file::name`) | What it asserts | Instruction sentence / ISEK that makes it fair | Could a CORRECT fix fail it? | Risk |
|---|---|---|---|---|
| `security/test_api_single_option.py::test_team_section_sensitive_value_not_revealed` | `GET /config/section/team_a=database/option/sql_alchemy_conn` (JSON) returns status < 500 and the password marker does not appear | Props: "No value of a team-scoped override of a sensitive option may be shown … for all of the configuration, one section, one option"; Contract-H: "Hiding must not turn a request into a server error" | **no** — hiding the value for a `[team=section]` spelling is the oracle and returns 200 | low |
| `…::test_team_section_sensitive_value_hidden_text_format` | Same with `Accept: text/plain` and `fernet_key` | Props "wherever Airflow presents configuration"; ISEK: this route serves JSON and text/plain | **no** — the value is hidden before rendering, so both media types see `< hidden >` | low |
| `…::test_team_name_with_dash_not_revealed` | `[data-eng=api] secret_key` is hidden | Props "a team may override any option for itself"; ISEK: team names are arbitrary, `-` is legal | **no** — `rpartition("=")`/`base_section_name` recovers `api` for any team name | low |
| `…::test_team_section_command_entry_not_revealed` | Team `sql_alchemy_conn_cmd` command string is hidden | Props: "it covers the command or secret reference a sensitive value is loaded from as well as the value itself" | **no** — the fix must treat `_cmd`/`_secret` suffixes as sensitive for team scopes | low |
| `…::test_team_env_var_spelling_not_revealed` | `AIRFLOW__TEAM_A___API_AUTH__JWT_SECRET` queried as `/section/team_a/option/_api_auth__jwt_secret` is hidden | Props: "This holds however the team-scoped value is supplied"; ISEK: the env-var spelling and the section/key it is reported under are visible in the parser | **no** — matching the registered option tail (or parsing the name) hides it; `pass-alt-env-parse.patch` proves both approaches pass | low |
| `security/test_api_listing.py::test_team_section_value_not_in_listing` | Full `GET /config` never contains the team DSN password | Props: "for all of the configuration"; Contract-H | **no** — the oracle walks the collected sections | low |
| `…::test_team_section_value_not_in_section_filtered_listing` | Section-filtered listing hides the team `fernet_key` and still contains `parallelism` | Props "one section"; Contract-P: non-sensitive team options stay readable | **no** — masking is per option, not per section | low |
| `…::test_team_section_command_and_secret_entries_not_in_listing` | Team `_cmd` and `_secret` references are absent from the listing | Props: command/secret reference clause | **no** — same `is_sensitive_option` suffix handling as the single-option route | low |
| `…::test_team_env_var_value_not_in_listing` | Team env-var DSN password absent from the listing | Props "however the team-scoped value is supplied" | **no** — the env var is reported under section `<team>`, key `_<section>__<key>`; ISEK/visible parser | low |
| `…::test_team_env_var_with_underscored_team_name_not_in_listing` | `AIRFLOW__ML_PLATFORM___CORE__FERNET_KEY` hidden | Props "however supplied"; ISEK: the format is `AIRFLOW__<TEAM>___<SECTION>__<KEY>`, team names may contain `_` | **no** — a fix is correct only if it handles an underscored team; the naive first-`__` split leaks and is not correct | low |
| `…::test_team_env_var_command_not_in_listing` | Team `AIRFLOW__TEAM_A___API__SECRET_KEY_CMD` hidden | Props command/secret reference clause | **no** — suffix recognition is required by the instruction | low |
| `security/test_api_backend_kwargs.py::test_team_env_backend_kwarg_not_in_listing` | `AIRFLOW__TEAM_A___SECRETS__BACKEND_KWARG__ROLE_ID` hidden | Props: "secrets-backend parameters"; ISEK/visible base code: `_PER_KEY_SENSITIVE_PREFIXES` treats `backend_kwarg__*` under `secrets` as sensitive; "Fix the flaw and its close variants" | **no** — extend `_is_per_key_sensitive_option` to team spellings; oracle does | medium |
| `…::test_team_section_backend_kwarg_not_in_listing` | `[team_a=secrets] backend_kwarg__secret_id` hidden in the listing | Same as above; ISEK: `base_section_name("team_a=secrets") == "secrets"` | **no** — the base helper's prefix then applies | medium |
| `security/test_api_team_view.py::test_team_view_hides_override_of_unset_sensitive_option` | `GET /config?team_name=team_a&section=sentry` hides a team `sentry_dsn` whose deployment-wide value is unset | Props: "the configuration as one team sees it"; ISEK: `sentry_dsn` is a registered sensitive option (the oracle's registry-based guard passes 20/20) | **no** — check registration of the base option, not whether the base value is already hidden | low |
| `…::test_team_view_hides_override_of_backend_kwargs` | Team `backend_kwargs` JSON hidden in the team view | Props team view + "secrets-backend parameters" | **no** — `backend_kwargs` is registered sensitive; the oracle's guard handles it | low |
| `security/test_log_redaction.py::test_team_section_value_redacted` | A process that imports `airflow` and calls `redact()` masks the team DSN | Props: "A team-scoped sensitive value must be redacted from Airflow's logs exactly like the deployment-wide value" | **no** — register team values with the start-up masker; oracle does | low |
| `…::test_team_env_var_value_redacted` | Same for a team env-var value | Props log clause + "however supplied" | **no** — the oracle scans both file sections and env names at start-up | low |
| `security/test_cli.py::test_config_list_hides_team_section_value` | `airflow config list --show-values --hide-sensitive` keeps `[team_a=database]` and drops the secret | Props CLI clause; Contract-H: "the option stays listed … reported the way it is today"; ISEK: `config list` prints section headers | **no** — masking the value leaves the section header; dropping the whole section would contradict "the way it is today" (wording ambiguity noted in §5) | low |
| `…::test_config_list_section_hides_team_section_value` | Same with `--section team_a=core` and `fernet_key` | Props CLI clause; Contract-P section preservation | **no** — per-option masking | low |
| `…::test_get_value_hide_sensitive_hides_team_section_value` | `airflow config get-value team_a=database sql_alchemy_conn --hide-sensitive` does not print the secret | Props CLI clause; Contract-P: "the command line without its option to hide them" implies the flag exists (it is in the injected CLI) | **no** — the flag and its help are visible in the repository | low |
| `functional/test_parser_legit.py::test_display_sensitive_returns_real_team_values` | `conf.as_dict(display_sensitive=True)` returns the team file and env values verbatim | Contract-P: "code that asks the configuration for unmasked values … the real values, team-scoped ones included, are still returned" | **no** — hiding only when `display_sensitive` is false | low |
| `…::test_masked_listing_still_marks_hidden` | Masked `as_dict` keeps team `parallelism == "77"` and base `fernet_key` in (`< hidden >`, `""`) | Contract-H + Contract-P | **no** — the base hidden form is preserved | low |
| `…::test_team_lookup_returns_real_value` | `conf.get(..., team_name="team_a")` returns the real team DSN | Contract-P: "code that asks the configuration for unmasked values … real values" | **no** — do not redact at the lookup layer | low |
| `functional/test_cli_legit.py::test_config_list_shows_team_non_sensitive_values` | `config list --show-values --hide-sensitive` prints `parallelism = 77` | Contract-P: non-sensitive team options "stay readable exactly as today" | **no** — only sensitive options are masked | low |
| `…::test_config_list_show_values_without_hiding_shows_team_value` | `--show-values` without hiding prints the team `fernet_key` | Contract-P: "the command line without its option to hide them" | **no** — this is the explicit unmasked path | low |
| `…::test_get_value_prints_value` | `get-value` without the flag prints the team DSN | Same Contract-P sentence | **no** | low |
| `…::test_get_value_hide_sensitive_keeps_non_sensitive` | `get-value --hide-sensitive` prints `77` for `parallelism` | Contract-P non-sensitive clause | **no** | low |
| `…::test_get_value_hide_sensitive_hides_base_value` | Base `database/sql_alchemy_conn` prints `< hidden >` | "Deployment-wide options keep their current behaviour" | **no** | low |
| `functional/test_log_legit.py::test_base_sensitive_value_still_redacted` | Base `[api] secret_key` value is masked at start-up | "Deployment-wide options keep their current behaviour"; Props log clause | **no** | low |
| `…::test_team_non_sensitive_value_not_redacted` | `[team_a=core] default_timezone` is still readable after `redact()` | "Non-sensitive values must not be redacted from logs" | **no** — only registered sensitive options are registered with the masker | low |
| `functional/test_api_legit.py::test_team_non_sensitive_option_readable` | Single-option API returns `{"team_a=core": {"parallelism": "77"}}` with 200 | Contract-P non-sensitive clause | **no** | low |
| `…::test_team_with_dash_non_sensitive_option_readable` | `[data-eng=core] dag_concurrency_note` readable | Contract-P + arbitrary team names (ISEK) | **no** | low |
| `…::test_base_sensitive_option_still_hidden` | Base `database/sql_alchemy_conn` is `< hidden >` with 200 | "Deployment-wide options keep their current behaviour" | **no** | low |
| `…::test_base_non_sensitive_option_readable` | Base `core/parallelism` equals `conf.get("core","parallelism")` | Same; ISEK | **no** | low |
| `…::test_missing_option_still_404` | A missing option in a team section is 404 | "Deployment-wide options keep their current behaviour"; ISEK: existing 404 contract | **no** — a hidden/sensitive option is 200, a genuinely missing one stays 404 | low |
| `…::test_listing_keeps_team_non_sensitive_values` | Listing contains team `parallelism` and a team env-var `default_timezone` | Contract-P non-sensitive + "however supplied" | **no** — only sensitive names are masked | low |
| `…::test_listing_keeps_base_values` | Listing keeps base hidden DSN and base `parallelism` | "Deployment-wide options keep their current behaviour" | **no** | low |
| `…::test_listing_keeps_team_non_kwarg_secrets_option` | `AIRFLOW__TEAM_A___SECRETS__USE_CACHE` appears as `team_a/_secrets__use_cache = True` | Contract-P: non-sensitive team option stays readable | **no** — the overbroad fix fails this; that is the intended guard (see §2) | low |
| `…::test_team_view_shows_team_overrides` | Team view shows `core.parallelism == "77"` | Contract-P: readable "through … the per-team configuration view" | **no** | low |
| `…::test_team_view_keeps_values_not_overridden` | Team view keeps base `dags_folder` and hides base `fernet_key` | Contract-P + "Deployment-wide options keep their current behaviour" | **no** | low |
| `…::test_team_view_for_team_without_overrides` | A team with no overrides gets base values, 200 | Contract-P; ISEK existing behaviour | **no** | low |
| `functional/project/test_config.py` (39 cases) | The repository's API config tests: JSON/text, 401/403/404, expose_config modes, and `TestPerKeyBackendKwargMasking` | "Deployment-wide options keep their current behaviour"; "Keep every legitimate use working"; these files are visible in `/app` and runnable | **no** — but the fix must stay additive: keep the route's 200/text/JSON contract, the `conf.as_dict` call shape and the base per-key masking behaviour | low |
| `functional/project/test_config_command.py` (197 cases) | The repository's CLI config tests: `show_config` write kwargs (incl. `hide_sensitive`), `get_value` raw output, lint/update | Contract-P; "Keep every legitimate use working"; visible | **no** — but must not change `config list`'s `conf.write` kwargs or make `get-value` redact by default | low |
| `functional/project/test_parser.py` (59 cases) | The shared parser contract incl. `sensitive_config_values`, base `_cmd`/`_secret` resolution, and team lookup (`test_team_skips_cmd_lookup`, `test_team_skips_secret_lookup`, `test_team_env_var_format`) | "Keep every legitimate use working"; ISEK/visible | **no** — but must not resolve team `_cmd`/`_secret`, rename the registry, or re-key the env spelling | low |

**Harness note.** The API tests drive the real FastAPI app in-process; CLI/log tests are real
subprocesses. `team_sections` uses the parser's public `add_section`/`set`, equivalent to a config
file section (the CLI/log tests use real config files). `score.py` gives 1.0 only when every group
passes, forces 0 when a functional test fails, and treats a skip as a fail; this is a faithful
"all-or-nothing" grader and does not create a correct-fix-fails path.

---

## 2. Leniency (QUALITY, non-blocking)

### 2a. Security properties

| Property | Most plausible WRONG fix | Caught? (test / check patch) |
|---|---|---|
| **P1** No team-scoped sensitive value displayed on any API surface (single option, listing, team view) | Strip the `team=` prefix in the single-option route only | **yes** — `sf-landing-only.patch`; `security/test_api_listing.py::test_team_section_value_not_in_listing`, `::test_team_section_value_not_in_section_filtered_listing`, `security/test_api_team_view.py::*`, `security/test_log_redaction.py::*` |
| P1 (refusal variant) | Crash / 500 instead of hiding | **yes for 500** — `sf-crash-single-option.patch`; every `security/test_api_single_option.py` test asserts `status < 500` |
| P1 (refusal variant) | 404, or 200 with the option omitted, for a team-sensitive option or a team view containing one | **NO** — see W1 |
| **P2** Every supply spelling (file section, env var, `_cmd`/`_secret`) | Fix file sections only | **yes** — `sf-no-env-spelling.patch`; `test_api_listing.py::test_team_env_var_value_not_in_listing`, `::test_team_env_var_with_underscored_team_name_not_in_listing`, `::test_team_env_var_command_not_in_listing`, `test_api_single_option.py::test_team_env_var_spelling_not_revealed`, `test_log_redaction.py::test_team_env_var_value_redacted` |
| P2 | Keep the base cmd/secret exemption for team scopes | **yes** — `sf-no-cmd-secret.patch`; `test_api_listing.py::test_team_section_command_and_secret_entries_not_in_listing`, `::test_team_env_var_command_not_in_listing`, `test_api_single_option.py::test_team_section_command_entry_not_revealed` |
| P2 (per-key) | Fix only the literal `secrets`/`workers` section prefixes | **yes** — `sf-no-backend-kwargs.patch`; `test_api_backend_kwargs.py::*` |
| **P3** Team values redacted from logs | Display-only fix | **yes** — `sf-no-log-redaction.patch`; `security/test_log_redaction.py::*` |
| **P4** Preservation: non-sensitive readable, unmasked callers get real values, no server error | Hide every team-scoped option | **yes** — `ff-overbroad-team-mask.patch`; `functional/test_api_legit.py::test_team_non_sensitive_option_readable`, `::test_listing_keeps_team_non_sensitive_values`, `::test_listing_keeps_team_non_kwarg_secrets_option`, `functional/test_cli_legit.py::test_config_list_shows_team_non_sensitive_values`, `::test_get_value_hide_sensitive_keeps_non_sensitive`, `functional/test_parser_legit.py::test_masked_listing_still_marks_hidden` |
| P4 | Mask even when `display_sensitive=True` | **yes** — `ff-display-sensitive-masked.patch`; `functional/test_parser_legit.py::test_display_sensitive_returns_real_team_values` |
| P4 | Disable exposure / 403 everything / redact `conf.get` | **yes** — the functional API suite asserts 200s (`test_api_legit.py::*`) and `test_parser_legit.py::test_team_lookup_returns_real_value` |

### 2b. Manifest traps

| Trap | Most plausible WRONG fix | Caught? (test / check patch) |
|---|---|---|
| **T1** landing single option | Literal registry lookup in the route; or special-case `team_a=database` | **yes** — `sf-landing-only.patch` is caught by the listing tests; a name/key special-case is caught by `test_team_name_with_dash_not_revealed`, `…hidden_text_format` (`fernet_key`), `…team_section_command_entry_not_revealed` |
| T1 | Refuse with 500 | **yes** — `sf-crash-single-option.patch`; `_assert_not_revealed` in every single-option test |
| **T2** listing file sections | Mask only in the route | **yes** — `sf-landing-only.patch`; `test_api_listing.py::test_team_section_value_not_in_listing`, `::test_team_section_value_not_in_section_filtered_listing` |
| **T3** env-var spelling | Skip env vars, or split the team name at the first `__` | **yes** — `sf-no-env-spelling.patch`; the four env tests; the underscored-team test defeats the naive split |
| **T4** CLI listing | API-only fix | **yes** — `sf-no-cli-list.patch`; `test_cli.py::test_config_list_hides_team_section_value`, `::test_config_list_section_hides_team_section_value` |
| **T5** `_cmd`/`_secret` shapes | Keep the base "don't hide cmd/secret" exemption | **yes** — `sf-no-cmd-secret.patch`; the three API cmd/secret tests; gap W5 for the CLI |
| **T6** log redaction | Display-only fix | **yes** — `sf-no-log-redaction.patch`; both `test_log_redaction.py` tests; gaps W7/W8 |
| **T7** per-key backend kwargs | Literal section prefixes | **yes** — `sf-no-backend-kwargs.patch`; both `test_api_backend_kwargs.py` tests; gaps W2/W3/W4/W8 |
| **T8** injected team view | Keep the "skip only if the base value is already hidden" guard | **yes** — `sf-no-team-view.patch`; both `test_api_team_view.py` tests; gaps W2 and W10 |
| **T9** injected get-value hide | Literal registry lookup | **yes** — `sf-no-get-value.patch`; `test_cli.py::test_get_value_hide_sensitive_hides_team_section_value`; gap W6 |

**Wrong-fix catalogue mapping.** `refuse_all`→`ff-overbroad-team-mask` (functional, caught);
`crash_as_refusal`→`sf-crash-single-option` (caught for 500 only; W1 covers 404/omit);
`wrong_resource`→`sf-no-team-view` (caught); `one_role_or_direction`→`sf-no-cli-list` (caught);
`unlisted_route`→`sf-published-only` (caught by the B-route tests);
`malformed_identity`→`sf-no-env-spelling` (caught); `adjacent_api`→`ff-display-sensitive-masked`
(caught). `reads_only`, `check_after_adjustment` and `missing_authority` are correctly `n/a`.

### 2c. Wrong fixes no test catches

1. **Refusal / omission instead of hiding.** On the single-option route, return 404 (or 200 with
   the option omitted) for a team-sensitive option. Every single-option security test asserts only
   `status < 500` and marker absence; no functional test pins 200 + `< hidden >` / listed for a
   *team* option. `sf-crash-single-option.patch` catches only the 500 variant. The same is true of
   a team view that 404s whenever a sensitive override exists.
2. **Per-key synthetic team options via the single-option route / team view.** Fix only
   `_mask_per_key_sensitive_options` (the listing path) and leave `_is_per_key_sensitive_option`
   literal. `GET /config/section/team_a=secrets/option/backend_kwarg__secret_id` then leaks.
   `test_api_backend_kwargs.py` only hits the listing; `test_api_team_view.py` uses the registered
   `backend_kwargs`, not a per-key option.
3. **Team view guarded by `conf.is_sensitive_option` only** (not the per-key helper): leaks
   `[team_a=secrets] backend_kwarg__*` and `[team_a=workers] secrets_backend_kwarg__*` through
   `GET /config?team_name=`. No test covers a per-key override in the team view.
4. **Only half of `_PER_KEY_SENSITIVE_PREFIXES`.** No team test uses
   `workers`/`secrets_backend_kwarg__` (neither section nor env var), so a fix hard-coding the
   `secrets`/`backend_kwarg__` prefix passes.
5. **Team `_cmd`/`_secret` through the CLI.** Every cmd/secret security test goes through the API.
   `config list --hide-sensitive` and `get-value --hide-sensitive` with a team
   `sql_alchemy_conn_cmd` are untested; `sf-no-cmd-secret.patch` fails only the API tests.
6. **Env-var spelling through `get-value` and a section-filtered listing.** Only the full listing
   and the single-option spelling are tested. `get-value team_a _api_auth__jwt_secret
   --hide-sensitive` and `GET /config?section=team_a` are not.
7. **Log redaction of team per-key backend kwarg env vars.** `pass-hardening.patch` adds masking of
   `AIRFLOW__<TEAM>___SECRETS__BACKEND_KWARG__*`; the oracle does not, and no test covers it. Since
   deployment-wide per-key kwarg env vars *are* masked (`configuration.py`), the instruction's
   "secrets-backend parameters" + "redacted … exactly like the deployment-wide value" makes this a
   real gap — both the oracle and the hardening pass.
8. **Log redaction of team `_cmd`/`_secret` reference strings.** Both log tests pass resolved values
   through `redact()`; the reference string itself is never tested.
9. **Partial redaction of the value.** Replacing only the password with `***` (leaving
   `postgresql://team_a:***@db/airflow`) passes every security test, because the markers are unique
   substrings and the tests assert only that the marker is absent. No test pins `< hidden >` or
   omission for a team-scoped option; the exact-form assertions are base-only
   (`test_api_legit.py::test_base_sensitive_option_still_hidden`,
   `test_parser_legit.py::test_masked_listing_still_marks_hidden`).
10. **`text/plain` listing and team view.** Only the single-option route is exercised with
    `text/plain`; the full/section-filtered listing and the team view are JSON-only. A fix that
    masks only in the JSON path would pass.
11. **Team view without `section`.** `GET /config?team_name=team_a` (full configuration) is never
    requested; a fix that applies overrides only when `section` is given passes the two team-view
    tests.
12. **Team name containing `=`.** The parser's `team_section_name`/`base_section_name` use the last
    `=`, but no test uses such a name; a fix splitting at the first `=` passes. Likewise, an env
    var for a team name containing `-` is untested (only the file-section dash case is).

---

## 3. Hints (QUALITY, non-blocking)

Quotes from `instruction.md`; proposed neutral wording:

1. *"Some options are registered as **sensitive**: database connection strings, the Fernet key, API
   and JWT secrets, secrets-backend parameters, and so on."* — names the sensitivity registry and
   enumerates the exact shapes used by the tests. → *"Some options carry sensitive material —
   credentials, keys, tokens and secrets-backend settings."*
2. *"Its configuration comes from a configuration file, environment variables and command/secret
   fallbacks."* — supply-mechanism variant list (T3/T5). → *"Its configuration is assembled from
   several sources."*
3. *"A team-scoped override holds the same kind of material as the deployment-wide option it
   overrides; for a sensitive option it is that team's own secret."* — paraphrases the fix approach
   (map the team spelling back to the base option). → *"A team may override any option for itself;
   a team's override of a sensitive option is that team's own secret."*
4. *"over the REST API or on the command line, for all of the configuration, one section, one
   option, or the configuration as one team sees it."* — enumerates the four access paths
   (T1/T2/T4/T8) as a checklist. → *"over the REST API or on the command line, at every scope at
   which configuration is exposed."* (Keep "the per-team configuration view" in Contract-P, where
   it is a preservation requirement.)
5. *"This holds however the team-scoped value is supplied, and it covers the command or secret
   reference a sensitive value is loaded from as well as the value itself."* — names the `_cmd` /
   `_secret` mechanism (T5). → *"This holds however the value is supplied, including when what is
   configured is a reference to the secret rather than the secret itself."*
6. *"When sensitive values are explicitly requested — the command line without its option to hide
   them, and code that asks the configuration for unmasked values (such as the Kubernetes provider
   or `airflow config lint`) — the real values, team-scoped ones included, are still returned."* —
   names the hide flag, the `display_sensitive` concept and two concrete callers. → *"When a caller
   explicitly requests unmasked values, the real values, team-scoped ones included, are still
   returned."*
7. *"Hiding must not turn a request into a server error."* — warns off the crash-as-refusal trap
   (`sf-crash-single-option.patch`). → *"A hidden value is returned as a normal successful
   response."*
8. *"The example above is one instance, not the full set of ways the properties can be violated."*
   and *"Fix the flaw and its close variants, not just the request shown."* — state the flaw count
   and the breadth of variants. → remove both; the existing *"Do not special-case the example
   input"* already covers the constraint.
9. The observed-impact URL *"`GET /api/v2/config/section/team_a=database/option/sql_alchemy_conn`"*
   — names the exact landing route (T1) and the `[team=section]` spelling. The repro is legitimate,
   but it can be softened: keep the config-file snippet and say *"the per-option configuration
   endpoint returns the full connection string"*.
10. *"Non-sensitive team-scoped options (for example `[team_a=core] parallelism = 64`) stay readable
    exactly as today, through the API, the per-team configuration view and the command line."* —
    enumerates the preservation surfaces and uses a test-shaped example. → *"Non-sensitive
    team-scoped options stay readable exactly as today, through every interface that shows
    configuration."*

No file name, function/identifier name, or test path appears in `instruction.md`.

---

## 4. Realism (QUALITY, non-blocking)

| Trap | Real code a maintainer could write? | Reachable through the real entry point? | Notes |
|---|---|---|---|
| T1 landing | **yes** — the reported site; the published upstream fix is this route | `GET /config/section/{section}/option/{option}` (in-process real app) | Realistic |
| T2 listing | **yes** — real shared-parser masking loop over `sensitive_config_values` | `GET /config` → `conf.as_dict` | Realistic; the reason to dismiss (lower-level library) is a solver-difficulty feature, not contrivance |
| T3 env spelling | **yes** — the existing `_include_envs` parsing produces section `<team>`, key `_<section>__<key>` | `GET /config`; `conf.as_dict` | Realistic; the odd section name is the real parser behaviour |
| T4 CLI listing | **yes** — real `conf.write` `is_sensitive` lookup | `airflow config list --show-values --hide-sensitive` | Realistic |
| T5 cmd/secret | **yes** — the real "Don't hide cmd/secret values here" exemption plus the team skip of cmd/secret resolution | API listing/single option | Realistic |
| T6 log redaction | **yes** — unmodified upstream `configuration.py:mask_secrets` (per notes, still in main) | `import airflow` → `settings.initialize` → `conf.mask_secrets` | Realistic |
| T7 per-key kwargs | **yes** — unmodified upstream `_PER_KEY_SENSITIVE_PREFIXES` masking (still in main) | `GET /config` → service masking | Realistic; the weakest test example is the config-file `[team_a=secrets] backend_kwarg__secret_id` spelling (the documented vector is the env var), but the existing base helper treats per-key options in `as_dict` as real |
| T8 team view | **yes, plausible** — a maintainer adding `team_name` to `GET /config` would naturally call the existing `conf.getsection(section, team_name=...)`; the guard "skip only if the base value is already hidden" looks complete because it defers to the masked base listing | `GET /config?team_name=...` (OpenAPI YAML updated by the injection) | Mildly synthetic: the team-view feature exists only in this task. The code itself reads like a real next feature, not a planted bug |
| T9 get-value hide | **yes, plausible** — mirrors the existing `config list --hide-sensitive` flag; the literal `(section, option) in conf.sensitive_config_values` lookup is exactly the same mistake as T1–T4 | `airflow config get-value <section> <option> --hide-sensitive` (flag added by the injection) | Mildly synthetic: the flag and the bug were added together. A maintainer could plausibly have done so |

No trap is unreachable; no trap relies on a harness-only route. The API tests use the real FastAPI
app, the CLI/log paths real subprocesses. The only "planted" surfaces are the injected team view
(T8) and the injected get-value flag (T9); both are defensible product changes, and neither looks
like a test-shaped special case. `sf-*`/`ff-*`/`pass-*` patches are check fixtures, not traps.

---

## 5. Verdict

### a. UNFAIRNESS gate — **READY**

No correct-fix-fails mechanism was found:

- No contradiction between `instruction.md` and any test. The one wording that could be read as
  permissive, Contract-H's "(or it is left out)", is an *allowance* (it lets a wrong or
  value-blank fix pass) rather than a test requirement a correct fix would miss; the tests
  assert the hidden value's absence, never that a team option must be exactly `< hidden >`.
- Every assertion is derivable from the instruction or ISEK: the registry of sensitive options
  (including `sentry_dsn` and the per-key `backend_kwarg__*`/`secrets_backend_kwarg__*` prefixes),
  the `[team=section]` and `AIRFLOW__<TEAM>___<SECTION>__<KEY>` spellings, the `_cmd`/`_secret`
  shapes, the JSON/text API, and the CLI's `--hide-sensitive` flags are all visible in the
  repository and/or standard Airflow knowledge.
- The harness is faithful: real FastAPI app, real CLI/log subprocesses, and the repository's own
  pristine project tests. The oracle passes 20/20 security and 316/316 functional; all 14 declared
  check outcomes are as declared.
- No impossible or ambiguous spec requirement: the oracle's `pass-hardening.patch` and
  `pass-alt-env-parse.patch` demonstrate that at least two distinct correct implementations pass.

### b. Quality findings — recorded, **not** a reason for NOT READY

See §2 (leniency, including the 12 uncaught wrong fixes), §3 (hints) and §4 (realism). They should
be tightened for delivery quality, but every one of them is either a wrong fix that also passes or
a wording/realism issue — none makes a correct fix fail.

### Quality to tighten

- Add security tests for: per-key synthetic team options through the single-option route and team
  view; team `workers`/`secrets_backend_kwarg__`; team `_cmd`/`_secret` via both CLI commands; env
  spelling via `get-value` and a section-filtered listing; the full team view (no `section`);
  `text/plain` for listing/team view.
- Add a functional test pinning the hidden form for a *team* option (200 and listed as
  `< hidden >`/blank, not 404 or omitted), closing the refusal gap; clarify Contract-H's "or it is
  left out".
- Assert whole-value hiding (not merely marker absence) so partial redaction fails.
- Cover log redaction of team per-key backend kwarg env vars (the `pass-hardening.patch` behaviour)
  and of team `_cmd`/`_secret` reference strings.
- Neutralize hints: the sensitive-option list; the supply-mechanism list; "same kind of material
  as the deployment-wide option" (fix approach); the enumerated access scopes; "command or secret
  reference"; "the command line without its option to hide them" plus the Kubernetes/lint names;
  "Hiding must not turn a request into a server error"; "one instance, not the full set" and
  "close variants"; the exact URL in the observed impact.
- Realism: T8/T9 are acceptable; the weakest example is the config-file per-key kwarg spelling —
  add its env-var variant (already in the first bullet).

---

# Hardening v2 (2026-10-21) — post-trial difficulty review

The task was solved (deepseek 1/3, and it fixed seven of the nine traps every run), so two further
levers were added. Both are real code paths of the same project; neither adds an instruction
sentence, a count, or a location hint.

## T10 — worker-side log registration (task SDK's own mask_secrets)

* Rule: *"A team-scoped sensitive value must be redacted from Airflow's logs exactly like the
  deployment-wide value of the same option."*
* Code: `task-sdk/src/airflow/sdk/configuration.py` ships a second copy of the masking loop. The
  task's injected `configure_logging` wires the otherwise uncalled `mask_secrets()` into a worker
  process's logging (real maintainer work: the method existed but had no caller). A re-executed
  worker (`_AIRFLOW__REEXECUTED_PROCESS=1`, the project's own worker marker) skips core start-up
  secret registration, so the worker's logging configuration is the only registration point there.
  At the vulnerable commit the deployment-wide value is redacted and a team-scoped value is not.
* Any correct layer passes: the SDK parser loop, the worker logging setup, a shared helper, or a
  generalisation of the sensitivity check. The coupled functional tests pin the base value (still
  redacted) and a non-sensitive team value (not redacted), so over-masking fails.
* Why it is fair: worker/task logs are Airflow's logs; the base value behaves correctly in the same
  process, so the instruction's "exactly like the deployment-wide value" is a literal, observable
  comparison. The duplicate is visible in the repository (a separate distribution with the same
  `mask_secrets` body), and an independent blind fix (written from instruction.md + repo only)
  found and fixed it.

## T11 — team-scoped per-key secrets-backend kwargs in logs

* Rule: *"This holds however the team-scoped value is supplied"* + the log rule. The deployment-wide
  `AIRFLOW__SECRETS__BACKEND_KWARG__*` value is redacted by the same masker today, so the
  team-scoped spelling must be too.
* Code: core's `mask_secrets` masks per-key backend kwargs although they are not in
  `sensitive_config_values`; its scan uses the base prefix `AIRFLOW__SECRETS__BACKEND_KWARG__`, so
  `AIRFLOW__<TEAM>___SECRETS__BACKEND_KWARG__<KEY>` (three underscores) is never matched.
* Any correct layer passes (register the matching env vars, generalise `is_sensitive_option` to the
  synthetic prefixes, or mask them where the other per-key kwargs are masked). Coupled functional
  tests keep a non-sensitive team `[secrets]` value visible and keep the base kwarg redacted.

## Independence and no single trap

* `sf-no-sdk-log-redaction.patch` fails T10's two security tests while passing T11's;
  `sf-no-team-kwarg-log.patch` fails T11's test while passing T10's. A run that closes one still
  fails on the other.
* The remaining old traps are unchanged, and the prior per-model misses (env-var spelling,
  per-key kwargs, worker mechanisms) are still present, so no single trap carries the task.
* The oracle (all 11 traps), `pass-hardening` and `pass-alt-env-parse` pass 23/23 security and
  320/320 functional; the blind fix passes with a different implementation shape.

## Checked and not violated

* No new instruction sentence names the levers, a file, a function, a route or a count; the new
  internal identifiers were added to `manifest.leak_terms` and do not occur in instruction.md.
* The new tests accept any refusal the instruction allows (they assert the value is absent, never a
  particular status or hidden spelling) and leave `display_sensitive=True` callers untouched.
