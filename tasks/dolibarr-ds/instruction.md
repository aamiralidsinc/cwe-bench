# Employee records are readable and changeable across teams

Dolibarr is an open-source ERP/CRM. Its REST API lets an authenticated employee work with
company records: leave requests and expense reports, together with the information and
workflow around them.

## What happens

An employee who holds only the ordinary leave permissions can ask the API for a leave request
that belongs to a colleague outside their team and receive the whole record. With that
employee's API key, a plain read such as `GET /api/index.php/holidays/{id}` returns a leave
filed by a user who is neither the caller nor one of their reports. The same key also lets
them change such records and run approval actions on them.

## The rule

For employee-owned records such as leave requests and expense reports, an actor may only see,
create, change, delete or otherwise act on a record — and on information derived from it —
when the user the record belongs to is inside the actor's management hierarchy: the actor and
every user below them, at any depth. A record may not be created for, moved to, or made
accessible to a user outside that hierarchy. The module's broader all-user permissions keep
their meaning: a holder may work with anyone's records.

This applies to everything the API returns or changes about such records, however the request
is shaped.

Everything that works today for permitted users must keep working exactly as today: an
employee's own records; records of users below them; records they are designated to approve;
records covered by the broader permissions; and requests that do not touch ownership.

A request the rule forbids must fail with a client error and have no effect: nothing may be
changed, deleted or created. The response shape and permissions of permitted requests stay as
they are.

The request form and identifiers above are examples of how the API is used, not the complete
set of ways a record can be reached or changed.

## Constraints

Fix the problem and its close variants. Keep legitimate use working. Do not look up the
upstream fix or the advisory. Do not special-case the example.
