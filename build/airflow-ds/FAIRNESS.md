# FAIRNESS.md — airflow-ds (pre-trial fairness and leniency review)

Scope reviewed: `tasks/airflow-ds/instruction.md`, every file under `tasks/airflow-ds/tests/`,
`solution/fix.patch`, `build/airflow-ds/manifest.json` (`patch_checks`, `traps`,
`wrong_fix_catalogue`), `build/airflow-ds/notes.md`, every `build/airflow-ds/checks/*.patch`, and
`environment/injection.patch`. Nothing was executed.

Basis shorthand: **ISEK** = "standard expert knowledge: …". Instruction quotations are from
`tasks/airflow-ds/instruction.md`.

**Build-state note (affects coverage only).** The manifest and notes describe a fairness revision
with 33 security tests and 318 functional tests (W1–W4, W8). The tree on disk has **26 security
tests** and **22 hidden functional tests**: the W1 success-status test, the W2 team-view per-key
test, the W3 `workers` cases, the W4 CLI `_cmd`/`_secret` test and the W8 dot-name tests are **not
present**. The instruction also lacks the C1 arbitrary-name sentence the notes say was added and
still contains the C2 "or it is left out" wording. The review below is of the tree as it exists;
the leniency gaps that the missing tests were meant to close are live.

## 1. Test-by-test fairness

### security/ (26 tests — any failure caps reward below 1.0)

