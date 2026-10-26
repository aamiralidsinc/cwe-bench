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

Project root: `/home/mara/cwe-bench`. Task: `onionshare-s2`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: ["GHSA-22P9-R2F5-22MF", "CVE-2026-54706", "PYSEC-2026-3585"]; onionshare/onionshare; CWE-59 improper link resolution before file access (symlink following) causing disclosure of files outside the shared roots - file-system path containment
- Pinned (vulnerable) commit: 8cc75e1d7e88bd31f7276733449d412bf71c8999. Published fix: 48f31cfac077fcc9c04c67c2a6dbf87d956f5eec.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v2",
 "model": "deepseek-flash",
 "entry_id": "16",
 "advisory_ids": [
  "GHSA-22P9-R2F5-22MF",
  "CVE-2026-54706",
  "PYSEC-2026-3585"
 ],
 "repo": "onionshare/onionshare",
 "pinned_commit": "8cc75e1d7e88bd31f7276733449d412bf71c8999",
 "fix_commits": [
  "48f31cfac077fcc9c04c67c2a6dbf87d956f5eec"
 ],
 "trust_decision": {
  "summary": "In share and website mode a path may be handed to the client only if os.path.realpath(path) equals a selected root directory or lies under root + os.sep; the decision is taken in the new SendBaseModeWeb._is_path_contained and enforced at every read of a shared path: the file inventory walk (set_file_info), the individual-file stream (stream_individual_file) and the zip bundle (ZipWriter.add_file/add_dir).",
  "evidence": [
   "cli/onionshare_cli/web/send_base_mode.py:73-132",
   "cli/onionshare_cli/web/send_base_mode.py:200-221",
   "cli/onionshare_cli/web/share_mode.py:575-601",
   "fix.diff:68-81",
   "fix.diff:135-139",
   "fix.diff:190-197",
   "fix.diff:218-225"
  ]
 },
 "landing_point": {
  "where": "cli/onionshare_cli/web/send_base_mode.py:113",
  "why": "The summary says OnionShare follows symlinks in shared directories, so the first place an engineer looks is the os.walk(filename) that fills self.files with os.path.join(root, nested_filename), i.e. the inventory of everything the web layer will serve."
 },
 "fix_sites": [
  {
   "where": "fix.diff:13-17",
   "entry_point": "onionshare-cli --share/--website <paths> (positional filename arg, cli/onionshare_cli/__init__.py:184-194) and the desktop file-selection list",
   "module_kind": "shared web base class (onionshare_cli.web.send_base_mode)"
  },
  {
   "where": "fix.diff:26-28",
   "entry_point": "set_file_info() public API, reached from cli/onionshare_cli/__init__.py:433,442 and desktop threads",
   "module_kind": "shared web base class"
  },
  {
   "where": "fix.diff:32-34",
   "entry_point": "GET / and GET /<path:path> in share and website mode (inventory feeds render_logic at cli/onionshare_cli/web/share_mode.py:431-457 and cli/onionshare_cli/web/website_mode.py:71-97)",
   "module_kind": "shared web base class"
  },
  {
   "where": "fix.diff:43",
   "entry_point": "set_file_info() public API (nested directory descent)",
   "module_kind": "shared web base class"
  },
  {
   "where": "fix.diff:51-57",
   "entry_point": "set_file_info() public API (nested files inside a shared directory)",
   "module_kind": "shared web base class"
  },
  {
   "where": "fix.diff:68-81",
   "entry_point": "internal helper used by GET /<path:path> (share and website) and GET /download (share)",
   "module_kind": "shared web base class"
  },
  {
   "where": "fix.diff:135-139",
   "entry_point": "GET /<path:path> individual-file stream in share mode (share_mode.py:445-447, when autostop_sharing is off) and website mode (website_mode.py:84,97,111)",
   "module_kind": "web request handler sink"
  },
  {
   "where": "fix.diff:190-197",
   "entry_point": "GET /download in share mode (cli/onionshare_cli/web/share_mode.py:166-169)",
   "module_kind": "archive writer / lower-level bundling API (class ZipWriter, constructible with web=None)"
  },
  {
   "where": "fix.diff:218-225",
   "entry_point": "GET /download in share mode (directory entries in the zip)",
   "module_kind": "archive writer / lower-level bundling API"
  }
 ],
 "O1_entry_points": 4,
 "O2_out_of_scope_site": {
  "kind": "lower_level_api",
  "where": "cli/onionshare_cli/web/share_mode.py:575-601 (class ZipWriter, add_file and add_dir)"
 },
 "O3_reason_to_dismiss": "ZipWriter is a generic archive helper that predates this advisory (constructed without a web object in cli/tests/conftest.py:93-114) and its input is already the filtered inventory, so the bundle is treated as covered; likewise the single-file /download path is 'just the file the user named'.",
 "O4_distance": {
  "files": 5,
  "packages": 3,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "A path the user explicitly selects that is itself a symlink, or a shared directory whose legitimate content is symlinked in (a website with symlinked assets, a dropbox folder of links), is silently dropped by the unconditional os.path.islink(filename): continue at root level, so a share that used to serve that file now serves nothing while the GUI size display still counts it.",
  "where": "fix.diff:26-28 (also fix.diff:74-75, where an empty selected_roots returns True for file-only shares); pinned behaviour that is being changed: cli/onionshare_cli/web/send_base_mode.py:105-107 and cli/onionshare_cli/web/share_mode.py:446-447"
 },
 "O6_input_shapes": [
  "root-level symlink to a regular file passed as a share argument",
  "root-level symlink to a directory passed as a share argument",
  "symlinked file directly inside a shared directory",
  "symlinked file at depth 2+ inside a shared directory",
  "symlinked directory encountered inside os.walk (dirnames, not descended)",
  "single-directory argument expanded through os.listdir (len(filenames)==1 and isdir)",
  "multi-argument list of files and directories (selected_roots only collects dirs)",
  "zip-bundle download of directories vs individual-file streaming of one file"
 ],
 "O7_producer": {
  "kind": "config_loader",
  "where": "cli/onionshare_cli/mode_settings.py:56-59 and :70-71 (share/website 'filenames' defaults) loaded from the persisted JSON at cli/onionshare_cli/mode_settings.py:128-145, then trusted without re-validation at cli/onionshare_cli/__init__.py:283-287 ('this persistent json file already has validated the filenames'); desktop saves the same list at desktop/onionshare/tab/mode/file_selection.py:520-528",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "Share mode GET /download when the share resolves to exactly one file and no directory: build_zipfile_list sets download_filename from the raw argument list and gzip-compresses it at setup, then download()/generate() stream it, with no islink or containment check anywhere on that branch (so a share of a symlink, or a persistent 'filenames' entry that is now a symlink, discloses the target).",
   "where": "cli/onionshare_cli/web/share_mode.py:491-513 and cli/onionshare_cli/web/share_mode.py:166-255",
   "reason_to_dismiss": "It is the 'single file' convenience path, not a directory walk, and the file was named explicitly by the user, so it reads as intentional sharing rather than a symlink discovered in a shared folder.",
   "distance": "same file as the ZipWriter half of the fix, one module away from the landing point in send_base_mode.py",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "Directory-listing route stats each name returned by os.listdir(filesystem_path), so a symlink inside a shared directory is still listed and its target's size is reported (os.path.getsize follows the link) even though the entry is no longer in self.files; the fix only reformatted this function.",
   "where": "cli/onionshare_cli/web/send_base_mode.py:166-196 (called from cli/onionshare_cli/web/share_mode.py:438-442 and cli/onionshare_cli/web/website_mode.py:89-93)",
   "reason_to_dismiss": "The listing discloses only existence and a byte size, not file content, and the fix's tests treat inventory membership rather than listing output as the property.",
   "distance": "same function the fix reformatted, in the landing-point file",
   "present_in_latest": "unknown",
   "latest_where": ""
  }
 ],
 "O8b_injection_room": [
  {
   "where": "cli/onionshare_cli/web/share_mode.py:473-539",
   "sibling": "A second bundle builder next to build_zipfile_list, e.g. a 'download just this folder' endpoint, reusing ZipWriter or re-implementing the same walk.",
   "why_realistic": "The maintainer already wrote two bundling paths in one function (single-file gzip branch vs ZipWriter zip branch) and the fix guarded only the second, so a third sibling written later in the same style is credible."
  },
  {
   "where": "desktop/onionshare/tab/mode/share_mode/__init__.py:415-423",
   "sibling": "_compute_total_size mirrors common.dir_size but calls os.path.getsize on a file argument without an islink test, so it follows a symlinked entry.",
   "why_realistic": "It is a GUI-side copy of the same size computation the CLI already hardened in common.dir_size (cli/onionshare_cli/common.py:594-605), exactly the kind of duplicated convenience helper a maintainer writes."
  },
  {
   "where": "cli/onionshare_cli/web/receive_mode.py:97-135",
   "sibling": "A receive-mode route that serves back files from request.receive_mode_dir, the mirror of share mode's individual-file stream.",
   "why_realistic": "Receive mode already records the on-disk directory per upload (receive_mode.py:114-126), so a 'preview/download what was uploaded' endpoint reusing the same dir would be a natural follow-up feature."
  }
 ],
 "O9_family": "CWE-59 improper link resolution before file access (symlink following) causing disclosure of files outside the shared roots - file-system path containment",
 "O9_dos": false,
 "O10_build": {
  "language": "Python 3.10-3.12",
  "toolchain": "Poetry (cli/pyproject.toml, cli/poetry.lock), pytest >=7.2 with cli/tests/pytest.ini; pure Python, no compile step",
  "services": [],
  "offline_after_build": true,
  "project_tests": "cli/tests/test_cli_web.py builds a Web object and drives the Flask test client offline (test_share_mode at line 75, test_share_mode_autostop_sharing_off at line 111); cli/tests/test_range_request.py covers the download range path; ZipWriter fixtures at cli/tests/conftest.py:93-114. Tor-dependent tests are skipped unless --runtor (cli/tests/conftest.py:26-32). The fix adds cli/tests/test_cli_web_symlink.py, which is not present at the pinned commit."
 },
 "O11_fix_minutes": 45,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "cli/onionshare_cli/web/send_base_mode.py, cli/onionshare_cli/web/share_mode.py",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Add a realpath/containment check only where the report points - filter symlinks while building self.files or guard stream_individual_file - which leaves ZipWriter's /download bundle and the single-file /download branch serving the target."
 },
 "out_of_scope_notes": [
  "Receive mode joins a client-supplied name onto the receive directory at cli/onionshare_cli/web/receive_mode.py:112-114; that is a write-direction link/path concern, not this advisory's disclosure property, so it was not pursued."
 ],
 "unverified": [
  "repo_mb could not be measured (no shell in this session), so tiny_repo/giant_repo were left unflagged; the pinned tree lists about 1250 files including desktop locales and bundled resources.",
  "present_in_latest for both O8 routes is unknown: no latest release tree was supplied, so I could not cite latest/path:line. The published fix diff has no hunk in share_mode.py's download()/build_zipfile_list region (fix.diff:1-231), so the single-file /download route appears still open at the fix commit itself.",
  "Nothing was executed against the project (per instructions); the single-file /download disclosure is a reading of cli/onionshare_cli/web/share_mode.py:491-539 plus :166-255, not a run.",
  "O1 was counted as 4 (share index route, share /download, website path route, set_file_info public API); a route-only reading of the same evidence would give 3.",
  "A residual gap in the fix's own logic was reasoned about but not run: because selected_roots stores os.path.realpath of every directory argument (fix.diff:13-17), a shared directory that is itself a symlink becomes its own containment root, so its target's contents still pass _is_path_contained; I listed it as injection room rather than as an O8 route because the fix does touch that code."
 ]
}
  ```
- Published fix sites:   - fix.diff:13-17 — entry point: onionshare-cli --share/--website <paths> (positional filename arg, cli/onionshare_cli/__init__.py:184-194) and the desktop file-selection list [shared web base class (onionshare_cli.web.send_base_mode)]
  - fix.diff:26-28 — entry point: set_file_info() public API, reached from cli/onionshare_cli/__init__.py:433,442 and desktop threads [shared web base class]
  - fix.diff:32-34 — entry point: GET / and GET /<path:path> in share and website mode (inventory feeds render_logic at cli/onionshare_cli/web/share_mode.py:431-457 and cli/onionshare_cli/web/website_mode.py:71-97) [shared web base class]
  - fix.diff:43 — entry point: set_file_info() public API (nested directory descent) [shared web base class]
  - fix.diff:51-57 — entry point: set_file_info() public API (nested files inside a shared directory) [shared web base class]
  - fix.diff:68-81 — entry point: internal helper used by GET /<path:path> (share and website) and GET /download (share) [shared web base class]
  - fix.diff:135-139 — entry point: GET /<path:path> individual-file stream in share mode (share_mode.py:445-447, when autostop_sharing is off) and website mode (website_mode.py:84,97,111) [web request handler sink]
  - fix.diff:190-197 — entry point: GET /download in share mode (cli/onionshare_cli/web/share_mode.py:166-169) [archive writer / lower-level bundling API (class ZipWriter, constructible with web=None)]
  - fix.diff:218-225 — entry point: GET /download in share mode (directory entries in the zip) [archive writer / lower-level bundling API]
- Uncovered routes to confirm (pattern B):   - cli/onionshare_cli/web/share_mode.py:491-513 and cli/onionshare_cli/web/share_mode.py:166-255 — Share mode GET /download when the share resolves to exactly one file and no directory: build_zipfile_list sets download_filename from the raw argument list and gzip-compresses it at setup, then download()/generate() stream it, with no islink or containment check anywhere on that branch (so a share of a symlink, or a persistent 'filenames' entry that is now a symlink, discloses the target). (reason to dismiss: It is the 'single file' convenience path, not a directory walk, and the file was named explicitly by the user, so it reads as intentional sharing rather than a symlink discovered in a shared folder.; still in latest: unknown)
  - cli/onionshare_cli/web/send_base_mode.py:166-196 (called from cli/onionshare_cli/web/share_mode.py:438-442 and cli/onionshare_cli/web/website_mode.py:89-93) — Directory-listing route stats each name returned by os.listdir(filesystem_path), so a symlink inside a shared directory is still listed and its target's size is reported (os.path.getsize follows the link) even though the entry is no longer in self.files; the fix only reformatted this function. (reason to dismiss: The listing discloses only existence and a byte size, not file content, and the fix's tests treat inventory membership rather than listing output as the property.; still in latest: unknown)
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

## Environment (`tasks/onionshare-s2/environment/Dockerfile`)
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

## Report to the solver (`tasks/onionshare-s2/instruction.md`)
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

## Tests (`tasks/onionshare-s2/tests/`)
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
- **Wrong-fix patches** go in `build/onionshare-s2/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/onionshare-s2/`:**
- `instruction.md`;
- `task.toml`, from `common/builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/onionshare-s2/manifest.json`:**
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

**Also in `build/onionshare-s2/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `common/builder/templates/` and `common/trial/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I common/gate/gate.py onionshare-s2 --only static
python3 -I common/gate/gate.py onionshare-s2 --only nop
python3 -I common/gate/gate.py onionshare-s2 --only oracle
python3 -I common/gate/gate.py onionshare-s2 --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/onionshare-s2/`;
  - edit only `tasks/onionshare-s2/`, `build/onionshare-s2/` and, for pattern B, the register;
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
