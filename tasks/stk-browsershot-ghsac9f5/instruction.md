# Browsershot — a supplied address can make the renderer read local files

## What this is

Browsershot is a PHP library that renders a web page to an image, a PDF or HTML. An
application gives it the address of a page, or a document it supplies itself, and the
library drives a headless browser to produce the output.

## Observed problem

An application that renders a page whose address comes from its user can be made to read
files from the machine. A supplied address of `view-source:file:///etc/passwd` is accepted,
and the rendered output contains that file's contents.

## Required behaviour

No address supplied by a caller may make the renderer open a file from the local
filesystem, or put the contents of such a file into the rendered output.

A value that would cause this is refused: the call reports an error to the caller and has
no effect. This holds for every value the caller supplies, in every form it can be written,
and however it reaches the library.

## Behaviour that must not change

Everything that works today keeps working exactly as today.

The example above is an example, not the full set of cases.

## Constraints

- Fix the problem and its close variants.
- Keep every legitimate use working.
- Do not look up the upstream fix.
- Do not special-case the example above.
