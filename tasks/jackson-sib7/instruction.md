# View-based access control bypassed during polymorphic deserialization

## Summary

Our service uses this JSON data-binding library to turn untrusted request
bodies into Java beans. We rely on `@JsonView` to enforce a privilege boundary:
low-privilege callers deserialize with a restricted view active, and any
property or constructor parameter annotated for a more privileged view is
supposed to be ignored (left unset) when that restricted view is active. This
is how we keep attacker-supplied JSON from populating privileged fields.

The filtering works for ordinary properties, but it is **not** applied to a
polymorphic property whose concrete subtype is chosen by a *separate, sibling
JSON field* (the discriminator lives next to the object, not inside it). When a
bean has such a property and that property is restricted to a privileged view,
a caller deserializing under a **less** privileged view still gets the property
populated straight from the request JSON. The privilege check is silently
skipped on this binding path, so the restricted value is bound anyway.

## How it is triggered

Through the library's public API: reading JSON for such a type with a
restricted view active, e.g.

```java
Container c = mapper.readerWithView(PublicView.class)
                    .forType(Container.class)
                    .readValue(untrustedJson);
```

where `Container` has a polymorphic property (`@JsonTypeInfo` with the type id
carried in a sibling property, plus `@JsonSubTypes`) that is annotated
`@JsonView(AdminView.class)`. Under `PublicView`, the admin-only property is
nonetheless filled from the JSON. The same bypass occurs regardless of how the
bean is constructed — via a property-based `@JsonCreator` constructor, via a
plain no-arg constructor with setters/fields, or via a builder. A related case:
when the discriminator field is itself a view-restricted creator parameter, its
value is likewise bound under a view that should hide it.

## Required outcome

When a view is active, a property or parameter that is not visible in that view
must never be populated from the input — on **every** binding path by which
untrusted JSON can reach a property, not just the one shown above. That includes
the polymorphic sibling-discriminator path, every way the bean is constructed
(property-based creator, no-arg constructor with setters/fields, builder), and
any mechanism by which otherwise-unmapped input can still be routed into a
restricted property — whether that collection point is declared as a field, as
a setter method, or as a constructor parameter, and whatever its declared type.
The fix must enforce the view boundary uniformly across all of these; blocking
only the one shape of input in the report above is not sufficient, and neither
is closing only the paths that bind a value directly onto an already-constructed
object while leaving the paths that gather input during construction open.

Legitimate behaviour must be preserved: with the appropriate (privileged) view,
or with no view active, these properties must still bind normally, and the
polymorphic subtype must still be resolved correctly from the discriminator.
Properties that *are* visible in the active view must continue to bind even when
a sibling value on the same object is hidden, and a property that carries no
view restriction at all must keep binding under any active view.

## Notes

The repository is in `/app`. There is no network. You can confirm the library
still compiles with `/opt/verify/compile-lib.sh`.
