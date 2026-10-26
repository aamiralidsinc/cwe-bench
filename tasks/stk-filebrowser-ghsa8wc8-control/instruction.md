# A restricted account can write and read outside its folder

File Browser is a web file manager. An administrator can restrict each account to one folder: that
account may create, overwrite, move and browse only inside the folder, and must never reach the rest
of the server's disk.

A user whose account is restricted to one folder can put a symbolic link inside that folder whose
target lies outside it, then upload to the link's path. The upload is accepted and the content is
written outside the user's folder, where the account has no rights.

## Requirement

No path an account supplies, and no path the product derives from it, may cause anything outside
that account's folder to be created, overwritten, moved, copied or otherwise changed, however the
path is written, whichever intermediate links it passes through, and however those links are written
or where they ultimately point.

No account may learn anything about anything outside its folder — content, names, sizes or times —
through any operation it performs.

A request that would violate these rules must fail with a client error and leave nothing changed
outside the folder.

These are invariants, not a list of cases. The example above is an example.

## Behaviour that must not change

- Creating a genuinely new file or folder inside the folder keeps working, including through a link
  whose target is inside the folder and does not exist yet.
- Overwriting a file that already exists inside the folder keeps working, including when it is
  reached through a link that resolves inside the folder.
- Listing inside the folder keeps working, including when a link inside it points to another place
  inside it.
- Every other legitimate operation on paths inside the folder keeps working exactly as today.
- An account whose folder is the whole server keeps its current unrestricted behaviour.

## Constraints

Fix the problem and its close variants. Keep legitimate use working. Do not look up the upstream fix.
Do not special-case the example above.
