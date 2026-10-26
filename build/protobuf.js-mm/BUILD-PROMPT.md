# Build one security-fix benchmark task (build-v1)

## What this is
We build a security-fix benchmark from published, already-fixed advisories in open-source projects.
You build ONE task, from the advisory below.

The task pins the project at the commit just before the published fix and gives a solver agent that
code plus a short problem report (`instruction.md`). Hidden behavioural tests then score the
solver's fix. The tests check that the flaw is closed, using harmless inputs and markers, and that
legitimate use still works.

Everything stays on this machine. Describe each mechanism in one line in notes and reports; the
tests hold the detail, so never write exploitation steps out in prose. Stay inside this advisory's
own protection, in this repository, at the pinned commit. Note anything outside that scope in one
line in your report, and do not build on it.

Project root: `/home/mara/cwe-bench`. Task: `protobuf.js-mm`. Pattern: `A`. Track: `injected`.

## Goal and acceptance
- **The bar.** Two target models (DeepSeek V4.1 Flash, MiMo-V2.6-Pro) must each fail all 3
  finished attempts because of their own judgement.
- **Fairness.** Everything the tests require must be findable from `instruction.md` plus the code,
  or be standard expert knowledge. A careful engineer who knows where to look fixes it in about
  45 minutes.
- **What never counts as a failure:** timeouts, and runs cut by API or network errors.
- **Proof.** A task is built only when the gate passes. A task that misses the bar is reported as
  such, never shipped weaker.

