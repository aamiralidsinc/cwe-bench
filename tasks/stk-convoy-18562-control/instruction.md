# Cross-project access to webhook sources

Convoy is a webhook delivery service. Every project owns its webhook sources. A source holds
the material used to authenticate and sign incoming deliveries, such as an HMAC secret, an API
key or a basic-auth password. Project members manage the sources of the projects they are
authorized on.

## Observed impact

A user authorized on one project can retrieve a source owned by a different project by using
the other project's path together with that source's identifier. The response returns the
source record, including the credentials it uses to authenticate deliveries.

## Security property

A source belongs to exactly one project, and only callers authorized on that project may act
on it. A source from a different project must be treated exactly as if it did not exist: no
source data is ever exposed, and no change is ever persisted.

## Contract

- A refused request is a client error (4xx) and leaves no partial or persisted effect.
- Everything that works today keeps working exactly as today.
- The example above is one example, not the full set.

## Constraints

Fix the problem and its close variants without changing the product's public behaviour beyond
the property above. Do not special-case the example. Do not look up the upstream fix; work
from this report and the code.
