# jackson-databind-sib2: pre-trial fairness and leniency review

Reviewer: an independent sub-agent (Opus 5.5) that did not write the tests. Date: 2026-10-16.
Read: instruction.md, every file in tests/, solution/fix.patch, manifest.json, notes.md,
checks/*.patch (diffed against the reference) and gate_report.partial.json. Nothing was run.

Instruction clauses cited below:
- **INV**: "While a view is active, no input may set a property that is restricted to views the
  active view does not include ... whatever the type looks like, however the object is built or
  populated, and whether the input creates a new object or is applied to an existing one."
- **IGN**: "Input aimed at such a property is ignored without an error ... The property keeps the
  value it had before the read (on a new object, its default)."
- **NEXT**: "Properties that are visible in the active view keep binding exactly as they do today,
  including when they sit next to a hidden value or depend on one."
- **PRIV**: "With a view that includes the property, or with no view active, everything binds
  exactly as it does today. A property with no view restriction keeps binding under any view."

## 1. Per-test table

### Security (12)

| test | asserts | fair because | correct fix could fail? | risk |
|---|---|---|---|---|
| ViewBypassTest::creatorPropertyHidden | admin-only ext-typed `asset` null under PublicView (creator) | the instruction's own example + INV | no | low |
| ViewBypassTest::defaultCtorPropertyHidden | same, default-ctor bean | INV ("however the object is built") | no | low |
| ViewBypassTest::builderPropertyHidden | same, builder bean | INV | no | low |
| ViewBypassTest::creatorValueHiddenTypeIdVisible | `asset` null when the type id is a visible creator param | INV | no | low |
| ViewBypassTest::typeIdCreatorParamHidden | admin-only type-id creator param `kind` null | INV (`kind` is itself a restricted property) | no | low |
| AnySetterBypassTest::mapExtrasHidden | admin-only catch-all Map stays empty | INV ("whatever the type looks like") | no | low |
| AnySetterBypassTest::methodExtrasHidden | same, setter method | INV | no | low |
| AnySetterBypassTest::nodeExtrasHidden | same, JsonNode field stays null | INV + IGN (default) | no | low |
| LinkedRecordBypassTest::recordIdHidden | admin-only `id` != input (7, 8); refusal accepted | INV | no | low |
| LinkedRecordBypassTest::constructedRecordIdHidden | same, constructor-built record | INV | no | low |
| CompactEntryBypassTest::updateKeepsRestrictedValues | update keeps `owner`/`roles`; refusal accepted | INV ("applied to an existing one"), IGN | no | low |
| CompactEntryBypassTest::defaultsKeepRestrictedValues | merged defaults keep `system`/`viewer` on a fresh read; refusal accepted | INV ("however ... populated"), IGN | no (see T2 below) | low |

### Functional (25)

| test | asserts | fair because | correct fix could fail? | risk |
|---|---|---|---|---|
| ViewFeatureTest (9 tests) | admin/no-view bind the ext-typed property; public `label` binds; subtype still resolves when only a field or only the type id is gated; visible type-id param binds | PRIV, NEXT ("depend on one" covers the gated-type-id case) | no | low |
| AnySetterFeatureTest (6 tests) | admin/no-view fill the catch-all (3 forms); unrestricted catch-all binds under PublicView; `label` binds | PRIV, NEXT | no | low |
| LinkedRecordFeatureTest::linksResolveUnderPublicView | under PublicView, `next.next` (`"next": 7`) is the root record | NEXT (`next` is visible and depends on the hidden id) and IGN ("without an error"); see T1 | maybe, only for an engineer who reads "ignored" as overriding NEXT | medium-low |
| LinkedRecordFeatureTest::constructedLinksResolveUnderPublicView | same, constructor-built record | same | same | medium-low |
| LinkedRecordFeatureTest::adminSetsIds / noViewSetsIdsConstructed | ids and links under admin / no view | PRIV | no | low |
| CompactEntryFeatureTest::publicUpdateBindsVisibleValues | `label`, and `note` after the hidden nested `roles`, bind on update | NEXT ("next to a hidden value"), IGN | no | low |
| CompactEntryFeatureTest::publicDefaultsBindVisibleValues | same through the merged defaults | NEXT, IGN | no | low |
| CompactEntryFeatureTest::adminUpdate / noViewUpdate / adminDefaults / publicNewEntry | privileged, view-less and fresh reads unchanged | PRIV, NEXT | no | low |

### The two concerns the builder flagged

**T1 (builder: medium). Verdict: fair as worded; risk medium-low.**
`identity_skip_whole.patch` drops the id input altogether. The read of
`{'id':7,...,'next':{...,'next':7}}` then ends in an unresolved forward-reference error. Before the
fix, the same request succeeds under PublicView with the link resolved. So the over-fix breaks
two clauses, not one:
- **IGN**: hidden input must be ignored *without an error*;
- **NEXT**: `next` is a visible property whose value depends on the hidden value, and it must bind
  *exactly as today*.

If a fix suppressed that error and left `next` null, it would still break NEXT. The only reading
that lets the over-fix through treats "ignored" as "the input value takes no part in the read at
all". NEXT is the more specific clause and closes that reading. NEXT also does not single out T1:
`ViewFeatureTest::visibleValueStillBoundWhenTypeIdGated` already relies on it for the inherited
task, so it is not a T1 hint. Security is not traded away: the identity lives only inside one
request and gives no privilege. No wording change is required.

Optional tightening, only if the client objects. It is neutral, but it does lower the trap's
difficulty a little. Append to IGN:
> "Only the restricted property itself is left unset; the rest of the read handles that input as
> it does today."

**T2 @JsonMerge form (builder: low-medium). Verdict: fair as worded; risk low.**
The defaults test is a direct case of INV: a view is active and input sets an admin-only `owner`.
INV is absolute, and it explicitly covers objects that are "populated" and input "applied to an
existing one". A merged default is exactly an existing instance that the input is applied to. The
expected values (`system`, `viewer`) follow from IGN ("keeps the value it had before the read").
The reference closes both routes with one check in the in-place update method. So any fix at the
deserializer layer passes both, and only a fix at the `ObjectReader` level misses the merge route,
which is a real leak. This is a discoverability burden, not an unfairness. No change is needed.

## 2. Leniency

| property / trap | most plausible wrong fix | caught? |
|---|---|---|
| ext-type-id (mined) | the upstream fix only | yes: 7 security tests fail (`upstream_fix_only.patch`) |
| catch-all (base sibling) | none, or drop all catch-alls under a view | yes: AnySetterBypassTest (`prev_reference_only` predecessor); AnySetterFeatureTest (`disable_feature.patch`) |
| T1 | fix the id in the field path only | yes: constructedRecordIdHidden (`miss_ctor_identity.patch`) |
| T1 | check the stand-in property's own (empty) views | yes: both id tests (`wrong_resource.patch`) |
| T1 | drop the id as identity too | yes: LinkedRecordFeatureTest x2 (`identity_skip_whole.patch`) |
| T2 | miss the in-place path | yes: CompactEntryBypassTest x2 (`miss_update.patch`) |
| T2 | throw instead of ignoring | yes: CompactEntryFeatureTest x2 (`crash_refusal.patch`) |
| T2 | skip one token, not the whole nested value | yes: `note`-after-`roles` assertions (no check patch) |

Wrong fixes that no test catches:
- (a) The catch-all on **constructor-built** beans (`bufferAnyProperty` / `bufferAnyParameterProperty`):
  the reference closes it, but no test covers it, so a fix that leaves it open passes. This is a
  real leak under INV.
- (b) Class-level default views or `DEFAULT_VIEW_INCLUSION` for the catch-all; this is hardening only.
- (c) A fix at the `ObjectReader` level for T2 is caught only through the merge test. That is
  acceptable.

(a) is lenient but not unfair. Optional: add one creator-bean catch-all security test (plus a
feature control).

## 3. Hints

- "`mapper.readerForUpdating(existing).withView(PublicView.class)`" and "to apply partial updates to
  records that already exist" point at the update route of T2. These lines name a public entry
  point, not a file or mechanism, and that API is the standard Jackson idiom. Acceptable.
  Optional neutral form: drop the code sample and keep "or applied to records that already exist".
- "however the object is built or populated" and "whatever the type looks like" are generic and
  cover several unnamed routes. They are fine.
- "sit next to a hidden value or depend on one" is generic and shared with the inherited coupled
  type-id test. It is fine.
- The instruction names no file, function, trap, variant list or flaw count. It contains no
  manifest leak term; the "default" in line 41 is the plain English word.

## 4. Realism

- All code at the vulnerable commit `d627a8a` is unmodified upstream code; nothing is planted.
- T1 rests on Jackson's own stand-in property design. Restricting server-assigned ids to an
  internal view while clients link records in one request is a common pattern.
- T2's in-place method sits next to two fresh-read methods that do check views. That is a
  plausible omission.
- The model combination in the `@JsonMerge` test (merge onto a default value of an array-shaped
  bean) is uncommon but uses only documented features, and the test reaches it through the public
  reader API.
- Nothing looks contrived.

## 5. Verdict

**READY.** No wording change is required for T1 or T2. Optional items: the T1 sentence in section
1, the `readerForUpdating` de-hint in section 3, and a constructor-built catch-all test (leniency
gap (a)).
