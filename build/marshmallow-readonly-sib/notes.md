# marshmallow-readonly-sib: build notes (round 2, trap stack)

Start 2026-10-16 12:31 UTC; end 12:53 UTC (date -u on this machine).

## What this is
A class-A "feature-absent sibling" task, like jackson-databind-sib, on a different library:
marshmallow (Python), pinned at dev HEAD `d08471b17880c62b789971ada638707a11d3f8d4`
(2026-10-06, version 4.3.1). Nothing is planted: the Dockerfile checks out unmodified upstream
code. There is no upstream advisory or fix, so `source = "injected"`, meaning the gaps are real,
pre-existing and found by us. The reference fix is ours.

Declarative marker: `dump_only` (read-only) and `load_only` (write-only), set on a field, in
`class Meta`, as constructor arguments, or from an enclosing schema with dotted names
(`"profile.role"`). The dotted form is a changelog feature since 2.x (#572).

## Gaps (all reproduced through Schema.load / Schema.dump in the task image, and on PyPI 3.26.1 locally)
- **T0, the instruction's example.** `schema.py:431-432`:
  `self.load_only = set(load_only) or set(self.opts.load_only)` (and the same for `dump_only`).
  Any constructor declaration, including the one an enclosing schema passes to a nested schema
  class, discards that schema's own `Meta` lists. Two lines above, `exclude` uses `|`.
  Example: `AccountSchema.Meta.dump_only = ("profile.created",)` makes `ProfileSchema`'s
  Meta-read-only `role` loadable.
- **T1, the base sibling (class A).** `fields.py:580-595`: `Nested.schema`'s schema-object branch
  (`Nested(S())`, `Nested(lambda: S())`, and the same objects inside List or Dict values) applies the
  enclosing schema's dotted `only`, `exclude` and `many`, but never its dotted `load_only` or
  `dump_only`. The class branch at 597-612 does. Upstream fixed dotted only/exclude for schema
  objects (#1384) but not these. The Nested docstring ("the instance's exclude, only, and many
  attributes will be respected") is the likely dismissal reason.
- **T3, the coupled trap.** `fields.py:581` makes `copy.copy(nested)`, a shallow copy:
  `declared_fields` and the field objects are shared with the original object. `_init_fields()`
  re-runs at every nesting, and `_bind_field` sets `field.dump_only = True`. So the natural T1 fix
  (copy the only/exclude precedent, then re-init) marks the field read-only for every other schema
  that nests the same object. The reference gives the copy its own field objects.
- **T0b.** If T0 is fixed where the enclosing schema builds the nested class, direct constructor
  use still drops the Meta lists. This trap is weak: most fixes will land at schema.py:431.

## Verified
- Vulnerable code: 10/10 security tests fail and 9/9 functional pass. Reference: 10/10 and 9/9.
- marshmallow's own suite (1190 tests) passes on vulnerable, reference, alt_correct_fix and
  hardening.
- Gate stages: static (only the expected blind/FAIRNESS problems), nop, oracle and patches all
  PASSED. All 11 check patches behave as declared (see manifest).
- The instruction's example prints `{'username': 'eve', 'profile': {'role': 'admin'}}` on the
  vulnerable code and raises `ValidationError` on the reference.
- Upstream search (GitHub issues, 2026-10-16): no report of dotted load_only/dump_only with schema
  objects, and none of the Meta `or`. #1886 (closed, "documented") is about Nested's own
  only/exclude args. Open PR #3077 only validates string arguments.

## Not verified / limits
- Deeper dotted paths through a schema object (`a.b.c` with `a` a schema object) are not handled
  by the reference (the inner fields keep the original object as root) and not tested.
- Changing `or` to a union changes documented-nowhere semantics: a constructor `dump_only` used
  to replace Meta's list. No project test relies on the replacement. The instruction states
  "declarations add up".
- Whether DeepSeek dismisses T1 the way it dismissed the jackson any-setter is a hypothesis.
  Visible clues that make T1 fair: the class branch passes these options three lines below, and
  the instruction says "whichever way the input reaches it".
- The blind patch and FAIRNESS.md are not done (by design: others do them).

## 2026-10-16 12:58-13:10 UTC: Fix A after the pre-trial fairness review (FAIRNESS.md: NOT READY)
- **Why.** The instruction promises "at any depth". The first reference gave the copy its own
  field objects, but `Field._bind_to_schema` keeps the first parent/root. So the copied fields
  still pointed at the original object, and `Outer.Meta.dump_only = ("unit.lead.tier",)` with
  `unit = Nested(obj)` still loaded `tier`. This was true on the reference and on
  alt_correct_fix.
- **Reference (`solution/fix.patch`).** A new `_unbound_copy` helper in fields.py copies each
  field of the schema-object copy with parent/root reset and the Nested `_schema` cache cleared,
  and recurses into List.inner, Tuple.tuple_fields and Mapping key/value fields. Dotted names now
  reach deeper schemas, whether or not the object was used before.
- **alt_correct_fix.** A generic `_detached` walk over `vars()`, applied only to the fields the
  enclosing names target. Deeper names go on the copy's own sets.
- **Isolating checks rebuilt on the new T1:** options_from_parent, read_only_direction_only and
  merge_in_nested_only.
- **New checks.**
  - `miss_depth.patch` (security_fail) is the first reference.
  - `rebuild_from_class.patch` (functional_fail) does `type(obj)(load_only=..., dump_only=...)`
    and loses the object's own unknown, many and only.
- **New tests.**
  - security `test_enclosing_read_only_two_levels_through_schema_object` (cold).
  - security `..._two_levels_through_used_schema_object`: the object is used first, and the
    test includes a List inside it.
  - functional `test_nested_object_keeps_its_own_options_under_restriction`: unknown=EXCLUDE,
    many=True and only=... on the objects.
  - functional `test_schema_object_unaffected_by_deeper_restriction_elsewhere`.
- **Results.** 12 security tests (all fail on vulnerable) and 11 functional tests (all pass on
  vulnerable). Reference, alt, hardening and blind_opus each score 12/12 and 11/11. The project
  suite (1190 tests) passes on reference, alt and hardening. Gate nop, oracle and patches PASSED;
  static PASSED. instruction.md is unchanged.
- 13:09Z (lead): trials started in parallel with the full strict gate; results count only if that gate run prints PASSED.
