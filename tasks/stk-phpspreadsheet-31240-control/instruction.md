# Reading an untrusted workbook can exhaust the process

## What this is

This is a PHP library for reading and writing spreadsheet files. Applications embed it to open
workbooks that users upload or fetch from elsewhere.

## Observed problem

A file supplied by a user can make the process consume far more memory or far more time than the
file itself accounts for. For example, a gzip-compressed spreadsheet of a few hundred kilobytes can
expand to hundreds of megabytes when it is decompressed; the process is then killed for running out
of memory. A single uploaded file is enough to take the whole service down.

## Required behaviour

Handling a workbook that comes from outside the application's own code must never exhaust the
process's memory, and it must terminate. A file that would do either is refused.

A refusal is clean: the library reports that it cannot handle the file, or it raises an error the
caller can catch. A fatal error, a process killed for lack of memory, a call that never returns, or
silently returning wrong data is not a refusal.

## Behaviour that must not change

Everything that works today keeps working exactly as today.

Workbooks of several megabytes, and compressed workbooks that expand to a few megabytes, are
ordinary files and must keep working normally.

## Constraints

- The example above is an example; it is not the full set of files that must be refused. Fix the
  problem and its close variants.
- Keep every legitimate use working.
- Do not look up the upstream fix or any existing implementation of it.
- Do not special-case the example.
- There is no network access.
