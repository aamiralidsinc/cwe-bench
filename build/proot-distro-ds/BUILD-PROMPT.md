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

Project root: `/home/mara/cwe-bench`. Task: `proot-distro-ds`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: ["GHSA-9XQ3-3FQG-4VG7", "CVE-2026-54574", "PYSEC-2026-3608"]; termux/proot-distro; CWE-61 symlink following / path traversal on archive extraction (A01)
- Pinned (vulnerable) commit: f5ff24beef945fcfe04831a913602169c17e97f6. Published fix: a96d7a9667f38e45d812614852ee3915d1c0ae45.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v2",
 "model": "claude-opus-5-5",
 "entry_id": "2641",
 "advisory_ids": [
  "GHSA-9XQ3-3FQG-4VG7",
  "CVE-2026-54574",
  "PYSEC-2026-3608"
 ],
 "repo": "termux/proot-distro",
 "pinned_commit": "f5ff24beef945fcfe04831a913602169c17e97f6",
 "fix_commits": [
  "a96d7a9667f38e45d812614852ee3915d1c0ae45"
 ],
 "trust_decision": {
  "summary": "Each archive member's host destination is decided by lexically joining its (dot-dot-filtered) name onto the rootfs/container dir, with no check that intermediate path components are not symlinks planted by earlier members; the fix adds per-hop clamped symlink resolution (_safe_resolve) at every write/read site.",
  "evidence": [
   "proot_distro/helpers/tar_extract.py:125-140",
   "proot_distro/helpers/tar_extract.py:215-222",
   "proot_distro/commands/restore.py:136-183",
   "proot_distro/commands/restore.py:268-327",
   "proot_distro/helpers/build_engine/copy_step.py:432-437",
   "fix.diff:259-309"
  ]
 },
 "landing_point": {
  "where": "proot_distro/helpers/tar_extract.py:136-140",
  "why": "Summary names `proot-distro install` + malicious tar; install_local.extract_plain_tar and docker layers.apply_layer both delegate to extract_tar_to_rootfs, whose _process_member builds parent/dest by plain os.path.join."
 },
 "fix_sites": [
  {
   "where": "proot_distro/helpers/tar_extract.py:136-140",
   "entry_point": "CLI `proot-distro install` (local tar / URL / docker pull / local OCI via apply_layer)",
   "module_kind": "shared helper (core extractor)"
  },
  {
   "where": "proot_distro/helpers/tar_extract.py:147-148",
   "entry_point": "CLI `proot-distro install` (dir member onto an existing symlink)",
   "module_kind": "shared helper (core extractor)"
  },
  {
   "where": "proot_distro/helpers/tar_extract.py:96-104",
   "entry_point": "CLI `proot-distro install` (deferred hardlink copy, both endpoints)",
   "module_kind": "shared helper (core extractor)"
  },
  {
   "where": "proot_distro/helpers/tar_extract.py:205-222",
   "entry_point": "CLI `proot-distro install` (hardlink linkname)",
   "module_kind": "shared helper (core extractor)"
  },
  {
   "where": "proot_distro/commands/restore.py:292",
   "entry_point": "CLI `proot-distro restore` (file or stdin backup)",
   "module_kind": "second implementation (separate streaming extractor in commands/)"
  },
  {
   "where": "proot_distro/commands/restore.py:320-327",
   "entry_point": "CLI `proot-distro restore` (hardlink read source)",
   "module_kind": "second implementation"
  },
  {
   "where": "proot_distro/helpers/build_engine/copy_step.py:432-437",
   "entry_point": "CLI `proot-distro build` (Dockerfile COPY/ADD, incl. ADD auto-extracted tar)",
   "module_kind": "build engine step (third materialiser, file_map based)"
  }
 ],
 "O1_entry_points": 3,
 "O2_out_of_scope_site": {
  "kind": "second_implementation",
  "where": "proot_distro/commands/restore.py:268-355 (own tar loop, not using tar_extract) and proot_distro/helpers/build_engine/copy_step.py:432-479 (file_map materialiser for `build`)"
 },
 "O3_reason_to_dismiss": "Advisory says `install`; restore only accepts archives 'created by proot-distro backup' (restore.py:263-265) and build's COPY/ADD inputs come from the user's own Dockerfile/context, so a solver can argue neither ingests attacker archives.",
 "O4_distance": {
  "files": 7,
  "packages": 4,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Legitimate symlinks in images (merged-usr `lib -> usr/lib`, absolute `/var/run -> /run`) must still be followed, re-rooted at the rootfs, so later layers/members writing through them land inside the rootfs; an over-broad fix that skips or rejects any member whose parent is a symlink breaks layered OCI installs, restore of normal backups and COPY into such paths.",
  "where": "fix.diff:142-150; fix.diff:303-306; proot_distro/helpers/docker/layers.py:97-102"
 },
 "O6_input_shapes": [
  "symlink member with absolute target (`evil -> /`) then a file member written through it",
  "symlink member with relative ascending target (`evil -> ../../`) then a file member through it",
  "directory member whose name is already an existing symlink (makedirs/chmod follow it)",
  "hardlink whose linkname routes through a planted symlink (host file read into rootfs)",
  "hardlink member processed before the symlink that redirects it (deferred copy re-resolved at copy time)",
  "symlink loops / excessive chains (return None, skip member)",
  "restore: new `<name>/rootfs/...` layout, legacy `installed-rootfs/<name>/...` layout and `<name>/<other>` back-compat layout, all resolved relative to container_dir",
  "build: file_map arcnames from ADD-extracted tar, context directory trees with symlinks, and COPY --from stage"
 ],
 "O7_producer": {
  "kind": "mapper",
  "where": "proot_distro/commands/restore.py:122-183 (_dest_path maps member names, incl. legacy prefix, to host paths)",
  "check_calls_producer": true
 },
 "O8_uncovered_routes": [
  {
   "route": "install post-extraction fixups write/append/chmod etc/resolv.conf, etc/hosts, etc/passwd|shadow|group|gshadow via raw os.path.join, following an archive-planted `etc` symlink on the host (the fix deliberately leaves such symlinks on disk).",
   "where": "proot_distro/commands/install.py:263-272",
   "reason_to_dismiss": "Fixups write fixed, trusted content to fixed paths after extraction, not archive data; write_hosts already unlinks the final component (proot_distro/helpers/rootfs.py:53-60), so it looks handled.",
   "distance": "same command, different module: proot_distro/helpers/rootfs.py:38-47, 50-61, 76-134",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "build engine also runs write_resolv_conf/write_hosts on stage rootfs assembled from pulled layers.",
   "where": "proot_distro/helpers/build_engine/engine.py:359-360",
   "reason_to_dismiss": "Build is a separate command; base images are 'trusted' by the Dockerfile author.",
   "distance": "helpers/build_engine package, far from tar_extract",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "login (crossing install->login state) chmods rootfs/tmp to 01777 and writes etc/profile.d/termux-profile.sh via raw joins, following a `tmp` or `etc` symlink planted by the installed archive.",
   "where": "proot_distro/commands/login/proot_cmd.py:180-185",
   "reason_to_dismiss": "Login is a different command that runs after install; the advisory is about extraction.",
   "distance": "commands/login package; also proot_distro/commands/login/env.py:95-133",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "restore deferred dir-mode chmod: a dir with a mode lacking owner rwx is queued, then a later member replaces it with a symlink, and the final os.chmod follows it to a host path (fix clamps only the parent at queue time).",
   "where": "proot_distro/commands/restore.py:296-302",
   "reason_to_dismiss": "Fixed site's _safe_dest already ran on that path; deferred chmod looks like cosmetic mode restoration.",
   "distance": "same file as fix, 60 lines below; final loop at proot_distro/commands/restore.py:365-369",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "tar_extract deferred directory utime follows a symlink that a later member put in place of the directory (timestamps only).",
   "where": "proot_distro/helpers/tar_extract.py:109-113",
   "reason_to_dismiss": "Only mtime is changed; low impact.",
   "distance": "same file as landing point",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "build _materialise_files dir-kind entry: makedirs(exist_ok)+chmod on a final component that is an existing symlink (from base image/earlier layer) follows it to the host; fix clamps the parent only and does not add the islink drop it added in tar_extract.",
   "where": "proot_distro/helpers/build_engine/copy_step.py:444-449",
   "reason_to_dismiss": "The published fix already touched this function; final-component handling looks deliberate ('never a same-named symlink's target').",
   "distance": "helpers/build_engine package",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "COPY --from=<stage|image> source check is lexical only; a symlinked component in the source stage rootfs makes the read follow to a host file that is packed into the layer (same read-side issue the fix clamped for hardlink sources).",
   "where": "proot_distro/helpers/build_engine/copy_step.py:210-227",
   "reason_to_dismiss": "Read side, Dockerfile-author-controlled path, and the advisory is about writes.",
   "distance": "helpers/build_engine package",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "WORKDIR makedirs+chmod 0755 on raw-joined host path follows base-image symlinks out of the stage rootfs.",
   "where": "proot_distro/helpers/build_engine/handlers.py:147-156",
   "reason_to_dismiss": "Path is from the Dockerfile author, not an archive.",
   "distance": "helpers/build_engine package",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "copy/sync `name:path` specs are contained lexically only (normpath+startswith), so guest symlinks in the path redirect host-side writes outside the rootfs.",
   "where": "proot_distro/paths.py:83-91",
   "reason_to_dismiss": "User-invoked copy between host and container; not archive extraction (borderline for the advisory's property).",
   "distance": "top-level paths.py, used by proot_distro/commands/copy.py:54-117 and proot_distro/commands/sync.py:406-501",
   "present_in_latest": "unknown",
   "latest_where": ""
  }
 ],
 "O8b_injection_room": [
  {
   "where": "proot_distro/helpers/rootfs.py:38-47",
   "sibling": "another post-install fixup (e.g. etc/machine-id or etc/timezone writer) using os.path.join(rootfs, 'etc', ...)",
   "why_realistic": "The module exists to hold such Termux integration fixups and is reused by other entry points (rootfs.py:21-25)."
  },
  {
   "where": "proot_distro/helpers/tar_extract.py:165-178",
   "sibling": "whiteout handler that resolves the whited-out sibling's path by following the final component",
   "why_realistic": "OCI whiteouts are handled ad hoc in the same extractor; a maintainer extending opaque-dir handling could easily join paths naively."
  },
  {
   "where": "proot_distro/commands/restore.py:173-174",
   "sibling": "restore post-step that rewrites manifest.json or applies rootfs fixups after extraction",
   "why_realistic": "install already writes manifest + fixups; parity for restore is a natural feature."
  }
 ],
 "O9_family": "CWE-61 symlink following / path traversal on archive extraction (A01)",
 "O9_dos": false,
 "O10_build": {
  "language": "Python",
  "toolchain": "CPython 3 standard library only (tarfile, shutil, os); pyproject.toml packaging",
  "services": [],
  "offline_after_build": true,
  "project_tests": "none: no test directory or test files in the pinned tree; the fix diff adds no tests"
 },
 "O11_fix_minutes": 120,
 "O12_red_flags": [
  "tiny_repo"
 ],
 "O13_recall_risk": "medium",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "proot_distro/helpers/tar_extract.py, proot_distro/commands/restore.py, proot_distro/helpers/build_engine/copy_step.py",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 0,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Add a realpath/commonpath containment check (or skip symlinked parents) in tar_extract._process_member only: it misses restore/build and either breaks legit absolute symlinks or leaves the deferred hardlink and post-install fixup paths open."
 },
 "out_of_scope_notes": [
  "proot_distro/l2s.py:123 rewrites l2s symlink targets during migration; not examined.",
  "ADD <url> downloads use AuthStrippingRedirectHandler (copy_step.py:239); redirect handling is a different concern."
 ],
 "unverified": [
  "repo_mb not measured (no shell used); tiny_repo inferred from ~80 small Python source files plus one screenshot.png.",
  "Whether pinned-commit routes are still present upstream: no latest release given, so present_in_latest is unknown everywhere.",
  "O8 login route impact assumes the archive's `tmp`/`etc` symlinks survive install unchanged; extraction keeps symlinks verbatim (proot_distro/helpers/tar_extract.py:192-196), but the full login flow was not traced.",
  "Whether `proot-distro reset` reaches extraction through install was not checked, so it is not counted in O1.",
  "recall_risk is a judgement: the advisory is post-cutoff and the fix commit message is explicit."
 ]
}
  ```
- Published fix sites:   - proot_distro/helpers/tar_extract.py:136-140 — entry point: CLI `proot-distro install` (local tar / URL / docker pull / local OCI via apply_layer) [shared helper (core extractor)]
  - proot_distro/helpers/tar_extract.py:147-148 — entry point: CLI `proot-distro install` (dir member onto an existing symlink) [shared helper (core extractor)]
  - proot_distro/helpers/tar_extract.py:96-104 — entry point: CLI `proot-distro install` (deferred hardlink copy, both endpoints) [shared helper (core extractor)]
  - proot_distro/helpers/tar_extract.py:205-222 — entry point: CLI `proot-distro install` (hardlink linkname) [shared helper (core extractor)]
  - proot_distro/commands/restore.py:292 — entry point: CLI `proot-distro restore` (file or stdin backup) [second implementation (separate streaming extractor in commands/)]
  - proot_distro/commands/restore.py:320-327 — entry point: CLI `proot-distro restore` (hardlink read source) [second implementation]
  - proot_distro/helpers/build_engine/copy_step.py:432-437 — entry point: CLI `proot-distro build` (Dockerfile COPY/ADD, incl. ADD auto-extracted tar) [build engine step (third materialiser, file_map based)]
- Uncovered routes to confirm (pattern B):   - proot_distro/commands/install.py:263-272 — install post-extraction fixups write/append/chmod etc/resolv.conf, etc/hosts, etc/passwd|shadow|group|gshadow via raw os.path.join, following an archive-planted `etc` symlink on the host (the fix deliberately leaves such symlinks on disk). (reason to dismiss: Fixups write fixed, trusted content to fixed paths after extraction, not archive data; write_hosts already unlinks the final component (proot_distro/helpers/rootfs.py:53-60), so it looks handled.; still in latest: unknown)
  - proot_distro/helpers/build_engine/engine.py:359-360 — build engine also runs write_resolv_conf/write_hosts on stage rootfs assembled from pulled layers. (reason to dismiss: Build is a separate command; base images are 'trusted' by the Dockerfile author.; still in latest: unknown)
  - proot_distro/commands/login/proot_cmd.py:180-185 — login (crossing install->login state) chmods rootfs/tmp to 01777 and writes etc/profile.d/termux-profile.sh via raw joins, following a `tmp` or `etc` symlink planted by the installed archive. (reason to dismiss: Login is a different command that runs after install; the advisory is about extraction.; still in latest: unknown)
  - proot_distro/commands/restore.py:296-302 — restore deferred dir-mode chmod: a dir with a mode lacking owner rwx is queued, then a later member replaces it with a symlink, and the final os.chmod follows it to a host path (fix clamps only the parent at queue time). (reason to dismiss: Fixed site's _safe_dest already ran on that path; deferred chmod looks like cosmetic mode restoration.; still in latest: unknown)
  - proot_distro/helpers/tar_extract.py:109-113 — tar_extract deferred directory utime follows a symlink that a later member put in place of the directory (timestamps only). (reason to dismiss: Only mtime is changed; low impact.; still in latest: unknown)
  - proot_distro/helpers/build_engine/copy_step.py:444-449 — build _materialise_files dir-kind entry: makedirs(exist_ok)+chmod on a final component that is an existing symlink (from base image/earlier layer) follows it to the host; fix clamps the parent only and does not add the islink drop it added in tar_extract. (reason to dismiss: The published fix already touched this function; final-component handling looks deliberate ('never a same-named symlink's target').; still in latest: unknown)
  - proot_distro/helpers/build_engine/copy_step.py:210-227 — COPY --from=<stage|image> source check is lexical only; a symlinked component in the source stage rootfs makes the read follow to a host file that is packed into the layer (same read-side issue the fix clamped for hardlink sources). (reason to dismiss: Read side, Dockerfile-author-controlled path, and the advisory is about writes.; still in latest: unknown)
  - proot_distro/helpers/build_engine/handlers.py:147-156 — WORKDIR makedirs+chmod 0755 on raw-joined host path follows base-image symlinks out of the stage rootfs. (reason to dismiss: Path is from the Dockerfile author, not an archive.; still in latest: unknown)
  - proot_distro/paths.py:83-91 — copy/sync `name:path` specs are contained lexically only (normpath+startswith), so guest symlinks in the path redirect host-side writes outside the rootfs. (reason to dismiss: User-invoked copy between host and container; not archive extraction (borderline for the advisory's property).; still in latest: unknown)
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

## Environment (`tasks/proot-distro-ds/environment/Dockerfile`)
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

## Report to the solver (`tasks/proot-distro-ds/instruction.md`)
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

## Tests (`tasks/proot-distro-ds/tests/`)
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
- **Wrong-fix patches** go in `build/proot-distro-ds/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/proot-distro-ds/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/proot-distro-ds/manifest.json`:**
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

**Also in `build/proot-distro-ds/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py proot-distro-ds --only static
python3 -I builder/gate.py proot-distro-ds --only nop
python3 -I builder/gate.py proot-distro-ds --only oracle
python3 -I builder/gate.py proot-distro-ds --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/proot-distro-ds/`;
  - edit only `tasks/proot-distro-ds/`, `build/proot-distro-ds/` and, for pattern B, the register;
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
