# A member may construct a class named by client data only when that class is eligible

## System

Hazelcast is an in-memory data grid. Members and clients exchange values using
Hazelcast's Compact serialization. A Compact value carries a schema, and the
schema's type name identifies the value's type. When a member reads a value it
looks the type name up; for a type that is not registered explicitly it can
fall back to zero-configuration serialization: it constructs an instance of
the class named by the type name and fills its fields from the bytes.

## Observed impact

A low-privileged client whose data a member deserializes chooses the class the
member constructs while reading that data. The member applies zero-configuration
serialization to whatever class the type name happens to denote, including
classes that are not part of the application's data model and classes that are
already handled by another serialization mechanism. For example, a client can
send a value naming a platform or JDK class and have that class constructed on
the member instead of the value being kept as data.

## Security property that must hold

No class named by data received from a client may be constructed — not even
transiently, before it is found eligible — unless that class is eligible for
zero-configuration Compact serialization on that deployment. A class is not
eligible when it is already serialized by another mechanism, when it belongs to
the platform's own implementation rather than to the application's data model,
or when the deployment's configuration excludes it. The platform's own
implementation covers every package the platform ships, whatever that package
is called. The rule holds however the data is encoded and wherever within it
the name appears. Ineligible data, and data naming a class that is not present
on the classpath, must never be delivered as an instance of the named class;
when the value can be read at all it must be delivered as a generic record that
keeps the same type name and fields.

The example above is illustrative, not an exhaustive list of ways the property
can be violated.

## Contracts the fix must honor

- **Normal read, not an error.** Reading a value whose type name is ineligible
  or unknown normally returns a generic record; a caller must not have to catch
  an exception to observe it. When ineligibility is found while reading a value
  contained within another, the containing value must still be delivered as a
  generic record whenever it can be represented as one; only when no
  generic-record form of the containing value exists may the read fail cleanly,
  and even then the named class must never be constructed.
- **No construction at all.** The named class must not be constructed before
  the decision — neither through a constructor nor through an allocation that
  bypasses constructors.
- **Preservation.** Ordinary user classes with no other serialization
  mechanism keep deserializing directly exactly as today, wherever they occur
  within a value, with ordinary sizes and field counts. Classes registered
  explicitly in the Compact serialization configuration keep using the Compact
  serializer even when another mechanism applies to them. Java serialization
  of serializable classes is unchanged, and unknown type names keep reading as
  generic records.
- **Default for every service.** Every serialization service the platform
  builds must apply the rule without the deployment opting in.

## Constraints

- Fix the flaw and its close variants, not just the shape shown.
- Keep every legitimate use working.
- Do not special-case the example input.
- Do not consult any upstream advisory or fix for this issue.
- There is no network access.
