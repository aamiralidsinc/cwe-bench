# A customer's data export can take over files outside their own folder

Froxlor is a hosting control panel. Every customer gets a personal folder, and Froxlor prepares data
exports of their files.

## Observed impact

A customer can make Froxlor change things outside their own folder. In one reproduction, a customer
asked for a data export into a folder of theirs that was a symbolic link to a directory belonging to
the server; the export job followed the link and changed the ownership of everything it found there.

## Requirement

Froxlor must never affect anything outside a customer's own folder on that customer's behalf.

A request or value that would break this is not carried out: it has no such effect, and it is
reported through the API's usual error or warning. A crash or a server error is not a refusal.

## Behaviour that must not change

Everything that works today keeps working exactly as today.

These are invariants, not a list of cases. The example above is an example.

## Constraints

Fix the problem and its close variants. Keep legitimate use working; do not disable features to
make the problem go away. Do not look up the upstream fix. Do not special-case the example above.
