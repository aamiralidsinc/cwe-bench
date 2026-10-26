# A written field can land on an object's prototype

This project is a small JavaScript library for reading and writing nested values in plain objects.
An application gives the library a name for a nested location, and the library walks or builds the
nested structure. Such names are usually chosen by a caller, not by the application.

An application stores a user-chosen setting at the nested location the user names. With the name

```
profile.__proto__.isAdmin
```

and the value `true`, the write completes. Afterwards `profile.isAdmin` reads as `true` although
nothing was stored for it, and it is not an own field of `profile`: it is absent when the object's
own fields are listed or checked. `profile` is no longer an ordinary object, because its prototype
has been replaced with an object influenced by the caller. Code that reads a field without checking
ownership accepts the attacker's value; code that lists own fields does not see it.

## Requirement

Every value the library writes on behalf of a caller must land as an own field of the object the
caller's name designates. No caller-supplied name may cause a value to be written onto a prototype
object, and no caller-supplied name may replace the prototype of any object. This is an invariant,
not a list of cases. The example above is an example.

## Behaviour that must not change

- Everything that works today keeps working exactly as today.
- When the library declines to act on a caller-supplied name, skipping it or raising an error are
  both acceptable, as long as nothing is written and the process keeps running.

## Constraints

Fix the problem and its close variants. Keep legitimate use working. Do not look up the upstream
fix. Do not special-case the example above.
