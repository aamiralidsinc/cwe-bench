# Unexpected file disclosure through a download

Silverpeas is a collaborative web platform. It stores the files that belong to collaborative
spaces: documents users upload, attachments, and resized images. Users reach those files by
downloading them from the application.

## What happens today

A user who is signed in can make a download request that names an absolute location on the server
instead of one of the files of a space they can reach. The server opens that location and returns
its contents. For example, a signed-in user can ask the application, through such a download
request, for the machine's hostname file and receive it, although that file belongs to no space
the user can access.

## What must hold

- Only a caller who is signed in, and who is entitled to the space a file belongs to, may receive
  that file. A caller who is not signed in, or who is not entitled to that space, must not receive
  it.
- A request must never cause a file outside the space it is entitled to be opened or returned,
  however the location is supplied.

## Contracts

- A refused request answers with a client error and returns no file content; it must not end in a
  server error.
- Everything that works today keeps working exactly as today.
- The request described above is an example, not the full set of requests or forms to consider.

## Constraints

Fix the problem and its close variants; keep legitimate use working; do not look up the upstream
fix; do not special-case the example.
