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

Project root: `/home/mara/cwe-bench`. Task: `stk-fast-xml-parser-ghsam7jm`. Pattern: `A+B`. Track: `stacked`.

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
- Advisory: GHSA-6w63-h3fj-q4vw; GHSA-m7jm-9gc2-mpf2
- Pinned (vulnerable) commit: a874ce78df0be1b5dceadc4e5e7e549c65a7a6ce. Published fix: 39b0e050bb90, a4bdced80369, 943ef0eb1b2d, ddcd0acf26dd.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "candidate_id": "h3-ghsa-m7jm-9gc2-mpf2",
 "pattern": "H3b",
 "repo": "naturalintelligence/fast-xml-parser",
 "pinned_commit": "a874ce78df0be1b5dceadc4e5e7e549c65a7a6ce",
 "protections": [
  "A DOCTYPE entity name must be consumed literally when the entity's replacement RegExp is built; no regex metacharacter admitted by the name grammar may act as a pattern (DocTypeReader.js:108-116).",
  "A name supplied through the external-entity API must be consumed literally when its replacement RegExp is built (XMLParser.addEntity -> OrderedObjParser.addExternalEntities).",
  "An entity replacement value must be inserted literally; it must not be interpreted as a String.replace replacement pattern ($&, $', $`, $n, $$).",
  "Entity substitution must not let a value that passed the 'no & in value' restriction become a new entity reference through re-scanning during later substitution passes."
 ],
 "traps": [
  {
   "id": "T1",
   "mechanism": "M8",
   "origin": "advisory_route",
   "locations": [
    "src/xmlparser/DocTypeReader.js:108",
    "src/xmlparser/DocTypeReader.js:113"
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
    "src/xmlparser/DocTypeReader.js:108",
    "src/xmlparser/DocTypeReader.js:113",
    "src/util.js:70",
    "src/xmlparser/OrderedObjParser.js:246",
    "src/xmlparser/OrderedObjParser.js:372"
   ]
  },
  {
   "id": "T2",
   "mechanism": "M2",
   "origin": "published_fix_far_site",
   "locations": [
    "src/xmlparser/OrderedObjParser.js:62",
    "src/xmlparser/XMLParser.js:46",
    "src/xmlparser/XMLParser.js:48"
   ],
   "reason_to_dismiss": "external entity names are supplied by the application through addEntity, not by the parsed XML, and the documented names are constants such as '#xD'",
   "distance": {
    "files": 2,
    "packages": 0
   },
   "protection_state": "weak",
   "tier_deepseek": "hard",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "src/xmlparser/OrderedObjParser.js:57",
    "src/xmlparser/OrderedObjParser.js:62",
    "src/xmlparser/XMLParser.js:34",
    "src/xmlparser/XMLParser.js:45",
    "src/xmlparser/XMLParser.js:48",
    "docs/v4/5.Entities.md:142",
    "spec/entities_spec.js:403"
   ]
  },
  {
   "id": "T3",
   "mechanism": "M4",
   "origin": "uncovered_upstream",
   "locations": [
    "src/xmlparser/OrderedObjParser.js:375",
    "src/xmlparser/OrderedObjParser.js:379",
    "src/xmlparser/OrderedObjParser.js:384"
   ],
   "reason_to_dismiss": "DOCTYPE values cannot contain '&', so the usual replacement tricks look blocked and the visible effect is only duplication of surrounding text",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "mimo",
   "evidence": [
    "src/xmlparser/DocTypeReader.js:114",
    "src/xmlparser/OrderedObjParser.js:375",
    "src/xmlparser/OrderedObjParser.js:379",
    "src/xmlparser/XMLParser.js:46"
   ]
  },
  {
   "id": "T4",
   "mechanism": "M7",
   "origin": "uncovered_upstream",
   "locations": [
    "src/xmlparser/OrderedObjParser.js:373",
    "src/xmlparser/OrderedObjParser.js:375",
    "src/xmlparser/OrderedObjParser.js:387"
   ],
   "reason_to_dismiss": "the repository documents this re-expansion as an intended side effect and a spec asserts it, and docs/v4/5.Entities.md:112 claims the '&'-in-value rule already blocks these attacks",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "xhard",
   "tier_mimo": "hard",
   "type": "both",
   "evidence": [
    "src/xmlparser/OrderedObjParser.js:373",
    "src/xmlparser/OrderedObjParser.js:375",
    "src/xmlparser/OrderedObjParser.js:387",
    "src/xmlparser/DocTypeReader.js:108",
    "spec/entities_spec.js:184",
    "docs/v4/5.Entities.md:64",
    "docs/v4/5.Entities.md:112"
   ]
  }
 ],
 "independent_groups": [
  [
   "T1"
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
  "a_fix_leaves_b_open": null,
  "b_in_code_a_wrote": null,
  "masking": [],
  "dependency_bump_fix": false,
  "in_repo_fix_possible": true
 },
 "conflicts": [
  {
   "a": "T1",
   "b": "T2",
   "what": "T1's simplest fix is to accept only XML-Name entity names, but the external-entity API documents and a spec uses the non-Name key '#xD' (docs/v4/5.Entities.md:142, spec/entities_spec.js:403); the shared fix must escape names rather than validate them, or T2's must-keep-working value breaks."
  },
  {
   "a": "T3",
   "b": "T4",
   "what": "A single-pass substitution that closes T4's re-expansion also removes the dynamic-entity expansion asserted by spec/entities_spec.js:184-225 and documented at docs/v4/5.Entities.md:64, while T3's literal-replacement fix has to preserve the two-step output that test expects."
  }
 ],
 "fairness_risks": [
  "addEntity('#xD', ...) is legitimate and documented (docs/v4/5.Entities.md:142-146; spec/entities_spec.js:403-412), but '#xD' is not an XML Name; a rule that entity names must be XML Names refuses a legitimate use.",
  "addEntity('gt', '<>') overrides a predefined entity and is asserted (spec/entities_spec.js:414-435); a rule forbidding shadowing of built-in entities would break legitimate behaviour.",
  "Valid XML names such as 'a1' or 'my-entity' are currently rejected by the entityRegex charset at DocTypeReader.js:108; widening the class to XML Name characters (util.js:3-5 includes '.' and '-') re-admits '.' as a regex metacharacter unless the name is escaped.",
  "Values containing '$' (for example a plain '$' or \"$'\") are legitimate text; a rule that refuses '$' in entity values contradicts legitimate data.",
  "The documented mitigation processEntities:false (OptionsBuilder.js:31; docs/v4/2.XMLparseOptions.md:622-623) does not prevent DOCTYPE entity regex construction because readDocType runs unconditionally at OrderedObjParser.js:246, while the option is only checked at OrderedObjParser.js:372.",
  "The dynamic-entity expansion (spec/entities_spec.js:184-225; docs/v4/5.Entities.md:64-99) must keep working, so any guard against T4 contradicts a shipped expectation.",
  "&amp;lt; must decode to '&lt;' (spec/entities_spec.js:512-534), which requires amp to stay last (OrderedObjParser.js:387); a literal single-pass decoder that handles amp first would double-decode."
 ],
 "effort_minutes": 90,
 "usable": true,
 "design": {
  "traps": [
   "T1",
   "T2",
   "T3"
  ],
  "why": "T1 is the anchor the advisory names and is the only must-fix; it is easy for both models because the report points at DOCTYPE entity names. T2 is the same guarded operation implemented a second time (entity name -> RegExp) behind a different producer (XMLParser.addEntity -> OrderedObjParser.addExternalEntities) and carries a real reason to dismiss ('names come from the developer, not the XML'), which is the absent-protection-plus-dismissal shape DeepSeek misses. T3 is a how-type mechanism on the other half of the same String.replace call: escaping the pattern (T1/T2) leaves replacement-pattern semantics ($', $`, $$) live, and the 'values cannot contain &' rule makes it easy to dismiss; that is the shape MiMo misses. The three need three separate edits in two files (DocTypeReader.js:113, OrderedObjParser.js:62, OrderedObjParser.js:375/379) and no shipped spec has to change, so the stack stays fair. T4 (a value re-entering reference resolution through the literal '&' that survives until the amp pass) is a stronger but riskier fourth trap: its natural fix contradicts the documented and tested dynamic-entity behaviour (spec/entities_spec.js:184-225, docs/v4/5.Entities.md:64-99), so it should be added only if the hidden tests intentionally redefine that behaviour."
 },
 "unverified": [
  "The pinned checkout does not contain A's fix (39b0e050bb90;a4bdced80369): package.json:3 shows 4.1.2 and CHANGELOG.md:3 tops out at 4.1.1 / 2023-02-03, months before a_published 2023-06-06; whether A's fix leaves B open therefore cannot be read from the pinned code and both history booleans are left null.",
  "B's fix (943ef0eb1b2d;ddcd0acf26dd) is not in the pinned checkout. The identification of the addExternalEntities sink (OrderedObjParser.js:62) as the B site and its origin 'published_fix_far_site' is an inference from the pinned code: it is the only other regex built from an entity name (the other is DocTypeReader.js:113), which fits the candidate's CWE-185. The candidate record's summary text was used as given; the B advisory itself was not read.",
  "If B is the OrderedObjParser.js:62 sink, then B is pre-existing code in the pin rather than a regression introduced by A; this follows from the pin being the pre-A state, but is not verifiable without A's and B's diffs.",
  "src/validator.js:228-248 contains a second DOCTYPE scanner that never validates entity names; it is not counted as a trap because that path has no entity sink (it only skips the declaration).",
  "Bundled copies (lib/fxparser.min.js and siblings) contain the same construction but are not counted: package.json:5 points main at src/fxp.js and the bundles are generated artifacts.",
  "DocTypeReader.js:112 uses an attacker-controlled name as a bare object key with no __proto__ guard, unlike OrderedObjParser.js:140 and xmlNode.js:11/15; this is outside the CWE-185 advisory scope and is not counted.",
  "The entityRegex name grammar [a-zA-z0-0] at DocTypeReader.js:108 admits '[', '\\', ']' and '^' (and excludes digits 1-9); the exact set of names that make the constructed RegExp throw versus over-match was reasoned from the character class, not executed."
 ]
}
  ```
- Published fix sites:   - src/xmlparser/DocTypeReader.js:108 — T1 M8 (reason to dismiss: none)
  - src/xmlparser/DocTypeReader.js:113 — T1 M8 (reason to dismiss: none)
  - src/xmlparser/OrderedObjParser.js:62 — T2 M2 (reason to dismiss: external entity names are supplied by the application through addEntity, not by the parsed XML, and the documented names are constants such as '#xD')
  - src/xmlparser/XMLParser.js:46 — T2 M2 (reason to dismiss: external entity names are supplied by the application through addEntity, not by the parsed XML, and the documented names are constants such as '#xD')
  - src/xmlparser/XMLParser.js:48 — T2 M2 (reason to dismiss: external entity names are supplied by the application through addEntity, not by the parsed XML, and the documented names are constants such as '#xD')
- Uncovered routes to confirm (pattern B):   - src/xmlparser/OrderedObjParser.js:375 — T3 M4 (reason to dismiss: DOCTYPE values cannot contain '&', so the usual replacement tricks look blocked and the visible effect is only duplication of surrounding text)
  - src/xmlparser/OrderedObjParser.js:379 — T3 M4 (reason to dismiss: DOCTYPE values cannot contain '&', so the usual replacement tricks look blocked and the visible effect is only duplication of surrounding text)
  - src/xmlparser/OrderedObjParser.js:384 — T3 M4 (reason to dismiss: DOCTYPE values cannot contain '&', so the usual replacement tricks look blocked and the visible effect is only duplication of surrounding text)
  - src/xmlparser/OrderedObjParser.js:373 — T4 M7 (reason to dismiss: the repository documents this re-expansion as an intended side effect and a spec asserts it, and docs/v4/5.Entities.md:112 claims the '&'-in-value rule already blocks these attacks)
  - src/xmlparser/OrderedObjParser.js:375 — T4 M7 (reason to dismiss: the repository documents this re-expansion as an intended side effect and a spec asserts it, and docs/v4/5.Entities.md:112 claims the '&'-in-value rule already blocks these attacks)
  - src/xmlparser/OrderedObjParser.js:387 — T4 M7 (reason to dismiss: the repository documents this re-expansion as an intended side effect and a spec asserts it, and docs/v4/5.Entities.md:112 claims the '&'-in-value rule already blocks these attacks)
- Design plan from the lead: TRACK = STACKED (H3b). Build the stacked design the reader chose: traps T1, T2, T3. Why: T1 is the anchor the advisory names and is the only must-fix; it is easy for both models because the report points at DOCTYPE entity names. T2 is the same guarded operation implemented a second time (entity name -> RegExp) behind a different producer (XMLParser.addEntity -> OrderedObjParser.addExternalEntities) and carries a real reason to dismiss ('names come from the developer, not the XML'), which is the absent-protection-plus-dismissal shape DeepSeek misses. T3 is a how-type mechanism on the other half of the same String.replace call: escaping the pattern (T1/T2) leaves replacement-pattern semantics ($', $`, $$) live, and the 'values cannot contain &' rule makes it easy to dismiss; that is the shape MiMo misses. The three need three separate edits in two files (DocTypeReader.js:113, OrderedObjParser.js:62, OrderedObjParser.js:375/379) and no shipped spec has to change, so the stack stays fair. T4 (a value re-entering reference resolution through the literal '&' that survives until the amp pass) is a stronger but riskier fourth trap: its natural fix contradicts the documented and tested dynamic-entity behaviour (spec/entities_spec.js:184-225, docs/v4/5.Entities.md:64-99), so it should be added only if the hidden tests intentionally redefine that behaviour. Follow the stacked-task rules appended at the end of this prompt; they add to the rules above.
- Host notes: Reader fairness risks (resolve each in the report's contracts or the tests): addEntity('#xD', ...) is legitimate and documented (docs/v4/5.Entities.md:142-146; spec/entities_spec.js:403-412), but '#xD' is not an XML Name; a rule that entity names must be XML Names refuses a legitimate use. | addEntity('gt', '<>') overrides a predefined entity and is asserted (spec/entities_spec.js:414-435); a rule forbidding shadowing of built-in entities would break legitimate behaviour. | Valid XML names such as 'a1' or 'my-entity' are currently rejected by the entityRegex charset at DocTypeReader.js:108; widening the class to XML Name characters (util.js:3-5 includes '.' and '-') re-admits '.' as a regex metacharacter unless the name is escaped. | Values containing '$' (for example a plain '$' or "$'") are legitimate text; a rule that refuses '$' in entity values contradicts legitimate data. | The documented mitigation processEntities:false (OptionsBuilder.js:31; docs/v4/2.XMLparseOptions.md:622-623) does not prevent DOCTYPE entity regex construction because readDocType runs unconditionally at OrderedObjParser.js:246, while the option is only checked at OrderedObjParser.js:372. | The dynamic-entity expansion (spec/entities_spec.js:184-225; docs/v4/5.Entities.md:64-99) must keep working, so any guard against T4 contradicts a shipped expectation. | &amp;lt; must decode to '&lt;' (spec/entities_spec.js:512-534), which requires amp to stay last (OrderedObjParser.js:387); a literal single-pass decoder that handles amp first would double-decode.. Conflicts the reader found: T1's simplest fix is to accept only XML-Name entity names, but the external-entity API documents and a spec uses the non-Name key '#xD' (docs/v4/5.Entities.md:142, spec/entities_spec.js:403); the shared fix must escape names rather than validate them, or T2's must-keep-working value breaks. | A single-pass substitution that closes T4's re-expansion also removes the dynamic-entity expansion asserted by spec/entities_spec.js:184-225 and documented at docs/v4/5.Entities.md:64, while T3's literal-replacement fix has to preserve the two-step output that test expects.

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

## Environment (`tasks/stk-fast-xml-parser-ghsam7jm/environment/Dockerfile`)
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

## Report to the solver (`tasks/stk-fast-xml-parser-ghsam7jm/instruction.md`)
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

## Tests (`tasks/stk-fast-xml-parser-ghsam7jm/tests/`)
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
- **Wrong-fix patches** go in `build/stk-fast-xml-parser-ghsam7jm/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/stk-fast-xml-parser-ghsam7jm/`:**
- `instruction.md`;
- `task.toml`, from `common/builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/stk-fast-xml-parser-ghsam7jm/manifest.json`:**
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

**Also in `build/stk-fast-xml-parser-ghsam7jm/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `common/builder/templates/` and `common/trial/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I common/gate/gate.py stk-fast-xml-parser-ghsam7jm --only static
python3 -I common/gate/gate.py stk-fast-xml-parser-ghsam7jm --only nop
python3 -I common/gate/gate.py stk-fast-xml-parser-ghsam7jm --only oracle
python3 -I common/gate/gate.py stk-fast-xml-parser-ghsam7jm --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/stk-fast-xml-parser-ghsam7jm/`;
  - edit only `tasks/stk-fast-xml-parser-ghsam7jm/`, `build/stk-fast-xml-parser-ghsam7jm/` and, for pattern B, the register;
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
is missing. The reader's record lists them, with evidence: `/home/mara/cwe-bench/pipelines/stacking/out/reader/h3-ghsa-m7jm-9gc2-mpf2.json`. Verify each trap on the
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

Stacked task slug: `stk-fast-xml-parser-ghsam7jm`. Control task slug: `stk-fast-xml-parser-ghsam7jm-control`. Manifest `stacking.reader_record`: `pipelines/stacking/out/reader/h3-ghsa-m7jm-9gc2-mpf2.json`.
