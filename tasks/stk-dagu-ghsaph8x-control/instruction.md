# DAG names can reach files outside the DAGs directory

## What this is

dagu is a workflow engine. Operators keep their workflow definitions as YAML files in a
single configured DAGs directory, and the server offers an HTTP API for creating,
reading, updating, renaming, deleting, and running them. The same directory is the
server's whole notion of where a DAG file belongs.

## What was observed

A client requested `/api/v1/dags/..%2F..%2Fnotes/spec` and the server returned the
contents of a YAML workflow file that was never placed in the configured DAGs directory.

## Required property

The configured DAGs directory is the only place a DAG file may be read, created, changed,
renamed, deleted, or executed from. No identifier, name, path, or entry — however it is
spelled or encoded, and whichever party supplies it — may cause any file outside that
directory to be touched.

An attempt made through the HTTP API must be refused with a client error and must leave
the filesystem unchanged. A value that cannot designate a location inside the DAGs
directory must never be redirected to a different location.

## Contracts

- Create, read, update, rename, delete, and run keep their current success responses for
  every DAG whose file lives inside the DAGs directory.
- Creating a DAG with a workflow body and creating one without a body both keep working.
- DAG names may contain dots. Dots are part of the documented name alphabet and stay
  legal wherever a DAG name is accepted.
- DAG files that already live in subdirectories of the DAGs directory keep working in
  those subdirectories.
- Everything that works today keeps working exactly as today.

The value in the example above is an example, not the full set of values or forms that
must be refused.

## Constraints

- Fix the problem and its close variants.
- Keep legitimate use working.
- Do not look up the upstream fix or an existing implementation.
- Do not special-case the example.
- There is no network access.
