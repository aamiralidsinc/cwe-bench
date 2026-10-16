# Callers can set fields that their view does not allow

## The system

Our service uses the JSON data-binding library in `/app` to bind untrusted
request bodies to Java objects: to create new records, and to apply partial
updates to records that already exist. Callers have different privileges, and
we express them with `@JsonView`. Each request is read with the caller's view
active, for example `mapper.readerWithView(PublicView.class)` or
`mapper.readerForUpdating(existing).withView(PublicView.class)`. A property
annotated for a more privileged view, such as `@JsonView(AdminView.class)`, must
stay out of reach of a caller whose view does not include it
(`AdminView extends PublicView`).

## What we observed

This works for most properties, but not all of them. Example: a document type
has a polymorphic property `asset`, annotated `@JsonView(AdminView.class)`,
whose subtype is chosen by a separate field `kind` next to it. A public caller
sends

```json
{"label": "x", "kind": "admin", "asset": {"name": "n", "secret": "s"}}
```

and reads it with `readerWithView(PublicView.class)`. `asset` is filled from the
request even though the caller's view does not include it.

This is one example, not the whole problem. Other types and other ways of
reading input let restricted values through in the same way.

## Required behaviour

- While a view is active, no input may set a property that is restricted to
  views the active view does not include. This holds for every kind of
  deserialization: whatever the type looks like, however the
  object is built or populated, and whether the input creates a new object or
  is applied to an existing one.
- Input aimed at such a property is ignored without an error, as the library
  already does for ordinary restricted properties. The property keeps the
  value it had before the read (on a new object, its default).
- Hiding a value must not change how the rest of the input binds. Properties
  that are visible in the active view keep binding exactly as they do today,
  including when they sit next to a hidden value or depend on one.
- With a view that includes the property, or with no view active, everything
  binds exactly as it does today. A property with no view restriction keeps
  binding under any view.

## Constraints

- Fix the flaw in the library itself, for every way input can reach a
  restricted property, not only the example above. Do not special-case the
  example's types, field names or values.
- Keep legitimate use working as described above.
- Do not modify or add tests; hidden tests will check the behaviour.
- Do not look up or copy an upstream fix for this issue.

## Notes

The repository is in `/app`. There is no network. You can confirm that the
library still compiles with `/opt/verify/compile-lib.sh`.