| test (file::name) | what it asserts | instruction sentence that makes it fair | could a correct fix fail it? | risk |
|---|---|---|---|---|
| `test_api_single_option.py::test_team_section_sensitive_value_not_revealed` | `GET /config/section/team_a=database/option/sql_alchemy_conn`: status < 500, marker absent (JSON) | "No value of a team-scoped override of a sensitive option may be shown … for the whole configuration, one section, or one option." | no | low |
| `test_api_single_option.py::test_team_section_sensitive_value_hidden_text_format` | same with `Accept: text/plain` | same sentence; ISEK: content negotiation must not bypass masking | no | low |
| `test_api_single_option.py::test_team_name_with_dash_not_revealed` | `data-eng=api` secret hidden | "and whatever the team is called" | no | low |
| `test_api_single_option.py::test_team_name_containing_separator_not_revealed` | `a=b=database` secret hidden | "and whatever the team is called" (sole, thin cover) | **maybe** — a fix that splits the team-scoped name on the **first** separator resolves base section `b=database`, finds no registered option and leaks (`checks/sf-first-separator.patch`). Only a right-to-left / base-section-resolution passes | medium |
| `test_api_single_option.py::test_team_section_command_entry_not_revealed` | team `sql_alchemy_conn_cmd` reference string hidden | "This covers the command or secret reference a sensitive value is loaded from as well as the value itself." | no (a value-only fix is non-compliant with that sentence) | low |
| `test_api_single_option.py::test_team_env_var_spelling_not_revealed` | env-var-reported spelling (`section=team_a`, key `_api_auth__jwt_secret`) hidden | "This holds however the team-scoped value is supplied." | no (a producer-side re-keying fix returns 404 here and still passes; that is leniency, not unfairness) | low |
| `test_api_listing.py::test_team_section_value_not_in_listing` | marker absent from full `GET /config` | property 1, "for the whole configuration" | no | low |
| `test_api_listing.py::test_team_section_value_not_in_section_filtered_listing` | marker absent with `section=` filter | property 1, "one section" | no | low |
| `test_api_listing.py::test_team_section_command_and_secret_entries_not_in_listing` | `_cmd` and `_secret` reference strings absent | "This covers the command or secret reference …" | no | low |
| `test_api_listing.py::test_team_name_containing_separator_not_in_listing` | `a=b=database` hidden in full listing | "and whatever the team is called" (thin) | **maybe** — first-separator split leaks | medium |
| `test_api_listing.py::test_team_name_containing_separator_section_filtered_not_in_listing` | same, `section=a=b=core` filter | same | **maybe** — first-separator split leaks | medium |
| `test_api_listing.py::test_team_env_var_value_not_in_listing` | team env-var value hidden in listing | "This holds however the team-scoped value is supplied." | no | low |
| `test_api_listing.py::test_team_env_var_with_underscored_team_name_not_in_listing` | `AIRFLOW__ML_PLATFORM___CORE__FERNET_KEY` hidden | "and whatever the team is called" | no (a tail match, a `___` split, or resolving against registered names all work) | low |
| `test_api_listing.py::test_team_env_var_command_not_in_listing` | team env `_CMD` reference hidden | property 2 + "however … supplied" | no | low |
| `test_api_backend_kwargs.py::test_team_env_backend_kwarg_not_in_listing` | team env per-key `backend_kwarg__role_id` hidden | "secrets-backend parameters" in the sensitive list + property 1 | no — exotic split spelling, but a spelling-resolving fix passes | medium |
| `test_api_backend_kwargs.py::test_team_section_backend_kwarg_not_in_listing` | `[team_a=secrets] backend_kwarg__secret_id` hidden | same | no | low |
| `test_api_backend_kwargs.py::test_team_name_containing_separator_backend_kwarg_not_in_listing` | `[a=b=secrets] backend_kwarg__secret_id` hidden | "and whatever the team is called" (thin) | **maybe** — first-separator split leaks | medium |
| `test_api_team_view.py::test_team_view_hides_override_of_unset_sensitive_option` | `GET /config?team_name=team_a&section=sentry` hides a team `sentry_dsn` when the base value is unset | "in the configuration view for one team" | no | low |
| `test_api_team_view.py::test_team_view_hides_override_of_backend_kwargs` | team-view override of `backend_kwargs` hidden | same + "secrets-backend parameters" | no | low |
| `test_cli.py::test_config_list_hides_team_section_value` | `config list --show-values --hide-sensitive`: marker absent **and** the header `[team_a=database]` present | property 1 ("on the command line"); the header assertion is **not** covered by "Hidden form", which expressly allows the option "or it is left out" | **maybe** — a compliant implementer who omits the hidden option and prunes the now-empty section drops the header and fails | medium |
| `test_cli.py::test_config_list_section_hides_team_section_value` | same with `--section team_a=core`; header `[team_a=core]` present | same | **maybe** — same header/pruning conflict | medium |
| `test_cli.py::test_config_list_hides_team_name_containing_separator` | `[a=b=database]` listed, secret hidden | same + "whatever the team is called" | **maybe** — first-separator split and/or empty-section pruning | medium |
| `test_cli.py::test_get_value_hide_sensitive_hides_team_section_value` | `get-value team_a=database sql_alchemy_conn --hide-sensitive`: marker absent | property 1 ("on the command line"); ISEK: a hide option must hide every spelling | no | low |
| `test_log_redaction.py::test_team_section_value_redacted` | process-start redaction covers the team file value | "A team-scoped sensitive value must be redacted from Airflow's logs exactly like the deployment-wide value of the same option." | no | low |
| `test_log_redaction.py::test_team_name_containing_separator_value_redacted` | same with `[a=b=database]` | "whatever the team is called" (thin) | **maybe** — first-separator split fails to register the value | medium |
| `test_log_redaction.py::test_team_env_var_value_redacted` | process-start redaction covers a team env value | property 3 + "however … supplied" | no | low |

### functional/ hidden tests (22 — any failure forces reward 0)

