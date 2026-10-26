# Cleaned markup can still mean something else to a browser

AntiSamy is a Java library that cleans untrusted HTML and CSS before an application puts the
result into a page. An application passes it a policy and the untrusted input, and receives the
cleaned markup it will display.

## What was observed

A page that stored the cleaned output of the following comment was served a fragment containing a
working `javascript:` link, so a visitor's browser ran the link's code:

    <style/>b<![cdata[</style><a href=javascript:alert(1)>test

## Required property

Whatever a client supplies, a browser that renders the markup the library returns must end up with
exactly the content the policy validated, and nothing else. The returned markup must never take on
a meaning that the validation did not approve.

## Contracts

- Cleaning does not fail with an unexpected error on input it accepts today. Whatever the library
  cannot approve is left out of the returned markup and reported; no part of it reaches the output
  in a form the browser treats as approved.
- Everything that works today keeps working exactly as today. Values the policy approves keep
  their meaning, and markup that renders correctly today keeps rendering the same way.
- The example above is an example, not the full set of inputs, values or forms that must be handled.

## Constraints

Fix the problem and its close variants. Keep legitimate use working. Do not look up the upstream fix
or an existing implementation. Do not special-case the example above.
