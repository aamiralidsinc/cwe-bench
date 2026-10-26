# A do-file run can run commands the service never issued

## What this is

Stata-MCP is a local service that lets an assistant or a script drive a Stata installation. A
client asks it to run an analysis do-file; the service builds the Stata command text for that run
and hands it to the local Stata command line.

## Observed impact

In one reproduction a client asked the service to run `/data/analysis.do` with a log name taken
from the uploader's dataset file name:

    stata_do("/data/analysis.do", log_file_name="wave1_clean")

The value used in the reproduction was not that clean one. The run reported success, and the
Stata session had additionally run a command the service never issued.

## Security property

Whatever value a client supplies is data for the commands the service itself builds, never
command syntax. The only Stata commands a request can cause are the ones the service issues for
that request; no caller value may make Stata run any other command.

## Contracts

- A refused call reports an error to its caller (a surface that returns a structured result
  returns an error entry; a surface that raises does so) and has no effect.
- Only a value that would change the command is refused. An ordinary value keeps working exactly
  as it does today, however it is spelled.
- Nothing else about the service's behaviour changes.

The example above is one instance, not the full set of ways the property can be violated.

## Constraints

- Fix the problem and its close variants, not just the call shown.
- Keep every legitimate use working.
- Do not look up the upstream advisory or fix for this issue.
- Do not special-case the example.
- There is no network access.
