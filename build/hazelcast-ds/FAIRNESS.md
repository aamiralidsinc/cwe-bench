# FAIRNESS.md — hazelcast-ds (pre-trial fairness & leniency review)

Reviewed: `tasks/hazelcast-ds/instruction.md`, every file in `tasks/hazelcast-ds/tests/`,
`tasks/hazelcast-ds/solution/fix.patch`, `build/hazelcast-ds/manifest.json`,
`build/hazelcast-ds/notes.md`, `build/hazelcast-ds/checks/*.patch`, and
`tasks/hazelcast-ds/environment/inject.patch` for the injected traps.
No Docker, trials or gates were run; no upstream advisory or fix was consulted.

Current tests: 17 security (4 classes) + 13 functional = 30. (The notes describe a
later 32-test revision — counter envelopes, a map-key test, tightened list/map
assertions. That revision is **not present** in the tree under review; see §2/§5.)

## 1. Test-by-test table

`file::name` | what it asserts | instruction sentence (or standard expert knowledge) that makes it fair | could a CORRECT fix fail it? | risk
---|---|---|---|---
**SecurityRestrictedTypeNameTest.java**
`SecurityRestrictedTypeNameTest::serializableTypeNameIsNotConstructed` | `CounterPayload` (user class, `Serializable`) type name at top level: `CONSTRUCTIONS == 0`, no exception, result is `GenericRecord` | "A class is not eligible when it is already serialized by another mechanism" + "No construction at all… neither through a constructor nor through an allocation that bypasses constructors" + "Reading a value whose type name is ineligible… normally returns a generic record; a caller must not have to catch an exception" | no | low
`SecurityRestrictedTypeNameTest::jdkTypeNameIsNotInstantiated` | `java.io.File` type name reads as `GenericRecord` | "a Compact value whose type name denotes a platform-internal or **JDK class** comes back… as an instance of that class" + property 2 | no | low
`SecurityRestrictedTypeNameTest::internalTransferTypeIsNotInstantiated` | `HeapData` type name reads as `GenericRecord` | property 2: "already serialized by another mechanism" and "platform's own implementation" | no | low
`SecurityRestrictedTypeNameTest::internalOutboundFrameTypeIsNotInstantiated` | `Packet` type name reads as `GenericRecord` | property 2: "belongs to the platform's own implementation rather than to the application's data model" | no | low
`SecurityRestrictedTypeNameTest::unsafeInputTypeIsNotInstantiated` | `UnsafeObjectDataInput` type name reads as `GenericRecord` | property 2 (platform implementation); the instruction's own "platform-internal" example | no | low
`SecurityRestrictedTypeNameTest::schemaCarriedInTheBinaryIsAlsoRestricted` | same, with the schema written into the binary | property 3: "whether the schema travels in the schema service or inside the binary" | no | low
**SecurityNestedValueTest.java**
`SecurityNestedValueTest::nestedInterfaceFieldIsNotInstantiated` | `PlainEnvelope.payload` (`Payload` interface) wire type `java.io.File`: `WireData.read` **must not throw**; whole result must be `GenericRecord` | property 3 (field position) + property 4 ("delivered as a generic record") | **YES** — the contract says "In a nested position that cannot hold a generic record the read may fail cleanly". A `Payload` field cannot hold a `GenericRecord`; a fix that implements exactly that carve-out (propagate the clean failure) is instruction-compliant and fails this test (uncaught call at line 38) | **high**
`SecurityNestedValueTest::nestedConcreteFieldIsReadAsGenericRecord` | `ConcreteEnvelope.payload` (`SerializablePayload`): no exception; result `GenericRecord` | property 3 + property 2 | **YES** — concrete field cannot hold a `GenericRecord`; same carve-out permits the clean failure the test forbids | **high**
`SecurityNestedValueTest::listElementIsNotInstantiated` | If read returns a `DataListEnvelope`, every item is a `GenericRecord`; exception or any other result is accepted | property 3 ("an element of … a collection") | no (weak: see §2) | low
`SecurityNestedValueTest::mapValueIsNotInstantiated` | Same for `DataMapEnvelope` values | property 3 ("…or a map") | no (weak: see §2) | low
`SecurityNestedValueTest::recordComponentIsNotInstantiated` | Record with `Payload` component, wire type `CounterPayload`: `CONSTRUCTIONS == 0`, no exception, result `GenericRecord` | property 3 ("a component of a record") + "No construction at all" | **YES** — counter half is fair, but a record component cannot hold a `GenericRecord`; the clean failure the carve-out permits fails the no-exception assertion | **high**
`SecurityNestedValueTest::recordConcreteComponentIsReadAsGenericRecord` | `ConcreteRecord(SerializablePayload)`: no exception; result `GenericRecord` | property 3 + property 2 | **YES** — same carve-out conflict | **high**
**SecurityProductClassTest.java**
`SecurityProductClassTest::memberInternalTypeIsNotInstantiated` | `com.hazelcast.instance.impl.HazelcastInstanceProxy` reads as `GenericRecord` | property 2: "belongs to the platform's own implementation rather than to the application's data model" | no — a fix implementing the stated categorical rule covers it; a "block only `*.internal`" fix would fail but does not satisfy property 2 | medium
`SecurityProductClassTest::discoveryFileReaderTypeIsNotInstantiated` | `com.hazelcast.kubernetes.KubernetesConfig$DefaultFileContentsReader` reads as `GenericRecord` | property 2 (shipped platform class, not application data model) + "classes that are not part of the application's data model" | no, on the categorical reading; interpretation risk only (not named `internal`/`impl` at top level) | medium
`SecurityProductClassTest::connectorDataSourceTypeIsNotInstantiated` | `com.hazelcast.jet.impl.connector.DataSourceFromJdbcUrl` reads as `GenericRecord` | property 2 (platform `.impl` connector) | no | medium
`SecurityProductClassTest::serializationStatisticsTypeIsNotInstantiated` | Injected `com.hazelcast.internal.serialization.impl.SerializationServiceStatistics` reads as `GenericRecord` | property 2 (platform implementation) | no — any family rule for platform packages covers it; only a hand-curated denylist misses the unguessable name (that is a leniency gap, not unfairness) | medium
**SecurityArrayElementTest.java**
`SecurityArrayElementTest::arrayElementIsNotInstantiated` | Array element wire type `CounterPayload`: `CONSTRUCTIONS == 0`; if typed `ArrayEnvelope` returned, elements must be `GenericRecord` | property 3 ("an element of an array") + "No construction at all" | no | low
**FunctionalZeroConfigTest.java**
`FunctionalZeroConfigTest::plainValueRoundTrip` | `PlainPayload` round-trips typed | "Ordinary user classes with no other serialization mechanism keep deserializing directly exactly as today" | no | low
`FunctionalZeroConfigTest::nestedInterfaceFieldRoundTrip` | `PlainEnvelope` with `PlainPayload` round-trips typed | same, "at the top level and nested" | no | low
`FunctionalZeroConfigTest::nestedConcreteFieldRoundTrip` | `ConcretePlainEnvelope` round-trips typed | same | no | low
`FunctionalZeroConfigTest::arrayRoundTrip` | `Payload[]` round-trips | "including arrays, lists, maps" | no | low
`FunctionalZeroConfigTest::listRoundTrip` | `List<Payload>` round-trips | same | no | low
`FunctionalZeroConfigTest::mapRoundTrip` | `Map<String,Payload>` round-trips | same | no | low
`FunctionalZeroConfigTest::recordRoundTrip` | record round-trips typed | "and records with ordinary sizes and field counts" | no | low
`FunctionalZeroConfigTest::unknownTypeNameRoundTrip` | unknown type name keeps fields in a `GenericRecord` | "unknown type names keep reading as generic records" | no | low
`FunctionalZeroConfigTest::registeredClassOverridesOtherMechanism` | `addClass(SerializablePayload)` stays Compact despite Java serialization | "Classes registered explicitly through `CompactSerializationConfig.addClass` … keep using the Compact serializer even when another mechanism applies" | no | low
`FunctionalZeroConfigTest::nestedRegisteredClassRoundTrip` | registered class nested in an unregistered envelope round-trips | same | no | low
`FunctionalZeroConfigTest::explicitSerializerRoundTrip` | `addSerializer(CustomPayloadSerializer)` round-trips | "…`CompactSerializationConfig.addSerializer` …" | no | low
`FunctionalZeroConfigTest::genericRecordValueRoundTrip` | unknown-name `GenericRecord` round-trips fields | "unknown type names keep reading as generic records" | no | low
`FunctionalZeroConfigTest::javaSerializationIsUnaffected` | `SerializablePayload` still round-trips via Java serialization | "Java serialization of serializable classes is unchanged" | no | low

