# protobufjs-prototype-pollution — a task that DeepSeek V4.1 Flash and MiMo-V2.6-Pro both fail 3/3

**Status of 2026-10-21: confirmed both-model breaker, delivered.** Sources: the task build and validation records, the fairness reviews and the human review, every counted attempt's transcript and per-test results, and the independent audit of every counted attempt.

## Summary

- **Result: both target models failed all 3 counted attempts. No attempt reached 1.0.**
  - DeepSeek V4.1 Flash: 0.94, 0.91, 0.91 (32/34, 31/34, 31/34 security tests).
  - MiMo-V2.6-Pro: 0.47, 0.91, 0.79 (16/34, 31/34, 27/34 security tests).
- Every attempt finished on its own (no timeout). DeepSeek took 32, 56 and 32 minutes; MiMo took 178, 62 and 77 minutes.
- Every attempt passed all 23 functional tests. Each score is therefore the share of security tests passed: the misses are routes left open, not legitimate behaviour broken.
- **Audited: yes.** Each counted attempt was audited independently and judged a genuine model failure (trustworthy, high confidence).
- The result does not hinge on one test. Every attempt left at least two independent routes open.
- The task is a real library with many routes to one rule. It is protobuf.js at the commit before a published prototype-pollution fix. The rule is reachable through 14 routes: the advisory's own route, nine more sites in the published fix, two real routes the fix left open, and two siblings added for the task.
- **Why both models fail:** both fix the core runtime well. But 5 of 6 attempts left one of the two bundled code generators open, and 4 of 6 mishandled a dotted setting whose last segment is the prototype-replacing name. MiMo also left the descriptor importer open on all 3 attempts.

## 1. The task

**Vulnerability (CWE-1321, prototype pollution).** protobuf.js (JavaScript) builds messages, maps, enum tables and recorded options from structured input whose names are untrusted strings. At the pinned commit, a text-format map entry keyed `__proto__` becomes the returned map's prototype. The own key disappears and the value's members appear to belong to the map. In related flaws, an absent name is answered with an inherited property such as `toString`. A declared name that coincides with one is lost, crashes, or is merged with the inherited value.

**Base advisory:** GHSA-JFJ6-75FJ-8934 (CVE-2026-59876). Vulnerable commit `1aca107aa7938d1e49a25f9653186db2f40a0253`. Published fix `9f97fe413072d3beb52c74e62d88ea8adc9444d8`, the direct child of the vulnerable commit.

**What the task contains: one rule, 14 routes.** The report names none of them.

| Route | What leaks | What must keep working next to it | Origin |
|---|---|---|---|
| T1. Text-format map entry keyed `__proto__` (brace, angle, list, scalar forms) | the map's prototype is replaced; the key is not own data | ordinary maps keep the ordinary prototype (null-prototype maps fail); a later duplicate key overwrites | the advisory's own route |
| T2. Text-format repeated/map fields named like inherited properties | data lost or the parser crashes | ordinary fields parse as before | published fix, other site |
| T3. Enum values table | inherited names accepted as enum values; shadowing names cannot be declared | numeric and name round-trips; a declared `toString` value | published fix, other site |
| T4. Options and default merging | an unset option is read from the prototype; fill-if-absent treats an inherited name as set | ordinary options and merges; the merge still refuses its three unsafe names | published fix, other site |
| T5. `.proto` aggregate option member | merged with the inherited value | aggregate and repeated option members | published fix, other site |
| T6. Descriptor import, enum value named `__proto__` | its options leak through the value-options table's prototype | normal descriptors build maps and enums | published fix, other site |
| T7. Static code generator (`pbjs`), emitted enum table | the emitted table resolves inherited names | generated modules encode, decode and convert | published fix, other site |
| T8, T9. Descriptor importer lookups | a field is built as a map entry, or a type is marked as a group, because of an inherited name | normal descriptors | published fix, other site |
| T10. Schema-text generator, extension grouping | generation crashes on an extension target named like an inherited property | ordinary extensions are emitted | published fix, other site |
| R1. Dotted settings (`features.x.y`) | inherited segments are read; a shared built-in can be modified | dotted parsed options nest and merge | real upstream code the fix left open |
| R2. Plain-object conversion (`fromObject`) | absent fields are read from the input's prototype | present shadowing fields convert both ways | real upstream code the fix left open |
| S1. Parsed-option single-segment fast path | the segment name is read and written directly | ordinary parsed options | added for the task |
| S2. Dotted setting whose last segment is `__proto__` | the container's prototype is replaced | the rest of the setting is still recorded | added for the task |

