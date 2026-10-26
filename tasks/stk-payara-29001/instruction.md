# Payara Server — an administrator's REST credential can be sent to a caller-chosen host

Payara Server's administration console is a web application. Administrators sign in to it and use it
to download files the console collects or produces. The console holds an administrator's REST
session credential and uses it, on the server side, for the administration requests it makes on the
administrator's behalf.

## Observed impact

An administrator who opens a link that asks the console to fetch a file while naming a different
administration base sends their stored REST credential to the host named in the link. The holder of
that host can replay the credential and take administrative control of the domain.

## Security property

Every download is carried out with the console's own server-side configuration and state. No value
supplied in a request may change the server-side decisions the console makes for a download, and no
such value may cause the console's stored administration REST credential to be sent to anything
other than the console's own administration endpoint. A request that would do so is answered with a
client error and has no effect.

## Contracts

- A refusal is an ordinary client error (any 4xx response). It is not a crash, a hang, or a server
  error, and it leaves nothing behind.
- Everything that works today keeps working exactly as today.
- The example above is one instance, not the full set of affected requests.

## Constraints

- Fix the underlying problem and its close variants, not only the example.
- Keep every legitimate use working.
- Do not look up the upstream fix for this issue.
- Do not special-case the example values.
