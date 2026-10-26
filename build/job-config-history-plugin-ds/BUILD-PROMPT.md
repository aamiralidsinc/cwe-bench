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

Project root: `/home/mara/cwe-bench`. Task: `job-config-history-plugin-ds`. Pattern: `A`. Track: `injected`.

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
- Advisory: ["GHSA-8QR4-27MH-HQFR", "CVE-2026-57287"]; jenkinsci/job-config-history-plugin; CWE-312 cleartext/encrypted secret exposure to under-privileged readers (missing output redaction)
- Pinned (vulnerable) commit: ba0105cedfa57aae6eab16a23c112b5b1cda2889. Published fix: c8fab15101dce336a8f17f10edd10c7221b860c0.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v2",
 "model": "claude-opus-5-5",
 "entry_id": "24575",
 "advisory_ids": [
  "GHSA-8QR4-27MH-HQFR",
  "CVE-2026-57287"
 ],
 "repo": "jenkinsci/job-config-history-plugin",
 "pinned_commit": "ba0105cedfa57aae6eab16a23c112b5b1cda2889",
 "fix_commits": [
  "c8fab15101dce336a8f17f10edd10c7221b860c0"
 ],
 "trust_decision": {
  "summary": "Users who hold Item/EXTENDED_READ but not CONFIGURE may view historical config.xml revisions, raw or as a diff, and these must have encrypted Secret values redacted. The permission gate is decided per action class (hasConfigurePermission/hasReadExtensionPermission), but the raw XML is returned unredacted.",
  "evidence": [
   "src/main/java/hudson/plugins/jobConfigHistory/JobConfigHistoryProjectAction.java:216-224",
   "src/main/java/hudson/plugins/jobConfigHistory/JobConfigHistoryProjectAction.java:424-432",
   "src/main/java/hudson/plugins/jobConfigHistory/JobConfigHistoryProjectAction.java:264-271",
   "src/main/java/hudson/plugins/jobConfigHistory/JobConfigHistoryRootAction.java:556-579",
   "src/main/java/hudson/plugins/jobConfigHistory/JobConfigHistoryBaseAction.java:567-577"
  ]
 },
 "landing_point": {
  "where": "src/main/java/hudson/plugins/jobConfigHistory/JobConfigHistoryProjectAction.java:216-224",
  "why": "The job-level configOutput view (getFile) is the obvious 'show old job config' path. It admits EXTENDED_READ users and returns xmlFile.asString() unredacted."
 },
 "fix_sites": [
  {
   "where": "fix.diff:15-16",
   "entry_point": "GET /computer/<agent>/jobConfigHistory/configOutput (ComputerConfigHistoryAction.getFile)",
   "module_kind": "agent history action (second implementation; gated by Computer.CONFIGURE so the redaction branch is unreachable)"
  },
  {
   "where": "fix.diff:25",
   "entry_point": "GET /computer/<agent>/jobConfigHistory/showDiffFiles (ComputerConfigHistoryAction.getLines)",
   "module_kind": "agent history action (passes redactSecrets=false)"
  },
  {
   "where": "fix.diff:57-68",
   "entry_point": "public static JobConfigHistoryBaseAction.getStringFromXmlFile (helper used by the getFile views)",
   "module_kind": "shared base class helper"
  },
  {
   "where": "fix.diff:82-98",
   "entry_point": "protected JobConfigHistoryBaseAction.getLines(XmlFile,XmlFile,boolean,boolean), the diff builder for all showDiffFiles views",
   "module_kind": "shared base class, lower-level diff API"
  },
  {
   "where": "fix.diff:123-124",
   "entry_point": "GET /job/<name>/jobConfigHistory/configOutput?type=xml|raw (JobConfigHistoryProjectAction.getFile)",
   "module_kind": "job history action (landing point)"
  },
  {
   "where": "fix.diff:147-155",
   "entry_point": "GET /job/<name>/jobConfigHistory/showDiffFiles (JobConfigHistoryProjectAction.getLines)",
   "module_kind": "job history action"
  },
  {
   "where": "fix.diff:157-184",
   "entry_point": "public static JobConfigHistoryProjectAction.redactAuthTokensInLines (post-diff masking of cleartext authToken in HTML-escaped line text)",
   "module_kind": "job history action helper"
  },
  {
   "where": "fix.diff:198-208",
   "entry_point": "GET /jobConfigHistory/showDiffFiles?name=<job>_deleted_<ts> (JobConfigHistoryRootAction.getLines)",
   "module_kind": "root/global history action (system + deleted jobs)"
  }
 ],
 "O1_entry_points": 3,
 "O2_out_of_scope_site": {
  "kind": "second_implementation",
  "where": "src/main/java/hudson/plugins/jobConfigHistory/JobConfigHistoryRootAction.java:556-579 (deleted-job diff in the global root action, a separate getLines implementation reached at /jobConfigHistory/showDiffFiles)"
 },
 "O3_reason_to_dismiss": "The root action serves system configs to admins, and a deleted job is no longer a job page, so a solver can argue the job-level views are the only ones covered by 'job configurations'.",
 "O4_distance": {
  "files": 4,
  "packages": 1,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Users with CONFIGURE must still get the raw XML, and doRestore must keep reading the unredacted revision. A fix placed in getOldConfigXml or HistoryDao.getOldRevision would write masked secrets back into the job or agent on restore.",
  "where": "src/main/java/hudson/plugins/jobConfigHistory/JobConfigHistoryProjectAction.java:467-481"
 },
 "O6_input_shapes": [
  "raw XML output view (configOutput type=xml and type=plain, same getFile)",
  "side-by-side diff lines built from XSLT-sorted XML (redaction must happen before diffing so both columns and the hideVersionDiffs path see redacted text)",
  "cleartext legacy <authToken> in the diff view only, matched in its HTML-escaped form (&lt;authToken&gt;), because DiffRowGenerator escapes line text",
  "encrypted {AQAAAB...} Secret values anywhere in the XML via ExtendedReadRedaction.applyAll"
 ],
 "O7_producer": {
  "kind": "mapper",
  "where": "src/main/java/hudson/plugins/jobConfigHistory/GetDiffLines.java:64-66 and src/main/java/hudson/plugins/jobConfigHistory/GetDiffLines.java:169-212 (DiffRowGenerator turns unified diff into HTML-escaped Line text), plus src/main/java/hudson/plugins/jobConfigHistory/JobConfigHistoryBaseAction.java:534-556 (XSLT sort)",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "Root configOutput for a deleted job returns the raw XML to global Item.CONFIGURE holders. The fix redacts the root diff for the same users but leaves root getFile untouched.",
   "where": "src/main/java/hudson/plugins/jobConfigHistory/JobConfigHistoryRootAction.java:432-442",
   "reason_to_dismiss": "The gate is Item.CONFIGURE, which in Jenkins policy may see encrypted secrets, so this is arguably not a leak. It is an inconsistency with the root diff path.",
   "distance": "same file as the O2 site; 1 package from the landing point",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "Job configOutput (getFile) does not mask a cleartext legacy <authToken>, which the job diff view masks after the fix.",
   "where": "src/main/java/hudson/plugins/jobConfigHistory/JobConfigHistoryProjectAction.java:216-224",
   "reason_to_dismiss": "The advisory is about encrypted values, and the fix's own test says the cleartext token 'cannot' be redacted.",
   "distance": "landing point itself",
   "present_in_latest": "unknown",
   "latest_where": ""
  }
 ],
 "O8b_injection_room": [
  {
   "where": "src/main/java/hudson/plugins/jobConfigHistory/ComputerConfigHistoryAction.java:116-139",
   "sibling": "Gate agent history views on Computer.EXTENDED_READ (as the job action does with Item.EXTENDED_READ) so the agent getFile/getLines become real extended-read routes needing redaction.",
   "why_realistic": "The agent action already consults hasReadExtensionPermission in getAgentConfigs(int,int) at ComputerConfigHistoryAction.java:231, so widening the view gate is a natural maintainer change."
  },
  {
   "where": "src/main/java/hudson/plugins/jobConfigHistory/JobConfigHistoryRootAction.java:620-637",
   "sibling": "Expose system-config history (non-deleted names) to EXTENDED_READ users through the root getFile/getLines.",
   "why_realistic": "getOldConfigXml already admits hasReadExtensionPermission for system names at JobConfigHistoryRootAction.java:626-627, while getFile/getLines additionally require CONFIGURE."
  },
  {
   "where": "src/main/java/hudson/plugins/jobConfigHistory/JobConfigHistoryProjectAction.java:202-205",
   "sibling": "An @Exported REST field or a doDownload endpoint returning the old revision XML for extended-read users.",
   "why_realistic": "The class already exports history metadata via the REST API at this site; a raw-revision export is a plausible feature request."
  }
 ],
 "O9_family": "CWE-312 cleartext/encrypted secret exposure to under-privileged readers (missing output redaction)",
 "O9_dos": false,
 "O10_build": {
  "language": "Java",
  "toolchain": "Maven, org.jenkins-ci.plugins:plugin parent 5.28, Jenkins core 2.504.3 (pom.xml:7-8, pom.xml:39-40), JDK 17+",
  "services": [],
  "offline_after_build": true,
  "project_tests": "src/test/java/hudson/plugins/jobConfigHistory/JobConfigHistoryProjectActionIT.java, JobConfigHistoryBaseActionTest.java, JobConfigHistoryRootActionTest.java, ComputerConfigHistoryActionIT.java (JenkinsRule-based)"
 },
 "O11_fix_minutes": 40,
 "O12_red_flags": [],
 "O13_recall_risk": "low",
 "pattern_fit": "A",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "src/main/java/hudson/plugins/jobConfigHistory/ComputerConfigHistoryAction.java, src/main/java/hudson/plugins/jobConfigHistory/JobConfigHistoryBaseAction.java, src/main/java/hudson/plugins/jobConfigHistory/JobConfigHistoryProjectAction.java, src/main/java/hudson/plugins/jobConfigHistory/JobConfigHistoryRootAction.java",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 0,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Wrap only JobConfigHistoryProjectAction.getFile's asString() in ExtendedReadRedaction.applyAll for non-CONFIGURE users, leaving the diff views (job and deleted-job root) unredacted."
 },
 "out_of_scope_notes": [
  "JobConfigHistoryRootAction.getOldConfigXml passes a request 'name' straight to HistoryDao with only a '..' check (JobConfigHistoryRootAction.java:620-656); this is an access-control question, not pursued.",
  "XmlSyntaxChecker returns SAX exception messages to the diff page (XmlSyntaxChecker.java:30-55); content echo not assessed."
 ],
 "unverified": [
  "Repo size in MB not measured (no shell). It is a single-package Jenkins plugin, so tiny_repo (<5 MB of source) is plausible but not confirmed; src/main/webapp bundles highlight.js.",
  "The fix's changes to ComputerConfigHistoryAction look like dead code: every agent view calls checkConfigurePermission (Computer.CONFIGURE) first (ComputerConfigHistoryAction.java:416-428), so !hasConfigurePermission() is never true there. Whether the advisory's 'agent configurations' claim relies on another route was not found.",
  "That ExtendedReadRedaction.applyAll matches only encrypted {AQAAAB...} Secret blobs, not cleartext tokens, is inferred from the fix's test comment (fix.diff:257) and was not read in core.",
  "That java-diff-utils DiffRowGenerator escapes HTML by default is inferred from the fix's &lt;authToken&gt; regex (fix.diff:110-111); not checked in the library source.",
  "present_in_latest is unknown for all O8 routes (no latest release given)."
 ]
}
  ```
- Published fix sites:   - fix.diff:15-16 — entry point: GET /computer/<agent>/jobConfigHistory/configOutput (ComputerConfigHistoryAction.getFile) [agent history action (second implementation; gated by Computer.CONFIGURE so the redaction branch is unreachable)]
  - fix.diff:25 — entry point: GET /computer/<agent>/jobConfigHistory/showDiffFiles (ComputerConfigHistoryAction.getLines) [agent history action (passes redactSecrets=false)]
  - fix.diff:57-68 — entry point: public static JobConfigHistoryBaseAction.getStringFromXmlFile (helper used by the getFile views) [shared base class helper]
  - fix.diff:82-98 — entry point: protected JobConfigHistoryBaseAction.getLines(XmlFile,XmlFile,boolean,boolean), the diff builder for all showDiffFiles views [shared base class, lower-level diff API]
  - fix.diff:123-124 — entry point: GET /job/<name>/jobConfigHistory/configOutput?type=xml|raw (JobConfigHistoryProjectAction.getFile) [job history action (landing point)]
  - fix.diff:147-155 — entry point: GET /job/<name>/jobConfigHistory/showDiffFiles (JobConfigHistoryProjectAction.getLines) [job history action]
  - fix.diff:157-184 — entry point: public static JobConfigHistoryProjectAction.redactAuthTokensInLines (post-diff masking of cleartext authToken in HTML-escaped line text) [job history action helper]
  - fix.diff:198-208 — entry point: GET /jobConfigHistory/showDiffFiles?name=<job>_deleted_<ts> (JobConfigHistoryRootAction.getLines) [root/global history action (system + deleted jobs)]
- Uncovered routes to confirm (pattern B): none
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

## Environment (`tasks/job-config-history-plugin-ds/environment/Dockerfile`)
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

## Report to the solver (`tasks/job-config-history-plugin-ds/instruction.md`)
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

## Tests (`tasks/job-config-history-plugin-ds/tests/`)
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
- **Wrong-fix patches** go in `build/job-config-history-plugin-ds/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/job-config-history-plugin-ds/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/job-config-history-plugin-ds/manifest.json`:**
- `slug`, `candidate`;
- `pattern`: `A`;
- `builder_prompt_version`: `build-v1`;
- `"strict_gate": true`;
- `verified`: entry point, sites, routes, services, project tests run;
- `leak_terms`, `patch_checks`, `wrong_fix_catalogue`;
- `traps`: one entry per lever, with `shape`, `where` (file:line), `security_tests`,
  `coupled_functional_tests`, `security_fail_patch`, and `realistic_because` (for pattern B: "real,
  unmodified upstream code");
- `status`.

**Also in `build/job-config-history-plugin-ds/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py job-config-history-plugin-ds --only static
python3 -I builder/gate.py job-config-history-plugin-ds --only nop
python3 -I builder/gate.py job-config-history-plugin-ds --only oracle
python3 -I builder/gate.py job-config-history-plugin-ds --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/job-config-history-plugin-ds/`;
  - edit only `tasks/job-config-history-plugin-ds/`, `build/job-config-history-plugin-ds/` and, for pattern B, the register;
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