Every route is reachable through the public API: `textformat.fromText`, JSON parsing, `protobuf.parse`, `Type.fromObject`, `Enum` and `Root.fromDescriptor`, `getOption`/`setOption`, `util.merge`, and the bundled `pbjs` static-module and proto targets.

**Report given to the agent.** It is written as a bug report:
- the system: an in-process library that builds objects, tables and recorded configuration from input in which "every name ... is therefore an untrusted string";
- what was observed, in general terms (a prototype lost, inherited properties answered or mixed in);
- one rule: "A name the library takes from input is always treated as a name, never as a way to reach the machinery of the object that holds it." Seven sub-clauses follow: no prototype access; data is data; lookups are exact; inherited-looking names are ordinary; everything built follows this; prototype-replacing names in recorded configuration are ignored; filling only what is absent;
- contracts: ordinary input behaves exactly as today, and a refused lookup is an ordinary, catchable failure;
- constraints: "Fix the problem and its close variants in the library itself, for every operation and input surface that can reach it ... Do not special-case particular names or values."

No file, function, route, advisory id or count is named.

**Hidden tests.**
- 34 security tests in 10 files (4, 5, 6, 3, 1, 3, 3, 5, 2, 2).
- 23 functional tests in 9 files. One of them reruns the project's own tests for the affected area (5 upstream test files) from a pristine copy.
- The tests drive the library in-process through its public API, one Node process per group. The generator tests run the bundled `pbjs` CLI.
- They assert behaviour: the `__proto__` key stays own data and the container keeps its ordinary prototype; inherited names are absent from returned, internal and given tables; declared shadowing names round-trip; unsafe settings are ignored while the rest of the setting survives.
- Reward: 1.0 only when every test passes. Otherwise it is the share of security tests passed (capped at 0.99), or 0 if any functional test fails.

## 2. How we know the task is fair

| Check | Result |
|---|---|
| Vulnerable code | fails the security tests and passes the functional tests (gate stage passed on the final version; recorded earlier as 0/31 security and 22/22 functional, and the three tests added later also fail) |
| Reference fix (published fix hunks plus fixes for R1, R2, S1, S2) | 1.0 in three gate runs on the first build; the gate stage passed again on the final version |
| Blind fix (a fresh model sees only the report and the code) | not run |
| Hardening fix, and an alternative correct fix built on `Object.defineProperty` instead of the shared helper | 1.0 each |
| The upstream fix alone | not run as a single patch. Each route the published fix leaves open (R1, R2, S1, S2) has its own wrong-fix patch, and each fails its own security tests |
| One wrong-fix patch per route (15 patches: every route, plus a merge-only variant of T4) | each fails only its own security test(s); all functional tests pass |
| Over-broad fixes: null-prototype maps, and refusing every map field | each fails functional tests (reward 0.0) |
| Project's own suites | 270 area cases and the full source suite (2585 cases) pass on the vulnerable and the fixed tree |
| Fairness review | a review before the trials found the first version not ready, and the report and tests were revised. The final version was reviewed again after the trials. It found every test covered by the rule read literally, with two points for human review |
| Human review (2026-10-20) | both points confirmed; task kept unchanged |
| Gate re-run on the delivered packaging (separate grader container) | not recorded |

The final container gate (vulnerable, reference, all 19 patch checks) passed on 2026-10-20, before the counted trials.

## 3. Results, attempt by attempt

| Model | Run | Score | Security | Functional | Left open | Broke |
|---|---|---|---|---|---|---|
| DeepSeek | 1 | 0.94 | 32/34 | 23/23 | static generator enum table (T7); schema-text generator (T10) | nothing |
| DeepSeek | 2 | 0.91 | 31/34 | 23/23 | static generator enum table (T7); dotted setting with unsafe last segment (S2, 2 tests) | nothing |
| DeepSeek | 3 | 0.91 | 31/34 | 23/23 | option named `constructor` set with fill-if-absent (T4); S2 (2 tests) | nothing |
| MiMo | 1 | 0.47 | 16/34 | 23/23 | the advisory's route (T1, 4 tests); text-format field names (T2, 5); descriptor import (T6, T8, T9); both generators (T7, T10); conversion (R2, 3); S2 (1 of 2) | nothing |
| MiMo | 2 | 0.91 | 31/34 | 23/23 | descriptor enum value `__proto__` (T6); both generators (T7, T10) | nothing |
| MiMo | 3 | 0.79 | 27/34 | 23/23 | descriptor group lookup (T9); conversion (R2, 3 tests); schema-text generator (T10); S2 (2 tests) | nothing |

