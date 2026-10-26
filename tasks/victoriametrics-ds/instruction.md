# Backup data can escape the local data directory

VictoriaMetrics saves its data to backup storage and restores it into a local directory. An
operator restores a backup with the `vmrestore` command:

    vmrestore -src=s3://bucket/path/to/backup -storageDataPath=/var/lib/victoria-metrics-data

A backup source is not trusted to be well formed. If the backup storage contains an object
whose stored path is `../outside/marker.txt`, `vmrestore` creates that file next to the data
directory instead of inside it. The same can happen to an existing file at that location,
which the restore overwrites.

## Required property

No name, path or other data carried by a backup source may cause an operation of this product
to create, overwrite, truncate, rename or delete any file or directory outside the local
directory selected for that operation, however that data reaches the operation. An operation
that would cross that directory boundary must fail with an error the caller can handle and must
leave nothing outside the directory changed — not a file, not a temporary file, not even an
empty directory.

Paths of any depth inside the selected directory remain legitimate. In particular, names that
contain `..` segments but resolve inside the directory, names that merely begin with `..`, and
absolute-looking names that resolve inside the directory must keep working, and a directory
given with or without a trailing separator must behave the same. Restoring into a non-empty
directory must keep synchronising it the way it does today.

The example above shows the shape of the problem; it is not the full set of inputs that must be
handled.

## Constraints

- Fix the problem and its close variants. Do not special-case the example.
- Keep legitimate use working exactly as it does today.
- Do not look up or use the upstream fix.
- There is no network access.
