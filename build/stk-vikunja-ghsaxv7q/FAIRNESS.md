# Fairness review — stk-vikunja-ghsaxv7q

Read: `tasks/stk-vikunja-ghsaxv7q/instruction.md`, all of `tests/` (security, functional, support, pristine, `test.sh`, `score.py`), `solution/fix.patch`, `manifest.json`, `notes.md`, `checks/*.patch`. Nothing was run; no upstream lookup.

## 1. Test-by-test fairness

| Test (file::name) | What it asserts | Instruction sentence that makes it fair | Could a correct fix fail it? | Risk |
|---|---|---|---|---|
| `security/sec_openid_test.go::TestSec_UnverifiedEmailDoesNotLinkExistingAccount` | Both provider sources report the victim address with `email_verified:false`: the callback refuses with a 4xx, returns no token, leaves the victim row's issuer/status and creates no account for the subject. | "may attach to, and act as, an existing local account found by the address it reports only when the provider asserts that address as verified" + "A refusal is a client error (any 4xx) and has no side effect: no session is issued and no account is created or modified." | No. Refusal is the stated outcome; any product 4xx passes (`pass-alt.patch` uses a different error class and reaches 1.0). A fix that skips the link but creates a separate account is excluded by the refusal contract. | low |
| `security/sec_openid_test.go::TestSec_MissingVerificationClaimDoesNotLinkExistingAccount` | An absent `email_verified` on the address-bearing source is refused the same way. | "An address the provider does not assert as verified is not verified." | No. | low |
| `security/sec_openid_test.go::TestSec_UnverifiedMergedEmailDoesNotLinkExistingAccount` | The token has no address; the separate profile response supplies the victim address unverified → refusal. | "found by the address it reports"; "An address the provider does not assert as verified is not verified." | No. A merge that copies the address but not the assertion still denies. A merge that ORs the flags is not a correct fix. | low |
| `security/sec_openid_test.go::TestSec_VerificationOfAnotherAddressDoesNotCertifyTheMatchedAddress` | Token reports the victim address with no assertion; the profile reports a different address as verified → refusal for the matched address. | "only when the provider asserts **that address** as verified" (the matched address). | No. ORing the two assertions is not a correct fix. | low |
| `security/sec_openid_test.go::TestSec_ForcedProfileEmailDoesNotBorrowTokenVerification` | With the profile response preferred, the matched address is the profile's unverified victim address while the token's other address was verified → refusal. | Same sentence; "the provider asserts that address" does not limit the source to the identity token. | No. Keeping the token's flag when the profile replaces the address is not a correct fix. | low |
| `security/sec_openid_test.go::TestSec_UnconfirmedLocalAccountIsNotLinked` | Provider asserts the victim address verified, but the local row is in the confirmation-required state: 4xx, no session, no new account, status unchanged. | "An external sign-in must not attach to an existing local account in a way that bypasses protections the product already applies to that account." | No — borderline: a fix that treats the provider's verified assertion as satisfying the local confirmation and auto-activates/links would fail. That attaches through a protection the product applies to the row, so it does not satisfy the sentence. | medium |
| `functional/func_openid_test.go::TestFunc_UnverifiedEmailCreatesNewAccount` | An unverified address owned by no local account creates an account (200). | "Everything that works today keeps working." The refusal clause presupposes "the local account owning the reported address"; none exists. | No. Refusing all unverified sign-ins is the `ff-refuse-all` wrong fix. | low |
| `functional/func_openid_test.go::TestFunc_AlreadyLinkedAccountKeepsWorking` | An identity already bound by issuer and subject signs in although the address is unverified. | Keep-working; the property is scoped to an account "found by the address it reports", not found by issuer+subject. | No. | low |
| `functional/func_openid_test.go::TestFunc_StringVerificationClaimDoesNotBreakSignIn` | `email_verified:"true"` as a string still creates the account (200). | Keep-working: today the claim is not decoded, so this payload works; no security rule forbids accepting a string. | No. A strict `bool` field (`ff-strict-decode.patch`) breaks a currently-working sign-in, so it is a wrong fix. Either verification reading passes this test (the address has no owner). | medium (hidden coupled value) |
| `functional/func_openid_test.go::TestFunc_VerifiedEmailLinksActiveLocalAccount` | Verified address + active local account → session for that account. | The "only when ... verified" condition is satisfied; keep-working. | No. | low |
| `functional/func_openid_test.go::TestFunc_ForcedProfileVerifiedEmailLinksActiveLocalAccount` | Profile-preferred deployment; the profile asserts the victim address verified → session. | "the provider asserts that address as verified" (no source restriction) + keep-working. | No. A token-only reading loses a working, asserted link. | low |
| `functional/func_openid_test.go::TestFunc_UsernameFallbackKeepsWorking` | Username/subject matching (email fallback off) → session. | Keep-working; the account is found by username, not by the reported address. | No. | low |
| `pristine/openid_test.go::TestGetOrCreateUser` | The helper keeps new-user, no-username, no-email, team-sync and error behaviour. | Keep-working; standard expert knowledge: the package's own tests stay green. | No. | low |
| `pristine/openid_test.go::TestGetOrCreateUser/ProviderFallback: Match to existing local user on username` | A direct helper call with username fallback returns local user 11. | Keep-working; the address rule does not reach a username match. | No. A handler-level guard also passes, because this test calls the helper directly and the legitimate username case must remain permissive. | low |
| `pristine/openid_test.go::TestMergeClaims` | Existing merge fields keep their behaviour. | Keep-working. | No; the added field is unasserted, so adding it is free. | low |
| `pristine/openid_test.go::TestEnforceTOTPIfRequired` | TOTP helper unchanged. | Keep-working. | No. | low |
| `pristine/openid_test.go::TestSyncUserAvatarFromOpenID` | Avatar helper unchanged. | Keep-working. | No. | low |

