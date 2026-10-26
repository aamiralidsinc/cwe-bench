# Private-key arithmetic is not independent of the key

## System

phpseclib is a pure-PHP cryptography library used by PHP applications, frameworks and
command-line tools. Among other things it implements the X25519 and X448 elliptic
curves: given a private scalar it derives the matching public key, and it computes an
ECDH shared secret from a private scalar and a peer's public point. It can do that work
in PHP itself or hand it to a native cryptography provider, and callers can select
which provider is used.

## Observed impact

The amount of arithmetic the library performs while handling a private scalar is not
constant. For two different private keys of the same curve, the same operation issues a
different number of big-number operations, so a local observer that measures timing, or
counts entries into the big-number provider, can learn the scalar and recover the
private key.

For example, deriving the public key from two 32-byte X25519 private keys performs a
visibly different amount of arithmetic when one key's leading bytes are small and the
other's are large.

## Security property that must hold

For any two valid private scalars of the same curve, the sequence and number of
arithmetic operations the library performs while handling either of them — deriving a
public value, deriving a shared secret, or validating the scalar — must be identical.
No secret value may decide which arithmetic runs or how often it runs.

## Required contracts

- Derived public keys and shared secrets stay byte-for-byte correct and match the
  standard published test vectors for each curve.
- Every curve, key form and operation that works today keeps working and keeps
  producing the same results. In particular, a key that is already valid must not start
  being rejected.
- The engine-selection API keeps its documented behaviour: a forced engine performs the
  work, forcing an engine that cannot support a curve still fails as it does today, and
  the pure-PHP engine keeps working when it is selected even if no native extension is
  present.
- Rejecting an invalid key is not a violation of the property; the requirement applies
  to valid keys.

These are examples, not the full set of inputs, curves, key forms or call paths that the
property covers.

## Constraints

- Fix the problem and its close variants; keep legitimate use working.
- Do not look up the upstream fix or existing implementations.
- Do not special-case the examples.
- There is no network access.
