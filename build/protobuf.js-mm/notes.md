# protobuf.js-mm — build notes

- Start UTC: 2026-10-18T19:31:22Z
- End UTC: 2026-10-18T21:05:00Z

## Plan (written before build)

### Recurring trust decision
A name taken from untrusted input (a text-format map key, a schema field name, an enum
identifier, an option name, a descriptor enum value name, a generated enum value name) must
be treated as an own data property of the object it is written to or read from. It must never
reach `Object.prototype` through `__proto__` and must never read an inherited member as if it
were message data.

### Main lever + far sites (Pattern A, published fix)

- **T1 (landing)** textformat map-entry write `map[key] = value` with key `__proto__` mutates
  the returned map's prototype. `ext/textformat.js:664`. Shapes: brace `{ key: "__proto__"
  value {...} }`, angle `< ... >`, list `labels: [ {...}, {...} ]`, missing key (default `""`).
  Reason to dismiss: none — the report leads here.

- **T2** textformat writes `object[field.name]` and creates map containers at `object[field.name]`;
  a schema field named `to_string` / `has_own_property` becomes `toString` / `hasOwnProperty`.
  `ext/textformat.js:640,467,652`. Repeated `toString` crashes on the inherited function;
  map `hasOwnProperty` writes the entry onto `Object.prototype.hasOwnProperty`.
  Reason to dismiss: field names come from the `.proto` schema, which looks trusted — only the
  map key is user input.

- **T3** `Enum` builds `valuesById = {}` so `values = Object.create(valuesById)` inherits
  `Object.prototype`; textformat `parseEnum` then accepts `constructor` / `toString` as enum
  identifiers. `src/enum.js:41`. Also `Enum#add("constructor")` reports a false duplicate.
  Reason to dismiss: Enum is a schema/reflection API that never parses text format.

- **T4** `ReflectionObject#getOption` returns inherited properties; `setOption(..., ifNotSet)`
  skips shadowing names. `src/object.js:272-294`. Reason to dismiss: the reflection options
  API, not the text format parser.

- **T5** `.proto` option aggregate values read `objectResult[propName]` without an own-property
  check, so a member named `constructor` / `to_string` is picked up and concatenated.
  `src/parse.js:822`. Reason to dismiss: the `.proto` syntax parser is a different input
  language from text format.

- **T6** `util.merge(dst, src, ifNotSet)` treats inherited keys as already set. `src/util/minimal.js:285`.
  Reason to dismiss: an internal merge helper, not an entry point a caller feeds untrusted names.

- **T7** `Enum.fromDescriptor` writes `values[valueName] = value` and `valuesOptions[valueName] = options`
  for a descriptor value named `__proto__`, setting the `valuesOptions` prototype;
  `Type.fromDescriptor` map-entry table and `groupTypeNames` are plain `{}`.
  `ext/descriptor.js:704-707,254,1009`. Reason to dismiss: the descriptor import path
  (FileDescriptorSet), a second implementation, not text format.

- **T8** `pbjs -t static` / `static-module` emits `valuesById = {}` into generated enum tables.
  `cli/targets/static.js:1106`. Reason to dismiss: a code generator emitting JS source; the
  generated code's threat model looks different from a parser.

### Injected siblings (track: injected; recurring trust decision)

- **S1** A merge-into-existing-object text-format convenience writes fields and map entries with
  direct assignment into the caller's target. `ext/textformat.js` (`mergeMessage`/`mergeField`/
  `mergeMapEntry` + `textformat.mergeFromText` / `Type.prototype.mergeFromText`, added by inject).
  Entry: `Type#mergeFromText`.
  Reason to dismiss: merge writes into an object the caller already owns, so it is not the
  returned map the report is about.

