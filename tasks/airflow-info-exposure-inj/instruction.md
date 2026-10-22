# Team-scoped secrets show up in plain text where Airflow hides sensitive configuration

## System

Apache Airflow is a workflow orchestration platform. Its configuration comes
from a configuration file, environment variables and command/secret fallbacks.
Some options are registered as **sensitive**: database connection strings,
the Fernet key, API and JWT secrets, secrets-backend parameters, and so on.
Wherever Airflow presents configuration with sensitive values hidden, it
replaces each sensitive value with the text `< hidden >`, and it redacts those
values from the logs it writes.

In a multi-team deployment, a team may override any option for itself. A
team-scoped override holds the same kind of material as the deployment-wide
option it overrides; for a sensitive option it is that team's own secret.

## Observed impact

With configuration exposed over the REST API (which always hides sensitive
values), a user who holds read access to configuration, and no access to the
secrets themselves, can read any team's credentials. For example, with

```
[team_a=database]
sql_alchemy_conn = postgresql://team_a:S3cret@db/airflow
```

in the configuration file, `GET /api/v2/config/section/team_a=database/option/sql_alchemy_conn`
returns the full connection string, password included, while the
deployment-wide `[database] sql_alchemy_conn` correctly comes back as
`< hidden >`.

## Security properties that must hold

- No value of a team-scoped override of a sensitive option may be shown
  anywhere Airflow shows configuration with sensitive values hidden — over the
  REST API or on the command line, for all of the configuration, one section,
  one option, or the configuration as one team sees it.
- This holds however the team-scoped value is supplied, and it covers the
  command or secret reference a sensitive value is loaded from as well as the
  value itself.
- A team-scoped sensitive value must be redacted from Airflow's logs exactly
  like the deployment-wide value of the same option.

## Contracts the fix must honor

- **Hidden form.** A hidden value is reported the way it is today: the option
  stays listed and its value is `< hidden >` (or it is left out). Hiding must
  not turn a request into a server error.
- **Preservation.** Non-sensitive team-scoped options (for example
  `[team_a=core] parallelism = 64`) stay readable exactly as today, through the
  API, the per-team configuration view and the command line. Deployment-wide
  options keep their current behaviour. When sensitive values are explicitly
  requested — the command line without its option to hide them, and code that asks the configuration for unmasked values
  (such as the Kubernetes provider or `airflow config lint`) — the real values,
  team-scoped ones included, are still returned. Non-sensitive values must not
  be redacted from logs.

The example above is one instance, not the full set of ways the properties can
be violated.

## Constraints

- Fix the flaw and its close variants, not just the request shown.
- Keep every legitimate use working.
- Do not special-case the example input.
- Do not consult any upstream advisory or fix for this issue.
- There is no network access.
