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

Project root: `/home/mara/cwe-bench`. Task: `grav-ds`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: ["GHSA-MC5Q-6HPJ-RP7J", "CVE-2026-61450", "CVE-2026-61842"]; getgrav/grav; CWE-200 information exposure via sandbox escape: the template sandbox's member allowlist is bypassed by PHP-side serializers/reflective dumpers and by a container accessor
- Pinned (vulnerable) commit: parent of 7efe70574e4cf01a251318478c13673029e93eb6 (parent_commit not given in candidate). Published fix: 7efe70574e4cf01a251318478c13673029e93eb6.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "35371",
 "advisory_ids": [
  "GHSA-MC5Q-6HPJ-RP7J",
  "CVE-2026-61450",
  "CVE-2026-61842"
 ],
 "repo": "getgrav/grav",
 "pinned_commit": "parent of 7efe70574e4cf01a251318478c13673029e93eb6 (parent_commit not given in candidate)",
 "fix_commits": [
  "7efe70574e4cf01a251318478c13673029e93eb6"
 ],
 "trust_decision": {
  "summary": "Editor-authored page Twig is untrusted and runs in the Twig sandbox; it may read config only through the redacting SandboxConfig facade. The sandbox member gate (GravSecurityPolicy) decides which objects and members it may touch, but PHP-side dump/serialize/cast filters read object state without going through that gate.",
  "evidence": [
   "system/src/Grav/Common/Twig/Twig.php:278-283",
   "system/src/Grav/Common/Twig/Twig.php:407-414",
   "system/src/Grav/Common/Twig/Twig.php:493-495",
   "system/src/Grav/Common/Twig/Sandbox/GravSecurityPolicy.php:65-80",
   "system/src/Grav/Common/Security.php:367-372",
   "system/config/security.yaml:334-346"
  ]
 },
 "landing_point": {
  "where": "system/src/Grav/Common/Twig/Extension/GravExtension.php:147",
  "why": "The summary names grav.offsetGet plus a dump filter; print_r is registered here and its implementation is at GravExtension.php:283-286."
 },
 "fix_sites": [
  {
   "where": "system/config/security.yaml:335-336",
   "entry_point": "Sandboxed page-content Twig member call grav.offsetGet('config') / grav.__get (HTTP page render via Twig::processPage/processString)",
   "module_kind": "defaults config (sandbox allowlist)"
  },
  {
   "where": "system/src/Grav/Common/Twig/Extension/GravExtension.php:147",
   "entry_point": "Twig filter |print_r in sandboxed page content",
   "module_kind": "Twig extension filter registration"
  },
  {
   "where": "system/src/Grav/Common/Twig/Extension/GravExtension.php:148",
   "entry_point": "Twig filter |yaml_encode in sandboxed page content",
   "module_kind": "Twig extension filter registration"
  },
  {
   "where": "system/src/Grav/Common/Twig/Extension/GravExtension.php:159",
   "entry_point": "Twig filter |string in sandboxed page content",
   "module_kind": "Twig extension filter registration"
  },
  {
   "where": "system/src/Grav/Common/Twig/Extension/GravExtension.php:198-199",
   "entry_point": "Twig functions vardump() and print_r() in sandboxed page content",
   "module_kind": "Twig extension function registration"
  },
  {
   "where": "fix.diff:59-62",
   "entry_point": "Twig core |json_encode filter (Twig CoreExtension), overridden by a guarded GravExtension filter",
   "module_kind": "second implementation (override of the vendor core filter)"
  },
  {
   "where": "fix.diff:261-270",
   "entry_point": "GravSecurityPolicy::isClassAllowed (new public API used by the guard); policy built by Security::buildTwigSandboxPolicy at system/src/Grav/Common/Security.php:300",
   "module_kind": "sandbox policy class"
  }
 ],
 "O1_entry_points": 7,
 "O2_out_of_scope_site": {
  "kind": "defaults_or_merge_route",
  "where": "system/config/security.yaml:335-336 (the Grav-class method allowlist in the shipped defaults; also the json_encode override of Twig core, fix.diff:59-62)"
 },
 "O3_reason_to_dismiss": "The allowlist in security.yaml looks like site-owner configuration, not code, and json_encode belongs to Twig core rather than Grav. Either lets a solver guard only print_r in GravExtension and stop there.",
 "O4_distance": {
  "files": 3,
  "packages": 2,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Several things must keep working. Trusted theme/plugin templates (unsandboxed) still use print_r/json_encode/yaml_encode on any object. Sandboxed content can still json_encode/print_r a page header (stdClass) and yaml_encode the redacting `config` facade. Removing these filters from the allowlist, or guarding them outside the sandbox, breaks all of that.",
  "where": "fix.diff:113-114; fix.diff:105-111; fix.diff:168-170; system/config/security.yaml:376-380"
 },
 "O6_input_shapes": [
  "a bare object (raw Config, SandboxConfig, Grav service)",
  "an array holding objects, walked recursively to depth 16 (fix.diff:149-162)",
  "a stdClass page header (allowed under the reflective tier, fix.diff:168-170)",
  "filter form vs function form (print_r filter and function, vardump function)",
  "reflective tier (print_r/vardump) vs serializing tier (json_encode/yaml_encode/string)"
 ],
 "O7_producer": {
  "kind": "config_loader",
  "where": "system/src/Grav/Common/Security.php:300-378 builds the GravSecurityPolicy from security.twig_sandbox.* and strips Config/Data when config_access is off (Security.php:367-372); isClassAllowed answers from that.",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "The Twig *function* string() is still bound to the unguarded stringFilter, which json_encodes arrays (and so calls Data::jsonSerialize on any Config inside them). The fix guarded only the same-named filter.",
   "where": "system/src/Grav/Common/Twig/Extension/GravExtension.php:213",
   "reason_to_dismiss": "The report and fix talk about filters; string() looks like a harmless scalar cast helper in the separate function list.",
   "distance": "same file, about 55 lines below the guarded filter registration; allowlisted at system/config/security.yaml:320",
   "present_in_latest": "yes",
   "latest_where": "latest/system/src/Grav/Common/Twig/Extension/GravExtension.php:232"
  },
  {
   "route": "The array filter and function call toArray() or a PHP (array) cast on any object, outside the member gate. This exposes protected/private state such as Plugin/Theme::$config or the container's service map, which a printer then outputs.",
   "where": "system/src/Grav/Common/Twig/Extension/GravExtension.php:163; system/src/Grav/Common/Twig/Extension/GravExtension.php:189; system/src/Grav/Common/Twig/Extension/GravExtension.php:911-928; system/src/Grav/Common/Plugin.php:39",
   "reason_to_dismiss": "|array is a type cast, not a dump/serialize filter, and the advisory names only offsetGet + dump.",
   "distance": "same file, different helper (arrayFilter ~600 lines from print_r); allowlisted at system/config/security.yaml:213 and :284",
   "present_in_latest": "no",
   "latest_where": "latest/system/src/Grav/Common/Twig/Extension/GravExtension.php:174; latest/system/src/Grav/Common/Twig/Extension/GravExtension.php:202; latest/system/src/Grav/Common/Twig/Extension/GravExtension.php:467-472"
  },
  {
   "route": "The yaml filter (Yaml::dump) is a second YAML printer next to yaml_encode, and the fix left it unguarded. It prints whatever array an earlier cast hands it.",
   "where": "system/src/Grav/Common/Twig/Extension/GravExtension.php:164; system/src/Grav/Common/Twig/Extension/GravExtension.php:936-939",
   "reason_to_dismiss": "The Symfony dumper refuses to serialize objects, so on its own it cannot leak an object.",
   "distance": "same file; allowlisted at system/config/security.yaml:262",
   "present_in_latest": "no",
   "latest_where": "latest/system/src/Grav/Common/Twig/Extension/GravExtension.php:175; latest/system/src/Grav/Common/Twig/Extension/GravExtension.php:489-494"
  },
  {
   "route": "The sandboxed render inherits the raw `system`, `site` and `theme` config arrays as template variables. Only `config` is replaced by the redacting facade, so json_encode/print_r on them prints unredacted config even with config_access off.",
   "where": "system/src/Grav/Common/Twig/Twig.php:298-300; system/src/Grav/Common/Twig/Twig.php:411-412; system/src/Grav/Common/Twig/Twig.php:493-495",
   "reason_to_dismiss": "These are documented standard template variables, and the default denied paths (plugins, security, ...) are not under them.",
   "distance": "other file and package (Twig.php vs Twig/Extension/GravExtension.php)",
   "present_in_latest": "no",
   "latest_where": "latest/system/src/Grav/Common/Twig/Twig.php:739-749"
  }
 ],
 "O8b_injection_room": [
  {
   "where": "system/src/Grav/Common/Twig/Extension/GravExtension.php:143",
   "sibling": "A json_decode/yaml_decode round-trip helper (e.g. a `to_json` or `pretty_json` filter) that serializes its argument with json_encode, added beside json_decode.",
   "why_realistic": "The extension already has many thin casting/serializing helpers registered in both filter and function form; a maintainer adding a pretty-print variant would reuse stringFilter-style json_encode."
  },
  {
   "where": "system/src/Grav/Common/Twig/Extension/GravExtension.php:1087-1113",
   "sibling": "dump()/debug() call toArray() on every context object and push it to the debugger; a non-debug variant could write it into page output.",
   "why_realistic": "The code already does a per-object toArray walk outside the member gate; it is only debug-gated (security.yaml:283)."
  }
 ],
 "O9_family": "CWE-200 information exposure via sandbox escape: the template sandbox's member allowlist is bypassed by PHP-side serializers/reflective dumpers and by a container accessor",
 "O9_dos": false,
 "O10_build": {
  "language": "PHP 8.3",
  "toolchain": "composer (twig/twig 3.x-dev), Codeception 5 unit tests",
  "services": [],
  "offline_after_build": true,
  "project_tests": "tests/unit/Grav/Common/Security/TwigSandboxTest.php (sandboxEnv render helper, GHSA-j274 config-exfil tests at :416-488), tests/unit/Grav/Common/Twig/Sandbox/SandboxConfigTest.php"
 },
 "O11_fix_minutes": 70,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "system/src/Grav/Common/Twig/Extension/GravExtension.php, system/src/Grav/Common/Twig/Sandbox/GravSecurityPolicy.php, system/config/security.yaml",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Drop offsetget from the Grav allowlist (or guard only print_r), and leave json_encode/yaml_encode/string, the string() function and the array cast open."
 },
 "out_of_scope_notes": [
  "The fix's serializing tier allows a raw Config through json_encode when security.twig_content.config_access is true, because Config stays allow-listed then (fix.diff:168-170, system/src/Grav/Common/Security.php:367-372). Not pursued.",
  "A later advisory GHSA-59qm-58v5-gvc5 closed the |array / |yaml routes upstream (per a latest-tree code comment), which raises recall risk for those routes."
 ],
 "unverified": [
  "The exact pinned parent commit hash (candidate parent_commit is null).",
  "Pimple\\Container private $values layout: vendor/ is not in the pinned tree. The grav|array container route relies on it; only the latest-tree comment confirms it.",
  "Whether `grav.theme` resolves to the Theme (Plugin subclass) instance under the sandbox's property/method resolution. Allowed at system/config/security.yaml:336 and the allowed_properties Grav entry; not traced through Twig's getAttribute.",
  "Repo size in MB (no du allowed; vendor not present).",
  "No tests in fix.diff, so regression_tests_in_pinned_commit could not apply; hidden tests must be written from scratch."
 ]
}
  ```
- Published fix sites:   - system/config/security.yaml:335-336 — entry point: Sandboxed page-content Twig member call grav.offsetGet('config') / grav.__get (HTTP page render via Twig::processPage/processString) [defaults config (sandbox allowlist)]
  - system/src/Grav/Common/Twig/Extension/GravExtension.php:147 — entry point: Twig filter |print_r in sandboxed page content [Twig extension filter registration]
  - system/src/Grav/Common/Twig/Extension/GravExtension.php:148 — entry point: Twig filter |yaml_encode in sandboxed page content [Twig extension filter registration]
  - system/src/Grav/Common/Twig/Extension/GravExtension.php:159 — entry point: Twig filter |string in sandboxed page content [Twig extension filter registration]
  - system/src/Grav/Common/Twig/Extension/GravExtension.php:198-199 — entry point: Twig functions vardump() and print_r() in sandboxed page content [Twig extension function registration]
  - fix.diff:59-62 — entry point: Twig core |json_encode filter (Twig CoreExtension), overridden by a guarded GravExtension filter [second implementation (override of the vendor core filter)]
  - fix.diff:261-270 — entry point: GravSecurityPolicy::isClassAllowed (new public API used by the guard); policy built by Security::buildTwigSandboxPolicy at system/src/Grav/Common/Security.php:300 [sandbox policy class]
- Uncovered routes to confirm (pattern B):   - system/src/Grav/Common/Twig/Extension/GravExtension.php:213 — The Twig *function* string() is still bound to the unguarded stringFilter, which json_encodes arrays (and so calls Data::jsonSerialize on any Config inside them). The fix guarded only the same-named filter. (reason to dismiss: The report and fix talk about filters; string() looks like a harmless scalar cast helper in the separate function list.; still in latest: yes)
  - system/src/Grav/Common/Twig/Extension/GravExtension.php:163; system/src/Grav/Common/Twig/Extension/GravExtension.php:189; system/src/Grav/Common/Twig/Extension/GravExtension.php:911-928; system/src/Grav/Common/Plugin.php:39 — The array filter and function call toArray() or a PHP (array) cast on any object, outside the member gate. This exposes protected/private state such as Plugin/Theme::$config or the container's service map, which a printer then outputs. (reason to dismiss: |array is a type cast, not a dump/serialize filter, and the advisory names only offsetGet + dump.; still in latest: no)
  - system/src/Grav/Common/Twig/Extension/GravExtension.php:164; system/src/Grav/Common/Twig/Extension/GravExtension.php:936-939 — The yaml filter (Yaml::dump) is a second YAML printer next to yaml_encode, and the fix left it unguarded. It prints whatever array an earlier cast hands it. (reason to dismiss: The Symfony dumper refuses to serialize objects, so on its own it cannot leak an object.; still in latest: no)
  - system/src/Grav/Common/Twig/Twig.php:298-300; system/src/Grav/Common/Twig/Twig.php:411-412; system/src/Grav/Common/Twig/Twig.php:493-495 — The sandboxed render inherits the raw `system`, `site` and `theme` config arrays as template variables. Only `config` is replaced by the redacting facade, so json_encode/print_r on them prints unredacted config even with config_access off. (reason to dismiss: These are documented standard template variables, and the default denied paths (plugins, security, ...) are not under them.; still in latest: no)
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

## Environment (`tasks/grav-ds/environment/Dockerfile`)
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

## Report to the solver (`tasks/grav-ds/instruction.md`)
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

## Tests (`tasks/grav-ds/tests/`)
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
- **Wrong-fix patches** go in `build/grav-ds/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/grav-ds/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/grav-ds/manifest.json`:**
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

**Also in `build/grav-ds/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py grav-ds --only static
python3 -I builder/gate.py grav-ds --only nop
python3 -I builder/gate.py grav-ds --only oracle
python3 -I builder/gate.py grav-ds --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/grav-ds/`;
  - edit only `tasks/grav-ds/`, `build/grav-ds/` and, for pattern B, the register;
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
