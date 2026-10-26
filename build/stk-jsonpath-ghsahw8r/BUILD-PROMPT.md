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

Project root: `/home/mara/cwe-bench`. Task: `stk-jsonpath-ghsahw8r`. Pattern: `A+B`. Track: `stacked`.

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
- Advisory: GHSA-pppg-cpfq-h7wr; GHSA-hw8r-x6gr-5gjp
- Pinned (vulnerable) commit: f20be141062453c26281e8d5ee8684cad62a1e35. Published fix: 6b2f1b4c2342, 73ad72e5ee78, b70aa713553c, 30942896d27c.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "candidate_id": "h3-ghsa-hw8r-x6gr-5gjp",
 "pattern": "H3a",
 "repo": "jsonpath-plus/jsonpath",
 "pinned_commit": "f20be141062453c26281e8d5ee8684cad62a1e35",
 "protections": [
  "P1: the default eval mode 'safe' must run filter and script expressions in the restricted AST interpreter (SafeEval), not in a native JS engine, in every build (node as well as browser).",
  "P2: the restricted interpreter must not let an expression reach a code-constructing object (the Function constructor via the constructor/prototype chain), whatever the property name's shape or the lookup route (member access or identifier lookup)."
 ],
 "traps": [
  {
   "id": "T1",
   "mechanism": "M2",
   "origin": "advisory_route",
   "locations": [
    "src/jsonpath-node.js:5",
    "src/jsonpath-node.js:7",
    "src/jsonpath.js:656-661"
   ],
   "reason_to_dismiss": "README says that in Node 'safe' 'has no effect and is equivalent to native as scripting is safe there', so vm.Script looks intentional.",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "src/jsonpath-node.js:4-5 (vm and safeVm both bound to Node's vm module)",
    "src/jsonpath-node.js:7 (exported SafeScript is vm.Script)",
    "src/jsonpath.js:165 (eval defaults to 'safe')",
    "src/jsonpath.js:656-661 ('safe', true and undefined all dispatch to this.safeVm.Script)",
    "src/jsonpath-browser.js:270-272 (only the browser build binds safeVm to the AST interpreter SafeScript)",
    "README.md:179-183 (documents Node 'safe' as equivalent to native)"
   ]
  },
  {
   "id": "T2",
   "mechanism": "M4",
   "origin": "advisory_route",
   "locations": [
    "src/jsonpath-browser.js:142-152",
    "src/jsonpath-browser.js:166-170"
   ],
   "reason_to_dismiss": "SafeEval is an AST interpreter with no eval/Function call, so it looks safe by construction. Member access is a plain obj[prop] with no property restriction.",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "src/jsonpath-browser.js:143-147 (any property name, including prototype-chain names, is read with obj[prop])",
    "src/jsonpath-browser.js:148-149 (function-valued results are returned bound, so constructor chains stay callable)",
    "src/jsonpath-browser.js:166-170 (any reached function is called with evaluated arguments)"
   ]
  },
  {
   "id": "T3",
   "mechanism": "M8",
   "origin": "advisory_route",
   "locations": [
    "src/jsonpath-browser.js:143-147"
   ],
   "reason_to_dismiss": "Once a check on the property name exists, a computed key looks like it is already covered because it evaluates to the same name. The check misses that the key may be a non-string value (an array) that is coerced only at obj[prop], or a string built at runtime (concatenation) rather than a literal.",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "weak",
   "tier_deepseek": "medium",
   "tier_mimo": "hard",
   "type": "mimo",
   "evidence": [
    "src/jsonpath-browser.js:143-145 (computed key is the evaluated value of any expression, not coerced to string before use)",
    "src/jsonpath-browser.js:163-165 (array expressions evaluate to arrays, which can serve as a computed key)",
    "src/jsonpath-browser.js:76-104 (binary '+' builds strings at runtime, so a check on the AST literal misses them)",
    "src/jsonpath-browser.js:147 (coercion of the key happens only at the property read)"
   ]
  },
  {
   "id": "T4",
   "mechanism": "M10",
   "origin": "uncovered_upstream",
   "locations": [
    "src/jsonpath-browser.js:133-137",
    "src/jsonpath-browser.js:199-201"
   ],
   "reason_to_dismiss": "Identifiers look like they resolve only to sandbox and @-variables ('is not defined' otherwise). But the 'in' test walks Object.prototype, so a bare identifier reaches inherited members such as 'constructor' (Object) and '__proto__' without any member-access name check.",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "xhard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "src/jsonpath-browser.js:134-135 ('ast.name in subs' accepts inherited names and returns subs[name])",
    "src/jsonpath-browser.js:200 (subs is a plain object literal spread from the sandbox, so it inherits Object.prototype)",
    "src/jsonpath-browser.js:166-170 (static methods on the reached object are callable with string arguments, so a dangerous name can travel as a call argument rather than a member name)"
   ]
  },
  {
   "id": "T5",
   "mechanism": "M11",
   "origin": "injection_room",
   "locations": [
    "src/jsonpath-browser.js:142-152",
    "src/jsonpath-browser.js:166-170"
   ],
   "reason_to_dismiss": "Blocking calls or bound methods, or refusing every member named like a prototype property, looks like the safest fix, but method calls on data and JSON own keys must keep working.",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "medium",
   "tier_mimo": "hard",
   "type": "mimo",
   "evidence": [
    "test/test.examples.js:256 (@.match(/TION$/i) must work)",
    "test/test.safe-eval.js:179 (array literal .includes(@property) must work)",
    "test/test.eval.js:221 (@.category.toLowerCase() must work)",
    "test/test.safe-eval.js:79-123 (sandbox functions must be callable)",
    "src/jsonpath-browser.js:148-149 (methods are returned bound, which the above relies on)"
   ]
  },
  {
   "id": "T6",
   "mechanism": "M1",
   "origin": "advisory_route",
   "locations": [
    "src/jsonpath.js:463-476",
    "src/jsonpath.js:436-453"
   ],
   "reason_to_dismiss": "Advisory payloads use the [?(...)] filter form. The dynamic-property form [(...)] and the nested-filter branch also reach _eval, so a string-level check placed only in the filter branch misses them.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "easy",
   "tier_mimo": "easy",
   "type": "neither",
   "evidence": [
    "src/jsonpath.js:432-436 (filter branch strips ?( ) and evaluates)",
    "src/jsonpath.js:463-474 ([(expr)] branch calls this._eval with the raw loc)",
    "src/jsonpath.js:438-453 (nested filter branch recurses via _trace into the same evaluator)",
    "src/jsonpath.js:631-681 (single _eval sink for all routes)"
   ]
  }
 ],
 "independent_groups": [
  [
   "T1"
  ],
  [
   "T2",
   "T3",
   "T6"
  ],
  [
   "T4"
  ],
  [
   "T5"
  ]
 ],
 "history": {
  "a_fix_leaves_b_open": true,
  "b_in_code_a_wrote": false,
  "masking": [
   "T1 masks T2/T3/T4 in the Node build. While Node 'safe' uses vm.Script (src/jsonpath-node.js:5), the SafeEval holes are reachable only through the browser build. Once T1 is fixed, they become the Node attack surface too.",
   "src/jsonpath-browser.js:144 evaluates a computed key without subs. Fixing that (passing subs) widens T3: keys held in sandbox or assigned variables (src/jsonpath-browser.js:171-178) become usable as computed keys."
  ],
  "dependency_bump_fix": false,
  "in_repo_fix_possible": true
 },
 "conflicts": [
  {
   "a": "T2",
   "b": "T5",
   "what": "A name denylist on member access, or a ban on calling bound methods, breaks @.match/.includes/.toLowerCase and sandbox functions (test/test.examples.js:256, test/test.safe-eval.js:179, test/test.eval.js:221). It also breaks JSON data that has an own key named 'constructor' unless the check exempts own properties."
  },
  {
   "a": "T1",
   "b": "T5",
   "what": "Switching Node 'safe' to SafeEval changes documented Node behaviour (README.md:181-182). Expressions that vm accepts but SafeEval rejects (e.g. 'this', test/test.errors.js:70-79) start throwing under the default eval."
  },
  {
   "a": "T4",
   "b": "T5",
   "what": "An own-property check in evalIdentifier must still resolve every sandbox key (including 'arguments', test/test.safe-eval.js:64-77) and the _$_ variables set at src/jsonpath.js:634-643."
  }
 ],
 "fairness_risks": [
  "Test harness masks T1: test-helpers/node-env.js:7-14 imports both src/jsonpath-node.js and src/jsonpath-browser.js, and both mutate the same JSONPath.prototype from src/jsonpath.js (src/jsonpath-node.js:4-5, src/jsonpath-browser.js:266-272). The browser import wins, so 'Node vm' tests actually run SafeScript. A hidden T1 test must run in a separate process, or check src/jsonpath-node.js's binding directly or via dist/index-node-*.",
  "JSONPath.cache (src/jsonpath.js:645-661, 693) is keyed by eval mode and code, not by implementation. A hidden test can be served a script compiled earlier in the same process by another build or binding. Clear the cache between cases.",
  "JSON data with own keys named 'constructor' or '__proto__' is a legitimate shape. A test refusing those names regardless of ownership would penalise correct fixes that only block inherited lookups.",
  "Method calls on values (.match, .includes, .toLowerCase, .length) and sandbox functions are must-keep-working. A test-visible rule 'no function calls' would contradict existing tests.",
  "The README documents Node 'safe' as equivalent to native (README.md:181-182). The task report must make clear that Node default eval is in scope, or T1 is unfair."
 ],
 "effort_minutes": 40,
 "usable": true,
 "design": {
  "traps": [
   "T1",
   "T2",
   "T3",
   "T4",
   "T5"
  ],
  "why": "Four independent fix sites with different reasons to dismiss: T1 (deepseek: the README says Node vm is safe; fix in src/jsonpath-node.js); T2+T3 (one member-access group, where T3 is a mimo how-type M8 shape: an array or runtime-built key evades a lexical or string-equality name check); T4 (deepseek/xhard: identifier lookup through the 'in' prototype walk reaches Object without any member name, a different fix site at src/jsonpath-browser.js:134); and T5 (mimo M11: method calls and own-key data must keep working, punishing over-hardening). T1 also masks the SafeEval holes in Node, so the stack rewards fixing both layers. T6 is left out as easy and absorbed by any SafeEval-level fix. Caveat: a single sink-side guard (refusing to call the Function constructor at src/jsonpath-browser.js:169) might collapse T2/T3/T4 into one group, unless hidden tests also cover native higher-order callbacks (e.g. Array.prototype.map) that invoke a reached constructor without going through evalCallExpression. See unverified."
 },
 "unverified": [
  "Pinned package.json:4 is version 9.0.0 and CHANGES.md:3 shows 10.0.0 unreleased, so neither A's fix (6b2f1b4c2342;73ad72e5ee78;b70aa713553c) nor B's (30942896d27c) is present. Their contents were not read in this checkout. From memory of upstream: A moved SafeScript into a shared module used by Node too and added a member-name block for 'constructor'; B (CVE-2025-1302) handled the computed array-key shape. Hence a_fix_leaves_b_open=true and b_in_code_a_wrote=false (B's sink, src/jsonpath-browser.js:142-152, predates A). Both are inferred from the candidate's 'incomplete fix' link, not from diffs.",
  "Whether upstream ever changed evalIdentifier to an own-property check (T4 origin 'uncovered_upstream') is from recollection, not verified in this checkout.",
  "The T4 route to the Function constructor through Object static methods (getPrototypeOf / getOwnPropertyDescriptor with the name passed as a string argument) is reasoned from src/jsonpath-browser.js:133-137,147-149,166-170. It was not executed.",
  "Whether a call-site-only guard (refusing Function at src/jsonpath-browser.js:169) can be bypassed via native higher-order callbacks was not executed. This decides whether T2/T3/T4 are truly independent of a sink-side fix.",
  "Prototype mutation via '__proto__' identifier/member plus Object.assign or __defineSetter__ is reachable through the same lookups. It is not recorded as a trap because it is CWE-1321, outside the candidate's CWE-94 advisories.",
  "That mocha loads node-env.js's setTimeout imports before any test runs (so the browser binding wins on the shared prototype) is inferred from test-helpers/node-env.js:6-15 and test/test.errors.js:70-79. The suite was not run."
 ]
}
  ```
- Published fix sites:   - src/jsonpath-node.js:5 — T1 M2 (reason to dismiss: README says that in Node 'safe' 'has no effect and is equivalent to native as scripting is safe there', so vm.Script looks intentional.)
  - src/jsonpath-node.js:7 — T1 M2 (reason to dismiss: README says that in Node 'safe' 'has no effect and is equivalent to native as scripting is safe there', so vm.Script looks intentional.)
  - src/jsonpath.js:656-661 — T1 M2 (reason to dismiss: README says that in Node 'safe' 'has no effect and is equivalent to native as scripting is safe there', so vm.Script looks intentional.)
  - src/jsonpath-browser.js:142-152 — T2 M4 (reason to dismiss: SafeEval is an AST interpreter with no eval/Function call, so it looks safe by construction. Member access is a plain obj[prop] with no property restriction.)
  - src/jsonpath-browser.js:166-170 — T2 M4 (reason to dismiss: SafeEval is an AST interpreter with no eval/Function call, so it looks safe by construction. Member access is a plain obj[prop] with no property restriction.)
  - src/jsonpath-browser.js:143-147 — T3 M8 (reason to dismiss: Once a check on the property name exists, a computed key looks like it is already covered because it evaluates to the same name. The check misses that the key may be a non-string value (an array) that is coerced only at obj[prop], or a string built at runtime (concatenation) rather than a literal.)
  - src/jsonpath.js:463-476 — T6 M1 (reason to dismiss: Advisory payloads use the [?(...)] filter form. The dynamic-property form [(...)] and the nested-filter branch also reach _eval, so a string-level check placed only in the filter branch misses them.)
  - src/jsonpath.js:436-453 — T6 M1 (reason to dismiss: Advisory payloads use the [?(...)] filter form. The dynamic-property form [(...)] and the nested-filter branch also reach _eval, so a string-level check placed only in the filter branch misses them.)
- Uncovered routes to confirm (pattern B):   - src/jsonpath-browser.js:133-137 — T4 M10 (reason to dismiss: Identifiers look like they resolve only to sandbox and @-variables ('is not defined' otherwise). But the 'in' test walks Object.prototype, so a bare identifier reaches inherited members such as 'constructor' (Object) and '__proto__' without any member-access name check.)
  - src/jsonpath-browser.js:199-201 — T4 M10 (reason to dismiss: Identifiers look like they resolve only to sandbox and @-variables ('is not defined' otherwise). But the 'in' test walks Object.prototype, so a bare identifier reaches inherited members such as 'constructor' (Object) and '__proto__' without any member-access name check.)
- Design plan from the lead: TRACK = STACKED (H3a). Build the stacked design the reader chose: traps T1, T2, T3, T4, T5. Why: Four independent fix sites with different reasons to dismiss: T1 (deepseek: the README says Node vm is safe; fix in src/jsonpath-node.js); T2+T3 (one member-access group, where T3 is a mimo how-type M8 shape: an array or runtime-built key evades a lexical or string-equality name check); T4 (deepseek/xhard: identifier lookup through the 'in' prototype walk reaches Object without any member name, a different fix site at src/jsonpath-browser.js:134); and T5 (mimo M11: method calls and own-key data must keep working, punishing over-hardening). T1 also masks the SafeEval holes in Node, so the stack rewards fixing both layers. T6 is left out as easy and absorbed by any SafeEval-level fix. Caveat: a single sink-side guard (refusing to call the Function constructor at src/jsonpath-browser.js:169) might collapse T2/T3/T4 into one group, unless hidden tests also cover native higher-order callbacks (e.g. Array.prototype.map) that invoke a reached constructor without going through evalCallExpression. See unverified. Follow the stacked-task rules appended at the end of this prompt; they add to the rules above.
- Host notes: Reader fairness risks (resolve each in the report's contracts or the tests): Test harness masks T1: test-helpers/node-env.js:7-14 imports both src/jsonpath-node.js and src/jsonpath-browser.js, and both mutate the same JSONPath.prototype from src/jsonpath.js (src/jsonpath-node.js:4-5, src/jsonpath-browser.js:266-272). The browser import wins, so 'Node vm' tests actually run SafeScript. A hidden T1 test must run in a separate process, or check src/jsonpath-node.js's binding directly or via dist/index-node-*. | JSONPath.cache (src/jsonpath.js:645-661, 693) is keyed by eval mode and code, not by implementation. A hidden test can be served a script compiled earlier in the same process by another build or binding. Clear the cache between cases. | JSON data with own keys named 'constructor' or '__proto__' is a legitimate shape. A test refusing those names regardless of ownership would penalise correct fixes that only block inherited lookups. | Method calls on values (.match, .includes, .toLowerCase, .length) and sandbox functions are must-keep-working. A test-visible rule 'no function calls' would contradict existing tests. | The README documents Node 'safe' as equivalent to native (README.md:181-182). The task report must make clear that Node default eval is in scope, or T1 is unfair.. Conflicts the reader found: A name denylist on member access, or a ban on calling bound methods, breaks @.match/.includes/.toLowerCase and sandbox functions (test/test.examples.js:256, test/test.safe-eval.js:179, test/test.eval.js:221). It also breaks JSON data that has an own key named 'constructor' unless the check exempts own properties. | Switching Node 'safe' to SafeEval changes documented Node behaviour (README.md:181-182). Expressions that vm accepts but SafeEval rejects (e.g. 'this', test/test.errors.js:70-79) start throwing under the default eval. | An own-property check in evalIdentifier must still resolve every sandbox key (including 'arguments', test/test.safe-eval.js:64-77) and the _$_ variables set at src/jsonpath.js:634-643.

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

## Environment (`tasks/stk-jsonpath-ghsahw8r/environment/Dockerfile`)
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

## Report to the solver (`tasks/stk-jsonpath-ghsahw8r/instruction.md`)
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

## Tests (`tasks/stk-jsonpath-ghsahw8r/tests/`)
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
- **Wrong-fix patches** go in `build/stk-jsonpath-ghsahw8r/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/stk-jsonpath-ghsahw8r/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/stk-jsonpath-ghsahw8r/manifest.json`:**
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

**Also in `build/stk-jsonpath-ghsahw8r/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py stk-jsonpath-ghsahw8r --only static
python3 -I builder/gate.py stk-jsonpath-ghsahw8r --only nop
python3 -I builder/gate.py stk-jsonpath-ghsahw8r --only oracle
python3 -I builder/gate.py stk-jsonpath-ghsahw8r --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/stk-jsonpath-ghsahw8r/`;
  - edit only `tasks/stk-jsonpath-ghsahw8r/`, `build/stk-jsonpath-ghsahw8r/` and, for pattern B, the register;
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
is missing. The reader's record lists them, with evidence: `/home/mara/cwe-bench/stacking/out/reader/h3-ghsa-hw8r-x6gr-5gjp.json`. Verify each trap on the
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
5. **A coupled must-keep-working value next to every hidden route**, tested functionally.
6. **Effort budget.** A careful engineer who knows where to look fixes everything in about 45-60
   minutes. If the stack needs more, drop the weakest concept.

**The report**
7. **One general property per distinct protection.** Never one per route, and never a count. Describe
   no surface, as the build template already requires. If the stack spans two protections, state two
   properties, each over its protected data or outcome.

**History rules** (by the record's `pattern`)
8. **H3a / H3b (fix of a fix):**
   - pin the parent of the earlier fix A's first commit;
   - the reference fix is the complete fix (A plus the later fix B, or an equivalent);
   - add `checks/upstream_first_fix.patch`, which is A's fix applied alone, with `expect: fail`, so
     upstream's first fix is proven to be a wrong fix.
9. **H3c (masking):** the masked bug's security test must fail on the pinned code through its own
   route, without relying on the masking bug, so the gate's nop stage holds.
10. **Conflicting fixes (F8):** when the record names a pair where the natural fix for one trap breaks
    a value another needs, test that value functionally. State it in the report as a
    must-keep-working behaviour, in property terms.
11. **Dependency-bump fixes (F5):** when upstream fixed a bug by upgrading a dependency, the task must
    be fixable inside the repository. The reference proves it. The report never asks for an upgrade,
    and the solver works offline.
12. **Recall check (every pattern):** add `checks/upstream_fix.patch` (every published fix commit for
    the stacked advisories, applied together) with `expect: fail`. If it passes, the stack adds
    nothing beyond what upstream shipped. Rework the design.

**The control task**
13. Also build `<slug>-control`: the same pinned code, the same report, but only the advisory's own
    route (the trap the report leads to) in the security tests and the reference. It isolates the
    effect of stacking from the effect of the host.

**Manifest:** add a `stacking` block containing:
- `pattern`;
- `reader_record`;
- `concepts` (groups of trap ids);
- `history`: advisories A and B with their fix commits, `pinned_commit` and its rule;
- `score_at_build`: from `stacking/score_stack.py`;
- `control_slug`.

**Exact manifest fields the static conformance check reads (step 5, `stacking/check_stack.py`). Emit these literally — the field NAMES and VALUES below must match, or the build is rejected before the container gate:**

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
  `{ "patch": "checks/miss_<concept>.patch", "kind": "security_fail", "expect": "fail", "misses": [<exactly this concept's trap ids>] }`.
  `misses` must be non-empty and be a subset of that concept's trap id group; one such check is required for every group in `stacking.concepts`.
- **Recall (always):** `{ "patch": "checks/upstream_fix.patch", "expect": "fail" }` — all published fix commits for the stacked advisories applied together.
- **Recall (H3a and every H3b variant):** also `{ "patch": "checks/upstream_first_fix.patch", "expect": "fail" }` — the earlier fix A applied alone.

Every `checks/*.patch` named above must be a real file in the task's `checks/` directory (the container gate then runs each with its `expect`ed outcome). A concept with no `security_fail` miss-check, a trap with no `type`, or a missing recall check/file each fails the conformance check.

**Report back:** also give the concept count, the DeepSeek-type and MiMo-type trap ids, the result of
each history check patch, and the control task's gate result.

Stacked task slug: `stk-jsonpath-ghsahw8r`. Control task slug: `stk-jsonpath-ghsahw8r-control`. Manifest `stacking.reader_record`: `stacking/out/reader/h3-ghsa-hw8r-x6gr-5gjp.json`.
