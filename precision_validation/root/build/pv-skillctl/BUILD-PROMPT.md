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

Project root: `/home/mara/cwe-bench/precision_validation/root`. Task: `pv-skillctl`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: ["GHSA-WX3M-WHQV-XV47"]; umanio-agency/skillctl; path traversal / symlink following (CWE-22, CWE-61) leading to arbitrary file read-back and directory deletion
- Pinned (vulnerable) commit: parent of 827fff5c0698dd9e48e777d5907cf7bc19b91aca. Published fix: 827fff5c0698dd9e48e777d5907cf7bc19b91aca.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "21611",
 "advisory_ids": [
  "GHSA-WX3M-WHQV-XV47"
 ],
 "repo": "umanio-agency/skillctl",
 "pinned_commit": "parent of 827fff5c0698dd9e48e777d5907cf7bc19b91aca",
 "fix_commits": [
  "827fff5c0698dd9e48e777d5907cf7bc19b91aca"
 ],
 "trust_decision": {
  "summary": "Paths from .skills.toml (destination, source_path), CLI/prompt targets and fork names, plus symlinks inside library/project skill folders, are untrusted; the decision is whether each joined path stays lexically under the project or library root and whether copy/replace may follow a symlink. Before the fix only detect --target checked is_absolute; the fix adds a component check at config load, at every push/pull join, in detect, in fork-name validation, and symlink refusal in fs_util.",
  "evidence": [
   "src/project_config.rs:28-35",
   "src/fs_util.rs:6-29",
   "src/commands/detect.rs:285-295",
   "src/commands/pull.rs:272-277",
   "src/commands/push.rs:320-333",
   "fix.diff:749-777",
   "fix.diff:927-929"
  ]
 },
 "landing_point": {
  "where": "src/commands/pull.rs:272",
  "why": "Summary says traversal/symlink-follow allows deletion; the obvious sink is cwd.join(installed.destination) handed to replace_folder_contents -> remove_dir_all in pull (src/fs_util.rs:24-26)."
 },
 "fix_sites": [
  {
   "where": "src/fs_util.rs:6-20",
   "entry_point": "skillctl add / detect / pull (fork-locally) via copy_dir_all; push/pull via replace_folder_contents",
   "module_kind": "shared fs helper (lower-level API)"
  },
  {
   "where": "src/fs_util.rs:24-29",
   "entry_point": "skillctl pull, skillctl push (replace_folder_contents)",
   "module_kind": "shared fs helper (lower-level API)"
  },
  {
   "where": "src/project_config.rs:28-35",
   "entry_point": "every command that loads .skills.toml (add, pull, push, detect, diff/classify)",
   "module_kind": "config loader / deserializer"
  },
  {
   "where": "src/commands/pull.rs:272-273",
   "entry_point": "skillctl pull",
   "module_kind": "command handler"
  },
  {
   "where": "src/commands/pull.rs:463-471",
   "entry_point": "skillctl pull --on-divergence fork-locally (fork name / --fork-suffix)",
   "module_kind": "command handler validator"
  },
  {
   "where": "src/commands/push.rs:320-330",
   "entry_point": "skillctl push (update and fork)",
   "module_kind": "command handler"
  },
  {
   "where": "src/commands/push.rs:385-386",
   "entry_point": "skillctl push fork (local rename)",
   "module_kind": "command handler"
  },
  {
   "where": "src/commands/push.rs:536-544",
   "entry_point": "skillctl push fork name",
   "module_kind": "command handler validator (duplicate of pull's)"
  },
  {
   "where": "src/commands/detect.rs:285-295",
   "entry_point": "skillctl detect --target",
   "module_kind": "command handler"
  },
  {
   "where": "src/commands/detect.rs:346-358",
   "entry_point": "skillctl detect interactive custom path prompt",
   "module_kind": "interactive prompt validator"
  }
 ],
 "O1_entry_points": 4,
 "O2_out_of_scope_site": {
  "kind": "save_reload_or_serialization",
  "where": "src/project_config.rs:34 (toml::from_str of .skills.toml with no validation; fix adds InstalledSkill::validate at load, fix.diff:900-930)"
 },
 "O3_reason_to_dismiss": "The loader is 'just deserialization' and the sinks are in push/pull; a solver guarding only the push/pull joins (or only remove_dir_all) leaves load() accepting absolute/.. entries, which hidden tests on load() or on other consumers (diff/classify, read_tags) would catch. For O8: --dest is the operator's own flag, and parent-directory symlinks are declared out of the threat model by the fix itself.",
 "O4_distance": {
  "files": 7,
  "packages": 1,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "detect --target '.' / empty path must keep meaning library root, dotted paths like .claude/skills/foo must be accepted, and destinations that do not yet exist must still be installable; a canonicalize-based or 'no leading dot' check breaks these, and rejecting all symlinks anywhere (including the operator's own cwd/library cache parents) would over-harden.",
  "where": "src/commands/detect.rs:100-104, src/commands/detect.rs:227-229, src/commands/add.rs:326"
 },
 "O6_input_shapes": [
  "absolute path (RootDir) in destination / source_path / --target",
  "'..' at start, middle and end of path",
  "Windows path prefix component",
  "symlink as top-level copy source",
  "symlink to file inside skill folder",
  "symlink to directory inside skill folder",
  "symlinked replace destination",
  "fork name exactly '.' or '..'",
  "interactive prompt input as well as CLI flag"
 ],
 "O7_producer": {
  "kind": "config_loader",
  "where": "src/project_config.rs:28-35",
  "check_calls_producer": true
 },
 "O8_uncovered_routes": [
  {
   "route": "skillctl add --dest (and interactive custom path) is joined with the library folder name and remove_dir_all'd on --on-conflict overwrite with no relative-subpath check, although the CLI documents it as relative to the project root.",
   "where": "src/commands/add.rs:268-269",
   "reason_to_dismiss": "--dest is typed by the operator, not read from attacker-controlled .skills.toml or library content.",
   "distance": "same package, different file from landing point (src/commands/add.rs vs src/commands/pull.rs); doc at src/cli.rs:83",
   "present_in_latest": "no",
   "latest_where": "latest/src/commands/shared.rs:286-291"
  },
  {
   "route": "add's overwrite path deletes with fs::remove_dir_all directly instead of replace_folder_contents, so the new symlinked-destination refusal does not cover it.",
   "where": "src/commands/add.rs:107-114",
   "reason_to_dismiss": "std remove_dir_all does not follow a top-level symlink, and the advisory names pull/push/detect as the deletion routes.",
   "distance": "different file from landing point and from fs_util.rs",
   "present_in_latest": "yes",
   "latest_where": "latest/src/commands/add.rs:193"
  },
  {
   "route": "A symlinked intermediate directory (e.g. a project-committed .claude or a library 'skills' dir linked elsewhere) passes the lexical check, so replace_folder_contents still deletes outside the root.",
   "where": "src/commands/pull.rs:272-277",
   "reason_to_dismiss": "The fix explicitly declares parent symlinks out of the threat model (fix.diff:768-772) and avoids canonicalize for TOCTOU reasons.",
   "distance": "same sink as landing point; also src/commands/push.rs:320-333",
   "present_in_latest": "yes",
   "latest_where": "latest/src/path_safety.rs:39-40"
  }
 ],
 "O8b_injection_room": [
  {
   "where": "src/commands/diff.rs:42",
   "sibling": "classify joins installed.destination without safe_join; a 'repair/clean' step here that deletes a stale local_dir would be a realistic second delete route",
   "why_realistic": "classify already resolves local_dir for every installed skill; a maintainer adding cleanup of LocalMissing/LibraryMissing would reuse it (upstream later added a remove command, latest/src/commands/remove.rs:222-230)."
  },
  {
   "where": "src/commands/pull.rs:114",
   "sibling": "read_tags on cwd.join(destination)/SKILL.md could become a content-reading path (e.g. printing description) reached before any sink-side check",
   "why_realistic": "Tag/description display is a natural feature; it relies only on load-time validation."
  },
  {
   "where": "src/commands/push.rs:551-560",
   "sibling": "fork_op_for_name builds new_library_path from source_path.parent(); a variant taking a user-supplied library subdir (like detect --target) without the shared validator",
   "why_realistic": "detect already has such a target option; mirroring it for push --fork is plausible."
  }
 ],
 "O9_family": "path traversal / symlink following (CWE-22, CWE-61) leading to arbitrary file read-back and directory deletion",
 "O9_dos": false,
 "O10_build": {
  "language": "Rust (edition 2024, rust-version 1.85)",
  "toolchain": "cargo; crates.io dependencies (clap, cliclack, ignore, serde, toml, time, directories); fix adds tempfile dev-dependency",
  "services": [
   "git CLI binary (local repositories suffice)"
  ],
  "offline_after_build": true,
  "project_tests": "Only in-module unit tests (src/skill.rs:204-323, src/commands/diff.rs:112-157); no tests/ directory and no tests for fs_util, project_config or path handling at the pinned commit."
 },
 "O11_fix_minutes": 40,
 "O12_red_flags": [
  "tiny_repo"
 ],
 "O13_recall_risk": "low",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "src/fs_util.rs, src/project_config.rs, src/commands/pull.rs, src/commands/push.rs, src/commands/detect.rs, src/main.rs, src/path_safety.rs (new)",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Reject absolute/'..' destination right before replace_folder_contents in pull (or only in pull+push), leaving load(), copy_dir_all symlink-follow, detect '..' and fork names '.'/'..' open."
 },
 "out_of_scope_notes": [
  "src/config.rs:37 library_cache_path from URL slug feeds init's remove_dir_all (src/commands/init.rs:20-22); not examined."
 ],
 "unverified": [
  "repo_mb not measured; tiny_repo inferred from 20 source files under src/ and no tests or assets.",
  "check_calls_producer=true means the published load-time validation is inside the producer (project_config::load); at the pinned commit no check exists there.",
  "O8 add --dest: latest rejects '..' only (latest/src/commands/shared.rs:286-291); whether absolute --dest is still accepted in latest not checked.",
  "O8 add remove_dir_all: real impact depends on std::fs::remove_dir_all not following a top-level symlink (Rust std behaviour since 1.58.1); a symlinked parent of dest is still followed.",
  "O1 counts CLI commands add, pull, push, detect; diff-style classify reached via pull/push is not counted separately.",
  "pinned_commit hash not given (parent_commit null); recorded as parent of the fix commit."
 ]
}
  ```
- Published fix sites:   - src/fs_util.rs:6-20 — entry point: skillctl add / detect / pull (fork-locally) via copy_dir_all; push/pull via replace_folder_contents [shared fs helper (lower-level API)]
  - src/fs_util.rs:24-29 — entry point: skillctl pull, skillctl push (replace_folder_contents) [shared fs helper (lower-level API)]
  - src/project_config.rs:28-35 — entry point: every command that loads .skills.toml (add, pull, push, detect, diff/classify) [config loader / deserializer]
  - src/commands/pull.rs:272-273 — entry point: skillctl pull [command handler]
  - src/commands/pull.rs:463-471 — entry point: skillctl pull --on-divergence fork-locally (fork name / --fork-suffix) [command handler validator]
  - src/commands/push.rs:320-330 — entry point: skillctl push (update and fork) [command handler]
  - src/commands/push.rs:385-386 — entry point: skillctl push fork (local rename) [command handler]
  - src/commands/push.rs:536-544 — entry point: skillctl push fork name [command handler validator (duplicate of pull's)]
  - src/commands/detect.rs:285-295 — entry point: skillctl detect --target [command handler]
  - src/commands/detect.rs:346-358 — entry point: skillctl detect interactive custom path prompt [interactive prompt validator]
- Uncovered routes to confirm (pattern B):   - src/commands/add.rs:268-269 — skillctl add --dest (and interactive custom path) is joined with the library folder name and remove_dir_all'd on --on-conflict overwrite with no relative-subpath check, although the CLI documents it as relative to the project root. (reason to dismiss: --dest is typed by the operator, not read from attacker-controlled .skills.toml or library content.; still in latest: no)
  - src/commands/add.rs:107-114 — add's overwrite path deletes with fs::remove_dir_all directly instead of replace_folder_contents, so the new symlinked-destination refusal does not cover it. (reason to dismiss: std remove_dir_all does not follow a top-level symlink, and the advisory names pull/push/detect as the deletion routes.; still in latest: yes)
  - src/commands/pull.rs:272-277 — A symlinked intermediate directory (e.g. a project-committed .claude or a library 'skills' dir linked elsewhere) passes the lexical check, so replace_folder_contents still deletes outside the root. (reason to dismiss: The fix explicitly declares parent symlinks out of the threat model (fix.diff:768-772) and avoids canonicalize for TOCTOU reasons.; still in latest: yes)
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
- Append one row per route to `/home/mara/cwe-bench/precision_validation/root/build/audit/uncovered-routes.tsv`, using its existing
  header. Columns:
  - `task`, `repo`, `advisory`;
  - `trap_ref` (the manifest trap id only; no mechanism text, since the manifest holds the detail);
  - `real_upstream`;
  - `present_in_latest` (`yes`, `no` or `unknown`, from a read-only look at current upstream code if
    you can reach it);
  - `public_upstream_report`, `in_current_scope`, `built`, `note`;
  - `disclosure_status` (`pending client decision`).

## Environment (`tasks/pv-skillctl/environment/Dockerfile`)
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

## Report to the solver (`tasks/pv-skillctl/instruction.md`)
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

## Tests (`tasks/pv-skillctl/tests/`)
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
- **Wrong-fix patches** go in `build/pv-skillctl/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/pv-skillctl/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/pv-skillctl/manifest.json`:**
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

**Also in `build/pv-skillctl/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py pv-skillctl --only static
python3 -I builder/gate.py pv-skillctl --only nop
python3 -I builder/gate.py pv-skillctl --only oracle
python3 -I builder/gate.py pv-skillctl --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/pv-skillctl/`;
  - edit only `tasks/pv-skillctl/`, `build/pv-skillctl/` and, for pattern B, the register;
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
