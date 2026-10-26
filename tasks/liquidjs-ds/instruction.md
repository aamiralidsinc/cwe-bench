# Rendering can expose values that were never in the caller's data

## The system

This repository is a template engine used as a library. An application creates an engine, parses a
template, and renders it against a scope of data, either synchronously or asynchronously. The same
engine can also be asked to evaluate a template expression, or to resolve a dotted/indexed path,
and return the value directly.

The engine ships with a read restriction that is on by default, for applications that pass it data
they do not fully trust: only an object's own properties may be read out of the scope. Values that
are reachable only through the prototype chain of the supplied data are meant to stay invisible to
templates.

## Observed impact

An application renders an ordinary template against data supplied by an untrusted source while the
default read restriction is in effect. The template looks at a sequence with entries that were
never supplied. Instead of an absent value, the rendered text contains a value the application
never supplied — one that lives on the sequence's prototype chain. The same value can also come
back from the engine when it is asked to resolve the expression directly.

A harmless reproduction: define a marker value on the built-in array prototype, hand the engine a
sequence whose last entry was never supplied, and render a template that reads that entry from the
end. The marker appears in the output.

## What must hold

While the read restriction is in effect (its default), no value that exists only on the prototype
chain of the data supplied to a render may be observable — neither in the text a render produces
nor in a value the engine returns to a caller that resolves an expression or a path. This holds for
every piece of supplied data and for any way a template obtains or derives a value from it.

## Contracts

- **Absence, not disclosure.** A read that would expose such a value must behave as if the value
  were not there: it must not appear in the rendered text and must not be returned to the caller.
  The engine's ordinary behaviour for a missing value applies; no new error is required.
- **Preservation.** Everything that works today keeps working exactly as today. In particular,
  values that are genuinely part of the supplied data stay visible and unchanged — a sequence's own
  elements, a string's characters, and the structural length or size reported for a sequence, a
  string, a set, a map or an object. Custom template objects keep resolving through their own API.
  Turning the read restriction off continues to permit inherited data through the reads it governs.
- **Surfaces.** The relevant public surfaces are the library API: rendering a template, evaluating
  an expression, and resolving a path.

The names and examples above describe how the flaw shows up; they are not the full set. Reason
about the property, not the samples.

## Constraints

- Fix the problem and its close variants, not just the exact example.
- Keep every legitimate use working.
- Do not look up the upstream fix for this issue.
- Do not special-case the example inputs.
