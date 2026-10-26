# A visitor's language can send translation requests to a host the application did not choose

i18next-http-backend is a backend for i18next. The application configures where its translation
resources are served, then asks the backend to request them for a given language and namespace. The
language can come from the visitor, through a query parameter, a cookie or a stored preference.

An application whose configured location begins with the language or namespace placeholder, and
which takes the language from the visitor, can be made to request translations from a host the
visitor chooses. The response is handed back to the application as if it were its translations.

## Requirement

No value supplied by a caller may make a request reach a destination other than the one the
application configured.

A refusal has no effect.

These are invariants, not a list of cases. The example above is an example.

## Behaviour that must not change

Everything that works today keeps working exactly as today.

## Constraints

Fix the problem and its close variants. Keep legitimate use working. Do not look up the upstream
fix. Do not special-case the example above.
