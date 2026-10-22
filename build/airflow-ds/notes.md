# airflow-ds — build notes

- Start UTC: 2026-10-18T22:12:47Z (pipeline start; this builder session begins 22:13Z)
- End UTC: see end of file

## Design plan (written before building)

Pinned commit is the direct parent of 62d37d52 (`266f18ec`); the same base flaw exists upstream:
sensitivity of a configuration value is a literal `(section, key)` lookup in the shared parser's
`sensitive_config_values`, so the alternate spellings used for a team-scoped override are not
recognised. The published fix (62d37d52 / d41ac7b6) resolves the spelling back to the base option at
four places.

Levers, each with a different reason a solver would dismiss or skip it:

- T1 A landing (published): the single-option REST route hides only a literal registered pair —
  `routes/public/config.py:156`.
- T2 A far site (published): the full/section listing masks by iterating the registry, so
  `[<team>=<section>]` file sections are skipped — shared `parser.py:1792-1803`. Dismiss: it is a
  lower-level shared library, not the API route the report leads to.
- T3 A far site / producer (published): the config loader splits a team environment variable into
  section `<team>` and key `_<section>__<key>`, a spelling the registry does not contain — shared
  `parser.py:790-794`. Dismiss: it looks like an unknown/ignored option.
- T4 A far site / render path (published): `airflow config list --hide-sensitive` re-checks the
  literal pair when writing — shared `parser.py:2035-2038`. Dismiss: local admin CLI run by the
  owner of the config file.
- T5 input shape (published): team-scoped `_cmd` / `_secret` fallbacks are never resolved for a team,
  so the command string or secret path itself is shown unless the name is resolved with the suffix.
  Dismiss: existing code deliberately leaves `_cmd`/`_secret` entries visible in a base section.
- T6 B (real, unmodified upstream): core start-up log redaction registers only base-section values
  with the secrets masker — `airflow-core/src/airflow/configuration.py:438-455`. Dismiss: different
  output channel (logs, not configuration display).
- T7 B (real, unmodified upstream): per-key secrets-backend kwarg masking is keyed on the literal
  `secrets`/`workers` section names — `core_api/services/public/config.py:34-58`. Dismiss: the
  published fix itself documents this as not leaking because the backend is not team aware.
- T8 injected sibling: `GET /config?team_name=<team>` (the configuration a team runs with) copies
  team overrides over the already-masked listing, skipping only options whose base value is already
  hidden. Placed in `services/public/config.py` + the route. Dismiss: it defers to the already-masked
  base listing, so it looks complete; and it is an admin API.
- T9 injected sibling: `airflow config get-value ... --hide-sensitive` re-checks the literal pair;
  the flag mirrors the existing `config list --hide-sensitive`. Dismiss: `get-value` prints raw
  values by design and is an admin CLI.
- T10 input shape (published fix covers, one-case fixes miss): team names are arbitrary labels.
  A name containing the section separator (`[a=b=core]`) is only resolved correctly when the name is
  split against the known base section, or from the right; splitting on the first separator leaves a
  base section that is not registered and leaks. Tested through the single-option route, the full
  listing, the per-key backend-kwarg route, the CLI listing and log redaction.

Pattern B routes confirmed on the pinned copy: T6 and T7 (rows added to the register).
The task-sdk `mask_secrets` lead is dropped: it has no in-tree caller at this commit, so there is no
real entry point.

Coupled behaviour kept working (functional tests): team-scoped non-sensitive options (single-option,
listing, team view, CLI, per-key non-kwarg `secrets` option) readable; deployment-wide options
unchanged; `display_sensitive=True` callers (and `config list --show-values` without hiding) still
get real values; non-sensitive values not redacted from logs; unknown option still 404.

## Status

- Local image (task Dockerfile, `--network none`): nop security 0/26, functional 317/317; oracle
  security 26/26, functional 317/317 (reward 1.0); `sf-first-separator.patch` security 20/26
  (exactly the six separator-shape tests), functional 317/317.
- Project tests (API config, CLI config, shared parser) run as part of the functional group and
  pass on both nop and oracle.
