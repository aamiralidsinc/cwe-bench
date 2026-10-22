# Untrusted names in Protocol Buffer input can replace the prototype of a returned object

## The system

`/app` is a JavaScript Protocol Buffer library. Applications use it to compile
`.proto` schemas, parse messages that arrive in the text format and in JSON,
build schema objects programmatically, import descriptor sets at runtime, merge
incoming input into objects they already hold, and generate static code from a
schema. Every object the library hands back to an application is keyed by names
that appear in that input or in that schema.

## What we observed

A service accepts text-format messages from its clients and hands the parsed
message to its own code. A client sends

    labels { key: "__proto__" value { admin: true } }

and the map that comes back is not the map the service expected: the entry is
not present as data, `admin` shows up as a property of the map itself, and every
later lookup on that map sees it. If the service decides anything from that map,
the client's values reach that decision along a path the service never wrote.

The same confusion shows up wherever a name from input or from a schema becomes
a key on an object the library builds or keeps — a map entry, a message field,
an enum identifier, an option or setting name, a descriptor entry, a table the
library emits.

## Security properties that must hold

- No name the library takes from input may reach or read the inherited shape of
  any object the library returns or stores. A name accepted as data is stored
  under that name as ordinary own, enumerable data, with its value readable
  under that key, and the container keeps the same shape it has for ordinary
  input. No shared built-in object may be modified.
- A name that is not declared is reported as invalid. It is never resolved to a
  value the container happens to inherit.
- A declared name that happens to coincide with a name every object inherits is
  an ordinary name: map keys, fields, enum values, options and settings with
  such a name must parse, be stored and be readable exactly like any other name.
- Reading a setting that was never set reports it as absent. It never returns
  an inherited value. Writing a setting stores the value under the name given.
- Rules the library applies at runtime apply equally to anything it emits as
  code.

This holds however the name arrives, and for every operation the library offers
— compiling a schema, parsing a message in either wire format, building or
importing schema objects, reading and writing settings, merging input into an
existing object, and generating code. The example above is one instance, not
the full set of ways the properties can be violated.

## Contracts the fix must honor

- **Refusal form.** When the library rejects input it reports an ordinary
  error: the caller gets an exception, the library keeps working afterwards, no
  partial result is left behind, and no shared built-in object is touched.
- **Accepted form.** When the library accepts input, the data it names is
  present under the names given. A map entry named `__proto__` is stored as an
  ordinary own entry whose value is reachable under that key. The map itself
  keeps the shape an ordinary JavaScript object has — a bare container with no
  inherited behaviour, or a map that drops or refuses the entry, does not
  satisfy this report.
- **Preservation.** Ordinary messages, schemas, descriptors, merges and
  generated modules keep working exactly as today. Maps with any number of
  ordinary entries parse as today. An enum's numeric-to-name lookup keeps
  working, and ordinary enum import and export are unchanged. Settings that
  were set are readable; settings that were not set read as absent.
- **Generality.** The example names are one instance. The same rule covers
  other names with the same character, other shapes of the same input, and the
  other operations named above.

## Constraints

- Fix the problem and its close variants, not just the request shown.
- Keep every legitimate use working.
- Do not modify or add tests, and do not special-case the example input.
- Do not consult any upstream advisory or fix for this issue.
