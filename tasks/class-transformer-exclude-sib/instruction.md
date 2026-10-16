# Clients can set properties our classes protect

## The system

Our API service uses the TypeScript object transformation library in `/app` to
turn untrusted JSON request bodies into class instances (new instances on
create, the stored instance on update) and to turn instances back into JSON
responses. We protect properties with the library's documented decorators and
options: excluding a property (in both directions or in one direction only),
exposing it only to certain groups or API versions, giving it a different name
in JSON, and excluding a whole class except the properties it explicitly
exposes. Our classes extend shared base classes, are nested in one another, and
a subclass sometimes declares an inherited property again to restrict it
further.

## What we observed

```ts
class Account {
  name: string;

  @Expose({ name: 'credit_limit', groups: ['staff'] })
  creditLimit = 0;
}

plainToInstance(Account, { name: 'eve', credit_limit: 50000 }, { groups: ['customer'] });
// Account { creditLimit: 50000, name: 'eve' }
```

A customer chose their own credit limit. This is one example, not the whole
problem: other classes of ours accept protected values from input, or show
them in output.

## Required behaviour

- A property that is excluded, or not exposed for the groups or version of the
  call, is never set from input and never written to output. This holds at any
  depth (nested objects, arrays, sets, maps), for new and existing instances,
  and whichever JSON name the input uses for it.
- Restrictions declared on a class, on its properties or on the class as a
  whole, also apply when transforming any of its subclasses, however many
  levels down.
- When a subclass restricts an inherited property further, the restriction
  applies to the subclass; the base class keeps behaving as it declares.
- Input for a protected property is silently ignored, exactly as the library
  already ignores input for an excluded property: no error, and the rest of the
  input is transformed as usual.
- Everything else works exactly as today: properties that are not restricted,
  or that are exposed to the call's groups and version, keep being read and
  written under their JSON names; the type a property declares for its value
  keeps deciding how that value is transformed; type discriminators, the
  transformation options and the library's own tests keep working.

## Constraints

- Fix the flaw in the library itself, for every way it can be reached, not only
  the example above. Do not special-case the example's classes, property names
  or values.
- Keep legitimate use working as described above.
- Do not modify or add tests; hidden tests will check the behaviour.
- Do not look up or copy an upstream fix for this issue.

## Notes

The repository is in `/app` with its dependencies installed. There is no
network. The project's own test suite runs with `npx jest` from `/app`.