| test (file::name) | what it asserts | instruction sentence that makes it fair | could a correct fix fail it? | risk |
|---|---|---|---|---|
| `test_api_legit.py::test_team_non_sensitive_option_readable` | team `parallelism` = `77`, 200 | "Non-sensitive team-scoped options … stay readable exactly as today" | no | low |
| `test_api_legit.py::test_team_with_dash_non_sensitive_option_readable` | dash team name readable | Preservation + "whatever the team is called" | no | low |
| `test_api_legit.py::test_team_name_containing_separator_non_sensitive_option_readable` | `a=b=core` readable through route and listing | Preservation + "whatever the team is called" | no — a pure hide fix leaves reads untouched; only a fix that rewrites/canonicalises section names fails | low |
| `test_api_legit.py::test_base_sensitive_option_still_hidden` | base `database/sql_alchemy_conn` = `< hidden >`, 200 | "Deployment-wide options keep their current behaviour"; "Hidden form … the way it is today" | no (omitting it would violate the preservation clause) | low |
| `test_api_legit.py::test_base_non_sensitive_option_readable` | base `core/parallelism` unchanged | "Deployment-wide options keep their current behaviour" | no | low |
| `test_api_legit.py::test_missing_option_still_404` | unknown option still 404 | "Keep every legitimate use working"; ISEK: masking must not swallow the not-found contract | no | low |
| `test_api_legit.py::test_listing_keeps_team_non_sensitive_values` | file and env non-sensitive team values visible | Preservation clause | no | low |
| `test_api_legit.py::test_listing_keeps_base_values` | base hidden/readable unchanged | "Deployment-wide options keep their current behaviour" | no | low |
| `test_api_legit.py::test_listing_keeps_team_non_kwarg_secrets_option` | env spelling `team_a` / `_secrets__use_cache` still reported with value `True` | "stay readable exactly as today" (pins the current display spelling) | **maybe** — a fix that re-keys env spellings into `[team_a=secrets]` fails; "exactly as today" covers it, and the project test `test_team_env_var_format` pins the same spelling | medium |
| `test_api_legit.py::test_team_view_shows_team_overrides` | team view shows `77` | Preservation; "the configuration view for one team" | no | low |
| `test_api_legit.py::test_team_view_keeps_values_not_overridden` | non-overridden values unchanged; base `fernet_key` is `< hidden >` | Preservation; "Hidden form … the way it is today" | no (omitting the base value would change deployment-wide behaviour) | low |
| `test_api_legit.py::test_team_view_for_team_without_overrides` | no-override team = base view | "Keep every legitimate use working" | no | low |
| `test_cli_legit.py::test_config_list_shows_team_non_sensitive_values` | `parallelism = 77` still printed | Preservation ("on the command line") | no | low |
| `test_cli_legit.py::test_config_list_show_values_without_hiding_shows_team_value` | without `--hide-sensitive` the full secret is printed | "the command line without its option to hide them … the real values, team-scoped ones included, are still returned" | no (over-masking fixes fail correctly) | low |
| `test_cli_legit.py::test_get_value_prints_value` | `get-value` without flag prints the exact value | same clause | no | low |
| `test_cli_legit.py::test_get_value_hide_sensitive_keeps_non_sensitive` | non-sensitive value readable with the flag | Preservation | no | low |
| `test_cli_legit.py::test_get_value_hide_sensitive_hides_base_value` | base value printed as `< hidden >` | "Hidden form … the way it is today" | no | low |
| `test_log_legit.py::test_base_sensitive_value_still_redacted` | base secret still redacted | "exactly like the deployment-wide value" | no | low |
| `test_log_legit.py::test_team_non_sensitive_value_not_redacted` | team non-sensitive value NOT redacted | "Non-sensitive values must not be redacted from logs." | no (over-registration fixes fail correctly) | low |
| `test_parser_legit.py::test_display_sensitive_returns_real_team_values` | `conf.as_dict(display_sensitive=True)` returns file and env team values | "code that asks the configuration for unmasked values … the real values, team-scoped ones included, are still returned" | no | low |
| `test_parser_legit.py::test_masked_listing_still_marks_hidden` | masked listing keeps non-sensitive values and marks the base hidden (`< hidden >` or `""` tolerated) | "Hidden form"; preservation | no | low |
| `test_parser_legit.py::test_team_lookup_returns_real_value` | `conf.get(..., team_name=)` returns the team value | same unmasked-caller clause | no | low |

### functional/project/ (pristine upstream copies re-installed by `test.sh`; 295 parametrized cases)

The three upstream files are legacy/regression covers, not bespoke tests; one row per file is used
rather than 295 rows.

| test file | what it asserts | fairness basis | could a correct fix fail it? | risk |
|---|---|---|---|---|
| `functional/project/test_config.py` (39 cases) | upstream API config behaviour: expose_config modes, 401/403/404, base masking, and `TestPerKeyBackendKwargMasking` (base `secrets`/`workers` synthetic kwargs) | ISEK + "Deployment-wide options keep their current behaviour" | no — an additive resolution keeps these green; the mocks patch `conf.as_dict`/`conf.has_option`, not the new resolver | low |
| `functional/project/test_config_command.py` (197 cases) | upstream CLI config list/get-value/lint behaviour, incl. `--hide-sensitive` on base values | ISEK + Preservation | no | low |
| `functional/project/test_parser.py` (59 cases) | upstream shared-parser behaviour, incl. `sensitive_config_values`, base `_cmd`/`_secret` resolution, and team lookup (`test_team_env_var_format`, `test_team_skips_cmd_lookup`, `test_team_skips_secret_lookup`) | ISEK + "Keep every legitimate use working" | no — but these forbid making team `_cmd`/`_secret` resolve, renaming the registry or re-keying env spellings; fixes must be additive. The solver can run these same files from the repo | low |

