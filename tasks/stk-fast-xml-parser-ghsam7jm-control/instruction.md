# Entity expansion can be redirected by an entity's name

`fast-xml-parser` is a JavaScript library that turns XML text into JavaScript values. Applications use it to read XML from untrusted sources: a caller hands a document to the parser and works with the returned object.

## Observed impact

A document can declare an entity under one name and have the parser insert that entity's text for a reference that uses a different name. For example:

```js
const { XMLParser } = require('fast-xml-parser');
new XMLParser().parse('<!DOCTYPE note [<!ENTITY a\\ "spoofed">]><note>&a;</note>');
// => { note: 'spoofed' }
```

The document never declared an entity called `a`, yet the element comes back holding the declared text, so the parsed value says something the document did not.

## Required behaviour

Entity names identify entries literally. The text inserted for a reference must be the declared text of the entity whose name is exactly the reference's name, and a declaration under one name must never change how a reference with any other name is resolved. This holds for every entity the parser knows about, however that entity came to be defined.

Entity replacement text is data, not instructions. Every character of the declared text must appear in the output as written, and nothing in it may add, remove or reorder the text around the reference.

A document that cannot be handled safely must be refused by throwing an error, and that refusal must not produce a result.

Everything that works today must keep working exactly as today, including the public API, its documented options, and every document the library currently parses successfully.

The examples above are examples; they are not the full set of names, values or documents that must be handled.

## Constraints

- Fix the problem and its close variants; do not special-case the examples.
- Keep legitimate uses working.
- Work only from this report and the repository.
- Do not look up the upstream fix.
