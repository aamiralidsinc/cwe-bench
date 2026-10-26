# Namespace-scoped requests reach into other namespaces

## The system

This project provides a long-term memory store for agent applications. An item is a value stored
under a key inside a namespace: a hierarchical name built from one or more labels. Applications
name their data by namespace and then work with it through a scope — the exact namespace, a
prefix, a suffix, or a match path — and teams commonly give every customer its own branch of the
namespace tree, relying on the store to keep a scoped request inside that branch.

## Observed problem

An application keeps one entry per customer. It stores an item under the namespace `("acme",)`
and another customer's item under `("acme-evil",)`. A read scoped to the prefix `("acme",)`
returns both items: the second one belongs to a different branch of the tree and was never in
scope. One customer's data is therefore reachable through an ordinary scoped request.

## Security properties that must hold

- A request that takes a namespace scope may act only on items whose namespaces lie inside that
  scope, and membership is decided label by label:
  - a prefix covers exactly the namespaces that begin with those labels, at any depth;
  - a suffix covers exactly the namespaces that end with those labels;
  - a `*` in a match path stands for exactly one label;
  - an exact namespace covers only itself.
- No item stored under a namespace outside the scope may be returned, revealed, changed or
  removed by such a request — whatever database an application has configured, whichever entry
  point performs it, and however the requested scope or the stored names are spelled.
- A scope that cannot name a valid namespace must be refused rather than matched against some
  other namespace.

## Contracts the fix must keep

- **Refusal.** When a request cannot be satisfied inside its scope, it fails as a client error
  (an exception or an error result) and leaves every item outside the scope untouched. A
  successful-looking result that carries out-of-scope data is never acceptable.
- **Names are exact.** A namespace label is a non-empty string that does not contain a period.
  Names are compared exactly: two namespaces that differ in any label, including letter case,
  are different namespaces. Labels may contain punctuation such as underscores or percent
  signs; punctuation is part of the name and never a wildcard.
- **Preservation.** Everything that works today keeps working exactly as today: an exact
  namespace still matches itself, a prefix stays open-ended at any depth, and every in-scope
  request still returns, lists or affects exactly the items it does today, including when a
  whole namespace subtree is handled in one request.

The example above is one instance, not the full set of ways the property can be violated.

## Constraints

- Fix the flaw and its close variants, not just the request shown.
- Keep every legitimate use working.
- Do not special-case the example input.
- Do not consult any upstream advisory or fix for this issue.
- There is no network access.
