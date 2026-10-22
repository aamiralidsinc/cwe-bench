# Scaffolder steps can act with the backend's privileged SCM credential

Backstage is a developer portal. Software templates run a sequence of scaffolder
steps. Some steps act on source-control content on behalf of the person running
the template: they accept a credential supplied by that person and, when it is
absent, fall back to the credential configured for the Backstage instance.

## Observed impact

An organisation configured its source-control integrations with a privileged
service credential. A user ran a template and supplied no personal credential;
a source-control operation then ran as the instance's integration identity,
which that user cannot use directly.

## Required behaviour

Add an opt-in instance setting `scaffolder.requireScmUserCredentials` (boolean,
default false). While it is enabled, no supported scaffolder step may perform
any source-control operation, however its target is expressed or referenced,
using the instance's configured integration credential. A step may proceed only
with a non-empty credential supplied through its own step input. Without one it
must fail with a client error before making any source-control request and
without constructing a client for the target host.

The same applies to an operation that inherently requires the instance's own
identity: it must be refused with a client error even when the user supplied a
credential.

An empty-string credential is treated as no credential.

Integrations that have no concept of a per-user credential keep their existing
behaviour, including their use of a configured integration credential.
An integration has a concept of a per-user credential when the product can read
its content using a credential supplied by the person running the template. An
integration whose content the product can only ever read with the configured
integration credential has no such concept: every operation on it keeps its
existing behaviour. The refusal above for operations that inherently require the
instance's own identity applies only within integrations that do have a
per-user credential.
Everything that is not a source-control operation keeps working without a user
credential.

Enabling the setting in the instance configuration must be sufficient at
startup; no per-step option may be required from the template author.

While the setting is absent or false, behaviour must be exactly as today: the
integration-credential fallback remains available to every step, and every step
keeps working as it does now.

## Contracts used by the checks

- Configuration key: `scaffolder.requireScmUserCredentials`.
- Where a step accepts a user credential, that input is named `token`; a step
  that already documents a different credential field keeps that name.
- The affected action factories accept an optional boolean option named
  `requireScmUserCredentials`; when it is true the mode is enforced, and when
  it is false or absent nothing changes.
- A refusal is a client error — the framework's `InputError`, not a crash.

## Notes

- Apply the rule to every supported step that can act on source-control
  content.
- Fix the problem and its close variants. Keep legitimate use working. Do not
  look up the upstream fix or an existing implementation. Do not special-case
  the examples.
- There is no network access.
