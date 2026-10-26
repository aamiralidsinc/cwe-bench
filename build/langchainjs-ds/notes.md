# langchainjs-ds — build notes

- Task: `langchainjs-ds` (pattern A+B, track injected), `@langchain/redis` RediSearch query-syntax
  injection (CWE-943). Advisory GHSA-5X6V-P487-7QH2 / CVE-2026-105799.
- Pinned: 71e53f1c07bc60e2c2304b10f0edd3c85c62b192. Published fix: 880e3969ea643a2147777a4d5e8bd606a697edf7.
- Start UTC: 2026-10-24T03:28:06Z. End UTC: 2026-10-24T04:35:01Z

## Verification already done before building

- Pinned source cloned in scratch (`~/.tb-graders/cwe/work/langchainjs-ds/src/repo`).
- Toolchain: Node 24 (host) / node:22 image, flat npm dep tree (`@langchain/core@1.1.39`,
  `redis@4.7.1`, `uuid@10`, `vitest@4.1.2`, `dotenv`, `typescript`, `@faker-js/faker`,
  plus the workspace `@langchain/tsconfig` copied into node_modules). Project unit tests
  `src/tests/filters.test.ts` (65) and `src/tests/vectorstores.test.ts` (28) pass at the pinned
  commit, both under pnpm and under the flat tree at `/workspace/node_modules`.
- Behavioural probe on the pinned tree through the public search entry point (mock redis client
  records the FT.SEARCH query): Tag string, Tag array, NumericFilter value, TimestampFilter value,
  GeoFilter value, legacy `buildCustomQuery` tag/text and legacy `string[]` filter all place the
  attacker-supplied text into the query unescaped. Details live in the tests.

## Security property (stated once)

No caller-supplied metadata-filter value and no caller-supplied filter field name may be
interpreted as RediSearch query syntax: it must reach Redis as inert data and may not add, remove
or alter a clause or address another field. A value that cannot be represented safely must make
the search fail before any query is sent.

## Levers (each with a different reason a solver would dismiss/skip it)

- T1 pattern A, far second implementation (where): the deprecated store's own query builder
  (`vectorstores.ts:buildCustomQuery`, `vectorstores.ts:prepareFilter` reached through
  `similaritySearchVectorWithScore`). Reason: class is `@deprecated`; its string filters are
  documented as raw pass-through; the report points at the fluent filter builders. Published fix
  does protect it → covered by tests.
- T2 pattern B, how-type, route where protection never existed: filter kinds whose *values* are
  interpolated with no runtime validation — numeric comparisons, date/time bounds and geographic
  filters (`filters.ts` NumericFilter/TimestampFilter/GeoFilter). Reason: the parameters are typed
  `number` / `Date | number` / a unit union, so a solver argues they cannot carry syntax; the fix
  added only field-name checks here. Different reason from T1.
- T3 pattern A, shape trap (field names): every filter class interpolates its field name into
  `@<field>:`; a field name that contains syntax closes the clause and opens another. Reason:
  field names are application configuration, not end-user values. Distinct from T2's value route.
- T4 injected S1, how-type (shape): a plain-object metadata filter shorthand added to the fluent
  store (`filter_object.ts` + `prepareFilter`/entry-point widening); tag arrays, scalar tags, text
  and numeric ranges are templated directly. Reason: it is a convenience path, not one of the
  builder classes the report names. Dismissed differently from T1's deprecated store.
- T5 injected S2, how-type (ordering/shape): a tag filter for separator-joined stored values
  (`filter_stored.ts`) that splits the caller's value on the configured separator *then* joins with
  `|`. Reason: it is separator handling rather than the reported tag/text escaping; a plausible fix
  escapes before splitting and breaks legitimate multi-value matching. Coupled value: `"red,blue"`
  must still match two tags.
- T6 injected S3, how-type (template vs data): `Custom` gained placeholder parameters
  (`filters.ts` CustomFilter); the raw template stays caller-controlled, but parameter values are
  substituted into the query. Reason: `Custom` is documented raw by design. Coupled value: raw
  `Custom` text and ordinary substitutions keep working.

## Routes investigated and excluded

- `CustomFilter` raw query text and the legacy plain-`string` filter: documented raw pass-throughs
  by design; the sibling S3 only adds a *data* channel; the raw forms are kept by functional tests.
- `vectorKey` / `metadataKey` / `contentKey` and schema field names: developer configuration, not
  caller-supplied; noted out of scope.
