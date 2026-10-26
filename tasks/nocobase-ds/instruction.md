# Uploads and plugins can reach files outside the areas the server manages

NocoBase is an extensible no-code platform. Administrators choose where uploaded files are stored
(a folder on the local disk, an S3 bucket, and so on) and which plugins the server loads and runs.
The server receives both kinds of setting from clients.

## What we observed

An account that can change storage settings was able to make the next attachment upload put its
file in a directory outside the storage area the server is meant to use.

## Required behaviour

No value a client supplies may cause the server to create, overwrite, read, delete or load any
filesystem object outside the locations the server manages for that purpose: files written for a
storage stay inside that storage's configured root, and a plugin is selected only by the name of an
installed plugin package. This holds for every value that ends up designating such a location,
including one stored in a record now and used later, and nothing outside those locations may be
created or changed even when a request is refused.

## Contracts

- A request that would place data outside those locations fails, and when the server rejects it it
  leaves no file, directory or record outside the managed locations.
- Nothing that works today may stop working. In particular, a storage root that an operator
  configures as an absolute directory outside the application directory (for example a mounted
  volume) must keep accepting uploads; ordinary storage sub-paths keep resolving as they do today;
  a change that leaves the root alone keeps working; installed plugins can still be enabled and
  disabled by name; and installing a plugin from an uploaded archive is unaffected.
- The examples above are examples, not the complete set. The same rules apply to every equivalent
  operation, including ones not mentioned here.

## Constraints

- Fix the problem and its close variants; keep legitimate use working.
- Do not look up the upstream fix.
- Do not special-case the examples.
