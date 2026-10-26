# Nuclio — project operations are not authorized

## What this is

Nuclio is a serverless platform. Users group functions, function events and API
gateways into projects, and manage the projects themselves through the product's
web API and command-line client. A deployment authorizes project work through an
external policy service: each project action is allowed or denied for the
authenticated caller.

## Observed problem

A caller who has no write rights on a project can still change or remove it. For
example, an authenticated user who may only read project `demo` sends

    PUT /api/projects/demo

with an updated description, and the project is changed even though the policy
service denies that user any write on `demo`. The same is true for removing a
project and for creating one under a name the caller does not own.

## Security property (invariant)

No caller may cause a project to be created, changed or removed unless the
deployment's authorization service allows that action on the project being
written for that caller. The decision and the write must agree on the object:
the authorization decision is made for the very project that the operation
creates, changes or removes, using the identity of the caller who made the
request. The rule holds for every operation the product offers that writes a
project, through every client interface and in every deployment mode, and the
refusal is the product's decision, not an option that a caller can waive. A
refused operation must leave every project exactly as it was: nothing created,
changed or removed.

## Keep working

Everything that works today keeps working exactly as it does today:

- An allowed write still reaches storage unchanged, with the same project
  configuration values (description, owner, labels).
- A request that carries the deployment's configured trusted-role credential
  keeps its current access, even when it carries no user identity of its own.
- A deployment configured without an authorization service keeps accepting
  project writes.

The examples above are examples, not the full set of cases.

## Refusal form

A refused operation returns a client error (a 4xx response code) and has no
side effect.

## Constraints

- Fix the underlying problem and its close variants, not just the example shown.
- Keep every legitimate use working.
- Do not special-case the example values.
- Do not look up the upstream fix for this issue.