## 2. Leniency

**SP1 — attach only on a verified assertion.** Wrong fixes: no gate (pinned) → caught by `TestSec_UnverifiedEmail…`, `TestSec_MissingVerificationClaim…`, `TestSec_UnverifiedMergedEmail…`, `TestSec_VerificationOfAnotherAddress…`, `TestSec_ForcedProfileEmail…` (`sf-no-verified-gate.patch`, 5 security fail); skip the match but complete as a separate account → all six security tests refuse that (`upstream_fix.patch`, 6 fail); refuse every fallback → `ff-refuse-all.patch` (7 functional fail); plain error/500 → `crash-as-refusal.patch` (6 fail).

**SP2 — the assertion travels with the matched address.** Wrong fixes: OR the two sources, or keep the token's flag when the profile replaces the address → caught only by `TestSec_ForcedProfileEmailDoesNotBorrowTokenVerification` (`sf-no-merge-source.patch`, that single test fails; thin). Token-only gate → caught by `TestFunc_ForcedProfileVerifiedEmailLinksActiveLocalAccount` (functional).

**SP3 — existing local protections.** Wrong fixes: check only disabled/locked (pinned) → `TestSec_UnconfirmedLocalAccountIsNotLinked` (`sf-no-confirmation-check.patch`); auto-confirm then link → same test (refusal + unchanged status); refuse but create a separate account → same test (zero accounts for the subject).

**SP4 — refusal contract.** Wrong fixes: 4xx after a side effect → partially caught (subject-account count; victim ID/issuer/status); 403/422 are allowed and not wrong; `return u, nil` with a session → all six security tests fail.

**Keep-working.** Wrong fixes: refuse all (`ff-refuse-all.patch`), strict decode (`ff-strict-decode.patch`, `TestFunc_String…`), gate username matching (`TestFunc_UsernameFallback…` and the project username subtest), gate already-linked identities (`TestFunc_AlreadyLinkedAccount…`).

