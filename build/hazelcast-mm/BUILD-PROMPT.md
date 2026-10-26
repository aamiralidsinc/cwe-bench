# Build one security-fix benchmark task (build-v1)

## What this is
We build a security-fix benchmark from published, already-fixed advisories in open-source projects.
You build ONE task, from the advisory below.

The task pins the project at the commit just before the published fix and gives a solver agent that
code plus a short problem report (`instruction.md`). Hidden behavioural tests then score the
solver's fix. The tests check that the flaw is closed, using harmless inputs and markers, and that
legitimate use still works.

Everything stays on this machine. Describe each mechanism in one line in notes and reports; the
tests hold the detail, so never write exploitation steps out in prose. Stay inside this advisory's
own protection, in this repository, at the pinned commit. Note anything outside that scope in one
line in your report, and do not build on it.

Project root: `/home/mara/cwe-bench`. Task: `hazelcast-mm`. Pattern: `A+B`. Track: `injected`.

## Goal and acceptance
- **The bar.** Two target models (DeepSeek V4.1 Flash, MiMo-V2.6-Pro) must each fail all 3
  finished attempts because of their own judgement.
- **Fairness.** Everything the tests require must be findable from `instruction.md` plus the code,
  or be standard expert knowledge. A careful engineer who knows where to look fixes it in about
  45 minutes.
- **What never counts as a failure:** timeouts, and runs cut by API or network errors.
- **Proof.** A task is built only when the gate passes. A task that misses the bar is reported as
  such, never shipped weaker.

