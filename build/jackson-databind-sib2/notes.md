# jackson-databind-sib2: build notes (round-2 trap stack)

Start: 2026-10-16T11:25Z. End: 2026-10-16T12:11Z.

## Base
A copy of `tasks/jackson-databind-sib`: the same Dockerfile, the same vulnerable checkout (`d627a8a`)
and the same offline javac + JUnit setup. Nothing is planted in `/app`. The task still contains:
- the mined flaw: the external-type-id path (`ExternalTypeHandler`);
- the base sibling: the `@JsonAnySetter` catch-all (`SettableAnyProperty` has no view code);
- the coupled test: the visible type-id creator parameter must still bind.

`"strict_gate": false` is removed, so the strict gate applies.

## Why these traps and not the ones the brief listed
I read both MiMo transcripts from round 1 that engaged with the catch-all:
- pvqkL7s (solved, 1.0);
- yWRg48p (0.0; it failed only on the coupled type-id test).

Both handled the routes inside the catch-all concept:
- both fell back to `beanDesc.findDefaultViews()` (class-level default views and DEFAULT_VIEW_INCLUSION),
  copying the precedent in `BeanDeserializerFactory`;
- both looked at the buffered `bufferAnyProperty` path.

So the "defaults route" and "creator vs setter" routes for the catch-all would not beat MiMo. I
discarded them. I looked for gaps outside that concept instead. I probed every candidate on the
vulnerable code:
- mix-ins, unwrapped, merge on object-shaped beans, creator properties, builders and records all
  honour views already;
- the two gaps below were the only real leaks found.

Transcript evidence that MiMo misses them:
- pvqkL7s wrote "What about `BeanAsArrayDeserializer`? Those have view checks. ✅". Its grep showed
  only the methods that do check views.
- pvqkL7s wrote "`ObjectIdValueProperty` handles the id itself. Let me check if there's a view check
  issue there", then moved on without a fix.
- yWRg48p did fix the identity property, but missed the array-shape update path.

## Traps (all real pre-existing gaps, verified by probe and by tests)

**T1, coupled visible binding on a feature-absent stand-in.**
- With `@JsonIdentityInfo(generator = PropertyGenerator, property = "id")`, `BeanDeserializerBuilder`
  (lines 425 and 497) replaces the real `id` property with an `ObjectIdValueProperty` that carries no
  views. `deserializeWithView` therefore sees it as visible in every view.
- `ObjectIdValueProperty.deserializeSetAndReturn` (lines 87-108) then writes the admin-only `id`.
- Constructor-built beans go through a second site that does the same thing:
  `PropertyValueBuffer.readIdProperty` / `handleIdValue` (lines 318-347).
- The coupling: the same input id is also the identity that visible links (`"next": 7`) resolve
  against. A correct fix keeps registering the identity and skips only the property write.
- The "natural" fix gives the stand-in the id's views, or skips the id entirely. It is secure but
  breaks visible links: `identity_skip_whole.patch` → functional_fail.
- Tests:
  - security: `LinkedRecordBypassTest.{recordIdHidden, constructedRecordIdHidden}`;
  - coupled functional: `LinkedRecordFeatureTest.{linksResolveUnderPublicView, constructedLinksResolveUnderPublicView}`;
  - also `adminSetsIds` and `noViewSetsIdsConstructed`.
- Realistic: server-assigned ids, writable only by internal tooling, with clients linking records
  inside one request.

**T2, merge / defaults / patch route, where the sibling path already checks views.**
- `BeanAsArrayDeserializer.deserialize(p, ctxt, bean)` (lines 151-198) is the in-place update method
  for `@JsonFormat(shape = ARRAY)` beans. It has no view check.
- The fresh-read methods next to it (`_deserializeNonVanilla` at 222, `_deserializeUsingPropertyBased`
  at 284) do check views, so a probe with a fresh read passes.
- Two routes reach it:
  - `readerForUpdating(existing).withView(PublicView)` (the PATCH idiom);
  - `@JsonMerge` on a property whose default value is an array-shaped bean (a server-defaults
    overlay, on a fresh read).
