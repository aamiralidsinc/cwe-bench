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
