# A published REST query can send datasource credentials to another server

Budibase is a low-code platform. An app builder can add a REST API datasource, store authentication
on it (a bearer token, or a basic username and password) together with fixed request headers, and
then write queries against that datasource. Those stored values are secrets: the product masks them
when it returns datasource details.

A query can be published so that anyone using the app may run it. A caller then supplies a value for
one of the query's parameters that makes the request address name a different server, and Budibase
sends the datasource's stored authentication and headers to that caller's server, where they can be
recorded and reused against the real API.

## Requirement

Credentials stored on a datasource may only be sent to the origin that the query's own saved
definition, together with the datasource's configuration, calls for.

If a request cannot keep the stored credentials on their own origin, the query is either refused —
a client error, with nothing sent — or carried out with every stored credential removed. A refused
query has no other effect.

These are invariants, not a list of cases. The example above is an example.

## Behaviour that must not change

Everything that works today keeps working exactly as today.

## Constraints

Fix the problem and its close variants. Keep legitimate use working. Do not look up the upstream fix.
Do not special-case the example above.
