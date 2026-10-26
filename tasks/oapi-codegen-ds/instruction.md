# Keep OpenAPI document text out of generated Go source

## The system

This project is a code generator. It reads an OpenAPI document that describes
an HTTP API and writes one Go source file containing the corresponding types,
constants, validators, client and server helpers. Teams run it as part of their
build, and the document it reads may come from a service they do not fully
control.

## Observed problem

A document whose server description contains a line break makes the generator
write a Go file in which a line of attacker-chosen text has become a real
top-level declaration in the generated package. The file still compiles, so the
change can go unnoticed while it is built into the application.

## Security property (invariant)

Text taken from the OpenAPI document is data, never code. For any document,
generation must either fail with an error or produce a single syntactically
valid Go file in which no identifier, declaration, import, statement or
expression comes from document text. Every piece of document text that the
generator emits must appear only as data: inside a correctly quoted Go string
literal that reads back as exactly the original text, or inside a comment.
This holds for any text anywhere in the document, however it is spelled,
whatever it contains and wherever it is placed, and at every point while a file
is being generated.

If the generator cannot represent a document safely it must return an error and
produce no output rather than write code that contains the text.

## Keep working

Everything that works today keeps working exactly as today. In particular:

- server URLs that contain `{name}` placeholders still become constructors that
  substitute each placeholder, including a placeholder with no declared
  variable, and a URL with several placeholders still works;
- every value the document supplies that the generator emits as data keeps its
  exact text: a URL, a default, a permitted value, a description, or the
  document's own metadata, including its quotes, backslashes, ordinary spaces
  and non-ASCII characters;
- ordinary permitted values keep the generated names they have today and still
  validate;
- a realistic document still generates its models, validators, client and
  server helpers without error.

A description such as `Primary "production" endpoint at C:\temp`, a URL such as
`https://{tenant}.example.com:{port}/v1`, and a permitted value such as
`beta value` are ordinary and must keep working. These are examples, not the
full set of inputs.

## Constraints

- Fix the underlying problem and its close variants, not just the example.
- Keep every legitimate use working.
- Do not special-case the example inputs.
- Do not consult any upstream fix, advisory, or changelog for this project.
