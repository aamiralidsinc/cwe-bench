# A low-privilege user can make the server use stored cloud credentials

## System

This project is a plugin for a self-hostable automation ("CI/CD") server. It lets
the server grow and shrink its pool of build agents automatically by backing them
with a cloud provider's elastic compute fleet. An administrator configures one or
more *clouds* through the server's web UI: they pick a **stored cloud credential**,
a **region**, an optional **endpoint**, and a fleet to draw instances from.

The plugin exposes a number of background helper endpoints and operations that
use a stored credential to contact the provider on the server's behalf. Many of
them take a credential reference plus a region and/or endpoint **from the
incoming request**.

## Observed impact

A user who only has basic read access to the automation server — not the right to
administer it — can call one of these helper endpoints directly (for example, with
a simple GET that carries a credential reference and a region) and the server will
go ahead and use the stored credential to talk to the cloud provider for them. The
same operations can also be driven by a request that was not a genuine form
submission at all (a side-effect-free, cross-site request), so merely luring an
administrator's browser is enough to trigger them. Because the region and endpoint
come from the request, the caller can also steer which host the server contacts
while holding that credential.

## Security properties that must hold

- No request may cause the server to use a stored cloud credential to contact the
  cloud provider unless the requester has the right to administer the server
  **and** the request is a genuine state-changing submission rather than a safe,
  side-effect-free one. This holds for every such operation the plugin exposes,
  whatever it returns.
- No value of the caller-supplied region or endpoint may cause a credential-bearing
  call to be directed at a host that is not one of the cloud provider's own
  endpoints. A request must not be able to point the server (while it holds the
  credential) at an attacker-chosen host.

## Contracts the fix must honor

- **Refusal form.** When a request is not entitled to an operation, or is not a
  proper submission, or names a region/endpoint that is not the provider's, the
  server must simply not perform it: respond with a client error (or, for a bad
  region/endpoint, an empty result or validation error) and cause no side effect —
  in particular the stored credential is never used. No specific status code or
  message is required.
- **Preservation.** Administrators must still use these operations, through a
  proper submission, with every real provider input: a blank endpoint (the host is
  then derived from the region), the provider's alternate (e.g. China) domains,
  values with surrounding whitespace or mixed case, a host given without a URL
  scheme, and the standard, government and isolated region names. Deriving a provider endpoint from an ordinary region name
  must behave exactly as today.
- **Magnitudes.** A legitimate call names, say, region `us-east-1` with a blank or
  genuine provider endpoint; the attack names a credential and a region/endpoint it
  should not be allowed to drive, or arrives as a bare GET. Both travel the same
  request-handling code.

The examples above are illustrations, not the full set of operations or request
shapes through which these properties can be violated.

## Constraints

- Fix the flaw and its close variants, not just the exact request shown.
- Keep every legitimate use working.
- Do not modify or add tests, and do not special-case the example input.
- Do not consult any upstream advisory or fix for this issue.
