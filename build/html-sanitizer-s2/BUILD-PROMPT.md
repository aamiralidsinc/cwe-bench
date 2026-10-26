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

Project root: `/home/mara/cwe-bench`. Task: `html-sanitizer-s2`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: ["GHSA-JVF5-RXVV-3MCG", "CVE-2026-47344"]; typo3/html-sanitizer; mutation XSS / parser differential on raw-text (RAWTEXT) delimitation (CWE-79)
- Pinned (vulnerable) commit: 988caa31b5fa0dbe17a8331bfa3245898a650d88. Published fix: bd1a88d9b5a5f67f1120ec41084e9c1a0675641c.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v2",
 "model": "deepseek-flash",
 "entry_id": "35192",
 "advisory_ids": [
  "GHSA-JVF5-RXVV-3MCG",
  "CVE-2026-47344"
 ],
 "repo": "typo3/html-sanitizer",
 "pinned_commit": "988caa31b5fa0dbe17a8331bfa3245898a650d88",
 "fix_commits": [
  "bd1a88d9b5a5f67f1120ec41084e9c1a0675641c"
 ],
 "trust_decision": {
  "summary": "Whether an element's character data may be echoed without encoding is decided only by the tag flag check in Rules::shallAllowInsecureRawText(), which trusts the raw-text boundaries the parser produced; the parser leaves whitespace-form end tags and noscript-nested raw text inside the element, so the check approves text that the browser will tokenize as live markup.",
  "evidence": [
   "src/Serializer/Rules.php:198-205",
   "src/Serializer/Rules.php:133-146",
   "src/Serializer/Rules.php:152-165",
   "src/Behavior/Tag.php:48",
   "src/Sanitizer.php:95-98",
   "src/Sanitizer.php:112-116",
   "src/Sanitizer.php:199-202"
  ]
 },
 "landing_point": {
  "where": "src/Serializer/Rules.php:198-205",
  "why": "The advisory/fix title names ALLOW_INSECURE_RAW_TEXT, whose only consumer is shallAllowInsecureRawText(); an engineer greps the flag (defined at src/Behavior/Tag.php:48, used in tests/ScenarioTest.php:455-463) and lands on the serializer gate, not on the tokenizer."
 },
 "fix_sites": [
  {
   "where": "src/Parser/Tokenizer.php (new file, fix.diff:76-150)",
   "entry_point": "Sanitizer::sanitize() (src/Sanitizer.php:83-93) -> Sanitizer::parse() (src/Sanitizer.php:95-98) -> parseFragment() on the parser built by createParser() (src/Sanitizer.php:199-202)",
   "module_kind": "new parser module: subclass of the vendor Tokenizer overriding rawText()"
  },
  {
   "where": "src/Parser/Html5.php (new file, fix.diff:37-74)",
   "entry_point": "Sanitizer::sanitize() via parseFragment(); additionally the public whole-document parse() (fix.diff:40-56), which no in-package caller uses",
   "module_kind": "new parser module: subclass of Masterminds\\HTML5 wiring the local Tokenizer into both parse() and parseFragment()"
  },
  {
   "where": "src/Sanitizer.php:20,199-202",
   "entry_point": "Sanitizer::__construct() (src/Sanitizer.php:76-81) for every Sanitizer::sanitize() call",
   "module_kind": "core service / parser factory"
  },
  {
   "where": "src/Serializer/Rules.php:198-205",
   "entry_point": "Sanitizer::sanitize() -> serialize() (src/Sanitizer.php:112-116); also the public Serializer\\Rules API (Rules::create() src/Serializer/Rules.php:59-65, traverse() 98-105)",
   "module_kind": "serializer output rules: context check denying ALLOW_INSECURE_RAW_TEXT under <noscript>"
  },
  {
   "where": "src/Serializer/Rules.php:152-165",
   "entry_point": "Masterminds Traverser walking text nodes (Rules::traverse() src/Serializer/Rules.php:98-105)",
   "module_kind": "serializer text writer (redundant isRawText() disjunct dropped; no behaviour change)"
  }
 ],
 "O1_entry_points": 2,
 "O2_out_of_scope_site": {
  "kind": "second_implementation",
  "where": "src/Sanitizer.php:199-202"
 },
 "O3_reason_to_dismiss": "The tokenizer that mis-parses </style\\t> is third-party code (composer.json:19 requires masterminds/html5 ^2.7.6), so the end-tag handling is an upstream parse bug and the local fix belongs in the serializer that echoes the text; and the whole-document parse() method the fix also overrides has no caller inside the package, so overriding only parseFragment() looks sufficient.",
 "O4_distance": {
  "files": 4,
  "packages": 3,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "ALLOW_INSECURE_RAW_TEXT must keep working for declared tags: <script type=\"application/ld+json\"> bodies and <iframe>/<style> raw content are emitted unencoded by design, so an over-broad fix that encodes all raw-text output in Rules::element()/text() breaks the JSON-LD script feature and the iframe raw-text expectation.",
  "where": "src/Serializer/Rules.php:133-146; tests/ScenarioTest.php:446-448 and tests/ScenarioTest.php:455-463"
 },
 "O6_input_shapes": [
  "raw-text end tag with whitespace before '>' (</style\\t>) instead of the exact </style> the old tokenizer searched for (fix.diff:249-258)",
  "nested raw-text elements, e.g. <iframe><style></iframe>...</style></iframe> (fix.diff:260-269)",
  "a raw-text element nested inside <noscript>, where the browser's raw-text mode for noscript (scripting on/off) re-delimits the output (fix.diff:271-280)",
  "the same payloads under both the default encoding behaviour and an ALLOW_INSECURE_RAW_TEXT behaviour (fix.diff:250-258), i.e. the shape pair decides whether the payload is loud or silent"
 ],
 "O7_producer": {
  "kind": "serializer",
  "where": "The DOM text nodes that Rules writes raw are produced one layer earlier by the parser (src/Sanitizer.php:95-98 -> parseFragment()) and consumed at serialization (src/Sanitizer.php:112-116); the gate at src/Serializer/Rules.php:198-205 inspects only the tag flag and never re-checks how the text was delimited by the tokenizer.",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "A raw-text element whose ancestor is <svg> or <math> is still emitted unencoded when its Behavior declares ALLOW_INSECURE_RAW_TEXT: the fix's new ancestor check knows only 'noscript', while browsers tokenize foreign content without RAWTEXT, so <svg><style><img src=x onerror=...></style></svg> comes out with the text as live markup (style is RAWTEXT only in the HTML insertion modes).",
   "where": "src/Serializer/Rules.php:120-150,198-205 (the only context guard the fix adds is hasAncestorWithName(...,'noscript'); svg/math are special-cased for the element itself at 126-128, not for raw-text descendants)",
   "reason_to_dismiss": "svg/math are already special-cased at src/Serializer/Rules.php:126-128 and the advisory is explicitly about noscript and whitespace end tags, so ALLOW_INSECURE_RAW_TEXT inside SVG reads as an unsupported combination rather than part of the same protection.",
   "distance": "same file as the fix's second hunk (Rules.php), but the mechanism it depends on is the parse/serialise split introduced in src/Sanitizer.php:95-98 and src/Parser/ (0 files from the landing point, 1 layer away in the parser)",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "Callers that build the DOM with their own Masterminds\\HTML5 and serialize through the public Serializer\\Rules API (Rules::create()/traverse()) still get the whitespace end-tag bypass, because the tokenizer substitution lives only in the protected Sanitizer::createParser(); the noscript half of the fix applies to Rules but the parse half does not.",
   "where": "src/Serializer/Rules.php:59-65,98-105 (public factory + traverse on a caller-supplied DOM), src/Sanitizer.php:199-202 (protected factory, the only place the fixed parser is installed)",
   "reason_to_dismiss": "Rules is only the output side; the caller owns parsing, so the package cannot be blamed for a DOM built by someone else's parser and the advisory is about Sanitizer::sanitize().",
   "distance": "0 files from the landing point (src/Serializer/Rules.php) but one layer away in src/Sanitizer.php:199-202, which is protected and therefore not reachable by a composing caller",
   "present_in_latest": "unknown",
   "latest_where": ""
  }
 ],
 "O8b_injection_room": [
  {
   "where": "src/Serializer/Rules.php:198-205",
   "sibling": "A second context rule beside the noscript one, denying ALLOW_INSECURE_RAW_TEXT for raw-text elements under svg/math (or under any non-HTML integration-point ancestor)",
   "why_realistic": "The fix itself establishes the pattern 'a raw-text element in context X is denied'; a maintainer following up on foreign-content mXSS would add exactly one more hasAncestorWithName() call here, and the svg/math special case three lines above (Rules.php:126-128) shows the file already reasons about foreign content."
  },
  {
   "where": "src/Serializer/Rules.php:207-212",
   "sibling": "A raw-text element set that differs from Elements::TEXT_RAW (e.g. treating noscript or plaintext as raw text only in the contexts where browsers do)",
   "why_realistic": "isRawText() is the single name-based oracle the whole gate depends on; adding or narrowing one element here changes the behaviour of every raw-text element and is the natural place for a maintainer to chase the next parser differential."
  },
  {
   "where": "src/Visitor/CommonVisitor.php:284",
   "sibling": "A second serialization route via Masterminds' own saveHTML() (also used at src/Behavior/Handler/AsTextHandler.php:31) that would need the same encoding/context rules applied",
   "why_realistic": "convertToText() already stringifies a node with the vendor serializer and stores the markup as a text node; if that node lands in a raw-text parent, Rules writes it back out unencoded, so a maintainer hardening raw text would naturally have to route this path through the same decision."
  }
 ],
 "O9_family": "mutation XSS / parser differential on raw-text (RAWTEXT) delimitation (CWE-79)",
 "O9_dos": false,
 "O10_build": {
  "language": "PHP",
  "toolchain": "PHP ^7.2 || ^8.0 with ext-dom, Composer; composer.json:17-25 requires masterminds/html5 ^2.7.6, psr/log ^1-^3 and phpunit ^8.5 (dev); phpunit.xml bootstraps vendor/autoload.php; vendor/ is NOT present in the screened tree, so one `composer install` is needed before tests run",
  "services": [],
  "offline_after_build": true,
  "project_tests": "PHPUnit suite in tests/ (phpunit.xml:10-13): tests/ScenarioTest.php:373-411 rawTextElementsAreHandled (every Elements::TEXT_RAW element), tests/ScenarioTest.php:617-639 specialTagsAreHandled incl. 'noscript raw text' at 631-634, tests/ScenarioTest.php:416-471 isJsonLdScriptAllowed for the legitimate ALLOW_INSECURE_RAW_TEXT output; plus tests/CommonBuilderTest.php, tests/Behavior/TagTest.php, tests/Behavior/AttrTest.php, tests/BehaviorTest.php, tests/EnvironmentTest.php"
 },
 "O11_fix_minutes": 45,
 "O12_red_flags": [
  "tiny_repo"
 ],
 "O13_recall_risk": "medium",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "src/Parser/Tokenizer.php, src/Parser/Html5.php, src/Sanitizer.php, src/Serializer/Rules.php",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 0,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Encode every raw-text child in Rules::element()/text() (or drop ALLOW_INSECURE_RAW_TEXT output entirely), which silences the payload but breaks the JSON-LD <script> and <iframe> raw output and never fixes the tokenizer's end-tag boundary."
 },
 "out_of_scope_notes": [
  "src/Visitor/CommonVisitor.php:284 and src/Behavior/Handler/AsTextHandler.php:31 stringify nodes with Masterminds' own saveHTML(), a serializer that applies none of Rules' decisions; noted, not pursued.",
  "<script> data-state escaping (<!-- and </script> inside strings) is a separate parser differential from this advisory's raw-text end-tag and noscript property; not pursued."
 ],
 "unverified": [
  "vendor/ (masterminds/html5 ^2.7.6) is absent from the screened tree, so the original Tokenizer::rawText() body, Elements::$html5 flags for noscript/style/iframe, and the parser's foreign-content behaviour for <svg><style> could not be read; the svg/math O8 route is inferred from the fix's own comment (fix.diff:116-118) and the HTML spec, and should be confirmed against the installed vendor tree before it is used as a hidden test.",
  "present_in_latest for both O8 routes is unknown: the inputs give 'latest release: none' and only the pinned tree plus the fix diff were available.",
  "repo_mb is null (no shell available); tiny_repo is flagged from the tree itself, which is ~31 PHP files plus composer.json/phpunit.xml/docs and no other assets.",
  "Whether any consumer calls the new Parser\\Html5::parse() (whole-document) path: no in-package caller exists, and out-of-package consumers cannot be inspected.",
  "O1=2 counts Sanitizer::sanitize() and the public Serializer\\Rules::create()/traverse() API; only the former is exercised by the project's own tests."
 ]
}
  ```
- Published fix sites:   - src/Parser/Tokenizer.php (new file, fix.diff:76-150) — entry point: Sanitizer::sanitize() (src/Sanitizer.php:83-93) -> Sanitizer::parse() (src/Sanitizer.php:95-98) -> parseFragment() on the parser built by createParser() (src/Sanitizer.php:199-202) [new parser module: subclass of the vendor Tokenizer overriding rawText()]
  - src/Parser/Html5.php (new file, fix.diff:37-74) — entry point: Sanitizer::sanitize() via parseFragment(); additionally the public whole-document parse() (fix.diff:40-56), which no in-package caller uses [new parser module: subclass of Masterminds\HTML5 wiring the local Tokenizer into both parse() and parseFragment()]
  - src/Sanitizer.php:20,199-202 — entry point: Sanitizer::__construct() (src/Sanitizer.php:76-81) for every Sanitizer::sanitize() call [core service / parser factory]
  - src/Serializer/Rules.php:198-205 — entry point: Sanitizer::sanitize() -> serialize() (src/Sanitizer.php:112-116); also the public Serializer\Rules API (Rules::create() src/Serializer/Rules.php:59-65, traverse() 98-105) [serializer output rules: context check denying ALLOW_INSECURE_RAW_TEXT under <noscript>]
  - src/Serializer/Rules.php:152-165 — entry point: Masterminds Traverser walking text nodes (Rules::traverse() src/Serializer/Rules.php:98-105) [serializer text writer (redundant isRawText() disjunct dropped; no behaviour change)]
- Uncovered routes to confirm (pattern B):   - src/Serializer/Rules.php:120-150,198-205 (the only context guard the fix adds is hasAncestorWithName(...,'noscript'); svg/math are special-cased for the element itself at 126-128, not for raw-text descendants) — A raw-text element whose ancestor is <svg> or <math> is still emitted unencoded when its Behavior declares ALLOW_INSECURE_RAW_TEXT: the fix's new ancestor check knows only 'noscript', while browsers tokenize foreign content without RAWTEXT, so <svg><style><img src=x onerror=...></style></svg> comes out with the text as live markup (style is RAWTEXT only in the HTML insertion modes). (reason to dismiss: svg/math are already special-cased at src/Serializer/Rules.php:126-128 and the advisory is explicitly about noscript and whitespace end tags, so ALLOW_INSECURE_RAW_TEXT inside SVG reads as an unsupported combination rather than part of the same protection.; still in latest: unknown)
  - src/Serializer/Rules.php:59-65,98-105 (public factory + traverse on a caller-supplied DOM), src/Sanitizer.php:199-202 (protected factory, the only place the fixed parser is installed) — Callers that build the DOM with their own Masterminds\HTML5 and serialize through the public Serializer\Rules API (Rules::create()/traverse()) still get the whitespace end-tag bypass, because the tokenizer substitution lives only in the protected Sanitizer::createParser(); the noscript half of the fix applies to Rules but the parse half does not. (reason to dismiss: Rules is only the output side; the caller owns parsing, so the package cannot be blamed for a DOM built by someone else's parser and the advisory is about Sanitizer::sanitize().; still in latest: unknown)
- Design plan from the lead: No lead plan is provided for this task — you are the lead as well as the builder. Using the Design section above and the screener record, design the task yourself and WRITE YOUR PLAN in `notes.md` BEFORE you build:
  - choose the main lever and at least one more, each with a DIFFERENT reason a solver would dismiss or skip it. The main lever must be HOW-type (its fix needs the mechanism understood: a producer the check never calls, a coupled must-keep-working value, a shape a plausible check mishandles, a route where the protection never existed); another entry point or a planted copy is only an extra;
  - decide the sites, routes and input shapes the security tests will cover;
  - identify the coupled must-keep-working behaviour next to each lever, for the functional tests;
  - for the injected track: decide the realistic sibling gap(s) to add — each must be code a maintainer could plausibly have left, reachable through the real entry point, covered by the task's one general property (never by a sentence of its own), and placed where the published fix never touches. First list EVERY possible sibling site and route you can find (the screener's O8/O8b leads plus your own search of the code). Then pick 2–4 of them: the most complex and hardest to find of all the candidates (how-type over where-type, far from where the report leads, with a plausible reason to dismiss), each with a different reason a solver would skip it. Record the full candidate list, and why each pick beat the others, in notes.md;
  - write the security property ONCE, in general terms over the protected data or outcome, before choosing routes. Every route and sibling must fall under it as written; the report must not describe where any of them lives;
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

## Environment (`tasks/html-sanitizer-s2/environment/Dockerfile`)
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

## Report to the solver (`tasks/html-sanitizer-s2/instruction.md`)
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

## Tests (`tasks/html-sanitizer-s2/tests/`)
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
- **Wrong-fix patches** go in `build/html-sanitizer-s2/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/html-sanitizer-s2/`:**
- `instruction.md`;
- `task.toml`, from `common/builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/html-sanitizer-s2/manifest.json`:**
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

**Also in `build/html-sanitizer-s2/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `common/builder/templates/` and `common/trial/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I common/gate/gate.py html-sanitizer-s2 --only static
python3 -I common/gate/gate.py html-sanitizer-s2 --only nop
python3 -I common/gate/gate.py html-sanitizer-s2 --only oracle
python3 -I common/gate/gate.py html-sanitizer-s2 --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/html-sanitizer-s2/`;
  - edit only `tasks/html-sanitizer-s2/`, `build/html-sanitizer-s2/` and, for pattern B, the register;
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