## 2. Leniency (quality, non-blocking)

### Per security property

**P1 — no team-scoped override of a sensitive option is shown in any hidden display, for any
supply route or team name.**
Most plausible wrong fix: strip/compare the team prefix only in the reported single-option route
(`checks/sf-landing-only.patch`). Caught by `security/test_api_listing.py` (both listing tests),
`security/test_cli.py` (list tests), `security/test_log_redaction.py`,
`security/test_api_backend_kwargs.py` and `security/test_api_team_view.py`. The broader "apply the
published upstream fix only" (`checks/sf-published-only.patch`) is caught by the two B-route groups
(`test_api_backend_kwargs.py`, `test_log_redaction.py`) and the two injected gaps
(`test_api_team_view.py`, `test_cli.py::test_get_value_hide_sensitive_hides_team_section_value`).
Channel-narrowing patches (`sf-no-cli-list`, `sf-no-env-spelling`, `sf-no-backend-kwargs`,
`sf-no-log-redaction`, `sf-no-team-view`, `sf-no-get-value`) are each caught by the trap tests
below. First-separator splitting (`sf-first-separator`) is caught by the six separator-shape tests
(20/26 on the recorded gate). Refuse-all (`ff-overbroad-team-mask`) is caught by
`functional/test_api_legit.py::test_team_non_sensitive_option_readable`,
`functional/test_cli_legit.py::test_config_list_shows_team_non_sensitive_values` and
`functional/test_parser_legit.py::test_masked_listing_still_marks_hidden`. Crash-as-refusal
(`sf-crash-single-option`) is caught by every `status < 500` assertion. Adjacent-API over-masking
(`ff-display-sensitive-masked`) is caught by
`functional/test_parser_legit.py::test_display_sensitive_returns_real_team_values` and
`functional/test_cli_legit.py::test_config_list_show_values_without_hiding_shows_team_value`.

