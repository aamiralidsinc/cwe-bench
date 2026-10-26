# mistral.rs server: server-local file read through a request image source

mistral.rs is an inference server that serves model requests over HTTP. A chat-completions request's
image part may name a location from which the server should load the image, and the server fetches or
reads that location on the request's behalf.

## Observed impact

A chat-completions request whose image part carries a `file:` URL for a path on the server machine
comes back with that path's content accepted as the image, so a client of the API can read files that
the server process can read.

## Security invariant

No value supplied in a request may make the server read data from its own filesystem, or reach an
address that is not publicly routable: not its own machine, not its loopback interface, and not a
private or link-local network.

## Contracts

- Refusal: a request that would break the invariant is refused with a client error and has no effect;
  nothing it names is read, fetched, or used before the refusal.
- Everything that works today keeps working exactly as today.

## Constraints

Fix the problem and its close variants. Do not look up the upstream fix. Do not special-case the
example.
