# A caller can choose where the gateway reads a stored file

TensorZero is a gateway and SDK for LLM applications. Requests can carry stored files
(images, PDFs, audio) and can refer to files the gateway stored earlier; the gateway
keeps these files in the object store named by its `[object_storage]` configuration,
either a local directory or an S3-compatible bucket.

**Observed impact.** A caller sends an object-storage read request with a storage
location of their own choosing instead of an object key — for example a filesystem
location that points outside the configured directory:

```
GET /internal/object_storage?storage_path={"kind":{"type":"filesystem","path":"/etc"},"path":"passwd"}
```

The gateway returns the contents of that file. Changing the location to an
S3-compatible bucket and endpoint of the caller's choosing makes the gateway issue
requests to a host the caller controls.

## Required invariant

No value supplied by a caller may make the product read file bytes from any location
other than the object store the gateway itself is configured to use. This holds for
every interface, request field, input form and processing stage, including values that
were stored earlier and are resolved later. A request that would cause such a read must
end in an error the caller can see, and no bytes from outside the configured store — and
no value computed from those bytes — may be returned, stored or logged.

## Contracts

- Refusals are ordinary errors: an HTTP error response or an error result, with no
  object data and no side effects.
- Objects that live inside the configured store stay readable by their key: the same
  bytes come back through every interface that returns object data today, and requests
  that reference stored files keep succeeding.
- Keys may contain ordinary text and `/` separators; only locations that leave the
  configured store are refused.
- The example above is one example, not the full set.

## Constraints

Fix the problem and its close variants. Keep legitimate use working. Keep the project
building the way its own automated checks build it, including optional features. Do not
modify or add tests. Do not look up the upstream fix. Do not special-case the example.
