# A node operations job can run commands on an edge node

KubeEdge lets an operator manage edge nodes from the cloud by submitting operations jobs. A job
selects the nodes it applies to and carries the values the edge needs to carry it out — for a node
upgrade, the version to move to and an optional installation image. The edge agent receives the job
and runs the matching tool on the node.

## What happens

A user who can submit a node upgrade job can put shell syntax into a value the job carries. When the
node acts on the job, the shell interprets that text instead of passing it through as a value. For
example, a job whose version is `v1.24.0; touch /tmp/owned #` makes the node create `/tmp/owned`
rather than treat the text as a version.

## What must be true

No value that a job submitter supplies may ever be interpreted by a shell on the node. Every value a
job carries must reach the tool that acts on it as literal data, and must never start a second
command, a command substitution, a redirection or a pipeline.

This holds for every value a job can carry, not only the version in the example, and however the
value reaches the node, including values the node stored when the job was first received and reuses
later.

A job that carries such a value must be refused with an error rather than acted on, and nothing
beyond the tool the job is meant to run may be executed or changed.

## What must keep working

Everything that works today keeps working exactly as today. In particular, ordinary jobs keep
succeeding with the same arguments handed to the same tools: versions with prerelease suffixes, image
references that name a registry and a port or that carry a tag or a digest, an empty image, and an
upgrade that keeps running in the background and writing its output where it does today.

The example above is an example, not the full set of values that must be rejected.

## Constraints

- Fix the problem and its close variants; do not special-case the example.
- Keep legitimate use working exactly as it does today.
- Do not look up the upstream fix or advisory.
