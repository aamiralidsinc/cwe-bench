# install can write outside the destination it was given

`install` is a file-installation command: it copies one or more source files to a named destination and, with `-D`, creates the missing directories that lead to that destination.

## Observed impact

An unprivileged user who can write inside a directory that the installer's destination passes through can redirect the install. The installer follows a symbolic link that stands where one of the destination's directories has to be, so the directory tree and the destination file are created at the link's target instead — overwriting, moving or removing a file the administrator never named.

One trigger, as the administrator would run it:

    install -D ./payload /srv/app/data/plugins/payload

If `/srv/app/data/plugins` is a symbolic link to a directory elsewhere, the tree is created at the link's target and `payload` is written there.

## Security properties

- Whenever `install` creates directories for a destination or places the destination file, a symbolic link at a path component must not redirect the work: nothing may be created, overwritten, renamed or removed at a link's target.
- The destination must be created at the named location. A run that cannot do that must end with a non-zero exit status and a diagnostic on standard error, not a panic; a run that reports success must leave the destination at the named path.
- These properties hold for every way `install` can be asked to create a directory or write the destination, and for destinations given as relative or absolute paths.

## What must keep working

- Every ordinary install: creating nested directories, installing into an existing directory, overwriting an existing destination file, re-installing over files that are already present in a destination directory, relative destinations, and all the attribute options `install` already offers.
- A destination directory that already exists and is reached through symbolic links in its parent path — for example a symlinked system, home or project directory prefix — must keep working exactly as today, including creating new subdirectories below it. Those links must be left in place.
- The errors `install` already reports for an unusable destination (for example a path component that is a regular file, or a directory operand that does not exist) must keep their current behaviour and must not become a successful install.

The example is one illustration, not a complete list: the properties apply to every comparable input.

Fix the problem and its close variants. Keep legitimate use working. Do not look up the upstream fix. Do not special-case the example. There is no network access.
