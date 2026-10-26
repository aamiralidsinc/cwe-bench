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

Project root: `/home/mara/cwe-bench`. Task: `stk-postcss-ghsafxqj`. Pattern: `A+B`. Track: `stacked`.

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
- Advisory: GHSA-6g55-p6wh-862q; GHSA-fxqj-rqcc-2cmp
- Pinned (vulnerable) commit: 233fb264ea4c37f9e2d7b64b2726e6d23fd02327. Published fix: aaec7b78b3ce, c64b7488d273, 7beca139e70f.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "candidate_id": "h3-ghsa-fxqj-rqcc-2cmp",
 "pattern": "H3b1",
 "repo": "postcss/postcss",
 "pinned_commit": "233fb264ea4c37f9e2d7b64b2726e6d23fd02327",
 "protections": [
  "Previous-map loading is gated by options (map:false, map.prev:false) and an annotation path is joined to dirname(opts.from) before existsSync/readFileSync (lib/previous-map.js:18, lib/previous-map.js:95, lib/previous-map.js:126, lib/previous-map.js:88).",
  "Before a new annotation is written, stale sourceMappingURL text is removed from the output: top-level Comment nodes of the root, or '/*#'-delimited blocks of the raw CSS string (lib/map-generator.js:65, lib/map-generator.js:70, lib/map-generator.js:77, lib/map-generator.js:91).",
  "The built-in Stringifier rewrites '<' sequences that could reopen an HTML tag ('</style', '<!--') in every chunk it builds, with Document child raws deliberately excluded (lib/stringifier.js:9, lib/stringifier.js:126, lib/stringifier.js:367).",
  "Source-map metadata parsed from map text is used only for reporting: Input#origin turns sources/sourceRoot into URLs/paths and never calls fs itself (lib/input.js:219, lib/input.js:238, lib/input.js:245)."
 ],
 "traps": [
  {
   "id": "T1",
   "mechanism": "M4",
   "origin": "advisory_route",
   "locations": [
    "lib/previous-map.js:72",
    "lib/previous-map.js:77",
    "lib/previous-map.js:124",
    "lib/previous-map.js:126",
    "lib/previous-map.js:88",
    "lib/previous-map.js:90"
   ],
   "reason_to_dismiss": "Auto-reading the map named by the CSS annotation is the documented feature (lib/previous-map.d.ts:13, lib/postcss.d.ts:300); a caller who does not want it must pass map:false or map.prev:false (lib/previous-map.js:18, lib/previous-map.js:95), so 'working as intended, not a vulnerability'.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "medium",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "lib/previous-map.js:72",
    "lib/previous-map.js:73",
    "lib/previous-map.js:77",
    "lib/previous-map.js:78",
    "lib/previous-map.js:82",
    "lib/previous-map.js:124",
    "lib/previous-map.js:126",
    "lib/previous-map.js:88",
    "lib/previous-map.js:90",
    "lib/input.js:71",
    "lib/postcss.d.ts:300",
    "test/previous-map.test.ts:170",
    "test/map.test.ts:384"
   ]
  },
  {
   "id": "T2",
   "mechanism": "M8",
   "origin": "uncovered_upstream",
   "locations": [
    "lib/previous-map.js:73",
    "lib/previous-map.js:77",
    "lib/map-generator.js:70",
    "lib/map-generator.js:73",
    "lib/parser.js:495",
    "lib/parser.js:513"
   ],
   "reason_to_dismiss": "Only a real comment is supposed to count as an annotation; marker text that merely appears inside a string, a declaration raw value, a selector or a nested rule is 'user data' the CSS cleaner should not rewrite.",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "both",
   "evidence": [
    "lib/previous-map.js:73",
    "lib/previous-map.js:77",
    "lib/map-generator.js:70",
    "lib/map-generator.js:73",
    "lib/parser.js:495",
    "lib/parser.js:498",
    "lib/parser.js:502",
    "lib/parser.js:513",
    "test/map.test.ts:558"
   ]
  },
  {
   "id": "T3",
   "mechanism": "M2",
   "origin": "published_fix_far_site",
   "locations": [
    "lib/lazy-result.js:381",
    "lib/lazy-result.js:382",
    "lib/map-generator.js:91",
    "lib/no-work-result.js:90"
   ],
   "reason_to_dismiss": "Without map options no map is produced, so there is nothing to clean; the annotation comment is content the user wrote and the fast path is only an optimization.",
   "distance": {
    "files": 2,
    "packages": 0
   },
   "protection_state": "weak",
   "tier_deepseek": "hard",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "lib/lazy-result.js:381",
    "lib/lazy-result.js:382",
    "lib/lazy-result.js:391",
    "lib/map-generator.js:91",
    "lib/map-generator.js:65",
    "lib/map-generator.js:70",
    "lib/no-work-result.js:80",
    "lib/no-work-result.js:90",
    "test/map.test.ts:167",
    "test/map.test.ts:580",
    "test/map.test.ts:569"
   ]
  },
  {
   "id": "T4",
   "mechanism": "M10",
   "origin": "uncovered_upstream",
   "locations": [
    "lib/input.js:74",
    "lib/input.js:75",
    "lib/input.js:202",
    "lib/input.js:224",
    "lib/input.js:238",
    "lib/input.js:245"
   ],
   "reason_to_dismiss": "Map file/sourceRoot/sources are part of the source-map format and mapping them back to file paths is exactly what Input#origin must do for Sass/compiler diagnostics, so any confinement here is 'over-hardening'.",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "mimo",
   "evidence": [
    "lib/input.js:74",
    "lib/input.js:75",
    "lib/input.js:198",
    "lib/input.js:202",
    "lib/input.js:219",
    "lib/input.js:224",
    "lib/input.js:238",
    "lib/input.js:245",
    "lib/previous-map.js:122",
    "lib/input.js:155",
    "lib/css-syntax-error.js:43",
    "test/previous-map.test.ts:269",
    "test/previous-map.test.ts:297"
   ]
  },
  {
   "id": "T5",
   "mechanism": "M11",
   "origin": "advisory_route",
   "locations": [
    "lib/previous-map.js:126",
    "lib/map-generator.js:265",
    "lib/map-generator.js:349",
    "lib/input.js:59",
    "lib/input.js:219"
   ],
   "reason_to_dismiss": "Absolute paths and file: URLs are legitimate for from/to, map.absolute and map sources, so the code intentionally keeps absolute paths; a blanket absolute-path rejection would break those, which is why the annotation path is treated the same way.",
   "distance": {
    "files": 2,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "medium",
   "tier_mimo": "hard",
   "type": "mimo",
   "evidence": [
    "lib/previous-map.js:126",
    "lib/previous-map.js:94",
    "lib/map-generator.js:265",
    "lib/map-generator.js:345",
    "lib/map-generator.js:349",
    "lib/input.js:59",
    "lib/input.js:219",
    "test/map.test.ts:607",
    "test/map.test.ts:625",
    "test/map.test.ts:638"
   ]
  },
  {
   "id": "T6",
   "mechanism": "M4",
   "origin": "uncovered_upstream",
   "locations": [
    "lib/stringifier.js:126",
    "lib/stringifier.js:367"
   ],
   "reason_to_dismiss": "Document child raws are the HTML around an inline CSS block and must stay byte-identical for HTML/document syntaxes; a committed test asserts that they are not escaped (test/stringifier.test.js:310).",
   "distance": {
    "files": 2,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "xhard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "lib/stringifier.js:9",
    "lib/stringifier.js:126",
    "lib/stringifier.js:367",
    "lib/stringifier.js:119",
    "test/stringifier.test.js:288",
    "test/stringifier.test.js:310",
    "test/processor.test.ts:581"
   ]
  },
  {
   "id": "T7",
   "mechanism": "M1",
   "origin": "advisory_route",
   "locations": [
    "lib/map-generator.js:296",
    "lib/no-work-result.js:80",
    "lib/no-work-result.js:81"
   ],
   "reason_to_dismiss": "The no-plugin path only builds a MapGenerator to decide whether a map exists; it is an internal duplicate of parse, so a guard placed in parse()/Input is assumed to cover it.",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "medium",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "lib/map-generator.js:283",
    "lib/map-generator.js:296",
    "lib/no-work-result.js:80",
    "lib/no-work-result.js:81",
    "lib/parse.js:8",
    "lib/input.js:71"
   ]
  },
  {
   "id": "T8",
   "mechanism": "M1",
   "origin": "uncovered_upstream",
   "locations": [
    "lib/terminal-highlight.js:51",
    "lib/css-syntax-error.js:64",
    "lib/css-syntax-error.js:124"
   ],
   "reason_to_dismiss": "Terminal highlighting only re-tokenizes an error snippet to color it; it is cosmetic code, not a file-loading path, and it is only reached when color output is supported.",
   "distance": {
    "files": 2,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "lib/terminal-highlight.js:51",
    "lib/terminal-highlight.js:9",
    "lib/css-syntax-error.js:50",
    "lib/css-syntax-error.js:60",
    "lib/css-syntax-error.js:64",
    "lib/css-syntax-error.js:124",
    "lib/input.js:139",
    "lib/input.js:271"
   ]
  }
 ],
 "independent_groups": [
  [
   "T1",
   "T5",
   "T7",
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
   "T6"
  ]
 ],
 "history": {
  "a_fix_leaves_b_open": true,
  "b_in_code_a_wrote": null,
  "masking": [
   "T3 is masked by T1: input.map is set only when the annotation file was actually read (lib/input.js:71, lib/previous-map.js:86-92), and the fast path in lib/lazy-result.js:381 is taken exactly when root.source.input.map is absent, so confining the read makes the stale annotation left in the output the only remaining carrier of the attacker path."
  ],
  "dependency_bump_fix": false,
  "in_repo_fix_possible": true
 },
 "conflicts": [
  {
   "a": "T1",
   "b": "T5",
   "what": "Confining the annotation path must not reject the absolute from/to paths, map.absolute file: URLs and file: sources that map generation legitimately emits (lib/input.js:59, lib/map-generator.js:265, lib/map-generator.js:349); an over-broad absolute-path rule fixes T1 but breaks those outputs (test/map.test.ts:607-636)."
  },
  {
   "a": "T1",
   "b": "T4",
   "what": "A containment rule applied to every map path would also confine map sources/sourceRoot, but legitimate maps resolve sources outside the project (test/previous-map.test.ts:279-294), so the read guard has to be scoped to annotation-derived paths while origin keeps resolving sources."
  },
  {
   "a": "T2",
   "b": "T3",
   "what": "Making clearAnnotation strip every text shape that loadAnnotation accepts would rewrite declaration raw values and selectors that merely contain the marker (lib/parser.js:495-514), so the provenance judgement has to be made in loadAnnotation, not in the output cleaner."
  }
 ],
 "fairness_risks": [
  "Previous maps must keep loading automatically from a real annotation relative to the CSS file (lib/postcss.d.ts:300, test/previous-map.test.ts:170-194, test/map.test.ts:384-414); a blanket refusal to read annotation files contradicts the documented feature.",
  "map.prev as a function or string is an explicit developer API that may name any path (lib/previous-map.js:98-110, test/previous-map.test.ts:224-267); a rule that forbids out-of-project reads for every prev form refuses legitimate input.",
  "annotation:false is documented to preserve the input annotation (test/map.test.ts:569-578, lib/postcss.d.ts:267-279); a rule that always strips sourceMappingURL text from output contradicts it.",
  "Absolute paths and URLs are legitimate for from/to/map.absolute and for map sources (lib/input.js:58-68, lib/map-generator.js:265, lib/map-generator.js:345-359, test/map.test.ts:607-652); a blanket lexical containment check refuses these legitimate inputs.",
  "Custom syntaxes, custom stringifiers and Document child raws must not be rewritten (test/stringifier.test.js:310-321, test/processor.test.ts:581-637); an 'escape everything' rule corrupts HTML documents.",
  "Maps legitimately reference sources outside the project (test/previous-map.test.ts:279-294, test/map.test.ts:364-414); refusing such source shapes breaks real Sass/compiler pipelines."
 ],
 "effort_minutes": 90,
 "usable": true,
 "design": {
  "traps": [
   "T1",
   "T2",
   "T3",
   "T4"
  ],
  "why": "Four independent judgements with four different dismissal arguments, covering one deepseek route and one mimo pressure: T1 (the auto-load feature, dismissed as 'documented behaviour' - the actual advisory route and the only file-read site), T2 (annotations hidden in strings/raw values/nested rules, dismissed as 'user data'), T3 (the no-map fast path that skips annotation cleaning, dismissed as 'nothing to clean'), and T4 (map metadata used for error reporting, dismissed as 'trusted build artifact' while a confinement fix must not break legitimate sourceRoot/sources). T1 carries the mimo coupling T5 (absolute paths/file: URLs must keep working elsewhere), so an over-broad absolute-path rule fails the existing map tests; T6 is a fifth, strongest-dismissal trap (a committed test asserts Document raws are not escaped) but it belongs to the escaping protection rather than CWE-200/22, so it is the optional extra. This beats a single-site read fix, which is one judgement and leaves T2/T3/T4 open, and it beats a pure escaping stack, whose only dismissal is nearly unanswerable and which does not touch the advisory's sourceMappingURL surface."
 },
 "unverified": [
  "No file-read guard exists anywhere in the pinned tree's sourceMappingURL path; the only security-shaped change visible in this checkout is the <style>-breakout escaping in lib/stringifier.js (CHANGELOG 8.5.10). I could not locate an A-side guard for GHSA-6g55-p6wh-862q, so b_in_code_a_wrote is left null: the git object database lives outside the worktree and was not read.",
  "Whether the withheld B fix targets previous-map.js (arbitrary read, matching the candidate summary) or the stringifier/document carve-out could not be determined from the pinned tree; both families are recorded, with T6 marked as out-of-family for the CWE-200/22 stack.",
  "The candidate's pattern label is H3b1 (szz_status); the output schema enumerates only H3a/H3b/H3c, so the sub-label was kept verbatim.",
  "fromJSON-hydrated PreviousMap objects (lib/fromJSON.js:19-24) bypass the PreviousMap constructor entirely and can carry attacker-supplied file/sourceRoot/sources; no filesystem read occurs, and the reporting impact is already covered by T4, so it was not counted as a separate group.",
  "The map.prev function route (lib/previous-map.js:100-110) is a second loadFile call site but is caller-controlled, so it is recorded as a fairness constraint rather than a trap.",
  "No tests were executed (shell execution is disabled in this session); all findings are from static reading of the pinned files and their committed tests."
 ]
}
  ```
- Published fix sites:   - lib/previous-map.js:72 — T1 M4 (reason to dismiss: Auto-reading the map named by the CSS annotation is the documented feature (lib/previous-map.d.ts:13, lib/postcss.d.ts:300); a caller who does not want it must pass map:false or map.prev:false (lib/previous-map.js:18, lib/previous-map.js:95), so 'working as intended, not a vulnerability'.)
  - lib/previous-map.js:77 — T1 M4 (reason to dismiss: Auto-reading the map named by the CSS annotation is the documented feature (lib/previous-map.d.ts:13, lib/postcss.d.ts:300); a caller who does not want it must pass map:false or map.prev:false (lib/previous-map.js:18, lib/previous-map.js:95), so 'working as intended, not a vulnerability'.)
  - lib/previous-map.js:124 — T1 M4 (reason to dismiss: Auto-reading the map named by the CSS annotation is the documented feature (lib/previous-map.d.ts:13, lib/postcss.d.ts:300); a caller who does not want it must pass map:false or map.prev:false (lib/previous-map.js:18, lib/previous-map.js:95), so 'working as intended, not a vulnerability'.)
  - lib/previous-map.js:126 — T1 M4 (reason to dismiss: Auto-reading the map named by the CSS annotation is the documented feature (lib/previous-map.d.ts:13, lib/postcss.d.ts:300); a caller who does not want it must pass map:false or map.prev:false (lib/previous-map.js:18, lib/previous-map.js:95), so 'working as intended, not a vulnerability'.)
  - lib/previous-map.js:88 — T1 M4 (reason to dismiss: Auto-reading the map named by the CSS annotation is the documented feature (lib/previous-map.d.ts:13, lib/postcss.d.ts:300); a caller who does not want it must pass map:false or map.prev:false (lib/previous-map.js:18, lib/previous-map.js:95), so 'working as intended, not a vulnerability'.)
  - lib/previous-map.js:90 — T1 M4 (reason to dismiss: Auto-reading the map named by the CSS annotation is the documented feature (lib/previous-map.d.ts:13, lib/postcss.d.ts:300); a caller who does not want it must pass map:false or map.prev:false (lib/previous-map.js:18, lib/previous-map.js:95), so 'working as intended, not a vulnerability'.)
  - lib/lazy-result.js:381 — T3 M2 (reason to dismiss: Without map options no map is produced, so there is nothing to clean; the annotation comment is content the user wrote and the fast path is only an optimization.)
  - lib/lazy-result.js:382 — T3 M2 (reason to dismiss: Without map options no map is produced, so there is nothing to clean; the annotation comment is content the user wrote and the fast path is only an optimization.)
  - lib/map-generator.js:91 — T3 M2 (reason to dismiss: Without map options no map is produced, so there is nothing to clean; the annotation comment is content the user wrote and the fast path is only an optimization.)
  - lib/no-work-result.js:90 — T3 M2 (reason to dismiss: Without map options no map is produced, so there is nothing to clean; the annotation comment is content the user wrote and the fast path is only an optimization.)
  - lib/previous-map.js:126 — T5 M11 (reason to dismiss: Absolute paths and file: URLs are legitimate for from/to, map.absolute and map sources, so the code intentionally keeps absolute paths; a blanket absolute-path rejection would break those, which is why the annotation path is treated the same way.)
  - lib/map-generator.js:265 — T5 M11 (reason to dismiss: Absolute paths and file: URLs are legitimate for from/to, map.absolute and map sources, so the code intentionally keeps absolute paths; a blanket absolute-path rejection would break those, which is why the annotation path is treated the same way.)
  - lib/map-generator.js:349 — T5 M11 (reason to dismiss: Absolute paths and file: URLs are legitimate for from/to, map.absolute and map sources, so the code intentionally keeps absolute paths; a blanket absolute-path rejection would break those, which is why the annotation path is treated the same way.)
  - lib/input.js:59 — T5 M11 (reason to dismiss: Absolute paths and file: URLs are legitimate for from/to, map.absolute and map sources, so the code intentionally keeps absolute paths; a blanket absolute-path rejection would break those, which is why the annotation path is treated the same way.)
  - lib/input.js:219 — T5 M11 (reason to dismiss: Absolute paths and file: URLs are legitimate for from/to, map.absolute and map sources, so the code intentionally keeps absolute paths; a blanket absolute-path rejection would break those, which is why the annotation path is treated the same way.)
  - lib/map-generator.js:296 — T7 M1 (reason to dismiss: The no-plugin path only builds a MapGenerator to decide whether a map exists; it is an internal duplicate of parse, so a guard placed in parse()/Input is assumed to cover it.)
  - lib/no-work-result.js:80 — T7 M1 (reason to dismiss: The no-plugin path only builds a MapGenerator to decide whether a map exists; it is an internal duplicate of parse, so a guard placed in parse()/Input is assumed to cover it.)
  - lib/no-work-result.js:81 — T7 M1 (reason to dismiss: The no-plugin path only builds a MapGenerator to decide whether a map exists; it is an internal duplicate of parse, so a guard placed in parse()/Input is assumed to cover it.)
- Uncovered routes to confirm (pattern B):   - lib/previous-map.js:73 — T2 M8 (reason to dismiss: Only a real comment is supposed to count as an annotation; marker text that merely appears inside a string, a declaration raw value, a selector or a nested rule is 'user data' the CSS cleaner should not rewrite.)
  - lib/previous-map.js:77 — T2 M8 (reason to dismiss: Only a real comment is supposed to count as an annotation; marker text that merely appears inside a string, a declaration raw value, a selector or a nested rule is 'user data' the CSS cleaner should not rewrite.)
  - lib/map-generator.js:70 — T2 M8 (reason to dismiss: Only a real comment is supposed to count as an annotation; marker text that merely appears inside a string, a declaration raw value, a selector or a nested rule is 'user data' the CSS cleaner should not rewrite.)
  - lib/map-generator.js:73 — T2 M8 (reason to dismiss: Only a real comment is supposed to count as an annotation; marker text that merely appears inside a string, a declaration raw value, a selector or a nested rule is 'user data' the CSS cleaner should not rewrite.)
  - lib/parser.js:495 — T2 M8 (reason to dismiss: Only a real comment is supposed to count as an annotation; marker text that merely appears inside a string, a declaration raw value, a selector or a nested rule is 'user data' the CSS cleaner should not rewrite.)
  - lib/parser.js:513 — T2 M8 (reason to dismiss: Only a real comment is supposed to count as an annotation; marker text that merely appears inside a string, a declaration raw value, a selector or a nested rule is 'user data' the CSS cleaner should not rewrite.)
  - lib/input.js:74 — T4 M10 (reason to dismiss: Map file/sourceRoot/sources are part of the source-map format and mapping them back to file paths is exactly what Input#origin must do for Sass/compiler diagnostics, so any confinement here is 'over-hardening'.)
  - lib/input.js:75 — T4 M10 (reason to dismiss: Map file/sourceRoot/sources are part of the source-map format and mapping them back to file paths is exactly what Input#origin must do for Sass/compiler diagnostics, so any confinement here is 'over-hardening'.)
  - lib/input.js:202 — T4 M10 (reason to dismiss: Map file/sourceRoot/sources are part of the source-map format and mapping them back to file paths is exactly what Input#origin must do for Sass/compiler diagnostics, so any confinement here is 'over-hardening'.)
  - lib/input.js:224 — T4 M10 (reason to dismiss: Map file/sourceRoot/sources are part of the source-map format and mapping them back to file paths is exactly what Input#origin must do for Sass/compiler diagnostics, so any confinement here is 'over-hardening'.)
  - lib/input.js:238 — T4 M10 (reason to dismiss: Map file/sourceRoot/sources are part of the source-map format and mapping them back to file paths is exactly what Input#origin must do for Sass/compiler diagnostics, so any confinement here is 'over-hardening'.)
  - lib/input.js:245 — T4 M10 (reason to dismiss: Map file/sourceRoot/sources are part of the source-map format and mapping them back to file paths is exactly what Input#origin must do for Sass/compiler diagnostics, so any confinement here is 'over-hardening'.)
  - lib/stringifier.js:126 — T6 M4 (reason to dismiss: Document child raws are the HTML around an inline CSS block and must stay byte-identical for HTML/document syntaxes; a committed test asserts that they are not escaped (test/stringifier.test.js:310).)
  - lib/stringifier.js:367 — T6 M4 (reason to dismiss: Document child raws are the HTML around an inline CSS block and must stay byte-identical for HTML/document syntaxes; a committed test asserts that they are not escaped (test/stringifier.test.js:310).)
  - lib/terminal-highlight.js:51 — T8 M1 (reason to dismiss: Terminal highlighting only re-tokenizes an error snippet to color it; it is cosmetic code, not a file-loading path, and it is only reached when color output is supported.)
  - lib/css-syntax-error.js:64 — T8 M1 (reason to dismiss: Terminal highlighting only re-tokenizes an error snippet to color it; it is cosmetic code, not a file-loading path, and it is only reached when color output is supported.)
  - lib/css-syntax-error.js:124 — T8 M1 (reason to dismiss: Terminal highlighting only re-tokenizes an error snippet to color it; it is cosmetic code, not a file-loading path, and it is only reached when color output is supported.)
- Design plan from the lead: TRACK = STACKED (H3b1). Build the stacked design the reader chose: traps T1, T2, T3, T4. Why: Four independent judgements with four different dismissal arguments, covering one deepseek route and one mimo pressure: T1 (the auto-load feature, dismissed as 'documented behaviour' - the actual advisory route and the only file-read site), T2 (annotations hidden in strings/raw values/nested rules, dismissed as 'user data'), T3 (the no-map fast path that skips annotation cleaning, dismissed as 'nothing to clean'), and T4 (map metadata used for error reporting, dismissed as 'trusted build artifact' while a confinement fix must not break legitimate sourceRoot/sources). T1 carries the mimo coupling T5 (absolute paths/file: URLs must keep working elsewhere), so an over-broad absolute-path rule fails the existing map tests; T6 is a fifth, strongest-dismissal trap (a committed test asserts Document raws are not escaped) but it belongs to the escaping protection rather than CWE-200/22, so it is the optional extra. This beats a single-site read fix, which is one judgement and leaves T2/T3/T4 open, and it beats a pure escaping stack, whose only dismissal is nearly unanswerable and which does not touch the advisory's sourceMappingURL surface. Follow the stacked-task rules appended at the end of this prompt; they add to the rules above.
- Host notes: Reader fairness risks (resolve each in the report's contracts or the tests): Previous maps must keep loading automatically from a real annotation relative to the CSS file (lib/postcss.d.ts:300, test/previous-map.test.ts:170-194, test/map.test.ts:384-414); a blanket refusal to read annotation files contradicts the documented feature. | map.prev as a function or string is an explicit developer API that may name any path (lib/previous-map.js:98-110, test/previous-map.test.ts:224-267); a rule that forbids out-of-project reads for every prev form refuses legitimate input. | annotation:false is documented to preserve the input annotation (test/map.test.ts:569-578, lib/postcss.d.ts:267-279); a rule that always strips sourceMappingURL text from output contradicts it. | Absolute paths and URLs are legitimate for from/to/map.absolute and for map sources (lib/input.js:58-68, lib/map-generator.js:265, lib/map-generator.js:345-359, test/map.test.ts:607-652); a blanket lexical containment check refuses these legitimate inputs. | Custom syntaxes, custom stringifiers and Document child raws must not be rewritten (test/stringifier.test.js:310-321, test/processor.test.ts:581-637); an 'escape everything' rule corrupts HTML documents. | Maps legitimately reference sources outside the project (test/previous-map.test.ts:279-294, test/map.test.ts:364-414); refusing such source shapes breaks real Sass/compiler pipelines.. Conflicts the reader found: Confining the annotation path must not reject the absolute from/to paths, map.absolute file: URLs and file: sources that map generation legitimately emits (lib/input.js:59, lib/map-generator.js:265, lib/map-generator.js:349); an over-broad absolute-path rule fixes T1 but breaks those outputs (test/map.test.ts:607-636). | A containment rule applied to every map path would also confine map sources/sourceRoot, but legitimate maps resolve sources outside the project (test/previous-map.test.ts:279-294), so the read guard has to be scoped to annotation-derived paths while origin keeps resolving sources. | Making clearAnnotation strip every text shape that loadAnnotation accepts would rewrite declaration raw values and selectors that merely contain the marker (lib/parser.js:495-514), so the provenance judgement has to be made in loadAnnotation, not in the output cleaner.

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

## Environment (`tasks/stk-postcss-ghsafxqj/environment/Dockerfile`)
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

## Report to the solver (`tasks/stk-postcss-ghsafxqj/instruction.md`)
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

## Tests (`tasks/stk-postcss-ghsafxqj/tests/`)
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
- **Wrong-fix patches** go in `build/stk-postcss-ghsafxqj/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/stk-postcss-ghsafxqj/`:**
- `instruction.md`;
- `task.toml`, from `common/builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/stk-postcss-ghsafxqj/manifest.json`:**
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

**Also in `build/stk-postcss-ghsafxqj/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `common/builder/templates/` and `common/trial/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I common/gate/gate.py stk-postcss-ghsafxqj --only static
python3 -I common/gate/gate.py stk-postcss-ghsafxqj --only nop
python3 -I common/gate/gate.py stk-postcss-ghsafxqj --only oracle
python3 -I common/gate/gate.py stk-postcss-ghsafxqj --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/stk-postcss-ghsafxqj/`;
  - edit only `tasks/stk-postcss-ghsafxqj/`, `build/stk-postcss-ghsafxqj/` and, for pattern B, the register;
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
is missing. The reader's record lists them, with evidence: `/home/mara/cwe-bench/pipelines/stacking/out/reader/h3-ghsa-fxqj-rqcc-2cmp.json`. Verify each trap on the
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

Stacked task slug: `stk-postcss-ghsafxqj`. Control task slug: `stk-postcss-ghsafxqj-control`. Manifest `stacking.reader_record`: `pipelines/stacking/out/reader/h3-ghsa-fxqj-rqcc-2cmp.json`.
