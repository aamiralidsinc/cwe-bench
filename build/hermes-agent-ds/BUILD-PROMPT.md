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

Project root: `/home/mara/cwe-bench`. Task: `hermes-agent-ds`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: ["GHSA-33QV-C5QM-799V", "CVE-2026-10223", "PYSEC-2026-3575"]; nousresearch/hermes-agent; prompt injection / untrusted content entering LLM system prompt or context (CWE-74)
- Pinned (vulnerable) commit: parent of 0dee92df22bdc0cfbcad90ca954aa14916f018de (parent_commit not given in candidate). Published fix: 0dee92df22bdc0cfbcad90ca954aa14916f018de.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "317",
 "advisory_ids": [
  "GHSA-33QV-C5QM-799V",
  "CVE-2026-10223",
  "PYSEC-2026-3575"
 ],
 "repo": "nousresearch/hermes-agent",
 "pinned_commit": "parent of 0dee92df22bdc0cfbcad90ca954aa14916f018de (parent_commit not given in candidate)",
 "fix_commits": [
  "0dee92df22bdc0cfbcad90ca954aa14916f018de"
 ],
 "trust_decision": {
  "summary": "Whether attacker-influenced text (project context files, on-disk memory entries, results of web/browser/MCP tools) may enter the system prompt / model context as instructions: decided by per-module regex scanners in agent/prompt_builder.py and tools/memory_tool.py, and (after the fix) by an untrusted-data wrapper in make_tool_result_message.",
  "evidence": [
   "agent/prompt_builder.py:55-69",
   "tools/memory_tool.py:137-149",
   "tools/memory_tool.py:201-217",
   "agent/tool_dispatch_helpers.py:320-328",
   "fix.diff:1142-1179"
  ]
 },
 "landing_point": {
  "where": "agent/prompt_builder.py:55",
  "why": "Generic 'Injection' summary in a coding agent leads to the existing prompt-injection scanner _scan_context_content and its weak _CONTEXT_THREAT_PATTERNS list (agent/prompt_builder.py:36-52)."
 },
 "fix_sites": [
  {
   "where": "agent/prompt_builder.py:55",
   "entry_point": "build_context_files_prompt / load_soul_md (agent/prompt_builder.py:1426, agent/prompt_builder.py:1313) and subdirectory hints (agent/subdirectory_hints.py:188); called from build_system_prompt_parts (agent/system_prompt.py:269)",
   "module_kind": "context-file loader (pattern set replaced by shared library, context scope)"
  },
  {
   "where": "agent/tool_dispatch_helpers.py:320",
   "entry_point": "every tool call result appended via make_tool_result_message (agent/tool_executor.py:447, agent/tool_executor.py:863, agent/agent_runtime_helpers.py:321, mini_swe_runner.py:540)",
   "module_kind": "message builder helper (new untrusted-data wrapper for web_*/browser_*/mcp_* tools)"
  },
  {
   "where": "tools/memory_tool.py:137",
   "entry_point": "memory tool add/replace actions (tools/memory_tool.py:315, tools/memory_tool.py:368)",
   "module_kind": "tool write-path validator (pattern set replaced, strict scope)"
  },
  {
   "where": "tools/memory_tool.py:201-217",
   "entry_point": "MemoryStore.load_from_disk at agent init and after compression (agent/agent_init.py:1076, agent/system_prompt.py:348), consumed by format_for_system_prompt (agent/system_prompt.py:279)",
   "module_kind": "save/reload path: frozen snapshot built from on-disk MEMORY.md/USER.md with no scan (new load-time sanitisation)"
  },
  {
   "where": "fix.diff:950-1207",
   "entry_point": "new tools/threat_patterns.scan_for_threats / first_threat_message used by the three sites above",
   "module_kind": "new shared pattern library (adds promptware/C2 patterns, scope split)"
  }
 ],
 "O1_entry_points": 5,
 "O2_out_of_scope_site": {
  "kind": "save_reload_or_serialization",
  "where": "tools/memory_tool.py:201-217 (load_from_disk builds the system-prompt snapshot from disk without calling _scan_memory_content; only writes via tools/memory_tool.py:315 and tools/memory_tool.py:368 are scanned). Second: agent/tool_dispatch_helpers.py:320 is a generic message-builder helper far from any scanner."
 },
 "O3_reason_to_dismiss": "Memory files are written only through the memory tool, which already scans on add/replace (tools/memory_tool.py:315), so re-scanning on load looks redundant; and tool results are not 'context files' at all, so the report's context-file framing excludes them.",
 "O4_distance": {
  "files": 4,
  "packages": 2,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Multimodal tool results (content lists with image_url parts) must pass through as lists, short tool outputs and low-risk tools (terminal, read_file, memory) are left untouched, and blocked memory entries stay in live state so memory(action=read/remove) still shows them; an over-broad fix that wraps or scans every tool result or drops poisoned entries from disk/live state breaks these.",
  "where": "agent/tool_executor.py:855-863; fix.diff:136-143; fix.diff:897-909; tools/memory_tool.py:189-190"
 },
 "O6_input_shapes": [
  "plain string tool result (wrapped)",
  "multimodal list tool result (deliberately unwrapped)",
  "already-wrapped string (re-entrancy guard)",
  "short string under 32 chars (unwrapped)",
  "tool names by exact match (web_extract, web_search) and by prefix (browser_*, mcp_*)",
  "on-disk memory entry vs tool-written entry",
  "entry already starting with [BLOCKED:",
  "invisible unicode (extended set incl. U+2062-2064, U+2066-2069) vs regex pattern hits",
  "filler-word variants via (?:\\w+\\s+)* in context patterns"
 ],
 "O7_producer": {
  "kind": "serializer",
  "where": "tools/memory_tool.py:206-217 (_read_file of MEMORY.md/USER.md then _render_block into _system_prompt_snapshot)",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "External memory provider system_prompt_block() text is joined straight into the system prompt with no threat scan.",
   "where": "agent/memory_manager.py:318-335",
   "reason_to_dismiss": "Plugin-provided memory backend (honcho etc.), a neighbouring feature the built-in memory fix never touched; provider is 'trusted code'.",
   "distance": "agent/memory_manager.py, consumed at agent/system_prompt.py:289-293; different file from all fix sites",
   "present_in_latest": "yes",
   "latest_where": "latest/agent/memory_manager.py:501-505"
  },
  {
   "route": "Prefetched external memory recall is fenced as 'authoritative reference data' with only tag stripping (sanitize_context), no threat scan.",
   "where": "agent/memory_manager.py:227-241",
   "reason_to_dismiss": "Already fenced in <memory-context>, so it looks like it already has the delimiter defence.",
   "distance": "agent/memory_manager.py, used at agent/conversation_loop.py:831",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "Codex app-server projection builds role=tool messages for MCP and dynamic tool results directly, bypassing make_tool_result_message, and uses name mcp.server.tool which the mcp_ prefix would not match anyway.",
   "where": "agent/transports/codex_event_projector.py:241-253",
   "reason_to_dismiss": "Separate transport (Codex runtime owns its own model loop); a legacy/alternate backend path.",
   "distance": "agent/transports/ subpackage, two directories from the landing point",
   "present_in_latest": "yes",
   "latest_where": "latest/agent/transports/codex_event_projector.py:101"
  },
  {
   "route": "x_search tool returns attacker-authored X posts but is not in the untrusted tool set, so its results are not wrapped.",
   "where": "tools/x_search_tool.py:517-523",
   "reason_to_dismiss": "Optional toolset needing XAI_API_KEY; report lists web/browser/MCP only.",
   "distance": "tools/x_search_tool.py vs agent/tool_dispatch_helpers.py:106-114 (fix.diff)",
   "present_in_latest": "yes",
   "latest_where": "latest/agent/tool_dispatch_helpers.py:484-485"
  },
  {
   "route": "Skill install scanner keeps its own separate THREAT_PATTERNS / INVISIBLE_CHARS copy, not migrated to the shared library (promptware patterns not applied to skills).",
   "where": "tools/skills_guard.py:86",
   "reason_to_dismiss": "Skills Guard is a separate, richer scanner with its own advisory history; the fix comment calls it the reference implementation.",
   "distance": "tools/skills_guard.py, same package as memory_tool",
   "present_in_latest": "unknown",
   "latest_where": ""
  }
 ],
 "O8b_injection_room": [
  {
   "where": "agent/subdirectory_hints.py:188",
   "sibling": "a second context-file loader (e.g. .github/copilot-instructions.md or .clinerules) that reads and appends without _scan_context_content",
   "why_realistic": "Loaders are copy-pasted per file type in agent/prompt_builder.py:1341-1423; a new one forgetting the scan call is a natural contributor slip."
  },
  {
   "where": "agent/tool_executor.py:78",
   "sibling": "an extra tool-result append path (e.g. a steer/interrupt or cached-result branch) that builds the role=tool dict inline instead of via make_tool_result_message",
   "why_realistic": "agent/conversation_loop.py:3337-3342 and agent/conversation_loop.py:3969-3974 already build tool dicts inline for synthetic errors."
  },
  {
   "where": "tools/memory_tool.py:458-464",
   "sibling": "a memory 'import/merge from file' action that extends memory_entries and rebuilds the snapshot without the scan",
   "why_realistic": "Drift-guard remediation text (tools/memory_tool.py:174-178) already discusses integrating external entries."
  }
 ],
 "O9_family": "prompt injection / untrusted content entering LLM system prompt or context (CWE-74)",
 "O9_dos": false,
 "O10_build": {
  "language": "Python (>=3.11)",
  "toolchain": "pip/uv install of pyproject.toml with dev extra (pytest 9, pytest-asyncio, pytest-timeout)",
  "services": [],
  "offline_after_build": true,
  "project_tests": "tests/tools/test_memory_tool.py exists at pinned commit (fix appends TestLoadTimeSnapshotSanitization); fix adds tests/tools/test_threat_patterns.py and tests/agent/test_tool_dispatch_helpers.py; scanners are pure functions testable offline"
 },
 "O11_fix_minutes": 60,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "agent/prompt_builder.py, agent/tool_dispatch_helpers.py, tools/memory_tool.py, tools/threat_patterns.py (new)",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Add a few more regexes to _CONTEXT_THREAT_PATTERNS in agent/prompt_builder.py and stop, leaving memory load-time snapshot and tool results unprotected."
 },
 "out_of_scope_notes": [
  "Published wrapper skips wrapping when content already starts with '<untrusted_tool_result' (fix.diff:142-143) and does not neutralise a closing tag inside content; latest adds a case-insensitive delimiter-token regex (latest/agent/tool_dispatch_helpers.py:489), suggesting later hardening of the fix itself.",
  "Hidden tests for a regex-pattern library are brittle: the exact pattern IDs (fix.diff:1006-1069) are not derivable from a short report, so tests should target behaviour (blocked/wrapped) not IDs."
 ],
 "unverified": [
  "repo size in MB not measured (no shell); tiny_repo/giant_repo not assessed",
  "pinned commit hash not given (parent_commit null); assumed repo dir is the fix's parent",
  "whether Codex-projected tool messages are ever replayed to a model (affects O8 route 3 severity)",
  "present_in_latest for prefetch fence and skills_guard routes not checked",
  "advisory prose not available; read only the fix diff",
  "recall_risk based on Brainworm references in the diff (fix.diff:322-339), not on external search"
 ]
}
  ```
- Published fix sites:   - agent/prompt_builder.py:55 — entry point: build_context_files_prompt / load_soul_md (agent/prompt_builder.py:1426, agent/prompt_builder.py:1313) and subdirectory hints (agent/subdirectory_hints.py:188); called from build_system_prompt_parts (agent/system_prompt.py:269) [context-file loader (pattern set replaced by shared library, context scope)]
  - agent/tool_dispatch_helpers.py:320 — entry point: every tool call result appended via make_tool_result_message (agent/tool_executor.py:447, agent/tool_executor.py:863, agent/agent_runtime_helpers.py:321, mini_swe_runner.py:540) [message builder helper (new untrusted-data wrapper for web_*/browser_*/mcp_* tools)]
  - tools/memory_tool.py:137 — entry point: memory tool add/replace actions (tools/memory_tool.py:315, tools/memory_tool.py:368) [tool write-path validator (pattern set replaced, strict scope)]
  - tools/memory_tool.py:201-217 — entry point: MemoryStore.load_from_disk at agent init and after compression (agent/agent_init.py:1076, agent/system_prompt.py:348), consumed by format_for_system_prompt (agent/system_prompt.py:279) [save/reload path: frozen snapshot built from on-disk MEMORY.md/USER.md with no scan (new load-time sanitisation)]
  - fix.diff:950-1207 — entry point: new tools/threat_patterns.scan_for_threats / first_threat_message used by the three sites above [new shared pattern library (adds promptware/C2 patterns, scope split)]
- Uncovered routes to confirm (pattern B):   - agent/memory_manager.py:318-335 — External memory provider system_prompt_block() text is joined straight into the system prompt with no threat scan. (reason to dismiss: Plugin-provided memory backend (honcho etc.), a neighbouring feature the built-in memory fix never touched; provider is 'trusted code'.; still in latest: yes)
  - agent/memory_manager.py:227-241 — Prefetched external memory recall is fenced as 'authoritative reference data' with only tag stripping (sanitize_context), no threat scan. (reason to dismiss: Already fenced in <memory-context>, so it looks like it already has the delimiter defence.; still in latest: unknown)
  - agent/transports/codex_event_projector.py:241-253 — Codex app-server projection builds role=tool messages for MCP and dynamic tool results directly, bypassing make_tool_result_message, and uses name mcp.server.tool which the mcp_ prefix would not match anyway. (reason to dismiss: Separate transport (Codex runtime owns its own model loop); a legacy/alternate backend path.; still in latest: yes)
  - tools/x_search_tool.py:517-523 — x_search tool returns attacker-authored X posts but is not in the untrusted tool set, so its results are not wrapped. (reason to dismiss: Optional toolset needing XAI_API_KEY; report lists web/browser/MCP only.; still in latest: yes)
  - tools/skills_guard.py:86 — Skill install scanner keeps its own separate THREAT_PATTERNS / INVISIBLE_CHARS copy, not migrated to the shared library (promptware patterns not applied to skills). (reason to dismiss: Skills Guard is a separate, richer scanner with its own advisory history; the fix comment calls it the reference implementation.; still in latest: unknown)
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

## Environment (`tasks/hermes-agent-ds/environment/Dockerfile`)
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

## Report to the solver (`tasks/hermes-agent-ds/instruction.md`)
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

## Tests (`tasks/hermes-agent-ds/tests/`)
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
- **Wrong-fix patches** go in `build/hermes-agent-ds/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/hermes-agent-ds/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/hermes-agent-ds/manifest.json`:**
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

**Also in `build/hermes-agent-ds/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py hermes-agent-ds --only static
python3 -I builder/gate.py hermes-agent-ds --only nop
python3 -I builder/gate.py hermes-agent-ds --only oracle
python3 -I builder/gate.py hermes-agent-ds --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/hermes-agent-ds/`;
  - edit only `tasks/hermes-agent-ds/`, `build/hermes-agent-ds/` and, for pattern B, the register;
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
