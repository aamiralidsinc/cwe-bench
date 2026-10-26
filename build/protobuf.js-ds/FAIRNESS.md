# FAIRNESS.md — protobuf.js-ds (pre-trial fairness & leniency review)

Reviewed on disk: `tasks/protobuf.js-ds/instruction.md`, all 34 security + 23 functional
tests, `tests/support/harness.js`, `tests/test.sh`, `tests/score.py`,
`solution/fix.patch`, `environment/injection.patch`, `manifest.json`, `notes.md`, all 19
`checks/*.patch`. No Docker, trial or gate was run; no upstream fix consulted online.

Legend — properties of the instruction's one general rule (a test is fair when the
property, read literally, applies to the route it drives; no route-naming sentence needed):
**P1** No prototype access ("No such name may be used to reach, read or replace the
prototype of any object …, and no shared built-in object may be modified"); **P2** Data is
data ("stored as an own, enumerable property under exactly that name … the ordinary
prototype … not dropped, renamed or refused"); **P3** Lookups are exact ("an entry that is
not present as an own property is absent … the objects and tables the library returns, the
ones it uses internally and the ones it is given … written, looked up or read back");
**P4** Ordinary inherited-looking names are ordinary; **P5** Everything built follows this;
**P6** Prototype-replacing names in recorded configuration are ignored; **P7** Filling only
what is absent; **C** Contracts that must keep working.

## 1. Test-by-test table

### security/01_textformat_map_proto.js

| test | asserts | fair because | could a correct fix fail? | risk |
|---|---|---|---|---|
| brace-delimited `__proto__` key stays data | map proto is `Object.prototype`; key own+enumerable; value reachable; no field leak | P2 "own, enumerable … value reachable"; P1 "container keeps the ordinary prototype" | no | low |
| angle-delimited `__proto__` key stays data | same for `<…>` form | P2/P1, form-independent | no | low |
| map list keeps `__proto__` entry next to ordinary ones | both keys own+enumerable; ordinary value kept | P2/P4 | no | low |
| scalar map entry with `__proto__` key stays data | own key, value `"x"` | P2 | no | low |

### security/02_textformat_field_names.js

| test | asserts | fair because | could a correct fix fail? | risk |
|---|---|---|---|---|
| repeated field shadowing inherited name parses as data | `toString` own, `["x","y"]` | P4 "declared … ordinary data"; P2 | no | low |
| list form of a repeated shadowing field | `toString` own, `["x","y"]` | P4/P2 | no | low |
| map field shadowing inherited name, no side effects | own map `{a:"b"}`; `Object.prototype.hasOwnProperty.a` unset | P4/P2; P1 "no shared built-in object may be modified" | no | low |
| repeated field named like a different inherited property | `propertyIsEnumerable` own, `["z"]` | P4/P2 | no | low |
| map field named like a different inherited property | `isPrototypeOf` own `{a:"b"}`, no side effect | P4/P2/P1 | no | low |

### security/03_enum_tables.js

| test | asserts | fair because | could a correct fix fail? | risk |
|---|---|---|---|---|
| text-format inherited enum name rejected | `kind:` set to `constructor`, `toString`, `isPrototypeOf` or `propertyIsEnumerable` throws | P3 "never answered with a property the object inherits"; "fails with an ordinary, catchable error" | no — `H.throws` accepts any error | low |
| JSON inherited enum name rejected | same via `protojson.fromJson` | P3; "Every name that appears in such input" | no | low |
| enum values table does not expose inherited properties | `new Enum("Shadow",{}).values.constructor/toString/… === undefined` | P3 applies to "tables the library returns" and "read back" | no — a lookup-site-only fix fails, but P3 states the rule for returned tables read back | medium |
| schema may declare shadowing enum values | `constructor=0`, `toString=1`, `valuesById[1]`, text parse | P4 "in every relation the library keeps" | no | low |
| shadowing enum value added via public API | `add("constructor",2)` both directions | P4 | no | low |
| refused enum lookup leaves table intact, parsing works | keys/values unchanged; valid parse after throw | C "keeps working afterwards and leaves no partial record behind" | no | low |

### security/04_options_and_merge.js

| test | asserts | fair because | could a correct fix fail? | risk |
|---|---|---|---|---|
| unset option not read from prototype | `getOption("toString"/"constructor"/…) === undefined`; ordinary works | P3 "established answer … is to report absence" | no | low |
| shadowing option name set and read | `toString`/`constructor` stored; `ifNotSet` no overwrite | P4 "recorded … ordinary data"; C | no — P7's `constructor` refusal is scoped to filling; P4 governs options | medium |
| merging defaults treats inherited property as absent | `merge({}, {toString:"value"}, true)` creates own keys | P7 "counts as present only when it is an own property" | no | low |

### security/05_proto_option_aggregate.js

| test | asserts | fair because | could a correct fix fail? | risk |
|---|---|---|---|---|
| schema aggregate option keeps shadowing member as data | `constructor:"ctor"`, `to_string`, `ordinary` kept, not concatenated | P4; P3 exact read | no | low |

### security/06_descriptor_import.js

| test | asserts | fair because | could a correct fix fail? | risk |
|---|---|---|---|---|
| imported `__proto__` enum value cannot leak options | `valuesOptions` proto `Object.prototype`; `deprecated` not inherited; ordinary values kept | P6 "ignored … rest of that work"; P2 container keeps ordinary proto | no — drop and own-store both pass | low |
| imported field named like inherited property not a map entry | field stays repeated/non-map; ordinary values round-trip | P3 "entry not present as an own property is absent" | no | low |
| imported nested type not marked a group | `group` not set; shape unchanged; round-trip | P3 | no | low |

### security/07_cli_generated_tables.js

| test | asserts | fair because | could a correct fix fail? | risk |
|---|---|---|---|---|
| emitted enum table does not resolve inherited values | generated `E.toString/constructor/isPrototypeOf/propertyIsEnumerable === undefined`; `A/B` kept | P3 read-back; P5 "every artifact it produces" | no | low |
| emitted conversion code does not read absent field | `fromObject({})` no own `toString`; encodes 0 bytes | P3 "the ones it is given"/read; P5 | no | low |
| generated schema text resolves extension target exactly | exit 0; `extend toString` and `extra` present | P3 internal name-keyed lookup; P5 | no | low |

### security/08_dotted_settings.js

| test | asserts | fair because | could a correct fix fail? | risk |
|---|---|---|---|---|
| dotted setting keeps given value, not inherited | `features.toString === "EXPLICIT"` | P4/P2 | no | low |
| inherited inner segment does not touch shared prototype | value stored; `Object.prototype.toString.inner` unset | P2/P1 | no | low |
| schema keeps dotted feature setting as data | `options.features.toString` kept | P4/P2 | no | low |
| unsafe final name leaves container prototype alone | `options.features` proto ordinary; `marker` absent | P6 "ignored … rest of that work carried out" | no — the clause keeps the surviving prefix; a whole-path early return would fail but drops an ordinary segment | medium |
| schema unsafe dotted setting leaves containers alone | `options.features` and `parsedOptions["features"]` exist, protos ordinary, `marker` absent | P6 | no — same prefix-container reading | medium |

### security/09_parsed_option_paths.js

| test | asserts | fair because | could a correct fix fail? | risk |
|---|---|---|---|---|
| dotted parsed option keeps shadowing segment | `(named).toString === "v"`, `a` kept | P4/P2 | no | low |
| unsafe parsed-option segment leaves prototype alone | option proto `Object.prototype`, `marker` absent, `a` kept | P6 | no — option exists from the sibling `(named).a` | low |

### security/10_converted_object_reads.js

| test | asserts | fair because | could a correct fix fail? | risk |
|---|---|---|---|---|
| conversion does not materialise absent fields | no own `toString`/`valueOf`; repeated `[]`, map `{}`; empty encode | P3 "the ones it is given"; P2 | no | low |
| conversion does not read another inherited name | `propertyIsEnumerable`/`isPrototypeOf` not own; empty encode | P3 | no | low |

### functional/01_textformat_legit.js

| test | asserts | fair because | could a correct fix fail? | risk |
|---|---|---|---|---|
| scalar/repeated/nested/map parse as before | ordinary values parse | C "Ordinary input behaves exactly as it does today" | no | low |
| map keeps ordinary prototype for ordinary keys | proto `Object.prototype`, keys `["a"]` | C; P2 | no | low |
| empty lists and missing map keys keep defaults | `[]`, `labels[""]` | C | no | low |
| later duplicate map key overwrites | last value wins, one key | C | no | low |
| ordinary messages format back to text | `toText` keeps count/key | C | no | low |

### functional/02_enum_legit.js

| test | asserts | fair because | could a correct fix fail? | risk |
|---|---|---|---|---|
| ordinary enum parse and numeric lookup | `values.ZERO`, `valuesById[1]`, `values[1]` | C "numeric round-trips are unchanged" | no | low |
| ordinary enum JSON parse | names and numbers accepted | C | no | low |
| enum JSON import/export | `fromJSON`/`toJSON` round-trip | C | no | low |
| JSON-imported shadowing value | `fromJSON({values:{toString:0}})` stored | P4 | no | low |

### functional/03_options_legit.js

| test | asserts | fair because | could a correct fix fail? | risk |
|---|---|---|---|---|
| ordinary options set/read/merge | set/get/`ifNotSet`/`setOptions` | C | no | low |
| unsafe option name ignored, options shape intact | no throw, proto unchanged, `hasOwn("__proto__") === false` | P6 "is ignored … not stored" | no — an own-`defineProperty` store fails, but P6 forbids storing it | medium |
| ordinary merging semantics | ordinary keys merged; `__proto__`/`prototype`/`constructor` skipped; `safe` kept | C; P7 "existing refusal … unchanged" | no — refusal asserted without `ifNotSet`, but the clause says unchanged and the repo already does it | medium |

### functional/04_parse_legit.js

| test | asserts | fair because | could a correct fix fail? | risk |
|---|---|---|---|---|
| aggregate and repeated option members kept | `a`,`b`,`list`; field option works | C | no | low |
| dotted parsed options nested and merged | `(named).a/.b` kept | C | no | low |

### functional/05_descriptor_legit.js

| test | asserts | fair because | could a correct fix fail? | risk |
|---|---|---|---|---|
| normal descriptor builds maps and enums | map decoded; enum `constructor=1` both ways | C; P4 | no | low |

### functional/06_cli_legit.js

| test | asserts | fair because | could a correct fix fail? | risk |
|---|---|---|---|---|
| generated module encodes/decodes | enum/map round-trip | C; P5 | no | low |
| generated module converts plain objects | `fromObject`/`toObject` ordinary | C; P5 | no | low |
| generated schema text keeps ordinary extensions | `extend Target`, `extra`, `target` present | C; P5 | no | low |

### functional/07_conversion_legit.js

| test | asserts | fair because | could a correct fix fail? | risk |
|---|---|---|---|---|
| present shadowing fields convert both ways | `toString`/`constructor`/`hasOwnProperty`/`valueOf` present | P4; C | no | low |
| plain messages have unchanged key set | `["ordinary"]` | C | no | low |

### functional/08_json_legit.js

| test | asserts | fair because | could a correct fix fail? | risk |
|---|---|---|---|---|
| ordinary JSON parse and round-trip | enum/map/repeated | C | no | low |
| JSON map keys and duplicate rejection | keys preserved; duplicate key throws | C; standard expert knowledge: duplicate JSON object keys are invalid | no | low |

### functional/09_project_area.js

| test | asserts | fair because | could a correct fix fail? | risk |
|---|---|---|---|---|
| pristine project area tests still pass | five upstream files pass | C "Unrelated existing behaviour is unchanged"; "Keep legitimate use working" | no | low |

## 2. Leniency (QUALITY, non-blocking)

### 2a. Per security property

| property | most plausible wrong fix | caught by |
|---|---|---|
| P1 | drop/refuse the `__proto__` map entry | security/01 (all 4); `ff-refuse-all` fails functional/01 |
| P1 | null-prototype text-format map | functional/01 "map keeps the ordinary prototype"; security/01 `assertSafeMap`; `ff-overbroad` |
| P1 | guard only the write, keep inherited reads | security/01/02; `sf-miss-r1` |
| P1 | blacklist only the inherited names the tests probe | **nothing** (see 2c.1) |
| P2 | refuse every shadowing name | security/03.4–5, security/04.2, functional/05, functional/07; `ff-refuse-all` |
| P2 | store `__proto__` option via `defineProperty` | functional/03.2 (`hasOwn === false`) |
| P2 | null-prototype returned containers | functional/01.2; security/06.1 (`valuesOptions` proto) |
| P3 | patch parser lookups, leave the values table | security/03.1–3; `sf-miss-t3` |
| P3 | fix returned tables, leave internal/given tables | security/06.2–3 (`sf-miss-t8/t9`), security/10 (`sf-miss-r2`) |
| P3 | use `in`/truthiness instead of own-property | security/10 (`toString in {}`), security/02 (`sf-miss-t2`) |
| P4 | refuse all names matching `constructor`/`toString` | security/03.4–5, security/04.2, functional/05, functional/07 |
| P4 | allow declared but not added/recorded names | security/03.5, security/04.2, functional/02.4 |
| P5 | runtime-only generator fix | security/07.1 (`sf-miss-t7`), security/07.2 (`sf-miss-r2`), security/07.3 (`sf-miss-t10`) |
| P6 | throw on the unsafe setting | security/08.4–5, security/09.2 (unwrapped) |
| P6 | store it as own data | functional/03.2; security/08/09 accept it |
| P6 | drop the whole setting instead of the name | security/08.4–5 (container missing) |
| P6 | let a descriptor value reparent the table | security/06.1 (`sf-miss-t6`) |
| P7 | presence via `dst[key] === undefined` | security/04.3 (`sf-miss-t4b`) |
| P7 | own-check but overwrite existing own entries | functional/03.1; security/04.2 |
| P7 | apply the merge refusal to every API | security/04.2, security/03.4–5 |

### 2b. Per trap (manifest.traps)

| trap | most plausible wrong fix | caught by / check |
|---|---|---|
| T1 | drop/refuse the entry, or null-proto the map | security/01.1–4; functional/01.2–3; `sf-miss-t1`, `ff-overbroad`, `ff-refuse-all` |
| T2 | fix map keys only; trust schema field names | security/02.1–5; `sf-miss-t2` |
| T3 | own-check parser lookups only, leave the values table | security/03.1–3; `sf-miss-t3` |
| T4 | own-check `getOption` only; leave merge/`ifNotSet` | security/04.1–3; `sf-miss-t4` (option+merge), `sf-miss-t4b` (merge only) |
| T5 | treat schema compilation as trusted | security/05.1; `sf-miss-t5` |
| T6 | fix runtime enum tables only; let `valuesOptions` inherit | security/06.1; `sf-miss-t6` |
| T7 | runtime-only fix; leave the emitted table | security/07.1; `sf-miss-t7` |
| R1 | guard unsafe segments but keep inherited reads | security/08.1–3, security/09.1; `sf-miss-r1` |
| R2 | trust the caller's object; runtime-only converter | security/10.1–2, security/07.2; `sf-miss-r2` |
| S1 | fix `setProperty`, leave the single-segment fast path | security/09.1–2; `sf-miss-s1` |
| S2 | guard only while recursing | security/08.4 (object value), security/08.5, security/09.2; `sf-miss-s2` |
| T8 | leave the map-entry table inheriting | security/06.2; `sf-miss-t8` |
| T9 | leave the group-name table inheriting | security/06.3; `sf-miss-t9` |
| T10 | leave the extension-grouping table inheriting | security/07.3; `sf-miss-t10` |

### 2c. Wrong fixes no test catches

1. A name blacklist tuned to the probed names (`constructor`, `toString`,
   `hasOwnProperty`, `valueOf`, `isPrototypeOf`, `propertyIsEnumerable`, `__proto__`):
   `toLocaleString`, `__defineGetter__`, `__lookupGetter__` etc. are never probed.
2. JSON map keys named `__proto__` and JSON message fields whose schema name shadows an
   inherited property (JSON is covered only for enum names).
3. A schema field literally named `__proto__` in text format and in the converter
   (security/02 and /10 use only inherited names; security/01 covers map keys only).
4. Descriptor option members of prototype-replacing shape outside enum-value options
   (`pass-hardening.patch` guards them; no test drives them).
5. Storing a descriptor enum value named `__proto__` as own data instead of ignoring it
   (security/06.1 accepts both, though P6 says ignored).
6. Shared built-ins other than `Object.prototype.hasOwnProperty.a` and
   `Object.prototype.toString.inner` are not inspected.
7. Partial-record cleanup after a refusal is only asserted for enum lookups
   (security/03.6); no map/option case.

## 3. Hints (QUALITY, non-blocking)

| quote | why it is a hint | neutral wording |
|---|---|---|
| "A caller supplied a name that the JavaScript runtime reserves for an object's prototype." | paraphrases the prototype-replacing key and the trap | "A caller's value ended up being used as the object's prototype." |
| "a name that had never been recorded was sometimes answered with a property the object merely inherits, and a name that happened to coincide with such an inherited property was lost, crashed, or was combined with something inherited" | enumerates the three failure variants the hidden tests vary | "absent names were sometimes answered with inherited properties, and names that coincided with such properties were mishandled" |
| "the existing refusal of the names that cannot be stored safely (the prototype-replacing name, `prototype` and `constructor`)" | names the exact special values; contradicts "Do not special-case particular names or values" | "the existing refusal of unsafe names is unchanged" |
| "Fix the problem and its close variants in the library itself, for every operation and input surface that can reach it, not only the single case above." | advertises a hidden variant list | "Fix the problem in the library itself wherever it can occur." |

No file, function or parameter name, no advisory id and no flaw count appears.

## 3a. Required: generalize

1. "the library builds objects, tables and recorded configuration from that input. It
   returns those to the application or uses them while doing so." — object-kind/stage
   list. Reword: "the library builds its results from that input."
2. "This holds for the objects and tables the library returns, the ones it uses internally
   and the ones it is given, and whether a name is written, looked up or read back." —
   three container roles plus object kinds. Reword: "This holds for every container the
   library holds or consults, and whether a name is written, looked up or read back."
3. "every object the library returns, every name-keyed lookup it consults, and every
   artifact it produces for another program to load" — names the emission stage. Reword:
   "every result the library produces, including anything it emits."
4. "Prototype-replacing names in recorded configuration are ignored. Where the library is
   recording configuration about what it is building, or reading a supplied description of
   what to build, …" — names the option and descriptor stages. Reword: "A name that would
   replace the prototype of the container it is written into is ignored: it is not stored,
   it raises no error, and the rest of the work completes as if that name were absent."
5. "A name that was declared or recorded" / "A name that was never declared or recorded" —
   "declared"/"recorded" are the schema and option stages. Reword: "A name the library
   holds as data" / "A name the library does not hold".
6. "When the caller asks that only absent entries be filled" — names the `ifNotSet` entry
   point. Reword: "An entry counts as present only when it is an own property; only
   entries that are not present are filled."

## 4. Realism (QUALITY, non-blocking)

T1–T10, R1 and R2 are real, unmodified upstream code at the pinned commit, reachable
through `textformat.fromText`, `protobuf.parse`, `Type.fromObject`,
`Enum`/`Enum.fromDescriptor`/`Root.fromDescriptor`, `getOption`/`setOption`,
`util.merge`, `util.setProperty`, and the bundled `pbjs` (static-module and proto
targets). T8–T10 are routes the published fix closed; R1–R2 are routes it left open;
those are realistic by definition, not "beyond the advisory". S1 (single-segment
parsed-option fast path) and S2 (guard scoped to recursion) are injected but are natural
maintainer mistakes, reachable through `.proto` options and `features.*`; neither is
contrived. The oracle's `=== "__proto__"` checks are legitimate for the one JS prototype
setter, and `pass-alt.patch` shows a generic `Object.defineProperty` solution also passes.
One artifact-accuracy issue: `manifest.verified.routes[0]` describes the final-segment
prototype replacement as part of R1, while `injected_siblings` assigns it to S2.

## 5. Verdict

**UNFAIRNESS gate: READY.** Every security test is covered by P1–P7 read literally over
the protected data/outcome; none needs a route-naming sentence. The natural correct fix
following the stated mechanism (own-property lookups, null-prototype name tables,
per-segment ignore of the prototype-replacing name) passes every test. The only
borderline points — security/08.4–5 expecting the surviving `features` container, and
`setOption` counting as "recorded configuration" — follow from "the rest of that work is
carried out" and from the repo's existing per-segment helper; a whole-path early return
would fail but drops an ordinary segment, contrary to P2/P6. No "yes"/unresolved "maybe".

**Required: generalize** — see §3a (six quotes; reword as the single property over the
protected data/outcome).

**Quality to tighten:**
- Add an unprobed inherited name (`toLocaleString`, `__defineGetter__`) to field, enum,
  option, merge and converter tests; add JSON map-key/field cases and a field literally
  named `__proto__`; add a descriptor option-member case and assert a descriptor
  `__proto__` value is ignored, not own; probe another shared built-in; add one
  non-enum partial-record check.
- Neutralize the four hints in §3.
- Correct `manifest.verified.routes[0]` (R1 vs S2).

**Human review:** confirm that "the rest of that work" is intended to keep the parent
container after a lone unsafe final segment (security/08 tests 4–5), and that
`setOption` falls under "recorded configuration".

GATE_A: READY
NEEDS_HUMAN_REVIEW: YES
