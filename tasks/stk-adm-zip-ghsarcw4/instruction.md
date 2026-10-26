# adm-zip — reading an untrusted archive can exhaust memory

## What this is

adm-zip is a Node.js library for reading and writing ZIP archives held in memory or on
disk. A caller hands it an archive buffer, then reads individual entries or extracts the
whole archive. Applications commonly use it on files that came from someone else: uploads,
build artifacts, mail attachments.

## Observed problem

An application that reads one entry from an untrusted archive can be driven into memory
exhaustion by a very small archive. An entry whose declared uncompressed size is zero, but
whose compressed bytes expand to hundreds of megabytes, is decompressed in full while the
read is in progress. The process's memory grows with the expanded data, not with the size of
the archive, and the read reports no error.

For example: an entry that declares an uncompressed size of 0 and carries a compressed
stream that expands to 64 MiB. Reading that entry through the library's normal read call
consumes the expanded size in memory.

## Security property

For any entry of an archive that a caller reads or extracts:

1. A read must not produce more decompressed bytes than the uncompressed size the entry
   declares. If the data would exceed that size, the read fails and produces no output.
2. A declared size must not, by itself, cause memory to be allocated. Memory may grow only
   as data is actually produced.

## Contracts

- A read that violates either bound fails and produces no output, and it must never crash
  the process.
- Everything that works today keeps working.
- The examples above are examples, not the full set.

## Constraints

- Fix the underlying problem and its close variants, not just the one example trigger.
- Keep every legitimate use working.
- Do not look up the upstream fix for this issue.
- Do not special-case the example values.
