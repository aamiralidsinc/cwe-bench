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

Project root: `/home/mara/cwe-bench`. Task: `stk-bmoor-ghsa4m8h`. Pattern: `A+B`. Track: `stacked`.

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
- Advisory: GHSA-h3rx-g5c9-8q4x; GHSA-4m8h-h59m-m34j
- Pinned (vulnerable) commit: 57084c55270c6a3bb23f3b82f3f9222a25df641e. Published fix: 7d4a086a1dc3, 29b0162cc1dc.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "candidate_id": "h3-ghsa-4m8h-h59m-m34j",
 "pattern": "H3b2",
 "repo": "b-heilman/bmoor",
 "pinned_commit": "57084c55270c6a3bb23f3b82f3f9222a25df641e",
 "protections": [
  "Reject the key segments `__proto__`, `constructor` and `prototype` at every level of a path before `core.set` descends and assigns, for every path shape core.parse accepts (dot string, bracket/quoted string, pre-split array); this one shared sink is what `bmoor.set`, `object.explode` and `Config.set`/`Config.sub`/`Config.assign` all reach. Absent in the pinned code (src/core.js:174-197, src/core.js:138-163).",
  "The same key rejection in the separate path-setter factory `makeSetter`/`_makeSetter`, which builds closures that assign `ctx[property]` directly and never calls `set`. Absent in the pinned code (src/core.js:199-228).",
  "The same key rejection in the separate deep-write implementation `object.merge`, which recurses into `to[key]` for every enumerable key of the source. Absent in the pinned code (src/object.js:155-183).",
  "A guard on the resolved target in `Config.sub` before `Object.assign(rtn, assign)`, because `core.get` can resolve a caller path to Object.prototype or Object itself. Absent in the pinned code (src/lib/config.js:55-66).",
  "The same key rejection in `core.del`, which walks the identical path grammar and then deletes `curSpace[val]`. Absent in the pinned code (src/core.js:310-336)."
 ],
 "traps": [
  {
   "id": "T1",
   "mechanism": "M4",
   "origin": "advisory_route",
   "what": "The shared path writer core.set walks every segment of a caller-supplied path and does `curSpace[val] = value` without rejecting `__proto__` / `constructor` / `prototype`; for a plain root it descends through the inherited Object.prototype and writes the attacker key there. Every caller of bmoor.set inherits the gap.",
   "locations": [
    "src/core.js:174",
    "src/core.js:180",
    "src/core.js:187",
    "src/core.js:188",
    "src/core.js:191",
    "src/core.js:194"
   ],
   "reason_to_dismiss": "",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "easy",
   "tier_mimo": "easy",
   "type": "neither",
   "evidence": [
    "src/core.js:174",
    "src/core.js:180",
    "src/core.js:187",
    "src/core.js:188",
    "src/core.js:191",
    "src/core.js:194",
    "src/core.spec.js:56",
    "src/core.spec.js:59"
   ]
  },
  {
   "id": "T2",
   "mechanism": "M8",
   "origin": "advisory_route",
   "what": "The path grammar accepts three shapes and set filters none of them after parsing: a dot string is split on '.', a bracket/quoted string is tokenised and unquoted, and an array path is copied as-is; so a plausible check on the raw path or on `path.split('.')` still lets `constructor.prototype.x`, `foo.__proto__.polluted`, `[\"__proto__\"][\"polluted\"]` and `['__proto__','polluted']` through, and a nested `a.__proto__.x` also works because only the first segment is non-reserved.",
   "locations": [
    "src/core.js:143",
    "src/core.js:144",
    "src/core.js:146",
    "src/core.js:153",
    "src/core.js:155",
    "src/core.js:156",
    "src/core.js:187",
    "src/core.js:191",
    "src/core.js:194"
   ],
   "reason_to_dismiss": "The library's own callers pass literal dotted paths (src/lib/config.js:19, src/lib/config.js:60, src/object.js:23), so a check on the dot form looks sufficient and bracket/array inputs read as a separate parser feature.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "mimo",
   "evidence": [
    "src/core.js:138",
    "src/core.js:143",
    "src/core.js:144",
    "src/core.js:146",
    "src/core.js:153",
    "src/core.js:155",
    "src/core.js:187",
    "src/core.js:191",
    "src/core.js:194",
    "src/core.spec.js:94",
    "src/core.spec.js:104",
    "src/core.spec.js:109"
   ]
  },
  {
   "id": "T3",
   "mechanism": "M2",
   "origin": "published_fix_far_site",
   "what": "makeSetter is a second implementation of the same path write: `_makeSetter` builds a closure chain that reads `ctx[property]`, creates `ctx[property] = {}` when falsy, and assigns `ctx[property] = value` at the leaf, never calling core.set. A guard added to set therefore leaves `bmoor.makeSetter('__proto__.polluted')`, `makeSetter('constructor.prototype.polluted')` and `object.makeExploder` writing through Object.prototype.",
   "locations": [
    "src/core.js:199",
    "src/core.js:202",
    "src/core.js:205",
    "src/core.js:208",
    "src/core.js:212",
    "src/core.js:218",
    "src/core.js:221",
    "src/core.js:224",
    "src/object.js:34"
   ],
   "reason_to_dismiss": "makeSetter is a closure factory whose path is normally a developer literal at the call site (makeExploder is fed Object.keys of a data object at src/object.js:31), so it reads as internal plumbing rather than a request-reachable sink.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "src/core.js:199",
    "src/core.js:202",
    "src/core.js:205",
    "src/core.js:208",
    "src/core.js:212",
    "src/core.js:218",
    "src/core.js:221",
    "src/core.js:224",
    "src/object.js:31",
    "src/object.js:34",
    "src/core.spec.js:66"
   ]
  },
  {
   "id": "T4",
   "mechanism": "M2",
   "origin": "published_fix_far_site",
   "what": "object.merge is a second, separate deep-write implementation: `m()` recurses into `to[key]` for every enumerable key of the source, and for a plain target `to['__proto__']` is Object.prototype, so merging a payload with an own `__proto__` key writes its keys onto Object.prototype without ever calling set.",
   "locations": [
    "src/object.js:155",
    "src/object.js:156",
    "src/object.js:160",
    "src/object.js:161",
    "src/object.js:176",
    "src/object.js:177"
   ],
   "reason_to_dismiss": "merge is a deep-copy helper for combining two in-memory objects (src/object.spec.js:146-177), not the path setter the report names, and callers are expected to pass trusted objects.",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "both",
   "evidence": [
    "src/object.js:155",
    "src/object.js:157",
    "src/object.js:160",
    "src/object.js:161",
    "src/object.js:176",
    "src/object.js:177",
    "src/object.js:178",
    "src/object.spec.js:146",
    "src/object.spec.js:161",
    "src/object.spec.js:167"
   ]
  },
  {
   "id": "T5",
   "mechanism": "M6",
   "origin": "uncovered_upstream",
   "what": "Config.assign flattens its payload with object.implode and then calls set once per flattened key. A nested `__proto__` object becomes the single key string '__proto__.polluted', so a check placed on the raw payload or on object.explode never runs, and a check on the flattened keys sees no segment equal to '__proto__'; core.set then re-splits the string and writes onto Object.prototype.",
   "locations": [
    "src/lib/config.js:25",
    "src/lib/config.js:27",
    "src/lib/config.js:29",
    "src/object.js:88",
    "src/object.js:90",
    "src/object.js:96",
    "src/object.js:99",
    "src/core.js:180",
    "src/core.js:187",
    "src/core.js:194"
   ],
   "reason_to_dismiss": "Config.assign is bulk patching of a Config object with data that is already destined to become configuration, and implode is just a flattening serializer; the report is about the path setter.",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "mimo",
   "evidence": [
    "src/lib/config.js:24",
    "src/lib/config.js:25",
    "src/lib/config.js:29",
    "src/object.js:57",
    "src/object.js:65",
    "src/object.js:88",
    "src/object.js:93",
    "src/object.js:96",
    "src/object.js:99",
    "src/core.js:153",
    "src/core.js:180",
    "src/core.js:194",
    "src/object.spec.js:100",
    "src/lib/config.spec.js:89"
   ]
  },
  {
   "id": "T6",
   "mechanism": "M10",
   "origin": "uncovered_upstream",
   "what": "Config.sub resolves a caller-supplied path with core.get and then Object.assign's into whatever object it got. For the path '__proto__' or 'constructor.prototype' core.get returns Object.prototype itself, so the write lands on the shared prototype even when core.set is guarded; the code decides that the resolved value is a sub-config object and never checks what object it actually is.",
   "locations": [
    "src/lib/config.js:56",
    "src/lib/config.js:58",
    "src/lib/config.js:59",
    "src/lib/config.js:60",
    "src/lib/config.js:62"
   ],
   "reason_to_dismiss": "sub() is a config helper for creating sub-configs; its path is expected to point at a settings branch the caller owns, and the Object.assign line looks like an ordinary merge into a plain object.",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "both",
   "evidence": [
    "src/lib/config.js:55",
    "src/lib/config.js:56",
    "src/lib/config.js:58",
    "src/lib/config.js:59",
    "src/lib/config.js:60",
    "src/lib/config.js:62",
    "src/core.js:250",
    "src/core.js:253",
    "src/core.js:257",
    "src/core.js:261"
   ]
  },
  {
   "id": "T7",
   "mechanism": "M1",
   "origin": "published_fix_far_site",
   "what": "core.del walks the same parsed path and then deletes `curSpace[val]`, so `del({}, 'constructor.prototype.toString')` (or any built-in reachable through the prototype chain) removes a property from Object.prototype. A guard added to set does not reach it.",
   "locations": [
    "src/core.js:310",
    "src/core.js:316",
    "src/core.js:317",
    "src/core.js:321",
    "src/core.js:324",
    "src/core.js:328",
    "src/core.js:331",
    "src/core.js:332"
   ],
   "reason_to_dismiss": "del only removes properties rather than writing an attacker value, so it is not 'pollution' and looks out of scope for a prototype-pollution report.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "src/core.js:310",
    "src/core.js:316",
    "src/core.js:321",
    "src/core.js:328",
    "src/core.js:331",
    "src/core.js:332",
    "src/core.spec.js:78",
    "src/core.spec.js:86"
   ]
  },
  {
   "id": "T8",
   "mechanism": "M1",
   "origin": "uncovered_upstream",
   "what": "Scheduler.startScript stores/looks up a script under a caller-supplied name on a plain object and then does `this.schedule.length = 0` on the value it found; the name '__proto__' resolves to Object.prototype, so a `length` property is added to Object.prototype. That is enough to flip bmoor.isArrayLike for every ordinary object, because it accepts any object whose inherited length is 0 (src/core.js:90-97).",
   "locations": [
    "move/Scheduler.js:11",
    "move/Scheduler.js:12",
    "move/Scheduler.js:13",
    "move/Scheduler.js:14",
    "move/Scheduler.js:15",
    "move/Scheduler.js:17",
    "move/Scheduler.js:18"
   ],
   "reason_to_dismiss": "move/Scheduler.js is not exported from the package entry (src/index.js:2-13) and script names are developer constants in a DOM-move helper; the sibling move/dom.js even requires a non-existent ./core.js (move/dom.js:2), so the whole move/ tree reads as stale.",
   "distance": {
    "files": 2,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "xhard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "move/Scheduler.js:7",
    "move/Scheduler.js:11",
    "move/Scheduler.js:13",
    "move/Scheduler.js:15",
    "move/Scheduler.js:17",
    "src/core.js:90",
    "src/core.js:93",
    "src/index.js:2",
    "move/dom.js:2",
    "package.json:11"
   ]
  }
 ],
 "independent_groups": [
  [
   "T1",
   "T2",
   "T5"
  ],
  [
   "T3"
  ],
  [
   "T4"
  ],
  [
   "T6"
  ],
  [
   "T7"
  ],
  [
   "T8"
  ]
 ],
 "history": {
  "a_fix_leaves_b_open": true,
  "b_in_code_a_wrote": false,
  "masking": [
   "Once a `__proto__` segment is rejected in core.set, the `constructor.prototype` spelling in the same traversal (src/core.js:187-194) becomes the surviving route; the two key families are only distinguishable after the first is closed.",
   "Once core.set is guarded, Config.sub's get-then-Object.assign route (src/lib/config.js:56-62) becomes the visible prototype write, because it never calls set at all.",
   "Once set/explode are guarded, the implode-then-set route through Config.assign (src/object.js:99, src/lib/config.js:25-29) is the remaining way the same traversal is reached, since its key arrives already flattened as '__proto__.polluted'."
  ],
  "dependency_bump_fix": false,
  "in_repo_fix_possible": true
 },
 "conflicts": [
  {
   "a": "T4",
   "b": "T1",
   "what": "A shared recursive sanitizer written to close merge must keep null replacement and array-by-reference (src/object.spec.js:146-177); reusing a strict object-rebuild guard there breaks the pinned merge behaviour, so the T1 guard has to stay at the key-segment level instead of rewriting values."
  },
  {
   "a": "T5",
   "b": "T1",
   "what": "Validating the Config.assign payload before implode (the natural fix if the report points at bulk config) has to preserve implode's skipArray pass-through and nested ignore semantics (src/object.js:93-98, src/object.spec.js:100-143) while the shared core.set guard closes T5 without touching that path."
  },
  {
   "a": "T6",
   "b": "T1",
   "what": "Config.sub must keep creating a missing branch through set() for ordinary paths (src/lib/config.js:59-60) and keep merging an override into a genuine sub-config; a fix that refuses any path whose resolved value is a prototype must not refuse ordinary sub-paths."
  }
 ],
 "fairness_risks": [
  "core.parse is shared by the writers (set at src/core.js:180, makeSetter at src/core.js:221, del at src/core.js:317) and by the readers get/makeGetter (src/core.js:238-300); putting a key blacklist in parse would refuse legitimate reads such as get(o,'constructor') or get(o,'a.constructor'), and the empty-path read pinned by src/core.spec.js:19-28.",
  "Array-form paths and bracket/quoted notation are supported, tested inputs (src/core.js:143-156, src/core.spec.js:94-117); a rule that refuses those shapes is over-broad, while a rule that only inspects the dot form is unsound.",
  "Ordinary data and config may legitimately have own properties named `constructor` or `prototype`; a blanket name blacklist rather than blocking traversal into prototype objects refuses legitimate objects.",
  "merge must keep replacing nulls and assigning arrays by reference (src/object.spec.js:146-177); a general recursive rebuild or deep validation breaks these pinned results.",
  "implode must keep `skipArray` pass-through and single-level `ignore` semantics (src/object.js:90-98, src/object.spec.js:100-143), and Config.assign must keep arrays working (src/lib/config.spec.js:81-107).",
  "makeSetter must keep auto-creating missing intermediate objects (src/core.js:204-206, src/core.spec.js:66-76); a guard that returns early per segment can break a legitimately missing branch.",
  "Scheduler script names are arbitrary strings; the coupled safe fix is a null-prototype `$scripts` map, not a name blacklist (move/Scheduler.js:7,11-18), and the same applies to any other keyed registry whose keys are user/event names.",
  "Config.sub has no test in the suite (src/lib/config.spec.js covers only the constructor, assign and on), so a fix there has no must-keep counterexample to satisfy beyond the documented intent of creating sub-configs."
 ],
 "effort_minutes": 90,
 "usable": true,
 "design": {
  "traps": [
   "T1",
   "T3",
   "T4",
   "T6"
  ],
  "why": "Four independent fix sites, each needing its own judgement, so a solver who fixes one leaves the others live. T1 is the reported shared path writer that object.explode, Config.set and Config.assign all funnel into. T3 is a second path setter in the same file that builds closures and never calls set, dismissed as developer-authored plumbing. T4 is a second deep-write implementation in another file, dismissed as a trusted deep copy, whose must-keep null/array semantics are exactly where an over-hardened fix (MiMo's failure mode) breaks the pinned test. T6 is a get-then-Object.assign route that never touches the guarded writer and instead writes to whatever core.get resolved, which is Object.prototype for '__proto__'/'constructor.prototype' (a wrong-object/how-type judgement). The four have four different reasons to dismiss (none, plumbing, trusted copy plus coupled values, config literal path) and cover the model profiles: T3 is the deepseek-style absent-protection-with-a-dismissal, T4 and T6 carry the coupled-value/how-type mechanisms MiMo tends to miss. This beats a design built on T2 or T5, because a single correct check on parsed segments in core.set closes the bracket/array/constructor shapes (T2) and the implode-to-Config.assign dotted key (T5) at the same time, so those are grouped with T1 rather than counted; T7 (del) and T8 (Scheduler) are same-class extra sites but weaker (deletion-only, and a module not exported by the package entry), so they are recorded but not part of the core stack."
 },
 "unverified": [
  "Git history could not be read from the pinned worktree (its .git is a link outside the readable root), so the contents of a_fix 7d4a086a1dc3 and b_fix 29b0162cc1dc are not inspected. The harness log records the pin as 'parent of 7d4a086a1d' (/home/mara/cwe-bench/pipelines/stacking/out/reader-ds/_run.log:142), which is why the pinned tree contains no prototype-pollution guard at any of the recorded sites.",
  "Which site A actually patched, and therefore which of T1/T3/T4/T5/T6 is the B advisory's route, is inferred from the code shape and the 'incomplete fix' label, not read from the fix commits. The pinned tree cannot distinguish an A fix in core.set from one in object.explode.",
  "A guard placed in core.parse or in a shared key helper called by set, makeSetter and del would collapse T1/T2/T5/T7 into one fix site (M3, shared lower layer); the grouping here assumes enforcement in the individual writers, and the fairness note explains why a parse-level guard is not a free win (it would also block reads).",
  "Whether the hidden behavioural tests exercise bracket/quoted or array path forms (T2), Config.assign (T5), Config.sub (T6) or move/Scheduler.js (T8) is unknown; those are recorded from the pinned code, not from advisory text.",
  "The end-to-end exploitability of Config.sub (T6) depends on a caller passing an attacker-controlled sub path; the library-level behaviour is verified from source, the application route is not reproduced here.",
  "Broadcast._listeners was checked as a possible extra keyed-write sink and rejected: on('__proto__', cb) resolves Object.prototype and then throws because Object.prototype has no push, so no property is written (src/eventing/broadcast.js:12-22).",
  "Whether the package tarball actually ships move/Scheduler.js is not verifiable from the tree (package.json has no files field, main is src/index.js at src/../package.json:11), so T8 is recorded with a strong scope dismissal."
 ]
}
  ```
- Published fix sites:   - src/core.js:174 — T1 M4 (reason to dismiss: none)
  - src/core.js:180 — T1 M4 (reason to dismiss: none)
  - src/core.js:187 — T1 M4 (reason to dismiss: none)
  - src/core.js:188 — T1 M4 (reason to dismiss: none)
  - src/core.js:191 — T1 M4 (reason to dismiss: none)
  - src/core.js:194 — T1 M4 (reason to dismiss: none)
  - src/core.js:143 — T2 M8 (reason to dismiss: The library's own callers pass literal dotted paths (src/lib/config.js:19, src/lib/config.js:60, src/object.js:23), so a check on the dot form looks sufficient and bracket/array inputs read as a separate parser feature.)
  - src/core.js:144 — T2 M8 (reason to dismiss: The library's own callers pass literal dotted paths (src/lib/config.js:19, src/lib/config.js:60, src/object.js:23), so a check on the dot form looks sufficient and bracket/array inputs read as a separate parser feature.)
  - src/core.js:146 — T2 M8 (reason to dismiss: The library's own callers pass literal dotted paths (src/lib/config.js:19, src/lib/config.js:60, src/object.js:23), so a check on the dot form looks sufficient and bracket/array inputs read as a separate parser feature.)
  - src/core.js:153 — T2 M8 (reason to dismiss: The library's own callers pass literal dotted paths (src/lib/config.js:19, src/lib/config.js:60, src/object.js:23), so a check on the dot form looks sufficient and bracket/array inputs read as a separate parser feature.)
  - src/core.js:155 — T2 M8 (reason to dismiss: The library's own callers pass literal dotted paths (src/lib/config.js:19, src/lib/config.js:60, src/object.js:23), so a check on the dot form looks sufficient and bracket/array inputs read as a separate parser feature.)
  - src/core.js:156 — T2 M8 (reason to dismiss: The library's own callers pass literal dotted paths (src/lib/config.js:19, src/lib/config.js:60, src/object.js:23), so a check on the dot form looks sufficient and bracket/array inputs read as a separate parser feature.)
  - src/core.js:187 — T2 M8 (reason to dismiss: The library's own callers pass literal dotted paths (src/lib/config.js:19, src/lib/config.js:60, src/object.js:23), so a check on the dot form looks sufficient and bracket/array inputs read as a separate parser feature.)
  - src/core.js:191 — T2 M8 (reason to dismiss: The library's own callers pass literal dotted paths (src/lib/config.js:19, src/lib/config.js:60, src/object.js:23), so a check on the dot form looks sufficient and bracket/array inputs read as a separate parser feature.)
  - src/core.js:194 — T2 M8 (reason to dismiss: The library's own callers pass literal dotted paths (src/lib/config.js:19, src/lib/config.js:60, src/object.js:23), so a check on the dot form looks sufficient and bracket/array inputs read as a separate parser feature.)
  - src/core.js:199 — T3 M2 (reason to dismiss: makeSetter is a closure factory whose path is normally a developer literal at the call site (makeExploder is fed Object.keys of a data object at src/object.js:31), so it reads as internal plumbing rather than a request-reachable sink.)
  - src/core.js:202 — T3 M2 (reason to dismiss: makeSetter is a closure factory whose path is normally a developer literal at the call site (makeExploder is fed Object.keys of a data object at src/object.js:31), so it reads as internal plumbing rather than a request-reachable sink.)
  - src/core.js:205 — T3 M2 (reason to dismiss: makeSetter is a closure factory whose path is normally a developer literal at the call site (makeExploder is fed Object.keys of a data object at src/object.js:31), so it reads as internal plumbing rather than a request-reachable sink.)
  - src/core.js:208 — T3 M2 (reason to dismiss: makeSetter is a closure factory whose path is normally a developer literal at the call site (makeExploder is fed Object.keys of a data object at src/object.js:31), so it reads as internal plumbing rather than a request-reachable sink.)
  - src/core.js:212 — T3 M2 (reason to dismiss: makeSetter is a closure factory whose path is normally a developer literal at the call site (makeExploder is fed Object.keys of a data object at src/object.js:31), so it reads as internal plumbing rather than a request-reachable sink.)
  - src/core.js:218 — T3 M2 (reason to dismiss: makeSetter is a closure factory whose path is normally a developer literal at the call site (makeExploder is fed Object.keys of a data object at src/object.js:31), so it reads as internal plumbing rather than a request-reachable sink.)
  - src/core.js:221 — T3 M2 (reason to dismiss: makeSetter is a closure factory whose path is normally a developer literal at the call site (makeExploder is fed Object.keys of a data object at src/object.js:31), so it reads as internal plumbing rather than a request-reachable sink.)
  - src/core.js:224 — T3 M2 (reason to dismiss: makeSetter is a closure factory whose path is normally a developer literal at the call site (makeExploder is fed Object.keys of a data object at src/object.js:31), so it reads as internal plumbing rather than a request-reachable sink.)
  - src/object.js:34 — T3 M2 (reason to dismiss: makeSetter is a closure factory whose path is normally a developer literal at the call site (makeExploder is fed Object.keys of a data object at src/object.js:31), so it reads as internal plumbing rather than a request-reachable sink.)
  - src/object.js:155 — T4 M2 (reason to dismiss: merge is a deep-copy helper for combining two in-memory objects (src/object.spec.js:146-177), not the path setter the report names, and callers are expected to pass trusted objects.)
  - src/object.js:156 — T4 M2 (reason to dismiss: merge is a deep-copy helper for combining two in-memory objects (src/object.spec.js:146-177), not the path setter the report names, and callers are expected to pass trusted objects.)
  - src/object.js:160 — T4 M2 (reason to dismiss: merge is a deep-copy helper for combining two in-memory objects (src/object.spec.js:146-177), not the path setter the report names, and callers are expected to pass trusted objects.)
  - src/object.js:161 — T4 M2 (reason to dismiss: merge is a deep-copy helper for combining two in-memory objects (src/object.spec.js:146-177), not the path setter the report names, and callers are expected to pass trusted objects.)
  - src/object.js:176 — T4 M2 (reason to dismiss: merge is a deep-copy helper for combining two in-memory objects (src/object.spec.js:146-177), not the path setter the report names, and callers are expected to pass trusted objects.)
  - src/object.js:177 — T4 M2 (reason to dismiss: merge is a deep-copy helper for combining two in-memory objects (src/object.spec.js:146-177), not the path setter the report names, and callers are expected to pass trusted objects.)
  - src/core.js:310 — T7 M1 (reason to dismiss: del only removes properties rather than writing an attacker value, so it is not 'pollution' and looks out of scope for a prototype-pollution report.)
  - src/core.js:316 — T7 M1 (reason to dismiss: del only removes properties rather than writing an attacker value, so it is not 'pollution' and looks out of scope for a prototype-pollution report.)
  - src/core.js:317 — T7 M1 (reason to dismiss: del only removes properties rather than writing an attacker value, so it is not 'pollution' and looks out of scope for a prototype-pollution report.)
  - src/core.js:321 — T7 M1 (reason to dismiss: del only removes properties rather than writing an attacker value, so it is not 'pollution' and looks out of scope for a prototype-pollution report.)
  - src/core.js:324 — T7 M1 (reason to dismiss: del only removes properties rather than writing an attacker value, so it is not 'pollution' and looks out of scope for a prototype-pollution report.)
  - src/core.js:328 — T7 M1 (reason to dismiss: del only removes properties rather than writing an attacker value, so it is not 'pollution' and looks out of scope for a prototype-pollution report.)
  - src/core.js:331 — T7 M1 (reason to dismiss: del only removes properties rather than writing an attacker value, so it is not 'pollution' and looks out of scope for a prototype-pollution report.)
  - src/core.js:332 — T7 M1 (reason to dismiss: del only removes properties rather than writing an attacker value, so it is not 'pollution' and looks out of scope for a prototype-pollution report.)
- Uncovered routes to confirm (pattern B):   - src/lib/config.js:25 — T5 M6 (reason to dismiss: Config.assign is bulk patching of a Config object with data that is already destined to become configuration, and implode is just a flattening serializer; the report is about the path setter.)
  - src/lib/config.js:27 — T5 M6 (reason to dismiss: Config.assign is bulk patching of a Config object with data that is already destined to become configuration, and implode is just a flattening serializer; the report is about the path setter.)
  - src/lib/config.js:29 — T5 M6 (reason to dismiss: Config.assign is bulk patching of a Config object with data that is already destined to become configuration, and implode is just a flattening serializer; the report is about the path setter.)
  - src/object.js:88 — T5 M6 (reason to dismiss: Config.assign is bulk patching of a Config object with data that is already destined to become configuration, and implode is just a flattening serializer; the report is about the path setter.)
  - src/object.js:90 — T5 M6 (reason to dismiss: Config.assign is bulk patching of a Config object with data that is already destined to become configuration, and implode is just a flattening serializer; the report is about the path setter.)
  - src/object.js:96 — T5 M6 (reason to dismiss: Config.assign is bulk patching of a Config object with data that is already destined to become configuration, and implode is just a flattening serializer; the report is about the path setter.)
  - src/object.js:99 — T5 M6 (reason to dismiss: Config.assign is bulk patching of a Config object with data that is already destined to become configuration, and implode is just a flattening serializer; the report is about the path setter.)
  - src/core.js:180 — T5 M6 (reason to dismiss: Config.assign is bulk patching of a Config object with data that is already destined to become configuration, and implode is just a flattening serializer; the report is about the path setter.)
  - src/core.js:187 — T5 M6 (reason to dismiss: Config.assign is bulk patching of a Config object with data that is already destined to become configuration, and implode is just a flattening serializer; the report is about the path setter.)
  - src/core.js:194 — T5 M6 (reason to dismiss: Config.assign is bulk patching of a Config object with data that is already destined to become configuration, and implode is just a flattening serializer; the report is about the path setter.)
  - src/lib/config.js:56 — T6 M10 (reason to dismiss: sub() is a config helper for creating sub-configs; its path is expected to point at a settings branch the caller owns, and the Object.assign line looks like an ordinary merge into a plain object.)
  - src/lib/config.js:58 — T6 M10 (reason to dismiss: sub() is a config helper for creating sub-configs; its path is expected to point at a settings branch the caller owns, and the Object.assign line looks like an ordinary merge into a plain object.)
  - src/lib/config.js:59 — T6 M10 (reason to dismiss: sub() is a config helper for creating sub-configs; its path is expected to point at a settings branch the caller owns, and the Object.assign line looks like an ordinary merge into a plain object.)
  - src/lib/config.js:60 — T6 M10 (reason to dismiss: sub() is a config helper for creating sub-configs; its path is expected to point at a settings branch the caller owns, and the Object.assign line looks like an ordinary merge into a plain object.)
  - src/lib/config.js:62 — T6 M10 (reason to dismiss: sub() is a config helper for creating sub-configs; its path is expected to point at a settings branch the caller owns, and the Object.assign line looks like an ordinary merge into a plain object.)
  - move/Scheduler.js:11 — T8 M1 (reason to dismiss: move/Scheduler.js is not exported from the package entry (src/index.js:2-13) and script names are developer constants in a DOM-move helper; the sibling move/dom.js even requires a non-existent ./core.js (move/dom.js:2), so the whole move/ tree reads as stale.)
  - move/Scheduler.js:12 — T8 M1 (reason to dismiss: move/Scheduler.js is not exported from the package entry (src/index.js:2-13) and script names are developer constants in a DOM-move helper; the sibling move/dom.js even requires a non-existent ./core.js (move/dom.js:2), so the whole move/ tree reads as stale.)
  - move/Scheduler.js:13 — T8 M1 (reason to dismiss: move/Scheduler.js is not exported from the package entry (src/index.js:2-13) and script names are developer constants in a DOM-move helper; the sibling move/dom.js even requires a non-existent ./core.js (move/dom.js:2), so the whole move/ tree reads as stale.)
  - move/Scheduler.js:14 — T8 M1 (reason to dismiss: move/Scheduler.js is not exported from the package entry (src/index.js:2-13) and script names are developer constants in a DOM-move helper; the sibling move/dom.js even requires a non-existent ./core.js (move/dom.js:2), so the whole move/ tree reads as stale.)
  - move/Scheduler.js:15 — T8 M1 (reason to dismiss: move/Scheduler.js is not exported from the package entry (src/index.js:2-13) and script names are developer constants in a DOM-move helper; the sibling move/dom.js even requires a non-existent ./core.js (move/dom.js:2), so the whole move/ tree reads as stale.)
  - move/Scheduler.js:17 — T8 M1 (reason to dismiss: move/Scheduler.js is not exported from the package entry (src/index.js:2-13) and script names are developer constants in a DOM-move helper; the sibling move/dom.js even requires a non-existent ./core.js (move/dom.js:2), so the whole move/ tree reads as stale.)
  - move/Scheduler.js:18 — T8 M1 (reason to dismiss: move/Scheduler.js is not exported from the package entry (src/index.js:2-13) and script names are developer constants in a DOM-move helper; the sibling move/dom.js even requires a non-existent ./core.js (move/dom.js:2), so the whole move/ tree reads as stale.)
- Design plan from the lead: TRACK = STACKED (H3b2). Build the stacked design the reader chose: traps T1, T3, T4, T6. Why: Four independent fix sites, each needing its own judgement, so a solver who fixes one leaves the others live. T1 is the reported shared path writer that object.explode, Config.set and Config.assign all funnel into. T3 is a second path setter in the same file that builds closures and never calls set, dismissed as developer-authored plumbing. T4 is a second deep-write implementation in another file, dismissed as a trusted deep copy, whose must-keep null/array semantics are exactly where an over-hardened fix (MiMo's failure mode) breaks the pinned test. T6 is a get-then-Object.assign route that never touches the guarded writer and instead writes to whatever core.get resolved, which is Object.prototype for '__proto__'/'constructor.prototype' (a wrong-object/how-type judgement). The four have four different reasons to dismiss (none, plumbing, trusted copy plus coupled values, config literal path) and cover the model profiles: T3 is the deepseek-style absent-protection-with-a-dismissal, T4 and T6 carry the coupled-value/how-type mechanisms MiMo tends to miss. This beats a design built on T2 or T5, because a single correct check on parsed segments in core.set closes the bracket/array/constructor shapes (T2) and the implode-to-Config.assign dotted key (T5) at the same time, so those are grouped with T1 rather than counted; T7 (del) and T8 (Scheduler) are same-class extra sites but weaker (deletion-only, and a module not exported by the package entry), so they are recorded but not part of the core stack. Follow the stacked-task rules appended at the end of this prompt; they add to the rules above.
- Host notes: Reader fairness risks (resolve each in the report's contracts or the tests): core.parse is shared by the writers (set at src/core.js:180, makeSetter at src/core.js:221, del at src/core.js:317) and by the readers get/makeGetter (src/core.js:238-300); putting a key blacklist in parse would refuse legitimate reads such as get(o,'constructor') or get(o,'a.constructor'), and the empty-path read pinned by src/core.spec.js:19-28. | Array-form paths and bracket/quoted notation are supported, tested inputs (src/core.js:143-156, src/core.spec.js:94-117); a rule that refuses those shapes is over-broad, while a rule that only inspects the dot form is unsound. | Ordinary data and config may legitimately have own properties named `constructor` or `prototype`; a blanket name blacklist rather than blocking traversal into prototype objects refuses legitimate objects. | merge must keep replacing nulls and assigning arrays by reference (src/object.spec.js:146-177); a general recursive rebuild or deep validation breaks these pinned results. | implode must keep `skipArray` pass-through and single-level `ignore` semantics (src/object.js:90-98, src/object.spec.js:100-143), and Config.assign must keep arrays working (src/lib/config.spec.js:81-107). | makeSetter must keep auto-creating missing intermediate objects (src/core.js:204-206, src/core.spec.js:66-76); a guard that returns early per segment can break a legitimately missing branch. | Scheduler script names are arbitrary strings; the coupled safe fix is a null-prototype `$scripts` map, not a name blacklist (move/Scheduler.js:7,11-18), and the same applies to any other keyed registry whose keys are user/event names. | Config.sub has no test in the suite (src/lib/config.spec.js covers only the constructor, assign and on), so a fix there has no must-keep counterexample to satisfy beyond the documented intent of creating sub-configs.. Conflicts the reader found: A shared recursive sanitizer written to close merge must keep null replacement and array-by-reference (src/object.spec.js:146-177); reusing a strict object-rebuild guard there breaks the pinned merge behaviour, so the T1 guard has to stay at the key-segment level instead of rewriting values. | Validating the Config.assign payload before implode (the natural fix if the report points at bulk config) has to preserve implode's skipArray pass-through and nested ignore semantics (src/object.js:93-98, src/object.spec.js:100-143) while the shared core.set guard closes T5 without touching that path. | Config.sub must keep creating a missing branch through set() for ordinary paths (src/lib/config.js:59-60) and keep merging an override into a genuine sub-config; a fix that refuses any path whose resolved value is a prototype must not refuse ordinary sub-paths.

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

## Environment (`tasks/stk-bmoor-ghsa4m8h/environment/Dockerfile`)
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

## Report to the solver (`tasks/stk-bmoor-ghsa4m8h/instruction.md`)
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

## Tests (`tasks/stk-bmoor-ghsa4m8h/tests/`)
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
- **Wrong-fix patches** go in `build/stk-bmoor-ghsa4m8h/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/stk-bmoor-ghsa4m8h/`:**
- `instruction.md`;
- `task.toml`, from `common/builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/stk-bmoor-ghsa4m8h/manifest.json`:**
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

**Also in `build/stk-bmoor-ghsa4m8h/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `common/builder/templates/` and `common/trial/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I common/gate/gate.py stk-bmoor-ghsa4m8h --only static
python3 -I common/gate/gate.py stk-bmoor-ghsa4m8h --only nop
python3 -I common/gate/gate.py stk-bmoor-ghsa4m8h --only oracle
python3 -I common/gate/gate.py stk-bmoor-ghsa4m8h --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/stk-bmoor-ghsa4m8h/`;
  - edit only `tasks/stk-bmoor-ghsa4m8h/`, `build/stk-bmoor-ghsa4m8h/` and, for pattern B, the register;
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
is missing. The reader's record lists them, with evidence: `/home/mara/cwe-bench/pipelines/stacking/out/reader/h3-ghsa-4m8h-h59m-m34j.json`. Verify each trap on the
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

Stacked task slug: `stk-bmoor-ghsa4m8h`. Control task slug: `stk-bmoor-ghsa4m8h-control`. Manifest `stacking.reader_record`: `pipelines/stacking/out/reader/h3-ghsa-4m8h-h59m-m34j.json`.
