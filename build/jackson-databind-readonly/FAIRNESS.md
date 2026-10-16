# FAIRNESS: jackson-databind-readonly (pre-trial review, 2026-10-16)

The reviewer did not write the tests. Read: instruction.md, tests/ (support, security,
functional, test.sh, score.py), solution/fix.patch, manifest.json, notes.md and checks/*.patch
(always_register, alt_correct_fix, precedent_guard_only and drop_readonly_names in full).
Also read: the vulnerable `BeanDeserializerFactory.addBeanProps` and `AnySetterTest` (pristine
copy of /app), and the Javadoc of `JsonProperty.Access`, `JsonIgnore` and `JsonMerge` in
jackson-annotations. Nothing was run.

Reference points used below:
- **RB1** = "No input may set a property declared read-only, however the object is built,
  populated or updated, and whatever the type looks like. This includes changing the contents
  of an object, collection or map that the property holds."
- **RB2** = "Input aimed at a read-only property is ignored without an error."
- **RB3** = "Serialization is unchanged".
- **RB4** = "Everything else binds exactly as it does today. This includes writable properties
  (also a writable property that shares its JSON name with a read-only one), merging into
  writable nested objects, and input that is not aimed at a read-only property, wherever that
  input is delivered today."
- **C1** = "for every way input can reach a read-only property".

## 1. Per-test table

Every security test accepts a clean `JacksonException` refusal. RB2 is enforced only by
functional tests.

### Security tests

| test | asserts | fair because | correct fix could fail? | risk |
|---|---|---|---|---|
| security/QuotaUpdateBypassTest::updateKeepsQuota | merging mapper, readerForUpdating(Account): quota.limit/used unchanged | the stated example; RB1 | no | low |
| security/QuotaUpdateBypassTest::newAccountKeepsDefaultQuota | fresh read with merging mapper keeps the default quota | RB1 "On a new object, it keeps the value it has..." | no | low |
| security/QuotaUpdateBypassTest::typeLevelMergeKeepsQuota | `configOverride(Quota).setMergeable(true)`: quota unchanged | RB1 "however ... updated"; "for example with setDefaultMergeable" signals other merge configs exist | no; any fix at the merge decision covers every merge source | low |
| security/QuotaUpdateBypassTest::fieldDeclaredQuotaKeptByUpdateValue | READ_ONLY on field, `updateValue`: quota unchanged | the instruction names `updateValue` and field/getter declaration via `@JsonProperty`; RB1 | no | low |
| security/ExtensibleTypeBypassTest::memberUpdateKeepsQuota | catch-all type, merge update: quota unchanged | RB1 "whatever the type looks like", C1 | no | low-medium (see T1) |
| security/ExtensibleTypeBypassTest::newMemberKeepsRoles | catch-all type, read-only List via getter not filled | RB1 "collection ... the property holds", "whatever the type looks like" | no | low-medium |
| security/ExtensibleTypeBypassTest::ticketCreatorNotFromInput | catch-all constructor bean, field-declared READ_ONLY creator param not "mallory" | RB1 "however the object is built"; standard expert knowledge: READ_ONLY on the field applies to the logical property, including its creator parameter (jackson already honours this without a catch-all, #1345 test ported in /app) | no | low-medium |
| security/ExtensibleTypeBypassTest::inviteRoleNotFromInput | record with `@JsonAnySetter` component: role not "owner" | as above | no | low-medium |

### Functional tests: BindingFeatureTest

| test | asserts | fair because | correct fix could fail? | risk |
|---|---|---|---|---|
| functional/BindingFeatureTest::writableNestedValuesMergeOnUpdate | writable profile/preferences merge, tags append | RB4 "merging into writable nested objects" | no | low |
| functional/BindingFeatureTest::typeLevelMergeStillWorks | type-level merge of writable Preferences | RB4 | no | low |
| functional/BindingFeatureTest::readOnlyInputIgnoredWithoutError | read-only key present: no error, writable values bind (3 mappers, create and update) | RB2, RB4 | only an exception-throwing fix, which RB2 forbids | low |
| functional/BindingFeatureTest::serializationShowsReadOnlyValues | read-only values serialized | RB3 | no | low |
| functional/BindingFeatureTest::classLevelReadOnlyStillHonoured | allowGetters control still blocks | RB1 and RB4 (works today) | no | low |
| functional/BindingFeatureTest::plainMapperReplacesNestedValues | non-merging mapper replaces nested value | RB4 | no | low |

### Functional tests: ExtensibleTypeFeatureTest

| test | asserts | fair because | correct fix could fail? | risk |
|---|---|---|---|---|
| functional/ExtensibleTypeFeatureTest::memberWritableValuesBindOnUpdate | catch-all type: writable values merge, read-only key in body causes no error | RB2, RB4 | no | low |
| functional/ExtensibleTypeFeatureTest::memberTagsStillCollectedWithoutMerging | writable getter-only List still filled on a catch-all type | RB4 | only "never write through getters", which RB4 forbids | low |
| functional/ExtensibleTypeFeatureTest::unknownKeysStillReachExtensionAttributes | unknown keys reach the catch-all | RB4 "wherever that input is delivered today" | no | low |
| functional/ExtensibleTypeFeatureTest::excludedPropertyKeyStillReachesExtensionAttributes | the `@JsonIgnore` field key still reaches the catch-all | RB4 last clause, plus standard expert knowledge: the `@JsonIgnore` Javadoc says "if there is a JsonAnySetter it will be called instead", and `/app/src/test/.../AnySetterTest._testIgnorals` asserts it ("@JsonIgnore not [blocked]") | yes, with always_register.patch (the root fix the in-code comment invites). It violates RB4's literal text and the documented `@JsonIgnore` contract | medium |
| functional/ExtensibleTypeFeatureTest::ticketBindsVisibleValuesAndExtras | creator values and extras bind, createdBy causes no error | RB2, RB4; does NOT assert where `createdBy` goes (lenient) | no | low |
| functional/ExtensibleTypeFeatureTest::inviteBindsVisibleValuesAndExtras | same for the record | same | no | low |
| functional/ExtensibleTypeFeatureTest::plainCreatedObjectsUnchanged | creator types without a catch-all are unchanged | RB4 | no | low |
| functional/ExtensibleTypeFeatureTest::sameNameWritableInputStillBinds | WRITE_ONLY `owner` setter binds although a READ_ONLY getter shares the name | RB4, stated explicitly | only drop_readonly_names, which RB4 names | low |
| functional/ExtensibleTypeFeatureTest::sameNameWritableInputStillBindsWithExtensions | same pair on a catch-all type; `owner` is bound, not collected | RB4 | no (owner has a setter, so it is bound before any catch-all routing) | low |

### Functional tests: UpstreamReadOnlyTest

| test | asserts | fair because | correct fix could fail? | risk |
|---|---|---|---|---|
| functional/UpstreamReadOnlyTest::readOnlyAndWriteOnly | upstream ReadOrWriteOnlyTest behaviour | RB2-RB4; the test ships in /app | no | low |
| functional/UpstreamReadOnlyTest::readOnly935 | upstream ReadOrWriteOnlyTest behaviour | as above | no | low |
| functional/UpstreamReadOnlyTest::readOnly1345 | upstream ReadOrWriteOnlyTest behaviour | as above | no | low |
| functional/UpstreamReadOnlyTest::readOnly1382 | upstream ReadOrWriteOnlyTest behaviour | as above | no | low |
| functional/UpstreamReadOnlyTest::viaReadOnly1805 | upstream ReadOrWriteOnlyTest behaviour | as above | no | low |
| functional/UpstreamReadOnlyTest::usingAllowGetters1805 | upstream ReadOrWriteOnlyTest behaviour | as above | no | low |
| functional/UpstreamReadOnlyTest::renamedReadOnly2779 | upstream ReadOrWriteOnlyTest behaviour | as above | no | low |
| functional/UpstreamReadOnlyTest::ignoralsWithCatchAll | class-level ignoral blocks; the `@JsonIgnore` key reaches the catch-all | RB4, the `@JsonIgnore` Javadoc, and AnySetterTest in /app (direct port) | yes, always_register | medium (same item as above) |
| functional/UpstreamReadOnlyTest::ignoredGetterWithCatchAll744 | the `@JsonIgnore` getter's key reaches the catch-all | as above (AnySetterTest #744 port) | yes, always_register | medium |

## 2. Leniency

| property / trap | most plausible wrong fix | caught by |
|---|---|---|
| base (merge on getter-only READ_ONLY) | none survives: any merge-branch guard closes all 4 base tests | QuotaUpdateBypassTest (4) |
| T1 (catch-all leaves the ignorable set empty) | copy the #1805 guard onto the merge branch (precedent_guard_only) | all 4 ExtensibleTypeBypassTest |
| T1 | guard merge and getters, skip creators (miss_creator) | ticketCreatorNotFromInput, inviteRoleNotFromInput |
| T1 | guard merge and creators, skip collections (miss_collections) | newMemberKeepsRoles |
| T1 | check READ_ONLY on the creator parameter only (wrong_resource) | ticketCreatorNotFromInput (field-declared) |
| T2 | register every ignored name even with a catch-all (always_register) | excludedPropertyKey..., ignoralsWithCatchAll, ignoredGetterWithCatchAll744 |
| T3 | treat read-only names as hard ignorals (drop_readonly_names) | both sameNameWritableInput* tests |
| refusal / feature removal | crash_refusal, disable_feature | functional tests (14/24 and 19/24 pass) |

Wrong or partial fixes that no test catches. All are low-plausibility, because the natural fix
site (addBeanProps / resolve) is shared by these routes:
- A per-property `@JsonMerge` on a READ_ONLY getter. Only mapper-wide and type-level merging
  are tested.
- A READ_ONLY **Map** reached through getter-as-setter on a catch-all type. Only a List is
  tested; it takes the same `_isSetterlessType` branch.
- Static-factory or delegating creators, builders (`@JsonPOJOBuilder`) and polymorphic subtypes
  combined with a catch-all. None is tested, and none was probed as leaking.
- Where a blocked read-only key ends up: dropped, or delivered to the catch-all. Neither is
  asserted. This is deliberate leniency, and the reference and alt_correct_fix differ here.

## 3. Hints

- No leak term from the manifest occurs in instruction.md. It never says catch-all, any-setter,
  creator, constructor or record.
- "This includes changing the contents of an object, collection or map that the property holds."
  This names the class of the merge and getter-as-setter mechanisms. Keep it: it is the contract
  that makes merge count as "set" (see 6). It does not point at the catch-all.
- "however the object is built, populated or updated, and whatever the type looks like." This
  loosely paraphrases the variant axes (creators, type shape). It is generic and needed for T1.
  Keep it.
- "(also a writable property that shares its JSON name with a read-only one)" names T3. That is
  unavoidable: without it, T3 would be unfair. Keep it.
- "wherever that input is delivered today" gives a mild nudge toward T2. It is generic. Keep it.
- "Other types and other ways of reading input let read-only values through in the same way."
  It gives no count or list. Acceptable.

No wording change is required.

## 4. Realism

- Nothing in /app is planted. The Dockerfile checks out d627a8a and deletes `.git`.
- Every gap is unmodified upstream code, reported byte-identical in 2.20.0.
- Both gaps are reachable through public `ObjectMapper` / `ObjectReader` APIs with ordinary
  configuration.
- The test models are realistic API DTOs:
  - an extension-attribute map;
  - a Lombok-style immutable bean;
  - a record with a server-decided field;
  - the "id in, summary out" READ_ONLY/WRITE_ONLY pair.
- `@JsonAnySetter` on a record component is a 2.18 feature. It is newer, but it is supported at
  this commit.

## 5. Are the gaps genuine, and is merging "set from input"?

**The READ_ONLY Javadoc.** It says the property "may only be read for serialization ... but not
written (set) during deserialization. Put another way, this would reflect 'read-only POJO', in
which value contained may be read but not written/set." It documents no exception for merging
or for catch-all types.

**Merging into a getter-only READ_ONLY POJO counts as "set from input".** Four reasons:
- (a) The instruction says so explicitly ("changing the contents of an object ... the property
  holds").
- (b) The Javadoc's "value contained may be ... not written".
- (c) jackson's own #1805 guard already treats mutating a READ_ONLY collection's contents through
  its getter as a bug ("need to ensure we don't accidentally sneak in getter-as-setter for
  READ_ONLY properties"). Merging through the same getter is the same class of write, one branch
  below.
- (d) The documented equivalent, `@JsonIgnoreProperties(allowGetters=true)`, is honoured on
  merge, so READ_ONLY diverging from it is an inconsistency, not a design choice.

**Counter-argument.** The `@JsonMerge` Javadoc describes merge as "current value is first
accessed (with a getter...) and then modified". A maintainer could argue that an explicit
per-property `@JsonMerge` on a READ_ONLY getter is a request to merge. The tests avoid this:
they use only mapper-wide and type-level defaults, where no such per-property intent exists.

**Catch-all gap.**
- The in-code comment ("although [databind#1805] would suggest we should block properties
  regardless, for now only consider unless there's any setter") shows the maintainers chose the
  exemption to keep `@JsonIgnore` keys flowing to the any-setter, which the `@JsonIgnore`
  Javadoc documents.
- That READ_ONLY creator params and collections leak as a result is a side effect. The comment
  itself labels it provisional ("for now", "#1805 would suggest we should block"). It is not a
  documented exception.
- Without a catch-all, the same creator and collection routes are blocked (#1345, #1805). The
  protection depends on an unrelated feature, which is a genuine defect.

**Classification.**
- Calling it CWE-915 is fair: applications use READ_ONLY as their mass-assignment control.
- It should be presented as a library contract gap with no advisory, not as a known CVE. An
  auditor may call it defence-in-depth. The manifest already states that no advisory exists.

## 6. Verdict: READY

**Medium items.**
- **T2** affects three functional tests, which fail always_register. I would rate it
  low-to-medium rather than medium. The behaviour it protects is:
  - stated literally by RB4 (a `@JsonIgnore` key is not aimed at a read-only property, and today
    it is delivered to the catch-all);
  - documented public contract (the `@JsonIgnore` Javadoc: "if there is a JsonAnySetter it will
    be called instead");
  - asserted by `AnySetterTest` in /app, which the solver can run with the JUnit jar in
    /opt/libs.
- **T1** (four security tests) rests on RB1's "whatever the type looks like" and "however the
  object is built", plus C1. The requirement is unconditional and states the route
  generically. No correct fix fails these tests, so it is fair.

No instruction or test change is required.

**Optional.** Add a probe for a READ_ONLY Map on a catch-all type and for a per-property
`@JsonMerge`. These are not needed for READY.
