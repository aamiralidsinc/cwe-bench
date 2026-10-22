# Definition data must never become code

Pimcore is a data and experience management platform. A data model is described by
definition documents that administrators or deployment pipelines supply. Applying a
definition stores it and makes the platform build program text and storage statements
from it, both at that moment and when the stored definitions are rebuilt later.

## Observed impact

A definition author can supply values that are treated as code or as statement syntax
rather than as data. For example, a definition that gives one of its entries a name
containing metacharacters produces generated program text that executes the author's
payload with the application's privileges, and the same definition can change the
structure of the statements the platform runs against its storage.

## What must hold

A definition is data, never code. No value that a definition document supplies for an
entry it declares may change the structure of the program text generated from that
definition, and no value that the platform embeds in a storage statement while applying
a definition may change that statement's structure. Such a value must remain inert
inside the text that contains it — it must not be able to end the construct it is placed
in and become syntax — or it must be refused with a client-visible error before anything
is generated or executed. The requirement holds for every such value, whatever it is
used for and whichever part of the platform consumes it: there is no exception for a
value because of what it looks like, and no difference according to where an embedded
value came from. A value that provides configuration rather than a name is accepted only
in recognised forms and never contributes syntax of its own.

## Contracts the behaviour relies on

- **Refusal form.** A refused definition raises a client-visible error while it is
  applied; once it is refused, nothing has been generated and nothing has been executed.
- **Public path.** The requirement holds on the platform's public interfaces for applying
  a definition and for generating the program text from it, not only when an internal
  helper is invoked directly.
- **Preservation.** Legitimate definitions keep producing exactly the program text and
  the storage statements they produce today. In particular: assigning the empty name
  transiently keeps working; every valid name from one character up to 63 characters,
  including one beginning with an underscore, is accepted; the platform's fixed internal
  names keep working; labels that already contain spaces, punctuation or separator
  characters keep their generated names; entry types that occupy several storage columns
  keep their layout; unique constraints keep every column they carry; configured column
  types keep their configured forms; and ordinary renames, ordinary default values and
  ordinary storage-maintenance operations keep working.

These examples are examples, not the full set of shapes that must be handled.

## Constraints

- Fix the problem and its close variants; keep legitimate use working.
- Do not look up the upstream fix.
- Do not special-case the examples.
- There is no network access.