- Gate: static fails only on the expected outstanding blind patch + FAIRNESS.md; nop PASS
  (26 security, 317 functional); oracle PASS (3 identical runs); patches PASS (15/15: 11 security_fail,
  2 functional_fail, 2 pass at reward 1.0).
- Shared-machine note: the gate's per-trial `docker network prune` races with the other builder
  gates on the same Docker daemon (13 concurrent gates observed): fresh compose networks were
  deleted before the sidecar started (`network ... not found`). Two stage attempts were lost to the
  race; a detached helper attached a keeper container only to this task's own `airflow-ds__*`
  networks and released it as soon as the trial's own containers were attached, which closed the
  race without touching other containers, images or the build cache.
- End UTC: 2026-10-19T00:35Z. Final gate stages: nop PASS, oracle PASS, patches PASS; static only
  the pipeline-owned blind patch + FAIRNESS.md outstanding (not written here, per the build brief).

## Fairness revision (2026-10-19, pre-trial)

Applied `FAIRNESS.md`:

- C1: property 1 now says team names are arbitrary labels and nothing may be assumed about the
  characters a name contains (no split direction or separator named).
- C2: "Hidden form" now requires the option to stay listed with `< hidden >` and the request to
  succeed; a section stays listed when all its values are hidden. The CLI section-header assertions
  are therefore consistent with the contract.
- W1: new security test `test_api_single_option.py::test_team_sensitive_option_hidden_with_success_status`
  asserts 200 + `< hidden >` (a hidden-asserting test cannot live in the functional group because
  the untouched code must pass every functional test at nop).
- W2: `test_api_team_view.py::test_team_view_hides_override_of_per_key_backend_kwarg`.
- W3: `test_api_backend_kwargs.py` gains team env-var and `[team=workers]` cases for the
  `secrets_backend_kwarg__` half of the per-key registry.
- W4: `test_cli.py::test_config_list_hides_team_command_and_secret_entries` covers team `_cmd` /
  `_secret` reference strings in the CLI listing.
- W8: a dot-containing team name (`data.eng`) is covered by two security tests and one functional
  readability test, so character-class allow-lists keyed to `[A-Za-z0-9_-=]` no longer pass.
- Counts after revision: 33 security, 318 functional. Local runs: nop security 0/33 + functional
  318/318; oracle security 33/33 + functional 318/318.

## Fairness revision re-applied (2026-10-20, pre-trial)

The tree on disk had been reset to the pre-revision state (26 security / 22 hidden functional tests,
old C1/C2 wording, hint sentences restored). Re-applied the recorded revision before trial:

- C1 and C2 restored verbatim from `FAIRNESS.md`: arbitrary-label notice in property 1, and the
  Hidden-form contract now requires the option to stay listed with `< hidden >`, the request to
  succeed, and an all-hidden section to stay listed.
- W1 (success status + exact `< hidden >`, in security), W2 (team-view per-key kwarg), W3 (both
  workers/`secrets_backend_kwarg__` shapes), W4 (CLI `_cmd`/`_secret`) and W8 (dot team name,
  security + functional) test additions restored, matching `manifest.traps`.
- Hint neutralisations from FAIRNESS.md §3 (items 1, 3, 4, 6, 7) applied to `instruction.md`.
- Counts are again 33 security and 318 functional (23 hidden + 295 project).
- Gate re-run 2026-10-20, one stage at a time: nop PASS (security 0/33, functional 318/318);
  oracle PASS (3 identical runs, reward 1.0); patches PASS (15/15: 11 security_fail,
  2 functional_fail, 2 pass at reward 1.0); static clean except the pipeline-owned blind patch.






## Sibling-injection upgrade (2026-10-20, instruction-only)