- **S2** A merge-into-existing-object ProtoJSON convenience writes fields and map entries with
  direct assignment into the caller's target, and does not go through the module's own safe-write
  helper. `ext/protojson.js` (`mergeMessageInto` + `protojson.mergeFromJson` /
  `Type.prototype.mergeFromJson`, added by inject). Entry: `Type#mergeFromJson`.
  Reason to dismiss: a different wire format from the reported text format, and the module already
  has a safe-write helper that the parse path uses, so the merge path looks covered.

Both are placed where the published fix never touches (new functions that did not exist at the
pinned commit; `ext/protojson.js` merge path is outside the published-fix diff).

### Coupled must-keep-working (functional)

- A `__proto__` map key stays a stored, enumerable own key with its value reachable, and the
  returned map keeps `Object.prototype` as its prototype (no null-prototype maps).
- Fields named `toString` / `hasOwnProperty` still parse into real arrays / maps.
- Enum values and options named `constructor` / `toString` stay settable (no false duplicate).
- Ordinary map keys, enum identifiers and option names keep working exactly as today.
- `Enum#add("__proto__", n)` keeps ignoring the reserved name (existing behaviour).
- Generated static enums still work as TypeScript-compatible tables (`values[n] === name`,
  `values[name] === n`).

### Input shapes (variants a one-case fix misses)

- map key `__proto__` with brace delimiter, angle delimiter, and list form
- map entry missing its key (defaults to `""`)
- repeated field named `to_string`, map field named `has_own_property`
- enum identifier `constructor` and `toString`
- descriptor enum value named `__proto__` with options
- parsed `.proto` option aggregate member named `constructor` / `to_string`
- merge-from-text and merge-from-JSON map key `__proto__` into a caller-owned target (injected S1 / S2)

### Sites / routes / services the security tests cover

Entry points: `textformat.fromText` / `Type#fromText` (incl. `textformat.install`), `protobuf.parse`,
`new protobuf.Enum` / `Enum#add` / `Enum.fromJSON`, `ReflectionObject#getOption`/`setOption`,
`util.merge`, `Enum.fromDescriptor` / `Type.fromDescriptor`, `protojson.fromJson` / `Type#fromJson`,
`textformat.mergeFromText` / `Type#mergeFromText`, `pbjs -t static`.
Services: none.

### What must not appear in instruction.md (leak_terms)

Identifiers below. The instruction speaks at product level only.

## Levers (one line each)

- T1 map key (A, landing): text-format map-entry write `map[key] = value` with key `__proto__`.
  `ext/textformat.js:791` addMapEntry / `:500` mergeMapEntry. Shapes: brace, angle, list, scalar,
  omitted key. Dismiss: none.
- T2 field names (A, far): plain property writes of camelCased schema field names.
  `ext/textformat.js:767,779,594`. Dismiss: field names come from the `.proto` schema.
- T3 enum names (A, far): `valuesById = {}` so `values = Object.create(valuesById)` inherits
  `Object.prototype`. `src/enum.js:41` / `Enum#add`. Dismiss: Enum never parses text format.
- T4 settings (A, far): `getOption` returns inherited members; `setOption(..., ifNotSet)` skips
  shadowing names. `src/object.js:272,285`. Dismiss: the reflection options API, not the parser.
- T5 schema options (A, far): `objectResult[propName]` without an own-property check.
  `src/parse.js:822`. Dismiss: the `.proto` parser is a different input language.
- T6 merge helper (A, far): `util.merge` ifNotSet treats inherited keys as already set.
  `src/util/minimal.js:285`. Dismiss: an internal helper, not an entry point.
- T7 descriptors (A, far): `mapEntries = {}`, `values[valueName] = value`, `groupTypeNames`
  `names = {}`. `ext/descriptor.js:254,707,1008`. Dismiss: a second implementation.
- T8 generated (A, far): emitted `valuesById = {}` / `ext = {}`. `cli/targets/static.js:1106`,
  `cli/targets/proto.js:280`. Dismiss: a code generator emitting source text.
- S1 injected: `Type#mergeFromText` writes into a caller-owned target (`ext/textformat.js:462,500`).
  Dismiss: not the returned map the report is about.