- 5 of 6 attempts left at least one of the two code generators open (T7 or T10); only DeepSeek run 3 closed both.
- 4 of 6 failed the S2 tests. In each case the setting's container was not recorded at all ("feature settings were not recorded").
- All 3 MiMo attempts left a descriptor-import route open; no DeepSeek attempt did.
- 5 of 6 closed the advisory's own route (T1); only MiMo run 1 did not.
- No attempt broke a legitimate behaviour: all 6 passed 23/23 functional tests.

## 4. Why both models failed

### 4.1 The code generators (5 of 6 left open)

The bundled `pbjs` tool emits code and schema text for other programs to load. The report covers it ("every artifact it produces for another program to load"), and the published fix changes both targets.
- DeepSeek, run 1, edited the static target but left the emitted enum table inheriting from `Object.prototype`. Its summary claimed: "Static and json-module artifacts generated from dangerous names evaluate correctly." The schema-text target still crashes with `TypeError: (ext[obj.extend]||...).push is not a function` (audit).
- DeepSeek, run 2, summarised: "CLI artifacts: static/json/proto target lookups and option handling isolate names". The emitted enum table still returned `[Function: toString]` as an enum value (grader log).
- MiMo, run 2, never edited any file under `cli/`, yet ended with: "The fix is complete across every input surface".
- MiMo, run 3, fixed the static target ("`static` mirrors the runtime with `valuesById = Object.create(null)`") but never touched the schema-text target.

### 4.2 The dotted setting with an unsafe last segment (4 of 6)

`setOption("features.__proto__", {...})` and the matching schema option must not replace the `features` container's prototype. The rest of the setting must still be recorded. The models closed the prototype write by dropping the whole setting, so the container was never created:
- DeepSeek, run 3: "Unsafe path segments (`__proto__`, `prototype`, `constructor`) are ignored without partial writes."
- DeepSeek, run 2: "`setProperty` refuses unsafe path segments".
- MiMo, run 3: "intermediate unsafe parts refused without creating containers; last-segment `__proto__` ignored (no error, no write)".

In all three the grader reported "feature settings were not recorded". The report's clause asks that such a name be "ignored ... and the rest of that work is carried out exactly as it would be without that name".

### 4.3 The descriptor importer (MiMo, 3 of 3)

- MiMo, run 1, never edited `ext/` at all. Late in the run it listed "protobuf JSON / textformat / descriptor" among the "remaining surfaces I haven't covered". It did not return to them, and so it also left the advisory's own text-format route open. Its final summary said: "The fix is in the library itself and covers every surface that can reach the bug".
- MiMo, run 2, made the importer's lookup tables null-prototype (T8, T9 pass), but an imported enum value named `__proto__` still replaced the value-options table's prototype (T6).
- MiMo, run 3, fixed T6 and T8, but the group-name lookup (T9) still marked a nested type as a group from an inherited property.

### 4.4 Plain-object conversion (MiMo, 2 of 3)

The generated `fromObject` converter reads each field from the caller's object, so an absent field is read from that object's prototype. This route is open at the pinned commit and also after the published fix. MiMo runs 1 and 3 left it open; run 3 never edited the converter. The grader reported "absent field was materialised as data".

### 4.5 A shadowing option set with fill-if-absent (DeepSeek, run 3)

The test sets options named `toString` and `constructor` with fill-if-absent and expects both stored. DeepSeek run 3 stored `toString` but kept refusing `constructor` on this path ("`setOption` uses own-presence for `ifNotSet` and still refuses unsafe names there"). The grader reported "shadowing option was not stored".

### 4.6 What they got right

