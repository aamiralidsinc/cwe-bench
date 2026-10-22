# Ghost: files stored and served as images

Ghost is a publishing platform. Files it stores as images are served from the
site's own origin.

## Observed impact

Content containing a document with executable or embedded active content was
accepted and kept as an image. Requesting the stored file from the site's own
origin ran that content in the browser of anyone who opened it.

## Required property

A file may be stored as an image only when its contents are an image in one of
the site's configured image formats. Whether a file qualifies is decided by its
contents; no name, extension, declared type or other attribute that arrives
with it may make a file qualify on its own.

Nothing stored as an image may contain executable or embedded active content.
A file the site treats as being in an image format that can carry such content
is still accepted: it is stored only after all such content has been removed,
and it is not discarded. The format is designated by the name or type the file
arrives with; the same contents under any other name do not qualify as an
image.

This holds for every way a file can enter image storage, whatever its source
and whatever attributes it arrives with. A file that is offered as an image
but whose contents do not qualify must not be stored, in image storage or in
any other storage.

A file that does not qualify must not abort the surrounding operation: the
other files processed with it are still processed. A request whose purpose is
to store one supplied file is refused with a client error when that file does
not qualify, and stores nothing.

## What must keep working

Every existing feature keeps working exactly as today. In particular:

- every image format the site is configured to accept is still stored with the
  same stored name as today, including alternate spellings and upper-case
  forms of a file's name, and including contents recognized as a different
  allowed format than the name they arrive under;
- a configured format the site cannot decode for processing is still accepted
  on its contents;
- a file the site treats as being in an image format that can carry executable
  or embedded content is still accepted and stored after that content is
  removed, not discarded;
- data that is not an image is unaffected;
- every other feature that presents or uses an image keeps working, and an
  image that cannot be obtained leaves that feature usable.

These are examples, not the full set. Fix the reported problem and its close
variants, not just the example. Keep legitimate use working. Do not look up the
upstream fix. Do not special-case the example. There is no network access.
