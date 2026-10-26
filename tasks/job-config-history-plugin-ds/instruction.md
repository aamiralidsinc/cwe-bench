# Stored configurations expose secrets to users who may only read them

The Job Configuration History plugin keeps every version of a job's configuration and lets users
browse the saved revisions. Jenkins separates the right to change a configuration from the right
to inspect it: a user may be allowed to read a job's configuration without being allowed to
change it.

A user who is allowed to inspect a job's configuration but not to change it can browse an earlier
revision and receives the job's secret values exactly as they were stored. For example,
`GET /job/example/jobConfigHistory/configOutput?type=xml&timestamp=<revision>` returns that
revision's configuration with its stored secret values intact.

## What must hold

A user who may inspect the configuration of an object managed by the controller but may not
configure that object must never be shown a secret value recorded in that configuration or in any
saved revision of it — neither the form in which the controller stores the value nor a plain-text
value kept in an older revision — through any output of the history feature.

A user who may configure the object keeps full access to the stored values, and restoring a saved
revision must restore the exact original values.

## Contracts

- When a reader is allowed to see a configuration, everything that is not a secret stays visible
  exactly as it is today.
- The history views and the restore action keep working for every user who could use them before.
- A refusal is a client error (4xx) and must not change stored state; a server error is not a
  refusal.
- The requirements apply to the whole history feature, not only to the example above.

There is no network access.

## Constraints

Fix the problem and its close variants. Keep legitimate use working. Do not look up the upstream
fix or any existing implementation. Do not special-case the example.
