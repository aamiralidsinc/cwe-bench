# Tenant-supplied configuration can give platform pods node-level privileges

## The system

This project is a Kubernetes serverless platform. Tenants declare how their code is built and run by
writing objects into their own namespaces. The platform's own controllers then create the pods that
build and execute that code, under service accounts the platform chooses. Tenants may shape those
pods in ordinary ways — resource limits, environment variables, additional containers, volumes,
scheduling. They are not cluster administrators, and nothing they declare may give a pod more power
than an ordinary unprivileged workload.

## Observed impact

A tenant who can write such an object — not an administrator — includes a pod-level setting in it,
and the platform accepts the object and creates pods that carry the setting. For example, a
declaration can ask for the pod to join the node's process-ID namespace; the resulting pod can then
see and signal every process on the node. The tenant never gained administrator rights, but the pods
the platform created on the tenant's behalf did.

## Security property

No value a tenant supplies in an object they are allowed to write may cause any pod the platform
creates on that tenant's behalf to:

- share the node's network, process-ID or IPC namespace;
- run a privileged container, or a container that permits privilege escalation;
- add an operating-system capability that grants administrative or cross-process power, including a
  grant of all capabilities;
- mount a path from the node's filesystem;
- run under a service account other than one the platform assigned.

The property holds however the value is expressed, wherever it appears in the object, and whatever
metadata accompanies it. The object cannot waive it. It applies in every namespace and to every
such object, whatever its name, labels or annotations; and to every pod the platform creates,
whenever it creates it.

The settings above are examples of the protected boundary, not the full set.

## Contracts the fix must honour

- **Refusal form.** A request that would store a value that violates the property must fail with a
  client error and leave nothing stored or deployed. No particular status code or message is
  required. When the platform instead meets such a value while creating a pod, it may decline to
  create it or create it without the forbidden settings; it must not crash.

## Keep working exactly as today

- Ordinary pod customisation: resource limits and requests, environment variables, additional
  ordinary and init containers, non-host volumes, image pull secrets, node selection, tolerations,
  affinity, and runtime class.
- Tenant-imposed hardening: restricting the user or group, a read-only root filesystem, seccomp
  profiles, dropping capabilities, explicitly setting `privileged` or `allowPrivilegeEscalation` to
  `false`, and adding capabilities that do not grant administrative or cross-process power.
- Customisation the cluster operator installs at deployment time, including pod-level security
  context and scheduling, still reaches every platform pod.
- Tenant customisation supplied in any supported form, when it carries only ordinary values, is
  still accepted and applied.
- Ordinary labels and annotations must not block acceptance; an object with ordinary metadata is
  treated like any other.
- The project's existing behaviour for the affected area.

## Constraints

- Fix the problem and its close variants, not only the example above.
- Keep every legitimate use working.
- Do not look up the upstream fix.
- There is no network access.
- Do not special-case the example.
