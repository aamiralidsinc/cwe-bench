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

Project root: `/home/mara/cwe-bench`. Task: `skillctl-s2`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: ["GHSA-WX3M-WHQV-XV47"]; umanio-agency/skillctl; path traversal (CWE-22) combined with symlink following (CWE-61): arbitrary file read, write and directory deletion outside the project and library roots
- Pinned (vulnerable) commit: 04ee4eb65c8533e6181e719db98dd068ac7bcc9d. Published fix: 827fff5c0698dd9e48e777d5907cf7bc19b91aca.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v2",
 "model": "deepseek-flash[1m]",
 "entry_id": "21611",
 "advisory_ids": [
  "GHSA-WX3M-WHQV-XV47"
 ],
 "repo": "umanio-agency/skillctl",
 "pinned_commit": "04ee4eb65c8533e6181e719db98dd068ac7bcc9d",
 "fix_commits": [
  "827fff5c0698dd9e48e777d5907cf7bc19b91aca"
 ],
 "trust_decision": {
  "summary": "Attacker-controlled: the `destination` and `source_path` strings deserialized from a PR-supplied `.skills.toml`, and the file tree (symlinks) of the skills library; trusted: the operator's project cwd and the library cache root. The decision is made on deserialization in `project_config::load` (`InstalledSkill::validate`, lexical components only) and again at copy time in `fs_util::copy_dir_all`/`replace_folder_contents` (symlink rejection).",
  "evidence": [
   "src/project_config.rs:28-35",
   "src/project_config.rs:16-22",
   "src/commands/push.rs:320-333",
   "src/commands/pull.rs:272-277",
   "src/fs_util.rs:12-16",
   "src/fs_util.rs:24-28"
  ]
 },
 "landing_point": {
  "where": "src/fs_util.rs:12",
  "why": "The summary names symlink-follow as the first defect (arbitrary file disclosure), and this is the branch where `entry.file_type()?.is_dir()` is false for a symlink so the entry falls to `fs::copy` at src/fs_util.rs:15, which dereferences it; the same helper is called from add, pull, detect and push."
 },
 "fix_sites": [
  {
   "where": "fix.diff:896-918",
   "entry_point": "skillctl add | push | pull | detect (all reach it through project_config::load)",
   "module_kind": "config_loader"
  },
  {
   "where": "fix.diff:930-934",
   "entry_point": "skillctl add | push | pull | detect (load-time validation gate)",
   "module_kind": "config_loader"
  },
  {
   "where": "fix.diff:753-781",
   "entry_point": "shared helper for skillctl detect/push/pull and project_config",
   "module_kind": "helper_module"
  },
  {
   "where": "fix.diff:558-566",
   "entry_point": "skillctl add, skillctl pull, skillctl detect (copy_dir_all top-level source)",
   "module_kind": "fs_primitive"
  },
  {
   "where": "fix.diff:573-582",
   "entry_point": "skillctl add, skillctl pull, skillctl detect (copy_dir_all descendant entries)",
   "module_kind": "fs_primitive"
  },
  {
   "where": "fix.diff:597-605",
   "entry_point": "skillctl push, skillctl pull (replace_folder_contents destination)",
   "module_kind": "fs_primitive"
  },
  {
   "where": "fix.diff:724",
   "entry_point": "crate root (module declaration)",
   "module_kind": "crate_root"
  },
  {
   "where": "fix.diff:418-430",
   "entry_point": "skillctl detect --target",
   "module_kind": "handler"
  },
  {
   "where": "fix.diff:437-441",
   "entry_point": "skillctl detect (interactive custom library-path prompt)",
   "module_kind": "handler"
  },
  {
   "where": "fix.diff:460-467",
   "entry_point": "skillctl pull",
   "module_kind": "handler"
  },
  {
   "where": "fix.diff:475-477",
   "entry_point": "skillctl pull --on-divergence fork --fork-suffix",
   "module_kind": "handler"
  },
  {
   "where": "fix.diff:502-513",
   "entry_point": "skillctl push",
   "module_kind": "handler"
  },
  {
   "where": "fix.diff:523-527",
   "entry_point": "skillctl push --on-divergence fork",
   "module_kind": "handler"
  },
  {
   "where": "fix.diff:535-537",
   "entry_point": "skillctl push --on-divergence fork (interactive name prompt)",
   "module_kind": "handler"
  }
 ],
 "O1_entry_points": 4,
 "O2_out_of_scope_site": {
  "kind": "lower_level_api",
  "where": "src/fs_util.rs:6"
 },
 "O3_reason_to_dismiss": "`fs_util::copy_dir_all` is a generic directory-copy helper with no knowledge of skills or `.skills.toml`, so a solver can call it infrastructure outside the advisory's config-traversal story and fix only the `destination`/`source_path` joins in push and pull.",
 "O4_distance": {
  "files": 5,
  "packages": 1,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "`.skills.toml` paths and `--target` values made only of `Normal` and `.` components must keep working, in particular `detect --target .` (library root) and `./foo` / `foo/./bar`; a fix that rejects every non-`Normal` component, or rejects `.` outright, breaks the documented flat-layout recipe and the `is_root` path.",
  "where": "src/commands/detect.rs:100-104"
 },
 "O6_input_shapes": [
  "absolute path (RootDir), e.g. `/home/seb/.ssh` for `destination`, `/home/seb/.aws` for `source_path`",
  "parent traversal at start, middle and end: `../../../etc`, `foo/../bar`, `foo/..`",
  "Windows prefix components (Component::Prefix)",
  "empty path and bare `.` (accepted; must stay accepted, `detect --target .`)",
  "`.`-interleaved relative paths `./foo`, `foo/./bar`, `.claude/skills/foo` (accepted)",
  "single-component fork names exactly `.` or `..` (push and pull `validate_fork_name`)",
  "symlink top-level source dir, symlinked file inside a tree, symlinked subdir inside a tree, symlinked replace destination",
  "same value arriving as a TOML-deserialized PathBuf (destination/source_path) or as a clap PathBuf flag (--target)"
 ],
 "O7_producer": {
  "kind": "config_loader",
  "where": "src/project_config.rs:28-35",
  "check_calls_producer": true
 },
 "O8_uncovered_routes": [
  {
   "route": "`skillctl add`'s destination is never validated: `resolve_destination` returns `--dest` verbatim (and the interactive custom prompt only checks for emptiness), then `dest_root.join(folder_name)` is passed to `fs::remove_dir_all` on --on-conflict overwrite and to `copy_dir_all`, so `--dest /` or `--dest ../..` writes and deletes outside the project; the published fix changed detect's equivalent `--target` but not add.",
   "where": "src/commands/add.rs:267-270",
   "reason_to_dismiss": "`--dest` is an explicit operator-supplied CLI flag, not a value deserialized from `.skills.toml` or shipped by the library, so it is outside the advisory's untrusted-input story.",
   "distance": "1 module dir from the landing point (src/commands/add.rs vs src/fs_util.rs), 2 files of reach (add.rs -> fs_util.rs)",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "Lexical-only join: `library_root.join(source_path)` and `cwd.join(destination)` are validated by components, but an intermediate directory replaced by a symlink (a library commit can flip a tracked skill folder to a symlink, which `git reset --hard` checks out) is still followed by `replace_folder_contents` -> `remove_dir_all`, and `copy_dir_all` only stats the final component.",
   "where": "src/commands/pull.rs:272-277",
   "reason_to_dismiss": "The project documents its threat model as purely lexical and explicitly trusts the base path's parents (`path_safety`'s own note says symlinks inside copied trees are handled in `fs_util`, and `copy_dir_all` does check the entry itself), so a solver can call base-side symlinks out of scope.",
   "distance": "src/commands/pull.rs -> src/fs_util.rs, one module hop; same for push at src/commands/push.rs:320-333",
   "present_in_latest": "unknown",
   "latest_where": ""
  }
 ],
 "O8b_injection_room": [
  {
   "where": "src/commands/add.rs:267-270",
   "sibling": "route `add --dest` through the same `validate_relative_subpath` helper detect's `--target` uses",
   "why_realistic": "add and detect are mirror commands (library<->project) with the same flag shape, and the fix added exactly this check to detect's `--target` while leaving add's `--dest` alone; README.md:121 already documents `--dest` as project-relative."
  },
  {
   "where": "src/project_config.rs:37-41",
   "sibling": "validate `InstalledSkill` in `save` as well as in `load`",
   "why_realistic": "push.rs:397-403 constructs a replacement `InstalledSkill` inline and save writes it unvalidated, so the invariant currently holds only on read; a maintainer hardening the type would add it here."
  },
  {
   "where": "src/commands/pull.rs:473-484",
   "sibling": "`local_fork_destination` joins cwd with `destination.parent()` without `safe_join`, mirroring push.rs:390 which was converted",
   "why_realistic": "push and pull duplicate the fork logic (`fork_op_for_name` vs `local_fork_destination`, two copies of `validate_fork_name`); the fix hardened push's abs_old/abs_new joins but left pull's destination construction as a name check only."
  },
  {
   "where": "src/commands/add.rs:367-379",
   "sibling": "the interactive custom-path prompt validates only non-empty, while detect.rs:353-356 got the shared validator",
   "why_realistic": "the two prompts are copy-paste siblings; the fix updated one and not the other."
  }
 ],
 "O9_family": "path traversal (CWE-22) combined with symlink following (CWE-61): arbitrary file read, write and directory deletion outside the project and library roots",
 "O9_dos": false,
 "O10_build": {
  "language": "Rust (edition 2024, rust-version 1.85)",
  "toolchain": "cargo/rustc; deps from crates.io in Cargo.toml (clap, cliclack, crossterm, directories, ignore, serde, serde_json, time, toml); the fix adds the dev-dependency tempfile",
  "services": [
   "git CLI on PATH (all commands shell out to git for clone/fetch/commit/push/hash-object/ls-tree)"
  ],
  "offline_after_build": true,
  "project_tests": "Unit tests only: SKILL.md frontmatter parsing (src/skill.rs:204-323), commit-message building (src/commands/push.rs:633-667), URL slug (src/config.rs:86-123), diff counting (src/commands/diff.rs:112-157). No path-handling tests exist at the pinned commit and the fix's new tests (fs_util, project_config, path_safety) are not present. CI runs cargo fmt --check, clippy -D warnings, build --all-targets, test --all (.github/workflows/ci.yml:26-36)."
 },
 "O11_fix_minutes": 40,
 "O12_red_flags": [
  "tiny_repo"
 ],
 "O13_recall_risk": "low",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "src/commands/detect.rs, src/commands/pull.rs, src/commands/push.rs, src/fs_util.rs, src/main.rs, src/path_safety.rs, src/project_config.rs",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Validate `destination` and `source_path` at the top of push::run and pull::run (reject absolute and `..` before the joins) and stop there, leaving `fs_util::copy_dir_all`'s symlink dereference and add's `--dest` untouched."
 },
 "out_of_scope_notes": [
  "src/commands/init.rs:21 calls `fs::remove_dir_all` on a cache path built from the configured URL via `slug_for_url` (src/config.rs:62-84), which restricts the value to an `owner-repo` slug; not pursued.",
  "`path_safety` accepts empty and `.` paths, so a `.skills.toml` entry with `destination = \"\"` resolves to the project root itself; a self-inflicted footgun rather than a traversal, not pursued."
 ],
 "unverified": [
  "Repository size was estimated from the file inventory (about 20 Rust source files, a few thousand lines) rather than measured, so `repo_mb` is null; `tiny_repo` is asserted on that estimate.",
  "Latest released code is unavailable (no latest release given), so `present_in_latest` for every O8 route is `unknown`.",
  "End-to-end offline exercise was not tested (reading only). push/pull/detect drive `git fetch`/`git push` against a cache under the XDG cache dir and require a github.com-shaped URL; the destructive copy happens before `git push`, so the vulnerable behaviour should be observable offline with a local cache, but this was not run.",
  "Cargo build was not run; the build needs the crates.io registry (no vendored crates in the tree)."
 ]
}
  ```
- Published fix sites:   - fix.diff:896-918 — entry point: skillctl add | push | pull | detect (all reach it through project_config::load) [config_loader]
  - fix.diff:930-934 — entry point: skillctl add | push | pull | detect (load-time validation gate) [config_loader]
  - fix.diff:753-781 — entry point: shared helper for skillctl detect/push/pull and project_config [helper_module]
  - fix.diff:558-566 — entry point: skillctl add, skillctl pull, skillctl detect (copy_dir_all top-level source) [fs_primitive]
  - fix.diff:573-582 — entry point: skillctl add, skillctl pull, skillctl detect (copy_dir_all descendant entries) [fs_primitive]
  - fix.diff:597-605 — entry point: skillctl push, skillctl pull (replace_folder_contents destination) [fs_primitive]
  - fix.diff:724 — entry point: crate root (module declaration) [crate_root]
  - fix.diff:418-430 — entry point: skillctl detect --target [handler]
  - fix.diff:437-441 — entry point: skillctl detect (interactive custom library-path prompt) [handler]
  - fix.diff:460-467 — entry point: skillctl pull [handler]
  - fix.diff:475-477 — entry point: skillctl pull --on-divergence fork --fork-suffix [handler]
  - fix.diff:502-513 — entry point: skillctl push [handler]
  - fix.diff:523-527 — entry point: skillctl push --on-divergence fork [handler]
  - fix.diff:535-537 — entry point: skillctl push --on-divergence fork (interactive name prompt) [handler]
- Uncovered routes to confirm (pattern B):   - src/commands/add.rs:267-270 — `skillctl add`'s destination is never validated: `resolve_destination` returns `--dest` verbatim (and the interactive custom prompt only checks for emptiness), then `dest_root.join(folder_name)` is passed to `fs::remove_dir_all` on --on-conflict overwrite and to `copy_dir_all`, so `--dest /` or `--dest ../..` writes and deletes outside the project; the published fix changed detect's equivalent `--target` but not add. (reason to dismiss: `--dest` is an explicit operator-supplied CLI flag, not a value deserialized from `.skills.toml` or shipped by the library, so it is outside the advisory's untrusted-input story.; still in latest: unknown)
  - src/commands/pull.rs:272-277 — Lexical-only join: `library_root.join(source_path)` and `cwd.join(destination)` are validated by components, but an intermediate directory replaced by a symlink (a library commit can flip a tracked skill folder to a symlink, which `git reset --hard` checks out) is still followed by `replace_folder_contents` -> `remove_dir_all`, and `copy_dir_all` only stats the final component. (reason to dismiss: The project documents its threat model as purely lexical and explicitly trusts the base path's parents (`path_safety`'s own note says symlinks inside copied trees are handled in `fs_util`, and `copy_dir_all` does check the entry itself), so a solver can call base-side symlinks out of scope.; still in latest: unknown)
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

## Environment (`tasks/skillctl-s2/environment/Dockerfile`)
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

## Report to the solver (`tasks/skillctl-s2/instruction.md`)
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

## Tests (`tasks/skillctl-s2/tests/`)
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
- **Wrong-fix patches** go in `build/skillctl-s2/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/skillctl-s2/`:**
- `instruction.md`;
- `task.toml`, from `common/builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/skillctl-s2/manifest.json`:**
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

**Also in `build/skillctl-s2/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `common/builder/templates/` and `common/trial/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I common/gate/gate.py skillctl-s2 --only static
python3 -I common/gate/gate.py skillctl-s2 --only nop
python3 -I common/gate/gate.py skillctl-s2 --only oracle
python3 -I common/gate/gate.py skillctl-s2 --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/skillctl-s2/`;
  - edit only `tasks/skillctl-s2/`, `build/skillctl-s2/` and, for pattern B, the register;
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
