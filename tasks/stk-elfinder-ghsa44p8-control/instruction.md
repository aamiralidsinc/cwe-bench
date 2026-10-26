# Web file manager: a request can reach past the browsed folder

The project is a web file manager. A deployment runs a connector script that exposes one or more storage roots over an HTTP API. The project root contains a ready-to-run sample deployment that serves its storage folder; `php -S 127.0.0.1:8080 -t .` starts it, and its HTTP endpoint is the sample connector.

## Observed impact

A request can make the server act on a location that is not under the folder the user is browsing. In one reproduction, an archive download whose file name was supplied by the client returned the contents of a file kept outside the server's scratch area, and that file was gone after the request finished.

## Required properties

1. A client-supplied value is judged by the location it names: it may not name a location outside the storage root the client is attached to.
2. The server's scratch area is not client storage: no client-supplied value may cause the server to hand out or delete anything the server did not itself put there.

The fix belongs in the application's own code, not in one deployment's configuration.

## Contracts

- A request that would break either property is not carried out: it has no such effect, and it is reported through the API's usual error or warning. A crash or a 5xx is not a refusal.
- Everything that works today keeps working exactly as today.

## Constraints

- Fix the problem and its close variants.
- Keep legitimate use working; do not disable features to make the problem go away.
- Do not look up the upstream fix.
- Do not special-case the example.
