# A crafted backup can write files outside the backup folder

## System

Home Assistant is a home-automation platform. Its backup feature creates an archive of the
installation and can accept an archive created elsewhere, for example to move a configuration to
a new installation. During first-time setup, before any user account exists, the setup flow
accepts a backup upload so a new installation can be brought up from it.

Every backup archive carries its own descriptive metadata: the name shown in the interface, a
date, and an identifier that distinguishes it from other backups. Home Assistant uses that
metadata when it stores a backup and when it later works with it.

## Observed impact

Uploading a crafted backup archive can make Home Assistant write a file outside the folder it
uses for backups. For example, an archive whose stored name is `../configuration` causes a file
to be written in the installation's configuration directory. The file name typed for the upload
itself is not what triggers this; the metadata inside the archive is.

## Security property

No value carried inside a backup archive, and no value supplied for a backup name, may be used
to create, write, move or delete anything outside the directory Home Assistant allocates for that
backup or for the files associated with it. This holds however the value arrives (supplied in
the current request, uploaded inside an archive, or saved earlier), whichever operation later
uses it, and even when that operation is refused. A request which would do so is refused, and
the refusal leaves nothing behind outside that directory.

## Behaviour that must be kept

- Ordinary backup names keep working exactly as today, including names with spaces, dots, mixed
  case and non-ASCII characters. They are stored under the same derived file name and listed with
  the same displayed name as before.
- The default name used when no name is supplied stays as today, and a custom name is kept as
  supplied.
- A normal identifier is accepted as today. A name or identifier that is merely long, or that
  contains spaces, dots, mixed case or non-ASCII characters, is legitimate.
- Everything that works today keeps working for backups that stay inside their folder, including
  the upload offered during first-time setup before setup is complete.
- A backup archive that cannot be used is left out of listings; one unusable archive already
  present must not break the backup list or start-up.

## Refusal

A request that carries such a value is refused with a client error (4xx), not answered by
rewriting the value and not by failing with a server error, and leaves no file or directory
behind outside the folder it was meant for. Silently storing the backup, or a file associated
with it, under a different name instead of refusing is not acceptable. The exact error message
and error code are not important.

## Constraints

- Fix the flaw and its close variants, not only the example shown.
- Keep every legitimate use working.
- Do not special-case the example values.
- Do not consult any upstream advisory or fix for this issue.
- There is no network access.
