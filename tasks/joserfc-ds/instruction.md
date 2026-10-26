# Empty shared secrets authenticate tokens

`joserfc` is a Python library for JSON Web Signature, JSON Web Encryption, JSON Web Key and
JSON Web Token. Applications use it to sign and verify HMAC-based access tokens (HS256,
HS384, HS512) and to manage the shared secret that backs them.

## Observed impact

Our authentication service verifies HS256 access tokens with a shared secret read from the
environment. When the variable is unset, the secret is the empty string, and a token whose
signature was computed from that same empty value is accepted as valid. We confirmed that a
token carrying `{"sub": "admin"}` was treated as authenticated, so anyone can mint a token
with any claims without knowing a secret.

## Required behaviour

**An empty secret must never authenticate anything.** Whether it is supplied to the library,
produced by it, or transformed by it before use, an empty secret must fail with a client error
instead of yielding a key, a signature, or an accepted token.

Secrets that do contain key material must keep working exactly as today. In particular, short
secrets that the library already accepts with a warning must keep warning and keep working;
refusing them is a regression, not a fix.

The rule applies to every HMAC algorithm and to every public path that takes, returns, or uses
key material. The example above is one way to reach the problem, not the full set.

## Contracts

- A refusal is a raised exception. The library must not return a key, a signature, a token
  object, or an accepted result in its place, and it must not fall back to accepting
  unverified input.
- Legitimate values keep their current behaviour exactly: the same inputs produce the same
  tokens and verify the same way.

## Constraints

Fix the problem and its close variants. Keep legitimate use working. Do not look up the
upstream fix. Do not special-case the example.
