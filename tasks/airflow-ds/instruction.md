# Team-scoped secrets are disclosed in clear text where Airflow conceals sensitive configuration

## System

Apache Airflow is a workflow orchestration platform. Its configuration can be
overridden for an individual team. A team-scoped override holds the same kind of
material as the deployment-wide option it overrides; where the deployment-wide
value is sensitive, the override is that team's own secret. Airflow already
conceals sensitive configuration values wherever it presents configuration in a
sensitive-hidden form, reporting them as the exact text `< hidden >`, and it
removes them from the output it produces.

## Observed impact

A user who is allowed to read configuration, but not the secrets themselves, can
obtain a team's credential in clear text. The deployment-wide value of the same
option is concealed, while the team-scoped override is not. For example, a
deployment-wide database password is reported as `< hidden >`, but a team's
override of that same option comes back intact, password included.

## Security property that must hold

No team-scoped override of an option whose deployment-wide counterpart Airflow
conceals as sensitive may be disclosed in clear text anywhere Airflow conceals
sensitive configuration or removes sensitive values from the output it produces.
This holds for the value itself and for any reference from which such a value is
loaded, at every interface and every granularity at which configuration is
presented, however the override is supplied, and for arbitrary team names: a
team name is an unconstrained label, and nothing may be assumed about the
characters it contains.

## Contracts the fix must honor

- **Hidden form.** A concealed value is reported the way it is today: the entry
  stays listed with the exact value `< hidden >`, and the request still
  succeeds — concealing must not turn a request into an error or a not-found. An
  all-concealed group stays listed.
- **Preservation.** Non-sensitive team-scoped values stay readable exactly as
  today, and deployment-wide values keep their current behaviour. Where current
  behaviour returns real values — team-scoped and deployment-wide alike — it
  must keep doing so. Non-sensitive values are not concealed from that output.

## Constraints

- Fix the flaw and its close variants, not just the case shown.
- Keep every legitimate use working.
- Do not special-case the example input.
- Do not look up or consult any upstream advisory or fix for this issue.
- There is no network access.
