# A low-privilege user can make the server act with its stored cloud access

## System

This project is a plugin for a self-hostable automation server. It grows and
shrinks the server's pool of build agents by backing them with elastic compute
instances from a cloud provider. An administrator configures one or more clouds
through the server's web UI, naming a stored cloud credential that the plugin may
use to contact that provider on the server's behalf.

## Observed impact

A user who holds only basic read access to the server can make it perform
provider-facing work with a stored credential, although that user is not allowed
to administer the server. The same work can also be driven by a request that is
not a genuine state-changing submission at all, so a safe, side-effect-free
request from an administrator's browser is enough. The caller can additionally
influence which host receives the credential-bearing call.

## Security property

No request may cause the server to use a stored cloud credential to act with the
provider unless the requester is allowed to administer the server and the request
is a genuine state-changing submission; and no caller-supplied value may cause
such a credential-bearing call to be sent to a host outside the provider's own
domains.

## Contracts the fix must honour

- **Refusal form.** When a request is not entitled to act, or is not a proper
  submission, the server must perform no side effect and must answer with a
  client error. When a request carries a value the server must not act on, it may
  instead answer with an empty result or a validation error. In every case the
  stored credential is never used to reach a host outside the provider's own
  domains. No particular status code or message is required.
- **Preservation.** Administrators' proper submissions must keep working exactly
  as today with every legitimate provider input the product accepts: a blank
  host value that leaves the host to be derived from an ordinary region name,
  the provider's alternate domains, surrounding-whitespace and mixed-case
  variants, a host given without a URL scheme, and the standard, government and
  isolated region names. A caller who holds the specific right to remove one
  managed item, but not server-wide administration, must still be able to remove
  that item through a proper submission.
- **Magnitudes.** A legitimate submission uses an ordinary provider region and
  either a blank host value or a genuine provider host; an attack carries a value
  outside the provider's own domains, or is not a genuine submission. Both travel
  the same request-handling code.

The examples above are illustrations, not the full set of operations or request
shapes through which these properties can be violated.

## Constraints

- Fix the flaw and its close variants, not just the exact request shown.
- Keep every legitimate use working.
- Do not modify or add tests, and do not special-case the example input.
- Do not consult any upstream advisory or fix for this issue.
