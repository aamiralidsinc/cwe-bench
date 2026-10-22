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

Project root: `/home/mara/cwe-bench`. Task: `trivy-path-traversal-inj`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: GHSA-8RC5-4FR6-64PW / CVE-2026-63328 - aquasecurity/trivy - CWE-22 path traversal (untrusted metadata name joined to a managed directory; arbitrary write/delete). Whether a plugin name (from a downloaded plugin.yaml, or from a CLI argument) may be joined onto the plugin root ~/.trivy/plugins to form a directory 
- Pinned (vulnerable) commit: 246ee3ca56b666e3c6e6462bf7c0ecd6f059341a. Published fix: d4213d7735c74e57f06c02ccb39ebca67abc7959.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "16736",
 "advisory_ids": [
  "GHSA-8RC5-4FR6-64PW",
  "CVE-2026-63328",
  "GO-2026-6250"
 ],
 "repo": "aquasecurity/trivy",
 "pinned_commit": "unknown (parent of d4213d7735c74e57f06c02ccb39ebca67abc7959; parent_commit not given and no .git in the pinned tree)",
 "fix_commits": [
  "d4213d7735c74e57f06c02ccb39ebca67abc7959"
 ],
 "trust_decision": {
  "summary": "Whether a plugin name (from a downloaded plugin.yaml, or from a CLI argument) may be joined onto the plugin root ~/.trivy/plugins to form a directory that is wiped, written, read or executed from; at the pinned commit nothing decides it, and the fix enforces it with os.Root confinement and filepath.IsLocal in Manager.install, Uninstall, load and loadMetadata.",
  "evidence": [
   "pkg/plugin/manager.go:129-139",
   "pkg/plugin/manager.go:351",
   "pkg/plugin/manager.go:157-162",
   "pkg/plugin/manager.go:317-325",
   "pkg/downloader/download.go:58-60",
   "fix.diff:332-345",
   "fix.diff:729-737"
  ]
 },
 "landing_point": {
  "where": "pkg/plugin/manager.go:139",
  "why": "The summary says the plugin manager allows arbitrary file write; the obvious write is os.Create(filepath.Join(plugin.Dir(), configFile)) in Manager.install, where plugin.Dir() comes from the untrusted name set at pkg/plugin/manager.go:351."
 },
 "fix_sites": [
  {
   "where": "pkg/plugin/manager.go:129-147",
   "entry_point": "CLI `trivy plugin install <src>` (pkg/commands/app.go:791), `trivy plugin run` (pkg/commands/app.go:850), `trivy plugin upgrade` (pkg/commands/app.go:892 via pkg/plugin/manager.go:245), env TRIVY_RUN_AS_PLUGIN (cmd/trivy/main.go:38)",
   "module_kind": "core handler (install path: download destination, RemoveAll in downloader, plugin.yaml write)"
  },
  {
   "where": "pkg/plugin/manager.go:156-167",
   "entry_point": "CLI `trivy plugin uninstall <name>` (pkg/commands/app.go:806)",
   "module_kind": "core handler (CLI-name route into RemoveAll)"
  },
  {
   "where": "pkg/plugin/manager.go:316-331",
   "entry_point": "CLI `trivy plugin info <name>` (pkg/commands/app.go:835), `trivy plugin upgrade <name>` (pkg/plugin/manager.go:238), output plugin `--format plugin=<name>` via plugin.Start (pkg/flag/options.go:626)",
   "module_kind": "core handler (CLI-name route into load/exec)"
  },
  {
   "where": "pkg/plugin/manager.go:333-359",
   "entry_point": "every load: LoadAll at startup (pkg/commands/app.go:123), `trivy plugin list` (pkg/commands/app.go:821), isInstalled during install (pkg/plugin/manager.go:362)",
   "module_kind": "metadata loader / save-reload (stored plugin.yaml name becomes plugin.dir)"
  },
  {
   "where": "pkg/plugin/manager.go:267-287",
   "entry_point": "LoadAll at startup (pkg/commands/app.go:123) and `trivy plugin list`/`upgrade`",
   "module_kind": "core handler (enumeration of installed plugins)"
  },
  {
   "where": "pkg/plugin/manager.go:60-96",
   "entry_point": "public Go API plugin.NewManager / package-level wrappers Install, Run, Start, Uninstall...",
   "module_kind": "wrapper / public API (signature change, NewManager now opens os.Root)"
  },
  {
   "where": "pkg/commands/app.go:119-127",
   "entry_point": "every trivy invocation (plugin commands added to the command tree)",
   "module_kind": "CLI wiring (manager lifecycle only, no check)"
  },
  {
   "where": "pkg/commands/app.go:791-892",
   "entry_point": "`trivy plugin` subcommands",
   "module_kind": "CLI wiring (switch to a per-command Manager, no check)"
  },
  {
   "where": "fix.diff:683-738",
   "entry_point": "new internal helper pkg/x/os Root.Join / NewRoot",
   "module_kind": "new lower-level helper (confinement primitive)"
  }
 ],
 "O1_entry_points": 8,
 "O2_out_of_scope_site": {
  "kind": "save_reload_or_serialization",
  "where": "pkg/plugin/manager.go:351 (loadMetadata sets plugin.dir from the stored plugin.yaml name rather than the directory name; reached from LoadAll pkg/plugin/manager.go:279 and load pkg/plugin/manager.go:325; the fix derives the directory from the directory name at fix.diff:403,423,461)"
 },
 "O3_reason_to_dismiss": "The installed plugin.yaml was written by Trivy itself and uninstall/info names are the local user's own CLI arguments, so a solver can argue only the freshly downloaded name in install() crosses a trust boundary and leave load/loadMetadata/Uninstall as they are.",
 "O4_distance": {
  "files": 2,
  "packages": 1,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "The install argument is legitimately a path or URL containing '/' (e.g. `testdata/test_plugin`, GitHub archive URLs, `name@vX.Y.Z`), archives with a single top-level directory are unwrapped, and uninstalling a missing plugin must log 'No such plugin' and return nil; a fix that applies IsLocal to the src argument or errors on a missing name breaks these.",
  "where": "pkg/plugin/manager.go:99-110, pkg/plugin/manager.go:120-126, pkg/plugin/manager.go:158-160, pkg/plugin/manager_unix_test.go:135"
 },
 "O6_input_shapes": [
  "relative dot-dot name in downloaded plugin.yaml (\"../escaped_plugin\", fix.diff:678)",
  "absolute name in plugin.yaml (\"/escaped_abs\", fix.diff:667)",
  "dot-dot hidden behind a missing component (\"missing/../../etc\", fix.diff:794)",
  "existing symlink inside the root that points outside (fix.diff:806-809)",
  "dot-dot CLI name for uninstall (\"../secret\", fix.diff:556)"
 ],
 "O7_producer": {
  "kind": "config_loader",
  "where": "pkg/plugin/manager.go:333-359 (loadMetadata decodes plugin.yaml and derives plugin.dir from plugin.Name at pkg/plugin/manager.go:351)",
  "check_calls_producer": true
 },
 "O8_uncovered_routes": [
  {
   "route": "Platform.Bin from plugin.yaml is joined onto the plugin directory without confinement to form the executed file path.",
   "where": "pkg/plugin/plugin.go:69",
   "reason_to_dismiss": "Bin names the plugin's own executable and the plugin author already gets code execution, and the advisory is about file write, not exec path.",
   "distance": "other file, same package (pkg/plugin/plugin.go vs pkg/plugin/manager.go)",
   "present_in_latest": "yes",
   "latest_where": "latest/pkg/plugin/plugin.go:69"
  }
 ],
 "O8b_injection_room": [
  {
   "where": "pkg/plugin/plugin.go:164-169",
   "sibling": "Plugin.Dir() falls back to TrivyHomeDir/plugins/p.Name when dir is unset; a caller that relies on the fallback reintroduces the name-to-path join outside the root.",
   "why_realistic": "The fallback is still present upstream (latest/pkg/plugin/plugin.go:163-167), and a maintainer adding a helper that builds a Plugin from the index or from metadata without going through loadMetadata would naturally call Dir()."
  },
  {
   "where": "pkg/plugin/index.go:36-56",
   "sibling": "A cache of per-plugin index data or a downloaded per-plugin asset stored under indexPath's directory and keyed by the index entry name.",
   "why_realistic": "Update already writes into the plugin root through plain os/fsutils calls rather than the root, so a per-plugin cache next to index.yaml would be written the same way."
  },
  {
   "where": "pkg/plugin/manager.go:237-265",
   "sibling": "An upgrade or rollback step that renames or backs up the old plugin directory using the newly downloaded name.",
   "why_realistic": "Upgrade reinstalls from plugin.Repository and can receive a different name, so a backup/rename keyed on updated.Name is a natural addition."
  }
 ],
 "O9_family": "CWE-22 path traversal (untrusted metadata name joined to a managed directory; arbitrary write/delete)",
 "O9_dos": false,
 "O10_build": {
  "language": "Go",
  "toolchain": "go 1.26.3 (go.mod:3); os.Root used by the fix needs Go >= 1.24",
  "services": [],
  "offline_after_build": true,
  "project_tests": "pkg/plugin/manager_unix_test.go (TestManager_Install with local testdata plugins and httptest), pkg/plugin/manager_test.go (Uninstall, Information, LoadAll, Upgrade), pkg/plugin/index_test.go, integration/plugin_test.go"
 },
 "O11_fix_minutes": 40,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "A",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "pkg/plugin/manager.go, pkg/commands/app.go, pkg/x/os/root.go (new)",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 0,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Reject plugin.Name containing \"..\" (or call filepath.Base) in install() right after decoding the downloaded plugin.yaml, leaving Uninstall/load CLI names, the absolute and symlink shapes, and loadMetadata's stored-name dir derivation alone."
 },
 "out_of_scope_notes": [
  "pkg/vex/repo/manager.go:107 joins a VEX repository Name from config onto the cache dir without confinement; latest adds filepath.IsLocal (latest/pkg/vex/repo/manager.go:109); likely the sibling advisory, a different sink.",
  "pkg/downloader/download.go:58-60 RemoveAll(dst) before download, and go-getter archive extraction, were not examined for entry-name traversal."
 ],
 "unverified": [
  "repo_mb not measured (no shell); Trivy is large with heavy testdata, so tiny_repo does not apply and giant_repo is unlikely but unconfirmed.",
  "The O8 Bin route is an exec-path escape, not a write; its security value is debatable because a malicious plugin already runs code, so a hidden test demanding it may be judged unfair. Pattern B is weak.",
  "Pinned commit hash not available in the tree; taken as the parent of the fix commit.",
  "O1 counts install, run, upgrade, uninstall, info, list/startup LoadAll, output plugin Start, and TRIVY_RUN_AS_PLUGIN; the write sink proper is reached by four of them (install, run, upgrade, TRIVY_RUN_AS_PLUGIN).",
  "In normal flow the stored plugin.yaml name matches its directory, so the loadMetadata save/reload route matters mainly when the stored name diverges (manual edits, or upgrade receiving a different name); not proven exploitable within the time.",
  "recall_risk is an estimate: the advisory was published 2026-08-18, after the knowledge cutoff, for a widely used project."
 ]
}
  ```
- Published fix sites:   - pkg/plugin/manager.go:129-147 — entry point: CLI `trivy plugin install <src>` (pkg/commands/app.go:791), `trivy plugin run` (pkg/commands/app.go:850), `trivy plugin upgrade` (pkg/commands/app.go:892 via pkg/plugin/manager.go:245), env TRIVY_RUN_AS_PLUGIN (cmd/trivy/main.go:38) [core handler (install path: download destination, RemoveAll in downloader, plugin.yaml write)]
  - pkg/plugin/manager.go:156-167 — entry point: CLI `trivy plugin uninstall <name>` (pkg/commands/app.go:806) [core handler (CLI-name route into RemoveAll)]
  - pkg/plugin/manager.go:316-331 — entry point: CLI `trivy plugin info <name>` (pkg/commands/app.go:835), `trivy plugin upgrade <name>` (pkg/plugin/manager.go:238), output plugin `--format plugin=<name>` via plugin.Start (pkg/flag/options.go:626) [core handler (CLI-name route into load/exec)]
  - pkg/plugin/manager.go:333-359 — entry point: every load: LoadAll at startup (pkg/commands/app.go:123), `trivy plugin list` (pkg/commands/app.go:821), isInstalled during install (pkg/plugin/manager.go:362) [metadata loader / save-reload (stored plugin.yaml name becomes plugin.dir)]
  - pkg/plugin/manager.go:267-287 — entry point: LoadAll at startup (pkg/commands/app.go:123) and `trivy plugin list`/`upgrade` [core handler (enumeration of installed plugins)]
  - pkg/plugin/manager.go:60-96 — entry point: public Go API plugin.NewManager / package-level wrappers Install, Run, Start, Uninstall... [wrapper / public API (signature change, NewManager now opens os.Root)]
  - pkg/commands/app.go:119-127 — entry point: every trivy invocation (plugin commands added to the command tree) [CLI wiring (manager lifecycle only, no check)]
  - pkg/commands/app.go:791-892 — entry point: `trivy plugin` subcommands [CLI wiring (switch to a per-command Manager, no check)]
  - fix.diff:683-738 — entry point: new internal helper pkg/x/os Root.Join / NewRoot [new lower-level helper (confinement primitive)]
- Uncovered routes to confirm (pattern B):   - pkg/plugin/plugin.go:69 — Platform.Bin from plugin.yaml is joined onto the plugin directory without confinement to form the executed file path. (reason to dismiss: Bin names the plugin's own executable and the plugin author already gets code execution, and the advisory is about file write, not exec path.; still in latest: yes)
- Design plan from the lead: TRACK = INJECTED (breaker recipe: only injected-sibling tasks at a recurring trust decision have beaten both models).

RECURRING DECISION / PROTECTED SINK: Whether a plugin name (from a downloaded plugin.yaml, or from a CLI argument) may be joined onto the plugin root ~/.trivy/plugins to form a directory that is wiped, written, read or executed from; at the pinned commit nothing decides it, and the fix enforces i

STEP 1 - confirm the published fix's sites and these uncovered-route leads with tests on the pinned copy: pkg/plugin/plugin.go:69 (Platform.Bin from plugin.yaml is joined onto the plugin; dismiss: Bin names the plugin's own executable and the).
STEP 2 - INJECT 2 to 4 sibling vulnerabilities of the SAME mechanism into our pinned copy at these recurring sites (verify each by reading the code): pkg/plugin/plugin.go:164-169 -> Plugin.Dir() falls back to TrivyHomeDir/plugins/p.Name when dir is uns (realistic: The fallback is still present upstream (latest/pkg/plugin/pl); pkg/plugin/index.go:36-56 -> A cache of per-plugin index data or a downloaded per-plugin asset stor (realistic: Update already writes into the plugin root through plain os/); pkg/plugin/manager.go:237-265 -> An upgrade or rollback step that renames or backs up the old plugin di (realistic: Upgrade reinstalls from plugin.Repository and can receive a ). Each sibling MUST be code a maintainer could plausibly have written (no tell-tale names/comments/shortcuts; match surrounding style), reachable through the real public entry point, covered by a stated invariant, placed where the published upstream fix never touches, and carry a DIFFERENT plausible reason-to-dismiss from the others (legacy/compat path, internal/trusted caller, unsupported combination, neighbouring feature). Distinct reasons-to-dismiss are the lever.
STEP 3 - hidden security tests require closing the base flaw, every uncovered route AND every injected sibling through the real entry point. The oracle closes all; a fix that closes only the obvious sites must score < 1.0 (add a security_fail check patch for exactly that partial fix).
STEP 4 - COUPLED MUST-KEEP-WORKING (one functional test per trap): The install argument is legitimately a path or URL containing '/' (e.g. `testdata/test_plugin`, GitHub archive URLs, `name@vX.Y.Z`), archives with a single top-level directory are unwrapped, and unins (near pkg/plugin/manager.go:99-110, pkg/plugin/manager.g); keep every legitimate use of the mechanism working.

Aim for >=3 levers with DIFFERENT reasons to dismiss. Every sibling must be findable by a blind engineer from instruction.md + code; if not, drop it. instruction.md stays product-level: system, one impact with one user trigger, invariants covering EVERY route/sibling (a natural list, no count); never name files/functions/fields/CVEs (all in manifest.leak_terms). Register each sibling and route in build/audit/uncovered-routes.tsv.
- Host notes: Language: Go. Offline after build, no external services. INJECTED: siblings go in OUR copy only, register them. Recurring trust decision (8 entry points) + screener injection room. Build+test via real entry points; project's own area tests pass at the pinned commit. Pin at the vulnerable commit; keep unrelated earlier fixes.

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

## Environment (`tasks/trivy-path-traversal-inj/environment/Dockerfile`)
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

## Report to the solver (`tasks/trivy-path-traversal-inj/instruction.md`)
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

## Tests (`tasks/trivy-path-traversal-inj/tests/`)
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
- **Wrong-fix patches** go in `build/trivy-path-traversal-inj/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/trivy-path-traversal-inj/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/trivy-path-traversal-inj/manifest.json`:**
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

**Also in `build/trivy-path-traversal-inj/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py trivy-path-traversal-inj --only static
python3 -I builder/gate.py trivy-path-traversal-inj --only nop
python3 -I builder/gate.py trivy-path-traversal-inj --only oracle
python3 -I builder/gate.py trivy-path-traversal-inj --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/trivy-path-traversal-inj/`;
  - edit only `tasks/trivy-path-traversal-inj/`, `build/trivy-path-traversal-inj/` and, for pattern B, the register;
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