**Bottom line for gate (a):** four tests (`nestedInterfaceFieldIsNotInstantiated`,
`nestedConcreteFieldIsReadAsGenericRecord`, `recordComponentIsNotInstantiated`,
`recordConcreteComponentIsReadAsGenericRecord`) demand a successful whole-value
`GenericRecord` fallback while the contract expressly permits a clean failure at exactly
those nested positions. That is a direct instruction/test contradiction, not a mere
coverage gap.

## 2. Leniency (QUALITY, non-blocking)

### Security properties / contracts

Property | most plausible wrong fix | caught? (test, checks patch)
---|---|---
P1 — eligibility decided before construction | Leave the eligibility check where the object is already built and fall back on the resulting exception (`check_after_adjustment`) | **Partly** — `serializableTypeNameIsNotConstructed`, `recordComponentIsNotInstantiated`, `arrayElementIsNotInstantiated` count constructions; `checks/miss_early_check.patch` (3 security fails). **Not caught** for `java.io.File`, `HeapData`, `Packet`, `UnsafeObjectDataInput`, product classes, or the nested interface/concrete fields, which have no construction counter; construct-then-fall-back passes those tests.
P2a — already serialized by another mechanism | Block only JDK prefixes, leave `Serializable` user classes eligible | **Caught** — `serializableTypeNameIsNotConstructed`, `nestedConcreteFieldIsReadAsGenericRecord`, `recordConcreteComponentIsReadAsGenericRecord`.
P2b — platform implementation | Curated denylist of the reported class + JDK only | **Caught** — internal trio + `schemaCarriedInTheBinaryIsAlsoRestricted` (`miss_defaults.patch`, 5 fails); `miss_routes.patch` (3 fails) for member/discovery/connector; `miss_sibling_class.patch` (1 fail) for the injected statistics class.
P2c — deployment restriction configuration excludes it | Implement no deployment-configurable exclusion at all | **NOT CAUGHT** — no test constructs a `CompactSerializationConfig` filter, allow-list or block-list. The oracle's `zeroConfigFilter` path (`fix.patch`: `ReflectiveClassFilter`) is entirely untested.
P3 — every position / schema location | Guard only the top-level value | **Caught** — 6 nested/record tests (`miss_nested.patch`, 7 fails); record sub-path by `miss_record.patch` (2 fails); array-element accessor by `miss_sibling_array.patch` (3 fails); binary schema by `schemaCarriedInTheBinaryIsAlsoRestricted`. **Not caught:** map **keys** — `mapValueIsNotInstantiated` uses `String` keys only, and `manifest.traps[nested_positions].security_tests` names `SecurityNestedValueTest::mapKeyIsNotInstantiated`, which does not exist in the tree. **Not caught:** any element/collection reader not on the shared `getArrayOfObject` path.
P4 — never delivered as the named class; generic record keeps type name and fields | Return an empty/mangled `GenericRecord` (or a `GenericRecord` with a different type name) for a restricted value | **Partially** — `instanceof GenericRecord` is checked, but no security test asserts the generic record's type name or fields. Only `unknownTypeNameRoundTrip` / `genericRecordValueRoundTrip` check field preservation, and only for unknown names. Crash-as-refusal is caught at top level by the no-exception tests.
C1 — normal read, not an error | Crash at top level as refusal | **Caught** at top level (`SecurityRestrictedTypeNameTest`, nested/record tests); **not caught** for list/map/array, which swallow exceptions.
C3 — preservation | Ban all unregistered classes (`refuse_all`) | **Caught** — `checks/disable_feature.patch`, 8 functional fails.
C4 — default for every member/client service | Install the rule only in the one builder the tests use (`DefaultSerializationServiceBuilder`) | **NOT CAUGHT** — `WireData.newService()` builds only that builder; no client service is constructed. (Tests do enforce that no deployment opt-in is required, since they use default config.)
Declarative-configuration preservation | Ignore XML/YAML registrations | **NOT CAUGHT** — only programmatic `addClass`/`addSerializer` are exercised.

