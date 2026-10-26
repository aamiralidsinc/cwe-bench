# A stored template document can run code when it is compiled

## The system

This repository is a JavaScript template engine. An application compiles a template document into a
function that renders data: the engine turns the document into JavaScript source, evaluates it, and
the resulting function produces the output.

Besides template text, the library's public compilation API accepts a document's abstract syntax
tree — the plain object structure that a parsed document is made of, and that can also be written as
JSON. Tools and applications use that form: a codemod edits a parsed document, a build step caches
parsed templates, and a service compiles a stored document later on. A stored document can therefore
be written by someone other than the application that compiles it.

## Observed impact

A service keeps template documents as parsed structures and compiles one when it renders a page:

```js
const document = JSON.parse(await store.get(templateId)); // written by a tenant
const render = Handlebars.compile(document);
render({ name: 'world' });
```

The page renders its ordinary output, but a value the document carried — not text the template
displays, but a value in one of the document's internal positions — was written into the generated
JavaScript, and it ran while the template was being built. Code chosen by whoever wrote the document
runs with the service's privileges.

## What must hold

A template document is data, never code. Whenever the library turns a document into template code,
everything the document contributes to that code is data:

- a value in a text position is inside a correctly quoted string literal and reads back as exactly
  that value; and
- a value in a position that declares another kind of literal is a literal of exactly that kind —
  a number in a numeric position, a boolean in a boolean position, exact whole-number text in an
  integer-literal position.

No other value may become an expression, statement, identifier or property name in the generated
code, however it is spelled, nested or labelled. A document carrying a value that cannot be
represented this way is refused with an ordinary library error, and nothing derived from it runs.

This holds for every value anywhere in the document and at every public entry point that turns a
document into code, not only the most common one.

## Contracts

- **Refusal.** A refused document raises an ordinary error from the compilation call; no template
  carrying the value is produced or run.
- **Preservation.** Everything that works today keeps working exactly as today. In particular:
  - ordinary template text renders the same output, and a prepared template keeps working;
  - number and boolean arguments keep their own types in the mode that passes arguments as their
    source text, and ordinary path source text keeps the normalisation it has today;
  - block parameters still bind, and indented partials still render with their indentation;
  - a very large numeric literal in template text is an ordinary number and keeps compiling;
  - a whole-number literal argument of any magnitude still reaches a helper as an integer.
- The examples above are examples, not an exhaustive list of values, positions, spellings or entry
  points; reason about the property, not the samples.

## Constraints

- Fix the problem and its close variants, not just the exact sample described above.
- Keep every legitimate use working.
- Do not look up the upstream fix for this issue.
- Do not special-case the example inputs.
