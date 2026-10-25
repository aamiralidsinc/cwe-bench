# Keep caller-supplied media keys inside the media area

## The system

This project is a content platform with a built-in media manager. Editors
upload images and files through the admin UI; the platform's server-side media
API receives each request, checks that the caller is a signed-in editor, and
then talks to whichever cloud storage backend the deployment is configured to
use — an object store or an image service. The project ships several such
backends behind the same media API.

An operator may configure a **media root**: the object-store prefix (folder)
under which all of a site's media is supposed to live. Some backends offer that
setting; others currently do not. The object key or directory for each
operation is chosen by the caller at request time and is passed on to the
storage service.

## Observed problem

A signed-in editor asks the media API for an upload URL for a key that is not
inside the configured media area — for example an object at the bucket root or
in another application's prefix. The API returns a working upload URL for that
key, so the editor can write, and later read back, objects anywhere the
deployment's storage credential can reach. The same unchecked value is used by
the delete and listing operations, and by the other storage backends the
project ships.

## Security properties (invariants)

- No caller-supplied object key, directory, file name, list of keys, or pair of
  keys used together may cause a read, write, copy, move, delete, presigned
  write URL or listing outside the media area the backend serves. When a media
  root is configured, every key used with the storage service must resolve at
  or below that root.
- The rule holds for every operation the media API exposes and every storage
  backend the project ships, including backends that have no configured root.
  Where no root is configured, a key must still be relative and must not be
  absolute or climb above the area being served.
- The rule holds for every input shape: a single value, a repeated value (a
  list), a key split across route segments, and a directory and file name
  supplied in a multipart or form body.
- A key that is absolute (a leading separator or a Windows drive letter),
  contains a NUL byte or a backslash, is empty, or uses `..` to climb above the
  area is refused with a client error (a 4xx response). No storage operation
  may be carried out for such a value.

## Keep working

Ordinary use must behave as it does today:

- uploading to, listing, and deleting objects inside the media area;
- deleting an item using the identifier the listing returned — that identifier
  may already include the configured root and must not be prefixed a second
  time;
- names containing a literal percent sign (they must not be decoded again);
- an inner `..` that still resolves inside the area (it is collapsed, not
  refused);
- a key spread over several route segments, and directories with leading or
  trailing slashes;
- listing the root of the area and any directory below it;
- copying between two keys that are both inside the area.

For example, requesting an upload URL for `photos/summer/a.png`, deleting the
identifier returned for that file, and listing `photos` are ordinary and must
keep working. These are examples, not the full set of operations or inputs.

## Constraints

- Fix the underlying problem and its close variants, not just the exact example.
- Keep every legitimate use working.
- Do not modify or add tests, and do not special-case the example inputs.
- Do not consult any upstream fix, advisory, or changelog for this project.