### Traps (manifest.traps)

Trap | most plausible wrong fix | caught by
---|---|---
`base_instantiation_order` | Keep the eligibility decision after `createObject` and fall back on the exception | `serializableTypeNameIsNotConstructed`, `recordComponentIsNotInstantiated`, `arrayElementIsNotInstantiated`; `checks/miss_early_check.patch`
`default_block_list` | Default block list omits `HeapData`, `Packet`, `UnsafeObjectDataInput` | internal trio + `schemaCarriedInTheBinaryIsAlsoRestricted` (+ element tests); `checks/miss_defaults.patch`
`nested_positions` | Guard only the top-level type name | 6 nested/record tests; `checks/miss_nested.patch`
`record_implementation` | Do not propagate the restriction from the record serializer ("records are built through the canonical constructor, so they are safe") | `recordComponentIsNotInstantiated`, `recordConcreteComponentIsReadAsGenericRecord`; `checks/miss_record.patch`
`uncovered_member_internal` | Ship only the published fix's block list (leaves `instance.impl` open) | `SecurityProductClassTest::memberInternalTypeIsNotInstantiated`; `checks/miss_routes.patch`
`uncovered_discovery_reader` | Same, Kubernetes helper left open | `discoveryFileReaderTypeIsNotInstantiated`; `checks/miss_routes.patch`
`uncovered_connector` | Same, Jet connector left open | `connectorDataSourceTypeIsNotInstantiated`; `checks/miss_routes.patch`
`sibling_serialization_machinery_class` | Restrict application data only, leaving the serializer's own package edge | `serializationStatisticsTypeIsNotInstantiated`; `checks/miss_sibling_class.patch`
`sibling_array_element_accessor` | Leave the array-element accessor resolving the element type name itself | `arrayElementIsNotInstantiated` (and list/map per notes); `checks/miss_sibling_array.patch`

