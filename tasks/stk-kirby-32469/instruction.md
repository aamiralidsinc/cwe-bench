# Kirby

Kirby is a PHP content management system. Editors work through a JSON API. Pages, sites and
user accounts hold files, and the API accepts both ordinary uploads and uploads that arrive in
several requests and are assembled in a staging area before the finished file is stored.

## Impact

A signed-in API client whose role is not allowed to create files on a page can start an upload
to that page's files collection. The request that carries the first part is answered as
successful and its bytes are written into the site's upload staging area, even though the
finished file would be refused.

## Security property

No part of an upload may be stored anywhere until the system has decided that the acting account
may perform the finished operation on the object the upload targets, judged with the same name,
declared file type and target that the finished file will have.

The limits and declared file type of an upload that arrives in several requests are fixed by its
first request and govern the whole upload; a later request that relies on different values cannot
substitute them and is refused.

## Contracts

- A request that must not be stored is refused with a client error (any 4xx) and has no effect:
  no byte is staged, no file is created, replaced or changed, and no account is modified.
- Everything that works today keeps working exactly as today.
- The example above is an example, not the full set of entry points or shapes.

Fix the problem and its close variants, keep all legitimate use working, do not look up the
upstream fix, and do not special-case the example.
