# Client-supplied names reach Camel's own message headers

Apache Camel is an integration framework. A route receives a message from outside the application,
runs the message through processors that read and act on its headers, and passes it on to another
endpoint. Next to the application's own headers, Camel reserves a set of header names for itself —
values such as the response status or the target path — that components read and act on.

We found that a client can set one of them. A request to a route that carries the header
`caMElHttpResponseCode: 503` reaches the route with Camel's response-status header already set to
503, so the reply the application did not control goes out with that status. The value is readable
under Camel's own spelling because message headers are matched without regard to case.

## The property

A name that comes from outside the application must never become one of Camel's own message
headers — not under any capitalization, and however the client supplies it. Only the application
itself may set those headers.

## Contracts

- The rest of such a request is processed normally. Dropping the name must not reject the request,
  must not answer with an error, and must not change the body or any other value.
- Everything that works today keeps working exactly as it does today: every other name a client
  supplies keeps arriving under its own name, and a value the application itself sets under one of
  Camel's own header names keeps having exactly the effect it has today.

The example above is one instance, not the list. Fix the problem and its close variants rather than
that one spelling, keep legitimate use working, do not special-case the example, and do not look up
the upstream fix.