### Wrong fixes no test catches (consolidated)

1. **No deployment-configurable exclusion** (property 2c): a fix with no filter/allow-list support passes all 30.
2. **Restricted map keys**: no `mapKeyIsNotInstantiated` test exists although the manifest claims one; a fix that guards values but not keys passes.
3. **Construct-then-fall-back** outside the three counter classes (all JDK/internal/product/nested-interface/nested-concrete positions).
4. **Silently dropping nested entries**: `listElementIsNotInstantiated` / `mapValueIsNotInstantiated` assert nothing when the read fails, returns `null`, returns anything other than the typed envelope, or returns a typed envelope with an empty/dropped collection.
5. **Generic-record content loss** for restricted type names: no test pins the returned record's type name or fields.
6. **Restriction installed in only one serialization-service builder**; no client-side service is exercised (C4).
7. **Declarative (XML/YAML) registration** preservation is untested.
8. **A denylist hard-coding exactly the tested class names** is indistinguishable from a principled fix by black-box tests (only "fix the flaw and its close variants" discourages it).

## 3. Hints (QUALITY, non-blocking)

1. Quote: "it constructs the class before deciding whether it is allowed to." and "The eligibility decision must be made before the class is constructed, not afterwards." — paraphrases the `base_instantiation_order` trap and the fix order. This is also the security invariant, so it is borderline; neutralize to: *"No class may be constructed, even transiently, before it is found eligible."*
2. Quote: "The rule holds wherever a type name can occur: the top-level value, a field of another value, an element of an array, a collection or a map, and a component of a record — whether the schema travels in the schema service or inside the binary." — a 1:1 variant list matching the hidden test matrix. Neutral: *"The rule holds wherever a type name can occur — at any depth and in any position within a value — and whether the schema travels in the schema service or inside the binary."*
3. Quote: "Classes registered explicitly through `CompactSerializationConfig.addClass`, `CompactSerializationConfig.addSerializer` or declarative configuration keep using the Compact serializer…" — names the exact public API mirrored in the functional tests. Neutral: *"Classes registered explicitly in the Compact serialization configuration (class registrations, custom serializers, or declarative configuration) keep using the Compact serializer…"*
4. Quote: "The restriction must be installed by every member and client serialization service without the deployment opting in." — presupposes the oracle's installed-restriction mechanism. Neutral: *"Every member and client serialization service must apply the rule without the deployment opting in."*
5. Quote: "when the deployment's restriction configuration excludes it" — presupposes a configurable restriction/allow-list design. Neutral: *"or when the deployment's configuration excludes it."*
6. Keep: "a Compact value whose type name denotes a platform-internal or JDK class…" — the only warrant for the JDK/product tests; not a hint at a file. Also keep "Fix the flaw and its close variants, not just the shape shown." — generic, no flaw count, and no `leak_terms` string appears in the instruction.

## 4. Realism (QUALITY, non-blocking)

- **Entry point.** `InternalSerializationService.toObject(Data)` → `CompactStreamSerializer.read` →
  `getOrCreateRegistration` → `ReflectiveCompactSerializer` / `ValueReaderWriters` /
  `JavaRecordSerializer` is the real member path for every client value. The tests build the same
  service through `DefaultSerializationServiceBuilder`. The live client-protocol path was not
  booted (notes), so reachability is behavioural rather than end-to-end; acceptable, but worth
  stating as a harness caveat.
