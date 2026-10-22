# Names taken from input must never reach an object's prototype

## The system

This repository is a JavaScript library that an application calls in-process.
The application hands it structured input, which may come from a peer, and the
library builds objects, tables and recorded configuration from that input. It
returns those to the application or uses them while doing so. Every name that
appears in such input is therefore an untrusted string.

## What was observed

A caller supplied a name that the JavaScript runtime reserves for an object's
prototype. The object that came back had lost its ordinary prototype: the
caller's value was no longer reachable as data under the supplied name, and
its members instead appeared to belong to the object itself, so every later
lookup on that object saw them.

Relatedly, a name that had never been recorded was sometimes answered with a
property the object merely inherits, and a name that happened to coincide with
such an inherited property was lost, crashed, or was combined with something
inherited instead of with the caller's data.

## The rule

A name the library takes from input is always treated as a name, never as a
way to reach the machinery of the object that holds it.

- **No prototype access.** No such name may be used to reach, read or replace
  the prototype of any object the library builds, returns, stores, mutates or
  reads, and no shared built-in object may be modified.
- **Data is data.** A name the library handles as data is stored as an own,
  enumerable property under exactly that name; its value is reachable under
  that name, and its container keeps the ordinary prototype it has for
  ordinary input. An accepted name is not dropped, renamed or refused.
- **Lookups are exact.** Wherever the library holds names in a lookup and
  consults one, an entry that is not present as an own property is absent. A
  name that was never declared or recorded is reported as invalid: the
  operation fails with an ordinary, catchable error, unless its established
  answer for an absent entry is to report absence, in which case it reports
  absence. It is never answered with a property the object inherits. This
  holds for the objects and tables the library returns, the ones it uses
  internally and the ones it is given, and whether a name is written, looked
  up or read back.
- **Ordinary inherited-looking names are ordinary.** A name that was declared
  or recorded, and that merely coincides with a property every object
  inherits, is ordinary data: it is stored and looked up exactly like any
  other name, in every relation the library keeps for such names.
- **Everything built follows this.** The same rule applies to every object the
  library returns, every name-keyed lookup it consults, and every artifact it
  produces for another program to load.
- **Prototype-replacing names in recorded configuration are ignored.** Where
  the library is recording configuration about what it is building, or
  reading a supplied description of what to build, a name that would replace
  the prototype of the container it belongs to is not stored as data: it is
  ignored, it raises no error, and the rest of that work is carried out
  exactly as it would be without that name.
- **Filling only what is absent.** When the caller asks that only absent
  entries be filled, an entry counts as present only when it is an own
  property; the existing refusal of the names that cannot be stored safely
  (the prototype-replacing name, `prototype` and `constructor`) is unchanged.

## Contracts that must keep working

- Ordinary input behaves exactly as it does today: every accepted entry keeps
  its value and its order, containers keep the ordinary prototype, and
  ordinary name and numeric round-trips are unchanged.
- A refused lookup is an ordinary, catchable failure. The library keeps
  working afterwards and leaves no partial record behind.
- Unrelated existing behaviour is unchanged.

## Constraints

- Fix the problem and its close variants in the library itself, for every
  operation and input surface that can reach it, not only the single case
  above. Do not special-case particular names or values.
- Keep legitimate use working as described.
- Do not modify or add tests; hidden tests will check the behaviour.
- Do not look up or copy an upstream fix for this issue.
