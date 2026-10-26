# A pinned CA is not bound to the host the client connects to

This project is a proxy platform. It opens outbound connections to servers, and those connections
can use TLS. Instead of trusting the system roots, an operator can pin a certificate by its
SHA-256 hash (`pinnedPeerCertSha256`). Pinning the server's own certificate is a direct identity
check. Pinning the certificate of a CA is meant to mean "a leaf issued by this CA, for the host I
am connecting to".

## Observed impact

An outbound speaks the gRPC transport over TLS to a server addressed by IP. Its TLS settings pin
the CA and do not set a `serverName`. The server presents a certificate issued by that CA but
valid for a domain it does not serve. The connection is established and traffic flows: whoever
holds any certificate from the pinned CA, for example one for a domain they control, can stand in
for the configured server.

## What must never happen

A client that pins a CA must only accept a certificate that is valid for the host it is connecting
to. A certificate issued by the pinned CA for any other host must be refused, no matter which
client opens the connection, which transport or subsystem it belongs to, or how the pinning
settings are supplied. When the client has no host it can check the certificate against, it must
refuse the connection instead of accepting it. Pinning a leaf certificate is a direct identity
check and is not subject to a host check.

The example above is an example, not the complete set.

## What must keep working

- A connection that pins a CA and whose certificate is valid for the host being dialed keeps
  connecting, exactly as today, on every transport and in every subsystem that opens TLS
  connections.
- A configured `serverName` keeps being the expected host and the TLS server name.
- A configured list of acceptable certificate names keeps working together with a pinned CA.
- Pinning a leaf certificate keeps working, including when no server name is configured.
- Every other legitimate behaviour stays exactly as it is today.

## Constraints

Fix the problem and its close variants. Do not special-case the example. Keep legitimate use
working. Do not look up the upstream advisory or its fix.