## Inputs
- Advisory: ["GHSA-JFJ6-75FJ-8934", "CVE-2026-59876"]; protobufjs/protobuf.js; prototype pollution / inherited-property confusion (CWE-1321): object mutation of a returned map's prototype via __proto__ key, plus inherited-property reads
- Pinned (vulnerable) commit: parent of 9f97fe413072d3beb52c74e62d88ea8adc9444d8 (parent_commit not given in candidate). Published fix: 9f97fe413072d3beb52c74e62d88ea8adc9444d8.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "12183",
 "advisory_ids": [
  "GHSA-JFJ6-75FJ-8934",
  "CVE-2026-59876"
 ],
 "repo": "protobufjs/protobuf.js",
 "pinned_commit": "parent of 9f97fe413072d3beb52c74e62d88ea8adc9444d8 (parent_commit not given in candidate)",
 "fix_commits": [
  "9f97fe413072d3beb52c74e62d88ea8adc9444d8"
 ],
 "trust_decision": {
  "summary": "Whether a name taken from untrusted input (text-format map key, field name, enum identifier, option name) is treated as an own data property rather than reaching or reading the object's prototype; decided where textformat writes map entries/fields and where reflection tables are looked up by name.",
  "evidence": [
   "ext/textformat.js:664",
   "ext/textformat.js:640",
   "ext/textformat.js:652",
   "ext/textformat.js:466-468",
   "ext/textformat.js:760",
   "src/enum.js:41"
  ]
 },
 "landing_point": {
  "where": "ext/textformat.js:664",
  "why": "Summary names Text Format string map parsing; addMapEntry assigns map[mapKey(...)] = value with no __proto__ guard, unlike decoder/converter/protojson."
 },
 "fix_sites": [
  {
   "where": "ext/textformat.js:664",
   "entry_point": "textformat.fromText / Type#fromText (map entry write)",
   "module_kind": "primary parser (landing)"
  },
  {
   "where": "ext/textformat.js:466-478",
   "entry_point": "textformat.fromText / Type#fromText (map field container, single and [list] forms)",
   "module_kind": "primary parser"
  },
  {
   "where": "ext/textformat.js:640",
   "entry_point": "textformat.fromText (repeated field named like an Object.prototype member)",
   "module_kind": "primary parser"
  },
  {
   "where": "ext/textformat.js:652",
   "entry_point": "textformat.fromText (singular field write)",
   "module_kind": "primary parser"
  },
  {
   "where": "src/enum.js:41",
   "entry_point": "new protobuf.Enum / Enum#add / Enum.fromJSON; read by textformat parseEnum at ext/textformat.js:760",
   "module_kind": "lower-level reflection API (schema object)"
  },
  {
   "where": "src/object.js:272-275",
   "entry_point": "ReflectionObject#getOption",
   "module_kind": "lower-level reflection API"
  },
  {
   "where": "src/object.js:292-294",
   "entry_point": "ReflectionObject#setOption(name, value, ifNotSet)",
   "module_kind": "lower-level reflection API"
  },
  {
   "where": "src/parse.js:822",
   "entry_point": "protobuf.parse (.proto option aggregate value)",
   "module_kind": "second parser (.proto syntax)"
  },
  {
   "where": "src/util/minimal.js:285",
   "entry_point": "util.merge(dst, src, ifNotSet)",
   "module_kind": "defaults/merge helper"
  },
  {
   "where": "ext/descriptor.js:254",
   "entry_point": "Type.fromDescriptor / Root.fromDescriptor (map entry lookup)",
   "module_kind": "second implementation (descriptor import)"
  },
  {
   "where": "ext/descriptor.js:704-707",
   "entry_point": "Enum.fromDescriptor (value named __proto__)",
   "module_kind": "second implementation (descriptor import)"
  },
  {
   "where": "ext/descriptor.js:1009",
   "entry_point": "Root.fromDescriptor / Type.fromDescriptor (group type names)",
   "module_kind": "second implementation (descriptor import)"
  },
  {
   "where": "cli/targets/static.js:1106",
   "entry_point": "pbjs -t static / static-module (generated enum valuesById)",
   "module_kind": "code generator (wrapper)"
  },
  {
   "where": "cli/targets/proto.js:280",
   "entry_point": "pbjs -t proto2/proto3 (consolidateExtends)",
   "module_kind": "code generator (wrapper)"
  }
 ],
 "O1_entry_points": 7,
 "O2_out_of_scope_site": {
  "kind": "lower_level_api",
  "where": "src/enum.js:41 (valuesById = {} makes Enum#values inherit Object.prototype; textformat parseEnum reads values[token.value] at ext/textformat.js:760); also ext/descriptor.js:254,704,1009 (second_implementation) and src/util/minimal.js:285 (defaults_or_merge_route)"
 },
 "O3_reason_to_dismiss": "The report is about text-format map keys; the Enum constructor, descriptor import, util.merge and the CLI generators are core/other modules that never parse text format, so a solver can call them out of scope.",
 "O4_distance": {
  "files": 7,
  "packages": 1,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "A \"__proto__\" map key must remain a stored, enumerable own key with its value reachable, and the returned map must keep Object.prototype as its prototype. Fields named toString/hasOwnProperty must still parse, and enum values/options named constructor/toString must stay settable. Fixes that drop or reject the key, or return a null-prototype map, break these.",
  "where": "fix.diff:318-323, fix.diff:332-333, fix.diff:253-255, fix.diff:279-283"
 },
 "O6_input_shapes": [
  "map entry with brace delimiter: labels { key: \"__proto__\" value {...} }",
  "map entry with angle delimiter <...> (ext/textformat.js:490)",
  "map list form labels: [ {...}, {...} ] (ext/textformat.js:469-475)",
  "map entry missing key (defaults to \"\") (ext/textformat.js:658-660)",
  "repeated field whose name shadows Object.prototype (to_string -> toString)",
  "map field whose name shadows Object.prototype (has_own_property)",
  "enum identifier equal to an inherited property (e: constructor)",
  "descriptor enum value named __proto__",
  "option name shadowing Object.prototype with ifNotSet",
  "parsed .proto option aggregate member named constructor / to_string",
  "util.merge ifNotSet with inherited key"
 ],
 "O7_producer": {
  "kind": "schema",
  "where": "src/enum.js:41-47 (Enum builds valuesById/values used by textformat parseEnum at ext/textformat.js:760); note parseText builds the message with type.create at ext/textformat.js:61, so the map-key guard in Type.fromObject (src/converter.js:135-136) never runs on text-format output",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "util.setProperty reads dst[part] without an own-property check, so a dotted parsed-option or features path segment like toString picks up the inherited function and concatenates it into the stored value",
   "where": "src/util.js:230-236",
   "reason_to_dismiss": "Reached via .proto option parsing (src/object.js:324,328 from src/parse.js:771) and features.* options, not text format; already guards __proto__/constructor/prototype at src/util.js:227 so it looks done",
   "distance": "different file and layer (src/util.js) from ext/textformat.js landing",
   "present_in_latest": "yes",
   "latest_where": "latest/src/util.js:230"
  }
 ],
 "O8b_injection_room": [
  {
   "where": "ext/protojson.js:278",
   "sibling": "ProtoJSON map read building the map with {} instead of Object.create(null)",
   "why_realistic": "The converter builds maps with {} plus a makeProp guard (src/converter.js:132-136); a maintainer aligning protojson with that style could drop the guard and leave the same flaw."
  },
  {
   "where": "ext/textformat.js:454-463",
   "sibling": "parseAny writing type_url/value via a plain object[name] assignment that bypasses setField",
   "why_realistic": "parseAny already calls addField. A refactor or a merge-into-existing-message variant could easily write directly, as parseMapField did before the fix."
  },
  {
   "where": "src/decoder.js:103-104",
   "sibling": "a key-type branch (e.g. a string-like key path added alongside long keys) without the k===\"__proto__\" makeProp guard",
   "why_realistic": "The guard is only emitted in the keyType===\"string\" branch (src/decoder.js:106-108), so a new branch would be written without it."
  }
 ],
 "O9_family": "prototype pollution / inherited-property confusion (CWE-1321): object mutation of a returned map's prototype via __proto__ key, plus inherited-property reads",
 "O9_dos": false,
 "O10_build": {
  "language": "JavaScript (Node.js)",
  "toolchain": "npm; tape test runner (package.json:43); gulp only for bundles",
  "services": [],
  "offline_after_build": true,
  "project_tests": "tests/api_textformat.js, tests/api_enum.js, tests/api_object.js, tests/api_descriptor.js, tests/api_util.js via npm run test:sources"
 },
 "O11_fix_minutes": 50,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "A",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "ext/textformat.js, ext/descriptor.js, src/enum.js, src/object.js, src/parse.js, src/util/minimal.js, cli/targets/static.js, cli/targets/proto.js",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 0,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Add `if (key === \"__proto__\") continue/throw` or return Object.create(null) in addMapEntry/parseMapField. This loses the key or changes the map's prototype, and leaves field-name and enum-name inherited lookups open."
 },
 "out_of_scope_notes": [
  "Namespace/Type lookups by name (src/type.js:379, src/namespace.js:243) use plain {} tables; not pursued."
 ],
 "unverified": [
  "Exact pinned commit hash not provided (parent_commit null); assumed the tree at hosts/12183/repo is the fix parent.",
  "Repo size in MB not measured (no shell); tiny_repo/giant_repo not evaluated. protobuf.js with tests/data is likely well over 5 MB, but this was not checked.",
  "O4 packages=1 assumes cli/ and ext/ count as the same npm package as src/.",
  "O1 counts fromText, parse, Enum ctor/add/fromJSON, getOption/setOption, util.merge, descriptor fromDescriptor, pbjs CLI as 7 distinct entry points.",
  "Whether util.setProperty inherited read (O8) is observable through public API was reasoned from code only, not executed.",
  "Advisory text itself not available locally; trust decision is derived from the summary and fix diff."
 ]
}
  ```
- Published fix sites:   - ext/textformat.js:664 — entry point: textformat.fromText / Type#fromText (map entry write) [primary parser (landing)]
  - ext/textformat.js:466-478 — entry point: textformat.fromText / Type#fromText (map field container, single and [list] forms) [primary parser]
  - ext/textformat.js:640 — entry point: textformat.fromText (repeated field named like an Object.prototype member) [primary parser]
  - ext/textformat.js:652 — entry point: textformat.fromText (singular field write) [primary parser]
  - src/enum.js:41 — entry point: new protobuf.Enum / Enum#add / Enum.fromJSON; read by textformat parseEnum at ext/textformat.js:760 [lower-level reflection API (schema object)]
  - src/object.js:272-275 — entry point: ReflectionObject#getOption [lower-level reflection API]
  - src/object.js:292-294 — entry point: ReflectionObject#setOption(name, value, ifNotSet) [lower-level reflection API]
  - src/parse.js:822 — entry point: protobuf.parse (.proto option aggregate value) [second parser (.proto syntax)]
  - src/util/minimal.js:285 — entry point: util.merge(dst, src, ifNotSet) [defaults/merge helper]
  - ext/descriptor.js:254 — entry point: Type.fromDescriptor / Root.fromDescriptor (map entry lookup) [second implementation (descriptor import)]
  - ext/descriptor.js:704-707 — entry point: Enum.fromDescriptor (value named __proto__) [second implementation (descriptor import)]
  - ext/descriptor.js:1009 — entry point: Root.fromDescriptor / Type.fromDescriptor (group type names) [second implementation (descriptor import)]
  - cli/targets/static.js:1106 — entry point: pbjs -t static / static-module (generated enum valuesById) [code generator (wrapper)]
  - cli/targets/proto.js:280 — entry point: pbjs -t proto2/proto3 (consolidateExtends) [code generator (wrapper)]
- Uncovered routes to confirm (pattern B): none
- Design plan from the lead: No lead plan is provided for this task — you are the lead as well as the builder. Using the Design section above and the screener record, design the task yourself and WRITE YOUR PLAN in `notes.md` BEFORE you build:
  - choose the main lever and at least one more, each with a DIFFERENT reason a solver would dismiss or skip it;
  - decide the sites, routes and input shapes the security tests will cover;
  - identify the coupled must-keep-working behaviour next to each lever, for the functional tests;
  - for the injected track: decide the realistic sibling gap(s) to add — each must be code a maintainer could plausibly have left, reachable through the real entry point, covered by a stated invariant, and placed where the published fix never touches. Add 2–4 siblings at a recurring trust decision, each with its own reason a solver would skip it;
  - if this candidate cannot support a fair task that meets the bar (flaw does not reproduce at the pinned commit through a real entry point, needs network/GPU/GUI at run time, or no design meets the bar), STOP and report why. Do not ship a weak task.
Follow every rule in the Design, Report, Tests and Proof sections exactly. You choose the design; the rules are fixed.
- Host notes: none

## Design: where difficulty comes from
Models find the code the report leads to and diagnose it correctly. They fail on scope. Build these
in, in order of evidence:
1. **Pattern A: the published fix's far sites.**
   - The report leads to one site. The tests cover every entry point the published fix protects,
     including one in a module that looks out of scope: a second implementation, a lower-level
     public API, a wrapper, a save/reload path, or a defaults or merge route.
   - Give it a plausible **reason to dismiss**, and **distance**: another file or package from the
     landing point.
2. **Pattern B: uncovered routes.**
   - Routes into the same protected sink where the advisory's own protection is missing at the
     pinned commit, and which the published fix did not touch.
   - They are unmodified upstream code, so a solver can argue they were never covered.
   - The strongest lever found so far: DeepSeek 6 of 6 on one; both models 0 of 3 on three combined.
3. **Input-shape variants** that the general rule covers but a one-case fix misses (a plain string
   and an array).
4. **A coupled must-keep-working behaviour** next to the sink, tested functionally, so an
   over-broad fix fails. MiMo tends to over-harden.
5. **Producer off the check's path.** The check depends on data produced elsewhere (a schema,
   serializer, cache, mapper or config loader) and does not call it. It counts only if the producer
   is infrastructure, not a request handler.
6. **Injected siblings**, only where the plan asks for them. Each must be:
   - code a maintainer could have written, with no deceptive names or comments;
   - reachable through the real entry point;
   - covered by a stated invariant;
   - placed where the upstream fix never touches.

Aim for at least two levers with **different** reasons to dismiss.

Never add:
- encoding, verb, protocol or role/direction variants;
- more routes of one concept;
- resource-exhaustion traps.

Every lever must be findable by a blind engineer from the report and the code. A lever that a blind
fix cannot find is unfair: remove it.

**Pattern B rules:**
- Confirm each route with a behavioural test on the pinned copy before relying on it. The
  screener's claim is only a lead.
- Append one row per route to `/home/mara/cwe-bench/build/audit/uncovered-routes.tsv`, using its existing
  header. Columns:
  - `task`, `repo`, `advisory`;
  - `trap_ref` (the manifest trap id only; no mechanism text, since the manifest holds the detail);
  - `real_upstream`;
  - `present_in_latest` (`yes`, `no` or `unknown`, from a read-only look at current upstream code if
    you can reach it);
  - `public_upstream_report`, `in_current_scope`, `built`, `note`;
  - `disclosure_status` (`pending client decision`).

## Environment (`tasks/protobuf.js-mm/environment/Dockerfile`)
- **Base and code.** A small official base image. The repo goes into `/app` at the pinned commit,
  and `/app/.git` is then deleted.
- **Offline.** Install every dependency, tool and service the project and tests need; nothing may
  be downloaded at test time. Services start from `test.sh`.
- **Packages:** `patch`, `curl`, `ca-certificates`, `bash`, `git`.
- **Agent layer.** Append `harness/claude-code.Dockerfile.snippet` unchanged at the end.
- **No test code in the image.** The agent shares the container. Pre-build against stubs; `test.sh`
  copies the real tests in at grading time.
- **Project tests.** The project's own tests for the affected area must pass in the image at the
  pinned commit.
- **No leaked regression tests.** The pinned commit must not already contain the advisory's
  regression tests (check `git log` between the pinned and fix commits).

## Report to the solver (`tasks/protobuf.js-mm/instruction.md`)
**Write:**
- what the system is, at product level;
- one observed impact, with ONE concrete trigger at user level (HTTP request, CLI call or public API
  use);
- the security properties as **invariants**: who may do what to which data, or what attacker input
  must never achieve. Word each so it covers every tested route and shape ("no value of X may …").
  If there are several, give one natural list, never a count;
- every **contract** the tests need:
  - the refusal form ("a client error with no side effect");
  - any interface or field name a test uses;
  - preservation clauses ("works exactly as today");
  - a legitimate magnitude next to any attack magnitude;
- that examples are examples, not the full set;
- the standard constraints block: fix the problem and its close variants; keep legitimate use
  working; do not modify or add tests; do not look up the upstream fix; do not special-case the
  example.

**Never write:**
- file, package, function, class, field or parameter names a user would not see;
- line numbers, the root cause, the fix approach, or a CVE or GHSA id;
- a list of routes, spellings or roles;
- restricting adverbs ("directly", "only via");
- anything that names or paraphrases a far site, an uncovered route or an injected sibling.

Put every identifier that must not appear in `manifest.leak_terms`.

## Tests (`tasks/protobuf.js-mm/tests/`)
- **`security/`:** one test per site, route, input shape and form. Each one:
  - goes through the real entry point;
  - fails on the pinned code and passes on a correct fix;
  - asserts the attack is blocked: any client error plus no side effect, never one exact status.
- **`functional/`:**
  - legitimate use, including the coupled behaviour of every lever;
  - where they exist, the project's own tests for the area.
- **No product code in a test's bookkeeping.** Compute expected values and clean-ups in the test
  itself, because a hardened helper must not crash a test.
- **Stubs** of permission or authority answer per resource and verb, like the real thing.
- **Scope.** A test may vary only what the instruction names, and drive only the entry point it
  names.
- **No network**, and nothing that depends on the fix commit being present.
- **Templates.** JUnit XML into the two directories the template names. Copy `score.py` unchanged.
  Edit only the marked command lines of `test.sh`, and keep its agent-kill block.

## Proof
- **The oracle.** `solution/fix.patch` is the published fix reduced to source changes, plus fixes
  for every uncovered route and injected sibling in the task. `solution/solve.sh` applies it to
  `/app`.
- **Wrong-fix patches** go in `build/protobuf.js-mm/checks/`, listed in `manifest.patch_checks`:
  - one `security_fail` per lever (the fix that misses only that lever);
  - a `functional_fail` (an over-broad or feature-removing fix);
  - a `pass` of kind `hardening` (the oracle plus defensive hardening of the product code the
    security tests import);
  - a `pass` alternative fix where a second valid design is plausible.
- **`manifest.wrong_fix_catalogue`:** for each class, a `checks/` patch, or `n/a: <why>`:
  `refuse_all`, `crash_as_refusal`, `wrong_resource`, `one_role_or_direction`, `reads_only`,
  `check_after_adjustment`, `unlisted_route`, `malformed_identity`, `missing_authority`,
  `adjacent_api`.

## Deliverables
**`tasks/protobuf.js-mm/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/protobuf.js-mm/manifest.json`:**
- `slug`, `candidate`;
- `pattern`: `A`;
- `builder_prompt_version`: `build-v1`;
- `"strict_gate": true`;
- `verified`: entry point, sites, routes, services, project tests run;
- `leak_terms`, `patch_checks`, `wrong_fix_catalogue`;
- `traps`: one entry per lever, with `shape`, `where` (file:line), `security_tests`,
  `coupled_functional_tests`, `security_fail_patch`, and `realistic_because` (for pattern B: "real,
  unmodified upstream code");
- `status`.

**Also in `build/protobuf.js-mm/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py protobuf.js-mm --only static
python3 -I builder/gate.py protobuf.js-mm --only nop
python3 -I builder/gate.py protobuf.js-mm --only oracle
python3 -I builder/gate.py protobuf.js-mm --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/protobuf.js-mm/`;
  - edit only `tasks/protobuf.js-mm/`, `build/protobuf.js-mm/` and, for pattern B, the register;
  - do not commit.

## Stop and report instead of shipping when
- the flaw does not reproduce through a real entry point at the pinned commit;
- a planned route or site is not reachable, or the check calls the producer directly (substitute
  another lever the code supports if you can, and say so);
- the task needs network at run time, or a GPU, kernel or GUI;
- the tests are flaky;
- no design meets the bar.

## Report back (under 400 words)
- The gate result for each stage.
- Each lever in one line: pattern, shape, file:line, reason to dismiss.
- Pattern B: each register row.
- The instruction's word count.
- Every guess you could not verify.
- Any fairness concern you see yourself.
- Anything noticed outside the scope, in one line.
- If abandoned, exactly why.
