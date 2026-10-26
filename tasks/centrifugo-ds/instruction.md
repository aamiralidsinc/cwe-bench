# Stop client-emulated headers from filling trusted proxy headers

## The system

This project is a real-time messaging server. Clients open a connection over a
transport (for example WebSocket, an HTTP streaming connection, Server-Sent
Events, or gRPC) and then send commands: subscribe to a channel, publish, call an
RPC, refresh the connection. The server can be configured to forward these events
to an application backend ("a proxy") and use the backend's answer.

Some transports cannot set real request headers, so a client may send a map of
headers with its connect request; client SDKs expose this as a headers option.
Operators configure, for each proxy, which header names are forwarded to the
backend, and may also configure static headers and static metadata.

## Observed problem

A client connects with the header-emulation option and supplies a value for a
header name that the proxy configuration lists as a transport header -- for
example an identity or forwarding header the operator expects its own edge to
set. The proxy backend receives the client's value under that name, as if the
transport or the infrastructure in front of the server had set it.

## Security property (invariant)

For every proxy request the server sends to an application backend, a value the
client supplied through header emulation may be forwarded under a name only if
that proxy configuration explicitly designates the name for client-supplied
values. Such a value must never reach the backend under a name the configuration
reserves for transport-supplied headers or transport metadata, however the value
is carried inside the server. When a name is designated for both sources and
both supply a value, the proxy request must carry only the transport-supplied
value under that name; the client value is used only when no transport value is
present.

## Configuration contract

- A proxy configuration accepts a list named `emulated_headers`, at the same
  level as `http_headers` and `grpc_metadata`, naming header names that may be
  sourced from the client's emulated map. It applies to every kind of proxy and
  to every proxy backend protocol.
- `http_headers` and `grpc_metadata` name transport-supplied values only. They
  must never be satisfied from the client's emulated map.
- A client is not refused for supplying an emulated value: the proxy call
  proceeds normally, with that value simply not forwarded under a reserved name.
- An emulated value the configuration does not designate is not forwarded.

## Keep working

Everything that works today keeps working exactly as today. In particular:

- an allowed transport header is still forwarded, and still overrides a static
  header with the same name;
- static headers are still applied when no allowed transport header names them;
- a name listed both as a transport name and for client-supplied values is still
  forwarded from the client's emulated map when the transport supplied no value
  for it, and the transport value still wins when it did;
- allowed transport metadata and static metadata are still forwarded;
- ordinary client connects through a proxy still succeed and carry the
  backend's answer.

A client may send any number of emulated headers the configuration designates,
and they are forwarded; a single client-supplied value for a name the operator
reserves for transport data is the case that must not be forwarded. For example,
an authorization token that browsers send through emulation and native clients
send as a real transport header is an ordinary dual-source name; a client
inventing a value for a forwarding or identity header reserved for infrastructure
is the case that must not pass. These are examples, not the full set of inputs.

## Constraints

- Fix the problem and its close variants everywhere the server forwards client
  data to a proxy backend.
- Keep legitimate use working; do not break the header-emulation feature.
- Do not look up the upstream fix or advisory.
- Do not special-case the example.
