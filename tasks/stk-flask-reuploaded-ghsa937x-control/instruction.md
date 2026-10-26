# An upload can be stored under a refused file type, or outside the upload folder

Flask-Reuploaded is a Python library that applications use to accept file uploads. An application
defines an upload set with a destination folder and the file types it accepts or refuses, then asks
the set to save each submitted file.

Our application lets a user choose the name a file is stored under. A user uploaded an image and
chose `payload.php`; the upload set accepts images only, but the file was saved under that name and
was later served as a script.

## Security invariant

No upload may end up stored under a name that can be taken as a file type the upload set refuses,
whatever letter case is used and however the name is supplied.

No upload may create or change anything outside the destination folder the upload set is configured
with.

## Contracts

- A save that breaks the type rule is refused with the library's existing refusal error, and it
  writes no file.
- A save that would reach outside the destination folder leaves nothing there created or changed,
  whether it is refused or kept inside the folder.
- Everything that works today keeps working exactly as today, including the library's public
  interfaces and their documented behaviour.

These rules are general. The example above is an example, not the full set.

## Constraints

- Fix the problem and its close variants.
- Keep legitimate use working.
- Do not look up the upstream fix.
- Do not special-case the example.