**P2 — the command or secret reference a sensitive value is loaded from is covered.**
Most plausible wrong fix: hide only resolved values, leave team `_cmd`/`_secret` strings visible
(the code's existing base-section stance) — `checks/sf-no-cmd-secret.patch`. Caught by
`security/test_api_single_option.py::test_team_section_command_entry_not_revealed`,
`security/test_api_listing.py::test_team_section_command_and_secret_entries_not_in_listing` and
`security/test_api_listing.py::test_team_env_var_command_not_in_listing`. **Not caught:** the same
shape through `config list --hide-sensitive`, `get-value --hide-sensitive`, or log redaction.

**P3 — team-scoped sensitive values are redacted from logs exactly like deployment-wide values.**
Most plausible wrong fix: a display-only fix with no secrets-masker registration —
`checks/sf-no-log-redaction.patch`. Caught by `security/test_log_redaction.py` (all three tests).
The opposite wrong fix (register every team value) is caught by
`functional/test_log_legit.py::test_team_non_sensitive_value_not_redacted`.

### Per trap in `manifest.traps`

- **T1 landing single option.** Wrong fix `sf-landing-only.patch` → yes:
  `test_api_listing.py::test_team_section_value_not_in_listing`,
  `test_cli.py::test_config_list_hides_team_section_value`,
  `test_log_redaction.py::test_team_section_value_redacted`. Crash variant
  `sf-crash-single-option.patch` → yes, `_assert_not_revealed` asserts status < 500 in every
  single-option test. **Gap:** no test requires 200 + `< hidden >` for a *team* sensitive option,
  so a 404/omission refusal passes.
- **T2 listing file sections.** Wrong fix route-only (`sf-landing-only.patch`) → yes:
  `test_api_listing.py::test_team_section_value_not_in_listing`,
  `::test_team_section_value_not_in_section_filtered_listing`.
- **T3 env-var spelling.** Wrong fix file sections only (`sf-no-env-spelling.patch`) → yes:
  `test_api_listing.py::test_team_env_var_value_not_in_listing`,
  `::test_team_env_var_with_underscored_team_name_not_in_listing`,
  `test_api_single_option.py::test_team_env_var_spelling_not_revealed`,
  `test_log_redaction.py::test_team_env_var_value_redacted`.
- **T4 CLI listing.** Wrong fix API-only (`sf-no-cli-list.patch`) → yes:
  `test_cli.py::test_config_list_hides_team_section_value`,
  `::test_config_list_section_hides_team_section_value`,
  `::test_config_list_hides_team_name_containing_separator`.
- **T5 cmd/secret shapes.** Wrong fix values only (`sf-no-cmd-secret.patch`) → yes:
  `test_api_single_option.py::test_team_section_command_entry_not_revealed`,
  `test_api_listing.py::test_team_section_command_and_secret_entries_not_in_listing`,
  `::test_team_env_var_command_not_in_listing`.
- **T6 log redaction.** Wrong fix display-only (`sf-no-log-redaction.patch`) → yes:
  `test_log_redaction.py::test_team_section_value_redacted`,
  `::test_team_name_containing_separator_value_redacted`,
  `::test_team_env_var_value_redacted`; over-mask caught by
  `test_log_legit.py::test_team_non_sensitive_value_not_redacted`.
- **T7 per-key backend kwargs.** Wrong fix literal-section prefixes (`sf-no-backend-kwargs.patch`)
  → yes: `test_api_backend_kwargs.py::test_team_env_backend_kwarg_not_in_listing`,
  `::test_team_section_backend_kwarg_not_in_listing`,
  `::test_team_name_containing_separator_backend_kwarg_not_in_listing`. **Gap:** no team
  `workers`/`secrets_backend_kwarg__` case.
- **T8 injected team view.** Wrong fix keep the guard "skip only when the base value is already
  hidden" (`sf-no-team-view.patch`) → yes:
  `test_api_team_view.py::test_team_view_hides_override_of_unset_sensitive_option`,
  `::test_team_view_hides_override_of_backend_kwargs`. **Gap:** a guard that calls only
  `conf.is_sensitive_option` (not the per-key helper) leaks synthetic `backend_kwarg__*` overrides;
  no test covers that shape in the team view.
- **T9 injected get-value hide.** Wrong fix literal registry lookup (`sf-no-get-value.patch`) →
  yes: `test_cli.py::test_get_value_hide_sensitive_hides_team_section_value`. **Gap:** the env-var
  spelling through `get-value` is untested.
- **T10 arbitrary team name.** Wrong fix split on the first separator (`sf-first-separator.patch`)
  → yes: `test_api_single_option.py::test_team_name_containing_separator_not_revealed`,
  `test_api_listing.py::test_team_name_containing_separator_not_in_listing`,
  `::test_team_name_containing_separator_section_filtered_not_in_listing`,
  `test_api_backend_kwargs.py::test_team_name_containing_separator_backend_kwarg_not_in_listing`,
  `test_cli.py::test_config_list_hides_team_name_containing_separator`,
  `test_log_redaction.py::test_team_name_containing_separator_value_redacted`. **Gap:** a
  character-class allow-list covering exactly `[A-Za-z0-9_-=]` is not caught (no dot/space/unicode
  name).

### Wrong fixes no test catches

1. **Refusal instead of hiding** on the single-option route: return 404 (or 200 with the option
   omitted) for a team-scoped sensitive option. Every single-option security test asserts only
   `status < 500` and marker absence; no functional test pins 200 + `< hidden >` for a team option.
   `sf-crash-single-option.patch` catches only the 500 variant. The "or it is left out" wording
   even appears to sanction it (W1).
2. **Team view guarded by registered options only** (`conf.is_sensitive_option`): leaks
   `[team_a=secrets] backend_kwarg__*` and `[team_a=workers] secrets_backend_kwarg__*` overrides
   through `GET /config?team_name=`. `security/test_api_team_view.py` covers only `sentry_dsn` and
   `backend_kwargs`; the per-key tests hit the listing path (W2).
3. **Only the `secrets`/`backend_kwarg__` half** of `_PER_KEY_SENSITIVE_PREFIXES` is handled; no
   team test uses `workers`/`secrets_backend_kwarg__`, so a fix hard-coding one prefix passes
   (W3).
4. **`_cmd`/`_secret` through the CLI**: every command/secret test goes through the API.
   `config list --hide-sensitive` and `get-value --hide-sensitive` with a team
   `sql_alchemy_conn_cmd` are untested (W4).
5. **Env-var spelling through `get-value` / a section-filtered listing**: only the full listing and
   the odd spelling on the single-option route are tested; `get-value team_a
   _api_auth__jwt_secret --hide-sensitive` and `GET /config?section=team_a` are not (W5).
6. **Log redaction of team `_cmd`/`_secret` reference strings**: the redaction tests pass only
   resolved values through `redact()` (W6).
7. **`text/plain` listing**: only the single-option route is exercised with `text/plain`; the full
   and section-filtered listings are JSON-only (W7).
8. **Test-shaped name allow-lists**: no team name outside `[A-Za-z0-9_-=]`; a fix keyed to that
   character class (e.g. dot names like `data.eng` are rejected or not resolved) passes (W8).

## 3. Hints (quality, non-blocking)

No file name, function/identifier name, trap name or flaw count appears in `instruction.md`. The
sentences that come closest to machinery or to a variant list:

1. *"Some options are **registered as sensitive**: database connection strings, the Fernet key,
   API and JWT secrets, secrets-backend parameters, and so on."* — paraphrases the sensitivity
   registry and enumerates the exact shapes used in tests (`sql_alchemy_conn`, `fernet_key`,
   `secret_key`, `jwt_secret`, `backend_kwargs`/`backend_kwarg__*`). Neutral: *"Some options carry
   sensitive material — credentials, keys, tokens and parameters of the secrets backend."*
   Keep "secrets backend" (it is the only notice for T7).
2. *"…it replaces each sensitive value with the text `< hidden >`, and it redacts those values from
   the logs it writes."* — describes the required output form and the log channel. Needed for
   fairness; keep.
3. *"…over the REST API, on the command line, in the configuration view for one team, or in the
   process logs — for the whole configuration, one section, or one option."* — a full variant list
   of the four channels and three granularities; it points at the injected team view (T8) and every
   other trap surface. Neutral: *"wherever Airflow shows configuration with sensitive values
   hidden, on every interface and at every granularity (whole configuration, one section, or one
   option), including process output."*
4. *"This covers the command or secret reference a sensitive value is loaded from as well as the
   value itself."* — names the `_cmd`/`_secret` mechanism nearly verbatim; it is also the only
   notice for T5. Keep the coverage, genericise the wording: *"This covers any reference from which
   a sensitive value is loaded as well as the value itself."*
5. *"This holds however the team-scoped value is supplied, and whatever the team is called."* —
   scope, not mechanism; the sole cover for T3/T10. Do not delete; strengthen (see C1 below).
6. *"(such as the Kubernetes provider or `airflow config lint`)"* — names two real unmasked
   callers. They are illustration, not a fix location. Neutral: *"(such as providers or CLI
   commands that consume configuration)"*.
