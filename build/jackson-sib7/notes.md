# jackson-sib7 — build notes (multi-sibling @JsonView injection)

## What this is
A sibling-stacked extension of `tasks/jackson-databind-sib`. The base task
injected ONE sibling family (`@JsonAnySetter` on `SettableAnyProperty
.deserializeAndSet`): it beat DeepSeek 0/3 but MiMo solved it on run 2. This
task keeps the original external-type-id flaw and the `deserializeAndSet`
any-setter siblings and ADDS a second, independently-unenforced invocation
route — the property-based-creator any-setter path — so a model must find and
close ALL of them.

## Ground-truth investigation (empirical, on the vulnerable commit)
I compiled jackson 2.18.4 at `d627a8a` offline and probed every candidate path
named in the prompt through the real `readerWithView(PublicView)` API:

- LEAK (genuinely unenforced): `@JsonAnySetter` as a Map field, a two-arg setter
  method, a JsonNode field, a Map constructor parameter, and a JsonNode
  constructor parameter.
- ALREADY ENFORCED (cannot host a sibling): plain `@JsonCreator` parameter,
  `@JsonUnwrapped` (databind#6060), map-valued property, polymorphic
  `As.PROPERTY`, and `readerForUpdating`/merge.

So on 2.18.4 the ONLY genuinely-unenforced deserialization family beyond the
mined `ExternalTypeHandler` path is `@JsonAnySetter`. The sibling diversity
therefore comes from that family's distinct invocation routes, which are real,
separate code sites — not re-skins of one guard.

## The siblings (5, across 3 distinct guard sites)
- S1 field any-setter (Map)      — SettableAnyProperty.deserializeAndSet (base)   = SITE 1
- S2 setter-method any-setter     — SettableAnyProperty.deserializeAndSet (base)   = SITE 1
- S3 JsonNode-field any-setter    — JsonNodeFieldAnyProperty.deserializeAndSet     = SITE 2
- S4 Map ctor-parameter any-setter  — BeanDeserializer._deserializeUsingPropertyBased buffer path = SITE 3
- S5 JsonNode ctor-parameter any-setter — same SITE 3

The decisive point: SITE 3 is reached as
`buffer.bufferAnyParameterProperty(_anySetter, k, _anySetter.deserialize(p,ctxt))`
inside the property-based creator. It NEVER calls `deserializeAndSet`, so the
guard that fixes S1/S2/S3 does not touch it. The creator-parameter any-setters
(`MapParameterAnyProperty` / `JsonNodeParameterAnyProperty`, added in
databind#562 for 2.18) inherit `SettableAnyProperty`'s total absence of view
handling AND are invoked on this separate route.

Nothing is planted into `/app`: the Dockerfile, the vulnerable checkout and
`compile-lib.sh` are identical to the base tasks. Every sibling is jackson's own
untouched code. No `if (planted)` tells.

## Oracle (`solution/fix.patch`, 3 files)
1. `ExternalTypeHandler.java` — the exact upstream hunks (original flaw).
2. `SettableAnyProperty.java` — a `visibleInView(ctxt, activeView)` accessor
   (reads the member's declared views; no `@JsonView` => visible in all views)
   and a guard at the top of `deserializeAndSet` (base + the JsonNode override)
   that discards the value when the active view hides the any-setter.
3. `BeanDeserializer.java` — one guard at the property-based-creator any-setter
   call site that skips the value (`p.skipChildren()`) when the any-setter is
   hidden in the active view. Covers S4/S5.

## Proof the upstream fix alone leaves >=1 sibling failing (decisive)
- `upstream_fix_only.patch` (ExternalTypeHandler only, byte-identical to
  tasks/jackson-databind/solution/fix.patch): local run security **5/10** pass,
  functional 20/20 pass — all 5 any-setter siblings still fail -> security_fail.
- `partial_fix.patch` (= the base jackson-databind-sib oracle: ExternalTypeHandler
  + the two `deserializeAndSet` guards, i.e. sites 1+2 but NOT 3): local run
  security **8/10** pass, functional 20/20 pass — the two creator-parameter
  siblings S4/S5 still fail -> security_fail. This is the new trap: the fix that
  fully solved the single-sibling base task is now only partial.

## Tests
- 10 security (all FAIL on vulnerable, all PASS on oracle): 5 external-type-id
  variants (ViewBypassTest) + 3 any-setter variants (AnySetterBypassTest:
  map/method/JsonNode) + 2 creator-parameter variants (AnySetterCreatorBypassTest:
  Map/JsonNode).
- 20 functional (all PASS on vulnerable and oracle): 9 external-type-id
  (ViewFeatureTest) + 6 any-setter (AnySetterFeatureTest) + 5 creator-parameter
  (AnySetterCreatorFeatureTest: admin populates Map/JsonNode ctor-param catch-all;
  no-view populates; a non-`@JsonView` ctor-param catch-all still binds under
  PublicView; the public `label` still binds when the ctor-param catch-all is
  hidden).

## Check patches
- `upstream_fix_only.patch` -> security_fail (see above).
- `partial_fix.patch`       -> security_fail (see above; the key new check).
- `disable_feature.patch`   -> functional_fail: upstream ExternalTypeHandler fix +
  an over-restrictive any-setter change that drops EVERY extra property whenever
  any view is active. Breaks functional (admin no longer populates the catch-all;
  a non-`@JsonView` catch-all is dropped under PublicView). Local run: 4
  functional fail.
- `alt_correct_fix.patch`   -> pass: a different correct fix of ALL paths — the
  ExternalTypeHandler `_hiddenInView` helper refactor + a cached-`ViewMatcher`
  `_hiddenInActiveView` any-setter helper + the BeanDeserializer creator-site
  guard routed through that same shared helper. Local run: 30/30 pass. Proves the
  tests do not hard-code the oracle's shape.

## Could not verify / caveats
- As in the base tasks, the library is compiled with `javac` against released
  `jackson-core`/`jackson-annotations` 2.18.4 rather than the exact SNAPSHOT
  siblings; the main sources compile cleanly against them. I did not re-run
  jackson's full Maven suite.
- A mapper with `MapperFeature.DEFAULT_VIEW_INCLUSION` disabled is not modelled;
  all tests use the default mapper (matching the base tasks).
- The empirical pre-checks above were run with local openjdk@21 + the released
  jars; the authoritative PASS is the Docker gate (`gate_report.json`).
