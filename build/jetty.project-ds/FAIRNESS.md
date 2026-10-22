# FAIRNESS — jetty.project-ds

Shorthands: **PROP** = "No value may establish an account's identity unless it is exactly that account's secret … two distinct values must never both authenticate … however the value is presented, and however the account's secret is held." **REF** = "A rejected login is an ordinary client error (any 4xx)…" **PRES** = "Every legitimate login keeps working…" **SK** = standard expert knowledge.

## 1. Test fairness

| Test (file::name) | Asserts | Covering sentence | Could a correct fix fail? | Risk |
|---|---|---|---|---|
| SecurityDigestEncodingTest::wrongPasswordThatCollapsesUnderTheLegacyEncodingIsRejected | secret `pa€`; digest for `pa?` → 4xx, no marker | PROP (however presented) | no — UTF-8 or an unrepresentable guard → 401; any 4xx accepted (REF) | low |
| SecurityDigestEncodingTest::…WhenAlgorithmIsOmitted | same, no `algorithm=`, default branch | PROP | no — same core fix; algorithm-keyed guard is the caught wrong fix | low |
| SecurityDigestEncodingTest::wrongPasswordIsRejectedWhenTheStrongerDigestAlgorithmIsSelected | challenge advertises SHA-256; wrong `pa?` → 4xx | PROP + SK (a challenge advertises the algorithm computed with) | no — UTF-8 there passes; deleting the feature breaks PRES | low |
| SecurityStoredCredentialEncodingTest::…StoredDigest | stored `MD5:` of `pa?`; `pa€` → 4xx | PROP (however held) + REF | no — UTF-8 or reject-non-ASCII in `MD5.check` | low |
| SecurityStoredCredentialEncodingTest::…StoredStrongDigest | same for `SHA256:` | PROP | no — same in `SHA256.check` | low |
| SecurityStoredCredentialProducerTest::wrongPasswordIsRejectedWhenTheStoredDigestWasProducedFromANonAsciiSecret | `MD5.digest(pa€)` non-null, `MD5:`-prefixed; `pa?` → 4xx | PRES + PROP | no under the primary mechanism: the natural producer fix keeps the format, hashes UTF-8. A refuse-to-mint or renamed-format fix fails the prefix assertion; that is a redesign, not the stated mechanism (Human review) | low |
| SecurityConfiguredSecretExactnessTest::valueThatDropsAConfiguredCharacterIsRejected | configured `pa? `; `pa?` → 4xx | PROP (however held) | no — only the loader can preserve it | low |
| SecurityUnrepresentableSecretTest::valueThatCollapsesOntoAnUnrepresentableSecretIsRejected | configured `pa`+lone surrogate; `pa?` → 4xx | PROP, literally | no — guard in digest, `Password`/`UserPrincipal`, or loader all pass | low |
| SecurityEe9DigestEncodingTest::wrongPasswordThatCollapsesUnderTheLegacyEncodingIsRejected | servlet copy: wrong `pa?` → 4xx | PROP (route-blind) | no — same fix in the second implementation | low |
| FunctionalDigestEncodingTest::correctPasswordIsAccepted | `password` accepted | PRES | no | low |
| FunctionalDigestEncodingTest::nonAsciiPasswordIsAcceptedWithTheServerEncoding | `pa€` accepted under ISO-8859-1 or UTF-8 | PRES | no — UTF-8 agreement passes; only a third convention fails, and Digest conventions are those two (SK) | low |
| FunctionalDigestEncodingTest::preHashedDigestCredentialIsAccepted | pre-hashed `MD5:` used as H(A1), not re-hashed | PRES | no — rehash is forbidden | low |
| FunctionalDigestEncodingTest::correctPasswordIsAcceptedWithTheStrongerAlgorithm | SHA-256 challenge; correct password accepted | PRES + SK | no | low |
| FunctionalBasicEncodingTest::correctPasswordIsAccepted | `password` accepted | PRES | no | low |
| FunctionalBasicEncodingTest::nonAsciiPlainPasswordIsAccepted | `pa€` accepted | PRES | no | low |
| FunctionalBasicEncodingTest::storedDigestCredentialIsAccepted | stored ASCII `MD5:` accepts `password` | PRES | no | low |
| FunctionalBasicEncodingTest::storedStrongDigestCredentialIsAccepted | stored ASCII `SHA256:` accepts `password` | PRES | no | low |
| FunctionalConfiguredSecretTest::ordinaryConfiguredSecretIsAccepted | configured `password` accepted | PRES | no | low |
| FunctionalConfiguredSecretTest::nonAsciiConfiguredSecretIsAccepted | configured `pa€` accepted | PRES | no | low |
| FunctionalUnrepresentableNeighbourTest::supplementaryCharacterSecretIsAcceptedWithAnAgreedEncoding | configured `pa😀` accepted either way | PRES | no — rejecting all surrogates is over-broad, contrary to PRES | low |
| FunctionalEe9DigestEncodingTest::correctPasswordIsAccepted | servlet copy: accepted | PRES | no | low |
| FunctionalEe9DigestEncodingTest::nonAsciiPasswordIsAcceptedWithTheServerEncoding | servlet copy: `pa€` accepted | PRES | no | low |
| FunctionalEe9DigestEncodingTest::preHashedDigestCredentialIsAccepted | servlet copy: pre-hashed `MD5:` accepted | PRES | no | low |