- `instruction.md` rewritten to a single general property over the protected data: no
  route/interface/command/channel/format/granularity list, no config-file/environment/logs wording,
  no example route. The example is now product-level data (a hidden deployment-wide password vs the
  same team's intact override), and the arbitrary-team-name clause stays in the property.
- Contracts preserved generally: hidden form (entry stays listed, exact `< hidden >`, request
  succeeds, all-hidden section stays listed) and preservation (non-sensitive team values readable,
  deployment-wide unchanged, real values wherever they are returned today, non-sensitive values not
  concealed from output).
- No test, solution/fix.patch, checks/, environment/ or repo change; prebuilt image reused.
  Nop/oracle/patch validity is unchanged by construction.
- `manifest.leak_terms` extended with the route/source/channel words the rewrite forbids
  (`REST API`, `api/v2`, `command line`, `configuration file`, `environment variable`, `logs`,
  `process output`) so the static scan enforces the §2 style.
- HOW-type levers already present, no new lever added: T3 (producer: team env-var spelling the
  registry lookup never sees), T6/T7 (real routes where protection never existed: start-up log
  redaction and per-key backend kwargs), T10 (parser/shape differential: arbitrary team names with
  the section separator).

## Hardening + Frontier delivery format (2026-10-21)

Pre-verdict: the trial record shows DeepSeek solved the task (one run at 1.0, one at 0.9091), and
it fixed every earlier A-site lever in both runs; only T6 (start-up log registration) and T10
(arbitrary team names) were each left open once. Two further fair levers exist in real, unmodified
upstream code and need no new injection:

- T11 (B, producer off the check's path): start-up log registration masks per-key secrets-backend
  variables only under the deployment-wide prefix (`AIRFLOW__SECRETS__BACKEND_KWARG__*`,
  `AIRFLOW__WORKERS__SECRETS_BACKEND_KWARG__*`). The team scoped spelling puts the team name before
  the section, so the collector never sees it and the team's material stays in clear in logs while
  the deployment-wide value is redacted. Dismissal: the published fix itself documents the secrets
  backend as not team aware, and the API already hides the same values.
- T12 (B, a second copy of the classification rule): per-key backend kwargs are sensitive by a rule
  that lives in the API service module, outside the registered option list. The CLI listing's write
  decision and `get-value` classify by the registered option list, so a team scoped per-key entry is
  printed in clear even though Airflow hides the deployment-wide counterpart in the API. Dismissal:
  the CLI is a local admin tool and the per-key rule is an API-layer detail; the deployment-wide
  per-key value is also visible there today (which the fix keeps as it is).

Both are covered by the existing general property ("anywhere Airflow conceals sensitive
configuration or removes sensitive values ... however the override is supplied"). The oracle now
also resolves those two shapes; the deployment-wide per-key behaviour is deliberately unchanged
(the preservation clause), so the per-key rule applies only to team scoped spellings.

Delivery format: converted to schema 1.4 per builder/FRONTIER-CONFORMANCE-SPEC.md — repo builds at
/workspace, separate offline verifier from tests/Dockerfile, artifacts restore, uid-1000 non-root
grading, fresh one-commit git baseline, canary GUID, B7 metadata, dual scoring. The verifier imports
the restored tree through PYTHONPATH over a pristine dependency install at /opt/airflow-pristine.
`blind.patch` is an informed fix (instruction + the injected tree + the trap list, no test files),
applied and verified in-container; it is wired as the strict gate's pass/blind entry.

Verifier detail: the hidden suites are copied to /workspace/.htests together with the root
conftest.py, and run with `--confcutdir=/workspace/.htests -o pythonpath=/workspace/.htests` so the
hidden conftest (fixtures and helpers) wins over the project's `pythonpath = ["airflow-core/src",
"airflow-core/tests"]` config, which otherwise makes `import conftest` resolve to the project's
conftest. Nop: 40/40 security tests fail, 30/30 hidden functional pass; oracle: 70/70 pass.

### Final gate (2026-10-21T22:xxZ – 2026-10-22T00:32Z)

- `conformance_check.py` prints `conforming`; `gate.py --only static` PASSED.
- `--only nop` PASSED: 40/40 security tests fail on the injected vulnerable code; 325/325 functional pass
  (30 hidden + 295 project).
- `--only oracle` PASSED: 3 identical runs, reward 1.0 (40 security + 325 functional).
- `--only patches` PASSED 18/18: 13 `security_fail` (each leaves its lever's security tests failing with
  every functional test passing), 2 `functional_fail`, and 3 `pass` at reward 1.0
  (`pass-hardening`, `pass-alt-env-parse`, `blind`).
- The two new lever checks: `sf-no-team-per-key-log.patch` leaves exactly the 2 team per-key log tests
  failing; `sf-no-cli-per-key.patch` leaves exactly the 5 team per-key CLI tests failing.