- Tests:
  - security: `CompactEntryBypassTest.{updateKeepsRestrictedValues, defaultsKeepRestrictedValues}`;
  - coupled functional: `CompactEntryFeatureTest.{publicUpdateBindsVisibleValues, publicDefaultsBindVisibleValues}`.
    These check that a visible element after a hidden structured element binds in its own position,
    so the hidden value must be skipped in full.
  - also admin, no-view and fresh-read controls.

Shape classes: T1 is rank 1 (coupled binding), with the rank-4 feature-absent element. T2 is rank 2
(merged/defaults route), with rank 4b (N-1 paths checked). They have different dismissal reasons:
- T1: "the id must be kept for references";
- T2: "array beans already have view checks".

## Reference fix (`solution/fix.patch`)
- The jackson-databind-sib reference: the upstream ExternalTypeHandler fix plus the catch-all.
- `ObjectIdValueProperty`: identity is still bound; the id property is written only when visible.
- `PropertyValueBuffer.handleIdValue`: the same rule.
- `PropertyValueBuffer.bufferAnyProperty` / `bufferAnyParameterProperty`: drop hidden catch-all
  values. This also closes the catch-all on constructor-built beans, which the sib reference left
  open (I verified the leak with a probe). It is not tested: it is the same concept as the base
  sibling, and MiMo already handles it.
- `BeanAsArrayDeserializer.deserialize(p, ctxt, bean)`: the same view check as `_deserializeNonVanilla`.

## Tests
- 12 security tests: the 8 inherited plus 4 new. All fail on the vulnerable code and all pass on the
  reference.
- 25 functional tests: the 15 inherited plus 10 new. All pass on both.
- New security tests accept a clean refusal (a Jackson exception) as safe. The "ignored without
  error" contract is enforced by the functional tests instead, so `crash_refusal.patch` fails only
  as functional.

## Check patches (local runs before the gate)
| patch | security | functional | expected |
|---|---|---|---|
| prev_reference_only | 8/12 | 25/25 | security_fail |
| miss_identity | 10/12 | 25/25 | security_fail |
| miss_ctor_identity | 11/12 | 25/25 | security_fail |
| miss_update | 10/12 | 25/25 | security_fail |
| wrong_resource | 10/12 | 25/25 | security_fail |
| identity_skip_whole | 12/12 | 23/25 | functional_fail |
| crash_refusal | 12/12 (gate) | 23/25 | functional_fail |
| alt_correct_fix | 12/12 | 25/25 | pass |
| hardening | 12/12 | 25/25 | pass |

`upstream_fix_only` and `disable_feature` were carried over and are checked by the gate.

## Instruction
Rewritten in the 3i style:
- the system;
- one trigger: the original external-type-id example;
- the invariant, with "every kind of deserialization … new object or applied to an existing one";
- the contracts: ignored without error; the value is kept, or the default on a new object; visible
  properties bind exactly as today, "including when they sit next to a hidden value or depend on
  one"; privileged and no-view reads are unchanged;
- the constraints block.

It names no mechanism: no catch-all, identity, array shape, merge, creator or builder.
`readerForUpdating(existing).withView(...)` is named because it is the user-facing entry point
that the update tests drive.

## Not verified / open
- The blind patch and FAIRNESS.md are owed by independent agents.
- I did not check whether upstream jackson later fixed T1 or T2. Offline agents cannot look it up
  either way.
- Fairness risk, medium:
  - T1's coupled test requires that the hidden id still links records. The instruction covers this
    only through "visible properties … depend on one … bind exactly as today".
  - A reviewer could argue that ignoring the id entirely (and so failing the link) is acceptable.
- Fairness risk, low/medium: T2's `@JsonMerge` defaults form relies on "however the object is
  built or populated".
- Jackson's full Maven suite was not run (offline SNAPSHOT parent), as in the base task.

## Gate (2026-10-16)
- static: only the expected problems (the blind patch and FAIRNESS.md are missing).
- nop: PASSED.
- oracle: PASSED.
- patches: PASSED. All 11 checks matched their expectation (gate_report.partial.json).
- 2026-10-16 12:26Z (lead): trials started in parallel with the full strict gate to save wall time; trial results count only if this gate run prints PASSED.
