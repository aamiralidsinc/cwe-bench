# Any account can take over a deployment's model configuration

## What this is

Cognee is a self-hosted memory service for LLM applications. A deployment is configured once
with the model provider, the model and the credentials it uses, and with the vector database it
stores embeddings in. Those settings are deployment-wide: every request uses them, and the
settings screen reads them back over the HTTP API.

## Observed impact

Any signed-in account can replace the deployment's model configuration. In one reproduction, an
ordinary account's token was used to send `POST /api/v1/settings` with a different provider,
model and key; the write succeeded, and from then on every request in the deployment used the
attacker-chosen values instead of the operator's.

## Security properties

1. The deployment-wide model and vector-database configuration is operator-owned. Only a caller
   the deployment treats as privileged may change it, and a refused change leaves the
   configuration exactly as it was.

2. The settings surface never discloses a stored credential, in whole or in part, and it always
   answers with the deployment's current configuration.

3. Anonymous callers are not given accounts on a deployment that requires authentication. An
   operator may open public sign-up; the behaviour above is the behaviour without that choice.

## Contracts

- A refused request answers with a client error (any 4xx) and has no effect.
- Everything that works today keeps working exactly as today: a deployment that runs without
  per-user access control keeps its single-operator workflow, and ordinary users keep the
  settings view they use.
- Nothing else about the deployment's settings behaviour changes.

The example above is one instance, not the full set of ways the properties can be violated.

## Constraints

- Fix the problem and its close variants, not just the request shown.
- Keep every legitimate use working.
- Do not look up the upstream advisory or fix for this issue.
- Do not special-case the example.
- There is no network access.
