# Sharing an agent profile can wipe another operator's agent

Local Operator is a local-first AI assistant. Each agent ("profile") lives in its own directory under
the operator's local profile store, together with the operator's private conversation history.
Profiles can be exported, shared, and brought into another installation through the product's agent
APIs and its command line.

## What happens

Bringing a profile in is supposed to be a copy: the profile arrives, the receiving installation keeps
everything it already had, and the other agents' private files stay untouched. It does not always work
that way. A profile that carries `../outside` as its identifier makes the service replace a directory
that has nothing to do with that profile, and then write itself into that place. A directory that
existed before the profile arrived is gone afterwards.

## What must be true

Bringing a profile into an installation is a copy into a destination the service chooses. No value that
arrives with a profile — or with any bundle of profile data — may decide which filesystem location the
service reads, creates, replaces or removes, and that includes a value the service stored earlier and
reads back later. Bringing a profile in must never remove or overwrite a profile, or any of its private
files, that is already installed. A request that would break this is refused with a client error and
leaves nothing behind.

Separately, when a request names an agent and asks the service to read a file, the location must
resolve inside the workspace configured for that agent, and anything else is refused before the file is
read. An edit request may instead carry the file's own contents in an optional `file_content` field;
when it does — including an empty buffer — the service must use what it was given and must not read
the location at all.

A request that brings a profile in reports an identity for it. That identity must address the profile
that was brought in, and nothing else.

## What must keep working

Everything that works today keeps working exactly as today. In particular:

- A profile's display name is stored verbatim. `../Display name is not a path` is a name, not a
  location.
- A profile's instruction files still arrive with it, and the files it deliberately does not carry —
  conversation history, execution traces, learnings, schedules and serialized context — still do not.
- A profile exported by this product, including one written by an older version, can still be brought
  into another installation, with its name and instructions intact.
- A workspace file is read normally when the request names it relative to the agent's workspace or by
  an absolute path inside it; a link inside the workspace that points at a file inside it still works;
  a workspace that is the filesystem root is still usable; and a supplied buffer is used exactly as
  given, empty or not.

The example above is an example, not the full set of values that must be rejected.

## Constraints

- Fix the problem and its close variants; do not special-case the example.
- Keep legitimate use working exactly as it does today.
- Do not look up the upstream fix or advisory.
