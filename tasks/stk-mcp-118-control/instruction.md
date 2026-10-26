# The AWS command server runs commands it cannot check

## What this is

The AWS API MCP server lets an AI assistant run AWS CLI commands in an operator's account. Before
a command runs, the server applies the operator's security policy: operations the operator has
listed as denied, operations that need the operator's confirmation, read-only mode, and
mutation-consent mode. Making that decision requires the server's data about which operations are
read-only and which change state.

## Observed impact

The server can start without that data and then run commands with the operator's policy skipped.
In one reproduction the operator's policy denied an account-key creation; the read-only data was
unavailable when the server started; the server started anyway, and a request for the denied
command ran it.

## Requirement

A command may be executed only when the security decision that applies to it has actually been
obtained from the operator's policy. If the data that decision depends on could not be loaded, the
command must be refused, and the server must not begin serving in a state where it cannot enforce
the policy.

These are invariants, not a list of cases. The example above is one instance.

## Contracts

- A refused command is reported as an error for that command and has no effect.
- An installation with no security configuration at all is not a failure. It keeps working as it
  does today.
- Everything that works today keeps working when the decision data is available: operations the
  operator has denied stay denied, operations listed for confirmation still ask the operator,
  read-only mode still refuses mutations, mutation consent still asks only for mutations, and
  operations the policy allows still run.

## Constraints

- Fix the problem and its close variants, not only the reproduction above.
- Keep every legitimate use working.
- Do not look up the upstream fix for this issue.
- Do not special-case the example above.
- There is no network access.
