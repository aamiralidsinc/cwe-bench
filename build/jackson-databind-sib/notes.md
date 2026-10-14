# jackson-databind-sib — build notes (injection A/B, Branch B)

## What this is
Branch B of the calibration A/B. A (control) = `tasks/jackson-databind`,
mined-only, SOLVED by both trial models. B = the SAME repo at the SAME
vulnerable commit (`d627a8a`), with a same-class `@JsonView` sibling bypass on a
reachable path the upstream fix never touched. The oracle must close BOTH; the
upstream fix alone must now FAIL.

## The sibling flaw (verified against the code, not assumed)
CWE-863, same class as the mined flaw: a `@JsonView`-restricted property is
populated from untrusted JSON under a lower-privilege view. The mined flaw lives
on the external-type-id polymorphic path (`ExternalTypeHandler`). The sibling
lives on the **`@JsonAnySetter` catch-all path** (`SettableAnyProperty`):

- A bean has a public `label` plus an admin-only catch-all
  (`@JsonView(AdminView.class) @JsonAnySetter Map<String,Object> extras`) that
  collects any otherwise-unmapped JSON keys.
- On the vulnerable commit, `SettableAnyProperty` has **no view handling at all**
  (grep for `View` in that file returns nothing). `BeanDeserializer` routes every
  unmapped property to `_anySetter.deserializeAndSet(...)` unconditionally, so
  under `PublicView` an attacker's extra keys are still collected into the
  admin-only `extras` — a genuine `@JsonView` authorization bypass.

This is a genuine pre-existing gap, not planted code: **nothing was injected into
`/app`.** The Dockerfile, the vulnerable checkout, and `compile-lib.sh` are
identical to the control task. The "injection" is that the task now exercises and
requires closing this second, independent place the same mistake lives. It reads
fully natural because it *is* jackson's own untouched code path.

Empirically confirmed (offline, in the task image), under `readerWithView`:
- vulnerable: Map-field, two-arg-method, and JsonNode any-setters ALL leak under
  `PublicView`;
- oracle: all three are withheld under `PublicView`, bind under `AdminView` and
  under no view, and a catch-all with NO `@JsonView` keeps binding under
  `PublicView` (not over-restricted).

## Why the upstream fix alone fails (the decisive property)
The upstream fix (`checks/upstream_fix_only.patch`, byte-identical to
`tasks/jackson-databind/solution/fix.patch`) only edits
`deser/impl/ExternalTypeHandler.java`. The sibling lives in
`deser/SettableAnyProperty.java`, which it never touches. So applied alone it
closes the 5 original security tests but leaves the 3 any-setter security tests
failing, while all 15 functional tests still pass → `security_fail`. That is the
calibration point: fixing only the mined flaw is no longer enough.

## Oracle
`solution/fix.patch` = the exact upstream `ExternalTypeHandler` hunks (identical
to the control) PLUS a `SettableAnyProperty` change that teaches the any-setter
to honor `@JsonView`: a `visibleInView(ctxt, activeView)` accessor (reads the
member's declared views via the introspector; no `@JsonView` ⇒ visible in all
views) and a guard at the top of `deserializeAndSet` (base + the JsonNode
override) that discards the value when the active view hides the any-setter.

## Tests
- 8 security (all FAIL on vulnerable, all PASS on oracle): 5 original external-
  type-id variants + 3 any-setter variants (Map field, setter method, JsonNode).
- 15 functional (all PASS on vulnerable and oracle): the 9 original + 6 for the
  any-setter feature (admin view populates Map/method/JsonNode catch-alls; no
  view populates; a non-`@JsonView` catch-all still binds under `PublicView`;
  the public `label` still binds when the catch-all is hidden).

## Wrong-fix / check patches
- `upstream_fix_only.patch` (security_fail): THE key check — exact upstream fix,
  closes the original path, leaves the sibling open. 3 security tests still fail,
  all functional pass.
- `disable_feature.patch` (functional_fail): upstream `ExternalTypeHandler` fix +
  an over-restrictive any-setter change that drops EVERY extra property whenever
  any view is active. Kills both exploits but breaks functional (admin view no
  longer populates the catch-all; a non-`@JsonView` catch-all is dropped under
  `PublicView`).
- `alt_correct_fix.patch` (pass): a different correct fix of BOTH — the
  `ExternalTypeHandler` `_hiddenInView` helper refactor (control task's alt) plus
  a different any-setter implementation (lazily-resolved, cached `ViewMatcher`
  with an inverted `_hiddenInActiveView` guard). Behaviour identical to the
  oracle; scores 1.0. Proves the tests do not hard-code the oracle's shape.

## Could not verify / caveats
- The sibling fix returns "visible" for a catch-all with no `@JsonView` declared,
  matching jackson's default `MapperFeature.DEFAULT_VIEW_INCLUSION = true`. A
  configuration with that feature disabled is not modelled (the control task does
  not model it either); all tests use the default mapper.
- As in the control task, the library is compiled with `javac` against released
  `jackson-core`/`jackson-annotations` 2.18.4 rather than the exact SNAPSHOT
  siblings; the main sources compile cleanly against them.
- I did not re-run jackson's full Maven suite (SNAPSHOT parent / offline).
