# Gitea

Gitea is a self-hosted Git service. People keep repositories there and attach issues, releases
and other work to them. A release can stay unpublished as a draft while its contents are still
being prepared. A file attached to a release is served from a download address.

## Impact

Material that has not been published yet is readable by people who are not allowed to see it. For
example, a visitor with no account, or an account that can only read a public repository, opened
the download address of a file attached to a draft release of that repository and received the
file.

## Security property

Work that has not been published stays closed. It may not be obtained, and nothing about it may
be learned, by anyone who is not entitled to prepare it or to publish it.

Nothing that belongs to one repository becomes visible through another: permission held in one
repository is not permission over material owned by a different one.

## Contracts

- A refused request answers with a client error (any 4xx) and changes nothing: no protected
  material or information, and no altered state.
- Everything that works today keeps working exactly as today.

These rules hold generally, not only for the example above. Fix the problem and its close
variants, keep all legitimate use working, do not look up the upstream fix, and do not
special-case the example.
