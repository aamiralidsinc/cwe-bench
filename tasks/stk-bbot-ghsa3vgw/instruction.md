# A malicious download can write outside the folder reserved for it

BBOT is a reconnaissance scanner. While scanning a target it downloads files that
the target publishes and expands the archives among them so their contents can be
scanned. It also saves material that it retrieves from third-party services which
the target references.

## Observed impact

A user runs a scan against a server that serves a crafted archive. While the scan
expands that archive, files appear outside the folder the scanner created for it,
at a location the server chose. The same kind of thing happens with names that come
back from a remote service: a crafted name makes the scanner save its output
outside the folder it reserved for that service.

## What must hold

1. Expanding an untrusted archive must not create, replace or modify anything
   outside the directory the scanner created for that archive, whatever the
   archive contains.
2. A name the scanner receives from a remote service must not cause it to create,
   replace or modify anything outside the scanner's own output folder for that
   service.

Both properties hold for every archive the scanner expands and every service it
saves data from. The examples above are examples, not the full set.

## Contracts

- When the scanner cannot perform an operation safely it must refuse it cleanly:
  nothing outside the scanner's own output folders is created or changed, and the
  scanner does not crash.
- Everything that works today keeps working exactly as today: the archives and
  service data that the scanner accepts now are still expanded and saved, in the
  same layout and at the same paths, and the ordinary inputs accepted today are
  still accepted.
- Fix the problem and its close variants. Do not special-case the examples, do not
  weaken legitimate behaviour to make the examples pass, and do not look up the
  upstream fix.
