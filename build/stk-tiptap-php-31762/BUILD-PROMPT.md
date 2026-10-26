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

Project root: `/home/mara/cwe-bench`. Task: `stk-tiptap-php-31762`. Pattern: `A+B`. Track: `stacked`.

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
- Advisory: 31762; improper handling of unexpected data type (CWE-241): uncaught TypeErro
- Pinned (vulnerable) commit: 6ea321fa665080e1a72ac5f52dfab19f6a292e2d. Published fix: 74bfb7be1c8c6102b240f3879b7f984a6ab87b97.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "candidate_id": "h4-31762",
 "pattern": "H4",
 "repo": "ueberdosis/tiptap-php",
 "pinned_commit": "6ea321fa665080e1a72ac5f52dfab19f6a292e2d",
 "protections": [
  "P1  Link URI check: Link::isAllowedUri() assumes its argument is a string and passes it to preg_replace/preg_match with no type test (src/Marks/Link.php:30-42; called from src/Marks/Link.php:54 and :77).",
  "P2  Shared attribute serialisation: HTML::renderAttributes() assumes every attribute value is stringable, normalising only booleans before htmlentities (src/Utils/HTML.php:45-69, sink at :64), fed by DOMSerializer::renderOpeningTag (src/Core/DOMSerializer.php:217-252, merge at :244, call at :277).",
  "P3  Text escaping in the HTML serialiser: htmlspecialchars($node->text) with no type test (src/Core/DOMSerializer.php:76-77).",
  "P4  Text escaping in the text serialiser: an independent copy of P3 with no type test (src/Core/TextSerializer.php:45-46).",
  "P5  Extension callbacks that consume raw attribute values and stringify them themselves (src/Nodes/TableCell.php:56-58, src/Nodes/CodeBlock.php:59-61, src/Extensions/Color.php:43, src/Extensions/TextAlign.php:36, src/Extensions/FontFamily.php:43, src/Marks/Highlight.php:52)."
 ],
 "traps": [
  {
   "id": "T1",
   "mechanism": "M4",
   "origin": "advisory_route",
   "locations": [
    "src/Marks/Link.php:30-42",
    "src/Marks/Link.php:41",
    "src/Marks/Link.php:77",
    "src/Core/DOMSerializer.php:239-252",
    "src/Editor.php:68-70"
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
    "src/Marks/Link.php:32",
    "src/Marks/Link.php:36",
    "src/Marks/Link.php:41",
    "src/Marks/Link.php:77",
    "src/Core/DOMSerializer.php:252"
   ]
  },
  {
   "id": "T2",
   "mechanism": "M3",
   "origin": "uncovered_upstream",
   "locations": [
    "src/Utils/HTML.php:45-69",
    "src/Utils/HTML.php:64",
    "src/Marks/Link.php:83",
    "src/Core/DOMSerializer.php:277",
    "src/Nodes/Image.php:31-41"
   ],
   "reason_to_dismiss": "The advisory and the fix branch name the link's URI check; target/rel are not URIs and image attributes are a different extension, so a type guard in isAllowedUri reads as the complete fix.",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "weak",
   "tier_deepseek": "hard",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "src/Utils/HTML.php:48-58",
    "src/Utils/HTML.php:63",
    "src/Utils/HTML.php:64",
    "src/Marks/Link.php:83",
    "src/Core/DOMSerializer.php:274-283",
    "src/Nodes/Image.php:41"
   ]
  },
  {
   "id": "T3",
   "mechanism": "M11",
   "origin": "uncovered_upstream",
   "locations": [
    "src/Nodes/TableCell.php:51-59",
    "src/Nodes/TableCell.php:31-36",
    "src/Core/DOMSerializer.php:235-245",
    "tests/DOMSerializer/Nodes/TableTest.php:215"
   ],
   "reason_to_dismiss": "colwidth is a table feature, is legitimately an array, and the link advisory names neither the table extension nor join(); the neighbouring integer colspan/rowspan/start values must keep rendering.",
   "distance": {
    "files": 2,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "mimo",
   "evidence": [
    "src/Nodes/TableCell.php:57",
    "src/Nodes/TableCell.php:52",
    "src/Core/DOMSerializer.php:236",
    "tests/DOMSerializer/Nodes/TableTest.php:83-88",
    "tests/DOMSerializer/Nodes/TableTest.php:215",
    "tests/DOMSerializer/Nodes/OrderedListTest.php:61"
   ]
  },
  {
   "id": "T4",
   "mechanism": "M1",
   "origin": "uncovered_upstream",
   "locations": [
    "src/Core/DOMSerializer.php:76-77",
    "src/Core/DOMSerializer.php:38",
    "src/Extensions/StarterKit.php:65-67",
    "src/Editor.php:68-70"
   ],
   "reason_to_dismiss": "The advisory is about a link attribute; a text node has no attributes and the published guard never comes near htmlspecialchars.",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "src/Core/DOMSerializer.php:76",
    "src/Core/DOMSerializer.php:77",
    "src/Core/DOMSerializer.php:38",
    "src/Extensions/StarterKit.php:65-67"
   ]
  },
  {
   "id": "T5",
   "mechanism": "M2",
   "origin": "uncovered_upstream",
   "locations": [
    "src/Core/TextSerializer.php:45-46",
    "src/Editor.php:73-76"
   ],
   "reason_to_dismiss": "Every example and the advisory use getHTML(); the second serialiser behind getText() is a separate class that a fix in DOMSerializer never reaches.",
   "distance": {
    "files": 2,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "medium",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "src/Core/TextSerializer.php:21-35",
    "src/Core/TextSerializer.php:45",
    "src/Core/TextSerializer.php:46",
    "src/Editor.php:73-76"
   ]
  },
  {
   "id": "T6",
   "mechanism": "M6",
   "origin": "uncovered_upstream",
   "locations": [
    "src/Core/DOMSerializer.php:235-241",
    "src/Extensions/Color.php:43",
    "src/Extensions/TextAlign.php:36",
    "src/Extensions/FontFamily.php:43",
    "src/Marks/Highlight.php:52"
   ],
   "reason_to_dismiss": "These are style/global attributes of unrelated extensions and none of them is a URL; the href guard never sees the values the serializer hands to these callbacks.",
   "distance": {
    "files": 2,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "src/Core/DOMSerializer.php:236",
    "src/Extensions/Color.php:37",
    "src/Extensions/Color.php:43",
    "src/Extensions/TextAlign.php:36",
    "src/Extensions/FontFamily.php:43",
    "src/Marks/Highlight.php:52"
   ]
  },
  {
   "id": "T7",
   "mechanism": "M4",
   "origin": "uncovered_upstream",
   "locations": [
    "src/Nodes/CodeBlock.php:51-66",
    "src/Nodes/CodeBlock.php:46",
    "src/Extensions/StarterKit.php:44-46"
   ],
   "reason_to_dismiss": "The language attribute is 'rendered' => false and is read straight from the node by its own extension, so it is not part of the attribute path the advisory touches.",
   "distance": {
    "files": 2,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "src/Nodes/CodeBlock.php:46",
    "src/Nodes/CodeBlock.php:59-61",
    "src/Extensions/StarterKit.php:44-46"
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
   "T2 is unreachable while href is also non-string: the mark is rendered first (src/Core/DOMSerializer.php:38 -> src/Marks/Link.php:77) and the URI check throws before any target/rel value reaches src/Utils/HTML.php:64, so fixing T1 is what exposes T2.",
   "T4 has the same ordering mask: marks are serialised before the text branch, so a text node carrying both a non-string href mark and a non-string text throws at the href first and only reaches src/Core/DOMSerializer.php:77 once T1 is fixed."
  ],
  "dependency_bump_fix": false,
  "in_repo_fix_possible": true
 },
 "conflicts": [
  {
   "a": "T2",
   "b": "T3",
   "what": "The attractive fix for T2 - normalise or drop every non-string attribute, either in DOMSerializer::renderOpeningTag:236 before the renderHTML callbacks or as a blanket is_string filter at src/Utils/HTML.php:63 - breaks T3's must-keep-working output: TableCell's colwidth would arrive at its join() callback as a string (src/Nodes/TableCell.php:57) and integer colspan/rowspan/start would be dropped, contradicting tests/DOMSerializer/Nodes/TableTest.php:215 and tests/DOMSerializer/Nodes/OrderedListTest.php:61."
  },
  {
   "a": "T1",
   "b": "T6",
   "what": "A producer-side normalisation that keeps arrays (needed by T3) still lets those arrays reach the style interpolations (T6), where PHP silently turns an array into 'Array' instead of rejecting it, so T6's fix has to be a rejection at the callback and not the same coercion T3 requires."
  }
 ],
 "fairness_risks": [
  "tests/DOMSerializer/Nodes/TableTest.php:215 requires colspan=\"2\" built from the integer 2 and data-colwidth=\"100,0\" built from the array [100, 0]; a rule that refuses every non-string attribute value contradicts this must-keep-working output.",
  "tests/DOMSerializer/Nodes/OrderedListTest.php:61 requires start=\"3\" from the integer 3; only booleans are normalised today (src/Utils/HTML.php:48-58), so integers are a legitimate non-string attribute type throughout.",
  "A legitimate use needs an array attribute value: TableCell colwidth is an array by design (src/Nodes/TableCell.php:37-59). The refused shape (non-string attribute) overlaps the legitimate shape, so the rule must reject array/object rather than require string.",
  "tests/DOMParser/Marks/LinkTest.php:127-137 and tests/DOMSerializer/Marks/LinkTest.php:33,63,94,124 require every valid string href (absolute, relative, protocol-relative, mailto, ftp) to render unchanged; the rule cannot be 'refuse unusual strings'.",
  "tests/DOMSerializer/Nodes/XSSTest.php:5-19 requires string text to stay escaped, not dropped, so a refusal rule for non-string text must leave string handling byte-identical.",
  "src/Nodes/Image.php:31-41 has no URI-scheme validation at all; that is an XSS-class gap outside this CWE-241 advisory and must not be folded into the type rule, since adding it would change documented output (tests/DOMSerializer/Nodes/ImageTest.php:29)."
 ],
 "effort_minutes": 55,
 "usable": true,
 "design": {
  "traps": [
   "T1",
   "T2",
   "T3",
   "T4",
   "T5"
  ],
  "why": "Five traps, five separate fix sites and five different reasons to stop. T1 is the anchor the report names, so a solver who only patches isAllowedUri passes the visible description. T2 is the same mark's target/rel and every other extension's attributes, dismissed as 'not a URI' even though the real defect is the shared attribute serialiser at src/Utils/HTML.php:64. T3 is the coupled value: the natural over-broad fix for T2 (drop or stringify every non-string attribute) breaks colspan=\"2\" and data-colwidth=\"100,0\" and is caught by the existing TableTest, which is exactly the over-hardening failure. T4 is the text node, dismissed as 'not an attribute', and T5 is the identical escaping defect in getText(), a second implementation that a getHTML-only fix leaves open. T1 also masks T2 and T4 in a single document, so a partial solution changes which failure is observed rather than making the document safe. The mix gives three deepseek-type routes (absent protection plus a real dismissal: T2, T4, T5), one mimo-type coupled value (T3) and one advisory anchor (T1), and each site is graded separately so partial fixes are distinguishable."
 },
 "unverified": [
  "Fix commit 74bfb7be1c8c6102b240f3879b7f984a6ab87b97 is not present in this worktree (no fix.diff and no extra hunks are visible), so whether the published guard sits inside isAllowedUri or at the call site src/Marks/Link.php:77 - and therefore whether a direct isAllowedUri() call with a non-string still throws - cannot be confirmed from the pinned code.",
  "No trap was executed (no shell in this session). The crash points are inferred from PHP signatures: preg_replace accepts an array subject, so an array href survives src/Marks/Link.php:36 and throws at preg_match on :41, while an object href throws at :36; htmlentities/htmlspecialchars/join accept only strings or only arrays as declared and reject the other kind.",
  "T6 and T7 need an object-shaped attribute value (stdClass after the json round-trip at src/Core/DOMSerializer.php:393): a plain array only raises 'Array to string conversion' at src/Extensions/Color.php:43 and src/Nodes/CodeBlock.php:60, so those two traps are object-only and their real-world shape is not verified.",
  "No non-string href/target/src/text case exists anywhere in the pinned tests (grep over tests/), which is consistent with the regression test being added by the fix, but the hidden test content is unknown.",
  "The PHP runtime version of the grading image was not checked; the TypeError claims assume PHP >= 8.0 as required by composer.json:19.",
  "Whether the renderAttributes boolean normalisation at src/Utils/HTML.php:48-58 was added deliberately as non-string support is unknown; it is the only type handling in the library and is why T2 is recorded as weak rather than absent.",
  "The published fix's rejection mode (return false, which blanks the href at src/Marks/Link.php:79-81, versus sanitising the value) is unknown, so no statement is made about the exact post-fix DOM."
 ]
}
  ```
- Published fix sites:   - src/Marks/Link.php:30-42 — T1 M4 (reason to dismiss: none)
  - src/Marks/Link.php:41 — T1 M4 (reason to dismiss: none)
  - src/Marks/Link.php:77 — T1 M4 (reason to dismiss: none)
  - src/Core/DOMSerializer.php:239-252 — T1 M4 (reason to dismiss: none)
  - src/Editor.php:68-70 — T1 M4 (reason to dismiss: none)
- Uncovered routes to confirm (pattern B):   - src/Utils/HTML.php:45-69 — T2 M3 (reason to dismiss: The advisory and the fix branch name the link's URI check; target/rel are not URIs and image attributes are a different extension, so a type guard in isAllowedUri reads as the complete fix.)
  - src/Utils/HTML.php:64 — T2 M3 (reason to dismiss: The advisory and the fix branch name the link's URI check; target/rel are not URIs and image attributes are a different extension, so a type guard in isAllowedUri reads as the complete fix.)
  - src/Marks/Link.php:83 — T2 M3 (reason to dismiss: The advisory and the fix branch name the link's URI check; target/rel are not URIs and image attributes are a different extension, so a type guard in isAllowedUri reads as the complete fix.)
  - src/Core/DOMSerializer.php:277 — T2 M3 (reason to dismiss: The advisory and the fix branch name the link's URI check; target/rel are not URIs and image attributes are a different extension, so a type guard in isAllowedUri reads as the complete fix.)
  - src/Nodes/Image.php:31-41 — T2 M3 (reason to dismiss: The advisory and the fix branch name the link's URI check; target/rel are not URIs and image attributes are a different extension, so a type guard in isAllowedUri reads as the complete fix.)
  - src/Nodes/TableCell.php:51-59 — T3 M11 (reason to dismiss: colwidth is a table feature, is legitimately an array, and the link advisory names neither the table extension nor join(); the neighbouring integer colspan/rowspan/start values must keep rendering.)
  - src/Nodes/TableCell.php:31-36 — T3 M11 (reason to dismiss: colwidth is a table feature, is legitimately an array, and the link advisory names neither the table extension nor join(); the neighbouring integer colspan/rowspan/start values must keep rendering.)
  - src/Core/DOMSerializer.php:235-245 — T3 M11 (reason to dismiss: colwidth is a table feature, is legitimately an array, and the link advisory names neither the table extension nor join(); the neighbouring integer colspan/rowspan/start values must keep rendering.)
  - tests/DOMSerializer/Nodes/TableTest.php:215 — T3 M11 (reason to dismiss: colwidth is a table feature, is legitimately an array, and the link advisory names neither the table extension nor join(); the neighbouring integer colspan/rowspan/start values must keep rendering.)
  - src/Core/DOMSerializer.php:76-77 — T4 M1 (reason to dismiss: The advisory is about a link attribute; a text node has no attributes and the published guard never comes near htmlspecialchars.)
  - src/Core/DOMSerializer.php:38 — T4 M1 (reason to dismiss: The advisory is about a link attribute; a text node has no attributes and the published guard never comes near htmlspecialchars.)
  - src/Extensions/StarterKit.php:65-67 — T4 M1 (reason to dismiss: The advisory is about a link attribute; a text node has no attributes and the published guard never comes near htmlspecialchars.)
  - src/Editor.php:68-70 — T4 M1 (reason to dismiss: The advisory is about a link attribute; a text node has no attributes and the published guard never comes near htmlspecialchars.)
  - src/Core/TextSerializer.php:45-46 — T5 M2 (reason to dismiss: Every example and the advisory use getHTML(); the second serialiser behind getText() is a separate class that a fix in DOMSerializer never reaches.)
  - src/Editor.php:73-76 — T5 M2 (reason to dismiss: Every example and the advisory use getHTML(); the second serialiser behind getText() is a separate class that a fix in DOMSerializer never reaches.)
  - src/Core/DOMSerializer.php:235-241 — T6 M6 (reason to dismiss: These are style/global attributes of unrelated extensions and none of them is a URL; the href guard never sees the values the serializer hands to these callbacks.)
  - src/Extensions/Color.php:43 — T6 M6 (reason to dismiss: These are style/global attributes of unrelated extensions and none of them is a URL; the href guard never sees the values the serializer hands to these callbacks.)
  - src/Extensions/TextAlign.php:36 — T6 M6 (reason to dismiss: These are style/global attributes of unrelated extensions and none of them is a URL; the href guard never sees the values the serializer hands to these callbacks.)
  - src/Extensions/FontFamily.php:43 — T6 M6 (reason to dismiss: These are style/global attributes of unrelated extensions and none of them is a URL; the href guard never sees the values the serializer hands to these callbacks.)
  - src/Marks/Highlight.php:52 — T6 M6 (reason to dismiss: These are style/global attributes of unrelated extensions and none of them is a URL; the href guard never sees the values the serializer hands to these callbacks.)
  - src/Nodes/CodeBlock.php:51-66 — T7 M4 (reason to dismiss: The language attribute is 'rendered' => false and is read straight from the node by its own extension, so it is not part of the attribute path the advisory touches.)
  - src/Nodes/CodeBlock.php:46 — T7 M4 (reason to dismiss: The language attribute is 'rendered' => false and is read straight from the node by its own extension, so it is not part of the attribute path the advisory touches.)
  - src/Extensions/StarterKit.php:44-46 — T7 M4 (reason to dismiss: The language attribute is 'rendered' => false and is read straight from the node by its own extension, so it is not part of the attribute path the advisory touches.)
- Design plan from the lead: TRACK = STACKED (H4). Build the stacked design the reader chose: traps T1, T2, T3, T4, T5. Why: Five traps, five separate fix sites and five different reasons to stop. T1 is the anchor the report names, so a solver who only patches isAllowedUri passes the visible description. T2 is the same mark's target/rel and every other extension's attributes, dismissed as 'not a URI' even though the real defect is the shared attribute serialiser at src/Utils/HTML.php:64. T3 is the coupled value: the natural over-broad fix for T2 (drop or stringify every non-string attribute) breaks colspan="2" and data-colwidth="100,0" and is caught by the existing TableTest, which is exactly the over-hardening failure. T4 is the text node, dismissed as 'not an attribute', and T5 is the identical escaping defect in getText(), a second implementation that a getHTML-only fix leaves open. T1 also masks T2 and T4 in a single document, so a partial solution changes which failure is observed rather than making the document safe. The mix gives three deepseek-type routes (absent protection plus a real dismissal: T2, T4, T5), one mimo-type coupled value (T3) and one advisory anchor (T1), and each site is graded separately so partial fixes are distinguishable. Follow the stacked-task rules appended at the end of this prompt; they add to the rules above.
- Host notes: Reader fairness risks (resolve each in the report's contracts or the tests): tests/DOMSerializer/Nodes/TableTest.php:215 requires colspan="2" built from the integer 2 and data-colwidth="100,0" built from the array [100, 0]; a rule that refuses every non-string attribute value contradicts this must-keep-working output. | tests/DOMSerializer/Nodes/OrderedListTest.php:61 requires start="3" from the integer 3; only booleans are normalised today (src/Utils/HTML.php:48-58), so integers are a legitimate non-string attribute type throughout. | A legitimate use needs an array attribute value: TableCell colwidth is an array by design (src/Nodes/TableCell.php:37-59). The refused shape (non-string attribute) overlaps the legitimate shape, so the rule must reject array/object rather than require string. | tests/DOMParser/Marks/LinkTest.php:127-137 and tests/DOMSerializer/Marks/LinkTest.php:33,63,94,124 require every valid string href (absolute, relative, protocol-relative, mailto, ftp) to render unchanged; the rule cannot be 'refuse unusual strings'. | tests/DOMSerializer/Nodes/XSSTest.php:5-19 requires string text to stay escaped, not dropped, so a refusal rule for non-string text must leave string handling byte-identical. | src/Nodes/Image.php:31-41 has no URI-scheme validation at all; that is an XSS-class gap outside this CWE-241 advisory and must not be folded into the type rule, since adding it would change documented output (tests/DOMSerializer/Nodes/ImageTest.php:29).. Conflicts the reader found: The attractive fix for T2 - normalise or drop every non-string attribute, either in DOMSerializer::renderOpeningTag:236 before the renderHTML callbacks or as a blanket is_string filter at src/Utils/HTML.php:63 - breaks T3's must-keep-working output: TableCell's colwidth would arrive at its join() callback as a string (src/Nodes/TableCell.php:57) and integer colspan/rowspan/start would be dropped, contradicting tests/DOMSerializer/Nodes/TableTest.php:215 and tests/DOMSerializer/Nodes/OrderedListTest.php:61. | A producer-side normalisation that keeps arrays (needed by T3) still lets those arrays reach the style interpolations (T6), where PHP silently turns an array into 'Array' instead of rejecting it, so T6's fix has to be a rejection at the callback and not the same coercion T3 requires.

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

## Environment (`tasks/stk-tiptap-php-31762/environment/Dockerfile`)
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

## Report to the solver (`tasks/stk-tiptap-php-31762/instruction.md`)
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

## Tests (`tasks/stk-tiptap-php-31762/tests/`)
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
- **Wrong-fix patches** go in `build/stk-tiptap-php-31762/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/stk-tiptap-php-31762/`:**
- `instruction.md`;
- `task.toml`, from `common/builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/stk-tiptap-php-31762/manifest.json`:**
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

**Also in `build/stk-tiptap-php-31762/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `common/builder/templates/` and `common/trial/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I common/gate/gate.py stk-tiptap-php-31762 --only static
python3 -I common/gate/gate.py stk-tiptap-php-31762 --only nop
python3 -I common/gate/gate.py stk-tiptap-php-31762 --only oracle
python3 -I common/gate/gate.py stk-tiptap-php-31762 --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/stk-tiptap-php-31762/`;
  - edit only `tasks/stk-tiptap-php-31762/`, `build/stk-tiptap-php-31762/` and, for pattern B, the register;
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
is missing. The reader's record lists them, with evidence: `/home/mara/cwe-bench/pipelines/stacking/out/reader/h4-31762.json`. Verify each trap on the
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

Stacked task slug: `stk-tiptap-php-31762`. Control task slug: `stk-tiptap-php-31762-control`. Manifest `stacking.reader_record`: `pipelines/stacking/out/reader/h4-31762.json`.
