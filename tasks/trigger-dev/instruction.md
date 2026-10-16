# Security review: background-jobs platform API

You are given the source of a self-hostable background-jobs platform whose
Remix/Express web application exposes an HTTP API (dashboard routes, a
versioned `/api/v1` surface, and a realtime surface). A security review of a
running instance surfaced the behaviours below. Each is reachable by an
ordinary client talking to the running server. Fix the underlying authorization
and input-handling problems so the attacks no longer work, while keeping the
legitimate features fully usable.

## Observed behaviours

**Outbound requests to internal addresses via alert webhooks.** A project can
register a webhook destination that the platform calls (a signed POST) whenever
an alert fires. The destination URL is accepted and stored with no restriction
on where it points. A tenant can register a destination aimed at the server's
own network — loopback services, the cloud instance-metadata endpoint, or
private/link-local ranges — and the multi-tenant control plane will then issue
requests to infrastructure it should never reach. Legitimate destinations on
ordinary public hosts must still be accepted.

**Cross-environment cancellation of deployments.** A project is split into
isolated environments (for example development, staging and production), each
with its own API key and a different level of trust. An in-progress deployment
belonging to one environment can be canceled using an API key issued for a
*different* environment of the same project. A low-trust development key can
therefore abort another environment's production deployment. Canceling a
deployment with a key belonging to that same environment must keep working.

**Unauthenticated writes into a run's realtime stream.** Each run has a
realtime data stream. Data can be written into a run's stream over HTTP with no
credentials at all; the run is addressed only by its identifier, and those
identifiers are short and predictable. An outsider who guesses or learns a run
identifier can inject arbitrary content into that run's live stream, including
for production runs. Authenticated, correctly scoped access to stream data must
continue to function.

**Unauthenticated driving of batch completion.** A dashboard endpoint that
advances a batch's completion/resume state can be invoked with no logged-in
session and with no check that the caller belongs to the batch's owning
organization. An anonymous request can drive processing of batches that belong
to other tenants. A logged-in member must still be able to use this endpoint
for their own batches.

## What must hold afterwards

- A stored alert-webhook destination that resolves to an internal / loopback /
  link-local / private address is refused; ordinary public destinations are
  accepted.
- A deployment can only be canceled by a credential scoped to that deployment's
  own environment.
- Writing into a run's realtime stream requires proper authorization; the
  anonymous write path must not exist.
- The batch-completion endpoint requires an authenticated caller who belongs to
  the owning organization.
- All of the legitimate flows above (creating normal alert channels, same
  environment deployment cancels, initializing deployments, authenticated
  realtime and batch use) continue to work.

The server is driven over HTTP exactly as a client would; a local Postgres and
Redis back it and no external services are involved.
