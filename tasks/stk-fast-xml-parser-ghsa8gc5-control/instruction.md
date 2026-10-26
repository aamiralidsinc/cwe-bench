# Entity handling in fast-xml-parser

fast-xml-parser validates XML documents and converts them into JavaScript objects. Applications
commonly run it over documents supplied by untrusted clients.

## Observed impact

A document of a few kilobytes can keep the parser busy for a long time and allocate far more memory
than the document itself. A DOCTYPE that declares one ordinary entity, together with a body that
references that entity many times, makes the parser build an output string millions of times larger
than the input. Because Node.js runs JavaScript on one thread, a single request of this kind can
block an application's event loop.

## Security property

For every document the library accepts, the work, memory and output produced must stay within
bounds the library enforces. No document, however small, may make entity handling consume a
disproportionate amount of resources. The bounds must be in force with the default configuration
and must hold for every entity reference the document contains, whatever supplies the replacement
value.

## Contracts

- Entity processing stays configurable through the existing `processEntities` option. It must keep
  accepting `true` and `false` with their current meaning, and must also accept an object whose
  `maxTotalExpansions` field is the maximum number of entity references to replace in one parse and
  whose `maxExpandedLength` field is the maximum total growth of the produced text in one parse.
  An `enabled: false` field keeps disabling entity processing.
- When a bound is exceeded, parsing fails by throwing an ordinary `Error`; no partial result is
  returned.
- Everything that works today keeps working: a document whose substitutions stay inside the bounds
  still parses to the same values it has today, and the parser's existing options keep their
  meaning. A document that expands a handful of references must still parse.
- The default bounds must be large enough for normal documents and small enough that the impact
  example above is refused.

These examples are examples, not the full set. Fix the problem and its close variants without
special-casing any document.

## Constraints

- Fix the problem and its close variants.
- Keep every legitimate use working.
- Do not look up the upstream fix.
- Do not special-case the example.
