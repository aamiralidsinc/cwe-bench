# Namespaced policies can read data outside their namespace

Kyverno is a Kubernetes policy engine. While evaluating policies, it resolves the external data a
policy declares for its rules, and it resolves that data with its own cluster identity, not with the
identity of the person who wrote the policy.

A user who may create a policy in their own namespace can write one whose declared context pulls in
an object from another namespace, for example a Secret. When the policy is evaluated, the other
namespace's value becomes part of the rule context and is surfaced through the rule result, although
the user has no access to that namespace.

## Requirement

No policy that belongs to a namespace may read, or otherwise affect, data that belongs to another
namespace or that is cluster-scoped.

Kyverno's own cluster identity must never be used on behalf of a policy that belongs to a namespace
to reach anything outside that policy's namespace.

A refusal is a client error and has no effect.

These are invariants, not a list of cases. The example above is an example.

## Behaviour that must not change

Everything that works today keeps working.

## Constraints

Fix the problem and its close variants. Keep legitimate use working. Do not look up the upstream fix.
Do not special-case the example above.
