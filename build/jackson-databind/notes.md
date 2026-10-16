# jackson-databind — build notes

## The flaw (verified against the code, not trusted from the row)
CWE-863. `@JsonView` filtering is applied to ordinary bean properties but not to
a polymorphic property whose type discriminator is carried in a *sibling* JSON
field (Jackson's `EXTERNAL_PROPERTY` include mode). Such a property's value is
buffered during parsing and assigned in a later "complete" step that never
consulted the active view, so a property/parameter restricted to a privileged
view is populated from attacker JSON when a lower-privilege view is active.

The candidate row's `flaw_one_line`, `entry_point_GUESS`, and
`tempting_wrong_fix_JUDGEMENT` all checked out against the diff and the code.
The fix (commit c628b35) adds the view check at **four** sites in
`ExternalTypeHandler`: the default-ctor `complete(bean)` loop, the
creator-based `complete(buffer, creator)` loop (value assignment *and* the
separate type-id-creator assignment, databind#999), the non-creator assignment
loop, and the eager `_deserializeAndSet` path. This is genuinely multi-site:
the three construction styles (creator / default-ctor+setter / builder) reach
the root cause through different methods.

## Entry point
`ObjectMapper.readerWithView(View).forType(T).readValue(json)` — the real
downstream library API. No internal helper is invoked by the tests.

## Variants (each really fails on vulnerable code)
1. creator path, whole property hidden
2. default-constructor path, whole property hidden (different handler method)
3. builder path, whole property hidden
4. type id is a visible creator param, value hidden (value must stay null)
5. reverse: the sibling type-id creator param is hidden (must stay null)

Cases 4 and 5 pin the two halves of the databind#999 type-id-creator logic so a
fix cannot get the common case right while leaking (or dropping) the
discriminator.

## Tests
- 5 security (all FAIL on vulnerable, all PASS on fix).
- 9 functional (all PASS on vulnerable and fix): privileged view sees the
  property on all three construction styles; no-view binds everything; visible
  value still binds when a sibling is hidden; visible discriminator still binds;
  subtype still resolves; public document round-trips. Includes a field-gated
  subtype case (a regression guard for the ordinary-field view path).

## Build / offline strategy
jackson-databind here is `2.18.9-SNAPSHOT` with a SNAPSHOT parent pom, so a
from-source Maven build is not reliably offline. Instead the verifier compiles
`/app/src/main/java` with `javac` against the released `jackson-core` /
`jackson-annotations` 2.18.4 jars (binary-compatible) plus a generated
`PackageVersion.java`, then compiles and runs the hidden tests with
`junit-platform-console-standalone`. All jars are vendored into the image at
build time; the trial needs no network. Verified the main sources compile
cleanly this way.

## Wrong-fix patches
- `shallow_creator_only.patch` (security_fail): upstream fix applied to ONLY the
  property-based-creator `complete()` method. Creator security tests pass;
  default-ctor and builder security tests still fail; functional all pass.
- `overrestrict_disable.patch` (functional_fail): skips every sibling-discriminator
  property whenever any view is active. Kills the exploit but drops the property
  even under the privileged view — breaks 5 functional tests.
- `alt_correct_fix.patch` (pass): the correct fix refactored to route all four
  sites through a private `_hiddenInView(view, prop)` helper — different text,
  identical behaviour; scores 1.0.

## Could not verify / caveats
- Did not run jackson-databind's full Maven test suite (SNAPSHOT parent /
  offline constraint). Ran its own `views` test package standalone instead.
- Pinned jackson-core/annotations to released 2.18.4; the SNAPSHOT main sources
  compiled against them with no missing-symbol errors, but this substitutes a
  released sibling for the exact snapshot the upstream build would use.

## 2026-10-16 test repair

Flagged items (lenient_items_2026-10-16.txt, TEST-REPAIRS.md; all three audit verdicts accept
their rewards, the 1.0 ones as genuine solves):
- 8hjvYno and kaRv44B RECs, "optional hardening: a security case with 'asset' before 'kind'
  on the default-constructor / builder bean": **fixed**. The old JSON always put the
  discriminator first. Fair: JSON member order is free, and the instruction requires that a
  hidden property "must never be populated ... for every way the bean is built" and that the fix
  must not be "a block on one particular shape of input".
- m45hNgn REC (0.0 is a genuine over-restriction failure, no test change): **skip**, nothing to do.
- "Include final-code/changes.patch in the postmortem bundle": not a test item, so outside this repair.

What the new order exercises: with the value first, `handlePropertyValue` buffers the value, and
it is bound eagerly when the discriminator arrives (the type-id branch of that method). That is a
different call site from the old order, where binding happens in the value branch. Correction to
the audit wording: this order does NOT reach the deserialization in `complete(bean)`. That only
binds a value itself when the discriminator is absent (defaultImpl, or a natural scalar value).
No test covers that path yet. It is a possible follow-up and is not part of this repair.

Changes (tests only; instruction.md unchanged):
- security/ViewBypassTest: `defaultCtorPropertyHiddenValueFirst`, `builderPropertyHiddenValueFirst`
  (PublicView, `{'label','asset','kind'}`: label binds, asset stays null).
- functional/ViewFeatureTest: `adminSeesGatedPropertyValueFirst` (AdminView, same order: both
  beans bind AdminAsset with its secret). This is an order-symmetric guard against over-restriction.
- New patch check `checks/eager_value_branch_only.patch` (security_fail): the reference fix, but
  the view check is moved from the shared bind helper into the value branch of
  `handlePropertyValue` only. All old tests pass with it. It fails exactly the two new security
  tests (reward 0.7143).

Gate (`slot.py 3 -- gate.py jackson-databind`): **PASSED**. nop: 7/7 security fail, 10/10
functional pass. Oracle 1.0 twice. shallow_creator_only fails 4 security tests (now including
both value-first ones). overrestrict_disable fails 5 functional tests. alt_correct_fix 1.0.
eager_value_branch_only fails the 2 new security tests.

Regrade: none of the 6 trials (jobs jackson-databind-{deepseek,mimo}-1014-051410) has
`final-code/changes.patch`, because they were run before harvesting, so `regrade_from_code.py`
cannot run on them. Nothing was written to the trial folders. As an INFORMAL check, I rebuilt each
run's final code by replaying its Edit/Write calls on /app/src/main (plus the one comment-only
`sed -i` in 3ZYC3oG) from the session transcript, starting from the vulnerable sources. I then
graded each rebuild with regrade_from_code.py in a scratch copy. The scratch copy sits outside
the trial folders. The results are not official regrades.

| trial | model | old | new (reconstructed) | failing tests |
|---|---|---|---|---|
| 8hjvYno | deepseek | 1.0 | 1.0 (7/7, 10/10) | none |
| nUFwdcp | deepseek | 1.0 | 1.0 (7/7, 10/10) | none |
| m45hNgn | deepseek | 0.0 | 0.0 (7/7, 9/10) | 1 functional (originally 8/9; per-test XML not saved, because the scratch mount does not reach the Colima VM) |
| 2F8wzqE | mimo | 1.0 | 1.0 (7/7, 10/10) | none |
| 3ZYC3oG | mimo | 1.0 | 1.0 (7/7, 10/10) | none |
| kaRv44B | mimo | 1.0 | 1.0 (7/7, 10/10) | none |

All rebuilt runs reproduce their original rewards and pass counts, which supports the rebuild.
None drops on the new value-first tests, so every model fix already handled both member orders.
