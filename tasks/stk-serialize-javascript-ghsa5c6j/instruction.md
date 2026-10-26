# Serialized output that runs supplied code

This project is a JavaScript library that turns a value into a string of literal JavaScript which
rebuilds that value when evaluated. Applications use it for kinds JSON cannot carry — regular
expressions, dates, maps, sets and functions — and embed the returned string in a page or hand it
to another process.

An application that embeds such a string in a page can be made to run code chosen by whoever
supplied the data. Serializing a value that contains a regular expression whose flag text is not
one a regular expression can really carry makes the returned string run that text when the page
evaluates it, even though the data was only ever meant to describe a regular expression.

## Required property

Whatever value a caller passes, the string the library returns must represent exactly the data the
caller asked it to serialize, and evaluating that string must run no code beyond what is needed to
rebuild that data. Nothing a caller supplies may make the output carry code that is not part of
the data.

## Behaviour that must not change

Everything that works correctly today keeps working exactly as today.

## Contracts

- A value the library cannot represent faithfully may be refused by raising an error instead of
  returning a string; the library must never return a string that misrepresents the data or
  carries code that was not in it.
- The example above is an example, not the full set of affected values.

## Constraints

Fix the problem and its close variants. Keep legitimate use working. Do not look up the upstream
fix. Do not special-case the example above.