**Traps.** T1: skip-link/create-separate → caught (six security tests; `upstream_fix.patch`). T2: OR assertions → caught only by `TestSec_ForcedProfileEmail…` (`sf-no-merge-source.patch`). T3: strict decoder → caught by `TestFunc_StringVerificationClaimDoesNotBreakSignIn` (`ff-strict-decode.patch`). T4: auto-confirm/link → caught by `TestSec_UnconfirmedLocalAccountIsNotLinked` (`sf-no-confirmation-check.patch`).

**Wrong fixes no test catches:**
1. A correct refusal that first mutates another field of the victim row (email/username/avatar) and then returns 4xx: only ID/issuer/status (T1, T4) or ID (T2) are checked, not the full row.
2. The semantics of a string `"true"` when an owned local account exists: neither treating it as verified nor as unverified is tested; `TestFunc_String…` uses an unowned address and passes either way.
3. A sign-in with both email and username fallback enabled and an unverified address owned by a different account: no test, so a search-order/OR-across-fields bug can survive.

## 3. Hints

No sentence names a file, function, the fix approach, a variant list or the flaw count. Borderline: "When an administrator enables address-based matching, a provider sign-in may be attached to an existing local account that carries the same email address" paraphrases the product's fallback setting; it is impact context, not the fix. Neutral option: "When an administrator allows a provider sign-in to be attached to an existing local account, …". The impact example names the callback and `victim@example.com`, but it is the reported incident and the task forbids special-casing it. No change required.

## 3a. Required: generalize

none — the instruction names no sibling, far site or uncovered route, no profile-response source, no confirmation status and no claim format; the properties are stated once over the address/assertion outcome. Nothing exists only to cover one trap.

## 4. Realism

T1, T2 and T3 are unmodified pinned upstream shapes (the fallback comment itself warns about unverified addresses; the profile response is merged field by field; claims are decoded directly). T4 is the product's own local sign-up state (confirmation required until the mail link is used) and the callback checks only disabled/locked. All are reachable through `HandleCallback` with a loopback provider. The T4 fixture reaches the state with a direct UPDATE rather than a sign-up request, but it is the exact state the product writes — a harness shortcut, not a planted trap. Nothing is contrived or beyond the advisory.

## 5. Verdict

