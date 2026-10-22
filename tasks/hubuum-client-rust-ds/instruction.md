# Sensitive values appear in the client's default diagnostics

This repository is a client library that applications use to call a remote server. Applications embed the library and routinely write the values and errors it returns into their own logs and error trackers.

Values the library hands back can carry content supplied by the server or secrets supplied by the caller. The library also provides the standard diagnostic representations for those values: `Display`, `Debug`, and the `std::error::Error::source` chain.

**Observed impact.** An application that logs a returned value or a failed call with `{}` or `{:?}` writes that content into its log, where operators and log-shipping systems can read data the application never intended to disclose.

## Required invariant

No server-supplied content and no caller-supplied secret may appear in the default `Display` or `Debug` representation of any error or result value the library returns, or anywhere reachable through the standard `std::error::Error::source` chain. This holds for every shape the library returns, including nested values, optional and required fields, containers, and values embedded in larger structures.

## Contracts the tests rely on

- The same data must remain available unchanged through the documented public fields and explicit accessors, and serialization and deserialization must not change.
- Diagnostics must stay useful: identifiers, names, statuses, kinds, timestamps and counts that are not sensitive continue to be shown.
- Error handling must keep working: failures still return errors, retries still retry, and successful calls still succeed.

## Constraints

Fix the problem and its close variants. Keep legitimate use working. Do not modify or add tests. Do not look up the upstream fix. Do not special-case any example.
