# Fairness review — stk-openremote-29156 (revision 2026-10-24, post-upgrade audit)

Source of the required change: `build/stk-openremote-29156/AUDIT-FIX-20261024.md` (instruction
rewording after the v1 -> v2 upgrade). The audit found one contradiction: the v2 property began
"**Apart from the master-realm superuser**, a request that names a realm must not reach … anything
that belongs to another realm", while
`security/SecUserReadTest.java::testSuperUserGetsNoUserOutsideTheNamedRealm` requires the
master-realm superuser to be refused when it names `master` and targets a `city` user. The tests and
the reference are correct (the reference guard applies to every caller), so only `instruction.md`
changed: the exemption is gone and the rule now reads, for every caller, "the master-realm superuser
may name any realm, but a request still reaches only the data of the realm it names". The coupled
keep-working sentence "A caller continues to reach its own data as it does today" is retained. This
restores the v1 property's scope ("only when it administers the realm named in the request and the
data belongs to that realm") in general terms, without naming a route, value or trap.

## Tests and their covering instruction

| test | asserts | covering sentence | correct fix could fail? | risk |
|---|---|---|---|---|
| `security/SecUserReadTest::testUserFromAnotherRealmIsNotReturnedThroughOwnRealmPath` | a `master` user read through the `building` path is refused | "A request that names a realm must not reach or affect anything that belongs to another realm" | no | low |
| `…::testUserFromAnotherRealmIsNotReturnedThroughThatRealmPath` | the same user read by naming `master` from a `building` administrator is refused | same; the caller administers only `building` ("if it administers that realm") | no | low |
| `…::testSuperUserGetsNoUserOutsideTheNamedRealm` | a superuser naming `master` cannot read a `city` user | same + "the master-realm superuser may name any realm, but a request still reaches only the data of the realm it names" | no | low |
| `…::testClientRolesOfForeignUserThroughOwnRealmPath` | foreign user's client roles through the own-realm path refused | same data property ("anything that belongs to another realm") | no | low |
| `…::testClientRolesOfForeignUserThroughThatRealmPath` | foreign user's client roles by naming the target realm refused | same | no | low |
| `…::testRealmRolesOfForeignUser` | foreign user's realm roles refused | same | no | low |
| `…::testSessionsOfForeignUserThroughOwnRealmPath` | foreign user's sessions through the own-realm path refused | same ("anything that belongs to another realm") | no | low |
| `…::testSessionsOfForeignUserThroughThatRealmPath` | foreign user's sessions by naming the target realm refused | same | no | low |
| `security/SecRoleDefinitionsTest::testBuildingAdministratorCannotListMasterRoleDefinitions` | `master` role definitions refused to a `building` administrator | same data property; the caller does not administer `master` | no | low |
| `…::testBuildingUserCannotListCityRoleDefinitions` | `city` role definitions refused to a plain `building` user | same; plain user reaches only its own data | no | low |
| `…::testBuildingAdministratorCannotListCityRoleDefinitions` | `city` role definitions refused to a `building` administrator | same | no | low |
| `security/SecSessionControlTest::testOtherRealmSessionSurvivesDisconnectAttempt` | a `master` session is not ended through the `building` path and stays connected | same data property ("reach or affect anything that belongs to another realm") | no — any 4xx, and no-effect is checked | low |
| `…::testOtherRealmSessionSurvivesOnItsOwnPath` | a `master` session is not ended by naming `master` | same | no | low |
| `…::testPlainUserCannotEndAnotherRealmsSession` | a plain user cannot end a `city` session | same; a plain user administers no realm | no | low |
| `functional/FuncUserReadTest::testSameRealmUserRecordIsReturned` | administrator reads a user of its own realm | "Everything that works today keeps working"; "within a realm a caller administers its access is unchanged" | no | low |
| `…::testUserReadsOwnRecordWithoutAdministrativeRole` | plain user reads its own record | "A caller continues to reach its own data as it does today" | no | low |
| `…::testUserCannotReadPeerWithoutAdministrativeRole` | plain user cannot read a peer | "within the realm it names, a caller may reach only its own data" | no | low |
| `…::testSuperUserReadsUsersOfEveryRealm` | superuser reads users while naming each user's realm | "the master-realm superuser may name any realm" + keep-working | no | low |
| `…::testCurrentUserRecordFollowsTheAuthenticatedIdentity` | the current-user read returns the caller's own record even when a realm header names another realm | "A caller continues to reach its own data as it does today" | no — own data is expressly kept | low |
| `functional/FuncRolesTest::testSameRealmRoleAssignmentsAreReturned` | own-realm role assignments | "within a realm a caller administers its access is unchanged" | no | low |
| `…::testUserReadsOwnRoles` | own role assignments | "A caller continues to reach its own data as it does today" | no | low |
| `…::testSuperUserReadsRoleAssignmentsAcrossRealms` | superuser reads role assignments of each named realm | "the master-realm superuser may name any realm" + keep-working | no | low |
| `…::testSameRealmRoleDefinitionsAreListed` | own-realm role catalogue | "within a realm a caller administers its access is unchanged" | no | low |
| `…::testSuperUserListsRoleDefinitionsOfEveryRealm` | superuser lists each named realm's catalogue | "the master-realm superuser may name any realm" | no | low |
| `functional/FuncSessionsTest::testSameRealmSessionsAreListed` | own-realm user's sessions | "within a realm a caller administers its access is unchanged" | no | low |
| `…::testSuperUserListsSessionsAcrossRealms` | superuser lists sessions of each named realm | "the master-realm superuser may name any realm" | no | low |
| `…::testUserListsOwnSessions` | plain user lists its own sessions | "A caller continues to reach its own data as it does today" | no | low |
| `…::testSameRealmAdministratorEndsASession` | administrator ends a session of its own realm | "within a realm a caller administers its access is unchanged" | no | low |
| `…::testSuperUserEndsSessionsAcrossRealms` | superuser ends a session of each named realm | "the master-realm superuser may name any realm" | no | low |
| `…::testMissingSessionIsNotFound` | an unknown session is refused | "Everything that works today keeps working"; standard product behaviour | no — any 4xx accepted | low |
| `functional/FuncLocaleTest::testUserUpdatesOwnLocale` | the caller updates its own locale (authenticated realm) | "A caller continues to reach its own data as it does today" | no | low |
| `…::testCurrentUserRecordIsReadableForANormalUser` | a plain user reads its own current record | same | no | low |

