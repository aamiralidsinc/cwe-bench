# A binding exclusion must hold for every spelling of a field

The project is the Spring Framework. Applications use its request-to-object data binding to copy
submitted form values onto an object. An application can exclude named object properties from that
binding.

Observed impact: an application binds a form submission onto a user object and excludes the `role`
property from binding. A submission that names the field `Role` instead of `role` is still written
to the object, so the exclusion has no effect.

Security property: when an application excludes a property from request-driven binding, no request
may write that property, however the request spells the field that reaches it.

Contracts:

- A refused write leaves the target object exactly as it was.
- Fields recorded as suppressed keep the name the request supplied, in the canonical form the
  product already uses.
- Everything that works today keeps working exactly as today.
- The example above is one example, not the complete set.

Constraints: fix the problem and its close variants; keep legitimate use working; do not look up
upstream changes to this project; do not special-case the example.