7. *"The example above is one instance, not the full set of ways the properties can be violated."*
   — tells the solver variants exist (no count). Acceptable; optional neutral wording: *"The
   example above is one instance."*
8. *"A team-scoped override holds the same kind of material as the deployment-wide option it
   overrides; for a sensitive option it is that team's own secret."* — states the fix principle in
   one sentence. It is the core requirement, not a leak of a file/function; keep.

The example (`[team_a=database] sql_alchemy_conn`, the exact GET URL) is the observed instance and
is de-special-cased by "The example above is one instance …" and "do not special-case the example
input". The tests deliberately reuse those names, but the security properties are general.

## 4. Realism (quality, non-blocking)

- **T1–T7 and T10** are the published upstream fix sites in real code: the REST config route, the
  shared parser (`as_dict`/`_include_envs`/`write`), the CLI write path, and core start-up masking.
  All are reachable from the documented entry points; nothing is planted. T3's
  `section=<team>`/`key=_<section>__<key>` spelling is odd but is the genuine loader split.
- **T6** (core `mask_secrets` registers only base-section values) and **T7** (per-key kwargs masked
  by literal `secrets`/`workers` section names) are real, unmodified upstream code with real
  entry points (`import airflow`; `GET /config`). The "nothing leaks; the backend is not team
  aware" rationalisation appears only in `checks/sf-published-only.patch`, not in the solver tree.
