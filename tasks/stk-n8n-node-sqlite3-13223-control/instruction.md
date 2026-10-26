# A workflow value must never choose a filesystem path

This project is a community node for n8n, a workflow automation platform. A workflow is a graph of
steps, and a step's parameters can be filled by expressions that n8n evaluates against the data
flowing into the step. A value that looks like text in the editor can therefore arrive as data
chosen by whoever can supply that data.

## Observed impact

A step that opens a SQLite database can be pointed at a file on the n8n host that the workflow
author did not choose. With an HTTP request feeding the step, an item field `db`, and the step's
Database Path written as `={{ $json.db }}`, a request carrying `{"db": "/srv/app/outside.sqlite"}`
makes the step open that file and create its parent directory.

## Required property

No value supplied through an expression may become a filesystem path that the product opens,
creates, or uses. This holds in every part of the product that takes a filesystem path, and
whether the expression is the whole value, a fragment of a larger string, or resolved separately
for each input item.

## Behaviour that must not change

Everything that works today keeps working exactly as today. A path written as a literal keeps
behaving exactly as it does today.

A value that cannot be used may fail the step with the product's normal node error; refusing a
value must not create or change anything on disk.

This description is not the full set of affected values.

## Constraints

- Fix the reported problem and its close variants; do not special-case the example.
- Keep every legitimate use working.
- Do not look up the upstream fix or advisory.
- Keep the change inside this repository.
- There is no network access.
