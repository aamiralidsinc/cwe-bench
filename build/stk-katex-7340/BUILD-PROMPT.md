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

Project root: `/home/mara/cwe-bench`. Task: `stk-katex-7340`. Pattern: `A+B`. Track: `stacked`.

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
- Advisory: 7340; CWE-807 reliance on an untrusted input in a security decision, reached
- Pinned (vulnerable) commit: 5a5bf2060431aaed5eb3b549f6fab24f55e9e70a. Published fix: 0adf7e77db6915d991803b29699f82b1ccf8d4f4.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "candidate_id": "h4-7340",
 "pattern": "H4",
 "repo": "katex/katex",
 "pinned_commit": "5a5bf2060431aaed5eb3b549f6fab24f55e9e70a",
 "protections": [
  "P1: a setting value, including the trust decision input, is taken from the caller's own options entry for that key, with the schema default used only when the option is absent or explicitly undefined (src/Settings.ts:336-348, src/Settings.ts:328-334).",
  "P2: isTrusted supplies a protocol derived from the context URL whenever the context does not already carry one, so a caller's trust function is handed a protocol KaTeX computed (src/Settings.ts:464-476, src/utils.ts:69-89).",
  "P3: macro names resolve only from own properties of the per-render macro map and of the builtin macro map (src/Namespace.ts:68-71, src/Namespace.ts:81-87, src/Namespace.ts:96-122).",
  "P4: CLI flag name, description, processor and default are taken from the schema entry that describes that flag (cli.js:26-31).",
  "P5: auto-render resolves its render options locally before calling katex.render (contrib/auto-render/auto-render.ts:130-161)."
 ],
 "traps": [
  {
   "id": "T1",
   "mechanism": "M5",
   "origin": "advisory_route",
   "locations": [
    "src/Settings.ts:342-347"
   ],
   "reason_to_dismiss": "",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "weak",
   "tier_deepseek": "easy",
   "tier_mimo": "easy",
   "type": "neither",
   "evidence": [
    "src/Settings.ts:342",
    "src/Settings.ts:343",
    "src/Settings.ts:379-385",
    "src/Settings.ts:268-272",
    "src/functions/href.ts:21-26",
    "src/functions/includegraphics.ts:86-91"
   ]
  },
  {
   "id": "T2",
   "mechanism": "M5",
   "origin": "advisory_route",
   "locations": [
    "src/Settings.ts:328-334",
    "src/Settings.ts:344-345"
   ],
   "reason_to_dismiss": "SETTINGS_SCHEMA is a module constant written in this same file, not caller input, so its entries are assumed not to be attacker-shaped; schema.default is present on only some entries and schema.processor on only three numeric ones, so both reads look like static bookkeeping rather than a decision path.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "weak",
   "tier_deepseek": "hard",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "src/Settings.ts:329",
    "src/Settings.ts:344",
    "src/Settings.ts:197-297",
    "src/Settings.ts:268-272",
    "src/Settings.ts:343",
    "src/Settings.ts:379-385"
   ]
  },
  {
   "id": "T3",
   "mechanism": "M8",
   "origin": "uncovered_upstream",
   "locations": [
    "src/Settings.ts:465-471"
   ],
   "reason_to_dismiss": "isTrusted is the check itself: it already derives the protocol and looks correct, and the reported shape is a polluted settings value, not a polluted context object, so there is nothing here a solver expects to change.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "bypassed",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "both",
   "evidence": [
    "src/Settings.ts:465",
    "src/Settings.ts:466-470",
    "src/Settings.ts:472-475",
    "src/utils.ts:69-89",
    "docs/options.md:50",
    "test/katex-spec.ts:3407-3413"
   ]
  },
  {
   "id": "T4",
   "mechanism": "M2",
   "origin": "published_fix_far_site",
   "locations": [
    "src/Namespace.ts:81-87"
   ],
   "reason_to_dismiss": "Namespace is the macro/undo-stack class, has no trust decision of its own, and already calls hasOwnProperty on current (and has() checks both maps), so it reads as a separate, already-guarded concern from the settings bug.",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "weak",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "src/Namespace.ts:85",
    "src/Namespace.ts:68-71",
    "src/Namespace.ts:22-27",
    "src/MacroExpander.ts:405-418",
    "src/MacroExpander.ts:42"
   ]
  },
  {
   "id": "T5",
   "mechanism": "M4",
   "origin": "published_fix_far_site",
   "locations": [
    "src/Namespace.ts:112-115"
   ],
   "reason_to_dismiss": "set() only records the previous value so the group can restore it; the value the caller asked to define is what gets written, so this reads as undo bookkeeping rather than a lookup that needs an own-property check.",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "src/Namespace.ts:113",
    "src/Namespace.ts:114",
    "src/Namespace.ts:44-51",
    "src/Namespace.ts:117-121",
    "src/Parser.ts:120-132"
   ]
  },
  {
   "id": "T6",
   "mechanism": "M6",
   "origin": "uncovered_upstream",
   "locations": [
    "cli.js:26-31"
   ],
   "reason_to_dismiss": "cli.js is a Node convenience binary outside src/, reached only through the katex bin, and prototype pollution in a short-lived CLI process looks unreachable; the advisory describes the library rendering path.",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "xhard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "cli.js:27",
    "cli.js:28-29",
    "cli.js:93",
    "cli.js:109",
    "cli.js:11",
    "package.json:138"
   ]
  },
  {
   "id": "T7",
   "mechanism": "M5",
   "origin": "uncovered_upstream",
   "locations": [
    "contrib/auto-render/auto-render.ts:130-161"
   ],
   "reason_to_dismiss": "auto-render is a separate contrib package entry that only decides which macros and delimiters apply, not trust itself, so it reads as a neighbouring convenience feature outside the advisory's settings path.",
   "distance": {
    "files": 1,
    "packages": 1
   },
   "protection_state": "weak",
   "tier_deepseek": "hard",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "contrib/auto-render/auto-render.ts:132",
    "contrib/auto-render/auto-render.ts:135",
    "contrib/auto-render/auto-render.ts:154-155",
    "contrib/auto-render/auto-render.ts:159",
    "contrib/auto-render/auto-render.ts:57",
    "package.json:183-185"
   ]
  },
  {
   "id": "T8",
   "mechanism": "M11",
   "origin": "advisory_route",
   "locations": [
    "src/Settings.ts:342-343",
    "src/Settings.ts:261-272",
    "src/Settings.ts:472-475"
   ],
   "reason_to_dismiss": "trust and strict are already accepted as functions (and strict as 'warn'/'ignore'/'error'), and an explicitly undefined own value already falls back to the default, so an own-property read is assumed to be value-agnostic and safe to bolt on.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "weak",
   "tier_deepseek": "medium",
   "tier_mimo": "hard",
   "type": "mimo",
   "evidence": [
    "src/Settings.ts:261-272",
    "src/Settings.ts:343",
    "src/Settings.ts:472-475",
    "test/katex-spec.ts:3407-3437",
    "test/katex-spec.ts:4594-4608",
    "test/helpers.ts:79",
    "docs/options.md:62-70"
   ]
  }
 ],
 "independent_groups": [
  [
   "T1",
   "T8"
  ],
  [
   "T2"
  ],
  [
   "T3"
  ],
  [
   "T4"
  ],
  [
   "T5"
  ],
  [
   "T6"
  ],
  [
   "T7"
  ]
 ],
 "history": {
  "a_fix_leaves_b_open": null,
  "b_in_code_a_wrote": null,
  "masking": [
   "T4 masks T5: while get() still falls through to this.builtins[name] (src/Namespace.ts:85) an inherited macro name already resolves, so the undo capture at src/Namespace.ts:114 makes no visible difference; once get() is own-property-only, set()/endGroup is the remaining way an inherited name becomes an own definition in this.current.",
   "T1 masks T2 in the reported shape: with Object.prototype.trust polluted, the report's new Settings() example is decided at src/Settings.ts:342 and the schema-default read at src/Settings.ts:329 gives no distinguishable result; T2 only shows when the polluted key is default or processor and the options carry no own value.",
   "T1/T2 mask T3 for trust:true callers: when trust is polluted to true every command is allowed anyway, so the forged protocol only matters in the function-valued trust configuration the docs describe (docs/options.md:62-70)."
  ],
  "dependency_bump_fix": false,
  "in_repo_fix_possible": true
 },
 "conflicts": [
  {
   "a": "T1",
   "b": "T8",
   "what": "The natural way to make the options read own-property-only (validate against the schema type or coerce with Boolean(optionValue)) is exactly what destroys the documented function-valued trust/strict forms and the own-undefined fallback that src/Settings.ts:343 currently provides, so the fix for T1 must stay value-agnostic."
  },
  {
   "a": "T4",
   "b": "T5",
   "what": "The natural fix for T4 (replace or copy the caller's macro map with a null-prototype object so inherited names cannot resolve) breaks the behaviour T5's undo machinery exists to provide: rendering writes \\def/\\gdef definitions back into the caller's own macros object (docs/options.md:18-25, test/katex-spec.ts:3971-3989), which requires this.current to stay the caller's object (src/Namespace.ts:24)."
  }
 ],
 "fairness_risks": [
  "trust may be a function and is invoked as this.trust(context) (src/Settings.ts:472-475; docs/options.md:62-70; test/katex-spec.ts:3407-3437): a rule requiring a boolean trust, or coercing with Boolean(), turns a documented allowlist function into unconditional trust.",
  "strict may be a function or 'warn'/'ignore'/'error' (src/Settings.ts:261-267; test/katex-spec.ts:4594-4608): the same coercion or type validation breaks it.",
  "An own property explicitly set to undefined must still fall back to the schema default (src/Settings.ts:343); replacing the '!== undefined' test with hasOwnProperty alone changes throwOnError and maxExpand defaults (the latter removes the expansion limit).",
  "options may legitimately be another Settings instance (test/helpers.ts:79 passes a Settings into katex.__renderToDomTree; test/katex-spec.ts:4590 constructs new Settings(nonstrictSettings)), so a fix that requires a plain object or rejects non-literal options breaks the existing harness.",
  "The macros object is documented as mutated and shared between render calls (docs/options.md:18-25, docs/options.md:72-88; src/Namespace.ts:22-27), and macro values may be functions (docs/options.md:23): a Namespace rewrite that copies/freezes the map or type-checks values breaks globalGroup and function macros.",
  "\\htmlClass/\\htmlId/\\htmlStyle/\\htmlData contexts carry no url or protocol (src/functions/html.ts:30-86; docs/options.md:58-60) and existing tests distinguish 'protocol' in context (test/katex-spec.ts:3421-3437), so a T3 fix that always injects a derived protocol changes the documented context shape.",
  "auto-render's other defaults - delimiters, ignoredTags, ignoredClasses, errorCallback (contrib/auto-render/auto-render.ts:135-155) - must keep working if the macros line at 159 is hardened.",
  "An options object whose prototype carries defaults (Object.create({...})) currently works because src/Settings.ts:342 reads through the chain; an own-property rule silently refuses that shape. It is not documented, so refusing it is low risk, but it is a shape a legitimate caller could be using."
 ],
 "effort_minutes": 60,
 "usable": true,
 "design": {
  "traps": [
   "T1",
   "T8",
   "T2",
   "T3",
   "T4",
   "T7"
  ],
  "why": "T1+T8 are one edit site with two distinct failure modes (leave the inherited options read, or over-harden and break function-valued trust/strict and the own-undefined fallback), so they are the anchor. T2 forces the solver off the options object onto the schema entries the constructor consumes (schema.default and schema.processor), with the strong dismissal that SETTINGS_SCHEMA is a file-local constant. T3 moves the decision point itself: isTrusted's protocol derivation is bypassed by an inherited protocol, and it looks like the check rather than a site needing a change. T4 moves to the macro namespace in another file where hasOwnProperty is already visible, which is the strongest reason to dismiss. T7 moves to a second package entry (contrib/auto-render) so a solver who reads and edits only src/Settings.ts fails even with a perfect settings fix. Five independent groups across three source files and two package entries, with deepseek-type traps (T2, T4, T7: weak/absent protection behind a plausible dismissal) and a mimo-type trap (T8: the coupled function/undefined value semantics). T5 is a real sixth group but is masked behind T4 and sits in the same Namespace patch, so it adds little; T6 (cli.js) is real but cannot be exercised by the jest harness without a dist build (cli.js:11 requires the built package, package.json:5, and testMatch is **/test/*-spec.ts at package.json:183-185), so it is recorded but not recommended for hidden tests."
 },
 "unverified": [
  "The fix commit 0adf7e77db6915d991803b29699f82b1ccf8d4f4 could not be read: no shell is available in this session and git objects are not readable as files. The origins marked published_fix_far_site follow the screener's fix_sites list (src/Settings.ts:329-331, 342-346; src/Namespace.ts:82-86, 113-115), not a diff I inspected.",
  "Git history could not be inspected, so a_fix_leaves_b_open and b_in_code_a_wrote are left null. The in-tree asymmetry at src/Namespace.ts:69-70 (has() checks both maps) versus src/Namespace.ts:82-85 (get() checks only current) is consistent with an earlier partial hardening, but no prior fix commit could be confirmed.",
  "Whether an attacker-reachable pollution primitive exists inside KaTeX itself was not investigated; every trap assumes an Object.prototype polluted by another library, as the screener's summary states.",
  "cli.js could not be exercised: it requires the built package at cli.js:11 (package.json main is dist/katex.js, package.json:5) and the pinned tree has no dist; the jest testMatch at package.json:183-185 does not reach it without a build.",
  "commander@8's option(flags, description, processor, defaultValue) argument order and its handling of a default for every flag come from the documented API; node_modules is absent from the pinned tree, so cli.js:28-29 behaviour is inferred, not executed.",
  "Repository size in MB was not measured (no shell).",
  "Prototype-chain reads of symbol and function tables (src/Parser.ts:467, 507, 943, 964, 971; src/buildCommon.ts:41-42, 126, 232; src/buildMathML.ts:33, 124; src/delimiter.ts:52) and the lexer catcode read at src/MacroExpander.ts:414 were considered and left out of the trap list: they can change expansion/rendering behaviour or throw, but do not reach the trust decision recorded here.",
  "The screener's kind set was M11+M2+M4+M5; I recorded M6 for the cli.js schema-metadata route and M8 for the isTrusted protocol shape because those two mechanisms are not covered by the four screener codes. Naming differs; the sites are the ones the screener flagged."
 ]
}
  ```
- Published fix sites:   - src/Settings.ts:342-347 — T1 M5 (reason to dismiss: none)
  - src/Settings.ts:328-334 — T2 M5 (reason to dismiss: SETTINGS_SCHEMA is a module constant written in this same file, not caller input, so its entries are assumed not to be attacker-shaped; schema.default is present on only some entries and schema.processor on only three numeric ones, so both reads look like static bookkeeping rather than a decision path.)
  - src/Settings.ts:344-345 — T2 M5 (reason to dismiss: SETTINGS_SCHEMA is a module constant written in this same file, not caller input, so its entries are assumed not to be attacker-shaped; schema.default is present on only some entries and schema.processor on only three numeric ones, so both reads look like static bookkeeping rather than a decision path.)
  - src/Namespace.ts:81-87 — T4 M2 (reason to dismiss: Namespace is the macro/undo-stack class, has no trust decision of its own, and already calls hasOwnProperty on current (and has() checks both maps), so it reads as a separate, already-guarded concern from the settings bug.)
  - src/Namespace.ts:112-115 — T5 M4 (reason to dismiss: set() only records the previous value so the group can restore it; the value the caller asked to define is what gets written, so this reads as undo bookkeeping rather than a lookup that needs an own-property check.)
  - src/Settings.ts:342-343 — T8 M11 (reason to dismiss: trust and strict are already accepted as functions (and strict as 'warn'/'ignore'/'error'), and an explicitly undefined own value already falls back to the default, so an own-property read is assumed to be value-agnostic and safe to bolt on.)
  - src/Settings.ts:261-272 — T8 M11 (reason to dismiss: trust and strict are already accepted as functions (and strict as 'warn'/'ignore'/'error'), and an explicitly undefined own value already falls back to the default, so an own-property read is assumed to be value-agnostic and safe to bolt on.)
  - src/Settings.ts:472-475 — T8 M11 (reason to dismiss: trust and strict are already accepted as functions (and strict as 'warn'/'ignore'/'error'), and an explicitly undefined own value already falls back to the default, so an own-property read is assumed to be value-agnostic and safe to bolt on.)
- Uncovered routes to confirm (pattern B):   - src/Settings.ts:465-471 — T3 M8 (reason to dismiss: isTrusted is the check itself: it already derives the protocol and looks correct, and the reported shape is a polluted settings value, not a polluted context object, so there is nothing here a solver expects to change.)
  - cli.js:26-31 — T6 M6 (reason to dismiss: cli.js is a Node convenience binary outside src/, reached only through the katex bin, and prototype pollution in a short-lived CLI process looks unreachable; the advisory describes the library rendering path.)
  - contrib/auto-render/auto-render.ts:130-161 — T7 M5 (reason to dismiss: auto-render is a separate contrib package entry that only decides which macros and delimiters apply, not trust itself, so it reads as a neighbouring convenience feature outside the advisory's settings path.)
- Design plan from the lead: TRACK = STACKED (H4). Build the stacked design the reader chose: traps T1, T8, T2, T3, T4, T7. Why: T1+T8 are one edit site with two distinct failure modes (leave the inherited options read, or over-harden and break function-valued trust/strict and the own-undefined fallback), so they are the anchor. T2 forces the solver off the options object onto the schema entries the constructor consumes (schema.default and schema.processor), with the strong dismissal that SETTINGS_SCHEMA is a file-local constant. T3 moves the decision point itself: isTrusted's protocol derivation is bypassed by an inherited protocol, and it looks like the check rather than a site needing a change. T4 moves to the macro namespace in another file where hasOwnProperty is already visible, which is the strongest reason to dismiss. T7 moves to a second package entry (contrib/auto-render) so a solver who reads and edits only src/Settings.ts fails even with a perfect settings fix. Five independent groups across three source files and two package entries, with deepseek-type traps (T2, T4, T7: weak/absent protection behind a plausible dismissal) and a mimo-type trap (T8: the coupled function/undefined value semantics). T5 is a real sixth group but is masked behind T4 and sits in the same Namespace patch, so it adds little; T6 (cli.js) is real but cannot be exercised by the jest harness without a dist build (cli.js:11 requires the built package, package.json:5, and testMatch is **/test/*-spec.ts at package.json:183-185), so it is recorded but not recommended for hidden tests. Follow the stacked-task rules appended at the end of this prompt; they add to the rules above.
- Host notes: Reader fairness risks (resolve each in the report's contracts or the tests): trust may be a function and is invoked as this.trust(context) (src/Settings.ts:472-475; docs/options.md:62-70; test/katex-spec.ts:3407-3437): a rule requiring a boolean trust, or coercing with Boolean(), turns a documented allowlist function into unconditional trust. | strict may be a function or 'warn'/'ignore'/'error' (src/Settings.ts:261-267; test/katex-spec.ts:4594-4608): the same coercion or type validation breaks it. | An own property explicitly set to undefined must still fall back to the schema default (src/Settings.ts:343); replacing the '!== undefined' test with hasOwnProperty alone changes throwOnError and maxExpand defaults (the latter removes the expansion limit). | options may legitimately be another Settings instance (test/helpers.ts:79 passes a Settings into katex.__renderToDomTree; test/katex-spec.ts:4590 constructs new Settings(nonstrictSettings)), so a fix that requires a plain object or rejects non-literal options breaks the existing harness. | The macros object is documented as mutated and shared between render calls (docs/options.md:18-25, docs/options.md:72-88; src/Namespace.ts:22-27), and macro values may be functions (docs/options.md:23): a Namespace rewrite that copies/freezes the map or type-checks values breaks globalGroup and function macros. | \htmlClass/\htmlId/\htmlStyle/\htmlData contexts carry no url or protocol (src/functions/html.ts:30-86; docs/options.md:58-60) and existing tests distinguish 'protocol' in context (test/katex-spec.ts:3421-3437), so a T3 fix that always injects a derived protocol changes the documented context shape. | auto-render's other defaults - delimiters, ignoredTags, ignoredClasses, errorCallback (contrib/auto-render/auto-render.ts:135-155) - must keep working if the macros line at 159 is hardened. | An options object whose prototype carries defaults (Object.create({...})) currently works because src/Settings.ts:342 reads through the chain; an own-property rule silently refuses that shape. It is not documented, so refusing it is low risk, but it is a shape a legitimate caller could be using.. Conflicts the reader found: The natural way to make the options read own-property-only (validate against the schema type or coerce with Boolean(optionValue)) is exactly what destroys the documented function-valued trust/strict forms and the own-undefined fallback that src/Settings.ts:343 currently provides, so the fix for T1 must stay value-agnostic. | The natural fix for T4 (replace or copy the caller's macro map with a null-prototype object so inherited names cannot resolve) breaks the behaviour T5's undo machinery exists to provide: rendering writes \def/\gdef definitions back into the caller's own macros object (docs/options.md:18-25, test/katex-spec.ts:3971-3989), which requires this.current to stay the caller's object (src/Namespace.ts:24).

## Design: where difficulty comes from
Models find the code the report leads to and diagnose it correctly. They fail on scope. Build these
in, in order of evidence:
1. **Pattern A: the published fix's far sites.**
   - The report leads to one site. The tests cover every entry point the published fix protects,
     including one in a module that looks out of scope: a second implementation, a lower-level
     public API, a wrapper, a save/reload path, or a defaults or merge route.
   - Give it a plausible **reason to dismiss**, and **distance**: another file or package from the
     landing point.
   - **A second implementation is the strongest form of this**: separate code doing the same
     guarded operation (a fallback backend, another package, another transport, a legacy version),
     so fixing the reported copy changes nothing in the other. Models fix the copy the example hits,
     re-run the example and stop. Prefer a real one (Pattern A or B) over a planted one. Find
     candidates by searching for the low-level primitive across packages (redirect following,
     header copying, file writes, message construction). It only counts if the report never
     describes it.
2. **Pattern B: uncovered routes.**
   - Routes into the same protected sink where the advisory's own protection is missing at the
     pinned commit, and which the published fix did not touch.
   - They are unmodified upstream code. A solver may argue they were never covered, but the task's
     general property covers them, so leaving one open is a model failure, not out of scope. The
     same holds for a route where the protection never existed: the property requires it.
   - Make sure the property, read literally, really covers each route (no word that excludes it),
     and that its test fails only when the protection is really missing (it must pass a correct
     fix placed at any valid layer).
   - The strongest lever found so far: DeepSeek 6 of 6 on one; both models 0 of 3 on three combined.
3. **Shape traps: an input form that a plausible check mishandles.** Examples: a value given as an
   array where the check only handles a string; a name split on the first separator when it can
   contain the separator; a resolved path against a lexical check; a rename or rewrite that happens
   after the check; a nested expression the check never inspects. Two conditions: the general
   property must cover the form literally, and the form must not fall inside anything a
   must-keep-working clause or a test fixture calls legitimate. A pure spelling, encoding, verb,
   protocol or role variant of a stated input is NOT a shape trap: both models always catch those
   (see "Never add").
4. **A coupled must-keep-working behaviour** next to the sink, tested functionally, so an
   over-broad fix fails. MiMo tends to over-harden.
5. **Producer off the check's path.** The check depends on data produced elsewhere (a schema,
   serializer, cache, mapper, table builder or config loader) and does not call it; the data
   reaches the check on a separate path (saved and reloaded, rebuilt from config). The fix needs
   both the check and the producer. Models trace into what the check calls, never back to where
   its data comes from. Rules:
   - it counts only if the producer is infrastructure, not a request handler;
   - verify that the check does **not** call the producer; if it does, the model follows the call
     and fixes it;
   - the report describes impact only through the check's path and states the property abstractly
     ("including data saved earlier"); it never points at the producer or the reload path;
   - avoid fixes where the check cannot compile without the producer change (that forces the find);
   - hidden tests must not need a field or function name the solver would have to guess;
   - prefer a producer deep in internal machinery (a table or schema builder). One behind a path
     that is easy to follow falls as soon as anything points at it.
6. **Injected siblings**, only where the plan asks for them. Each must be:
   - code a maintainer could have written, with no deceptive names or comments;
   - reachable through the real entry point;
   - covered by the task's general property, never by a sentence of its own;
   - placed where the upstream fix never touches.
7. **Wrong object.** The authorization check exists but decides on a different object than the one
   the request actually touches: a neighbouring or proxy resource (a parent or container instead of
   the item written), or an identity field the caller supplies (an account inside a caller-provided
   resource name; a parent read from one part of the request while the write uses another). Models
   copy the nearby precedent. Rules:
   - the instruction names the protected object class in product terms ("the objects that hold the
     limits"), never the check or its location;
   - the security test denies exactly the object touched while the proxy object stays allowed;
   - a functional test keeps a legitimate request on that same object working.
8. **Ordering.** The check is right but runs at the wrong moment: after an adjustment turns the
   attacker's value into a different bad value (an offset, a clamp, a unit conversion, a
   normalisation), or after a side effect has already happened (a directory created, a file cleared,
   copied or re-permissioned, a request sent) before the refusal. Rules:
   - the instruction states the property over the attacker's input or the outcome ("nothing outside
     the folder is created or changed, even when the request is refused"), never the order of steps;
   - the security test checks the side effect itself, not only the response;
   - any fix that keeps the property passes, wherever it places the check.
9. **Route where the protection never existed.** Real code reaches the protected sink but never had
   the check at all, so its absence reads as design (DeepSeek missed one 6 of 6 times). Rules:
   - it needs a plausible reason to dismiss: an unsupported combination, a legacy path, a
     neighbouring feature. If the project documents the protection as applying everywhere with no
     exceptions, there is no reason to dismiss and the route adds nothing;
   - the general property must cover it literally; never describe it in the instruction;
   - confirm it with a behavioural test on the pinned copy, like any Pattern B route.
10. **Merged or defaults route.** The restricted value reaches the sink through defaults, a merge,
    inheritance, a patch, or stored configuration rather than the request field the report shows.
    Models treat the report's example fields as the whole set. Rules:
    - state the property over the sink ("anything a submitter supplies that ends up in X, however
      it gets there"), not over the entry or field;
    - the security test drives the merged or stored route through the real entry point;
    - a functional test keeps legitimate defaults and merges working.

Aim for at least two levers with **different** reasons to dismiss.

**At least one lever must be how-type**: its fix needs the mechanism understood, not only found.
How-type levers are a producer off the check's path (5), a coupled must-keep-working value (4), a
shape that a plausible check mishandles (3: a separator split, a rename after the check), and a
route where the protection never existed. Where-type levers (another entry point into the same code,
a second copy, injected siblings) only cost a search. They held only when the report stayed general,
so count them as extras, never as the task's main difficulty.

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

## Environment (`tasks/stk-katex-7340/environment/Dockerfile`)
- **Base and code.** A small official base image. The repo goes into `/app` at the pinned commit,
  and `/app/.git` is then deleted.
- **Offline.** Install every dependency, tool and service the project and tests need; nothing may
  be downloaded at test time. Services start from `test.sh`.
- **Packages:** `patch`, `curl`, `ca-certificates`, `bash`, `git`.
- **Agent layer.** Append `common/trial/claude-code.Dockerfile.snippet` unchanged at the end.
- **No test code in the image.** The agent shares the container. Pre-build against stubs; `test.sh`
  copies the real tests in at grading time.
- **Project tests.** The project's own tests for the affected area must pass in the image at the
  pinned commit.
- **No leaked regression tests.** The pinned commit must not already contain the advisory's
  regression tests (check `git log` between the pinned and fix commits).

## Report to the solver (`tasks/stk-katex-7340/instruction.md`)
**Write:**
- what the system is, at product level;
- one observed impact, with ONE concrete trigger at user level (HTTP request, CLI call or public API
  use);
- the security property as an **invariant**, stated once in general terms: who may do what to which
  data, or what attacker input must never achieve ("no value of X may …, however it arrives"). It is
  fair when, read literally, it covers every tested route and shape; it must not point at any of
  them. Write a second property only for a genuinely different protection, never one per route,
  and never a count;
- every **contract** the tests need, each stated once for the whole product, never per route:
  - the refusal form ("a client error with no side effect");
  - any interface or field name a test uses, stated so it applies everywhere. If a sibling's test
    would need a contract that only that sibling uses, change the test so it does not, or drop the
    sibling;
  - preservation clauses ("everything that works today keeps working exactly as today"). Name a
    coupled legitimate value in property terms ("visible values keep binding even next to a hidden
    one"), not by the feature or route it sits on;
  - a legitimate magnitude next to any attack magnitude;
- that examples are examples, not the full set;
- the standard constraints block: fix the problem and its close variants; keep legitimate use
  working; do not look up the upstream fix; do not special-case the
  example.

**Never write:**
- file, package, function, class, field or parameter names a user would not see;
- line numbers, the root cause, the fix approach, or a CVE or GHSA id;
- a list of routes, spellings or roles;
- restricting adverbs ("directly", "only via");
- anything that names or paraphrases a far site, an uncovered route or an injected sibling;
- any clause that describes where a far site, uncovered route or injected sibling lives, even in
  product terms: no route, operation, command, channel, object kind, stage or format that points
  at one of them. State each property once, over the protected data or outcome, so it covers every
  route without pointing at any;
- a word that is general but is also the name of one stage or entry point ("loading" when the
  product has a load call). Pick wording that cannot be read as one surface.

Check before you finish: for each sentence of the report, ask whether it exists to cover one
specific route or trap. If it does, delete it or widen it into the general property.

Put every identifier that must not appear in `manifest.leak_terms`.

## Tests (`tasks/stk-katex-7340/tests/`)
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
- **Wrong-fix patches** go in `build/stk-katex-7340/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/stk-katex-7340/`:**
- `instruction.md`;
- `task.toml`, from `common/builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/stk-katex-7340/manifest.json`:**
- `slug`, `candidate`;
- `pattern`: `A+B`;
- `builder_prompt_version`: `build-v1`;
- `"strict_gate": true`;
- `verified`: entry point, sites, routes, services, project tests run;
- `leak_terms`, `patch_checks`, `wrong_fix_catalogue`;
- `traps`: one entry per lever, with `shape`, `where` (file:line), `security_tests`,
  `coupled_functional_tests`, `security_fail_patch`, and `realistic_because` (for pattern B: "real,
  unmodified upstream code");
- `status`.

**Also in `build/stk-katex-7340/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `common/builder/templates/` and `common/trial/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I common/gate/gate.py stk-katex-7340 --only static
python3 -I common/gate/gate.py stk-katex-7340 --only nop
python3 -I common/gate/gate.py stk-katex-7340 --only oracle
python3 -I common/gate/gate.py stk-katex-7340 --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/stk-katex-7340/`;
  - edit only `tasks/stk-katex-7340/`, `build/stk-katex-7340/` and, for pattern B, the register;
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


