# class-transformer-exclude-sib: build notes (round 2, trap stack)

Start 2026-10-16 13:04 UTC (scout); build from 13:42 UTC; end: see bottom.

## What this is
A class-A "feature-absent sibling" task on a third library (after jackson-databind-sib and
marshmallow-readonly-sib): class-transformer (TypeScript), pinned at develop HEAD
`a2734a5d154c9b0beb9a10555a04416bc371de06` (2025-01-17, version 0.5.1, the latest npm release).
Nothing is planted: the Dockerfile checks out unmodified upstream code. There is no advisory and no
merged fix, so `source = "injected"`. The reference fix is ours.

Declarative markers: `@Exclude()` (both directions or `toClassOnly` / `toPlainOnly`), `@Expose({ groups })`,
`@Expose({ since, until })`, `@Expose({ name })` (JSON name), and the whole-class `@Exclude()` with
`@Expose()` whitelisting (README "Skipping all properties of the class").

## Scout (13:04-13:40 UTC)
- pydantic 2.13 (dataclass `init=False` via TypeAdapter, nested) and cattrs 25.3 (`init=False`):
  protected; BaseConverter crashes instead of bypassing. Rejected.
- DRF: not probed beyond reading (central `_writable_fields`; known gaps are documented). Rejected for time.
- class-transformer: runtime-class-vs-declared-@Type (subclass exclusions ignored when nested under a
  declared base type, input via plainToClassFromExist and output) is REAL but documented as intended by
  the project's own test (basic-functionality.spec.ts "make sure given type is used instead of
  automatically guessed one"). Rejected; the instruction preserves that behaviour explicitly.
- class-transformer T0 and T1 below: proven with probes on npm 0.5.1 and at the pinned commit.

## Gaps and traps (manifest.traps)
- **T0, the instruction's example.** `TransformOperationExecutor.getKeys` (lines 478-513) filters keys by
  exclusion / version / group using the plain key; for a property with `@Expose({ name })` the plain key
  is the JSON name, so every restriction on a renamed property is skipped on input
  (plainToInstance, plainToClassFromExist, nested, arrays, maps, sets, excludeExtraneousValues).
  Open upstream reports: #1030 (groups, 2021), #1832 / PR #1840 (versions). Output is unaffected.
- **T1, base sibling (class A, feature-absent).** `MetadataStorage.getStrategy` (98-105) reads only the
  class's own class-level decorator; every property-level lookup walks ancestors. A base class
  `@Exclude()` with `@Expose()` whitelist is ignored for every subclass, on input and output.
  Open upstream reports #95 (2018) and #1097. Likely dismissal: "TS class decorators are not inherited".
- **T2, MiMo trap (wrong record / helper with divergent order).** `findExposeMetadataByCustomName`
  (88-92) returns ancestors' records first; `findExposeMetadata` returns the subclass's own record
  first. A T0 fix that checks the record found by JSON name (name_lookup_record.patch, the natural fix)
  misses a subclass that re-declares an inherited renamed property with groups. Coupled functional
  tests: the base class keeps its unrestricted declaration; staff can still set the subclass property.
- The instruction states each: "whichever JSON name the input uses", "restrictions declared on a class
  ... also apply when transforming any of its subclasses", "when a subclass restricts an inherited
  property further, the restriction applies to the subclass; the base class keeps behaving as it
  declares", and the preservation list (declared @Type keeps deciding; discriminators; options).

## Verified
- Vulnerable: 14/14 security fail, 15/15 functional pass. Reference: 14/14 and 15/15 (locally, node 24,
  the repo's own jest 26 / ts-jest 26 via tests/jest.config.js with APP_DIR).
- Project suite (96 tests) passes on vulnerable, reference, alt_correct_fix, hardening.
- All 11 check patches behave as declared locally (see manifest).
- Extra probes of the reference beyond the tests (Map values, Set, depth 3, T2 with `since`, whitelist +
  renamed groups in a grandchild, serialize/deserialize, instanceToInstance): all hold.
- Gate stages: see bottom.

## Not verified / limits
- T0 and T1 are public open issues (with unmerged PRs); a model may remember them. The instruction
  forbids looking up an upstream fix; trials are offline.
- The T1 bullet in the instruction is explicit about subclasses (needed for fairness: without it,
  non-inheritance of class decorators is arguable). So T1 may act as a search problem rather than a
  class-A dismissal; whether DeepSeek still misses it is a hypothesis.
- A subclass that declares a class-level `@Expose()` under an `@Exclude()` base: the reference keeps the
  base's whole-class exclusion (union). Not tested, because the instruction does not settle it beyond
  "restrictions ... also apply"; a nearest-ancestor fix would also pass the tests.
- Restrictions on a subclass object held by a property whose declared `@Type` is the base class are
  NOT applied (upstream's documented "declared type wins"); stated as preserved, not tested.
- Blind patch and FAIRNESS.md not done (by design: others do them).

## Status: PARKED (13:25 UTC)
Coordinator message at ~13:22 UTC: marshmallow-readonly-sib fell to DeepSeek in 10 min because the
whole mechanism sits in two small files; class A needs DISTANCE in a large codebase, and small
libraries (class-transformer named explicitly) are poor hosts. Stopped here: Docker build aborted by me;
gate static passes apart from the expected blind/FAIRNESS items; nop/oracle/patches were run only
locally (results above), never in Docker. Follow-up scout of a large host (DRF 3.16: read_only/write_only
are centralised in Serializer._writable_fields/_readable_fields, OrderingFilter honours write_only;
Django admin save-as-new is an ordinary add) found nothing real in the remaining time box.
Lead found in that follow-up (not built, fails the distance rule): Django main
(django/contrib/admin/options.py) changelist list_editable never consults get_readonly_fields(request, obj),
so a field read-only per user or per object can be bulk-edited from the changelist. Unreported on Trac
(summary search, 2026-10-16). The per-object *permission* half was fixed upstream ~2026-04 (#15759,
commits 84db026 + 5b3cfce), in the same function, so there is no distance between example and sibling.
Scout end 13:29 UTC.
