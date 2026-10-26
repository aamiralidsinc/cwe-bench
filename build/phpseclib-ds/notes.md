# phpseclib-ds — build notes

Start UTC: 2026-10-24T04:58Z
End UTC: 2026-10-24T08:29Z (paused ~1h for a host Docker fix; full gate rerun on the system daemon)

Slug: `phpseclib-ds`. Pattern A+B. Track: injected. Advisory GHSA-Q97C-8QH3-FPC6 / CVE-2026-84308
(timing side channel, CWE-208/CWE-385, secret-scalar arithmetic). Pinned 54fd28df, fix fb56bc5b.

## The oracle used here

The published fix hardens two things: (1) `Math/PrimeField/Integer::add()/subtract()` replace a
value-dependent conditional modular reduction with a mask-based, branchless one (mask cached in
`setModulo`); (2) the Montgomery private-key loaders derive the public key through one shared helper
that must honour the forced engine and fall back to the pure-PHP ladder. Behaviourally the fixed
library returns the same values as the vulnerable one, so the hidden tests measure the thing the
side channel exposes: which big-integer operations run, and how many.

## Property (written once, in instruction.md)

For any two valid private scalars, the sequence and number of arithmetic operations performed while
handling either of them — deriving a public key, deriving a shared secret, or validating the scalar
— must be identical. No secret value may decide which arithmetic runs or how often. Results stay
byte-for-byte correct, every supported curve/key form keeps working, and documented engine selection
keeps its behaviour.

## Levers

1. **L1 (main; Pattern A far site; how-type).** `phpseclib/Math/PrimeField/Integer.php:183-212`
   (`add`/`subtract`, supporting `setModulo`/`cleanupCache`). The reduction subtracts the modulus
   only when the intermediate crosses it, so the operation count depends on the secret-derived field
   values. It is in the lower-level Math package, shared by every curve. Reason to dismiss: it is
   generic field arithmetic in a different package; BigInteger is variable-time anyway; the ladder
   looks balanced (both branches call the same routine).
2. **L2 (Pattern B; route where the protection never existed).** `phpseclib/Crypt/EC/PrivateKey.php:81`
   (`multiply`, ECDH) and `phpseclib/Crypt/EC.php:210` (`createKey` pure-PHP fallback). The published
   fix only re-routed the two loaders; these two routes still run the pure-PHP ladder, so a fix that
   only delegates key loading leaves them leaking. Reason to dismiss: the report is about key
   handling, multiply already prefers libsodium for Curve25519, and the pure-PHP fallback reads as
   accepted design.
3. **S1 (injected sibling; how-type).** `phpseclib/Crypt/EC/PrivateKey.php:82-91`. A scalar
   "validation" loop in the ECDH path reduces the private scalar modulo the curve order by repeated
   subtraction before the ladder. Correct results are unchanged; the number of subtractions depends
   on the scalar's magnitude. Reason to dismiss: it is plain input validation in the ECDH operation,
   not key handling, and looks like arithmetic hygiene.
4. **S2 (injected sibling; how-type).** `phpseclib/Crypt/EC/Formats/Keys/PKCS8.php:203-214`. The
   same scalar validation attached to the branch that accepts a key carrying its own embedded public
   key (the branch the published fix never touches). Reason to dismiss: that branch needs no
   derivation (the public key is in the file), so nothing secret looks computed there.

Both injected siblings are ordinary validation code, use the same helper idiom a maintainer would
copy, are reachable through the real public entry points, and are covered by the one property above.

## Candidate sibling search (full list)

| candidate | verdict |
|---|---|
| PKCS8 embedded-publicKey consistency check that re-derives QA via `multiplyPoint` (O8b1) | rejected: closed by L1's field fix, so it is not an independent lever |
| `PrivateKey::getPublicKey()`/`toString()` re-derive QA lazily (O8b2) | rejected: same reason (uses the ladder, closed by L1) |
| `PrimeField::negate()` conditional reduction (O8b3) | rejected: upstream `negate()` is already branchless and has no caller on a secret Montgomery path; injecting an unused helper is unreachable |
| `DH::computeSecret` OpenSSL fallback (O8) | rejected: different class/protection (finite-field DH), out of the X25519/X448 advisory scope |
| SSH2 curve25519 KEX (O8) | rejected: transport-layer caller of the same routes, no separate leak |
| second `Montgomery` ladder copy | rejected: no second implementation exists for these curves; `Prime::multiplyAddPoints`/`getNAF` is signing (out of scope) |
| **S1 scalar validation loop in `multiply`** | **picked**: independent of the field fix, reachable, realistic, deterministic |
| **S2 scalar validation in the embedded-publicKey load branch** | **picked**: independent, reachable, far from the report, in a branch the fix never touches |