- `k` in the KNN clause: not a metadata-filter value; not part of this advisory's protection.
- Encodings/spellings of the same characters: excluded by the build rules.
- NumericFilter/TimestampFilter/GeoFilter field-name checks are part of T3; their *value*
  interpolation is T2.

## Verification plan (recorded after the build)

- Injection applied to the pinned tree; project tests re-run.
- Oracle patch (published source fix + T2 values + T3 StoredTag + T4/T5/T6 escaping) built from
  the injected tree; all hidden security + functional tests run on pinned (nop), oracle, and each
  wrong-fix patch.
- Gate: static → nop → oracle → patches.

## Build record

- Upstream fix reduced to source changes: `filters.ts`, `vectorstores.ts` and the new
  `query_safety.ts` (no upstream regression tests or changeset are shipped). The pinned tree does
  not contain the fix's tests (`git diff pinned..fix` adds them), so there is no leaked regression.
- Injected siblings compiled into the shipped tree: `filter_object.ts` (+ `vectorstores_fluent.ts`
  branch and public filter type), `filter_stored.ts` (+ exports), and optional `$name` parameters on
  the existing `Custom`/`CustomFilter` in `filters.ts`.
- Oracle adds, on top of the published source fix, runtime value validation for the numeric,
  date/time and geographic filters, a field-name check for the injected stored tag filter, and
  escaping for the three sibling paths. Raw `Custom` text (no parameters) and the legacy plain-string
  filter stay raw by design and are covered by functional tests.
- Local rehearsal (host, same dependency versions as the verifier, `tests/score.py`):
  - pinned+injected: reward 0.0, security 0/37, functional 127/127 (34 hidden + 93 project).
  - oracle: reward 1.0, security 37/37, functional 127/127.
  - every `sf-miss-*` patch: at least one security failure, all functional pass (31-35/37 security).
  - `sf-stringonly`: exactly the array/Set security tests fail.
  - `ff-overbroad`, `ff-refuse-all`, `ff-ordering`, `ff-escape-custom`: functional failures,
    security 37/37.
  - `pass-hardening`, `pass-alt`: reward 1.0.
- Register: three Pattern B rows appended to `build/audit/uncovered-routes.tsv` for the numeric,
  date/time and geographic value routes; current upstream `main` (38eb4d8) still has only the
  field-name checks there, so `present_in_latest=yes`.
- Toolchain: Node 22 base; pnpm 10.14 workspace install + built `@langchain/core` in the agent
  image; a pinned flat npm dependency tree (`tests/deps`) in the verifier, symlinked at
  `/workspace/node_modules` by `tests/test.sh`.
- Verifier image rehearsal (real `lcjs-tests-test` image, test.sh as root, as Harbor runs it):
  pinned+injected reward 0.0 (security 0/37, functional 127/127); oracle reward 1.0 (164/164);
  `sf-miss-legacy` reward 0.8378 (6 security failures, 0 functional); `ff-overbroad` reward 0.0
  (10 functional failures); `pass-alt` reward 1.0.
- Gate: static PASSED; nop PASSED (security 0/37, functional 127/127). Oracle and patches run next;
  the shared VM's Harbor sometimes leaves containers "Dead" after scoring, so individual stages
  may need an infra retry.


## Gate result (2026-10-24T04:35:01Z)

- static: PASS (only the downstream-authored blind patch and FAIRNESS.md remain outstanding, as allowed).
- nop: PASS — security 0/37 (every security test fails on the pinned+injected tree), functional 127/127.
- oracle: PASS — three trials, each reward 1.0, 164/164, identical per-test maps.
- patches: PASS — 13 checks: sf-miss-{legacy,values,fields,shorthand,storedtag,params} and sf-stringonly are
  security_fail (security 2-6 failing, functional all pass); ff-overbroad / ff-refuse-all / ff-ordering /
  ff-escape-custom are functional_fail (functional 3-26 failing, security all pass); pass-hardening and
  pass-alt score 1.0.
- A `--only` stage run writes `gate_report.partial.json`; each stage above was run on its own, in order.

## What I could not verify

- The target models' behaviour (the bar): no trials were run, as instructed.
- `present_in_latest` was checked read-only on upstream `main` at 38eb4d8: the three Pattern B value
  routes still have only field-name checks, so they are recorded as `yes`.
- The agent image resolves its flat npm tree without a lockfile (the verifier ships a pinned lockfile);
  the direct dependency versions match the verifier's, transitive versions are resolved at image build.
- The shared VM's Harbor occasionally leaves containers "Dead" after the verifier has scored; every
  stage above still returned a scored trial. A retry is the correct response to such a stage error.