## Leniency (QUALITY)

| wrong fix | caught by |
|---|---|
| refuse every cross-realm-named request | `ff-refuse-all.patch` → `functional_fail` (16 functional errors) |
| crash/other `Throwable` instead of a client-error refusal | `sf-crash-as-refusal.patch` → `security_fail` |
| guard the path realm but not the target object's realm | `sf-wrong-object.patch` → `security_fail` (8) |
| exempt the superuser from the per-user realm check | `sf-superuser-exempt.patch` → `security_fail` (1) |
| guard reads only, not session control | `sf-get-only.patch` → `security_fail` (8) |
| compare named realm to the caller's realm instead of checking access | `ff-realm-equality.patch` → `functional_fail` (5) |
| leave the current-user reads on the client realm header | `ff-current-user-header.patch` → `functional_fail` (1) |
| miss the per-user concept | `miss-per-user.patch` → 8 security fails |
| miss the role-catalogue concept | `miss-role-definitions.patch` → 3 security fails |
| miss session control | `miss-session-control.patch` → 3 security fails |
| ship the published fix alone (session control open) | `upstream_fix.patch` → `security_fail` (3) |
| an equivalent correct fix with lookup by realm / by target user | `pass-alternative.patch` → `pass` |
| a stricter correct fix (null/blank input refused too) | `pass-hardening.patch` → `pass` |

No wrong fix in the catalogue is left uncatched.

## Hints (QUALITY)

No file, function, header, endpoint, mechanism, trap, variant list or count is named. The one literal
case is the advisory's own reported request in the impact example, explicitly called "one instance".
The property and refusal sentences state the protected outcome. The v1 per-route preservation list
and the "roles and sessions" system prose are gone.

**Required: generalize** — none. No sentence describes where a sibling, far site or uncovered route
lives.

## Realism (QUALITY)

All traps are real, unmodified upstream code at the pinned commit (per `manifest.traps` and
`notes.md`); T1–T3 are the advisory's own route family, T4 is a published-fix far site, T5 an
uncovered upstream route, T6 a coupled current-user value. Nothing is planted or contrived.

## Stacking checks

Concepts: **C1 = T1/T2/T3/T6** (per-user profile/role/session reads plus the current-user coupling),
**C2 = T4** (realm-level role catalogue), **C3 = T5** (session control).

### S1 — Coupled traps