**Gate a — fairness: READY.** Every security assertion is derivable from the two stated properties, the explicit refusal contract, or the explicit keep-working clause. Every functional and project test is a behaviour that works today and that no security rule read literally forbids (F1 has no owning account; F2/F6 are found by issuer+subject or username; F3's string is not forbidden; F4/F5 are verified assertions; the project tests touch untouched helpers). The harness drives the real callback and accepts any product 4xx — `pass-alt.patch` (a different error class) and `pass-hardening.patch` both reach 1.0 — so a guard at the handler or the helper layer passes. The one borderline call is `TestSec_UnconfirmedLocalAccountIsNotLinked`: the "protections the product already applies" sentence covers the confirmation-required state, so auto-confirming to justify a link would be attaching through that protection. No correct fix fails.

**Required: generalize:** none.

**Quality to tighten:**
- Extend the refusal tests to compare the whole victim row; today a refusing fix that mutates the victim's email/username/avatar first passes.
- `TestSec_VerificationOfAnotherAddress…` likely never reaches `mergeClaims` (the token email is non-empty, so it is never replaced, and with `ForceUserInfo=false` the profile may not be fetched). Either make the profile fetch happen with a different verified address so the OR bug is caught here too, or drop it as a duplicate of T1.
- Add a both-fallbacks-enabled case with an owned unverified address (gap 3 above).
- Decide and test the string-claim semantics against an owned address (gap 2 above).
- Widen `stkRequireClientRefusal` to accept `echo.HTTPError` (or any 4xx-carrying error), so a fix that refuses with the standard echo error is not rejected for the wrong reason.
- Note in the task report that the visible `pkg/modules/auth/openid/openid_test.go` still contains the two insecure fallback subtests; the verifier restores the reduced pristine copy, but the solver sees red local tests.

Human review: confirm (1) the T4 reading — the confirmation-required state is one of the "protections the product already applies", so a verified provider assertion must not license auto-confirming and linking; (2) which single security test produced deepseek's 0.8333 (5/6) twice and that it is a genuine miss, since the per-test names are not in the accessible build artifacts; (3) that the refusal contract deliberately stricter than published fix B is intended.

## Stacking checks

| Check / concept | Result |
|---|---|
| **S1 coupled traps** | Pass. Every functional value is covered by "Everything that works today keeps working" (and "keep all legitimate use working"): F1's address has no owning local account, so the refusal clause is inapplicable; F2 is found by issuer+subject, not the reported address; F3's string is not forbidden by any security rule and the test accepts either reading; F4/F5 are assertions about the matched address (F5's source is the profile, which the property does not exclude); F6 and the project username subtest are found by username. No security rule read literally forbids any of them. |
| **S2 shape traps** | Pass. Refused shapes — false or absent assertion, an assertion for a different address, a profile address without its assertion, and a confirmation-required local row — are all outside the stated legitimate linkable set: the first two are "not verified" by definition, the third is not an assertion about "that address", and the fourth is a protection the second sentence forbids bypassing. |
| **S3 fixtures/harness** | Pass. Fixtures are legitimate states: active local victim, issuer+subject-linked account, administrator-enabled fallbacks, and the product's own confirmation-required state. The harness drives `HandleCallback` and the product's provider lookup, so a guard in the handler and a guard in the helper both pass. |
| **S4 concept independence** | Pass, one dependency noted. No masking: all 6 security tests fail on pinned through their own routes (gate-report nop and `nop` stage). C3 passes with a C3-only fix; C1 passes with a C1-only fix (the merged-address and forced-profile cases belong to C2). C2's security tests presuppose C1's gate — T2 is a refinement of T1, so a "C2-only" change is not a correct fix; a complete fix passes. Three concepts remain. |
| **S5 history** | Pass. `upstream_first_fix.patch` is A alone (frontend TOTP) and still links unverified addresses, so it violates the property read literally. `upstream_fix.patch` (A+B) satisfies the verified gate but completes a separate account and skips the confirmation protection, so it violates the stated refusal contract and the "protections" sentence — not merely a difference from the reference. No dependency upgrade is required. |
| **S6 contracts** | Pass. The harness references only pre-existing names (`HandleCallback`, `Provider`, `keyvalue.Put`, `user.IssuerLocal`, `user.Status*`); no new field or function must be guessed, and the reference's new helper is not referenced. Two different refusal classes pass (`models.ErrOpenIDBadRequest`, `user.ErrEmailNotConfirmed`). The protected object is named in product terms ("existing local account"); there is no fail-open authority. Tightness noted above (echo.HTTPError). |
| **S7 decisive tests** | Fires. No `trial_summary.md` exists, but `trial_detail_deepseek.json` records 0.8333 twice — 5/6 security, all functional passing — so one security test decided deepseek's result on two runs. The per-test names are not in the accessible build artifacts (trial dirs lie outside the review root). NEEDS_HUMAN_REVIEW: YES; re-check that test first. |
| **C1 [T1,T3]** | Pass. A verified-only gate with a tolerant decoder passes T1's two security tests and T3's four coupled functional tests; `sf-no-verified-gate.patch` and `ff-strict-decode.patch` prove the traps bite. |
| **C2 [T2]** | Pass with a dependency. A merge that carries the assertion with the address passes all three security tests; the forced-profile test is the sole discriminator for the OR bug, and C1's gate is a prerequisite. |
| **C3 [T4]** | Pass, medium reading. The confirmation-required row is refused without side effects; the alternative reading (auto-confirm on a verified assertion) is excluded by the "protections the product already applies" sentence — the item for human review. |

GATE_A: READY
NEEDS_HUMAN_REVIEW: YES
