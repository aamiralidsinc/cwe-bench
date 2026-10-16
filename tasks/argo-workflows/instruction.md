# Security review: workflow-engine API server and execution path

We exercised a running instance of this Kubernetes-native workflow engine with an
authenticated but low-privilege client, and separately drove its workflow-execution
logic, and found several ways a caller can exceed the permissions they were granted
or degrade the service. Please treat the server's gRPC/HTTP API surface and the
workflow-execution path as the entry points; each symptom below was reproduced
through one of them.

## Reading templates the caller is not allowed to read
A user whose Kubernetes RBAC does not grant read access to workflow templates can
still retrieve the full body of a namespaced workflow template — and likewise of a
cluster-scoped template — simply by calling the corresponding "get template" API.
The server hands back the object even though an access review for that caller would
deny it. Fetching a template must be refused for a caller the cluster would not
authorize, while a caller who is authorized must still receive the template.

## Editing synchronization limits the caller is not allowed to touch
The synchronization-limit API lets a caller create, read, update, and delete the
cluster objects that hold semaphore/concurrency limits in an arbitrary namespace,
without ever checking whether the caller is permitted to modify configuration in
that namespace. A tenant with no rights in another namespace can nonetheless read
or rewrite that namespace's concurrency limits. Each of these operations must be
gated by the caller's permission in the target namespace; an authorized caller must
still be able to manage limits normally.

## Repository credentials disclosed through logs
Whenever the system loads, saves, streams, lists, or deletes an artifact, it writes
a description of the configured artifact backend to the log. That description
contains the backend's access credentials — access keys, passwords, and tokens — so
anyone able to read the logs obtains the repository secrets. Artifact handling must
keep working, but credentials must never be emitted to the log stream.

## Unauthenticated oversized request exhausts memory
The event/webhook entry point accepts unauthenticated POST requests and buffers the
entire request body into memory before it verifies any signature. A single very
large body therefore forces a correspondingly large allocation, giving an
unauthenticated client an easy way to exhaust the server's memory. An over-large
body must be refused up front, while normally sized, correctly signed webhook
requests must still be processed as before.

## Overriding a referenced template's protections
When the engine is configured so that submitted workflows must reference a reusable
template (a "template referencing" restriction intended to lock down what submitters
may run), a submitter can still set pod-level fields directly on the referencing
workflow — for instance host networking, a pod security context, or the service
account identity — and those values take effect, overriding the protections the
referenced template was meant to enforce. Under this restriction such a submission
must be rejected, while a legitimate referencing workflow that overrides nothing
must still run.

## Required outcome
Change the code so that every behaviour above is corrected, through the same entry
points, without breaking legitimate authorized use of any of these features. A
caller must never obtain data or effects beyond what their permissions allow, secrets
must stay out of the logs, and the service must not be trivially exhausted by an
unauthenticated request.
