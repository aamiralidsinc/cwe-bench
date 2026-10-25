# Keep untrusted model and weights files from reading outside themselves

## The system

This project is a deep-learning library. Users save a model's architecture and
weights into a local artifact and later load them back. Supported artifact
forms include a self-contained model archive, an unzipped model directory, a
single weights file, a sharded weights set described by a small index file plus
several shard files, and the older single-file model format. Users also have a
utility that opens a weights file to inspect and edit it and to resave it.

These artifacts are routinely obtained from third parties: downloaded model
zoos, checkpoints uploaded by users, weights attached to a report. Loading one
is a normal operation on data the person running it may not trust.

## Observed problem

A saved artifact can express indirection: instead of storing a value inside
itself, one of its entries can point at data kept in a different file on the
host, or at another file that accompanies the artifact. A crafted artifact
using such an entry makes the loader open that other file and fill model
weights — or the inspector's data — with its contents. The party who supplied
the artifact, or anyone who can read the resulting model, then sees bytes from
a local file the load was never given. The same applies when an entry is a link
to another location rather than a stored value, and at any position in the
artifact: a single value, a group of values, the top-level container, or
optimizer state.

The problem is the same when weights are loaded into an existing model, when a
saved model is rebuilt, when a sharded weights set is loaded, when the older
single-file model is loaded, and when the inspection/editing utility opens a
weights file.

## Security properties (invariants)

- No content of an untrusted model or weights artifact may cause any API that
  loads or inspects it to read data from outside the set of files that make up
  that artifact. This holds for every artifact form named above, for every
  position an entry can occupy, and for every way the format lets an artifact
  express indirection, including a link to another location and a value whose
  bytes are kept in an external file.
- When an artifact contains an entry that would reach outside the artifact,
  the operation must fail safely: the public call raises a client-side error,
  and no model variable and no inspector data is populated from the
  out-of-bounds file. A call that returns successfully while carrying outside
  data is not acceptable.
- The protection must hold at every loading and inspection entry point, not
  only the one first noticed, and for a link or indirection at any level of the
  artifact, not only at the deepest one.

## Keep working

Ordinary, self-contained artifacts must behave exactly as they do today,
including:

- saving a model's weights and loading them into a freshly built model, for a
  single weights file and for a sharded set whose shard files are listed by its
  index file (including a set where one layer's values are split across two
  shard files);
- saving a model and loading it back, both as a zipped archive and as an
  unzipped directory;
- loading the older single-file model format, including loading weights by
  name and restoring optimizer state;
- loading a weights file saved by an older release whose entry layout differs
  from the current one;
- inspecting and resaving an ordinary weights file with the
  inspection/editing utility;
- weights stored in reduced-precision types;
- an artifact that already declares that a value lives in an external file:
  this is refused today and must stay refused. That refusal is existing
  behaviour, not the gap to fill.

For scale: an ordinary artifact here is small — a two-layer dense model of a
few tens of kilobytes, a two-shard weights set of the same size. Loading it
must not become slower or stricter in any user-visible way. An artifact that
names a file outside itself is the case that must be refused. These are
examples, not the full set of formats, positions or APIs.

## Constraints

- Fix the underlying problem and its close variants, not just the exact example.
- Keep every legitimate use working.
- Do not modify or add tests, and do not special-case the example inputs.
- Do not consult any upstream fix, advisory, or changelog for this project.