## 2. Leniency (QUALITY)

| Property / trap | Most plausible wrong fix | Caught by |
|---|---|---|
| P1 exactness, P4 magnitudes | normalize, or fix only the reported sink | S1/S2/S4; `sf-normalize-only`, `sf-miss-core-digest` |
| P2 refusal form | throw on failure (500) | every security test via `isClientError`; `ff-crash` |
| P3 preservation | refuse all / reject non-Latin-1 / rehash | F1–F14; `ff-refuse-all`, `ff-overbroad`, `ff-rehash` |
| reported_digest | fix only that branch | S1/S2; `sf-miss-core-digest` |
| servlet_second_implementation | core-only fix | S9; `sf-miss-servlet-digest` |
| stored_digest_credential_route | authenticator-only fix | S4; `sf-miss-stored-digest` |
| stronger_digest_algorithm_injected | default-MD5-only fix | S3; `sf-miss-strong-algorithm` |
| stored_strong_digest_injected | `MD5:`-only fix | S5; `sf-miss-stored-strong-digest` |
| stored_credential_producer | fix checks, not the producer | S6; `sf-miss-producer-digest` |
| configured_secret_exactness | fix comparison, keep the trim | S7; `sf-miss-config-exactness` |
| unrepresentable_secret_shape | UTF-8 without `canEncode` guard | S8; `sf-miss-unrepresentable` |

Not caught: (i) trimming/refusing whitespace-bearing configured secrets, leaving the exact `pa? ` unusable (S7 never authenticates the exact value); (ii) a 4xx that still creates a side effect; (iii) rejecting all non-ASCII in `Credential.MD5/SHA256.check` (passes S4/S5, F7/F8).

## 3. Hints (QUALITY)

| Quote | Problem | Neutral wording |
|---|---|---|
| "A secret already held in a one-way form must be used exactly as held and must not be recomputed." | names the stored-credential form; neutralizes the rehash fix | "Every legitimate login keeps working; credentials a deployment already holds must keep authenticating the same clients." |
| "A secret containing characters that the server does not represent faithfully must remain usable when the client and server agree on how those characters are represented." | paraphrases the fix approach | delete; covered by "Every legitimate login keeps working" |
| "the attack presents a value that differs by one character the server does not represent faithfully" | restates the mechanism | "the attack presents a different value that the server treats as the same value" |

## 3a. Required: generalize

- "This project is a Java web server and servlet container." — names the servlet-container surface where the second implementation lives, in product terms. Reword: "This project is a Java server."

## 4. Realism (QUALITY)

The digest sink, servlet copy, `Credential.MD5.check`/`.digest`, `PropertyUserStore` trim and encoder replacement are real, unmodified upstream code reachable over real HTTP/config; none is "beyond the advisory". The injected SHA-256 siblings are plausible maintainer additions reachable via `setAlgorithm`/`getCredential`; each is a whole small feature, slightly engineered but not contrived. The lone-surrogate config is unusual, but the path is real.

## 5. Verdict

Gate a: the primary correct fix — UTF-8 at every credential-derived comparison, an unrepresentable-value guard, and preserving the configured value — passes all 23 tests; `pass-alt`, `pass-hardening`, `pass-blind` show other valid layers also pass. REF frees status/message (any 4xx). The producer/config routes are covered literally by PROP ("however the account's secret is held"), so they do not fire gate a. The sole over-constraint, the producer's `MD5:` prefix, is satisfied by the stated-mechanism fix. **Required changes to remove unfairness: none.**

**Quality to tighten:** add an exact-secret success case to S7 (`pa? ` must authenticate); add a functional login with a non-ASCII secret stored as `MD5:`/`SHA256:`; assert refusal leaves no session; relax the producer prefix assertion to "parseable by `Credential.getCredential`". Re-verify `sf-miss-*` expectations if the first two are added.

**Human review:** confirm that requiring `Credential.MD5.digest` to return an `MD5:`-prefixed value is acceptable, since a format-changing correct fix would fail that one assertion.

GATE_A: READY
NEEDS_HUMAN_REVIEW: YES
