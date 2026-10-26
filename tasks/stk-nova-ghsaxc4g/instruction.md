# Files written for a new server can land outside its disk image

## System

Nova is the compute service of OpenStack. When it creates a server, it writes
material into that server's disk image while the image is mounted on the
compute host. Those writes are performed with host administrator privilege.

## Observed impact

A user can make the compute service create or change a file on the compute
host, outside their own instance image. For example, creating a server through
the Compute API with a personality entry whose path walks upward

```
personality: [{"path": "/../../../../tmp/nova-demo", "contents": "<base64>"}]
```

makes the service write `/tmp/nova-demo` on the host instead of a file inside
the instance image.

## Security property

No request may create, remove or change anything on the compute host outside
the instance's own disk image.

## Contracts the fix must honor

- **Refusal.** A request that would leave the image fails with an error rather
  than succeeding, and the failed request leaves nothing outside the image
  created, removed or changed.
- **Preservation.** Everything that already works keeps working exactly as
  today.

The example above is one instance, not the full set of ways the property can
be violated.

## Constraints

- Fix the flaw and its close variants, not just the request shown.
- Keep every legitimate use working.
- Do not special-case the example input.
- Do not consult any upstream advisory or fix for this issue.
- There is no network access.
