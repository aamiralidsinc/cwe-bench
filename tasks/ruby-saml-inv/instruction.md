# SAML sign-in and sign-out handling: security report

Our web application signs users in through our identity provider (IdP) using
SAML. It relies on the Ruby SAML service-provider library in `/app` to accept the
IdP's messages (login responses, logout requests and logout responses), decode
them, and verify the IdP's signature before trusting who the user is.

## What we observed

In a review, an attacker who had captured one response genuinely signed by our
IdP got altered responses accepted as signed. For example: take that signed
response and add, next to the signed assertion, a copy of it that carries the
same identifier but names `attacker@evil.example` as the user. The library's
signature check still reports the response as validly signed.

Crafted requests to the SAML endpoints, some of them tiny, also made the
application spend large amounts of memory and CPU before anything was refused.

## Security properties the library must keep

- A document is reported as validly signed only when its signature designates,
  without ambiguity, the single element it covers, and that element is exactly
  what the IdP signed. A document in which the signed identifier could refer to
  more than one element must never be reported as validly signed by any of the
  library's signature checks.
- The library's configurable maximum message size, at its current default,
  applies to every kind of message, whatever form it arrives in.
- No message, however it is encoded or compressed, may lead the library to parse
  or otherwise process content larger than that maximum. A message that is over
  the maximum as received, or that grows past it when decoded, is refused before
  it is parsed.
- Refusing a message that is over the maximum as received costs almost nothing:
  it happens before the library reads through the message's contents.
- A refusal takes the form the library already uses for over-size messages: an
  error is raised when the message is handed to the library, and no message
  object is returned.

## What must keep working

- Correctly signed responses still verify, pass full response validation, and
  expose the user's identity and attributes as today.
- Normally sized messages, in every form the library accepts today (compressed
  ones included), are decoded and processed exactly as today.

## Constraints

- Fix the library so that the attack above and close variants of it no longer
  work, while legitimate use keeps working. Blocking only the example, or
  disabling signature checking or message decoding, is not a fix.
- Do not modify or add tests.
- Do not look up the upstream fix.
