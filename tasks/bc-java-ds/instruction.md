# Name constraints in certificate path validation

Bouncy Castle (`bc-java`) is a cryptography library for Java. Applications use its `PKIX`
`CertPathValidator` (from the `BC` provider) to decide whether a certificate chain can be trusted.
A CA can attach X.509 name constraints to its certificates to restrict the names its subordinates
are allowed to certify, and the validator is expected to enforce them.

A certificate for `ceo@bank.com.` validates on a chain whose issuing CA excludes the mail host
`bank.com`. The address is the same mailbox the CA forbade; it is written as a fully qualified name
with the root label spelled out. An attacker who can obtain a certificate from such a CA can
therefore present an identity the CA meant to forbid, and any client that trusts the validator's
verdict accepts it.

## What must hold

No certificate path may be accepted when any certificate in it carries a name that lies outside the
permitted names its issuers allow, or inside the names they exclude. This holds for every kind of
name a certificate can carry, and for every way such a name can be written: two spellings of the
same name must reach the same decision, and a constraint that applies to a name must apply wherever
the certificate carries that name.

A path that violates the constraints is refused by throwing
`java.security.cert.CertPathValidatorException`.

Paths that satisfy the constraints keep validating. The meaning each form of a name constraint has
today must not widen or narrow: a constraint that names one host still covers exactly that host, a
constraint written as a domain still covers names below it, and any matching behaviour a deployment
has explicitly opted into keeps working when it is enabled.

The names in this report are examples, not the full set.

## Constraints

Fix the problem and its close variants. Keep legitimate use working exactly as it does today. Do
not look up the upstream fix for this report, and do not special-case the example names.