## Stacked task: additional rules

You are building a **stacked** task: one checkout with several independent places where a protection
is missing. The reader's record lists them, with evidence: `/home/mara/cwe-bench/pipelines/stacking/out/reader/h4-7340.json`. Verify each trap on the
pinned code before you rely on it. The record is a lead.

**The stack**
1. **At least 3 independent concepts.** If one guard or one fix site would close two traps, they are
   ONE concept. Count your reference fix's independent edit sites, not advisories or routes.
2. **Each concept is hard on its own** for at least one target model (tier hard or xhard in the
   record).
3. **Both models covered.** At least one DeepSeek-type trap (a route where the protection never
   existed, with a plausible reason to dismiss it) and at least one MiMo-type trap (a coupled
   must-keep-working value next to a hidden one, or a how-type mechanism).
4. **No single trap carries the task.** A fix that closes every concept except the hardest must still
   fail. Add one `security_fail` check patch per concept (a fix that misses only that concept).
5. **A coupled must-keep-working value next to every hidden route**, tested functionally. The
   report covers it ONLY through the general keep-working sentence ("everything that works today
   keeps working"); it never names or describes the value. If a security rule, read literally, would
   forbid that value, reword the security rule over its protected outcome instead of adding an
   exception that names the value.
6. **Effort budget.** A careful engineer who knows where to look fixes everything in about 45-60
   minutes. If the stack needs more, drop the weakest concept.

**The report**
7. **One general property per distinct protection, and nothing per trap.** Never one per route, and
   never a count. Describe no surface, as the build template already requires. If the stack spans two
   protections, state two properties, each over its protected data or outcome.
   - **The one-bug test:** for every sentence of the report, ask "would this sentence be here if the
     task had only the advisory's own route?" If not, delete it. That covers forms ("in every form it
     can be named"), timing ("and again when the call connects"), sources ("whichever response
     supplies it"), encodings, aliases, example values in keep-working lines, and lists of resources.
   - Only the advisory's own route may be shown, in the impact example.
   - General contracts that hold for every route stay: the refusal form (for example "a client
     error, with no effect"), an operator opt-in, "keep every legitimate use working".
   - Keep the report short: the goal in a few lines, the property, the general contracts.
   - After the build, `pipelines/stacking/4-listing/run_listing_check.sh` classifies every hidden trap against the
     report. One NAMED hidden trap, or more than one DESCRIBED hidden trap, is a FAIL. Once the
     reviewer is calibrated (`pipelines/stacking/4-listing/LISTING_ENFORCE`), a FAIL means the task is not marked sound.

**History rules** (by the record's `pattern`)
8. **H3a / H3b (fix of a fix):**
   - pin the parent of the earlier fix A's first commit;
   - the reference fix is the complete fix (A plus the later fix B, or an equivalent);
   - add `checks/upstream_first_fix.patch`, which is A's fix applied alone, with `expect: fail`, so
     upstream's first fix is proven to be a wrong fix.
9. **H3c (masking):** the masked bug's security test must fail on the pinned code through its own
   route, without relying on the masking bug, so the gate's nop stage holds.
10. **Conflicting fixes (F8):** when the record names a pair where the natural fix for one trap breaks
    a value another needs, test that value functionally. The report covers it only through the
    general keep-working sentence, as in rule 5; never by naming the value.
11. **Dependency-bump fixes (F5):** when upstream fixed a bug by upgrading a dependency, the task must
    be fixable inside the repository. The reference proves it. The report never asks for an upgrade,
    and the solver works offline.
12. **Recall check (every pattern):** add `checks/upstream_fix.patch` (every published fix commit for
    the stacked advisories, applied together) with `expect: fail`. If it passes, the stack adds
    nothing beyond what upstream shipped. Rework the design.

**The control task**
13. Also build `<slug>-control`: the same pinned code, the same report, but only the advisory's own
    route (the trap the report leads to) in the security tests and the reference. It isolates the
    effect of stacking from the effect of the host. The two `instruction.md` files stay byte-identical
    for the task's whole life: any later change to the stacked report (fairfix, upgrade) is copied to
    the control. `check_stack.py` checks it.

**Manifest:** add a `stacking` block containing:
- `pattern`;
- `reader_record`;
- `concepts` (groups of trap ids);
- `history`: advisories A and B with their fix commits, `pinned_commit` and its rule;
- `score_at_build`: copy the `score` of your job's row in `pipelines/stacking/out/stack_scores_ds.tsv` (do NOT run
  `score_stack.py`: it rewrites the shared selection file);
- `control_slug`.

**Exact manifest fields the static conformance check reads (step 5, `pipelines/stacking/3-build-gate/check_stack.py`). Emit these literally — the field NAMES and VALUES below must match, or the build is rejected before the container gate:**

`manifest.traps[]` — one object per trap:
- `id` (string) — referenced by `stacking.concepts`.
- `type` — exactly one of `"deepseek"`, `"mimo"`, or `"both"`. At least one trap must be `"deepseek"` or `"both"`, and at least one must be `"mimo"` or `"both"`.
- `origin` — for a hidden route, one of `"uncovered_upstream"`, `"published_fix_far_site"`, `"injection_room"`. Any trap with such an `origin` must also carry `coupled_functional_tests`: a non-empty list of the functional-test ids that keep its must-keep-working value honest.

`manifest.stacking` — an object with exactly these keys (all required):
- `pattern` — e.g. `"H3a"`, `"H3b1"`, `"H3b2"`, `"H4"`.
- `concepts` — a list of **at least 3** groups; each group is a list of trap `id`s forming one independent concept. Every id must exist in `manifest.traps`.
- `history`, `control_slug`, `score_at_build`, `reader_record` — as described above.

`manifest.patch_checks[]` — in addition to the task's normal patch checks, add:
- **One per concept** (a fix that closes every concept EXCEPT this one, so its security tests still fail):
  `{ "patch": "checks/miss_<concept>.patch", "kind": "security_fail", "expect": "security_fail", "misses": [<exactly this concept's trap ids>] }`.
  `misses` must be non-empty and be a subset of that concept's trap id group; one such check is required for every group in `stacking.concepts`.
- **Recall (always):** `{ "patch": "checks/upstream_fix.patch", "expect": "security_fail" }` — all published fix commits for the stacked advisories applied together.
- **Recall (H3a and every H3b variant):** also `{ "patch": "checks/upstream_first_fix.patch", "expect": "security_fail" }` — the earlier fix A applied alone.

Every `checks/*.patch` named above must be a real file in the task's `checks/` directory (the container gate then runs each with its `expect`ed outcome). A concept with no `security_fail` miss-check, a trap with no `type`, or a missing recall check/file each fails the conformance check.

**Report back:** also give the concept count, the DeepSeek-type and MiMo-type trap ids, the result of
each history check patch, and the control task's gate result.

Stacked task slug: `stk-katex-7340`. Control task slug: `stk-katex-7340-control`. Manifest `stacking.reader_record`: `pipelines/stacking/out/reader/h4-7340.json`.
