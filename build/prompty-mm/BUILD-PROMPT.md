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

Project root: `/home/mara/cwe-bench`. Task: `prompty-mm`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: ["GHSA-WXHM-2MQ7-7697", "CVE-2026-53598", "PYSEC-2026-3538"]; microsoft/prompty; path traversal / arbitrary file read (CWE-22, CWE-200) via author-controlled include path
- Pinned (vulnerable) commit: parent of 88ac9948d7d37995edbb2f6d36913436626c39e1 (parent_commit not given in candidate). Published fix: 88ac9948d7d37995edbb2f6d36913436626c39e1.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "6237",
 "advisory_ids": [
  "GHSA-WXHM-2MQ7-7697",
  "CVE-2026-53598",
  "PYSEC-2026-3538"
 ],
 "repo": "microsoft/prompty",
 "pinned_commit": "parent of 88ac9948d7d37995edbb2f6d36913436626c39e1 (parent_commit not given in candidate)",
 "fix_commits": [
  "88ac9948d7d37995edbb2f6d36913436626c39e1"
 ],
 "trust_decision": {
  "summary": "Whether a frontmatter ${file:path} reference (written by the prompt author) may be read: decided per runtime in the loader's pre_process reference resolver, which at the pinned commit joins the path onto the prompt directory and reads it without any containment check (no '..', absolute-path or symlink check).",
  "evidence": [
   "runtime/python/prompty/prompty/core/loader.py:154-160",
   "runtime/typescript/packages/core/src/core/loader.ts:146-148",
   "runtime/rust/prompty/src/loader/resolve.rs:101-110",
   "runtime/csharp/Prompty.Core/ReferenceResolver.cs:103-108"
  ]
 },
 "landing_point": {
  "where": "runtime/python/prompty/prompty/core/loader.py:154",
  "why": "The PYSEC id and the 'file reference expansion' summary point at the Python package's ${file:} branch in _pre_process; the README documents ${file:path.json} next to the Python loader."
 },
 "fix_sites": [
  {
   "where": "runtime/python/prompty/prompty/core/loader.py:155",
   "entry_point": "prompty.load() / prompty.load_async() (Python public API)",
   "module_kind": "primary implementation (Python loader)"
  },
  {
   "where": "runtime/typescript/packages/core/src/core/loader.ts:147",
   "entry_point": "load() exported from @prompty/core (TypeScript public API)",
   "module_kind": "second implementation (TypeScript runtime)"
  },
  {
   "where": "runtime/rust/prompty/src/loader/resolve.rs:106",
   "entry_point": "prompty::load / load_async / load_from_string (Rust public API); reached by two passes, resolve_references at runtime/rust/prompty/src/loader.rs:148 and pre_process via resolve_single_ref at runtime/rust/prompty/src/loader.rs:172",
   "module_kind": "second implementation (Rust crate), including a lower-level public API (load_from_string with caller-supplied base_path)"
  },
  {
   "where": "runtime/csharp/Prompty.Core/ReferenceResolver.cs:105",
   "entry_point": "PromptyLoader.Load / LoadAsync, and the public ReferenceResolver.CreatePreProcess (C# public API)",
   "module_kind": "second implementation (C#), including a lower-level public helper (CreatePreProcess)"
  },
  {
   "where": "runtime/csharp/Prompty.Core/PromptyLoader.cs:55",
   "entry_point": "PromptyLoader.Load / LoadAsync (C#), plumbing of the new allowed-roots option",
   "module_kind": "wrapper (loader options plumbing)"
  }
 ],
 "O1_entry_points": 9,
 "O2_out_of_scope_site": {
  "kind": "second_implementation",
  "where": "runtime/rust/prompty/src/loader/resolve.rs:101-110 and runtime/csharp/Prompty.Core/ReferenceResolver.cs:103-108 (also runtime/typescript/packages/core/src/core/loader.ts:146-148); Rust resolves twice, runtime/rust/prompty/src/loader.rs:148 and runtime/rust/prompty/src/loader.rs:172"
 },
 "O3_reason_to_dismiss": "The advisory is filed as a PYSEC/Python issue, so the Rust, C# and TypeScript runtimes look like separate packages. PromptyTool 'path' is a tool reference that spec \u00a79.7 says to resolve relative to the parent with no containment (spec/spec.md:2503-2504), not a ${file:} expansion.",
 "O4_distance": {
  "files": 4,
  "packages": 4,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "${file:} references inside the prompt directory (e.g. shared connection JSON injected into model.connection) must keep working, and parsed JSON/YAML is returned as structured data. With the fix, files outside the prompt directory must still load when the host opts in through allowed roots. An over-broad fix (reject every '..' or every absolute path, or drop ${file:}) breaks the shared-config and allowed-root cases.",
  "where": "runtime/python/prompty/tests/test_loader.py:352-365; runtime/python/prompty/prompty/core/loader.py:167-175; fix.diff:592-607"
 },
 "O6_input_shapes": [
  "relative '../' traversal (fix.diff:566-575)",
  "absolute path (fix.diff:577-590; the fix adds an explicit is_absolute branch at fix.diff:541-543 and fix.diff:317-319)",
  "symlink inside the prompt directory pointing outside (fix.diff:609-625)",
  "nested dicts and arrays of frontmatter (Rust recursive walk, fix.diff:983-994)",
  "opt-in allowed roots, sibling directory reached through '..' (fix.diff:592-607)"
 ],
 "O7_producer": {
  "kind": "config_loader",
  "where": "Frontmatter is the config. LoadContext.pre_process is invoked by the generated model loader on every nested dict (runtime/python/prompty/prompty/core/loader.py:99-100, runtime/typescript/packages/core/src/core/loader.ts:82-85). __source_path, which later drives PromptyTool child resolution, is stored in metadata at runtime/python/prompty/prompty/core/loader.py:105.",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "Python PromptyTool handler joins frontmatter tool.path onto the parent's directory and calls load() on it with no containment, and the child does not inherit allowed roots.",
   "where": "runtime/python/prompty/prompty/core/tool_dispatch.py:274-280",
   "reason_to_dismiss": "It is a tool-kind feature that loads another .prompty, not ${file:} expansion; spec says resolve relative to parent.",
   "distance": "different file (core/tool_dispatch.py) from core/loader.py, same package",
   "present_in_latest": "no",
   "latest_where": ""
  },
  {
   "route": "Python OpenAI wire projection of PromptyTool loads the child at parent_dir/tool_path with no containment.",
   "where": "runtime/python/prompty/prompty/providers/openai/executor.py:151-156",
   "reason_to_dismiss": "Provider-specific wire-format code; looks like an OpenAI adapter, not the loader.",
   "distance": "different subpackage (providers/openai) from core/loader.py",
   "present_in_latest": "no",
   "latest_where": ""
  },
  {
   "route": "TypeScript core PromptyTool handler resolves tool.path against the parent's directory and loads it with no containment.",
   "where": "runtime/typescript/packages/core/src/core/tool-dispatch.ts:184-196",
   "reason_to_dismiss": "Same as the Python handler: a tool reference, not a file include.",
   "distance": "different file from core/loader.ts, same package",
   "present_in_latest": "no",
   "latest_where": ""
  },
  {
   "route": "TypeScript OpenAI wire projection loads the PromptyTool child path with no containment.",
   "where": "runtime/typescript/packages/openai/src/wire.ts:372-379",
   "reason_to_dismiss": "Separate provider package (@prompty/openai).",
   "distance": "different npm package from @prompty/core",
   "present_in_latest": "no",
   "latest_where": ""
  },
  {
   "route": "Rust PromptyTool handler joins the tool_def 'path' onto the parent's directory with no containment.",
   "where": "runtime/rust/prompty/src/tool_dispatch.rs:473-484",
   "reason_to_dismiss": "Tool dispatch, not the loader's resolve module.",
   "distance": "different module (tool_dispatch.rs) from loader/resolve.rs, same crate",
   "present_in_latest": "no",
   "latest_where": ""
  },
  {
   "route": "C# PromptyTool handler combines the parent's directory (or the CWD when there is no source path) with promptyTool.Path and calls PromptyLoader.Load with no containment.",
   "where": "runtime/csharp/Prompty.Core/ToolDispatch.cs:128-133",
   "reason_to_dismiss": "Tool dispatch, not ReferenceResolver.",
   "distance": "different file (ToolDispatch.cs) from ReferenceResolver.cs, same project",
   "present_in_latest": "no",
   "latest_where": ""
  }
 ],
 "O8b_injection_room": [
  {
   "where": "runtime/python/prompty/prompty/core/loader.py:115-160",
   "sibling": "A second include-style protocol (e.g. ${prompt:...} or ${template:...}) that reads a file relative to the prompt directory through its own branch.",
   "why_realistic": "The protocol switch already dispatches by name ('env', 'file'), and the TS comment says the loader handles YAML natively, so adding a protocol branch with its own path join is a natural extension."
  },
  {
   "where": "runtime/python/prompty/prompty/core/loader.py:89-107",
   "sibling": "A body-level include (e.g. a {% include %}-style template loader or image/file content part with a local path) resolved relative to __source_path.",
   "why_realistic": "__source_path is stored for exactly this kind of relative lookup, and rich 'file'/'image' content kinds already exist (runtime/python/prompty/prompty/core/types.py:50)."
  }
 ],
 "O9_family": "path traversal / arbitrary file read (CWE-22, CWE-200) via author-controlled include path",
 "O9_dos": false,
 "O10_build": {
  "language": "Python, TypeScript, Rust, C# (four parallel runtimes; a task can pin one or all)",
  "toolchain": "uv + pytest (runtime/python/prompty); npm + vitest (runtime/typescript); cargo, rust 1.85, edition 2024 (runtime/rust); .NET 9 SDK + xUnit (runtime/csharp)",
  "services": [],
  "offline_after_build": true,
  "project_tests": "runtime/python/prompty/tests/test_loader.py (TestReferenceResolution, TestFileSharedConfig); runtime/typescript/packages/core/tests/loader.test.ts; runtime/rust/prompty/src/loader/resolve.rs mod tests; runtime/csharp/Prompty.Core.Tests/LoaderTests.cs"
 },
 "O11_fix_minutes": 75,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "runtime/python/prompty/prompty/core/loader.py; runtime/typescript/packages/core/src/core/loader.ts; runtime/typescript/packages/core/src/core/index.ts; runtime/typescript/packages/core/src/index.ts; runtime/rust/prompty/src/loader.rs; runtime/rust/prompty/src/loader/resolve.rs; runtime/rust/prompty/src/lib.rs; runtime/csharp/Prompty.Core/ReferenceResolver.cs; runtime/csharp/Prompty.Core/PromptyLoader.cs; runtime/csharp/Prompty.Core/PromptyLoadOptions.cs (new)",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 0,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Reject values containing '..' in the Python ${file:} branch only, which misses absolute paths, symlinks, the other three runtimes and the PromptyTool path routes."
 },
 "out_of_scope_notes": [
  "${env:VAR} expansion lets frontmatter read any process environment variable into prompt fields (runtime/python/prompty/prompty/core/loader.py:142-152); different protection, not pursued.",
  "The C# PromptyTool handler falls back to the process CWD when __source_path is missing (runtime/csharp/Prompty.Core/ToolDispatch.cs:129-131)."
 ],
 "unverified": [
  "repo_mb not measured (no shell); tiny_repo/giant_repo not assessed. Four runtimes plus vscode/web suggest a mid-size repo.",
  "pinned_commit hash not given in the candidate (parent_commit null); taken to be the parent of the fix commit.",
  "present_in_latest 'no' for the PromptyTool routes rests on a grep of latest/runtime finding no PromptyTool, tool.path or tool_path in .py/.ts/.rs/.cs files. The feature looks removed or renamed, not fixed in place. A comment in latest/runtime/python/prompty/prompty/core/loader.py:231-232 says a shared containment primitive guards every author-controlled filesystem sink; its callers were not traced.",
  "Whether a non-.prompty file loaded as a PromptyTool child gets its content into the prompt (Python treats body-only files as instructions, runtime/python/prompty/prompty/core/loader.py:93-94) was inferred, not traced end to end in every runtime.",
  "Whether ${file:} strings inside an included JSON/YAML file are resolved again by pre_process on nested dicts (a nested-include input shape) was not traced.",
  "The fix diff lines 1225-2717 and 2951-5944 (lockfiles, package.json, docs) were skimmed only by file header and treated as non-source."
 ]
}
  ```
- Published fix sites:   - runtime/python/prompty/prompty/core/loader.py:155 — entry point: prompty.load() / prompty.load_async() (Python public API) [primary implementation (Python loader)]
  - runtime/typescript/packages/core/src/core/loader.ts:147 — entry point: load() exported from @prompty/core (TypeScript public API) [second implementation (TypeScript runtime)]
  - runtime/rust/prompty/src/loader/resolve.rs:106 — entry point: prompty::load / load_async / load_from_string (Rust public API); reached by two passes, resolve_references at runtime/rust/prompty/src/loader.rs:148 and pre_process via resolve_single_ref at runtime/rust/prompty/src/loader.rs:172 [second implementation (Rust crate), including a lower-level public API (load_from_string with caller-supplied base_path)]
  - runtime/csharp/Prompty.Core/ReferenceResolver.cs:105 — entry point: PromptyLoader.Load / LoadAsync, and the public ReferenceResolver.CreatePreProcess (C# public API) [second implementation (C#), including a lower-level public helper (CreatePreProcess)]
  - runtime/csharp/Prompty.Core/PromptyLoader.cs:55 — entry point: PromptyLoader.Load / LoadAsync (C#), plumbing of the new allowed-roots option [wrapper (loader options plumbing)]
- Uncovered routes to confirm (pattern B):   - runtime/python/prompty/prompty/core/tool_dispatch.py:274-280 — Python PromptyTool handler joins frontmatter tool.path onto the parent's directory and calls load() on it with no containment, and the child does not inherit allowed roots. (reason to dismiss: It is a tool-kind feature that loads another .prompty, not ${file:} expansion; spec says resolve relative to parent.; still in latest: no)
  - runtime/python/prompty/prompty/providers/openai/executor.py:151-156 — Python OpenAI wire projection of PromptyTool loads the child at parent_dir/tool_path with no containment. (reason to dismiss: Provider-specific wire-format code; looks like an OpenAI adapter, not the loader.; still in latest: no)
  - runtime/typescript/packages/core/src/core/tool-dispatch.ts:184-196 — TypeScript core PromptyTool handler resolves tool.path against the parent's directory and loads it with no containment. (reason to dismiss: Same as the Python handler: a tool reference, not a file include.; still in latest: no)
  - runtime/typescript/packages/openai/src/wire.ts:372-379 — TypeScript OpenAI wire projection loads the PromptyTool child path with no containment. (reason to dismiss: Separate provider package (@prompty/openai).; still in latest: no)
  - runtime/rust/prompty/src/tool_dispatch.rs:473-484 — Rust PromptyTool handler joins the tool_def 'path' onto the parent's directory with no containment. (reason to dismiss: Tool dispatch, not the loader's resolve module.; still in latest: no)
  - runtime/csharp/Prompty.Core/ToolDispatch.cs:128-133 — C# PromptyTool handler combines the parent's directory (or the CWD when there is no source path) with promptyTool.Path and calls PromptyLoader.Load with no containment. (reason to dismiss: Tool dispatch, not ReferenceResolver.; still in latest: no)
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

## Environment (`tasks/prompty-mm/environment/Dockerfile`)
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

## Report to the solver (`tasks/prompty-mm/instruction.md`)
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

## Tests (`tasks/prompty-mm/tests/`)
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
- **Wrong-fix patches** go in `build/prompty-mm/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/prompty-mm/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/prompty-mm/manifest.json`:**
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

**Also in `build/prompty-mm/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py prompty-mm --only static
python3 -I builder/gate.py prompty-mm --only nop
python3 -I builder/gate.py prompty-mm --only oracle
python3 -I builder/gate.py prompty-mm --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/prompty-mm/`;
  - edit only `tasks/prompty-mm/`, `build/prompty-mm/` and, for pattern B, the register;
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