- **`base_instantiation_order`, `default_block_list`, `nested_positions`, `record_implementation`.**
  Real pinned code at real trust decisions; not planted. The missing default block list matches
  what later upstream releases added.
- **Pattern B routes** (`HazelcastInstanceProxy`, `KubernetesConfig$DefaultFileContentsReader`,
  `DataSourceFromJdbcUrl`). Real, unmodified upstream classes; instantiable from a wire type name
  at pinned and by the published fix; later upstream releases block them. Plausible. The connector
  has no no-arg constructor, which implies the reflective path allocates without a constructor —
  consistent with the stated "allocation that bypasses constructors" contract.
- **`sibling_serialization_machinery_class` (S2).** The injected `SerializationServiceStatistics`
  is ordinary maintenance code next to the serialization services, but it exists in this copy only
  as a block target; its javadoc ("not part of the serialized form of any user object") pre-empts
  the objection. Plausible but planted — a curated-denylist fix is ambushed by design. Flagged,
  acceptable with note.
- **`sibling_array_element_accessor` (S1).** The injected `readArrayElement` helper is the weakest
  realism point: it duplicates the checked registration logic and its javadoc explicitly says the
  lookup happens "from the type name directly instead of going through the same checked entry
  point that is used for top-level values". A real maintainer would not write that comment; it
  reads as a self-documenting vulnerability and hands the solver the S1 fix. The *location* is
  plausible (generic-record code duplicates read logic), but the comment should be removed or made
  neutral before the trial.

## 5. Verdict

### a. UNFAIRNESS gate: **NOT READY**

Reason: an instruction/test contradiction on nested ineligibility. The contract sentence

> "In a nested position that cannot hold a generic record the read may fail cleanly, but it must
> still never construct the named class."

expressly permits exactly the clean failure that four tests forbid:

- `SecurityNestedValueTest::nestedInterfaceFieldIsNotInstantiated` (`Payload` field cannot hold a
  `GenericRecord`; the test calls `WireData.read` with no try/catch and requires a `GenericRecord`)
- `SecurityNestedValueTest::nestedConcreteFieldIsReadAsGenericRecord` (`SerializablePayload` field)
- `SecurityNestedValueTest::recordComponentIsNotInstantiated` (`Payload` component)
- `SecurityNestedValueTest::recordConcreteComponentIsReadAsGenericRecord`
  (`SerializablePayload` component)

A competent engineer who implements the carve-out literally — let the nested read fail cleanly
after refusing to construct — satisfies every security property and fails these four tests. Both
reference fixes happen to pass, but the contract admits a third, test-failing design.

**Exact change required (either one):**

(a) *Recommended (matches "a caller must not have to catch an exception").* Replace that sentence
in `instruction.md` with:

> "When ineligibility is found while reading a nested value, the containing value must still be
> delivered as a generic record whenever it can be represented as one; only when no
> generic-record form of the containing value exists may the read fail cleanly, and even then the
> named class must never be constructed."

(b) Alternatively, loosen the four tests: wrap each read in try/catch, accept a clean failure,
and assert only that the named class was never constructed/delivered (for the two interface/concrete
field tests this would make them assertion-free unless a construction counter is added — which is
why (a) is preferable).

Secondary (recommended; not the gate failure): make the platform-class warrant explicit in
property 2 — *"The platform's own implementation covers every package the platform ships, not only
packages named 'internal'."* — so `instance.impl`, `kubernetes` and `jet.impl.connector` are
unambiguously in scope.

### b. QUALITY findings (recorded, NOT a reason for NOT READY)

- **Leniency:** no test for deployment-configured exclusion (property 2c); no map-key test
  (the manifest names `mapKeyIsNotInstantiated`, which does not exist); no construction counters
  for the JDK/internal/product/nested-field positions; list/map element tests pass vacuously on
  failure, `null`, a non-envelope result, or a typed envelope with dropped entries; no assertion
  that a restricted value's fallback record keeps its type name/fields; no client serialization
  service and no declarative-configuration coverage. Close the gaps named in §2; re-run
  `checks/*.patch` afterwards.
- **Hints:** neutralize §3 items 1–5; keep item 6.
- **Realism:** remove or neutralize the `readArrayElement` javadoc in
  `environment/inject.patch`; note the S2 class is planted; state the live-wire-path caveat.
- **Manifest hygiene:** `manifest.traps[nested_positions].security_tests` and
  `verified.variants` list tests/variants (map keys, tightened list/map assertions, 19+13)
  that the current tree does not contain. Align manifest with the actual tests.
