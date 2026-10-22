# Tenants can obtain node-level privileges through Fission Environments and Functions

Fission is a serverless framework for Kubernetes. Tenants describe their runtimes as `Environment` objects and their code as `Function` objects. The platform's own controllers then create the pods that build and run that code, using the platform's service accounts. Tenants may customise those pods, for example with resource limits, extra containers, volumes or node placement. They are not cluster administrators, though, and the platform is supposed to keep them inside an ordinary, unprivileged pod.

## Observed impact

A tenant who is allowed to create Environments in their own namespace can apply something like:

```yaml
apiVersion: fission.io/v1
kind: Environment
metadata: {name: py, namespace: tenant-a}
spec:
  version: 2
  runtime:
    image: fission/python-env:latest
    podspec:
      hostPID: true
```

The object is accepted. The platform then schedules the environment's pods in the node's PID namespace, where they can see and signal every process on the node. Other settings in the same family get through as well, and they give the tenant node or cluster access the platform never granted.

## Required behaviour

No Environment or Function object written by a tenant may cause any pod that the platform creates on the tenant's behalf to:

- share the node's network, PID or IPC namespace;
- run a privileged container, or a container that allows privilege escalation;
- add a Linux capability that grants administrative or cross-process power (for example `SYS_ADMIN`, `NET_ADMIN`, `SYS_PTRACE`, `SYS_MODULE`);
- mount a path from the node's filesystem;
- run under a service account other than the one the platform assigns.

This covers every part of these objects that shapes the resulting pods, and it applies both when an object is created and on any later update or patch. Admission must refuse such an object with a validation error, and nothing may be stored or deployed. Objects that are already stored in the cluster, such as objects created before an upgrade or while admission was unavailable, must never yield such pods either. The platform may decline to deploy them, or deploy them without the forbidden settings, but no component may crash.

The examples above are illustrations, not the full set.

## Must keep working exactly as today

- All other pod customisation: resources, environment variables, extra unprivileged containers and init containers, ConfigMap/Secret/emptyDir volumes, node selectors, tolerations and affinity.
- Security hardening that tenants set at pod or container level, such as `runAsNonRoot`, `runAsUser`, `fsGroup`, seccomp profiles, a read-only root filesystem, dropping capabilities, or explicitly setting `privileged`/`allowPrivilegeEscalation` to `false`.
- Adding capabilities from the container runtime's default set, such as `NET_BIND_SERVICE` or `CHOWN`.
- The cluster operator's install-time pod-spec patches for runtime and builder pods, including their pod-level security context.
- The project's existing test suite.

## Constraints

- Fix the problem and its close variants, not only the example above.
- Keep legitimate use working.
- Do not modify or add tests.
- Do not look up the upstream fix.
- Do not special-case the example.