- **T8** (`GET /config?team_name=`) is injected but plausible: a per-team configuration view is a
  natural feature built on `conf.getsection(team_name=)`, and the "skip when the base value is
  already hidden" guard is a natural, incomplete guard that looks complete because it defers to
  the already-masked listing. Reachable through the REST surface; flagged as injected.
- **T9** (`get-value --hide-sensitive`) is injected but mirrors the existing
  `config list --hide-sensitive` flag, including help text. Plausible and reachable; flagged as
  injected.
- **T10** (`[a=b=database]`, a team name containing the section separator) is the most exotic and
  the most planted-looking input. A team name containing `=` is unusual in a real deployment; the
  feature treats names as opaque labels, so it is defensible only because the published fix
  resolves right-to-left. Flagged as borderline contrived (see C1 and the quality list: add a more
  realistic dot/space name and keep the separator case as an extra, with explicit wording).
- The `team_view` test for `sentry_dsn` (team sets a DSN while the deployment does not) and the
  `ML_PLATFORM` underscored team name are realistic.
- Build consistency: `manifest.json` and `notes.md` record a 33-test revision and claim the
  arbitrary-name sentence was added, but the tree contains 26 security tests and the old wording.
  This looks like a reset/revert; it increases leniency (the W1–W4/W8 covers are absent) and should
  be reconciled before trial, but it is not itself an unfairness.

## 5. Verdict — two gates

### a. UNFAIRNESS gate: **NOT READY**

Two gate-a mechanisms remain in the tree on disk:

**C1 (ambiguous spec vs. the separator-shape tests).** Six security tests
(`test_api_single_option.py::test_team_name_containing_separator_not_revealed`,
`test_api_listing.py::test_team_name_containing_separator_not_in_listing`,
`::test_team_name_containing_separator_section_filtered_not_in_listing`,
`test_api_backend_kwargs.py::test_team_name_containing_separator_backend_kwarg_not_in_listing`,
`test_cli.py::test_config_list_hides_team_name_containing_separator`,
`test_log_redaction.py::test_team_name_containing_separator_value_redacted`) plus one functional
readability test require a team name containing `=`. Their only cover is *"whatever the team is
called"*, which does not say names are opaque or may contain the separator the implementation uses.
A competent implementation of the inverse of `f"{team_name}={section}"` using
`split("=", 1)` / `partition("=")` satisfies every explicit sentence except that phrase and fails
six security tests (`checks/sf-first-separator.patch`, recorded 20/26). This is an unresolved
"maybe". Required change (exact wording):

> Replace "This holds however the team-scoped value is supplied, and whatever the team is called."
> with "This holds however the team-scoped value is supplied. Team names are arbitrary labels and
> nothing may be assumed about the characters a name contains."

(Neutral: names no separator and no split direction.)

**C2 (instruction says one thing, tests another).** "Hidden form" says the option "stays listed and
its value is `< hidden >` **(or it is left out)**". Three CLI tests
(`security/test_cli.py::test_config_list_hides_team_section_value` line 17,
`::test_config_list_section_hides_team_section_value` line 31,
`::test_config_list_hides_team_name_containing_separator` line 45) additionally require the section
header to remain in stdout. A compliant fix that leaves the hidden option out and does not print a
section with nothing visible fails them. Required change — pick one:
(i) amend the contract to

> "**Hidden form.** A hidden value is reported the way it is today: the option stays listed and its
> value is `< hidden >`, and the request still succeeds — hiding must not turn a request into an
> error or a not-found. A section stays listed even when every value in it is hidden."

and (optionally) add a functional test pinning 200 + `< hidden >` for a team-scoped sensitive
single option (this also closes leniency W1); **or**
(ii) delete the three `assert "[team_…]" in proc.stdout` header assertions, keeping only the
marker-absence assertions. Option (ii) loosens the grader and admits section-dropping fixes, so (i)
is recommended.

Also reconcile the tree with the recorded revision: add the missing W1–W4/W8 tests (presently
absent) when applying C1/C2, so the gate runs the test set the manifest claims.

### b. QUALITY gate (recorded, not a reason for NOT READY)

See the "Quality to tighten" list below; all items are coverage/quality improvements, not
unfairness.