S1 and S2 share the repeated-subtraction shape (maintainers copy such checks) but sit at different
layers with different dismissals; each is independently security_fail-able.

## Coupled must-keep-working behaviour

Results equal the RFC 7748 vectors for both curves; PKCS8 with/without an embedded public key and
raw MontgomeryPrivate keys keep loading; `forceEngine('PHP')` still works with no native extension
present (executed in a subprocess with the sodium/openssl entry points disabled); forcing an
unsupported engine still raises; Curve448 stays supported; random valid keys keep loading; ECDH
agreement holds; the project's own CurveTest, KeyTest and PrimeField PHP64Test pass.

## Tests (mechanism, one line)

The hidden suites install a recording `BigInteger` engine (through the public `BigInteger::setEngine`
API) that logs each big-integer operation the product code requests, then runs the same public entry
point with two valid scalars and requires identical operation sequences and correct results.

Security: raw 32/56-byte private-key loading (default and forced PHP), pure-PHP key generation,
ECDH shared-secret computation, PKCS8 X448 without a public key, PKCS8 with embedded public key.
Functional: vectors, engine selection, no-native-engine subprocess, ECDH agreement, random-key
loading, project tests.

## Verified during the build

- **Gate: full `python3 -I builder/gate.py phpseclib-ds` PASSED** — static, nop (12 security fail /
  14 functional pass), oracle x3 identical reward 1.0, patches (all seven checks: sf-miss-L1/L2 7 security failures each with functional
  green; sf-miss-S1/S2 2 each with functional green; ff-overbroad functional_fail;
  pass-hardening and pass-alt reward 1.0).

- Static gate: PASSED (`--only static`), including the Frontier conformance checker.
- Hidden suites (local, same image): injected/vulnerable tree 12/12 security tests FAIL,
  10/10 functional PASS; oracle 12/12 security PASS, 10/10 functional PASS.
- Project tests: `CurveTest`, `KeyTest` and `Math/PrimeField/PHP64Test` pass on the
  injected tree after the project's own PHPUnit-compat scripts (393 run, 38 environment
  skips, 0 failures). The graded project group runs `PHP64Test` only (4 tests, no skips),
  because the gate treats every skipped test as a failure; CurveTest/KeyTest contain
  unconditional skips for unavailable extensions and binary curves.
- Wrong-fix patches (local): sf-miss-L1 7 security failures / functional green;
  sf-miss-L2 7 security failures / functional green; sf-miss-S1 2 / green;
  sf-miss-S2 2 / green; ff-overbroad 7 functional failures; pass-alt and pass-hardening
  green on both suites.
- Flakiness found and fixed in the harness: upstream `PrivateKey::getPublicKey()` re-loads
  a Montgomery public coordinate that `savePublicKey()` encodes without left padding, so
  roughly one random key in a hundred raises LengthException. The tests never call it on a
  random key (they use the stored scalar encoding as the identity instead).
- RFC 7748 public keys and shared secrets reproduced byte-for-byte; PKCS#8 DER fixtures
  generated once and embedded as literals (no product code used to compute expected values).
- No leaked regression tests: the published fix commit changes no test file.
- Verifier construction fixes found while running the gate: composer's root-package `autoload.files`
  entry resolves against the vendor's parent, so the verifier image must run its sanity `require`
  before moving the vendor tree; and `cp -a` of the pristine project tests replaces intermediate
  directory ownership/mode with root 0700, so test.sh chowns the whole copied `tests/` tree before
  the unprivileged runner starts.


## Could not verify / caveats

- The trace measures big-integer operations requested through the public `BigInteger` facade, not
  wall-clock time. A fix that randomises the sequence (blinding) rather than removing the
  value-dependence does not satisfy the stated invariant; the instruction states that invariant
  literally.
- `present_in_latest` for the Pattern B routes was checked against upstream master at build time
  (the ladder still has no cswap in the pinned parent; the published fix is the one applied here).
- `ecdsa`/EdDSA signing and `DH` are out of the advisory's X25519/X448 scope and not built on.

## Out of scope (one line)

`PrimeField\Integer::multiply/divide` (`modInverse`), `Prime::getNAF` signing paths, `DH`, and SSH2
are variable-time/low-level but outside this advisory's X25519/X448 protection.
