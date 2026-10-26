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

Project root: `/home/mara/cwe-bench`. Task: `stk-dompurify-ghsap98j`. Pattern: `A+B`. Track: `stacked`.

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
- Advisory: GHSA-c2j3-45gr-mqc4; GHSA-p98j-92pf-mc4p
- Pinned (vulnerable) commit: 0cae5187403132f96a6d357649e4b15633fc210a. Published fix: a9ca1e537422, b9b9d80f7e40.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "candidate_id": "h3-ghsa-p98j-92pf-mc4p",
 "pattern": "H3b2",
 "repo": "cure53/dompurify",
 "pinned_commit": "0cae5187403132f96a6d357649e4b15633fc210a",
 "protections": [
  "IN_PLACE: every node the sanitizer detaches from the caller's live tree is stripped of non-allowlisted attributes before sanitize returns, via the end-of-walk harvest of DOMPurify.removed into _neutralizeSubtree/_stripDisallowedAttributes (src/purify.ts:2528-2546, src/purify.ts:1310-1328, src/purify.ts:1267-1286).",
  "IN_PLACE + KEEP_CONTENT: the original children of a disallowed wrapper are hoisted back into the walk instead of being left detached as clones, so the nodes that carry already-queued resource events are the ones sanitized (src/purify.ts:1701-1739).",
  "IN_PLACE abort: a mid-walk exception empties the caller's live root so it is not returned half-sanitized, and the original error is rethrown (src/purify.ts:1190-1220, src/purify.ts:2432-2438, src/purify.ts:2519-2525).",
  "IN_PLACE entry: a forbidden or DOM-clobbered root is refused with a throw instead of being sanitized or neutralized (src/purify.ts:2402-2425)."
 ],
 "traps": [
  {
   "id": "T1",
   "mechanism": "M1",
   "origin": "advisory_route",
   "locations": [
    "src/purify.ts:2168",
    "src/purify.ts:1825",
    "src/purify.ts:2536"
   ],
   "reason_to_dismiss": "Hooks are the application's own trusted code and the node is gone from the returned tree, so the output looks clean; the only argument for leaving it is that a hook which removes a node is executing the caller's instruction.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "bypassed",
   "tier_deepseek": "easy",
   "tier_mimo": "easy",
   "type": "neither",
   "evidence": [
    "src/purify.ts:2168",
    "src/purify.ts:1825",
    "src/purify.ts:2383",
    "src/purify.ts:2536",
    "src/purify.ts:1708",
    "test/test-suite.js:5387"
   ]
  },
  {
   "id": "T2",
   "mechanism": "M10",
   "origin": "uncovered_upstream",
   "locations": [
    "src/purify.ts:2057",
    "src/purify.ts:2168",
    "src/purify.ts:1310",
    "src/purify.ts:2536"
   ],
   "reason_to_dismiss": "The report describes a hook removing the node it was called on; a hook that reaches out and removes an ancestor, a sibling or a child is a different shape, hooks are trusted, and the node the hook was invoked with was neutralized, so the fix looks complete.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "bypassed",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "mimo",
   "evidence": [
    "src/purify.ts:2504",
    "src/purify.ts:2168",
    "src/purify.ts:2536",
    "src/purify.ts:1310",
    "test/test-suite.js:5604"
   ]
  },
  {
   "id": "T3",
   "mechanism": "M4",
   "origin": "published_fix_far_site",
   "locations": [
    "src/purify.ts:1197",
    "src/purify.ts:1206",
    "src/purify.ts:2434",
    "src/purify.ts:2521"
   ],
   "reason_to_dismiss": "This is only the abort path: the call throws, the in-place root is emptied so the caller's tree looks fail-closed, and the children were detached rather than left rendered.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "xhard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "src/purify.ts:1190",
    "src/purify.ts:1197",
    "src/purify.ts:1206",
    "src/purify.ts:2521",
    "src/purify.ts:1165",
    "test/test-suite.js:5615"
   ]
  },
  {
   "id": "T4",
   "mechanism": "M7",
   "origin": "uncovered_upstream",
   "locations": [
    "src/purify.ts:2383",
    "src/purify.ts:1138",
    "src/purify.ts:2536"
   ],
   "reason_to_dismiss": "A hook that calls sanitize again is exotic app behaviour, the nested call looks self-contained, and its own harvest is assumed to tidy up the removals.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "bypassed",
   "tier_deepseek": "hard",
   "tier_mimo": "xhard",
   "type": "both",
   "evidence": [
    "src/purify.ts:1608",
    "src/purify.ts:2383",
    "src/purify.ts:1138",
    "src/purify.ts:2536",
    "src/purify.ts:2358"
   ]
  },
  {
   "id": "T5",
   "mechanism": "M2",
   "origin": "published_fix_far_site",
   "locations": [
    "src/purify.ts:2188",
    "src/purify.ts:2191",
    "src/purify.ts:2433",
    "src/purify.ts:2536"
   ],
   "reason_to_dismiss": "Shadow content is assumed inert (template.content is), and the IN_PLACE pre-pass already sanitized the shadow root, so a hook removal there looks harmless.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "bypassed",
   "tier_deepseek": "medium",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "src/purify.ts:2176",
    "src/purify.ts:2188",
    "src/purify.ts:2191",
    "src/purify.ts:2271",
    "src/purify.ts:2433",
    "src/purify.ts:2536"
   ]
  }
 ],
 "independent_groups": [
  [
   "T1",
   "T5"
  ],
  [
   "T2"
  ],
  [
   "T3"
  ],
  [
   "T4"
  ]
 ],
 "history": {
  "a_fix_leaves_b_open": true,
  "b_in_code_a_wrote": true,
  "masking": [
   "T1 masks T2, T3 and T4: while hook removals are silently unneutralised, the removed-list harvest (src/purify.ts:2536-2540) looks like complete coverage, so the ancestor/sibling shape, the abort teardown and the re-entrancy bookkeeping are never exercised.",
   "T1's natural per-node fix masks T2: a check on the hook's currentNode (parentless) fires for the reported shape but not for an ancestor removal, where currentNode keeps its parent and the detached armed subtree is a different object.",
   "T3 is masked by the throw contract: the caller sees an exception, so the children _neutralizeRoot detaches raw (including the armed <img> in the C3-F2 fixture, test/test-suite.js:5615-5626) are never inspected."
  ],
  "dependency_bump_fix": false,
  "in_repo_fix_possible": true
 },
 "conflicts": [
  {
   "a": "T1",
   "b": "T2",
   "what": "A per-node check on the hook's currentNode (T1's natural fix) is exactly what leaves the ancestor/sibling shape of T2 open; widening it to a containment test over the iterator root pulls in <template>.content and attached shadow-root nodes, which are not childNodes descendants of the root and whose hook-added attributes must survive in the output, so the T2 fix has to add template/shadow walking while T1's minimal fix does not."
  },
  {
   "a": "T3",
   "b": "T4",
   "what": "Fixing T4 by keeping the removal list local to each sanitize call leaves _neutralizeRoot (T3) with no list of its own: the abort barrier detaches children itself, so neutralization has to happen at the point of detach, whereas T4's fix pushes toward an end-of-call harvest - the two fixes disagree about when neutralization happens."
  }
 ],
 "fairness_risks": [
  "Documented node-removing hooks must keep working: demos/hooks-node-removal-demo.html:20-25 removes empty nodes in beforeSanitizeAttributes and demos/hooks-node-removal2-demo.html:49-53 removes a <footer> in uponSanitizeElement; a rule that throws on, or refuses, any hook-detached node contradicts documented behaviour.",
  "DOMPurify.removed is a public inventory (src/types.ts:19-23) that callers and tests read (test/test-suite.js:1538-1547), even though README.md:86 warns against security use; a fix that stops recording removals or rebinds the array breaks observable behaviour.",
  "Attributes a hook adds to kept nodes are documented as not re-validated (test/test-suite.js:3272-3288); a blanket 'strip everything that left the root' rule must not reach nodes that are in the output, including all of <template>.content and attached shadow roots, which are not descendants of the root through childNodes.",
  "A clobbered or forbidden IN_PLACE root must still throw rather than be neutralized (test/test-suite.js:1461-1474, test/test-suite.js:4771-4792); a rule that requires the live tree to be neutralized on every exit would contradict that documented refusal contract.",
  "Refused input shape: a hook that removes an empty element (the documented demo) is a legitimate shape that a 'hooks may not detach nodes' rule would reject."
 ],
 "effort_minutes": 120,
 "usable": true,
 "design": {
  "traps": [
   "T1",
   "T2",
   "T3",
   "T4"
  ],
  "why": "Four independent sites with four different dismissals. T1 is the reported route and is the warm-up: a hook detaches the current node, the iterator's next step resumes after the detached subtree, no handler in that subtree is ever stripped, and the node never enters DOMPurify.removed, so the return-path harvest (src/purify.ts:2536-2540) cannot see it. T2 is the wrong-object case: a hook that detaches an ancestor, sibling or child leaves the node the hook was invoked with parented, so the natural 'is currentNode still parented?' guard reports success; closing it needs containment reasoning against the iterator root, which then has to be extended to template.content and shadow roots or it strips nodes that ARE in the output. T3 is the far-site case with the strongest dismissal ('we throw, so we failed closed'): _neutralizeRoot empties the root but detaches its children raw (src/purify.ts:1197 vs 1206), so the armed <img> of the existing C3-F2 fixture survives - a DeepSeek-type trap. T4 is the bookkeeping case: a re-entrant sanitize from inside a hook replaces DOMPurify.removed (src/purify.ts:2383), so everything the outer walk detached before the nested call is never harvested - a how-type mechanism MiMo tends to miss. T5 (hook removal inside the shadow walk) is grouped with T1 because a guard placed in _sanitizeAttributes, which _sanitizeShadowDOM also calls (src/purify.ts:2188-2191), closes both; only a main-walk-only guard leaves it open. This design beats the one-guard alternatives: a single tree-diff guard is heavier, has to special-case template.content/shadow roots or over-strip documented hook-added attributes, and still needs a separate answer for the abort barrier and for the re-entrant call."
 },
 "unverified": [
  "Advisory-to-code mapping is inferred: the only IN_PLACE detached-handler protection in the pin is the audit-5 neutralisation (src/purify.ts:2528-2546; test/test-suite.js:5387-5449) plus the move-hoist (src/purify.ts:1730-1732). The advisory text for GHSA-c2j3-45gr-mqc4 and both fix diffs (a9ca1e537422, b9b9d80f7e40) are not in the tree.",
  "The later fix b9b9d80f7e40 is not in the pinned tree, so which of T2/T4/T5 it leaves open ('uncovered_upstream') and whether it extends into _neutralizeRoot ('published_fix_far_site') cannot be verified; the origins are inferences from the code shape, not from a diff.",
  "The reason a hook-detached subtree's descendants are never walked is the DOM NodeIterator pre-removing steps (DOM spec, not in the tree); the repo states the equivalent threat model at src/purify.ts:1708-1717 and pins the armed-original class at test/test-suite.js:5387-5409.",
  "History encoding: b_in_code_a_wrote=true records that the later gap is in the coverage of the neutralisation code the earlier fix added (src/purify.ts:2536-2540) - an incomplete fix, not a regression; the detach itself happens at the older hook call sites (src/purify.ts:1825, src/purify.ts:2168).",
  "Queued-event execution is not observable in this checkout (the node harness uses jsdom/happy-dom, which do not load resources), so traps are stated as attribute invariants (the captured original keeps or loses its on* handler), matching what the existing audit-5 and C3-F2 tests assert (test/test-suite.js:5412-5448, test/test-suite.js:5626-5631).",
  "T4's precondition (a hook calling DOMPurify.sanitize re-entrantly) is exercised nowhere in the suite; src/purify.ts:242-258 shows re-entrancy is a considered scenario for Trusted Types policies, but no test calls sanitize from inside a hook.",
  "The entry-refusal paths (src/purify.ts:2402-2425) also exit with the caller's live tree still armed, but are not listed as traps because the throw is the documented refusal contract (test/test-suite.js:1461-1474, test/test-suite.js:4771-4792); whether a hidden test would want neutralisation there is unknown."
 ]
}
  ```
- Published fix sites:   - src/purify.ts:2168 — T1 M1 (reason to dismiss: Hooks are the application's own trusted code and the node is gone from the returned tree, so the output looks clean; the only argument for leaving it is that a hook which removes a node is executing the caller's instruction.)
  - src/purify.ts:1825 — T1 M1 (reason to dismiss: Hooks are the application's own trusted code and the node is gone from the returned tree, so the output looks clean; the only argument for leaving it is that a hook which removes a node is executing the caller's instruction.)
  - src/purify.ts:2536 — T1 M1 (reason to dismiss: Hooks are the application's own trusted code and the node is gone from the returned tree, so the output looks clean; the only argument for leaving it is that a hook which removes a node is executing the caller's instruction.)
  - src/purify.ts:1197 — T3 M4 (reason to dismiss: This is only the abort path: the call throws, the in-place root is emptied so the caller's tree looks fail-closed, and the children were detached rather than left rendered.)
  - src/purify.ts:1206 — T3 M4 (reason to dismiss: This is only the abort path: the call throws, the in-place root is emptied so the caller's tree looks fail-closed, and the children were detached rather than left rendered.)
  - src/purify.ts:2434 — T3 M4 (reason to dismiss: This is only the abort path: the call throws, the in-place root is emptied so the caller's tree looks fail-closed, and the children were detached rather than left rendered.)
  - src/purify.ts:2521 — T3 M4 (reason to dismiss: This is only the abort path: the call throws, the in-place root is emptied so the caller's tree looks fail-closed, and the children were detached rather than left rendered.)
  - src/purify.ts:2188 — T5 M2 (reason to dismiss: Shadow content is assumed inert (template.content is), and the IN_PLACE pre-pass already sanitized the shadow root, so a hook removal there looks harmless.)
  - src/purify.ts:2191 — T5 M2 (reason to dismiss: Shadow content is assumed inert (template.content is), and the IN_PLACE pre-pass already sanitized the shadow root, so a hook removal there looks harmless.)
  - src/purify.ts:2433 — T5 M2 (reason to dismiss: Shadow content is assumed inert (template.content is), and the IN_PLACE pre-pass already sanitized the shadow root, so a hook removal there looks harmless.)
  - src/purify.ts:2536 — T5 M2 (reason to dismiss: Shadow content is assumed inert (template.content is), and the IN_PLACE pre-pass already sanitized the shadow root, so a hook removal there looks harmless.)
- Uncovered routes to confirm (pattern B):   - src/purify.ts:2057 — T2 M10 (reason to dismiss: The report describes a hook removing the node it was called on; a hook that reaches out and removes an ancestor, a sibling or a child is a different shape, hooks are trusted, and the node the hook was invoked with was neutralized, so the fix looks complete.)
  - src/purify.ts:2168 — T2 M10 (reason to dismiss: The report describes a hook removing the node it was called on; a hook that reaches out and removes an ancestor, a sibling or a child is a different shape, hooks are trusted, and the node the hook was invoked with was neutralized, so the fix looks complete.)
  - src/purify.ts:1310 — T2 M10 (reason to dismiss: The report describes a hook removing the node it was called on; a hook that reaches out and removes an ancestor, a sibling or a child is a different shape, hooks are trusted, and the node the hook was invoked with was neutralized, so the fix looks complete.)
  - src/purify.ts:2536 — T2 M10 (reason to dismiss: The report describes a hook removing the node it was called on; a hook that reaches out and removes an ancestor, a sibling or a child is a different shape, hooks are trusted, and the node the hook was invoked with was neutralized, so the fix looks complete.)
  - src/purify.ts:2383 — T4 M7 (reason to dismiss: A hook that calls sanitize again is exotic app behaviour, the nested call looks self-contained, and its own harvest is assumed to tidy up the removals.)
  - src/purify.ts:1138 — T4 M7 (reason to dismiss: A hook that calls sanitize again is exotic app behaviour, the nested call looks self-contained, and its own harvest is assumed to tidy up the removals.)
  - src/purify.ts:2536 — T4 M7 (reason to dismiss: A hook that calls sanitize again is exotic app behaviour, the nested call looks self-contained, and its own harvest is assumed to tidy up the removals.)
- Design plan from the lead: TRACK = STACKED (H3b2). Build the stacked design the reader chose: traps T1, T2, T3, T4. Why: Four independent sites with four different dismissals. T1 is the reported route and is the warm-up: a hook detaches the current node, the iterator's next step resumes after the detached subtree, no handler in that subtree is ever stripped, and the node never enters DOMPurify.removed, so the return-path harvest (src/purify.ts:2536-2540) cannot see it. T2 is the wrong-object case: a hook that detaches an ancestor, sibling or child leaves the node the hook was invoked with parented, so the natural 'is currentNode still parented?' guard reports success; closing it needs containment reasoning against the iterator root, which then has to be extended to template.content and shadow roots or it strips nodes that ARE in the output. T3 is the far-site case with the strongest dismissal ('we throw, so we failed closed'): _neutralizeRoot empties the root but detaches its children raw (src/purify.ts:1197 vs 1206), so the armed <img> of the existing C3-F2 fixture survives - a DeepSeek-type trap. T4 is the bookkeeping case: a re-entrant sanitize from inside a hook replaces DOMPurify.removed (src/purify.ts:2383), so everything the outer walk detached before the nested call is never harvested - a how-type mechanism MiMo tends to miss. T5 (hook removal inside the shadow walk) is grouped with T1 because a guard placed in _sanitizeAttributes, which _sanitizeShadowDOM also calls (src/purify.ts:2188-2191), closes both; only a main-walk-only guard leaves it open. This design beats the one-guard alternatives: a single tree-diff guard is heavier, has to special-case template.content/shadow roots or over-strip documented hook-added attributes, and still needs a separate answer for the abort barrier and for the re-entrant call. Follow the stacked-task rules appended at the end of this prompt; they add to the rules above.
- Host notes: Reader fairness risks (resolve each in the report's contracts or the tests): Documented node-removing hooks must keep working: demos/hooks-node-removal-demo.html:20-25 removes empty nodes in beforeSanitizeAttributes and demos/hooks-node-removal2-demo.html:49-53 removes a <footer> in uponSanitizeElement; a rule that throws on, or refuses, any hook-detached node contradicts documented behaviour. | DOMPurify.removed is a public inventory (src/types.ts:19-23) that callers and tests read (test/test-suite.js:1538-1547), even though README.md:86 warns against security use; a fix that stops recording removals or rebinds the array breaks observable behaviour. | Attributes a hook adds to kept nodes are documented as not re-validated (test/test-suite.js:3272-3288); a blanket 'strip everything that left the root' rule must not reach nodes that are in the output, including all of <template>.content and attached shadow roots, which are not descendants of the root through childNodes. | A clobbered or forbidden IN_PLACE root must still throw rather than be neutralized (test/test-suite.js:1461-1474, test/test-suite.js:4771-4792); a rule that requires the live tree to be neutralized on every exit would contradict that documented refusal contract. | Refused input shape: a hook that removes an empty element (the documented demo) is a legitimate shape that a 'hooks may not detach nodes' rule would reject.. Conflicts the reader found: A per-node check on the hook's currentNode (T1's natural fix) is exactly what leaves the ancestor/sibling shape of T2 open; widening it to a containment test over the iterator root pulls in <template>.content and attached shadow-root nodes, which are not childNodes descendants of the root and whose hook-added attributes must survive in the output, so the T2 fix has to add template/shadow walking while T1's minimal fix does not. | Fixing T4 by keeping the removal list local to each sanitize call leaves _neutralizeRoot (T3) with no list of its own: the abort barrier detaches children itself, so neutralization has to happen at the point of detach, whereas T4's fix pushes toward an end-of-call harvest - the two fixes disagree about when neutralization happens.

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

## Environment (`tasks/stk-dompurify-ghsap98j/environment/Dockerfile`)
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

## Report to the solver (`tasks/stk-dompurify-ghsap98j/instruction.md`)
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

## Tests (`tasks/stk-dompurify-ghsap98j/tests/`)
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
- **Wrong-fix patches** go in `build/stk-dompurify-ghsap98j/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/stk-dompurify-ghsap98j/`:**
- `instruction.md`;
- `task.toml`, from `common/builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/stk-dompurify-ghsap98j/manifest.json`:**
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

**Also in `build/stk-dompurify-ghsap98j/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `common/builder/templates/` and `common/trial/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I common/gate/gate.py stk-dompurify-ghsap98j --only static
python3 -I common/gate/gate.py stk-dompurify-ghsap98j --only nop
python3 -I common/gate/gate.py stk-dompurify-ghsap98j --only oracle
python3 -I common/gate/gate.py stk-dompurify-ghsap98j --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/stk-dompurify-ghsap98j/`;
  - edit only `tasks/stk-dompurify-ghsap98j/`, `build/stk-dompurify-ghsap98j/` and, for pattern B, the register;
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
is missing. The reader's record lists them, with evidence: `/home/mara/cwe-bench/pipelines/stacking/out/reader/h3-ghsa-p98j-92pf-mc4p.json`. Verify each trap on the
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

Stacked task slug: `stk-dompurify-ghsap98j`. Control task slug: `stk-dompurify-ghsap98j-control`. Manifest `stacking.reader_record`: `pipelines/stacking/out/reader/h3-ghsa-p98j-92pf-mc4p.json`.
