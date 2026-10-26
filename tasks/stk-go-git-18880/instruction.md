# Reference-name containment in the repository storage

This project is a pure-Go implementation of Git. Applications embed it to open, read and change
repositories; the reference names they hand to the library can come from their own input, from
configuration, or from a remote.

## Observed impact

An application stores a reference under a name taken from its input. With a name such as
`refs/../../config`, the write leaves the reference area and replaces the repository's
configuration file. The repository is then corrupt and can no longer be opened normally.

## Security property

Every reference name a caller supplies must stay within the repository's reference storage,
whatever form it takes. It must never create, overwrite, expose or remove anything other than the
reference it names: not the repository's own administrative data (its configuration, packed
references, index, hooks, object store and the like). A name that cannot be confined must be
refused.

## Contracts

- A refused name returns an error and has no effect: nothing is created, changed or removed.
- Everything that works today keeps working exactly as today.
- The examples in this report are examples, not the full set.
- Fix the problem and its close variants. Keep legitimate use working. Do not look up the upstream
  fix. Do not special-case the example.
