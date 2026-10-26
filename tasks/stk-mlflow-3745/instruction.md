# Gateway calls can be pointed at internal addresses

## System

MLflow's AI Gateway lets an operator register provider secrets and route
completion requests through them. A secret carries a provider's credentials
together with configuration describing where that provider is reached; an
endpoint call makes the gateway issue a request to that destination.

## Observed impact

An authenticated user who may create gateway secrets can make the gateway
connect to an address of their choosing inside the deployment or on the host.
For example, registering a secret whose provider address is
`http://127.0.0.1:8080/v1`, creating an endpoint from it, and sending a chat
request to that endpoint causes the gateway to open a connection to the local
service, and the response is relayed back to the caller.

## Security property that must hold

No destination-forming value supplied by a user (an address, host, or any other
value the call's destination is built from), and no such value already stored
for a gateway, may cause an outbound gateway call to reach a destination that is
not publicly routable. A destination reached because of a destination-forming
value a user supplied (an address, host, or any other value the call's
destination is built from), or because of such a value already stored for a
gateway, is refused unless it is publicly routable or the operator has
explicitly enabled internal upstreams; internal, loopback, link-local, and
unspecified destinations are not publicly routable.
The rule holds both when such a value is supplied — the configuration is refused
and the request has no effect — and again when a call is about to connect.

## Contracts the fix must honor

- **Refusal form.** A refused configuration or call is reported to the client as
  a client error and has no effect.
- **Preservation.** Everything that works today keeps working.
- **Opt-in.** An operator may enable internal upstreams; the behaviour described
  here is the behaviour without such an opt-in.
- **Error handling.** A refusal is a normal client error, not a crash, a hang, or
  a server error.

The example above is one instance, not the full set of ways the property can be
violated.

## Constraints

- Fix the flaw and its close variants, not just the request shown.
- Keep every legitimate use working.
- Do not special-case the example input.
- Do not consult any upstream advisory or fix for this issue.
- There is no network access.