Every attempt made option reads, enum tables and default merging own-property-exact, and kept every legitimate behaviour (23/23 functional, including the project's own area tests). 5 of 6 closed the advisory's own route. The failures are coverage failures: routes in other files and tools (generators, importer, converter), and one coupled contract (ignore the name, keep the setting).

### 4.7 Model profiles on this task

- **DeepSeek V4.1 Flash:** fast (32–56 minutes) and broad. It edited 22 to 28 library files per attempt, left 2 or 3 routes open each time, and stated the edge-case choices that cost it (dropping the whole unsafe setting, refusing `constructor`).
- **MiMo-V2.6-Pro:** slower (62–178 minutes) and more variable (16 to 31 of 34). Two attempts declared complete coverage of every surface while whole directories (`ext/` in run 1, `cli/` in run 2) were untouched.

## 5. Evaluation setup

- Harness: Harbor with the Claude Code agent.
- Models: DeepSeek V4.1 Flash (reasoning effort max) and MiMo-V2.6-Pro (provider default effort). Each had 3 counted attempts, with early exit on a solve; neither solved, so all 3 count for both.
- Offline: the agent could reach only the two model APIs, and web tools were disabled. The repository has no upstream git history. The hidden tests are copied in only after the agent stops.
- Time limit: 3 hours per attempt (1.5 times the task's 2-hour setting). No attempt reached it; the longest took 178 minutes.
- Every counted attempt was audited before it counted, by an independent reviewer (Claude Opus 5.5, high effort). It checked:
  - no hidden-test access, no lookups, no reference to the advisory;
  - grading started after the agent stopped, with no tool calls during grading;
  - each failing test reflects a route the model left open that a correct fix would close.
- What counts: a timeout counts as a failure; an attempt cut off by a provider or network outage is not counted. Earlier attempts on a previous version of the task are not counted.

## 6. Questions you may ask

**Is the failure the model's fault and not the task's?** The reference fix, an alternative fix and a hardening fix each score 1.0. One wrong-fix patch per route shows that each route's tests fail exactly when that route is left open. Fairness reviews checked every test against the report, and a human review confirmed the two borderline points. After each attempt, an independent audit read the transcript and results and judged all six genuine model failures.

**Does it hinge on one test?** No. Every attempt left at least two independent routes open: DeepSeek T7+T10, T7+S2, T4+S2; MiMo nine routes, T6+T7+T10, T9+R2+T10+S2. Discounting any one route's tests leaves all 6 attempts below 1.0.

**Could the model have seen the answer?** The agent had no internet access beyond the model APIs and no access to the hidden tests. The audit checked every transcript for test reads and advisory lookups and found none. Two of the routes (R1, R2) are open in the published fix as well, and two (S1, S2) exist only in this task, so copying the upstream fix would not be enough.

**What does a 0.91 or a 0.47 mean?**
- 0.91 means 31 of 34 security tests passed with nothing broken: in practice two routes left open.
- 0.47 means 16 of 34 passed: most routes outside the core runtime were left open.
- A 0.0 would mean a legitimate behaviour was broken; no attempt scored 0.0.

## Appendix: what is in the task package

| What | Contents |
|---|---|
| Task (`tasks/protobufjs-prototype-pollution/`) | `instruction.md`; `task.toml`; `environment/` (pinned commit, the sibling patch, dependencies); `solution/` (reference fix); `tests/` (34 security and 23 functional tests, harness, scorer, grader image) |
| Validation (internal) | gate reports, 19 patch checks (15 single-route misses, 2 over-broad fixes, a hardening fix and an alternative fix), fairness reviews, human review |
| Attempts (internal) | per attempt: score, per-test results, transcript and the audit's verdict |

- **Internal slug:** `protobuf.js-ds`.
- **Counted runs:** `protobuf.js-ds-deepseek-r1-20261020-074647-n001`, `-r2-20261020-081907-n002`, `-r3-20261020-091514-n003`; `protobuf.js-ds-mimo-r1-20261020-094807-n004`, `-r2-20261020-124638-n005`, `-r3-20261020-134834-n006`.
- **Sources used:**
  - the delivered task and its `RESULTS.md` section;
  - the build record (`manifest.json`, `notes.md`, `FAIRNESS.md`, `FAIRNESS.md.preFix`, `HUMAN-REVIEW.md`, `gate_report*.json`, `recover.log`, `upgrade-gate.log`, `trial_detail.json`, `runs_*.log`);
  - for each counted run: `result.json`, `config.json`, `verifier/results.json`, `verifier/security.log`, `agent/trajectory.json` and `postmortem-*/POSTMORTEM.json`.
