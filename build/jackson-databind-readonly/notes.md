# jackson-databind-readonly: build notes (round-2 trap stack, new protection feature)

Start: 2026-10-16T13:28Z. End: see the gate section.

## Base
- Same Dockerfile, vulnerable checkout (`d627a8a`) and offline javac + JUnit setup as
  `jackson-databind-sib2`. Nothing is planted in `/app`.
- The protection feature is different: write-protection declared with
  `@JsonProperty(access = READ_ONLY)` (and `@JsonIgnoreProperties(allowGetters = true)`, which
  turned out to be honoured on every route and serves as a control).
- source = `injected`, but both gaps are real, unmodified upstream code. There is no advisory or
  fix. `BeanDeserializerFactory.addBeanProps` is byte-identical in the 2.20.0 sources jar.

## Scout (13:28Z to about 13:40Z; probes in ~/.tb-graders/cwe/work/jackson-databind-readonly/probe)
I ran about 45 routes through javac probes (`P1.java`, `P2.java`) on d627a8a.
- Honoured on the vulnerable code:
  - plain setter/field beans and readerForUpdating of them;
  - creator params, whether declared on the field or on the param, when the type has no catch-all;
  - records without a catch-all;
  - builders;
  - unwrapped children, mix-ins and polymorphic subtypes;
  - renamed read-only properties;
  - read-only lists without a catch-all (the #1805 guard);
  - `allowGetters` everywhere.
- Leaking:
  - merge on a getter-only read-only POJO: default mergeable, type override or `@JsonMerge`;
    fresh read, readerForUpdating or updateValue;
  - when the type has an `@JsonAnySetter`: creator params (classic constructor, record, and the
    2.18 any-setter-as-creator-param), collection/map getter-as-setter, and merge.
- Rejected:
  - `@JsonIgnore` on the setter plus `@JsonProperty` on the getter. The private field is still
    set through INFER_PROPERTY_MUTATORS, but the JsonIgnore Javadoc calls this split case
    "read-only (read from input into POJO)", so intent is unclear.
  - Array shape: read-only properties are dropped from the positions. That is a functional quirk,
    not a write.
  - PropertyGenerator identity with a READ_ONLY id: a definition error.
- Javadoc of `Access.READ_ONLY`: "may only be read for serialization ... but not written (set)
  during deserialization". Nothing documents the merge or catch-all exceptions.

## Example (base route)
- A mapper with `setDefaultMergeable(true)` and `readerForUpdating(account)` merges
  `{"quota":{"limit":1000000}}` into a read-only `Quota`.
- It lands in the merge branch of `BeanDeserializerFactory.addBeanProps` (line 614), which has no
  ignorable guard. The #1805 guard for collections sits 12 lines above and is the obvious
  precedent to copy.

## Traps
**T1 (neighbour precedent defeated by a feature-absent branch; creator form off the check's path).**
- When the type has a catch-all, `addBeanProps` (lines 553-566) never registers the read-only
  names. The in-code comment ("for now only consider unless there's any setter") makes this look
  deliberate.
- Two other checks depend on that set:
  - the #1805 guard (line 603, `builder.hasIgnorable`);
  - the creator marking in `BeanDeserializerBase.resolve` (lines 523-532), used by
    `PropertyBasedCreator` (lines 76 and 90). These are in a different file and package from the
    example's landing site.
- So the precedent-copy fix closes the base and misses:
  - merge with a catch-all;
  - a read-only List with a catch-all;
  - a constructor-built bean with a catch-all;
  - a record with a catch-all component.
- Tests: `security/ExtensibleTypeBypassTest`, all 4 methods.

**T2 (shared helper with divergent contracts / adjacent API).**
- The same ignored-names set carries read-only names and `@JsonIgnore`d names.
- `@JsonIgnore`d keys still reach the catch-all by design. Jackson's own `AnySetterTest` asserts
  this, and it ships in `/app/src/test`.
- The root fix the comment invites ("#1805 would suggest we should block properties regardless")
  is secure but breaks this (`always_register.patch` gives functional_fail).
- Tests:
  - `functional/ExtensibleTypeFeatureTest.excludedPropertyKeyStillReachesExtensionAttributes`;
  - ported `UpstreamReadOnlyTest.ignoralsWithCatchAll` and `ignoredGetterWithCatchAll744`.
- The instruction covers this with "input that is not aimed at a read-only property, wherever
  that input is delivered today".

**T3 (coupled visible binding).**
- A WRITE_ONLY `owner` id setter shares its JSON name with a READ_ONLY `owner` summary getter.
- The read-only name is in the ignored set, so a fix that treats that set as hard ignorals drops
  the writable input (`drop_readonly_names.patch` gives functional_fail).
- Tests: `functional/ExtensibleTypeFeatureTest.sameNameWritableInput*`.
- The instruction states this contract explicitly.

## Reference fix (`solution/fix.patch`, BeanDeserializerFactory only, about 20 lines)
- Always compute the ignored names.
- When there is a catch-all, mark creator properties with those names as ignorable. Their keys
  then still go to the catch-all, so nothing else changes.
- Skip getter-only properties with those names before both the getter-as-setter branch and the
  merge branch.
- Verified with the probes: every leak is closed, and the same-name pair still binds.

## Tests
- 8 security tests: all fail on the vulnerable code and all pass on the reference.
- 24 functional tests: all pass on both. They include ports of jackson's ReadOrWriteOnlyTest and
  the AnySetterTest ignorals.
- Security tests accept a clean `JacksonException` refusal. "Ignored without error" is enforced
  by the functional tests (`crash_refusal.patch` gives functional_fail).
- The writable getter-only properties (`tags`, `preferences`) use differently named backing
  fields. Otherwise jackson writes through the inferred field and `disable_feature` would not be
  caught. This was found by the first check run and fixed before the gate.

## Check patches (local runs, hidden suite)
| patch | security | functional | expected |
|---|---|---|---|
| precedent_guard_only | 4/8 | 24/24 | security_fail |
| miss_creator | 6/8 | 24/24 | security_fail |
| miss_collections | 7/8 | 24/24 | security_fail |
| wrong_resource | 7/8 | 24/24 | security_fail |
| always_register | 8/8 | 21/24 | functional_fail |
| drop_readonly_names | 8/8 | 22/24 | functional_fail |
| crash_refusal | 8/8 | 14/24 | functional_fail |
| disable_feature | 8/8 | 19/24 | functional_fail |
| alt_correct_fix | 8/8 | 24/24 | pass |
| hardening | 8/8 | 24/24 | pass |

Jackson's own tests: I compiled and ran 602 tests from 106 files, covering every file that
mentions READ_ONLY, JsonAnySetter, JsonMerge, allowGetters, setDefaultMergeable or
ConstructorProperties, plus all of deser/merge, deser/filter and deser/creators.
- Vulnerable: 601/602. Reference: 601/602.
- The one failure is a JDK17 module-opens issue that occurs on both.
- I did not run these tests against the alt or hardening patches.

## Not verified / open
- The blind patch and FAIRNESS.md are owed by independent agents.
- The full Maven suite was not run (offline SNAPSHOT parent), as in the base task.
- Fairness risk, medium:
  - T2 relies on the generic preservation clause plus jackson's own test in /app.
  - A reviewer could argue that stopping `@JsonIgnore`d keys from reaching the catch-all is an
    acceptable side effect.
- Fairness risk, low/medium: T1's catch-all forms rely on "whatever the type looks like" and
  "however the object is built". Catch-all types are not mentioned.
- Distance:
  - The T1 creator form is in another file and package (`BeanDeserializerBase`,
    `deser/impl/PropertyBasedCreator`).
  - The root cause and the merge/collection forms are in the same method as the example's
    landing site, about 50 lines away. That is less distance than sib2's `SettableAnyProperty`.

## Gate (2026-10-16)
- static: only the expected problems (blind patch and FAIRNESS.md missing).
- nop: PASSED.
- oracle: PASSED.
- patches: PASSED (all 10 checks matched their expectation).
- End: 14:05Z.
- 14:21Z (lead): trials started in parallel with the full strict gate; results count only if that gate run prints PASSED.
