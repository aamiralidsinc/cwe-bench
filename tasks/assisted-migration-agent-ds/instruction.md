# Outbound vCenter connections must be able to validate the server certificate

## The system

This product is an agent that a client drives over HTTP. Part of its job is to
connect to the client's VMware vCenter: it builds an inventory of virtual
machines and datastores, benchmarks storage throughput, inspects individual
VMs, and collects utilisation data for rightsizing. Each of those jobs takes a
vCenter address, a user name and a password from the client, opens an outbound
connection to that address, and does its work over the connection.

Today the agent always opens those connections without checking the vCenter
server's TLS certificate. A client that runs vCenter with its own certificate
authority has no way to ask for an authenticated channel, and no way to hand
over the authority that should be trusted. The agent will therefore complete a
TLS session with whatever host answers on the supplied address, including one
that presents a forged certificate.

## Required property

Wherever the agent accepts vCenter connection details, it also accepts two
optional values:

- `cacert` — a PEM-encoded certificate bundle, supplied as a string;
- `skipTls` — a boolean.

When the connection details say that validation is wanted, the agent must not
complete a TLS session with a server whose certificate does not chain to the
supplied bundle, or, when no bundle is supplied, to the system trust store. The
certificate must also be valid for the host named in the address. This holds
for every operation the agent performs on the client's behalf, whether the
connection details are the request body or are nested inside it, and whether
the operation answers immediately or continues in the background.

The options mean the following:

- `cacert` supplied, with `skipTls` absent or `false`: validate the server
  certificate against that bundle.
- `skipTls` explicitly `false` and no `cacert`: validate against the system
  trust store.
- `skipTls` `true` and no `cacert`: connect without validating the certificate.
- neither value supplied: behave exactly as the product does today.
- `cacert` supplied together with `skipTls` `true`: contradictory; the request
  must fail with a client error before any connection is attempted.
- `cacert` supplied but not a usable PEM certificate bundle: the request must
  fail with a client error before any connection is attempted.

A connection that is refused because the certificate cannot be validated must
not be established at all: no TLS session may complete, and no vCenter work may
be done over it. The request, or the operation it starts, must fail rather than
report success.

For example, a client sends an address, a user name, a password and
`"skipTls": false` for a vCenter whose certificate is self-signed and unknown to
the system trust store. The agent must not complete a TLS session with that
server. This example shows the shape of the problem; it is not the full set of
operations, inputs or certificate conditions that must be handled.

## Keep working

Everything that works today keeps working exactly as it does today, including:

- requests that supply neither value, which continue to connect to self-signed
  vCenter deployments without validating the certificate;
- requests that set `skipTls` to `true`, which continue to connect without
  validating;
- requests that supply a well-formed bundle which did issue the server's
  certificate, which connect successfully;
- the existing request and response shapes of every operation, and their
  normal lifecycle, including the work that continues after an immediate
  response.

## Constraints

- Fix the underlying problem and its close variants, not just the example.
- Keep every legitimate use working.
- Do not consult any upstream fix, advisory or changelog for this project.
- Do not special-case the example inputs.
- There is no network access.
