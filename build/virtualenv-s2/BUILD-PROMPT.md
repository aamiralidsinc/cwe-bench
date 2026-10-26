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

Project root: `/home/mara/cwe-bench`. Task: `virtualenv-s2`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: ["GHSA-94P9-XGH2-XP45", "BIT-VIRTUALENV-2026-102930", "CVE-2026-102930", "PYSEC-2026-4011"]; pypa/virtualenv; download of code without integrity check (CWE-494), supply-chain/artifact integrity
- Pinned (vulnerable) commit: d721ff140ce4afdc2a9b76751e4584e25d9fbea6. Published fix: a01ed3e2f239d6ab1fce62c5c7664ccf268fff6d.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v2",
 "model": "deepseek-flash[1m]",
 "entry_id": "2350",
 "advisory_ids": [
  "GHSA-94P9-XGH2-XP45",
  "BIT-VIRTUALENV-2026-102930",
  "CVE-2026-102930",
  "PYSEC-2026-4011"
 ],
 "repo": "pypa/virtualenv",
 "pinned_commit": "d721ff140ce4afdc2a9b76751e4584e25d9fbea6",
 "fix_commits": [
  "a01ed3e2f239d6ab1fce62c5c7664ccf268fff6d"
 ],
 "trust_decision": {
  "summary": "A downloaded seed wheel is trusted to be the PyPI release its filename names: at the pinned commit nothing decides this - download_wheel trusts pip's exit code and the filename it parsed - while the fix decides it in download_wheel (acquire.py) by sha256 against PyPI's JSON release record via verify_wheel_digest in periodic_update.py, and declines to decide at all when PIP_INDEX_URL/PIP_EXTRA_INDEX_URL/PIP_INDEX is set.",
  "evidence": [
   "src/virtualenv/seed/wheels/acquire.py:135-142",
   "src/virtualenv/seed/wheels/acquire.py:145-154",
   "src/virtualenv/seed/wheels/embed/__init__.py:96-108",
   "fix.diff:65",
   "fix.diff:79-81",
   "fix.diff:101-125"
  ]
 },
 "landing_point": {
  "where": "src/virtualenv/seed/wheels/acquire.py:86",
  "why": "download_wheel is the only place virtualenv fetches a seed wheel with `pip download`; a reader of the summary 'downloaded seed wheels are not integrity-checked' lands on this function and on its return at acquire.py:140-142, where the wheel is handed back unexamined."
 },
 "fix_sites": [
  {
   "where": "src/virtualenv/seed/wheels/acquire.py:86-142",
   "entry_point": "virtualenv CLI environment creation with seeding (FromAppData._get_seed_wheels -> get_wheel(download=True)) and the public virtualenv.seed.wheels.get_wheel(download=True) API",
   "module_kind": "seed-wheel acquisition handler"
  },
  {
   "where": "fix.diff:41-45",
   "entry_point": "same download_wheel callers; the gate reads the caller's env (os.environ via Seeder.env), i.e. virtualenv CLI env creation and --upgrade-embed-wheels",
   "module_kind": "module-level defaults/gate in the acquisition module"
  },
  {
   "where": "fix.diff:101-134",
   "entry_point": "virtualenv --upgrade-embed-wheels (manual_upgrade -> do_update -> download_wheel) and the background periodic updater (trigger_update -> do_update)",
   "module_kind": "verification helper in the periodic-update / PyPI-metadata module"
  }
 ],
 "O1_entry_points": 3,
 "O2_out_of_scope_site": {
  "kind": "lower_level_api",
  "where": "src/virtualenv/seed/wheels/periodic_update.py:382-405 (_pypi_get_distribution_info_cached / _pypi_get_distribution_info) - the digest check lands in the periodic-update module and has to reach the private cached PyPI JSON loader, one module away from the download sink"
 },
 "O3_reason_to_dismiss": "A wheel the periodic updater replays from the app-data update log was already hashed when download_wheel fetched it, so checking it again on reload is redundant.",
 "O4_distance": {
  "files": 4,
  "packages": 3,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "A custom/private pip index (or an offline mirror) legitimately serves a rebuilt wheel under the same distribution, version and filename PyPI also uses; a blanket 'hash must equal PyPI's digest' check rejects a wheel that came from exactly the configured source. The caller's env is forwarded straight into the pip subprocess, so this is a supported configuration.",
  "where": "src/virtualenv/seed/wheels/acquire.py:134"
 },
 "O6_input_shapes": [
  "wheel path parsed from pip stdout marker 'Saved ' (src/virtualenv/seed/wheels/acquire.py:148-152)",
  "wheel path parsed from marker 'File was already downloaded ' (a file already sitting in the house) (src/virtualenv/seed/wheels/acquire.py:150)",
  "no marker at all: fall back to any compatible wheel already in the target folder (src/virtualenv/seed/wheels/acquire.py:153-154, 157-172)",
  "no wheel identified anywhere -> RuntimeError instead of an AttributeError (fix.diff:75-77)",
  "distribution or version absent from PyPI's 'releases' map -> not verifiable, let through (fix.diff:113-116, 128-134)",
  "release present but the exact filename not among its files -> let through (fix.diff:134)",
  "release file entry with no sha256 digest -> let through (fix.diff:117-121)",
  "PyPI lookup fails (offline / URLError) -> let through (fix.diff:388-405 path via _pypi_get_distribution_info)",
  "custom index configured through PIP_INDEX_URL, PIP_EXTRA_INDEX_URL or PIP_INDEX -> whole check skipped (fix.diff:41-45)"
 ],
 "O7_producer": {
  "kind": "serializer",
  "where": "src/virtualenv/seed/wheels/periodic_update.py:180-194 (UpdateLog.from_dict / from_app_data) writing and reading the embed update log stored at src/virtualenv/app_data/via_disk_folder.py:104-105, whose filenames are turned back into a Wheel at src/virtualenv/seed/wheels/periodic_update.py:53-56, 68",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "The periodic updater replays a wheel from the persisted embed update log (Wheel(app_data.house / filename)) and seeds it without ever re-reading its bytes; the project's own test asserts the second get_wheel call reuses the cached wheel without downloading.",
   "where": "src/virtualenv/seed/wheels/periodic_update.py:53-56",
   "reason_to_dismiss": "Those wheels were hashed when download_wheel fetched them, so the reload path needs no second check.",
   "distance": "same package (seed/wheels), one module over from acquire.py; state crosses the app-data JSON store at src/virtualenv/app_data/via_disk_folder.py:104-105 and is exercised by tests/unit/seed/wheels/test_acquire.py:135-159",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "Wheels supplied through --extra-search-dir are accepted by from_dir and seeded without any digest check.",
   "where": "src/virtualenv/seed/wheels/bundle.py:54-59",
   "reason_to_dismiss": "The user pointed virtualenv at that directory, so its contents are the user's own trust decision.",
   "distance": "same package as the landing point (seed/wheels/bundle.py, one file)",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "Seeding installs from a cached extracted wheel image keyed only by the wheel file stem; when an image exists it is reused without looking at the wheel file again.",
   "where": "src/virtualenv/seed/embed/via_app_data/via_app_data.py:67-70",
   "reason_to_dismiss": "The image was built from a wheel that had already passed the download check.",
   "distance": "two packages away: seed/wheels -> seed/embed/via_app_data, with the reuse test at src/virtualenv/seed/embed/via_app_data/pip_install/base.py:219-220 and src/virtualenv/seed/embed/via_app_data/via_app_data.py:156-160",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "The PipInvoke seeder installs into the target venv with `pip install --find-links <folder> <dist>==<version>` and only passes --no-index when downloads are disabled, so pip may resolve the requirement itself.",
   "where": "src/virtualenv/seed/embed/pip_invoke.py:57-58",
   "reason_to_dismiss": "The requirement is version-pinned and the matching wheel is already in the --find-links folder, so pip never needs an index.",
   "distance": "two packages away: seed/wheels -> seed/embed (pip_invoke.py)",
   "present_in_latest": "unknown",
   "latest_where": ""
  }
 ],
 "O8b_injection_room": [
  {
   "where": "src/virtualenv/seed/wheels/bundle.py:54-59",
   "sibling": "Digest-verify a wheel taken from --extra-search-dir against PyPI when its filename matches a published release.",
   "why_realistic": "It is the same shape as download_wheel: a wheel arriving from outside the bundle, keyed by distribution/version/for_py_version, and the module already has discover_wheels to name the candidate."
  },
  {
   "where": "src/virtualenv/seed/wheels/periodic_update.py:311-314",
   "sibling": "Verify the copied embed wheel after copy2 into app_data.house, or verify the house copy before it is replayed.",
   "why_realistic": "The maintainer already owns this file and already copies a wheel into the house here; a second entry into the same directory is a natural place for the same check."
  },
  {
   "where": "src/virtualenv/seed/embed/via_app_data/via_app_data.py:67-70",
   "sibling": "Key the cached wheel image on a digest of the wheel rather than its stem, or re-verify the wheel when the image is reused.",
   "why_realistic": "The cache key already names the installer class and the wheel stem; extending it with a hash is a small, natural change and the reuse branch is right there at line 70."
  }
 ],
 "O9_family": "download of code without integrity check (CWE-494), supply-chain/artifact integrity",
 "O9_dos": false,
 "O10_build": {
  "language": "Python (requires-python >=3.9)",
  "toolchain": "hatchling + hatch-vcs build backend; pytest/tox for tests; no compiled extensions",
  "services": [],
  "offline_after_build": true,
  "project_tests": "tests/unit/seed/wheels/test_acquire.py (mocks acquire.Popen), tests/unit/seed/wheels/test_periodic_update.py (mocks urlopen), tests/unit/seed/wheels/test_bundle.py (bundled-wheel sha256 checks), tests/unit/seed/embed/test_bootstrap_link_via_app_data.py and test_pip_invoke.py; the live path needs PyPI, but every existing test mocks the subprocess and the JSON fetch, so the suite runs offline."
 },
 "O11_fix_minutes": 45,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "src/virtualenv/seed/wheels/acquire.py, src/virtualenv/seed/wheels/periodic_update.py",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 0,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Compare the wheel's sha256 with a digest fetched from PyPI inside download_wheel only, then verify by re-running that one path and stop."
 },
 "out_of_scope_notes": [
  "Other hardening already in this tree (zip-slip guard at src/virtualenv/seed/embed/via_app_data/pip_install/base.py:26-41, activation argument quoting) belongs to different advisories and was not assessed.",
  "Limitation documented in the fix itself: a pip.conf/PIP_CONFIG_FILE index redirect is invisible to the index gate (fix.diff:34-40); noted as a fix-internal limit, not pursued as an additional route."
 ],
 "unverified": [
  "Repository size in MB could not be measured (no shell available); the src tree is about 106 files including four bundled wheels, so the tiny_repo threshold was not decided and the flag is left off.",
  "No latest release or latest tree was provided ('none'), so present_in_latest for every O8 route is unknown.",
  "Whether any hidden test exercises a real PyPI round trip: tests here mock urlopen, so the affected behaviour was not executed and no code was run."
 ]
}
  ```
- Published fix sites:   - src/virtualenv/seed/wheels/acquire.py:86-142 — entry point: virtualenv CLI environment creation with seeding (FromAppData._get_seed_wheels -> get_wheel(download=True)) and the public virtualenv.seed.wheels.get_wheel(download=True) API [seed-wheel acquisition handler]
  - fix.diff:41-45 — entry point: same download_wheel callers; the gate reads the caller's env (os.environ via Seeder.env), i.e. virtualenv CLI env creation and --upgrade-embed-wheels [module-level defaults/gate in the acquisition module]
  - fix.diff:101-134 — entry point: virtualenv --upgrade-embed-wheels (manual_upgrade -> do_update -> download_wheel) and the background periodic updater (trigger_update -> do_update) [verification helper in the periodic-update / PyPI-metadata module]
- Uncovered routes to confirm (pattern B):   - src/virtualenv/seed/wheels/periodic_update.py:53-56 — The periodic updater replays a wheel from the persisted embed update log (Wheel(app_data.house / filename)) and seeds it without ever re-reading its bytes; the project's own test asserts the second get_wheel call reuses the cached wheel without downloading. (reason to dismiss: Those wheels were hashed when download_wheel fetched them, so the reload path needs no second check.; still in latest: unknown)
  - src/virtualenv/seed/wheels/bundle.py:54-59 — Wheels supplied through --extra-search-dir are accepted by from_dir and seeded without any digest check. (reason to dismiss: The user pointed virtualenv at that directory, so its contents are the user's own trust decision.; still in latest: unknown)
  - src/virtualenv/seed/embed/via_app_data/via_app_data.py:67-70 — Seeding installs from a cached extracted wheel image keyed only by the wheel file stem; when an image exists it is reused without looking at the wheel file again. (reason to dismiss: The image was built from a wheel that had already passed the download check.; still in latest: unknown)
  - src/virtualenv/seed/embed/pip_invoke.py:57-58 — The PipInvoke seeder installs into the target venv with `pip install --find-links <folder> <dist>==<version>` and only passes --no-index when downloads are disabled, so pip may resolve the requirement itself. (reason to dismiss: The requirement is version-pinned and the matching wheel is already in the --find-links folder, so pip never needs an index.; still in latest: unknown)
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

## Environment (`tasks/virtualenv-s2/environment/Dockerfile`)
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

## Report to the solver (`tasks/virtualenv-s2/instruction.md`)
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

## Tests (`tasks/virtualenv-s2/tests/`)
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
- **Wrong-fix patches** go in `build/virtualenv-s2/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/virtualenv-s2/`:**
- `instruction.md`;
- `task.toml`, from `common/builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/virtualenv-s2/manifest.json`:**
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

**Also in `build/virtualenv-s2/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `common/builder/templates/` and `common/trial/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I common/gate/gate.py virtualenv-s2 --only static
python3 -I common/gate/gate.py virtualenv-s2 --only nop
python3 -I common/gate/gate.py virtualenv-s2 --only oracle
python3 -I common/gate/gate.py virtualenv-s2 --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/virtualenv-s2/`;
  - edit only `tasks/virtualenv-s2/`, `build/virtualenv-s2/` and, for pattern B, the register;
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
