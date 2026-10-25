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

Project root: `/home/mara/cwe-bench/precision_validation/root`. Task: `pv-pnpm`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: ["GHSA-5WX6-MG75-V57R", "CVE-2026-55487"]; pnpm/pnpm; origin/identity confusion in an allow-list (CWE-346/693): build approval keyed on attacker-controlled manifest name
- Pinned (vulnerable) commit: parent of bf1b731ee6c0ea98709e671ff0f46bf654480ab8 (parent_commit not given in candidate; tree at /home/mara/screen3/hosts/8873/repo). Published fix: bf1b731ee6c0ea98709e671ff0f46bf654480ab8.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "8873",
 "advisory_ids": [
  "GHSA-5WX6-MG75-V57R",
  "CVE-2026-55487"
 ],
 "repo": "pnpm/pnpm",
 "pinned_commit": "parent of bf1b731ee6c0ea98709e671ff0f46bf654480ab8 (parent_commit not given in candidate; tree at /home/mara/screen3/hosts/8873/repo)",
 "fix_commits": [
  "bf1b731ee6c0ea98709e671ff0f46bf654480ab8"
 ],
 "trust_decision": {
  "summary": "Whether a dependency may run lifecycle/prepare scripts is decided by matching the package name/version (taken from the fetched manifest or the depPath) against allowBuilds in createAllowBuildFunction; for git/tarball/directory artifacts that name is attacker-controlled, so a spoofed manifest name satisfies a registry-package approval.",
  "evidence": [
   "building/policy/src/index.ts:34-43",
   "building/during-install/src/index.ts:94",
   "exec/prepare-package/src/index.ts:36",
   "fix.diff:428-438",
   "fix.diff:1315-1328"
  ]
 },
 "landing_point": {
  "where": "building/policy/src/index.ts:34",
  "why": "The summary says a spoofed manifest identity satisfies allowBuilds; the allowBuilds matcher (createAllowBuildFunction) is the obvious place, and it compares only pkgName/version."
 },
 "fix_sites": [
  {
   "where": "building/policy/src/index.ts:5-46",
   "entry_point": "all build paths: pnpm install/add, pnpm rebuild, pnpm dlx (createAllowBuildFunction + isBuildExplicitlyDisallowed)",
   "module_kind": "policy core (landing point)"
  },
  {
   "where": "building/during-install/src/index.ts:94",
   "entry_point": "pnpm install / pnpm add (buildModules)",
   "module_kind": "build executor"
  },
  {
   "where": "building/after-install/src/index.ts:334",
   "entry_point": "pnpm rebuild / pnpm approve-builds (_rebuild)",
   "module_kind": "second build executor (rebuild)"
  },
  {
   "where": "building/after-install/src/index.ts:81",
   "entry_point": "pnpm rebuild <pkg> (selector matching by manifest name)",
   "module_kind": "CLI selector matcher"
  },
  {
   "where": "exec/prepare-package/src/index.ts:36",
   "entry_point": "pnpm install / pnpm dlx with a git or git-hosted tarball dependency (prepare scripts)",
   "module_kind": "lower-level library (fetch-time prepare)"
  },
  {
   "where": "fetching/git-fetcher/src/index.ts:47",
   "entry_point": "pnpm install with git: dependency",
   "module_kind": "fetcher"
  },
  {
   "where": "fetching/tarball-fetcher/src/gitHostedTarballFetcher.ts:83",
   "entry_point": "pnpm install with github:/codeload tarball dependency",
   "module_kind": "fetcher"
  },
  {
   "where": "deps/graph-builder/src/lockfileToDepGraph.ts:244",
   "entry_point": "pnpm install (frozen/headless, global virtual store)",
   "module_kind": "graph builder (GVS fast path)"
  },
  {
   "where": "deps/graph-hasher/src/index.ts:339",
   "entry_point": "pnpm install / rebuild / self-update with global virtual store (built-hash selection)",
   "module_kind": "hasher"
  },
  {
   "where": "installing/deps-installer/src/install/link.ts:489",
   "entry_point": "pnpm install (side-effects cache read)",
   "module_kind": "linker"
  },
  {
   "where": "installing/deps-restorer/src/index.ts:935",
   "entry_point": "pnpm install --frozen-lockfile (headless, side-effects cache)",
   "module_kind": "headless restorer"
  },
  {
   "where": "installing/deps-restorer/src/linkHoistedModules.ts:138",
   "entry_point": "pnpm install with nodeLinker=hoisted",
   "module_kind": "headless restorer (hoisted variant)"
  },
  {
   "where": "installing/deps-installer/src/install/index.ts:486",
   "entry_point": "pnpm install (revoked-approval detection vs .modules.yaml allowBuilds)",
   "module_kind": "save/reload of previous policy"
  },
  {
   "where": "installing/deps-installer/src/install/index.ts:1103",
   "entry_point": "pnpm install (re-run previously ignored builds)",
   "module_kind": "orchestrator"
  },
  {
   "where": "installing/deps-installer/src/install/verifyLockfileResolutions.ts:251-264",
   "entry_point": "pnpm install with an existing lockfile (verification gate; new shape-mismatch rule)",
   "module_kind": "lockfile validation (save/reload)"
  },
  {
   "where": "installing/commands/src/handleIgnoredBuilds.ts:50",
   "entry_point": "pnpm install (writes ignored builds into allowBuilds)",
   "module_kind": "CLI config writer"
  },
  {
   "where": "building/commands/src/policy/approveBuilds.ts:198",
   "entry_point": "pnpm approve-builds",
   "module_kind": "CLI command"
  },
  {
   "where": "pacquet/crates/package-manager/src/build_modules.rs:550",
   "entry_point": "pnpm install delegated to pacquet (Rust frozen install)",
   "module_kind": "second implementation (Rust port)"
  },
  {
   "where": "pacquet/crates/git-fetcher/src/prepare_package.rs:103",
   "entry_point": "pacquet install of git dependency",
   "module_kind": "second implementation (Rust port)"
  },
  {
   "where": "pacquet/crates/lockfile-verification/src/verify_lockfile_resolutions.rs:120",
   "entry_point": "pacquet frozen install verification gate",
   "module_kind": "second implementation (Rust port)"
  }
 ],
 "O1_entry_points": 5,
 "O2_out_of_scope_site": {
  "kind": "second_implementation",
  "where": "pacquet/crates/package-manager/src/build_modules.rs:550 (Rust port; also pacquet/crates/git-fetcher/src/prepare_package.rs:103 and pacquet/crates/lockfile-verification/src/verify_lockfile_resolutions.rs:120)"
 },
 "O3_reason_to_dismiss": "pacquet is an experimental Rust port in a separate crate tree that only runs when an install is delegated to it, so a solver fixing the TypeScript policy can argue it is a separate product; the pnpr server route can be dismissed as an opt-in remote resolver that 'does its own verification'.",
 "O4_distance": {
  "files": 34,
  "packages": 21,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Registry packages approved by plain name (allowBuilds: {pkg: true}) must still build; custom:* and variations resolutions must still pass the lockfile gate; revoked-approval detection must still evaluate old name approvals with trust (otherwise every git dep is falsely reported revoked); git/tarball artifacts approved by their peer-suffix-free depPath must build.",
  "where": "fix.diff:436-438, fix.diff:1076-1080, fix.diff:1272-1282, installing/deps-installer/src/install/index.ts:475-492"
 },
 "O6_input_shapes": [
  "allowBuilds key as package name, name@version, name@range with '||', and as a lockfile depPath with or without peer suffix (fix.diff:477-488)",
  "artifact kinds: git resolution, git-hosted tarball (codeload/bitbucket/gitlab), direct tarball URL, local directory (fix.diff:23)",
  "lockfile resolution with gitHosted true, non-boolean, or explicit false on a git-host URL (fix.diff:1284-1290)",
  "file: or other non-http(s) tarball under a name@semver key (fix.diff:1296-1298)",
  "upper-case scheme/host git-host URL (fix.diff:1761-1774)",
  "variations resolution whose variants mix registry and non-registry (fix.diff:1272-1276)",
  "scp-style git repo ids (user@host:path) vs ssh:// URLs with port (fix.diff:3238-3246)",
  "lockfile with zero resolution verifiers configured (shape gate must still run; fix.diff:1203, fix.diff:1231-1234)"
 ],
 "O7_producer": {
  "kind": "schema",
  "where": "installing/deps-installer/src/install/verifyLockfileResolutions.ts:251-264 (lockfile entry gate; post-fix trust signal is the depPath key shape produced by the lockfile, invariant enforced here)",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "pnpr server install: the client skips its own verifyLockfileResolutions, the server verifies the input lockfile with collect_resolution_policy_violations, which the fix makes discard shape violations, then the client runs a headless install with name-trusting allowBuild and records the lockfile as shape-verified.",
   "where": "installing/deps-installer/src/install/index.ts:312-315; pnpr/crates/pnpr/src/resolver.rs:505; pnpr/crates/pnpr/src/resolver.rs:242; installing/deps-installer/src/install/index.ts:2398; fix.diff:2321-2324",
   "reason_to_dismiss": "pnpr is an opt-in remote resolver in its own crate tree that already has a verification step, and the fix's own comment says shape violations are deliberately not collected in collect-mode.",
   "distance": "pnpr/crates/pnpr (separate Rust server package) vs landing point building/policy (TS)",
   "present_in_latest": "unknown",
   "latest_where": "latest/pnpr/crates/pnpr/src/resolver/verify_lockfile.rs:121; latest/pnpm/crates/lockfile-verification/src/verify_lockfile_resolutions.rs:341-344"
  },
  {
   "route": "pnpm rebuild / approve-builds read node_modules/.pnpm/lock.yaml (current lockfile) and gate builds on its depPath keys without ever running the shape gate.",
   "where": "building/after-install/src/index.ts:116-117; building/after-install/src/index.ts:287-296",
   "reason_to_dismiss": "The current lockfile is pnpm-written internal state derived from an already-verified install, so it is 'trusted by construction'.",
   "distance": "building/after-install vs installing/deps-installer gate (different package)",
   "present_in_latest": "unknown",
   "latest_where": "latest/pnpm11/building/after-install/src/getRebuildContext.ts:64"
  }
 ],
 "O8b_injection_room": [
  {
   "where": "engine/pm/commands/src/self-updater/installPnpm.ts:149",
   "sibling": "self-updater builds an allowBuild from allowBuilds and could pass manifest name/version directly to a build step",
   "why_realistic": "It already constructs its own allowBuild outside the main install pipeline; a maintainer adding builds to self-update would copy the old name-based call."
  },
  {
   "where": "installing/deps-installer/src/install/index.ts:1653",
   "sibling": "a post-build ignored-builds filter that parses name/version from depPath instead of passing the depPath",
   "why_realistic": "isBuildExplicitlyDisallowed previously did exactly this parse (building/policy/src/index.ts:7-9)."
  },
  {
   "where": "installing/deps-restorer/src/index.ts:600",
   "sibling": "headless ignored-builds re-check using dp.parse(name) against allowBuilds",
   "why_realistic": "Same pattern used in several places pre-fix (approveBuilds.ts:198, handleIgnoredBuilds.ts:50)."
  }
 ],
 "O9_family": "origin/identity confusion in an allow-list (CWE-346/693): build approval keyed on attacker-controlled manifest name",
 "O9_dos": false,
 "O10_build": {
  "language": "TypeScript (Node.js) monorepo plus Rust crates (pacquet, pnpr)",
  "toolchain": "Node.js + pnpm workspace (tsc project references, jest); cargo for pacquet/pnpr",
  "services": [
   "@pnpm/registry-mock (local verdaccio) for install e2e tests"
  ],
  "offline_after_build": null,
  "project_tests": "building/policy/test/index.ts, installing/deps-installer/test/install/lifecycleScripts.ts, installing/deps-installer/test/install/verifyLockfileResolutions.ts, exec/prepare-package/test/index.ts, building/commands/test/build/index.ts, pacquet crate tests (build_modules/tests.rs, verify_lockfile_resolutions/tests.rs)"
 },
 "O11_fix_minutes": 150,
 "O12_red_flags": [],
 "O13_recall_risk": "low",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "building/{after-install,commands,during-install,policy}, core/types, deps/{graph-builder,graph-hasher,path}, exec/prepare-package, fetching/{git-fetcher,tarball-fetcher}, installing/{commands,deps-installer,deps-restorer}, lockfile/{fs,utils}, resolving/git-resolver, pacquet/crates/{git-fetcher,lockfile-verification,lockfile,package-manager} (34 source files)",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Make prepare-package/buildModules refuse name-based approval for git deps only (check resolution type at the TS call site), leaving the lockfile depPath-shape forgery, rebuild, side-effects-cache, GVS hash and pacquet paths open."
 },
 "out_of_scope_notes": [
  "fix.diff also bumps a shell-quote override (pnpm-workspace.yaml) for an unrelated advisory; ignored.",
  "trustLockfile opt-out skips the verification gate (installing/deps-installer/src/install/index.ts:387); documented user opt-out, not pursued."
 ],
 "unverified": [
  "pinned_commit hash not provided; the repo directory is assumed to be the parent of the fix commit.",
  "O8 pnpr route: whether the TS client sends frozen_lockfile so the server returns the input lockfile verbatim (pnpr/crates/pnpr/src/resolver/resolve.rs:209) was not traced; end-to-end reachability unconfirmed.",
  "present_in_latest for both O8 routes: latest still drops shape violations in collect mode, but the latest pnpr client/server may check shapes elsewhere (latest pnpr-client maps RESOLUTION_SHAPE_MISMATCH); not confirmed.",
  "O10 offline_after_build: unit tests for policy/verification look offline; git fetcher and some build tests fetch from github.com, so not all area tests are offline.",
  "repo_mb not measured (no shell); likely well above 5 MB and below 1.5 GB.",
  "Fit risk: the fix changes the public AllowBuild signature (core/types/src/config.ts, fix.diff:644-649); hidden tests written against the new signature would penalise valid alternative designs.",
  "Fit risk: O11 of about 150 minutes is far above the 45-minute fairness budget; a task would need to be scoped to a subset of sites."
 ]
}
  ```
- Published fix sites:   - building/policy/src/index.ts:5-46 — entry point: all build paths: pnpm install/add, pnpm rebuild, pnpm dlx (createAllowBuildFunction + isBuildExplicitlyDisallowed) [policy core (landing point)]
  - building/during-install/src/index.ts:94 — entry point: pnpm install / pnpm add (buildModules) [build executor]
  - building/after-install/src/index.ts:334 — entry point: pnpm rebuild / pnpm approve-builds (_rebuild) [second build executor (rebuild)]
  - building/after-install/src/index.ts:81 — entry point: pnpm rebuild <pkg> (selector matching by manifest name) [CLI selector matcher]
  - exec/prepare-package/src/index.ts:36 — entry point: pnpm install / pnpm dlx with a git or git-hosted tarball dependency (prepare scripts) [lower-level library (fetch-time prepare)]
  - fetching/git-fetcher/src/index.ts:47 — entry point: pnpm install with git: dependency [fetcher]
  - fetching/tarball-fetcher/src/gitHostedTarballFetcher.ts:83 — entry point: pnpm install with github:/codeload tarball dependency [fetcher]
  - deps/graph-builder/src/lockfileToDepGraph.ts:244 — entry point: pnpm install (frozen/headless, global virtual store) [graph builder (GVS fast path)]
  - deps/graph-hasher/src/index.ts:339 — entry point: pnpm install / rebuild / self-update with global virtual store (built-hash selection) [hasher]
  - installing/deps-installer/src/install/link.ts:489 — entry point: pnpm install (side-effects cache read) [linker]
  - installing/deps-restorer/src/index.ts:935 — entry point: pnpm install --frozen-lockfile (headless, side-effects cache) [headless restorer]
  - installing/deps-restorer/src/linkHoistedModules.ts:138 — entry point: pnpm install with nodeLinker=hoisted [headless restorer (hoisted variant)]
  - installing/deps-installer/src/install/index.ts:486 — entry point: pnpm install (revoked-approval detection vs .modules.yaml allowBuilds) [save/reload of previous policy]
  - installing/deps-installer/src/install/index.ts:1103 — entry point: pnpm install (re-run previously ignored builds) [orchestrator]
  - installing/deps-installer/src/install/verifyLockfileResolutions.ts:251-264 — entry point: pnpm install with an existing lockfile (verification gate; new shape-mismatch rule) [lockfile validation (save/reload)]
  - installing/commands/src/handleIgnoredBuilds.ts:50 — entry point: pnpm install (writes ignored builds into allowBuilds) [CLI config writer]
  - building/commands/src/policy/approveBuilds.ts:198 — entry point: pnpm approve-builds [CLI command]
  - pacquet/crates/package-manager/src/build_modules.rs:550 — entry point: pnpm install delegated to pacquet (Rust frozen install) [second implementation (Rust port)]
  - pacquet/crates/git-fetcher/src/prepare_package.rs:103 — entry point: pacquet install of git dependency [second implementation (Rust port)]
  - pacquet/crates/lockfile-verification/src/verify_lockfile_resolutions.rs:120 — entry point: pacquet frozen install verification gate [second implementation (Rust port)]
- Uncovered routes to confirm (pattern B):   - installing/deps-installer/src/install/index.ts:312-315; pnpr/crates/pnpr/src/resolver.rs:505; pnpr/crates/pnpr/src/resolver.rs:242; installing/deps-installer/src/install/index.ts:2398; fix.diff:2321-2324 — pnpr server install: the client skips its own verifyLockfileResolutions, the server verifies the input lockfile with collect_resolution_policy_violations, which the fix makes discard shape violations, then the client runs a headless install with name-trusting allowBuild and records the lockfile as shape-verified. (reason to dismiss: pnpr is an opt-in remote resolver in its own crate tree that already has a verification step, and the fix's own comment says shape violations are deliberately not collected in collect-mode.; still in latest: unknown)
  - building/after-install/src/index.ts:116-117; building/after-install/src/index.ts:287-296 — pnpm rebuild / approve-builds read node_modules/.pnpm/lock.yaml (current lockfile) and gate builds on its depPath keys without ever running the shape gate. (reason to dismiss: The current lockfile is pnpm-written internal state derived from an already-verified install, so it is 'trusted by construction'.; still in latest: unknown)
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

## Environment (`tasks/pv-pnpm/environment/Dockerfile`)
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

## Report to the solver (`tasks/pv-pnpm/instruction.md`)
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

## Tests (`tasks/pv-pnpm/tests/`)
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
- **Wrong-fix patches** go in `build/pv-pnpm/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/pv-pnpm/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/pv-pnpm/manifest.json`:**
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

**Also in `build/pv-pnpm/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py pv-pnpm --only static
python3 -I builder/gate.py pv-pnpm --only nop
python3 -I builder/gate.py pv-pnpm --only oracle
python3 -I builder/gate.py pv-pnpm --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/pv-pnpm/`;
  - edit only `tasks/pv-pnpm/`, `build/pv-pnpm/` and, for pattern B, the register;
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
