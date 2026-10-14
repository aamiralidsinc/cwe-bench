# SAML response handling: security report

This repository is a Ruby library used by relying-party (service-provider)
applications to process SAML messages received from an identity provider:
decoding them and verifying the identity provider's signature before trusting
their contents. A security review of an application built on this library,
reached only through the library's ordinary public entry points
(`OneLogin::RubySaml::Response`, `OneLogin::RubySaml::SloLogoutrequest`,
`OneLogin::RubySaml::Logoutresponse` and the document signature check they
perform), surfaced the problems below. Please investigate and fix them.

## Observed behaviours

**Forged content accepted as signed.** Starting from a single document that the
identity provider legitimately signed, an attacker can assemble a SAML response
that the library still reports as having a valid signature, even though it now
also carries attacker-controlled content. Concretely, if the response is made to
contain more than one element bearing the identifier that the signature refers
to — the genuinely signed element plus an additional element the attacker
added — the signature check still succeeds. Because the signature is supposed to
be the only thing standing between an anonymous request and a trusted identity,
this lets an attacker who has obtained any one signed document present responses
whose trusted contents they control. The signature verification step must refuse
to treat such an ambiguous document as validly signed; only genuinely signed
material may be accepted.

**Tiny message, huge expansion.** SAML messages may arrive compressed. A very
small compressed, encoded message can be crafted so that it expands into an
enormous document when the library decodes it. The library decodes and keeps the
whole expanded result, so a short attacker request turns into a large memory and
CPU cost, which can be repeated cheaply to exhaust the service. Decoding must be
bounded so that a message whose decoded size exceeds the configured limit is
rejected rather than fully expanded and processed.

**Oversized input processed before it is rejected.** A greatly oversized message
is scanned and parsed before any size limit is applied, so an attacker can impose
large processing costs simply by sending bulky input, regardless of how it is
encoded. Oversized messages must be refused up front, before that expensive work,
whatever their encoding.

## What must keep working

A genuinely and correctly signed SAML response must continue to validate, and its
identity/attributes must remain readable. Normally sized messages — including
legitimately compressed ones — must continue to decode and be processed as before.
A correct fix closes all of the issues above without breaking this behaviour.
