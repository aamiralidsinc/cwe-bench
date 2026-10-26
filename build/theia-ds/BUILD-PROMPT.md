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

Project root: `/home/mara/cwe-bench`. Task: `theia-ds`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: ["GHSA-3JWW-HXQJ-WFQ2", "CVE-2026-44688"]; eclipse-theia/theia; Untrusted-workspace configuration and content reaching AI agents (workspace-trust bypass / CWE-829 inclusion from an untrusted control sphere)
- Pinned (vulnerable) commit: parent of e3fdfe6992389bc5fa611058d00c39d7408508ed (parent_commit not given in candidate). Published fix: e3fdfe6992389bc5fa611058d00c39d7408508ed.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "7951",
 "advisory_ids": [
  "GHSA-3JWW-HXQJ-WFQ2",
  "CVE-2026-44688"
 ],
 "repo": "eclipse-theia/theia",
 "pinned_commit": "parent of e3fdfe6992389bc5fa611058d00c39d7408508ed (parent_commit not given in candidate)",
 "fix_commits": [
  "e3fdfe6992389bc5fa611058d00c39d7408508ed"
 ],
 "trust_decision": {
  "summary": "Whether AI features may run, and whether AI preferences may be read from workspace/folder scope, given workspace trust. Before the fix the decision was only 'AI enabled in preferences' (AIIdeActivationServiceImpl.isActive) and workspace-scope AI settings were always merged in; the fix adds canRun = isActive && workspaceTrusted plus a TrustAwarePreferenceReader that drops workspace/folder scopes when untrusted.",
  "evidence": [
   "packages/ai-ide/src/browser/ai-ide-activation-service.ts:41-43",
   "packages/ai-ide/src/browser/ai-ide-activation-service.ts:52-63",
   "fix.diff:1170-1172",
   "fix.diff:1078-1085"
  ]
 },
 "landing_point": {
  "where": "packages/ai-ide/src/browser/workspace-functions.ts:203",
  "why": "The summary talks about adversarial workspace file and directory names reaching AI chat, so a reader would go first to the workspace-listing tools (GetWorkspaceDirectoryStructure / GetWorkspaceFileList at workspace-functions.ts:543) that put names into the prompt. The published fix does not touch them; it gates AI on workspace trust instead."
 },
 "fix_sites": [
  {
   "where": "packages/ai-ide/src/browser/ai-ide-activation-service.ts:41",
   "entry_point": "AIActivationService.isActive/canRun (public DI service consumed by every AI package)",
   "module_kind": "core service (activation state)"
  },
  {
   "where": "packages/ai-core/src/browser/ai-core-frontend-module.ts:181",
   "entry_point": "AICommandHandlerFactory wrapper: isEnabled of every AI command (e.g. ai-editor Ask AI)",
   "module_kind": "wrapper_or_composition"
  },
  {
   "where": "packages/ai-core/src/browser/frontend-language-model-service.ts:40",
   "entry_point": "LanguageModelService.sendRequest public API (all LLM-backed agents, terminal agent, session naming)",
   "module_kind": "lower_level_api"
  },
  {
   "where": "packages/ai-core/src/browser/ai-settings-service.ts:64",
   "entry_point": "AISettingsService.getSettings (ai-features.agentSettings preference)",
   "module_kind": "config loader (preference read)"
  },
  {
   "where": "packages/ai-core/src/browser/frontend-language-model-alias-registry.ts:143",
   "entry_point": "LanguageModelAliasRegistry (ai-features.languageModelAliases preference)",
   "module_kind": "config loader (preference read)"
  },
  {
   "where": "packages/ai-chat/src/browser/chat-tool-preference-bindings.ts:54",
   "entry_point": "ToolConfirmationManager.getConfirmationMode (tool-call approval, ai-features.chat.toolConfirmation)",
   "module_kind": "defaults_or_merge_route (preference merge)"
  },
  {
   "where": "packages/ai-ide/src/browser/template-preference-contribution.ts:76",
   "entry_point": "workspace prompt-template directories/files/extensions preferences -> PromptFragmentCustomizationService (custom agents, prompt templates)",
   "module_kind": "config loader (preference read)"
  },
  {
   "where": "packages/ai-chat-ui/src/browser/chat-view-widget.tsx:152",
   "entry_point": "AI chat view input enablement",
   "module_kind": "UI widget"
  },
  {
   "where": "packages/ai-chat-ui/src/browser/chat-input-widget.tsx:651",
   "entry_point": "AI chat input widget enablement",
   "module_kind": "UI widget"
  },
  {
   "where": "packages/ai-chat-ui/src/browser/chat-tree-view/chat-view-tree-widget.tsx:224",
   "entry_point": "chat tree inline inputs (edit request) enablement",
   "module_kind": "UI widget"
  },
  {
   "where": "packages/ai-chat-ui/src/browser/ai-chat-ui-contribution.ts:161",
   "entry_point": "chat commands (new chat, task context, show/rename/delete chats) isEnabled",
   "module_kind": "command contribution"
  },
  {
   "where": "packages/ai-chat-ui/src/browser/chat-view-widget-toolbar-contribution.tsx:60",
   "entry_point": "EDIT_SESSION_SETTINGS command",
   "module_kind": "command contribution"
  },
  {
   "where": "packages/ai-code-completion/src/browser/ai-code-frontend-application-contribution.ts:96",
   "entry_point": "monaco inline completion provider registration",
   "module_kind": "editor provider"
  },
  {
   "where": "packages/ai-editor/src/browser/ai-code-action-provider.ts:59",
   "entry_point": "monaco code action provider registration and per-call check (line 67)",
   "module_kind": "editor provider"
  },
  {
   "where": "packages/ai-claude-code/src/browser/claude-code-command-contribution.ts:59",
   "entry_point": "Claude Code open config/memory commands",
   "module_kind": "command contribution"
  }
 ],
 "O1_entry_points": 9,
 "O2_out_of_scope_site": {
  "kind": "defaults_or_merge_route",
  "where": "packages/ai-chat/src/browser/chat-tool-preference-bindings.ts:54 (also :83, :130, :134); siblings packages/ai-core/src/browser/ai-settings-service.ts:64 and packages/ai-core/src/browser/frontend-language-model-service.ts:40-41"
 },
 "O3_reason_to_dismiss": "Tool-confirmation, agent-settings and request-settings reads are 'just preference merging' in ai-chat/ai-core, far from chat input and file names; once the chat UI is disabled in untrusted workspaces a solver can argue workspace-scope settings no longer matter, and that skills/Claude Code/Codex are separate features or external CLIs.",
 "O4_distance": {
  "files": 18,
  "packages": 7,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "In a trusted workspace, workspace-scope AI settings (tool confirmation incl. '*', prompt template dirs, aliases, request settings) must still apply; in an untrusted one, user/global and default values must still apply (not wiped). Commands stay visible (isVisible keeps isActive) and only become disabled. Preference writes stay on PreferenceService. An over-broad fix that blanks all AI preferences or hides AI entirely breaks these.",
  "where": "fix.diff:1078-1085, fix.diff:262-268, fix.diff:119-121, packages/ai-chat/src/browser/chat-tool-preference-bindings.ts:83"
 },
 "O6_input_shapes": [
  "workspace-scope value vs folder-scope value (resourceUri) vs user/global vs default (fix.diff:1082-1084)",
  "wildcard '*' tool confirmation key vs per-tool key, incl. confirmAlwaysAllow tools (fix.diff:230-260)",
  "reads before trust resolves (fail-closed) vs after, and trust changing at runtime (fix.diff:1040-1072, fix.diff:598-601)",
  "prompt template directories vs single files vs additional extensions (fix.diff:1414-1459)",
  "isActive true but untrusted vs AI disabled in preferences (fix.diff:1185-1191, fix.diff:1325-1328)"
 ],
 "O7_producer": {
  "kind": "config_loader",
  "where": "PreferenceService workspace-scope merge consumed at packages/ai-chat/src/browser/chat-tool-preference-bindings.ts:54, packages/ai-ide/src/browser/template-preference-contribution.ts:76, packages/ai-core/src/browser/ai-settings-service.ts:64",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "Workspace '.prompts/skills' directory is always loaded into agent skills regardless of workspace trust",
   "where": "packages/ai-core/src/browser/skill-service.ts:174",
   "reason_to_dismiss": "Skills are a separate feature from prompt templates; the directory is hard-coded, not a preference, and the preference docs say it is 'always included' (packages/ai-core/src/common/ai-core-preferences.ts:142-145).",
   "distance": "ai-core/src/browser/skill-service.ts; different file from template-preference-contribution in ai-ide; path built at skill-service.ts:232",
   "present_in_latest": "yes",
   "latest_where": "latest/packages/ai-core/src/browser/skill-service.ts:322"
  },
  {
   "route": "ai-features.skills directories preference read from workspace scope via the raw preference proxy, not the trust-aware reader",
   "where": "packages/ai-core/src/browser/skill-service.ts:179",
   "reason_to_dismiss": "Directories go through Path.untildify against the home dir, so it looks like a user-level setting, not a workspace one.",
   "distance": "same package as the new reader (ai-core) but a different file",
   "present_in_latest": "yes",
   "latest_where": "latest/packages/ai-core/src/browser/skill-service.ts:269"
  },
  {
   "route": "Claude Code chat agent sends requests to its backend CLI service directly, bypassing the trust gate added to LanguageModelService.sendRequest",
   "where": "packages/ai-claude-code/src/browser/claude-code-chat-agent.ts:239",
   "reason_to_dismiss": "It is an external CLI agent with its own permission model, not a Theia language model; chat input is already disabled by canRun.",
   "distance": "ai-claude-code package, separate from ai-core where the gate lives",
   "present_in_latest": "yes",
   "latest_where": "latest/packages/ai-claude-code/src/browser/claude-code-chat-agent.ts:239"
  },
  {
   "route": "Codex chat agent sends requests to its backend service directly, bypassing the LanguageModelService trust gate",
   "where": "packages/ai-codex/src/browser/codex-chat-agent.ts:110",
   "reason_to_dismiss": "Same as Claude Code: an external agent integration; reached only via ChatService.sendRequest (packages/ai-chat/src/common/chat-service.ts:280), which has no trust check of its own.",
   "distance": "ai-codex package",
   "present_in_latest": "yes",
   "latest_where": "latest/packages/ai-codex/src/browser/codex-chat-agent.ts:113"
  },
  {
   "route": "SCANOSS change-set scan action still gates rendering on isActive, not canRun",
   "where": "packages/ai-scanoss/src/browser/change-set-scan-action/change-set-scan-action.tsx:73",
   "reason_to_dismiss": "It is a licence scanner, not an LLM feature, and change sets only exist after an AI chat already ran.",
   "distance": "ai-scanoss package",
   "present_in_latest": "yes",
   "latest_where": "latest/packages/ai-scanoss/src/browser/change-set-scan-action/change-set-scan-action.tsx:73"
  }
 ],
 "O8b_injection_room": [
  {
   "where": "packages/ai-terminal/src/browser/ai-terminal-agent.ts:152",
   "sibling": "An AI package reading its own workspace-overridable preference (e.g. model/request settings) via PreferenceService.get instead of TrustAwarePreferenceReader",
   "why_realistic": "Every AI package already injects PreferenceService directly; the reader is new and opt-in, so a maintainer adding a setting would naturally use the old service."
  },
  {
   "where": "packages/ai-copilot/src/browser/copilot-status-bar-contribution.ts:77",
   "sibling": "A provider/command gated on activationService.isActive instead of canRun",
   "why_realistic": "isActive and canRun sit side by side on the same interface and isVisible deliberately keeps isActive, so mixing them up is easy."
  }
 ],
 "O9_family": "Untrusted-workspace configuration and content reaching AI agents (workspace-trust bypass / CWE-829 inclusion from an untrusted control sphere)",
 "O9_dos": false,
 "O10_build": {
  "language": "TypeScript",
  "toolchain": "Node.js + npm workspaces/lerna monorepo; per-package 'theiaext test' (mocha, jsdom) per packages/ai-core/package.json:52",
  "services": [],
  "offline_after_build": true,
  "project_tests": "packages/ai-chat/src/browser/chat-tool-preference-bindings.spec.ts (pre-existing, extended by fix); fix adds packages/ai-core/src/browser/trust-aware-preference-reader.spec.ts; MCP trust handling in packages/ai-mcp/src/browser/mcp-frontend-application-contribution.ts:131 is a working in-repo precedent"
 },
 "O11_fix_minutes": 120,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "packages/ai-chat-ui/src/browser/{ai-chat-ui-contribution.ts,chat-input-widget.tsx,chat-tree-view/chat-view-tree-widget.tsx,chat-view-widget-toolbar-contribution.tsx,chat-view-widget.tsx}; packages/ai-chat/src/browser/chat-tool-preference-bindings.ts; packages/ai-claude-code/src/browser/claude-code-command-contribution.ts; packages/ai-code-completion/src/browser/ai-code-frontend-application-contribution.ts; packages/ai-core/src/browser/{ai-activation-service.ts,ai-core-frontend-module.ts,ai-settings-service.ts,frontend-language-model-alias-registry.ts,frontend-language-model-service.ts,trust-aware-preference-reader.ts}; packages/ai-editor/src/browser/ai-code-action-provider.ts; packages/ai-ide/src/browser/{ai-ide-activation-service.ts,ai-workspace-restriction-contribution.ts,frontend-module.ts,ide-chat-welcome-message-provider.tsx,template-preference-contribution.ts}",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 0,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Sanitise or escape file/directory names in the workspace-listing tools (or disable the chat input when untrusted) and leave workspace-scope tool-confirmation/settings/template merges and the LLM send path ungated."
 },
 "out_of_scope_notes": [
  "MCP server autostart already has its own trust gating at the pinned commit (packages/ai-mcp/src/browser/mcp-frontend-application-contribution.ts:219-226); not pursued."
 ],
 "unverified": [
  "The advisory summary (prompt injection via adversarial file/directory names) does not obviously match the fix (workspace-trust restricted mode for AI). The advisory text was not available; the mapping of this fix commit to the advisory is assumed from the candidate record.",
  "pinned_commit hash not given (parent_commit null); recorded as the parent of the fix commit.",
  "repo_mb unknown (no size measurement done); giant_repo/tiny_repo not assessed beyond Theia being a large monorepo.",
  "O1 count of 9 groups the 45 changed lines by distinct public entry point; the exact grouping is a judgement call.",
  "Reachability of the Claude Code/Codex routes while chat UI is disabled depends on callers of ChatService.sendRequest outside the chat UI; not fully traced.",
  "Buildability (npm install needs network for native deps) not checked by running anything."
 ]
}
  ```
- Published fix sites:   - packages/ai-ide/src/browser/ai-ide-activation-service.ts:41 — entry point: AIActivationService.isActive/canRun (public DI service consumed by every AI package) [core service (activation state)]
  - packages/ai-core/src/browser/ai-core-frontend-module.ts:181 — entry point: AICommandHandlerFactory wrapper: isEnabled of every AI command (e.g. ai-editor Ask AI) [wrapper_or_composition]
  - packages/ai-core/src/browser/frontend-language-model-service.ts:40 — entry point: LanguageModelService.sendRequest public API (all LLM-backed agents, terminal agent, session naming) [lower_level_api]
  - packages/ai-core/src/browser/ai-settings-service.ts:64 — entry point: AISettingsService.getSettings (ai-features.agentSettings preference) [config loader (preference read)]
  - packages/ai-core/src/browser/frontend-language-model-alias-registry.ts:143 — entry point: LanguageModelAliasRegistry (ai-features.languageModelAliases preference) [config loader (preference read)]
  - packages/ai-chat/src/browser/chat-tool-preference-bindings.ts:54 — entry point: ToolConfirmationManager.getConfirmationMode (tool-call approval, ai-features.chat.toolConfirmation) [defaults_or_merge_route (preference merge)]
  - packages/ai-ide/src/browser/template-preference-contribution.ts:76 — entry point: workspace prompt-template directories/files/extensions preferences -> PromptFragmentCustomizationService (custom agents, prompt templates) [config loader (preference read)]
  - packages/ai-chat-ui/src/browser/chat-view-widget.tsx:152 — entry point: AI chat view input enablement [UI widget]
  - packages/ai-chat-ui/src/browser/chat-input-widget.tsx:651 — entry point: AI chat input widget enablement [UI widget]
  - packages/ai-chat-ui/src/browser/chat-tree-view/chat-view-tree-widget.tsx:224 — entry point: chat tree inline inputs (edit request) enablement [UI widget]
  - packages/ai-chat-ui/src/browser/ai-chat-ui-contribution.ts:161 — entry point: chat commands (new chat, task context, show/rename/delete chats) isEnabled [command contribution]
  - packages/ai-chat-ui/src/browser/chat-view-widget-toolbar-contribution.tsx:60 — entry point: EDIT_SESSION_SETTINGS command [command contribution]
  - packages/ai-code-completion/src/browser/ai-code-frontend-application-contribution.ts:96 — entry point: monaco inline completion provider registration [editor provider]
  - packages/ai-editor/src/browser/ai-code-action-provider.ts:59 — entry point: monaco code action provider registration and per-call check (line 67) [editor provider]
  - packages/ai-claude-code/src/browser/claude-code-command-contribution.ts:59 — entry point: Claude Code open config/memory commands [command contribution]
- Uncovered routes to confirm (pattern B):   - packages/ai-core/src/browser/skill-service.ts:174 — Workspace '.prompts/skills' directory is always loaded into agent skills regardless of workspace trust (reason to dismiss: Skills are a separate feature from prompt templates; the directory is hard-coded, not a preference, and the preference docs say it is 'always included' (packages/ai-core/src/common/ai-core-preferences.ts:142-145).; still in latest: yes)
  - packages/ai-core/src/browser/skill-service.ts:179 — ai-features.skills directories preference read from workspace scope via the raw preference proxy, not the trust-aware reader (reason to dismiss: Directories go through Path.untildify against the home dir, so it looks like a user-level setting, not a workspace one.; still in latest: yes)
  - packages/ai-claude-code/src/browser/claude-code-chat-agent.ts:239 — Claude Code chat agent sends requests to its backend CLI service directly, bypassing the trust gate added to LanguageModelService.sendRequest (reason to dismiss: It is an external CLI agent with its own permission model, not a Theia language model; chat input is already disabled by canRun.; still in latest: yes)
  - packages/ai-codex/src/browser/codex-chat-agent.ts:110 — Codex chat agent sends requests to its backend service directly, bypassing the LanguageModelService trust gate (reason to dismiss: Same as Claude Code: an external agent integration; reached only via ChatService.sendRequest (packages/ai-chat/src/common/chat-service.ts:280), which has no trust check of its own.; still in latest: yes)
  - packages/ai-scanoss/src/browser/change-set-scan-action/change-set-scan-action.tsx:73 — SCANOSS change-set scan action still gates rendering on isActive, not canRun (reason to dismiss: It is a licence scanner, not an LLM feature, and change sets only exist after an AI chat already ran.; still in latest: yes)
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

## Environment (`tasks/theia-ds/environment/Dockerfile`)
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

## Report to the solver (`tasks/theia-ds/instruction.md`)
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

## Tests (`tasks/theia-ds/tests/`)
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
- **Wrong-fix patches** go in `build/theia-ds/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/theia-ds/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/theia-ds/manifest.json`:**
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

**Also in `build/theia-ds/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py theia-ds --only static
python3 -I builder/gate.py theia-ds --only nop
python3 -I builder/gate.py theia-ds --only oracle
python3 -I builder/gate.py theia-ds --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/theia-ds/`;
  - edit only `tasks/theia-ds/`, `build/theia-ds/` and, for pattern B, the register;
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
