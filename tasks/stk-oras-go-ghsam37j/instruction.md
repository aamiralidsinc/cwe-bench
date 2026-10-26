# A file store can be made to write outside its working directory

ORAS is a tool and Go library for storing and copying OCI artifacts. Its file-backed content store
keeps everything it is given under one working directory, and it can unpack a layer archive into
that directory when an artifact is copied with unpacking enabled.

An operator copied an artifact from an untrusted registry into a file-backed store with unpacking
enabled. The copy completed, and a file that the artifact described had been created outside the
store's working directory.

## Requirement

No content you give the store may cause it to create, modify, replace or alias a file or a link
outside the store's working directory.

The store's documented option to allow writes outside the working directory keeps its effect for
operators who set it.

A request that the store refuses must fail as an ordinary client error and must leave nothing
outside the working directory.

## Behaviour that must not change

Everything that works today keeps working.

The example above is one example, not the full set.

## Constraints

Fix the problem and its close variants. Keep legitimate use working. Do not look up the upstream
fix. Do not special-case the example above.
