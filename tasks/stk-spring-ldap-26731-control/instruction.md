# Spring LDAP: password-less sign-in is reported as success

Spring LDAP is the LDAP integration library for Spring applications. An application uses it to open
directory contexts and to check a user's password when signing a user in.

## What was observed

An application that signs a user in can be told that the sign-in succeeded even though no password
was checked: `authenticate(query, "")` returns success while no credential was ever verified.

## The property

Through this library, no sign-in that is checked against a password may accept an empty or absent
password for a named user, however the identity and the password reach the library.

## Contracts

- A refused sign-in must fail the way a rejected bind already fails in this library: no bind is
  sent, and the caller sees the library's authentication failure rather than a successful result.
- Every legitimate sign-in keeps working exactly as it does today.
- The example is an example, not the full set.

## Constraints

- Fix the problem and its close variants.
- Keep legitimate use working.
- Do not look up the upstream fix.
- Do not special-case the example.
