# IP address classification

This project is a library for parsing and inspecting IP addresses. Applications use its
classification checks to decide whether an address is internal or public before connecting to it,
for example an HTTP client that refuses to fetch a URL whose host is not globally reachable.

An application that used the library's checks on the IPv6 address `::ffff:127.0.0.1` was told it
was an ordinary global address, and connected to its own loopback interface.

## Required property

Any check the library offers that classifies an address as internal or public must answer for the
address the value actually reaches. An address that is not globally reachable must never be
reported as an ordinary global or public address.

The IPv6 address type exposes `isPrivate`, which reports whether an address is in a private
range.

## Behaviour that must not change

Everything that works correctly today keeps working exactly as today.

## Constraints

Fix the problem and its close variants. Keep legitimate use working. Do not look up the upstream
fix. Do not special-case the example above.