- S2 injected: `Type#mergeFromJson` writes into a caller-owned target (`ext/protojson.js:386,413`).
  Dismiss: different wire format; the module already has a safe-write helper.

Distinct reasons-to-skip: none / trusted-schema / different-API / different-language /
internal-helper / second-implementation / generator / caller-owned-target / looks-covered.

## Verified

- Flaw reproduces at pinned+injected through the real surfaces: `Type#fromText` (braced, angle,
  list, scalar, omitted key), `.proto` compile + `Enum#add`, `getOption`/`setOption`, `util.merge`,
  `Enum.fromDescriptor` / `Type.fromDescriptor`, `pbjs -t static` (evaluated as a generated
  module), `Type#mergeFromText`, `Type#mergeFromJson`. Offline; no network.
- Oracle (`solution/fix.patch`) closes all 10 levers and legit use keeps working. 53 security /
  42 functional task tests: 53 fail on vulnerable, all pass on oracle; functional 42/42 on both.
- Project area tests: 10 pristine files (`api_textformat`, `api_protojson`, `api_enum`,
  `api_object`, `api_util`, `api_descriptor`, `api_mapfield`, `comp_options`,
  `comp_options-parse`, `comp_options-textformat`) restored over `/app/tests` and run with the
  project's own tape runner — pass on both trees. Nothing deselected.
- All 19 check patches behave as declared (10 security_fail each isolating one lever, 5 further
  security_fail wrong-fix shapes, 2 functional_fail, 2 pass). Verified by applying each to the
  vulnerable tree and running the hidden suite:
  - sf-miss-map-key 6F, sf-miss-field-name 5F, sf-no-enum 9F, sf-no-settings 6F,
    sf-no-schema-options 3F, sf-no-merge-helper 4F, sf-no-descriptor 6F, sf-no-generated 5F,
    sf-miss-merge-text 5F, sf-no-merge-json 4F (each: security fail, functional 42/42);
  - sf-crash-map-key 11F, sf-reads-only-settings 2F, sf-textformat-only 37F,
    sf-published-only 10F, sf-far-sites-only 16F;
  - ff-reject-inherited-names functional 11F, ff-drop-reserved-map-keys functional 1F;
  - pass-hardening and pass-alt-approach both 53/53 + 42/42.
- `fix.patch` and every `checks/*.patch` apply with `patch -p1` on the pinned+injected tree.

## Not verified / dropped

- `present_in_latest` for the injected siblings is n/a (they are our-copy-only).
- Pattern B uncovered route `util.setProperty` (`src/util.js`) was not pursued: the input says
  uncovered routes are "none", and it is outside this advisory's own protection.
- T6 `constructor` as a merge key is intentionally skipped by `isUnsafeProperty` in both states
  (accepted oracle behaviour); the T6 tests cover `toString` / `hasOwnProperty` / `valueOf` /
  `isPrototypeOf` only.
- `Enum#add("__proto__")` is already a no-op in both states (pre-existing reserved-name skip);
  kept as functional "must keep working", not a security lever.
- Generated `__proto__` enum values never reach the table (same reserved-name skip), so T8 covers
  the inherited-member names only.

## Gate

- static: only the two allowed leftovers (missing `blind` patch, missing `FAIRNESS.md`).
- nop: PASSED — security 0/53 (all fail on vulnerable), functional 42/42.
- oracle: PASSED — reward 1.0, security 53/53, functional 42/42, identical across 3 runs.
- patches: in progress (Docker networking flake under concurrent host load; retries).
- Scratch verifier note: `cli/node_modules/protobufjs` in the work trees pointed at the oracle
  checkout, so local `pbjs` runs hid the pre-fix `Enum#add` false-duplicate. The harness now
  retargets that symlink at the tree under test; Docker (where it points at `/app`) was correct.

## End UTC
2026-10-18T21:05:00Z
