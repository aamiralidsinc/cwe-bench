# Request input can change properties declared read-only

## The system

Our account service uses the JSON data-binding library in `/app` to bind
untrusted request bodies to Java objects: to create new objects, and to apply
partial updates to objects that already exist
(`mapper.readerForUpdating(existing).readValue(body)`,
`mapper.updateValue(existing, body)`). Values that only the server maintains
are declared read-only, with `@JsonProperty(access = JsonProperty.Access.READ_ONLY)`
or with `@JsonIgnoreProperties(value = {...}, allowGetters = true)`. Clients see
them in responses but must never set them. For partial updates, some of our
mappers merge nested objects instead of replacing them, for example with
`mapper.setDefaultMergeable(true)`.

## What we observed

An account has a read-only quota object (with fields `limit` and `used`):

```java
public class Account {
    public String name;
    private final Quota quota = new Quota();

    @JsonProperty(access = JsonProperty.Access.READ_ONLY)
    public Quota getQuota() { return quota; }
}
```

The mapper has `setDefaultMergeable(true)`. A client sends
`{"quota": {"limit": 1000000}}`, and the service applies it with
`mapper.readerForUpdating(account).readValue(body)`. Afterwards
`account.getQuota().limit` is 1000000.

This is one example, not the whole problem. Other types and other ways of
reading input let read-only values through in the same way.

## Required behaviour

- No input may set a property declared read-only, however the object is
  built, populated or updated, and whatever the type looks like. This includes
  changing the contents of an object, collection or map that the property
  holds. The property keeps the value it had before the read. On a new object,
  it keeps the value it has when the input does not mention it.
- Input aimed at a read-only property is ignored without an error.
- Serialization is unchanged: read-only properties are still written out.
- Everything else binds exactly as it does today. This includes writable
  properties (also a writable property that shares its JSON name with a
  read-only one), merging into writable nested objects, and input that is not
  aimed at a read-only property, wherever that input is delivered today.

## Constraints

- Fix the flaw in the library itself, for every way input can reach a
  read-only property, not only the example above. Do not special-case the
  example's types, field names or values.
- Keep legitimate use working as described above.
- Do not modify or add tests; hidden tests will check the behaviour.
- Do not look up or copy an upstream fix for this issue.

## Notes

The repository is in `/app`. There is no network. You can confirm that the
library still compiles with `/opt/verify/compile-lib.sh`.
