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

Project root: `/home/mara/cwe-bench`. Task: `comfyui-manager-s3`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: ["GHSA-95PQ-HR8P-F5G7", "CVE-2025-67303", "PYSEC-2026-2422"]; comfy-org/comfyui-manager; Unprotected alternate channel (CWE-420): security-policy state persisted where an unprotected file API can rewrite it, bypassing the security-level gate
- Pinned (vulnerable) commit: c8dce94c031ed87a8673d354482a39dedc15407b. Published fix: e44c5cef58fb4973670b86433b9d24d077b44a26.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v2",
 "model": "deepseek-flash[1m]",
 "entry_id": "2366",
 "advisory_ids": [
  "GHSA-95PQ-HR8P-F5G7",
  "CVE-2025-67303",
  "PYSEC-2026-2422"
 ],
 "repo": "comfy-org/comfyui-manager",
 "pinned_commit": "c8dce94c031ed87a8673d354482a39dedc15407b",
 "fix_commits": [
  "e44c5cef58fb4973670b86433b9d24d077b44a26"
 ],
 "trust_decision": {
  "summary": "Whether an install/remove/reboot operation is allowed is decided by security_level read from config.ini under <user>/default/ComfyUI-Manager/, a directory ComfyUI's user-data API exposes to remote writers, so the policy input itself is attacker-writable; the published fix moves that state to the protected <user>/__manager path, raises a migrated level to 'normal' and forces 'strong' when the host has no System User API.",
  "evidence": [
   "glob/manager_server.py:89-100",
   "glob/manager_core.py:217-234",
   "glob/manager_core.py:1710-1743",
   "glob/manager_core.py:1680-1707",
   "prestartup_script.py:88-92"
  ]
 },
 "landing_point": {
  "where": "glob/manager_core.py:217",
  "why": "the single place that composes the Manager data directory for the server and CLI; README:143 names the same legacy path"
 },
 "fix_sites": [
  {
   "where": "glob/manager_core.py:217-220",
   "entry_point": "ComfyUI startup import (glob/manager_core.py:239-241) and cm-cli `set_user_directory` -> core.update_user_directory (cm-cli.py:146)",
   "module_kind": "core library, global path setup"
  },
  {
   "where": "glob/manager_core.py:1722-1741",
   "entry_point": "every security-gated HTTP route via manager_server.is_allowed_security_level -> core.get_config()",
   "module_kind": "config loader, main branch"
  },
  {
   "where": "glob/manager_core.py:1743-1768",
   "entry_point": "core.get_config() when config.ini is missing or unparseable (defaults fallback)",
   "module_kind": "config loader, exception fallback branch"
  },
  {
   "where": "fix.diff:377-732",
   "entry_point": "imported by manager_core.update_user_directory and manager_server; runs at ComfyUI startup (new module manager_migration.py)",
   "module_kind": "new core module"
  },
  {
   "where": "fix.diff:748-752",
   "entry_point": "/manager/queue/update_all, /snapshot/remove, /snapshot/restore, /customnode/install/git_url, /customnode/install/pip, /manager/reboot",
   "module_kind": "HTTP route module, 403 body only (not a protection site)"
  },
  {
   "where": "fix.diff:825-846",
   "entry_point": "GET /manager/startup_alerts (new route)",
   "module_kind": "HTTP route module, new UI route"
  },
  {
   "where": "prestartup_script.py:88",
   "entry_point": "ComfyUI startup: custom_nodes/ComfyUI-Manager/prestartup_script.py",
   "module_kind": "startup script, second independent path implementation"
  },
  {
   "where": "prestartup_script.py:519",
   "entry_point": "same startup script: path of startup-scripts/install-scripts.txt, hardcoded from folder_paths.user_directory",
   "module_kind": "startup script, third hardcoded path"
  },
  {
   "where": "prestartup_script.py:795-797",
   "entry_point": "same startup script: executes startup-scripts/install-scripts.txt (fix wraps this in an old-ComfyUI block)",
   "module_kind": "startup script, execution sink"
  },
  {
   "where": "fix.diff:968-978",
   "entry_point": "browser UI fetches of the Manager routes (handle403Response)",
   "module_kind": "browser UI, 403 message text only (not a protection site)"
  }
 ],
 "O1_entry_points": 3,
 "O2_out_of_scope_site": {
  "kind": "second_implementation",
  "where": "prestartup_script.py:88-92 (and the third hardcoded variant at prestartup_script.py:519)"
 },
 "O3_reason_to_dismiss": "prestartup_script.py runs before ComfyUI's server exists and is not a web route, so a solver can argue the reported remote-API issue does not reach it and that the path only needs changing where the HTTP layer reads config.",
 "O4_distance": {
  "files": 3,
  "packages": 2,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "a user who deliberately sets security_level = weak or normal- in the protected config keeps that level; the fix raises the level only once, during migration, and only when it is below 'normal' (README:366-376 defines weak as a supported level, and Update ComfyUI stays low-risk/always allowed at README:389-390)",
  "where": "fix.diff:688-709"
 },
 "O6_input_shapes": [
  "legacy dir only, new dir absent (normal migration path)",
  "legacy dir and new config both present (first update after ComfyUI upgrade)",
  "legacy dir present without config.ini",
  "neither directory present (nothing to migrate)",
  "config.ini unparseable or missing the [default] section",
  "security_level = weak or normal- (raise to normal) vs normal/strong/absent (leave unchanged)",
  "host ComfyUI with folder_paths.get_system_user_directory vs without it",
  "read_config success branch vs exception/defaults branch",
  "startup-script artifacts present vs absent at boot"
 ],
 "O7_producer": {
  "kind": "config_loader",
  "where": "prestartup_script.py:99-107",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "startup-scripts/restore-snapshot.json is executed at boot (cm-cli restore-snapshot) from the same manager data dir; the fix blocks install-scripts.txt on old ComfyUI but leaves this file unblocked, so a file written through the unprotected user-data path still runs at next start",
   "where": "prestartup_script.py:574-616",
   "reason_to_dismiss": "restore-snapshot is a documented legitimate feature and its HTTP trigger /snapshot/restore is already gated, so the boot handoff file looks like a trusted internal artifact",
   "distance": "repo-root startup script, one file away from glob/manager_core.py",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "pip_overrides.json / pip_blacklist.list / pip_auto_fix.list are loaded at boot from the manager data dir and can redirect package installs; on a host without the System User API the fix adds no block for them, only a path change that has no effect there",
   "where": "prestartup_script.py:124-136",
   "reason_to_dismiss": "pip_overrides/blacklist are admin convenience files, not the security policy, and the migration already moves the directory",
   "distance": "startup script plus glob/manager_util.py:494 in another module",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "config.ini is written by /manager/preview_method, /manager/db_mode, /manager/policy/component, /manager/policy/update and /manager/channel_url_list with no is_allowed_security_level check at any level, including 'strong'",
   "where": "glob/manager_server.py:1475-1541",
   "reason_to_dismiss": "these are benign UI preferences chosen from predefined value lists and cannot set security_level itself, so they look unrelated to the policy file",
   "distance": "same file as the gates but different routes, ~700 lines away",
   "present_in_latest": "unknown",
   "latest_where": ""
  }
 ],
 "O8b_injection_room": [
  {
   "where": "glob/manager_util.py:404-410",
   "sibling": "a second PIPFixer-like class or helper that takes the manager data dir as a constructor argument and is instantiated by a new caller that computes the legacy path itself",
   "why_realistic": "the class already accepts manager_files_path from outside, so a new tool or CLI subcommand can pass its own path without touching update_user_directory"
  },
  {
   "where": "glob/manager_server.py:996",
   "sibling": "an additional boot-time handoff artifact under startup-scripts/ (e.g. a queued-install or queued-update JSON) written by a new route and executed by prestartup, with no security gate of its own",
   "why_realistic": "the install-scripts.txt / restore-snapshot.json pair already established this pattern as the way long operations survive a restart"
  },
  {
   "where": "glob/manager_core.py:229-233",
   "sibling": "a new Manager state file added beside config.ini/channels.list (e.g. a trust store or security state file) read directly by a feature instead of through update_user_directory",
   "why_realistic": "the block already enumerates a growing set of per-file globals that a maintainer extends for each feature"
  },
  {
   "where": "glob/share_3rdparty.py:68-138",
   "sibling": "share tokens and API keys written under the manager dir, with a sibling feature writing them to a user-visible path for a browser-side share flow",
   "why_realistic": "the sharing features already persist keys and messages in this directory and are the kind of feature that needs the file readable from the browser"
  }
 ],
 "O9_family": "Unprotected alternate channel (CWE-420): security-policy state persisted where an unprotected file API can rewrite it, bypassing the security-level gate",
 "O9_dos": false,
 "O10_build": {
  "language": "Python (plus browser JS)",
  "toolchain": "pip/uv install from pyproject.toml (GitPython, PyGithub, matrix-nio, transformers, huggingface-hub, typer, rich, typing-extensions, toml, uv, chardet); manager_migration.py imports only stdlib, the rest needs a ComfyUI install for folder_paths/torch",
  "services": [],
  "offline_after_build": true,
  "project_tests": "none: no test directory, no test dependency or runner in pyproject.toml; the fix adds no tests"
 },
 "O11_fix_minutes": 60,
 "O12_red_flags": [
  "tiny_repo"
 ],
 "O13_recall_risk": "medium",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "glob/manager_core.py, glob/manager_migration.py (new), glob/manager_server.py, prestartup_script.py, js/common.js, js/cm-api.js, js/comfyui-manager.js, js/custom-nodes-manager.js, js/model-manager.js, js/snapshot.js",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 0,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Gate the routes on has_system_user_api() or clamp is_allowed_security_level to deny, leaving config.ini in user/default and never moving the state"
 },
 "out_of_scope_notes": [
  "The unprotected channel itself is ComfyUI's own user-data file API (a different repository, the fix's referenced ComfyUI PR #10966); I did not read or pursue it."
 ],
 "unverified": [
  "repo source size was not measured directly (no shell available); the 17 Python and 15 JS files in this tree suggest under 5 MB of source, which is why tiny_repo is flagged",
  "latest code state for the O8 routes: no latest release was supplied, so present_in_latest is unknown",
  "whether ComfyUI's user-data route really permits writes into user/default/ComfyUI-Manager was not checked (external repository)"
 ]
}
  ```
- Published fix sites:   - glob/manager_core.py:217-220 — entry point: ComfyUI startup import (glob/manager_core.py:239-241) and cm-cli `set_user_directory` -> core.update_user_directory (cm-cli.py:146) [core library, global path setup]
  - glob/manager_core.py:1722-1741 — entry point: every security-gated HTTP route via manager_server.is_allowed_security_level -> core.get_config() [config loader, main branch]
  - glob/manager_core.py:1743-1768 — entry point: core.get_config() when config.ini is missing or unparseable (defaults fallback) [config loader, exception fallback branch]
  - fix.diff:377-732 — entry point: imported by manager_core.update_user_directory and manager_server; runs at ComfyUI startup (new module manager_migration.py) [new core module]
  - fix.diff:748-752 — entry point: /manager/queue/update_all, /snapshot/remove, /snapshot/restore, /customnode/install/git_url, /customnode/install/pip, /manager/reboot [HTTP route module, 403 body only (not a protection site)]
  - fix.diff:825-846 — entry point: GET /manager/startup_alerts (new route) [HTTP route module, new UI route]
  - prestartup_script.py:88 — entry point: ComfyUI startup: custom_nodes/ComfyUI-Manager/prestartup_script.py [startup script, second independent path implementation]
  - prestartup_script.py:519 — entry point: same startup script: path of startup-scripts/install-scripts.txt, hardcoded from folder_paths.user_directory [startup script, third hardcoded path]
  - prestartup_script.py:795-797 — entry point: same startup script: executes startup-scripts/install-scripts.txt (fix wraps this in an old-ComfyUI block) [startup script, execution sink]
  - fix.diff:968-978 — entry point: browser UI fetches of the Manager routes (handle403Response) [browser UI, 403 message text only (not a protection site)]
- Uncovered routes to confirm (pattern B):   - prestartup_script.py:574-616 — startup-scripts/restore-snapshot.json is executed at boot (cm-cli restore-snapshot) from the same manager data dir; the fix blocks install-scripts.txt on old ComfyUI but leaves this file unblocked, so a file written through the unprotected user-data path still runs at next start (reason to dismiss: restore-snapshot is a documented legitimate feature and its HTTP trigger /snapshot/restore is already gated, so the boot handoff file looks like a trusted internal artifact; still in latest: unknown)
  - prestartup_script.py:124-136 — pip_overrides.json / pip_blacklist.list / pip_auto_fix.list are loaded at boot from the manager data dir and can redirect package installs; on a host without the System User API the fix adds no block for them, only a path change that has no effect there (reason to dismiss: pip_overrides/blacklist are admin convenience files, not the security policy, and the migration already moves the directory; still in latest: unknown)
  - glob/manager_server.py:1475-1541 — config.ini is written by /manager/preview_method, /manager/db_mode, /manager/policy/component, /manager/policy/update and /manager/channel_url_list with no is_allowed_security_level check at any level, including 'strong' (reason to dismiss: these are benign UI preferences chosen from predefined value lists and cannot set security_level itself, so they look unrelated to the policy file; still in latest: unknown)
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

## Environment (`tasks/comfyui-manager-s3/environment/Dockerfile`)
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

## Report to the solver (`tasks/comfyui-manager-s3/instruction.md`)
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

## Tests (`tasks/comfyui-manager-s3/tests/`)
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
- **Wrong-fix patches** go in `build/comfyui-manager-s3/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/comfyui-manager-s3/`:**
- `instruction.md`;
- `task.toml`, from `common/builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/comfyui-manager-s3/manifest.json`:**
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

**Also in `build/comfyui-manager-s3/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `common/builder/templates/` and `common/trial/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I common/gate/gate.py comfyui-manager-s3 --only static
python3 -I common/gate/gate.py comfyui-manager-s3 --only nop
python3 -I common/gate/gate.py comfyui-manager-s3 --only oracle
python3 -I common/gate/gate.py comfyui-manager-s3 --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/comfyui-manager-s3/`;
  - edit only `tasks/comfyui-manager-s3/`, `build/comfyui-manager-s3/` and, for pattern B, the register;
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
