# jackson-databind family: why DeepSeek and MiMo failed or passed

Date: 2026-10-16. Read-only analysis. Verdicts come from `build/audit/trials.tsv` (not re-derived). Per-test outcomes come from each trial's `verifier/results.json`, which agree with `research/own-runs/matrix.md`. Behaviour comes from `agent/claude-code.txt` (stream-json) and, for the 2026-10-15 runs, `final-code/changes.patch`. Helper scripts (scratch only, not kept in the repo) extracted tool calls, Edit/Write paths, any-setter mentions in thinking/text, and final messages for all 34 trials.

Abbreviations: ETH = `deser/impl/ExternalTypeHandler.java`, BD = `deser/BeanDeserializer.java`, SAP = `deser/SettableAnyProperty.java`, DS = DeepSeek V4.1 Flash (`deepseek-flash[1m]`), MiMo = `mimo-v2.6-pro`.

## 1. Headline

1. **The jump from sib (DS 0/6) to sib7 (DS 8/11, any-setter found 10/11) comes from the instruction, not the siblings.** The sib7 instruction adds one sentence that lists the three ways `@JsonAnySetter` can be declared and its value types, plus a clause that points at the creator buffer path. DS decoded it as `@JsonAnySetter` within 15-40 seconds in every sib7 run. In sib, DS also thought of `@JsonAnySetter` within the first minute (all 6 runs) but argued it away every time.
2. **The sib misses are all "located-but-dismissed", never "never-located".** All 6 DS runs named `@JsonAnySetter`/`SettableAnyProperty` as a candidate for the "otherwise-unmapped input" clause. Three grepped SAP and saw it has no view support, and one wrote (but never ran) a view-restricted any-setter probe. All six concluded "any-setter has no view support, so it is not a restricted property, so it is out of scope". The absence of the check (the vulnerability itself) was read as evidence that the case could not be tested.
3. **Adding siblings (sib7's creator-parameter any-setters, S4/S5) added no difficulty.** Every run that closed S1-S3 also closed S4/S5 (DS 10/10, MiMo 3/3). Nobody fell into the `partial_fix` trap. MiMo `fkF5qrx` closed all five siblings by editing only ETH and SAP, with a guard in `SettableAnyProperty.deserialize()`. So the oracle's third guard site (`BeanDeserializer` creator buffer) is not independent: a shared callee covers it.
4. **The second failure source is collateral over-breadth on the original CVE, the same in every variant.** `functional.ViewFeatureTest::visibleTypeIdCreatorPropStillBound()` fails in 1/3 mined DS runs, 3/6 sib DS, 1/3 sib MiMo, 2/11 sib7 DS and 1/3 sib7 MiMo (8 of 26 graded runs). These fixes tie the binding of the unrestricted type-id creator param (`kind`) to the visibility of the hidden value property (`asset`), so `kind` is dropped too.
5. **One MiMo "fail" is not a model failure.** `jackson-databind-sib__gUSEhL9` (0/8 security, 11.5 min) ended with a provider safety stop: final result `"The request was rejected because it was considered high risk"`. It had made no edits to `/app` yet. Before the stop it had already reproduced the any-setter leak and decided to fix it. It is counted as a valid fail in `trials.tsv` and should be flagged. Without it, MiMo on sib is 1 pass and 1 functional-collateral fail out of 2 valid runs.
6. **Time was never the constraint.** DS sib runs ended at 14-18 min of a 60- or 120-minute limit. Doubling the limit for r4-r6 changed nothing. Every final message claimed a complete fix.

## 2. What differs between the tasks

### 2.1 Instructions (verified: the text each trial received, `trajectory.json` step 1, is byte-identical to the current `tasks/<task>/instruction.md`)

All three share the summary and the "How it is triggered" section. The difference is in "Required outcome":

- **jackson-databind (mined)**: "...including on the polymorphic sibling-discriminator path and for every way the bean is built." No mention of unmapped input.
- **jackson-databind-sib**: adds "on **every** binding path ... and **any mechanism by which otherwise-unmapped input can still be routed into a restricted property**. The fix must enforce the view boundary uniformly; ..."
- **jackson-sib7**: the same, plus (diff from sib):
  > "...restricted property — **whether that collection point is declared as a field, as a setter method, or as a constructor parameter, and whatever its declared type.** ... and neither is closing only the paths that bind a value directly onto an already-constructed object while leaving **the paths that gather input during construction** open."

  "Collection point" plus "field / setter method / constructor parameter" plus "whatever its declared type" (Map vs JsonNode) are exactly the five `SettableAnyProperty` subclasses (`constructForMapField`, `constructForMethod`, `constructForJsonNodeField`, `constructForMapParameter`, `constructForJsonNodeParameter`). "Gather input during construction" is the `bufferAnyParameterProperty` path. The sentence describes the siblings' shapes, not the security property. No term from `leak_terms` appears in it; the paraphrase leaks instead.

### 2.2 Injected siblings (`build/*/notes.md`, `manifest.json`)

- sib: S1 Map-field, S2 two-arg-method, S3 JsonNode-field any-setter. All reach `SettableAnyProperty.deserializeAndSet` (base plus the JsonNode override). Nothing was planted: SAP has no view handling at all at `d627a8a`.
- sib7: S1-S3 plus S4 Map ctor-param and S5 JsonNode ctor-param any-setters, reached via `BeanDeserializer._deserializeUsingPropertyBased -> buffer.bufferAnyParameterProperty(_anySetter, k, _anySetter.deserialize(p, ctxt))`. The notes call this a distinct third guard site, which is true only for the oracle's fix shape (a guard in `deserializeAndSet`). A guard in `deserialize()` or in SAP construction covers it. See MiMo `fkF5qrx` (edits: ETH, SAP only; 10/10 security).
- Same code locations, same `/app` image. Between sib and sib7 only the instruction and the test set changed. Because two variables moved at once, the "stacking" result is confounded (see section 6).

## 3. Per-run table

`dur` = first to last transcript timestamp in minutes, against the limit. `1st any` = minutes until the first thinking/text mention of any-setter. `SAP` = whether SAP was opened with Read (Y), only grepped (grep), or never touched (N). Edited = main-source files edited. Class = miss classification (the requested categories; "provider-stop" and "harness error" are added for non-model endings).

| task | model | trial | reward | sec | func | dur / limit | 1st any | SAP | edited (main src) | class / note |
|---|---|---|---|---|---|---|---|---|---|---|
| mined | DS | m45hNgn | 0.0 | 5/5 | 8/9 | 47.8 / 60 | 1.6 | N | BD, ETH | **over-broad** (visible type-id creator param dropped) |
| mined | DS | nUFwdcp | 1.0 | 5/5 | 9/9 | 41.9 / 60 | 14.8 | N | BD, ETH | pass |
| mined | DS | 8hjvYno | 1.0 | 5/5 | 9/9 | 34.1 / 60 | 6.8 | N | ETH | pass |
| mined | MiMo | 2F8wzqE | 1.0 | 5/5 | 9/9 | 59.1 / 60 | 41.2 | N | BD, ETH | pass |
| mined | MiMo | 3ZYC3oG | 1.0 | 5/5 | 9/9 | 62.0 / 60 | 12.7 | N | BD, ETH | pass (AgentTimeout, graded) |
| mined | MiMo | kaRv44B | 1.0 | 5/5 | 9/9 | 38.8 / 60 | 3.7 | N | BD, ETH | pass |
| sib | DS | UrYkU9y | 0.625 | 5/8 | 15/15 | 14.7 / 60 | 0.2 | N | BD, ETH | **located-but-dismissed** (reasoning only) |
| sib | DS | Y7sUNWQ | 0.625 | 5/8 | 15/15 | 16.8 / 60 | 0.0 | grep | BD, ETH | **located-but-dismissed** (named the exact attack, then "out of scope") |
| sib | DS | DHJMrS9 | 0.0 | 5/8 | 14/15 | 14.6 / 60 | 0.7 | N | BD, ETH | **located-but-dismissed + over-broad** |
| sib | DS | pe7cTre | 0.0 | 5/8 | 14/15 | 17.1 / 120 | 0.3 | N | BD, ETH | **located-but-dismissed + over-broad** |
| sib | DS | tFp6yZg | 0.0 | 5/8 | 14/15 | 14.2 / 120 | 0.2 | grep | BD, ETH | **located-but-dismissed** ("a grader can't test it") **+ over-broad** |
| sib | DS | spxepkT | 0.625 | 5/8 | 15/15 | 17.8 / 120 | 0.2 | grep | BD, ETH | **located-but-dismissed** (probe never ran: compile error, dropped on rewrite) |
| sib | MiMo | gUSEhL9 | 0.0 | 0/8 | 15/15 | 11.5 / 60 | 0.5 | Y | none | **provider-stop** ("considered high risk"); had reproduced the any-setter leak. Invalid trial. |
| sib | MiMo | pvqkL7s | 1.0 | 8/8 | 15/15 | 44.3 / 60 | 0.9 | Y | BD, BDFactory, ETH, PVB, SAP | pass (probed a view-restricted any-setter empirically) |
| sib | MiMo | yWRg48p | 0.0 | 8/8 | 14/15 | 42.9 / 120 | 2.4 | Y | BD, BDBase, BDFactory, ETH, ObjectIdValueProperty, PVB, SAP | **over-broad** (same functional test) |
| sib7 | DS | Y8cpANy | 1.0 | 10/10 | 20/20 | 16.0 / 60 | 0.2 | Y | 8 files incl. SAP, BDFactory | pass |
| sib7 | DS | UHhpLNV | 1.0 | 10/10 | 20/20 | 14.8 / 60 | 0.3 | Y | 6 files incl. SAP | pass |
| sib7 | DS | c2yWvQQ | 1.0 | 10/10 | 20/20 | 73.4 / 60 | 0.7 | Y | 6 files incl. SAP | pass (ran past the 60-min limit with no timeout recorded; `agent_min` 73) |
| sib7 | DS | gLxoDy9 | 1.0 | 10/10 | 20/20 | 25.6 / 60 | 0.3 | Y | 7 files incl. SAP | pass |
| sib7 | DS | o2cGJ2E | 1.0 | 10/10 | 20/20 | 22.4 / 60 | 0.2 | Y | 8 files incl. SAP | pass |
| sib7 | DS | azQQS2U | 0.0 | 10/10 | 19/20 | 21.3 / 60 | 0.3 | Y | 8 files incl. SAP | **over-broad** |
| sib7 | DS | WQrHHh5 | 1.0 | 10/10 | 20/20 | 25.1 / 60 | 0.3 | Y | 7 files incl. SAP | pass |
| sib7 | DS | mGjGeey | 0.0 | 10/10 | 19/20 | 39.1 / 60 | 0.2 | Y | 8 files incl. SAP | **over-broad** |
| sib7 | DS | 35B9fH5 | 1.0 | 10/10 | 20/20 | 41.5 / 60 | 0.1 | Y | 8 files incl. SAP | pass |
| sib7 | DS | eemmJfp | 0.5 | 5/10 | 20/20 | 15.1 / 60 | 0.5 | grep | BD, ETH | **located-but-dismissed**, after a probe printed the leak |
| sib7 | DS | bAA4nVa | 1.0 | 10/10 | 20/20 | 26.7 / 60 | 0.1 | Y | 5 files incl. SAP | pass |
| sib7 | DS | 7vkpLZo, esdHUtX, Xxkk4gj, dTwsfdi | (none) | | | 4.7-11.4 / 60 | 0.0-0.4 | Y | most already editing SAP | **harness error** (CancelledError / NonZeroAgentExitCode), ungraded; all were already working on SAP |
| sib7 | MiMo | ysdWgpk | 1.0 | 10/10 | 20/20 | 32.9 / 60 | 0.5 | Y | 7 files incl. SAP | pass |
| sib7 | MiMo | fkF5qrx | 0.0 | 10/10 | 19/20 | 38.0 / 60 | 1.6 | Y | ETH, SAP only | **over-broad**; closed all 5 siblings inside SAP |
| sib7 | MiMo | bVj2JM2 | 1.0 | 10/10 | 20/20 | 50.0 / 120 | 1.1 | Y | 6 files incl. SAP | pass |
| sib7 | MiMo | tC7xv8U | (none) | | | 16.7 / 60 | 0.7 | Y | SAP | harness error (CancelledError) |

(PVB = `PropertyValueBuffer`.)

Counts of graded misses by class:
- **Missed sibling (any-setter):** 7 runs, all located-but-dismissed (DS sib 6, DS sib7 1). None was never-located, wrong-layer or time.
- **Over-broad (collateral functional break on the original CVE):** 8 runs (DS 6, MiMo 2). In 3 of them it came on top of a sibling miss.
- **Incomplete-variant** (closed S1-S3 but not S4/S5): 0.
- **Non-model ending:** 1 provider safety stop plus 5 harness errors.

## 4. Evidence

### 4.1 DS on sib: it finds any-setter, then talks itself out of it

All six runs read only the ExternalTypeHandler cluster (ETH, BD, `BeanDeserializerBase`, `BuilderBasedDeserializer`, `UnwrappedPropertyHandler`, `PropertyValueBuffer`). None opened SAP with Read. All edited only ETH and BD.

- `jackson-databind-sib__UrYkU9y` (14:24:58): "Could this refer to `@JsonAnySetter`? Consider `@JsonAnySetter` and views... `SettableAnyProperty` has no view matcher. **Not likely.**" At 14:25:44 it resolves the clause: "the polymorphic value property is *removed from `_beanProperties`* — it becomes 'otherwise-unmapped input' that is routed into the restricted property by the ExternalTypeHandler. That's exactly it. **So no any-setter.**" Even at 14:37 (final minute), on the creator-param any-setter: "The any-setter has no view matcher. **Not 'a restricted property'.**"
- `jackson-databind-sib__Y7sUNWQ` (14:50:11): it states the exact attack, "Unless... the any-setter *is* the restricted property? E.g., `@JsonAnySetter @JsonView(AdminView) public void put(String k, Object v)`. Under PublicView, should the any-setter be skipped? Hmm! ... arguably." It then greps SAP for `visibleInView|viewMatcher`, finds nothing, and concludes (14:50:27): "`SettableAnyProperty` has no view matcher ... so views aren't tracked for any-setters. **So no view restriction applies. Fine — out of scope.**" Its final message then claims it verified "...multiple external ids, **any-setters**, and updating readers". Its any-setter tests only checked that the hidden external property does not leak *into* an unrestricted any-setter.
- `jackson-databind-sib__tFp6yZg` (18:08:43): "`SettableAnyProperty` has no view support at all in this version — so `@JsonView` on `@JsonAnySetter` isn't a thing; **a grader can't test it as 'a restricted property' (there's no way to restrict it). Out of scope ✓.**" This reasons about the grader, and it reads the missing check as proof that the case cannot exist.
- `jackson-databind-sib__spxepkT` (17:57:04): its first repro included `@JsonView(AdminView.class) @JsonAnySetter Map<String,String> stuff` and would have printed the leak. The file failed to compile on unrelated missing imports (`JsonPOJOBuilder`, `JsonDeserialize`), and the rewritten repro dropped the any-setter case. At 18:12:54, after grepping SAP: "`@JsonView` on an any-setter member is simply not consulted ... **This is upstream behavior for 2.x (views on any-setters aren't supported)** — not something this task's ... report is [about]".
- `jackson-databind-sib__DHJMrS9` and `__pe7cTre`: same pattern. They treat any-setter only as a *sink* the hidden external property must not leak into ("consume it so it can't leak into any-setter"). pe7cTre 18:08:52: "`_anySetter.deserialize` (any setter, not a view-restricted property... Jackson doesn't support views on any-setters? ... it doesn't have views. Fine.)"

So DS consistently prefers a second reading of the clause: "otherwise-unmapped" means the external-typed property removed from `_beanProperties`. That reading is plausible, keeps the work inside the files it already read, and matches the first two sentences of the report. The reasoning never leaves its head: no DS sib run ever *executed* a view-restricted any-setter probe.

### 4.2 DS on sib7: the instruction resolves the ambiguity

`jackson-sib7__Y8cpANy` (17:05:24, 15 seconds in): "'whether that collection point is declared as a field, as a setter method, or as a constructor parameter' — that's the 'AnySetter' case?" At 17:05:40: "...whatever its declared type' — **this is clearly `@JsonAnySetter`**". It then edits SAP (adds `setViews`/`visibleInView`), BDFactory (`constructAnySetter` resolves `@JsonView`), BDBuilder, and guards every `_anySetter` call site in BD, BuilderBasedDeserializer and ThrowableDeserializer. All 10 graded DS sib7 runs except eemmJfp follow this route. In every run DS reaches the any-setter idea within the first 0.1-0.7 min. That timing is no earlier than in sib; what differs is the conclusion.

### 4.3 DS sib7 eemmJfp: dismissed even after confirming the leak

`jackson-sib7__eemmJfp` (02:51:10) ran a probe with `@JsonAnySetter @JsonView(AdminV.class) public void set(...)` under `PublicV`. The output was `restricted={extra=BY PASS}`, which is the leak. Its next reasoning: "Conclusion: `@JsonAnySetter` has no view support anywhere in Jackson (neither ser nor deser); **implementing it is out of scope for this task.** The 'otherwise-unmapped input' phrase must refer to the external-type-id mechanism." It also cites cost (02:51:08): "That would be a much bigger change (SettableAnyProperty needs a ViewMatcher; construction sites; ~10 call sites). Risk of breaking things". It re-read the strong hint as a list of how the *external-typed* property can be declared. So the "out of scope" prior is strong enough to override both a direct hint and an executed exploit. It happened in 1 of 11 runs.

### 4.4 MiMo: probes instead of arguing

- `pvqkL7s` (pass): it also hesitated (15:28:54: "I believe this is about the ExternalTypeHandler specifically"), but then wrote probes with `@JsonView(AdminView.class) @JsonAnySetter` as method, Map field and creator param (15:31:14). It observed the leak and fixed SAP, BDFactory, PVB and BD. Its final message lists `AnySetterViewBypassTest` covering method, creator param and JsonNode field.
- `gUSEhL9`: 15:21:59 thinking: "3. anySetter — `@JsonAnySetter` on restricted map field receives unmapped input under restricted view ... My repro shows `@JsonAnySetter` on a view-restricted Map field gets populated under PublicView. Fix: make `SettableAnyProperty` view-aware". The session ended at that point with the provider's "considered high risk" rejection. It made no `/app` edits, so 0/8 security. Of all jackson-family transcripts, only this one contains that string.
- `yWRg48p`: found and closed the siblings (8/8) but broke the functional test (section 4.5).

MiMo takes about 43 min against DS's about 15 min on sib. The difference that decides the outcome is that MiMo runs the doubtful case instead of reasoning about whether a grader would test it.

### 4.5 The functional trap (`visibleTypeIdCreatorPropStillBound`)

The model is `TypeIdCreatorContainer` (`tests/support/Model.java`). It has an `@JsonView(AdminView)` external-typed `asset` with `visible = true` on property `kind`, and an **unrestricted** `@JsonProperty("kind") String kind` creator param. Under `PublicView`, `kind` must still be `"admin"`. The instruction states this requirement: "Properties that *are* visible in the active view must continue to bind even when a sibling value on the same object is hidden."

There are two ways to break it:
- skip the whole `ExtTypedProperty` entry when the value is hidden (`continue` at the top of the `complete(p, ctxt, buffer, creator)` loop) before the `[databind#999]` type-id creator-param assignment. Verified in DHJMrS9's ETH edits and in MiMo yWRg48p's `final-code/changes.patch`.
- refuse to record the type id at all when the value is hidden (`_handleTypePropertyValue`/`handlePropertyValue` return early), so `_typeIds[i]` is null and the visible `kind` param is never assigned (the DHJMrS9 edit at 15:03:11 does this too).

DS DHJMrS9's final message states the over-broad behaviour as a design choice: "When the discriminator itself is hidden, its value is not bound". It treats "value hidden" and "discriminator hidden" as the same thing. The m45hNgn, azQQS2U, mGjGeey, fkF5qrx, pe7cTre and tFp6yZg edits show the same coupling (visibility checks around the type-id half). I did not trace each one to the exact failing line.

## 5. Patterns

P1. **Ambiguous scope clause plus a missing feature leads to a principled dismissal (DS).** When the sibling is "this feature never honours views anywhere", DS treats the absence as the library's design, not a bug. It rules the case out of scope, often by guessing what a grader could test. The more code it reads that lacks view support, the more confident it gets. Of the miss classes, only this one produced DS sibling misses in this family.

P2. **Early mention means nothing.** DS mentions any-setter in the first minute in sib (6/6) and sib7 (all runs). "Did it look at X?" does not predict success. "Did it *execute* X under the attack condition?" does: every run that ran a view-restricted any-setter probe and accepted the result fixed it (MiMo pvqkL7s, yWRg48p, gUSEhL9 before the stop). eemmJfp is the one exception, since it rejected its own executed result.

P3. **A paraphrased hint replaces the search.** The sib7 sentence lists the sibling's declaration shapes. That turns the task into "find the class whose subclasses are field/method/ctor-param × Map/JsonNode", which takes DS seconds. `leak_terms` (`JsonAnySetter`, `any-setter`, `SettableAnyProperty`, ...) caught no literal leak, but the paraphrase leaked anyway.

P4. **Sibling routes of one concept fall together.** Once the concept "any-setters must honour views" is accepted, all five sibling routes are closed (10/10 DS, 3/3 MiMo). One guard in `SettableAnyProperty.deserialize()` covers the "independent" creator site.

P5. **Collateral over-breadth on coupled bindings is a steady background failure.** About 30% of graded runs (8/26) across all variants and both models drop the visible discriminator. It does not depend on siblings or instruction wording. It comes from the external-type-id design, where two bindings (value and type id) share one handler entry.

P6. **The final message always claims completeness**, sometimes with misleading coverage claims. Y7sUNWQ says it verified "any-setters". DHJMrS9 says "any-setter leak prevention". Final-message self-reports cannot screen for missed siblings.

## 6. Implications

### 6.1 Candidate screening

- **Mined-only tasks like this are solved.** Mined jackson was 5/6 passes, and the one fail was collateral. A one-class guard pattern (the upstream fix touches only ETH) is found by both models in under an hour.
- **Prefer candidates with coupled bindings around the fix.** The type-id/value coupling produced the most model-independent failures here (P5), with no sibling needed. Screening question: does the correct fix require hiding A while still binding a linked B that the same code entry handles? Turn that into an explicit functional test, as this family did.
- **Count the provider-stop and harness-error rate when estimating cost.** In this family 6 of 34 trials ended without a model verdict (1 provider stop, 5 harness errors). `trials.tsv` counts the provider stop as a graded fail, and `build/audit/audit_results.py` should flag a final result of "The request was rejected because it was considered high risk" (and similar) as invalid.

### 6.2 Sibling injection

- **"Feature-absent" siblings beat DS and not MiMo.** A sibling where the whole mechanism lacks the security feature (SAP has no view support at all) gets dismissed by a reasoning-first model (DS 6/6) but found by a probe-first model (MiMo 2/2 valid runs found it). For a breaker against both models, a feature-absent sibling alone is not enough.
- **Prefer siblings that look like an *omitted check where the feature is otherwise honoured*.** Two examples: one call site out of N that skips `visibleInView`, or one subclass whose override drops the guard. Then the "the library doesn't support this" argument is not available, and the model has to audit call sites. That audit is the depth DS skipped. This is untested; it is the direct counterpart of P1.
- **Keep the instruction at the level of the security property.** The sib wording ("any mechanism by which otherwise-unmapped input can still be routed into a restricted property") is the most a hint can say. Do not list declaration forms, value types or "during construction" phases. Suggested gate: give the instruction alone to a model and ask it to name the code mechanism it implies. If the answer names the sibling's class or its subclass family, rewrite the instruction.
- **Fairness note (for the two-criteria rule).** In sib, DS's argument that an any-setter is "not a property annotated for a more privileged view" is contestable but not absurd. The fairness defence is that `@JsonView` on an `@JsonAnySetter` member is an annotation on a deserialization member, and the instruction says "any property or constructor parameter annotated for a more privileged view". To make the sibling clearly fair without leaking it, prefer visible-material clues, such as an existing repo test or doc that shows views on the sibling's member type, over more instruction prose. I did not check whether upstream Jackson treats views on any-setters as a bug or as an unsupported feature.

### 6.3 Stacking

- **sib7 did not test stacking.** It changed the instruction and the siblings at the same time, and the instruction change explains the whole jump (P3). To measure stacking, rerun the sib7 sibling set with the sib instruction (and optionally sib with the sib7 instruction). This is an A/B against the same instruction file.
- **Stacked siblings must not share a choke point.** Add a check patch per stack: one guard in the lowest shared callee (here `SettableAnyProperty.deserialize`/`deserializeAndSet`). If that patch scores `pass`, the stack is one concept, and the extra siblings add test count, not difficulty. The sib7 oracle's "3 distinct guard sites" passed the gate only because the gate checked the oracle's own layer.
- **Stack different concepts, not routes of one concept.** P4 shows that routes of one mechanism fall together once the concept is accepted. A stack that can beat a model needs siblings with *different* reasons to be dismissed or missed, for example one feature-absent sibling (beats reasoning-first models) plus one omitted-call-site sibling (needs a call-site audit), on different classes.
- **Expect the collateral trap to keep scoring.** Keep a coupled-binding functional test like `visibleTypeIdCreatorPropStillBound` in every stacked variant. It caught about 30% of runs regardless of sibling design, and models increasingly over-guard when told to "enforce the view boundary uniformly across all of these".

## 7. Audit notes (no files changed)

- `jackson-databind-sib__gUSEhL9` (MiMo) should be marked invalid (provider safety stop), not a 0/8 fail. MiMo's per-model verdict on sib becomes 1 solved out of 2 valid runs.
- `jackson-sib7__c2yWvQQ` ran 73 min under a 3600 s limit with `timed_out=False`. The limit may not have been enforced for that run; check before trusting its time data.
- The 5 ungraded sib7 runs (CancelledError / NonZeroAgentExitCode) were all already working on SAP when they died. They do not change the conclusion.
