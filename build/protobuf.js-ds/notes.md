# protobuf.js-ds build notes

Started: 2026-10-18T19:08:03Z
Finished: 2026-10-18T20:45:00Z (build; the last full patches attempt was still running at the time of writing)

Task: protobufjs/protobuf.js, advisory GHSA-JFJ6-75FJ-8934 / CVE-2026-59876
(CWE-1321 inherited-property confusion). Pinned commit
`1aca107aa7938d1e49a25f9653186db2f40a0253`, verified upstream as the parent of
the published fix `9f97fe413072d3beb52c74e62d88ea8adc9444d8`
(`git log -1 --format=%P` on a shallow clone). Track: injected. Pattern: A.

## Levers (one line each)

- T1 (A, report): text-format map entry keyed `__proto__` becomes the returned
  map's prototype; must be an own enumerable key with the map keeping the
  ordinary object prototype. `ext/textformat.js` (parseMapField/addMapEntry).
- T2 (A, far in the same parser): field containers read the input object by
  field name, so repeated/map fields named like inherited properties throw or
  silently lose data. `ext/textformat.js` (addField/getField/setField).
- T3 (A, far, lower-level API + producer): enum values table inherits
  Object.prototype, so text/JSON enum lookups accept inherited names and a
  schema cannot declare or add such a value. `src/enum.js`.
- T4 (A, far, defaults/merge route): option reads and merge-ifNotSet treat an
  inherited property as a recorded value. `src/object.js`, `src/util/minimal.js`.
- T5 (A, far, second parser): an aggregate `.proto` option member named like an
  inherited property is concatenated with it. `src/parse.js`.
- T6 (A, far, second implementation): an imported descriptor enum value named
  `__proto__` reparents the value-options table and leaks its options.
  `ext/descriptor.js`.
- T7 (A, far, wrapper): the static generator emits an enum table that still
  inherits Object.prototype. `cli/targets/static.js`.
- R1 (B, real upstream, still in latest): dotted settings read inherited
  segments, and a final unsafe segment reparents the container.
  `src/util.js` setProperty.
- R2 (B, real upstream, still in latest): the generated plain-object converter
  reads absent fields from the input object's prototype. `src/converter.js`.
- S1 (injected): a single-segment fast path in the parsed-option merge reads
  and writes the segment name directly. `src/object.js` setParsedOption.
- S2 (injected): the unsafe-name guard in the dotted-setting helper applies
  only while recursing, so a final unsafe segment is written.
  `src/util.js` setProperty.

Each trap has a `sf-miss-*.patch` that reverts only that lever; all 11 were run
locally against the hidden suites: each leaves at least one security test
failing while every functional test passes. `ff-overbroad.patch` (null-prototype
text-format maps) and `ff-refuse-all.patch` (reject every map field) each fail a
functional test. `pass-hardening.patch` and `pass-alt.patch` score 1.0;
`pass-alt` uses direct `Object.defineProperty` writes instead of the shared
helper.

## Verified

- The flaw reproduces through the public API at the pinned commit: text-format
  maps, field containers, enum tables, option/merge lookups, aggregate options,
  descriptor import, the static generator, dotted settings and plain-object
  conversion were each exercised in Node 20 against the pinned tree.
- The reference fix (published source hunks plus fixes for R1, R2, S1, S2) makes
  all 31 security and 22 functional hidden tests pass in the built image
  (reward 1.0); the untouched image scores 0/31 security and 22/22 functional.
- The project's own 270 area tests pass at pinned+injected and at the oracle;
  the full `npm run test:sources` suite (2585 cases) also passes on both.
- The repo at the pinned commit contains no regression tests from the fix
  commit (the fix commit is the child of the pinned commit).
- Image build: pinned commit fetched from GitHub, `.git` removed, injection
  applied, dependencies installed from the committed lockfile, the CLI's stale
  bundled copy of the library replaced with a link to `/app`, and a pristine
  copy of the five area test files placed under `/opt/pristine-tests`. No
  network at test time (verified with `docker run --network none`).

## Could not / did not verify

- The exact upstream advisory text was not available locally; the scope was
  taken from the fix diff and the screener record.
- Namespace/type lookup by name is a real inherited read at the pinned commit
  but is outside this advisory's protection; it is noted here, not built on.
- The injected siblings are our copy only; `real_upstream` is `no` for them.

## Infrastructure note (gate patches stage)

The original build lost patches-stage trials to a Docker compose network race
(`network ... not found` while starting the container, an infrastructure
error, not a task result). On the 2026-10-20 fairness revision the whole
patches stage ran clean in one attempt: all 16 checks matched their declared
expectation (report in `gate_report.partial.json`). The per-trial evidence for
the older runs is in `patches-incontainer-summary.txt`.