| functional value | concept | covering clause | security rule that could forbid it |
|---|---|---|---|
| `FuncUserReadTest.testSameRealmUserRecordIsReturned`, `testUserReadsOwnRecordWithoutAdministrativeRole` | C1 | "Everything that works today keeps working"; "A caller continues to reach its own data as it does today" | none: the data belongs to the named realm and the caller administers it, or is the caller's own |
| `FuncRolesTest.testSameRealmRoleAssignmentsAreReturned`, `testUserReadsOwnRoles` | C1 | same | none: own realm / own data |
| `FuncSessionsTest.testSameRealmSessionsAreListed`, `testUserListsOwnSessions` | C1 | same | none: own realm / own data |
| `FuncUserReadTest.testCurrentUserRecordFollowsTheAuthenticatedIdentity` | C1 | "A caller continues to reach its own data as it does today" | none: it returns the caller's own record; own data is expressly kept |
| `FuncUserReadTest.testSuperUserReadsUsersOfEveryRealm` | C1 | "the master-realm superuser may name any realm" | none: each read names the realm the user belongs to |
| `FuncRolesTest.testSuperUserReadsRoleAssignmentsAcrossRealms` | C1 | same | none: ditto |
| `FuncSessionsTest.testSuperUserListsSessionsAcrossRealms` | C1 | same | none: ditto |
| `FuncRolesTest.testSameRealmRoleDefinitionsAreListed` | C2 | "within a realm a caller administers its access is unchanged" | none: the named realm is the caller's own |
| `FuncRolesTest.testSuperUserListsRoleDefinitionsOfEveryRealm` | C2 | "the master-realm superuser may name any realm" | none: each read names the realm whose catalogue it returns |
| `FuncSessionsTest.testSameRealmAdministratorEndsASession` | C3 | "within a realm a caller administers its access is unchanged" | none: the session's user belongs to the named realm |
| `FuncSessionsTest.testSuperUserEndsSessionsAcrossRealms` | C3 | "the master-realm superuser may name any realm" | none: each session belongs to the realm named |
| `FuncSessionsTest.testMissingSessionIsNotFound` | C3 | "Everything that works today keeps working" | none: an unknown session reaches nothing; refused with a client error |

Result: no contradiction in any concept. The v2 contradiction — the superuser exempted while
`testSuperUserGetsNoUserOutsideTheNamedRealm` requires refusal — is removed by rewording the rule
over its protected outcome, not by naming the value.

### S2 — Shape traps

| concept | refused shape | outside the legitimate set because |
|---|---|---|
| C1 | foreign user identifier under the caller's own realm path; foreign realm path; superuser naming `master` with a `city` target | legitimate is the caller's own data, or data of the realm named when the caller administers it; the superuser's reach is still bounded by the named realm |
| C2 | `master`/`city` role catalogue requested by a `building` administrator or plain user | legitimate is the role catalogue of a realm the caller administers |
| C3 | `master`/`city` session identifier under the `building` path or under the `master` path; `city` session ended by a plain user | legitimate is a session whose user belongs to the realm named and which the caller administers |

### S3 — Fixtures and harness

Every fixture state is a normal, authorised one: three realms, users with their roles, and connected
sessions the product would have. The harness builds the real `UserResourceImpl` (the product's
resource) with the injected servlet request and security context and calls its resource methods —
the same entry the JAX-RS layer invokes — so a correct guard in any per-user read, the role
catalogue, the session operation or a shared helper passes. Pass.

### S4 — Concept independence

| concept | security tests on pinned | own route | correct fix alone passes |
|---|---|---|---|
| C1 | the eight `SecUserReadTest` cases | per-user reads | yes — `miss-per-user.patch` flips 8, functional green |
| C2 | the three `SecRoleDefinitionsTest` cases | realm role catalogue | yes — `miss-role-definitions.patch` flips 3, functional green |
| C3 | the three `SecSessionControlTest` cases | session disconnect | yes — `miss-session-control.patch` flips 3, functional green |

Every security test fails on the pinned code through its own route; no masking applies (pattern H4,
not H3c).

### S5 — History

Pattern H4 (stacked). `checks/upstream_fix.patch` is the published fix alone; it leaves session
control open (3 security tests fail), so read literally against "must not reach or affect anything
that belongs to another realm" it violates the property. It is wired `security_fail` (recall). No
`upstream_first_fix.patch` is required for H4. Pass.

### S6 — Contracts

Tests drive the product resource's public operations; no field or function name must be guessed. The
protected object classes are stated in product terms ("user account", a realm's "role", "data"; a
connected client's session is "anything that belongs to another realm"). Any 4xx refusal is
accepted, so the refusal form does not force one error class. No fail-open fallback is involved.
Pass.

### S7 — Decisive tests

No `build/stk-openremote-29156/trial_summary.md` exists, so no trial decided anything. The audit
itself was a read-only review of the instruction upgrade; its single finding
(`testSuperUserGetsNoUserOutsideTheNamedRealm` contradicted by the superuser exemption) is now
removed in `instruction.md`, and the test remains a correct-fix-passing assertion. Re-checked
against S1–S6: no correct fix fails it, and it is not a single-test decider of any run.

## Verdict

The pinned code fails all 14 security tests; the reference passes all 32 hidden tests. Every
functional value is covered by the general keep-working sentence, and no security rule read
literally forbids one. Gate a is clear.

GATE_A: READY
NEEDS_HUMAN_REVIEW: NO