## Inputs
- Advisory: ["GHSA-6V25-8WQ6-XQ4J", "CVE-2026-107726"]; hazelcast/hazelcast; unsafe reflection / untrusted type-name instantiation during deserialization (class allow/deny filtering, CWE-470/CWE-502-like)
- Pinned (vulnerable) commit: parent of 361979da12f18950c24719db832ca6c5e7c0534f (parent_commit not given in candidate). Published fix: 361979da12f18950c24719db832ca6c5e7c0534f.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "23901",
 "advisory_ids": [
  "GHSA-6V25-8WQ6-XQ4J",
  "CVE-2026-107726"
 ],
 "repo": "hazelcast/hazelcast",
 "pinned_commit": "parent of 361979da12f18950c24719db832ca6c5e7c0534f (parent_commit not given in candidate)",
 "fix_commits": [
  "361979da12f18950c24719db832ca6c5e7c0534f"
 ],
 "trust_decision": {
  "summary": "On deserialization the member treats the wire-supplied compact schema typeName as a class name, loads it and reflectively instantiates/populates it; whether that class is eligible for zero-config (reflective) compact deserialization is decided in CompactStreamSerializer registration (fix) instead of only a JDK-prefix check that runs after the object is already instantiated (pinned).",
  "evidence": [
   "hazelcast/src/main/java/com/hazelcast/internal/serialization/impl/compact/CompactStreamSerializer.java:183-196",
   "hazelcast/src/main/java/com/hazelcast/internal/serialization/impl/compact/CompactStreamSerializer.java:223-263",
   "hazelcast/src/main/java/com/hazelcast/internal/serialization/impl/compact/ReflectiveCompactSerializer.java:144-158",
   "hazelcast/src/main/java/com/hazelcast/internal/serialization/impl/compact/ReflectiveCompactSerializer.java:181-186",
   "hazelcast/src/main/java/com/hazelcast/internal/nio/InstanceCreationUtil.java:49-60",
   "fix.diff:1040-1049",
   "fix.diff:868-879"
  ]
 },
 "landing_point": {
  "where": "hazelcast/src/main/java/com/hazelcast/internal/serialization/impl/compact/CompactStreamSerializer.java:246-263",
  "why": "\"low-privileged client\" + \"member memory access\" leads to where a client-controlled compact typeName is turned into a Class via ClassLoaderUtil.loadClass and handed to the reflective serializer."
 },
 "fix_sites": [
  {
   "where": "hazelcast/src/main/java/com/hazelcast/internal/serialization/impl/compact/CompactStreamSerializer.java:223-228",
   "entry_point": "member toObject of client-sent compact Data (any client op whose value/key/argument is deserialized on the member) -> CompactStreamSerializer.read -> getOrCreateRegistration",
   "module_kind": "core serialization (central registration)"
  },
  {
   "where": "hazelcast/src/main/java/com/hazelcast/internal/serialization/impl/compact/CompactStreamSerializer.java:246-263",
   "entry_point": "same; typeName-to-class resolution now falls back to GenericRecord when restricted (fix.diff:1050-1066)",
   "module_kind": "core serialization"
  },
  {
   "where": "hazelcast/src/main/java/com/hazelcast/internal/serialization/impl/compact/CompactStreamSerializer.java:183-197",
   "entry_point": "same; nested restricted class rewinds and returns GenericRecord (fix.diff:1011-1037)",
   "module_kind": "core serialization"
  },
  {
   "where": "hazelcast/src/main/java/com/hazelcast/internal/serialization/impl/compact/CompactStreamSerializer.java:96-98",
   "entry_point": "canBeSerializedAsCompact used by field checks and registration (fix.diff:995-1006)",
   "module_kind": "core serialization"
  },
  {
   "where": "hazelcast/src/main/java/com/hazelcast/internal/serialization/impl/compact/CompactStreamSerializer.java:310-312",
   "entry_point": "CompactSerializationConfig.addClass / declarative <classes> registration (fix.diff:1073-1079)",
   "module_kind": "core serialization (config registration)"
  },
  {
   "where": "hazelcast/src/main/java/com/hazelcast/internal/serialization/impl/compact/ReflectiveCompactSerializer.java:181-186",
   "entry_point": "reflective read/write of zero-config classes; old check removed (fix.diff:1430-1438)",
   "module_kind": "core serialization"
  },
  {
   "where": "hazelcast/src/main/java/com/hazelcast/internal/serialization/impl/compact/record/JavaRecordSerializer.java:101-103",
   "entry_point": "zero-config Java record deserialization (fix.diff:1545-1560)",
   "module_kind": "second implementation (records)"
  },
  {
   "where": "hazelcast/src/main/java/com/hazelcast/internal/serialization/impl/compact/zeroconfig/ValueReaderWriters.java:213-241",
   "entry_point": "nested compact field / array / collection element of a reflectively serialized class (fix.diff:1574-1592)",
   "module_kind": "core serialization (field readers)"
  },
  {
   "where": "hazelcast/src/main/java/com/hazelcast/internal/serialization/impl/compact/CompactUtil.java:177-218",
   "entry_point": "JDK-prefix check removed, superseded by ReflectiveClassFilter (fix.diff:1091-1213)",
   "module_kind": "core serialization util"
  },
  {
   "where": "hazelcast/src/main/java/com/hazelcast/internal/serialization/impl/DefaultSerializationServiceBuilder.java:310-335",
   "entry_point": "every member/client SerializationService build: default blocklist (HeapData, Packet, UnsafeObjectDataInput, shaded, jctools, agrona AtomicCounter) (fix.diff:854-879)",
   "module_kind": "defaults route (builder)"
  },
  {
   "where": "hazelcast/src/main/java/com/hazelcast/internal/serialization/impl/AbstractSerializationService.java:130-136",
   "entry_point": "serialization service construction (fix.diff:793-832)",
   "module_kind": "core serialization"
  },
  {
   "where": "hazelcast/src/main/java/com/hazelcast/internal/config/AbstractDomConfigProcessor.java:236-238",
   "entry_point": "member/client XML config <compact-serialization><zero-config-filter> (fix.diff:676-691)",
   "module_kind": "config loader"
  },
  {
   "where": "hazelcast/src/main/java/com/hazelcast/internal/config/YamlMemberDomConfigProcessor.java:755-757",
   "entry_point": "member YAML config zero-config-filter (fix.diff:757-763)",
   "module_kind": "config loader (second implementation)"
  },
  {
   "where": "hazelcast/src/main/java/com/hazelcast/client/config/impl/YamlClientDomConfigProcessor.java:130-132",
   "entry_point": "client YAML config zero-config-filter (fix.diff:237-243)",
   "module_kind": "config loader (second implementation)"
  },
  {
   "where": "hazelcast-spring/src/main/java/com/hazelcast/spring/AbstractHazelcastBeanDefinitionParser.java:365-367",
   "entry_point": "Spring XML namespace <hz:zero-config-filter> (fix.diff:131-137)",
   "module_kind": "wrapper (Spring integration module)"
  },
  {
   "where": "hazelcast/src/main/java/com/hazelcast/config/ConfigXmlGenerator.java:529-535",
   "entry_point": "ConfigXmlGenerator / dynamic config export (fix.diff:496-512, 748)",
   "module_kind": "save/reload (config serializer)"
  },
  {
   "where": "hazelcast/src/main/java/com/hazelcast/config/CompactSerializationConfig.java:81-84",
   "entry_point": "public config API setZeroConfigFilter + copy constructor/equals (fix.diff:414-473)",
   "module_kind": "public config API"
  }
 ],
 "O1_entry_points": 5,
 "O2_out_of_scope_site": {
  "kind": "second_implementation",
  "where": "hazelcast/src/main/java/com/hazelcast/internal/serialization/impl/compact/record/JavaRecordSerializer.java:101-103 (Java record path chosen at CompactStreamSerializer.java:225, separate from ReflectiveCompactSerializer); also defaults route DefaultSerializationServiceBuilder.java:310-335"
 },
 "O3_reason_to_dismiss": "Records are immutable and built through their canonical constructor, and the report's gadgets (HeapData, UnsafeObjectDataInput) are plain classes, so the record serializer looks unaffected; for O8 classes, \"the advisory is about memory access, a file reader or JDBC DataSource is a different gadget\".",
 "O4_distance": {
  "files": 22,
  "packages": 8,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Zero-config compact for ordinary user POJOs/records must keep working; classes explicitly registered (addClass/addSerializer/declarative <classes>) bypass the restriction; data whose class is restricted or absent must still deserialize as GenericRecord instead of failing (fix rewinds and returns GenericRecord).",
  "where": "hazelcast/src/main/java/com/hazelcast/internal/serialization/impl/compact/CompactStreamSerializer.java:187-191; fix.diff:997-999; fix.diff:1028-1036; fix.diff:1050-1066; fix.diff:1077"
 },
 "O6_input_shapes": [
  "top-level compact object with schema in schema service (CompactStreamSerializer.java:178-181)",
  "top-level compact object with schema included in binary (CompactWithSchemaStreamSerializerAdapter.java:48-50)",
  "nested compact field of a reflective class (ValueReaderWriters.java:213-220; DefaultCompactReader.java:121-123)",
  "array / collection / map element of compact type (ValueReaderWriters.java:235-242)",
  "Java record top-level and record component (JavaRecordSerializer.java:101-103; fix.diff:1506-1526)",
  "nested compact read through GenericRecord.getObject (CompactInternalGenericRecord.java:421-423)",
  "config-registered class with reflective/record serializer (CompactStreamSerializer.java:310-312; fix.diff:1077)"
 ],
 "O7_producer": {
  "kind": "schema",
  "where": "schema typeName from wire/schema service: hazelcast/src/main/java/com/hazelcast/internal/serialization/impl/compact/CompactStreamSerializer.java:184-185,199-220; replicated via hazelcast/src/main/java/com/hazelcast/internal/serialization/impl/compact/schema/PrepareSchemaReplicationOperation.java:56; resolved registration cached in typeNameToRegistrationMap CompactStreamSerializer.java:61,243",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "Kubernetes discovery file-reader class reachable as a zero-config compact type (reads an arbitrary file path held in state)",
   "where": "hazelcast/src/main/java/com/hazelcast/kubernetes/KubernetesConfig.java:181-190",
   "reason_to_dismiss": "Package-private discovery helper, not a memory-access class; advisory is about member memory.",
   "distance": "kubernetes package vs serialization.impl.compact; different subsystem",
   "present_in_latest": "no",
   "latest_where": "latest/hazelcast/src/main/java/com/hazelcast/internal/serialization/impl/DefaultSerializationServiceBuilder.java:370"
  },
  {
   "route": "Jet JDBC DataSource adapter instantiable via Objenesis with a client-chosen jdbcUrl",
   "where": "hazelcast/src/main/java/com/hazelcast/jet/impl/connector/DataSourceFromJdbcUrl.java:32-52",
   "reason_to_dismiss": "Jet connector class with no no-arg constructor; looks like a neighbouring feature, not serialization.",
   "distance": "jet.impl.connector package",
   "present_in_latest": "no",
   "latest_where": "latest/hazelcast/src/main/java/com/hazelcast/internal/serialization/impl/DefaultSerializationServiceBuilder.java:373"
  },
  {
   "route": "Member internals (com.hazelcast.instance.impl, e.g. Node) not blocklisted",
   "where": "hazelcast/src/main/java/com/hazelcast/instance/impl/Node.java:1",
   "reason_to_dismiss": "Internal classes \"would never be sent by a client\"; only the reported memory gadgets were blocked.",
   "distance": "instance.impl package",
   "present_in_latest": "no",
   "latest_where": "latest/hazelcast/src/main/java/com/hazelcast/internal/serialization/impl/DefaultSerializationServiceBuilder.java:354"
  },
  {
   "route": "Client-side internals (com.hazelcast.client.impl.clientside) and OSGi script engine (com.hazelcast.osgi.impl) not blocklisted",
   "where": "hazelcast/src/main/java/com/hazelcast/osgi/impl/OSGiScriptEngine.java:1",
   "reason_to_dismiss": "Client-only / OSGi-only code; looks like an unsupported combination on a member.",
   "distance": "osgi.impl and client.impl.clientside packages",
   "present_in_latest": "no",
   "latest_where": "latest/hazelcast/src/main/java/com/hazelcast/internal/serialization/impl/DefaultSerializationServiceBuilder.java:362-363"
  },
  {
   "route": "UnsafeObjectDataOutput (Unsafe-write sibling of the blocklisted UnsafeObjectDataInput) not in default blocklist",
   "where": "hazelcast/src/main/java/com/hazelcast/internal/serialization/impl/UnsafeObjectDataOutput.java:50-63",
   "reason_to_dismiss": "Output stream is only written by the member itself; advisory mentions reading memory.",
   "distance": "serialization.impl package (same as builder)",
   "present_in_latest": "yes",
   "latest_where": "latest/hazelcast/src/main/java/com/hazelcast/internal/serialization/impl/DefaultSerializationServiceBuilder.java:366-374"
  }
 ],
 "O8b_injection_room": [
  {
   "where": "hazelcast/src/main/java/com/hazelcast/internal/serialization/impl/compact/CompactInternalGenericRecord.java:421-423",
   "sibling": "a GenericRecord nested-object accessor that resolves the typeName to a class through a private helper instead of getOrCreateRegistration",
   "why_realistic": "GenericRecord/query code is maintained separately from the reflective serializer and already duplicates read logic (lines 784, 1076)."
  },
  {
   "where": "hazelcast/src/main/java/com/hazelcast/internal/serialization/impl/compact/CompactStreamSerializer.java:353-379",
   "sibling": "a declarative-class registration path that builds the registration without saveRegistration's restriction check",
   "why_realistic": "Three near-duplicate registration methods already exist; a fourth (e.g. dynamic config) skipping the shared helper is plausible."
  }
 ],
 "O9_family": "unsafe reflection / untrusted type-name instantiation during deserialization (class allow/deny filtering, CWE-470/CWE-502-like)",
 "O9_dos": false,
 "O10_build": {
  "language": "Java (17+; records and pattern matching, e.g. CompactStreamSerializer.java:115)",
  "toolchain": "Maven multi-module (hazelcast, hazelcast-spring, hazelcast-sql, ...)",
  "services": [],
  "offline_after_build": true,
  "project_tests": "hazelcast/src/test/java/com/hazelcast/internal/serialization/impl/compact/ReflectiveSerializationRestrictionTest.java, AbstractReflectiveSerializationRestrictionTest.java (pinned); fix adds DefaultReflectiveSerializationRestrictionTest, NestedReflectiveRestrictionTest, ReflectiveSerializationMixedRestrictionsTest; unit-level via DefaultSerializationServiceBuilder, no cluster needed"
 },
 "O11_fix_minutes": 75,
 "O12_red_flags": [],
 "O13_recall_risk": "low",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "CompactStreamSerializer.java, ReflectiveClassFilter.java (new), ExtraReflectiveCompactSerializationRestrictions.java (new), ReflectiveCompactSerializer.java, ReflectiveCompactSerializationUnsupportedException.java, CompactUtil.java, DefaultCompactWriter.java, record/JavaRecordSerializer.java, record/JavaRecordReader.java, zeroconfig/ValueReaderWriters.java, AbstractSerializationService.java, DefaultSerializationServiceBuilder.java, config/ClassFilter.java, config/CompactSerializationConfig.java, config/ConfigAccessor.java, config/ConfigXmlGenerator.java, config/JavaSerializationFilterConfig.java, internal/config/AbstractDomConfigProcessor.java, internal/config/ConfigXmlGeneratorHelper.java, internal/config/YamlMemberDomConfigProcessor.java, client/config/impl/YamlClientDomConfigProcessor.java, hazelcast-spring AbstractHazelcastBeanDefinitionParser.java (+ XSD/JSON schemas)",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Add HeapData/UnsafeObjectDataInput to the existing check inside ReflectiveCompactSerializer.createFastReadWriteCaches, which still runs after createObject and misses the record serializer and the default-blocklist route."
 },
 "out_of_scope_notes": [
  "SQL PojoUpsertTarget has its own java-reflection-filter (hazelcast-sql/src/main/java/com/hazelcast/jet/sql/impl/inject/PojoUpsertTargetDescriptor.java:43); separate protection, not pursued.",
  "Fix diff ReaderWriterAdapter.read calls readerWriter.read twice (fix.diff:1469-1471); looks like an upstream bug, not pursued."
 ],
 "unverified": [
  "pinned_commit hash: parent_commit is null in the candidate; assumed to be the parent of the fix commit.",
  "repo_mb not measured (no shell); Hazelcast is large but giant_repo (>1.5 GB) not confirmed.",
  "O8 routes: exploitability of each class not checked; evidence is that latest upstream added them to the same default blocklist (latest DefaultSerializationServiceBuilder.java:350-376). UnsafeObjectDataOutput is only a candidate by symmetry.",
  "Fairness risk for Pattern B: the full list of dangerous classes is a denylist that a solver cannot derive from the report alone; hidden tests should check only classes a careful engineer could find (e.g. the Unsafe/Data family), or accept an allowlist-style fix.",
  "Defence ordering: pinned check in createFastReadWriteCaches runs after createObject (ReflectiveCompactSerializer.java:151 vs 155/183); behaviour with a cached reader (readFast) not traced at runtime.",
  "Java version and offline Maven build not verified from pom.xml."
 ]
}
  ```
- Published fix sites:   - hazelcast/src/main/java/com/hazelcast/internal/serialization/impl/compact/CompactStreamSerializer.java:223-228 — entry point: member toObject of client-sent compact Data (any client op whose value/key/argument is deserialized on the member) -> CompactStreamSerializer.read -> getOrCreateRegistration [core serialization (central registration)]
  - hazelcast/src/main/java/com/hazelcast/internal/serialization/impl/compact/CompactStreamSerializer.java:246-263 — entry point: same; typeName-to-class resolution now falls back to GenericRecord when restricted (fix.diff:1050-1066) [core serialization]
  - hazelcast/src/main/java/com/hazelcast/internal/serialization/impl/compact/CompactStreamSerializer.java:183-197 — entry point: same; nested restricted class rewinds and returns GenericRecord (fix.diff:1011-1037) [core serialization]
  - hazelcast/src/main/java/com/hazelcast/internal/serialization/impl/compact/CompactStreamSerializer.java:96-98 — entry point: canBeSerializedAsCompact used by field checks and registration (fix.diff:995-1006) [core serialization]
  - hazelcast/src/main/java/com/hazelcast/internal/serialization/impl/compact/CompactStreamSerializer.java:310-312 — entry point: CompactSerializationConfig.addClass / declarative <classes> registration (fix.diff:1073-1079) [core serialization (config registration)]
  - hazelcast/src/main/java/com/hazelcast/internal/serialization/impl/compact/ReflectiveCompactSerializer.java:181-186 — entry point: reflective read/write of zero-config classes; old check removed (fix.diff:1430-1438) [core serialization]
  - hazelcast/src/main/java/com/hazelcast/internal/serialization/impl/compact/record/JavaRecordSerializer.java:101-103 — entry point: zero-config Java record deserialization (fix.diff:1545-1560) [second implementation (records)]
  - hazelcast/src/main/java/com/hazelcast/internal/serialization/impl/compact/zeroconfig/ValueReaderWriters.java:213-241 — entry point: nested compact field / array / collection element of a reflectively serialized class (fix.diff:1574-1592) [core serialization (field readers)]
  - hazelcast/src/main/java/com/hazelcast/internal/serialization/impl/compact/CompactUtil.java:177-218 — entry point: JDK-prefix check removed, superseded by ReflectiveClassFilter (fix.diff:1091-1213) [core serialization util]
  - hazelcast/src/main/java/com/hazelcast/internal/serialization/impl/DefaultSerializationServiceBuilder.java:310-335 — entry point: every member/client SerializationService build: default blocklist (HeapData, Packet, UnsafeObjectDataInput, shaded, jctools, agrona AtomicCounter) (fix.diff:854-879) [defaults route (builder)]
  - hazelcast/src/main/java/com/hazelcast/internal/serialization/impl/AbstractSerializationService.java:130-136 — entry point: serialization service construction (fix.diff:793-832) [core serialization]
  - hazelcast/src/main/java/com/hazelcast/internal/config/AbstractDomConfigProcessor.java:236-238 — entry point: member/client XML config <compact-serialization><zero-config-filter> (fix.diff:676-691) [config loader]
  - hazelcast/src/main/java/com/hazelcast/internal/config/YamlMemberDomConfigProcessor.java:755-757 — entry point: member YAML config zero-config-filter (fix.diff:757-763) [config loader (second implementation)]
  - hazelcast/src/main/java/com/hazelcast/client/config/impl/YamlClientDomConfigProcessor.java:130-132 — entry point: client YAML config zero-config-filter (fix.diff:237-243) [config loader (second implementation)]
  - hazelcast-spring/src/main/java/com/hazelcast/spring/AbstractHazelcastBeanDefinitionParser.java:365-367 — entry point: Spring XML namespace <hz:zero-config-filter> (fix.diff:131-137) [wrapper (Spring integration module)]
  - hazelcast/src/main/java/com/hazelcast/config/ConfigXmlGenerator.java:529-535 — entry point: ConfigXmlGenerator / dynamic config export (fix.diff:496-512, 748) [save/reload (config serializer)]
  - hazelcast/src/main/java/com/hazelcast/config/CompactSerializationConfig.java:81-84 — entry point: public config API setZeroConfigFilter + copy constructor/equals (fix.diff:414-473) [public config API]
- Uncovered routes to confirm (pattern B):   - hazelcast/src/main/java/com/hazelcast/kubernetes/KubernetesConfig.java:181-190 — Kubernetes discovery file-reader class reachable as a zero-config compact type (reads an arbitrary file path held in state) (reason to dismiss: Package-private discovery helper, not a memory-access class; advisory is about member memory.; still in latest: no)
  - hazelcast/src/main/java/com/hazelcast/jet/impl/connector/DataSourceFromJdbcUrl.java:32-52 — Jet JDBC DataSource adapter instantiable via Objenesis with a client-chosen jdbcUrl (reason to dismiss: Jet connector class with no no-arg constructor; looks like a neighbouring feature, not serialization.; still in latest: no)
  - hazelcast/src/main/java/com/hazelcast/instance/impl/Node.java:1 — Member internals (com.hazelcast.instance.impl, e.g. Node) not blocklisted (reason to dismiss: Internal classes "would never be sent by a client"; only the reported memory gadgets were blocked.; still in latest: no)
  - hazelcast/src/main/java/com/hazelcast/osgi/impl/OSGiScriptEngine.java:1 — Client-side internals (com.hazelcast.client.impl.clientside) and OSGi script engine (com.hazelcast.osgi.impl) not blocklisted (reason to dismiss: Client-only / OSGi-only code; looks like an unsupported combination on a member.; still in latest: no)
  - hazelcast/src/main/java/com/hazelcast/internal/serialization/impl/UnsafeObjectDataOutput.java:50-63 — UnsafeObjectDataOutput (Unsafe-write sibling of the blocklisted UnsafeObjectDataInput) not in default blocklist (reason to dismiss: Output stream is only written by the member itself; advisory mentions reading memory.; still in latest: yes)
- Design plan from the lead: No lead plan is provided for this task — you are the lead as well as the builder. Using the Design section above and the screener record, design the task yourself and WRITE YOUR PLAN in `notes.md` BEFORE you build:
  - choose the main lever and at least one more, each with a DIFFERENT reason a solver would dismiss or skip it;
  - decide the sites, routes and input shapes the security tests will cover;
  - identify the coupled must-keep-working behaviour next to each lever, for the functional tests;
  - for the injected track: decide the realistic sibling gap(s) to add — each must be code a maintainer could plausibly have left, reachable through the real entry point, covered by a stated invariant, and placed where the published fix never touches. Add 2–4 siblings at a recurring trust decision, each with its own reason a solver would skip it;
  - if this candidate cannot support a fair task that meets the bar (flaw does not reproduce at the pinned commit through a real entry point, needs network/GPU/GUI at run time, or no design meets the bar), STOP and report why. Do not ship a weak task.
Follow every rule in the Design, Report, Tests and Proof sections exactly. You choose the design; the rules are fixed.
- Host notes: none

## Design: where difficulty comes from
Models find the code the report leads to and diagnose it correctly. They fail on scope. Build these
in, in order of evidence:
1. **Pattern A: the published fix's far sites.**
   - The report leads to one site. The tests cover every entry point the published fix protects,
     including one in a module that looks out of scope: a second implementation, a lower-level
     public API, a wrapper, a save/reload path, or a defaults or merge route.
   - Give it a plausible **reason to dismiss**, and **distance**: another file or package from the
     landing point.
2. **Pattern B: uncovered routes.**
   - Routes into the same protected sink where the advisory's own protection is missing at the
     pinned commit, and which the published fix did not touch.
   - They are unmodified upstream code, so a solver can argue they were never covered.
   - The strongest lever found so far: DeepSeek 6 of 6 on one; both models 0 of 3 on three combined.
3. **Input-shape variants** that the general rule covers but a one-case fix misses (a plain string
   and an array).
4. **A coupled must-keep-working behaviour** next to the sink, tested functionally, so an
   over-broad fix fails. MiMo tends to over-harden.
5. **Producer off the check's path.** The check depends on data produced elsewhere (a schema,
   serializer, cache, mapper or config loader) and does not call it. It counts only if the producer
   is infrastructure, not a request handler.
6. **Injected siblings**, only where the plan asks for them. Each must be:
   - code a maintainer could have written, with no deceptive names or comments;
   - reachable through the real entry point;
   - covered by a stated invariant;
   - placed where the upstream fix never touches.

Aim for at least two levers with **different** reasons to dismiss.

Never add:
- encoding, verb, protocol or role/direction variants;
- more routes of one concept;
- resource-exhaustion traps.

Every lever must be findable by a blind engineer from the report and the code. A lever that a blind
fix cannot find is unfair: remove it.

**Pattern B rules:**
- Confirm each route with a behavioural test on the pinned copy before relying on it. The
  screener's claim is only a lead.
- Append one row per route to `/home/mara/cwe-bench/build/audit/uncovered-routes.tsv`, using its existing
  header. Columns:
  - `task`, `repo`, `advisory`;
  - `trap_ref` (the manifest trap id only; no mechanism text, since the manifest holds the detail);
  - `real_upstream`;
  - `present_in_latest` (`yes`, `no` or `unknown`, from a read-only look at current upstream code if
    you can reach it);
  - `public_upstream_report`, `in_current_scope`, `built`, `note`;
  - `disclosure_status` (`pending client decision`).

## Environment (`tasks/hazelcast-mm/environment/Dockerfile`)
- **Base and code.** A small official base image. The repo goes into `/app` at the pinned commit,
  and `/app/.git` is then deleted.
- **Offline.** Install every dependency, tool and service the project and tests need; nothing may
  be downloaded at test time. Services start from `test.sh`.
- **Packages:** `patch`, `curl`, `ca-certificates`, `bash`, `git`.
- **Agent layer.** Append `harness/claude-code.Dockerfile.snippet` unchanged at the end.
- **No test code in the image.** The agent shares the container. Pre-build against stubs; `test.sh`
  copies the real tests in at grading time.
- **Project tests.** The project's own tests for the affected area must pass in the image at the
  pinned commit.
- **No leaked regression tests.** The pinned commit must not already contain the advisory's
  regression tests (check `git log` between the pinned and fix commits).

## Report to the solver (`tasks/hazelcast-mm/instruction.md`)
**Write:**
- what the system is, at product level;
- one observed impact, with ONE concrete trigger at user level (HTTP request, CLI call or public API
  use);
- the security properties as **invariants**: who may do what to which data, or what attacker input
  must never achieve. Word each so it covers every tested route and shape ("no value of X may …").
  If there are several, give one natural list, never a count;
- every **contract** the tests need:
  - the refusal form ("a client error with no side effect");
  - any interface or field name a test uses;
  - preservation clauses ("works exactly as today");
  - a legitimate magnitude next to any attack magnitude;
- that examples are examples, not the full set;
- the standard constraints block: fix the problem and its close variants; keep legitimate use
  working; do not modify or add tests; do not look up the upstream fix; do not special-case the
  example.

**Never write:**
- file, package, function, class, field or parameter names a user would not see;
- line numbers, the root cause, the fix approach, or a CVE or GHSA id;
- a list of routes, spellings or roles;
- restricting adverbs ("directly", "only via");
- anything that names or paraphrases a far site, an uncovered route or an injected sibling.

Put every identifier that must not appear in `manifest.leak_terms`.

## Tests (`tasks/hazelcast-mm/tests/`)
- **`security/`:** one test per site, route, input shape and form. Each one:
  - goes through the real entry point;
  - fails on the pinned code and passes on a correct fix;
  - asserts the attack is blocked: any client error plus no side effect, never one exact status.
- **`functional/`:**
  - legitimate use, including the coupled behaviour of every lever;
  - where they exist, the project's own tests for the area.
- **No product code in a test's bookkeeping.** Compute expected values and clean-ups in the test
  itself, because a hardened helper must not crash a test.
- **Stubs** of permission or authority answer per resource and verb, like the real thing.
- **Scope.** A test may vary only what the instruction names, and drive only the entry point it
  names.
- **No network**, and nothing that depends on the fix commit being present.
- **Templates.** JUnit XML into the two directories the template names. Copy `score.py` unchanged.
  Edit only the marked command lines of `test.sh`, and keep its agent-kill block.

## Proof
- **The oracle.** `solution/fix.patch` is the published fix reduced to source changes, plus fixes
  for every uncovered route and injected sibling in the task. `solution/solve.sh` applies it to
  `/app`.
- **Wrong-fix patches** go in `build/hazelcast-mm/checks/`, listed in `manifest.patch_checks`:
  - one `security_fail` per lever (the fix that misses only that lever);
  - a `functional_fail` (an over-broad or feature-removing fix);
  - a `pass` of kind `hardening` (the oracle plus defensive hardening of the product code the
    security tests import);
  - a `pass` alternative fix where a second valid design is plausible.
- **`manifest.wrong_fix_catalogue`:** for each class, a `checks/` patch, or `n/a: <why>`:
  `refuse_all`, `crash_as_refusal`, `wrong_resource`, `one_role_or_direction`, `reads_only`,
  `check_after_adjustment`, `unlisted_route`, `malformed_identity`, `missing_authority`,
  `adjacent_api`.

## Deliverables
**`tasks/hazelcast-mm/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/hazelcast-mm/manifest.json`:**
- `slug`, `candidate`;
- `pattern`: `A+B`;
- `builder_prompt_version`: `build-v1`;
- `"strict_gate": true`;
- `verified`: entry point, sites, routes, services, project tests run;
- `leak_terms`, `patch_checks`, `wrong_fix_catalogue`;
- `traps`: one entry per lever, with `shape`, `where` (file:line), `security_tests`,
  `coupled_functional_tests`, `security_fail_patch`, and `realistic_because` (for pattern B: "real,
  unmodified upstream code");
- `status`.

**Also in `build/hazelcast-mm/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py hazelcast-mm --only static
python3 -I builder/gate.py hazelcast-mm --only nop
python3 -I builder/gate.py hazelcast-mm --only oracle
python3 -I builder/gate.py hazelcast-mm --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/hazelcast-mm/`;
  - edit only `tasks/hazelcast-mm/`, `build/hazelcast-mm/` and, for pattern B, the register;
  - do not commit.

## Stop and report instead of shipping when
- the flaw does not reproduce through a real entry point at the pinned commit;
- a planned route or site is not reachable, or the check calls the producer directly (substitute
  another lever the code supports if you can, and say so);
- the task needs network at run time, or a GPU, kernel or GUI;
- the tests are flaky;
- no design meets the bar.

## Report back (under 400 words)
- The gate result for each stage.
- Each lever in one line: pattern, shape, file:line, reason to dismiss.
- Pattern B: each register row.
- The instruction's word count.
- Every guess you could not verify.
- Any fairness concern you see yourself.
- Anything noticed outside the scope, in one line.
- If abandoned, exactly why.
