# SENAITE: unauthorized record changes and executable record text

SENAITE is a laboratory information management system. Lab staff and client
programs use its integration API to look at records and to change them.

Two problems are reported.

**Anyone can change data they have no right to change.** A signed-in analyst
who may not edit a request's title still changes it through the integration
API update; the value is stored. A caller who is not signed in can do the
same.

**Record text is executed.** A record value can be sent as text in the format
the product already accepts. When that text contains an expression, the API
runs the expression while handling the request instead of storing the text as
data, so arbitrary operations run with the server's privileges.

## Required behaviour

1. A caller must not be able to change data the caller is not permitted to
   change. Such a request is refused and leaves the stored data untouched.
2. A record value supplied as text is data and must never be executed.

## Contracts

- A refusal is a client error (an error response or an exception) and has no
  effect on the stored data.
- Everything that works today keeps working: legitimate requests are not
  refused, and the product keeps returning the information it returns today.

## Constraints

- Fix the reported problems and their close variants.
- Keep legitimate use working exactly as it works today.
- Do not look up the upstream fix.
- Do not special-case the examples above.