## Pre-trial fairness revision (2026-10-20)

Addressed `FAIRNESS.md`. The previous revision section below was inaccurate: it
described changes that were never written to disk. This section describes the
files as they now stand.

1. `instruction.md` states that a setting/option/metadata name that would
   replace its container's prototype is ignored: not stored, no exception, and
   processing continues; a descriptor-imported value or option name of that
   shape is dropped. The declared-name guarantee is limited to ordinary
   inherited names (`constructor`, `toString`).
2. Refusal-as-exception is scoped to an undeclared lookup name (enum/JSON), so
   the silent continuation required by `security/08` and `security/09` is
   stated, not inferred.
3. Added the own-property rule for `ifNotSet` default merging, plus the
   existing merge refusal of the prototype-replacing key, `prototype` and
   `constructor` (asserted by `functional/03`).
4. Neutralised the variant/entry-point lists, the surface list, the test-spec
   sentence and the ordinary-behaviour surface list; reworded the map and enum
   contracts without naming null-prototype maps or the values table.
5. Added `isPrototypeOf`/`propertyIsEnumerable` probes to the text-format field,
   enum text/JSON lookup, enum-table, option, merge, generated-table and
   converter tests, so a name blacklist no longer passes. These also complete
   the test lists `manifest.traps` already advertised (T2's two extra field
   forms and R2's second converter assertion).
6. The schema unsafe-dotted-setting test (`security/08` test 5) now uses an
   aggregate object value and inspects the parsed-option container, so it
   detects the S2 final-segment flaw independently (it fails on
   `sf-miss-s2.patch`).
7. Added the advertised post-refusal enum test: after a refused inherited-name
   lookup the table is unchanged and a valid message still parses.
8. Added `sf-miss-t4b.patch`, which reverts only the `util.merge` own-property
   fix, so the T4 merge assertion is exercised by a dedicated check
   (`security_fail`, functional all pass).

`security/10`'s new converter assertions use scalar fields: repeated/map
defaults are own empty containers in protobuf.js even for an absent input, so
only a scalar field distinguishes an inherited read.

Local verification (fresh container from the built image, hidden suites mounted
at `/tests`): nop 0/31 security and 22/22 functional; oracle 31/31 and 22/22;
every `sf-miss-*` leaves ≥1 security test failing with functional all passing;
`ff-overbroad` and `ff-refuse-all` fail functional; `pass-alt` and
`pass-hardening` are 0/0.

## Downstream

`blind.patch` and `FAIRNESS.md` are intentionally absent; the static gate
reports only those two. The blind patch should be added to `patch_checks` with
`expect = "pass"`, `kind = "blind"` when written.

## Sibling-injection upgrade (2026-10-20, after the pre-trial fairness revision)

1. `instruction.md` was rewritten to one general property over the protected
   outcome. Every sentence that named or described a route, surface, stage,
   format, file, function or object kind was removed, including the report's
   concrete text-format example, the option/merge/descriptor/generator
   sentences and the null-prototype/map/values-table contract wording. The
   coupled contracts are kept but stated generally: own data vs absent vs
   silently ignored configuration, everything the library emits follows the
   same rule, and filling-only-what-is-absent still counts an entry as present
   only when it is an own property and keeps its existing refusal of unsafe
   names.
2. The three reference-fix hunks that no trap covered were promoted to levers
   and covered behaviourally through the public entry points:
   - T8 `ext/descriptor.js` map-entry table (`mapEntries`): an imported
     repeated message field whose type name ends in an inherited property is
     no longer built as a map entry (the pinned tree throws
     "invalid map entry descriptor").
   - T9 `ext/descriptor.js` group-name table (`groupTypeNames`): an imported
     nested type named like an inherited property is no longer marked as a
     group.
   - T10 `cli/targets/proto.js` extension grouping (`consolidateExtends`): the
     schema-text target no longer crashes when an extension target is named
     like an inherited property.
   Tests live in `security/06_descriptor_import.js` (two) and
   `security/07_cli_generated_tables.js` (one). `functional/06_cli_legit.js`
   gained the coupled ordinary-extension assertion.
3. New checks, each the reference fix with only its own hunk reverted:
   `sf-miss-t8.patch`, `sf-miss-t9.patch`, `sf-miss-t10.patch`; all three are
   `security_fail` in `manifest.patch_checks` (19 checks total).

Verified without a gate run: against `dev/inj4` (pinned + injection) the three
new security tests fail and all functional behaviour passes; against
`dev/oracle4` all pass; with each new check patch applied to a copy of
`dev/inj4`, only that check's own security test fails and every functional
test passes. The reference `solution/fix.patch` needed no change: it already
closed T8-T10. No repository code, image or environment file was changed, so
no image rebuild is needed.
