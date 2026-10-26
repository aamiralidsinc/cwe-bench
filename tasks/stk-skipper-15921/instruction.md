# Policies can be made to allow a request whose body was cut short

Skipper is an HTTP router and reverse proxy. One of its filter families asks an external policy
engine whether a request may reach the upstream. Some routes also hand the request body to the
policy, and the proxy bounds how many body bytes a policy may see: a very large upload is cut at a
configured maximum before it is evaluated.

An operator writes a policy that allows a request only when the body it was shown is the whole
body. A client sends a body larger than that maximum as a streamed upload with no declared length.
The policy is given the leading part of the body, the request is forwarded, and the upstream acts
on the full body although the policy never saw it.

## Requirement

A request whose body was cut at the configured maximum must never be presented to a policy as if
that cut body were the whole body, on every route that evaluates a request body and whichever way
the request carries it.

A body at or below the configured maximum must be presented to the policy as complete, and the
upstream must still receive the whole body after the decision.

A refusal is a client error and has no effect: the upstream is not contacted.

These are invariants, not a list of cases. The example above is an example.

## Behaviour that must not change

Everything that works today keeps working.

## Constraints

Fix the problem and its close variants. Keep legitimate use working. Do not look up the upstream
fix. Do not special-case the example above.
