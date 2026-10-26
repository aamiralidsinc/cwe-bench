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

Project root: `/home/mara/cwe-bench`. Task: `schema-org-s2`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: ["GHSA-HWMC-R6MF-JH83"]; spatie/schema-org; CWE-79 cross-site scripting - HTML script-context injection in generated ld+json output
- Pinned (vulnerable) commit: 8833f42996208e50488e6547e7102166c0331dd9. Published fix: be389b4759214c11cc1364a16e34a929c5af5a88.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v2",
 "model": "deepseek-flash[1m]",
 "entry_id": "34875",
 "advisory_ids": [
  "GHSA-HWMC-R6MF-JH83"
 ],
 "repo": "spatie/schema-org",
 "pinned_commit": "8833f42996208e50488e6547e7102166c0331dd9",
 "fix_commits": [
  "be389b4759214c11cc1364a16e34a929c5af5a88"
 ],
 "trust_decision": {
  "summary": "The decision 'is this JSON safe to embed inside a <script> element' is taken at output-encoding time, once per toScript() implementation: src/BaseType.php:163, src/Graph.php:1211 and src/MultiTypedEntity.php:1098 all json_encode with JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES only, so a '</script>' inside any property value terminates the element; the same three encoders are duplicated verbatim in the code-generator that writes src/ (generator/templates/static/BaseType.php:163, generator/templates/twig/Graph.php.twig:301, generator/templates/twig/MultiTypedEntity.php.twig:188).",
  "evidence": [
   "src/BaseType.php:163",
   "src/Graph.php:1211",
   "src/MultiTypedEntity.php:1098",
   "generator/templates/static/BaseType.php:163",
   "generator/templates/twig/Graph.php.twig:301",
   "generator/templates/twig/MultiTypedEntity.php.twig:188",
   "src/BaseType.php:113-137"
  ]
 },
 "landing_point": {
  "where": "src/BaseType.php:163",
  "why": "Every one of the ~1,600 generated types inherits toScript() from this abstract base (src/BaseType.php:12), and the advisory summary names toScript() output, so a reader who read only the summary opens BaseType first."
 },
 "fix_sites": [
  {
   "where": "src/BaseType.php:163",
   "entry_point": "BaseType::toScript() (also via __toString at src/BaseType.php:176-179, and via ReferencedType::toScript()/__toString() which delegate at src/ReferencedType.php:39-52); reached from every generated type, e.g. Schema::localBusiness()->toScript()",
   "module_kind": "public library API (abstract base class of all schema types)"
  },
  {
   "where": "src/Graph.php:1211",
   "entry_point": "Graph::toScript() and (string) $graph (__toString at src/Graph.php:1219-1222)",
   "module_kind": "public library API (independent @graph document builder)"
  },
  {
   "where": "src/MultiTypedEntity.php:1098",
   "entry_point": "MultiTypedEntity::toScript() and (string) $entity (__toString at src/MultiTypedEntity.php:1106-1109)",
   "module_kind": "public library API (independent multi-@type entity wrapper)"
  },
  {
   "where": "generator/templates/static/BaseType.php:163",
   "entry_point": "composer generate / php generate.php -> GenerateCommand -> PackageGenerator -> Filesystem::cloneStaticFiles(), which copies this file byte-for-byte to src/BaseType.php (generator/Writer/Filesystem.php:48-62)",
   "module_kind": "dev-only code-generator template (autoload-dev namespace Spatie\\SchemaOrg\\Generator)"
  },
  {
   "where": "generator/templates/twig/Graph.php.twig:301",
   "entry_point": "composer generate -> Filesystem::createBuilderClass() renders this Twig template into src/Graph.php (generator/Writer/Filesystem.php:84-87)",
   "module_kind": "dev-only code-generator Twig template"
  },
  {
   "where": "generator/templates/twig/MultiTypedEntity.php.twig:188",
   "entry_point": "composer generate -> Filesystem::createBuilderClass() renders this Twig template into src/MultiTypedEntity.php (generator/Writer/Filesystem.php:89-92)",
   "module_kind": "dev-only code-generator Twig template"
  }
 ],
 "O1_entry_points": 3,
 "O2_out_of_scope_site": {
  "kind": "second_implementation",
  "where": "generator/templates/static/BaseType.php:163 (plus generator/templates/twig/Graph.php.twig:301 and generator/templates/twig/MultiTypedEntity.php.twig:188) - a second, dev-only copy of the same encoders that is the real source of src/BaseType.php, src/Graph.php and src/MultiTypedEntity.php"
 },
 "O3_reason_to_dismiss": "generator/ is maintainer-only tooling loaded through autoload-dev and only runs on `composer generate`, so a solver can argue the shipped runtime is fixed once src/ is patched and the template copies are not part of the published surface.",
 "O4_distance": {
  "files": 3,
  "packages": 1,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "toArray()/jsonSerialize() (and therefore json_encode($type), documented in README.md:100-104) must keep returning raw, unescaped values with unescaped slashes and unicode; only the <script> embedding may escape. An over-broad fix that escapes in setProperty()/serializeProperty()/toArray() breaks API consumers and the existing expectation that json_encode($type) equals json_encode($expected) with literal '<'/'>' values, and HTML-escaping the whole encoded body would also break the URL expectations in GraphTest.php:219-220.",
  "where": "src/BaseType.php:102-137"
 },
 "O6_input_shapes": [
  "plain string property value containing </script>",
  "value inside a nested child Type (serialized through serializeProperty)",
  "array-valued property / array of strings",
  "@id (identifier) value",
  "node value inside Graph and inside MultiTypedEntity",
  "case and padding variants such as </SCRIPT > and the HTML comment opener <!-- (JSON_HEX_TAG escapes every < and > regardless of case, so the flag covers them)"
 ],
 "O7_producer": {
  "kind": "schema",
  "where": "generator/Writer/Filesystem.php:48-93 - cloneStaticFiles() copies generator/templates/static/* into src/ and createBuilderClass() renders the Graph/MultiTypedEntity Twig templates into src/, i.e. this builder produces the very classes the hidden check exercises",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "toScript() assembles the whole <script ...> tag from nonceAttr(), which interpolates the value stored by the public BaseType::setNonce() (src/BaseType.php:57-62) into a double-quoted attribute without escaping; a quote breaks out of the attribute and a following </script> closes the element, so the tag is still injection-prone even after the JSON body is hex-escaped.",
   "where": "src/BaseType.php:150-159",
   "reason_to_dismiss": "nonce is a server-side CSP token configured by the developer, not untrusted schema content, and the advisory text only describes script break-out from property values.",
   "distance": "same file, 4 lines above the fixed line",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "Graph::nonceAttr() builds the same script-tag attribute from the value stored by Graph::setNonce() (src/Graph.php:1137) with no escaping.",
   "where": "src/Graph.php:1198-1207",
   "reason_to_dismiss": "same argument: the nonce is developer-supplied CSP configuration rather than attacker-controlled schema data.",
   "distance": "same file, 4 lines above the fixed line",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "MultiTypedEntity::nonceAttr() builds the same script-tag attribute from the value stored by MultiTypedEntity::setNonce() (src/MultiTypedEntity.php:1010) with no escaping.",
   "where": "src/MultiTypedEntity.php:1085-1094",
   "reason_to_dismiss": "same argument: the nonce is developer-supplied CSP configuration rather than attacker-controlled schema data.",
   "distance": "same file, 4 lines above the fixed line",
   "present_in_latest": "unknown",
   "latest_where": ""
  }
 ],
 "O8b_injection_room": [
  {
   "where": "src/ReferencedType.php:39-42",
   "sibling": "a ReferencedType::toScript() that builds its own <script> tag instead of delegating to $this->type->toScript()",
   "why_realistic": "ReferencedType already re-implements toArray()/jsonSerialize()/__toString() for the wrapper case and was touched recently for @id resolution (commit c6b3d4d, CHANGELOG.md:9), so a maintainer working there could plausibly emit the tag itself and copy the encoder call without the HEX_TAG flag."
  },
  {
   "where": "src/BaseType.php:150-159",
   "sibling": "an attribute-escaping helper shared by nonceAttr() in the three tag-building classes",
   "why_realistic": "the nonce attribute is constructed in the same small method family as toScript() and was originally written with the same trust assumption; a maintainer adding any further tag attribute (nonce, id, data-*) would add it here."
  },
  {
   "where": "generator/templates/twig/Graph.php.twig:299-303",
   "sibling": "a fourth generated class with its own toScript(), e.g. an ItemList/Payload builder template",
   "why_realistic": "every script-tag-emitting class in src/ comes from a template and Filesystem::createBuilderClass() already emits three of them (generator/Writer/Filesystem.php:77-93); adding one more template adds another unescaped copy that the runtime tests never touch."
  }
 ],
 "O9_family": "CWE-79 cross-site scripting - HTML script-context injection in generated ld+json output",
 "O9_dos": false,
 "O10_build": {
  "language": "PHP",
  "toolchain": "Composer; php ^8.2 with ext-json; dev: pestphp/pest ^2.36 || ^3.0, twig/twig ^3.21, symfony/console ^6||^7, league/flysystem ^3, illuminate/collections ^10, friendsofphp/php-cs-fixer, graham-campbell/analyzer",
  "services": [],
  "offline_after_build": true,
  "project_tests": "Pest tests in tests/: BaseTypeTest.php (ld+json script tag, nonce attribute, toArray/json_encode expectations), GraphTest.php, MultiTypedEntityTest.php, GraphIdentifierTest.php, GeneratedTypeSmokeTest.php, AnalysisTest.php; run with vendor/bin/pest. No test covers generator/templates, and the generator itself is not exercised by the suite."
 },
 "O11_fix_minutes": 20,
 "O12_red_flags": [],
 "O13_recall_risk": "low",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "src/BaseType.php, src/Graph.php, src/MultiTypedEntity.php, generator/templates/static/BaseType.php, generator/templates/twig/Graph.php.twig, generator/templates/twig/MultiTypedEntity.php.twig",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 0,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Add JSON_HEX_TAG to src/BaseType::toScript() only (the class the report's example exercises), or string-replace '</script' in the encoded body instead of changing the encoder flags."
 },
 "out_of_scope_notes": [
  "Nothing beyond this advisory's own protection was pursued; the nonce-attribute routes (O8) are reported as the same toScript() sink rather than as a separate advisory.",
  "Generator regeneration (composer generate) fetches the schema.org JSON-LD release from raw.githubusercontent.com unless --local is used with a cache in generator/temp, which is gitignored and empty at the pinned commit."
 ],
 "unverified": [
  "Repo size in MB could not be measured without a shell; the tree holds 1,872 PHP files including ~1,600 generated type classes and 913 contract interfaces, so it is clearly above 5 MB and far below 1.5 GB, but the exact figure is unknown.",
  "Whether the O8 nonce route falls inside the advisory's published scope is a judgement call: it is the same toScript() <script> tag, but an attribute-context break-out rather than a script-element break-out.",
  "No latest release was supplied for this candidate, so present_in_latest for the O8 routes is unknown.",
  "Not verified whether the hidden suite can exercise generator/templates offline; the static template could be loaded after renaming its class, but the project ships no such test and Twig rendering of the builder templates needs a fabricated type collection."
 ]
}
  ```
- Published fix sites:   - src/BaseType.php:163 — entry point: BaseType::toScript() (also via __toString at src/BaseType.php:176-179, and via ReferencedType::toScript()/__toString() which delegate at src/ReferencedType.php:39-52); reached from every generated type, e.g. Schema::localBusiness()->toScript() [public library API (abstract base class of all schema types)]
  - src/Graph.php:1211 — entry point: Graph::toScript() and (string) $graph (__toString at src/Graph.php:1219-1222) [public library API (independent @graph document builder)]
  - src/MultiTypedEntity.php:1098 — entry point: MultiTypedEntity::toScript() and (string) $entity (__toString at src/MultiTypedEntity.php:1106-1109) [public library API (independent multi-@type entity wrapper)]
  - generator/templates/static/BaseType.php:163 — entry point: composer generate / php generate.php -> GenerateCommand -> PackageGenerator -> Filesystem::cloneStaticFiles(), which copies this file byte-for-byte to src/BaseType.php (generator/Writer/Filesystem.php:48-62) [dev-only code-generator template (autoload-dev namespace Spatie\SchemaOrg\Generator)]
  - generator/templates/twig/Graph.php.twig:301 — entry point: composer generate -> Filesystem::createBuilderClass() renders this Twig template into src/Graph.php (generator/Writer/Filesystem.php:84-87) [dev-only code-generator Twig template]
  - generator/templates/twig/MultiTypedEntity.php.twig:188 — entry point: composer generate -> Filesystem::createBuilderClass() renders this Twig template into src/MultiTypedEntity.php (generator/Writer/Filesystem.php:89-92) [dev-only code-generator Twig template]
- Uncovered routes to confirm (pattern B):   - src/BaseType.php:150-159 — toScript() assembles the whole <script ...> tag from nonceAttr(), which interpolates the value stored by the public BaseType::setNonce() (src/BaseType.php:57-62) into a double-quoted attribute without escaping; a quote breaks out of the attribute and a following </script> closes the element, so the tag is still injection-prone even after the JSON body is hex-escaped. (reason to dismiss: nonce is a server-side CSP token configured by the developer, not untrusted schema content, and the advisory text only describes script break-out from property values.; still in latest: unknown)
  - src/Graph.php:1198-1207 — Graph::nonceAttr() builds the same script-tag attribute from the value stored by Graph::setNonce() (src/Graph.php:1137) with no escaping. (reason to dismiss: same argument: the nonce is developer-supplied CSP configuration rather than attacker-controlled schema data.; still in latest: unknown)
  - src/MultiTypedEntity.php:1085-1094 — MultiTypedEntity::nonceAttr() builds the same script-tag attribute from the value stored by MultiTypedEntity::setNonce() (src/MultiTypedEntity.php:1010) with no escaping. (reason to dismiss: same argument: the nonce is developer-supplied CSP configuration rather than attacker-controlled schema data.; still in latest: unknown)
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

## Environment (`tasks/schema-org-s2/environment/Dockerfile`)
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

## Report to the solver (`tasks/schema-org-s2/instruction.md`)
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

## Tests (`tasks/schema-org-s2/tests/`)
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
- **Wrong-fix patches** go in `build/schema-org-s2/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/schema-org-s2/`:**
- `instruction.md`;
- `task.toml`, from `common/builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/schema-org-s2/manifest.json`:**
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

**Also in `build/schema-org-s2/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `common/builder/templates/` and `common/trial/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I common/gate/gate.py schema-org-s2 --only static
python3 -I common/gate/gate.py schema-org-s2 --only nop
python3 -I common/gate/gate.py schema-org-s2 --only oracle
python3 -I common/gate/gate.py schema-org-s2 --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/schema-org-s2/`;
  - edit only `tasks/schema-org-s2/`, `build/schema-org-s2/` and, for pattern B, the register;
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
