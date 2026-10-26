# Names that users store are rendered as markup

OpenSTAManager is an open-source ERP/CRM for technical assistance and invoicing. Users name the
things they create — groups of users, customers and suppliers, contacts, service types — and the
product shows those names back to everyone who works with them, on record pages and in the
suggestion lists that fill its search fields.

## What happens

A user who is allowed to manage users and permissions renames a group to `Beta <img src=x>`. The
editor accepts it. Opening that group's page then shows an actual image element where the name
should be, and a colleague who picks the same group in a search field receives the same element
in the suggestion instead of the group's name. The stored value is served back that way on every
visit, to every user who can see the group.

## The rule

A value a user saved is text. Wherever the product displays that value to any user — on a
record page or in any suggestion list it offers — the value must arrive as text: it must never
be able to create or alter elements, attributes, links or script, whatever characters it
contains. This covers values that were saved before the fix as well as values saved after it,
and however the product reaches them.

Interface used by the suggestion lists: the search answer is JSON, and an item's display text is
its `text` value; an item that sits inside an optgroup carries its display text the same way,
under its own `text` key.

Everything that works today must keep working exactly as today: names still display, a record
still lists its members and their details, and the links the product itself builds around a name
— the record links it puts next to a suggestion — still work and still point at the same record.

The names, characters and places above are examples of how the product is used, not the complete
set of values, surfaces or ways a stored name can reach a page.

## Working on it

A local instance can be started with `/opt/osm/run-app.sh` and is then reachable at
`http://127.0.0.1:8099/`; it comes with an administrator account (`admin` / `testpass`) and an
ordinary account (`clerk` / `testpass`). `/opt/osm/run-app.sh stop` stops it.

## Constraints

Fix the problem and its close variants. Keep legitimate use working. Do not look up the upstream
fix or the advisory. Do not special-case the example.
